from __future__ import annotations

import pytest

from crepe.pipeline import PipelineRunner


@pytest.mark.integration
def test_paused_run_is_not_executed(configured_env, run_db):
    run_id = run_db.create_run(run_id="paused-run")
    run_db.update_run(run_id, status="paused", stage="extract", error_message="Paused by operator via CLI")

    runner = PipelineRunner(configured_env, run_db)
    result = runner.run_normalize(run_id)

    assert result == run_id
    record = run_db.get_run(run_id)
    assert record.status == "paused"
    assert record.stage == "extract"
