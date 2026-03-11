from __future__ import annotations

import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path

REQUIRED_CREDENTIAL_KEYS = ("MS_TENANT_ID", "MS_CLIENT_ID", "MS_CLIENT_SECRET")
SUPPORTED_CREDENTIAL_SOURCES = {"managed", "external_env"}


@dataclass(slots=True)
class SettingsState:
    credential_source: str = "managed"
    external_env_path: str | None = None


class SettingsManager:
    def __init__(self, config_dir: Path | None = None) -> None:
        self.config_dir = (config_dir or default_config_dir()).expanduser().resolve()
        self.settings_path = self.config_dir / "settings.json"
        self.managed_env_path = self.config_dir / ".env"

    def load_state(self) -> SettingsState:
        if not self.settings_path.exists():
            return SettingsState()
        try:
            payload = json.loads(self.settings_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return SettingsState()
        source = str(payload.get("credential_source", "managed"))
        external_path = payload.get("external_env_path")
        if source not in SUPPORTED_CREDENTIAL_SOURCES:
            source = "managed"
        if external_path is not None and not isinstance(external_path, str):
            external_path = None
        return SettingsState(credential_source=source, external_env_path=external_path)

    def save_state(self, state: SettingsState) -> SettingsState:
        if state.credential_source not in SUPPORTED_CREDENTIAL_SOURCES:
            raise ValueError(f"Unsupported credential source: {state.credential_source}")
        self.config_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "credential_source": state.credential_source,
            "external_env_path": state.external_env_path,
        }
        self.settings_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return state

    def resolve_active_env_path(self, state: SettingsState | None = None) -> Path:
        resolved_state = state or self.load_state()
        if resolved_state.credential_source == "external_env" and resolved_state.external_env_path:
            return Path(resolved_state.external_env_path).expanduser().resolve()
        return self.managed_env_path

    def read_env_file(self, path: Path) -> dict[str, str]:
        if not path.exists():
            return {}
        values: dict[str, str] = {}
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]
            values[key] = value
        return values

    def resolve_credentials(self, state: SettingsState | None = None) -> tuple[dict[str, str], SettingsState, Path]:
        resolved_state = state or self.load_state()
        source_path = self.resolve_active_env_path(resolved_state)
        file_values = self.read_env_file(source_path)
        merged = {key: (os.getenv(key) or file_values.get(key, "")) for key in REQUIRED_CREDENTIAL_KEYS}
        return merged, resolved_state, source_path

    def upsert(
        self,
        *,
        credential_source: str,
        external_env_path: str | None,
        credential_updates: dict[str, str | None] | None = None,
    ) -> SettingsState:
        if credential_source not in SUPPORTED_CREDENTIAL_SOURCES:
            raise ValueError(f"Unsupported credential source: {credential_source}")
        normalized_external_path = external_env_path.strip() if external_env_path else None
        if credential_source == "external_env" and not normalized_external_path:
            raise ValueError("external_env_path is required when credential_source is external_env")
        state = SettingsState(credential_source=credential_source, external_env_path=normalized_external_path)
        self.save_state(state)
        if credential_updates:
            self.write_managed_credentials(credential_updates)
        return state

    def write_managed_credentials(self, credential_updates: dict[str, str | None]) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        existing = self.read_env_file(self.managed_env_path)
        changed = False
        for key in REQUIRED_CREDENTIAL_KEYS:
            if key not in credential_updates:
                continue
            raw_value = credential_updates.get(key)
            if raw_value is None:
                continue
            value = raw_value.strip()
            if not value:
                if key in existing:
                    existing.pop(key, None)
                    changed = True
                continue
            if existing.get(key) != value:
                existing[key] = value
                changed = True
        if not changed and self.managed_env_path.exists():
            return
        lines = [f"{key}={existing[key]}" for key in sorted(existing)]
        if lines:
            body = "\n".join(lines) + "\n"
        else:
            body = ""
        self.managed_env_path.write_text(body, encoding="utf-8")
        self._apply_restrictive_permissions(self.managed_env_path)

    def managed_credential_presence(self) -> dict[str, bool]:
        values = self.read_env_file(self.managed_env_path)
        return {key: bool(values.get(key)) for key in REQUIRED_CREDENTIAL_KEYS}

    @staticmethod
    def _apply_restrictive_permissions(path: Path) -> None:
        try:
            if os.name == "nt":
                path.chmod(stat.S_IREAD | stat.S_IWRITE)
            else:
                path.chmod(0o600)
        except OSError:
            return


def default_config_dir() -> Path:
    override = os.getenv("CREPE_CONFIG_DIR")
    if override:
        return Path(override)
    if os.name == "nt":
        app_data = os.getenv("APPDATA")
        if app_data:
            return Path(app_data) / "crepe"
        return Path.home() / "AppData" / "Roaming" / "crepe"
    return Path.home() / ".config" / "crepe"
