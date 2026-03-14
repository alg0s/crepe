from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from crepe.settings import SettingsManager


@dataclass(slots=True)
class Config:
    tenant_id: str
    client_id: str
    client_secret: str
    base_dir: Path
    db_path: Path
    cluster_count: int = 6
    chat_gap_minutes: int = 120
    request_timeout_seconds: float = 120.0
    max_retries: int = 4
    log_level: str = "INFO"
    privacy_fail_on_content: bool = True
    ner_enabled: bool = True
    sentiment_mode: str = "hybrid"
    nlp_language: str = "en"
    nlp_strict: bool = True
    credential_source: str = "managed"
    external_env_path: str | None = None
    managed_env_path: Path | None = None
    active_env_path: Path | None = None

    @property
    def raw_root(self) -> Path:
        return self.base_dir / "raw"

    @property
    def normalized_root(self) -> Path:
        return self.base_dir / "normalized"

    @property
    def processed_root(self) -> Path:
        return self.base_dir / "processed"

    @property
    def reports_root(self) -> Path:
        return self.base_dir / "reports"

    def ensure_directories(self) -> None:
        for path in (
            self.base_dir,
            self.raw_root,
            self.normalized_root,
            self.processed_root,
            self.reports_root,
            self.db_path.parent,
        ):
            path.mkdir(parents=True, exist_ok=True)


def load_config(base_dir: str | None = None, db_path: str | None = None) -> Config:
    base = Path(base_dir or os.getenv("CREPE_BASE_DIR", "../data")).expanduser().resolve()
    database_path = Path(db_path or os.getenv("CREPE_DB_PATH", base / "crepe.sqlite3")).expanduser().resolve()
    settings_manager = SettingsManager()
    credentials, state, source_path = settings_manager.resolve_credentials()
    config = Config(
        tenant_id=credentials.get("MS_TENANT_ID", ""),
        client_id=credentials.get("MS_CLIENT_ID", ""),
        client_secret=credentials.get("MS_CLIENT_SECRET", ""),
        base_dir=base,
        db_path=database_path,
        cluster_count=int(os.getenv("CREPE_CLUSTER_COUNT", "6")),
        chat_gap_minutes=int(os.getenv("CREPE_CHAT_GAP_MINUTES", "120")),
        request_timeout_seconds=float(os.getenv("CREPE_REQUEST_TIMEOUT_SECONDS", "120")),
        max_retries=int(os.getenv("CREPE_MAX_RETRIES", "4")),
        log_level=os.getenv("CREPE_LOG_LEVEL", "INFO"),
        privacy_fail_on_content=os.getenv("CREPE_PRIVACY_FAIL_ON_CONTENT", "1").lower() not in {"0", "false", "no"},
        ner_enabled=os.getenv("CREPE_NER_ENABLED", "1").lower() not in {"0", "false", "no"},
        sentiment_mode=os.getenv("CREPE_SENTIMENT_MODE", "hybrid").lower(),
        nlp_language=os.getenv("CREPE_NLP_LANGUAGE", "en").lower(),
        nlp_strict=os.getenv("CREPE_NLP_STRICT", "1").lower() not in {"0", "false", "no"},
        credential_source=state.credential_source,
        external_env_path=state.external_env_path,
        managed_env_path=settings_manager.managed_env_path,
        active_env_path=source_path,
    )
    config.ensure_directories()
    return config


def validate_credentials(config: Config) -> None:
    missing = [
        name
        for name, value in (
            ("MS_TENANT_ID", config.tenant_id),
            ("MS_CLIENT_ID", config.client_id),
            ("MS_CLIENT_SECRET", config.client_secret),
        )
        if not value
    ]
    if missing:
        raise ValueError(f"Missing required credentials: {', '.join(missing)}")
