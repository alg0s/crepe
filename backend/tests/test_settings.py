from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from crepe.settings import SettingsManager


@pytest.mark.unit
def test_settings_manager_upsert_managed_writes_env(tmp_path):
    manager = SettingsManager(tmp_path / "cfg")
    state = manager.upsert(
        credential_source="managed",
        external_env_path=None,
        credential_updates={
            "MS_TENANT_ID": "tenant",
            "MS_CLIENT_ID": "client",
            "MS_CLIENT_SECRET": "secret",
        },
    )
    assert state.credential_source == "managed"
    values = manager.read_env_file(manager.managed_env_path)
    assert values["MS_TENANT_ID"] == "tenant"
    assert values["MS_CLIENT_ID"] == "client"
    assert values["MS_CLIENT_SECRET"] == "secret"
    if os.name != "nt":
        mode = stat.S_IMODE(manager.managed_env_path.stat().st_mode)
        assert mode == 0o600


@pytest.mark.unit
def test_settings_manager_external_source_requires_path(tmp_path):
    manager = SettingsManager(tmp_path / "cfg")
    with pytest.raises(ValueError):
        manager.upsert(credential_source="external_env", external_env_path=None, credential_updates=None)


@pytest.mark.unit
def test_settings_manager_resolves_external_env_credentials(tmp_path):
    manager = SettingsManager(tmp_path / "cfg")
    external = tmp_path / "external.env"
    external.write_text(
        "MS_TENANT_ID=tenant-ext\nMS_CLIENT_ID=client-ext\nMS_CLIENT_SECRET=secret-ext\n",
        encoding="utf-8",
    )

    manager.upsert(credential_source="external_env", external_env_path=str(external), credential_updates=None)
    resolved, state, active_path = manager.resolve_credentials()

    assert state.credential_source == "external_env"
    assert active_path == Path(external).resolve()
    assert resolved["MS_TENANT_ID"] == "tenant-ext"
    assert resolved["MS_CLIENT_ID"] == "client-ext"
    assert resolved["MS_CLIENT_SECRET"] == "secret-ext"
