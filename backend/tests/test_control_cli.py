from __future__ import annotations

import pytest

from crepe import control_cli
from crepe.storage.db import RunDatabase


@pytest.mark.unit
def test_control_cli_pause_and_resume(monkeypatch, tmp_path, capsys):
    base_dir = tmp_path / "data"
    db_path = base_dir / "crepe.sqlite3"
    base_dir.mkdir(parents=True, exist_ok=True)
    db = RunDatabase(db_path)
    run_id = db.create_run(run_id="control-run")
    db.update_run(run_id, status="running", stage="extract")

    monkeypatch.setattr(
        "sys.argv",
        [
            "crepe-control",
            "--base-dir",
            str(base_dir),
            "--db-path",
            str(db_path),
            "pause",
        ],
    )
    control_cli.main()
    assert db.get_run(run_id).status == "paused"

    monkeypatch.setattr(
        "sys.argv",
        [
            "crepe-control",
            "--base-dir",
            str(base_dir),
            "--db-path",
            str(db_path),
            "resume",
        ],
    )
    control_cli.main()
    assert db.get_run(run_id).status == "created"

    monkeypatch.setattr(
        "sys.argv",
        [
            "crepe-control",
            "--base-dir",
            str(base_dir),
            "--db-path",
            str(db_path),
            "status",
            "--limit",
            "5",
        ],
    )
    control_cli.main()
    out = capsys.readouterr().out
    assert "control-run" in out
    assert "Running: no" in out
