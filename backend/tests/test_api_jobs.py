from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from crepe.api.app import create_app


@pytest.mark.integration
def test_active_job_endpoints_and_single_active_guard(configured_env, run_db):
    run_id = run_db.create_run(run_id="active-job")
    run_db.update_run(run_id, status="running", stage="extract")

    client = TestClient(create_app(configured_env))

    active = client.get("/api/jobs/active")
    assert active.status_code == 200
    payload = active.json()
    assert payload["is_running"] is True
    assert payload["active_run"]["run_id"] == run_id

    pause = client.post("/api/jobs/pause")
    assert pause.status_code == 200
    assert pause.json()["status"] == "paused"

    cancel = client.post("/api/jobs/cancel")
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "cancelled"

    next_id = run_db.create_run(run_id="running-job-2")
    run_db.update_run(next_id, status="running", stage="analyze")
    blocked = client.post("/api/runs", json={"pipeline": "demo", "background": False, "scope": {}})
    assert blocked.status_code == 409
    assert "Another job is active" in blocked.text
