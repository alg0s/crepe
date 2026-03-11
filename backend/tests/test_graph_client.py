from __future__ import annotations

import httpx

from crepe.graph_client import GraphClient
from crepe.storage.files import build_run_paths


class FakeHttpClient:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def get(self, path, params=None):
        self.calls.append((path, params))
        return self.responses.pop(0)

    def close(self):
        return None


def _response(status_code: int, payload: dict, headers: dict | None = None):
    request = httpx.Request("GET", "https://graph.microsoft.com/v1.0/users")
    return httpx.Response(status_code, json=payload, headers=headers, request=request)


def test_graph_client_paginates_and_writes_raw(configured_env, run_db):
    run_id = run_db.create_run(run_id="graph-client")
    run_paths = build_run_paths(configured_env, run_id)
    client = GraphClient(configured_env, "token", run_paths)
    client.client = FakeHttpClient(
        [
            _response(200, {"value": [{"id": "1"}], "@odata.nextLink": "https://graph.microsoft.com/v1.0/users?$skip=1"}),
            _response(200, {"value": [{"id": "2"}]}),
        ]
    )
    values = client.get_paginated("/users", "users")
    assert [row["id"] for row in values] == ["1", "2"]
    assert len(list((run_paths.raw_dir / "users").glob("*.json"))) == 2


def test_graph_client_retries_transient_errors(configured_env, run_db, monkeypatch):
    run_id = run_db.create_run(run_id="graph-retry")
    run_paths = build_run_paths(configured_env, run_id)
    client = GraphClient(configured_env, "token", run_paths)
    client.client = FakeHttpClient(
        [
            _response(429, {"value": []}, headers={"Retry-After": "0"}),
            _response(200, {"value": [{"id": "1"}]}),
        ]
    )
    monkeypatch.setattr("crepe.graph_client.time.sleep", lambda *_: None)
    values = client.get_paginated("/users", "users")
    assert values == [{"id": "1"}]

