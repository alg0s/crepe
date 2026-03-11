from __future__ import annotations

from pathlib import Path

import pytest

from crepe.config import load_config, validate_credentials


def test_validate_credentials_raises_when_missing(monkeypatch, tmp_path):
    monkeypatch.delenv("MS_TENANT_ID", raising=False)
    monkeypatch.delenv("MS_CLIENT_ID", raising=False)
    monkeypatch.delenv("MS_CLIENT_SECRET", raising=False)
    config = load_config(str(tmp_path / "data"), str(tmp_path / "data" / "crepe.sqlite3"))
    with pytest.raises(ValueError):
        validate_credentials(config)


def test_load_config_reads_managed_settings_env(monkeypatch, tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / ".env").write_text(
        "MS_TENANT_ID=tenant-from-file\nMS_CLIENT_ID=client-from-file\nMS_CLIENT_SECRET=secret-from-file\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CREPE_CONFIG_DIR", str(config_dir))
    monkeypatch.delenv("MS_TENANT_ID", raising=False)
    monkeypatch.delenv("MS_CLIENT_ID", raising=False)
    monkeypatch.delenv("MS_CLIENT_SECRET", raising=False)

    config = load_config(str(tmp_path / "data"), str(tmp_path / "data" / "crepe.sqlite3"))

    assert config.tenant_id == "tenant-from-file"
    assert config.client_id == "client-from-file"
    assert config.client_secret == "secret-from-file"
    assert config.credential_source == "managed"
    assert config.active_env_path == Path(config_dir / ".env").resolve()


def test_load_config_prefers_process_env_over_settings_file(monkeypatch, tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / ".env").write_text(
        "MS_TENANT_ID=tenant-from-file\nMS_CLIENT_ID=client-from-file\nMS_CLIENT_SECRET=secret-from-file\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CREPE_CONFIG_DIR", str(config_dir))
    monkeypatch.setenv("MS_CLIENT_SECRET", "secret-from-env")

    config = load_config(str(tmp_path / "data"), str(tmp_path / "data" / "crepe.sqlite3"))

    assert config.client_secret == "secret-from-env"
