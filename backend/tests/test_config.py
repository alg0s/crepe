from __future__ import annotations

import pytest

from crepe.config import load_config, validate_credentials


def test_validate_credentials_raises_when_missing(monkeypatch, tmp_path):
    monkeypatch.delenv("MS_TENANT_ID", raising=False)
    monkeypatch.delenv("MS_CLIENT_ID", raising=False)
    monkeypatch.delenv("MS_CLIENT_SECRET", raising=False)
    config = load_config(str(tmp_path / "data"), str(tmp_path / "data" / "crepe.sqlite3"))
    with pytest.raises(ValueError):
        validate_credentials(config)

