from __future__ import annotations

from fastapi.testclient import TestClient

from crepe.api.app import create_app
from crepe.pipeline import PipelineRunner


def test_api_endpoints_return_run_and_graph(sample_run, configured_env, run_db):
    run_id, _, _ = sample_run
    runner = PipelineRunner(configured_env, run_db)
    runner.run_normalize(run_id)
    runner.run_analyze(run_id)
    runner.run_suggest(run_id)

    client = TestClient(create_app(configured_env))
    runs_response = client.get("/api/runs")
    assert runs_response.status_code == 200
    graph_response = client.get(f"/api/runs/{run_id}/graph", params={"mode": "user_network"})
    assert graph_response.status_code == 200
    payload = graph_response.json()
    assert "nodes" in payload
    assert "links" in payload

