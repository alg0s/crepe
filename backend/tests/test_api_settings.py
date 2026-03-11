from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from crepe.api.app import create_app


@pytest.mark.integration
def test_settings_endpoints_manage_non_secret_payloads(configured_env, monkeypatch):
    client = TestClient(create_app(configured_env))

    get_resp = client.get("/api/settings")
    assert get_resp.status_code == 200
    initial_payload = get_resp.json()
    assert initial_payload["credential_source"] in {"managed", "external_env"}
    assert "secret" not in json.dumps(initial_payload)

    put_resp = client.put(
        "/api/settings",
        json={
            "tenant_id": "tenant-updated",
            "client_id": "client-updated",
            "client_secret": "secret-updated",
        },
    )
    assert put_resp.status_code == 200
    updated_payload = put_resp.json()
    assert updated_payload["graph_auth_configured"] is True
    assert updated_payload["managed_credentials"]["MS_CLIENT_SECRET"] is True
    assert "secret-updated" not in json.dumps(updated_payload)

    status_resp = client.get("/api/system/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["credential_source"] == "managed"

    class FakeAuthenticator:
        def __init__(self, *_args, **_kwargs):
            pass

        def get_access_token(self):
            return "token"

    monkeypatch.setattr("crepe.api.app.GraphAuthenticator", FakeAuthenticator)
    test_resp = client.post("/api/settings/test-graph")
    assert test_resp.status_code == 200
    assert test_resp.json()["ok"] is True
