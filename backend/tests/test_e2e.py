from __future__ import annotations

from fastapi.testclient import TestClient

from crepe.api.app import create_app
from crepe.pipeline import PipelineRunner


def test_fixture_run_end_to_end(sample_run, configured_env, run_db):
    run_id, run_paths, _ = sample_run
    runner = PipelineRunner(configured_env, run_db)
    runner.run_normalize(run_id)
    runner.run_analyze(run_id)
    runner.run_suggest(run_id)

    assert (run_paths.processed_dir / "graph_edges.csv").exists()
    assert (run_paths.processed_dir / "proposed_channels.csv").exists()
    assert (run_paths.reports_dir / "summary.md").exists()

    client = TestClient(create_app(configured_env))
    summary_response = client.get(f"/api/runs/{run_id}/summary")
    assert summary_response.status_code == 200
    recommendations_response = client.get(f"/api/runs/{run_id}/recommendations")
    assert recommendations_response.status_code == 200
    assert recommendations_response.json()["recommendations"]
