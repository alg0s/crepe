from __future__ import annotations

from pathlib import Path

import pytest

from crepe.storage.db import RunDatabase


@pytest.mark.unit
def test_run_database_create_update_and_artifacts(tmp_path):
    db = RunDatabase(tmp_path / "runs.sqlite3")
    run_id = db.create_run(scope={"scope": "demo"})

    run = db.get_run(run_id)
    assert run is not None
    assert run.status == "created"
    assert run.scope() == {"scope": "demo"}

    db.update_run(run_id, status="running", stage="extract", summary={"count": 2})
    updated = db.get_run(run_id)
    assert updated is not None
    assert updated.status == "running"
    assert updated.stage == "extract"
    assert updated.summary() == {"count": 2}

    db.add_artifact(run_id, "extract", "users.json", Path("/tmp/users.json"))
    artifacts = db.list_artifacts(run_id)
    assert len(artifacts) == 1
    assert artifacts[0]["name"] == "users.json"


@pytest.mark.unit
def test_run_database_update_unknown_run_raises(tmp_path):
    db = RunDatabase(tmp_path / "runs.sqlite3")
    with pytest.raises(KeyError):
        db.update_run("missing-run", status="failed")
