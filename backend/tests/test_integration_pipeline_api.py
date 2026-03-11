from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from crepe.api.app import create_app
from crepe.pipeline import PipelineRunner


@pytest.mark.integration
def test_demo_pipeline_and_api_metadata_end_to_end(configured_env, run_db):
    runner = PipelineRunner(configured_env, run_db)
    run_id = runner.run_demo(run_id="integration-demo")

    client = TestClient(create_app(configured_env))
    graph = client.get(f"/api/runs/{run_id}/graph", params={"mode": "user_network"})
    assert graph.status_code == 200
    payload = graph.json()
    assert payload["nodes"]
    assert payload["links"]
    assert any(link["edge_type"] == "user_user_flow" for link in payload["links"])

    first_node_id = payload["nodes"][0]["node_id"]
    node_detail = client.get(f"/api/runs/{run_id}/nodes/{first_node_id}")
    assert node_detail.status_code == 200
    node_payload = node_detail.json()
    assert "messages" in node_payload
    if node_payload["messages"]:
        first_message = node_payload["messages"][0]
        assert "receiver_ids" in first_message
        assert "entity_ids" in first_message
        assert "sentiment_label" in first_message
        assert "body_text" not in first_message
        assert "combined_text" not in first_message

    clusters = client.get(f"/api/runs/{run_id}/clusters")
    assert clusters.status_code == 200
    assert "summary" in clusters.json()
