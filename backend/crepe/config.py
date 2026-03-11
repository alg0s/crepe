from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Config:
    tenant_id: str
    client_id: str
    client_secret: str
    base_dir: Path
    db_path: Path
    cluster_count: int = 6
    chat_gap_minutes: int = 120
    request_timeout_seconds: float = 30.0
    max_retries: int = 4
    log_level: str = "INFO"
    privacy_fail_on_content: bool = True

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
    config = Config(
        tenant_id=os.getenv("MS_TENANT_ID", ""),
        client_id=os.getenv("MS_CLIENT_ID", ""),
        client_secret=os.getenv("MS_CLIENT_SECRET", ""),
        base_dir=base,
        db_path=database_path,
        cluster_count=int(os.getenv("CREPE_CLUSTER_COUNT", "6")),
        chat_gap_minutes=int(os.getenv("CREPE_CHAT_GAP_MINUTES", "120")),
        request_timeout_seconds=float(os.getenv("CREPE_REQUEST_TIMEOUT_SECONDS", "30")),
        max_retries=int(os.getenv("CREPE_MAX_RETRIES", "4")),
        log_level=os.getenv("CREPE_LOG_LEVEL", "INFO"),
        privacy_fail_on_content=os.getenv("CREPE_PRIVACY_FAIL_ON_CONTENT", "1").lower() not in {"0", "false", "no"},
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
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
