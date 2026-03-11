from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from crepe.api.app import create_app
from crepe.pipeline import PipelineRunner


@pytest.mark.integration
def test_api_full_endpoint_surface(sample_run, configured_env, run_db):
    run_id, _, _ = sample_run
    runner = PipelineRunner(configured_env, run_db)
    runner.run_normalize(run_id)
    runner.run_analyze(run_id)
    runner.run_suggest(run_id)

    client = TestClient(create_app(configured_env))
    status_resp = client.get("/api/system/status")
    assert status_resp.status_code == 200
    status_payload = status_resp.json()
    assert status_payload["graph_auth_configured"] is True
    assert status_payload["credential_source"] == "managed"

    settings_resp = client.get("/api/settings")
    assert settings_resp.status_code == 200
    settings_payload = settings_resp.json()
    assert settings_payload["graph_auth_configured"] is True
    assert settings_payload["effective_credentials"]["MS_CLIENT_SECRET"] is True
    assert "secret" not in json.dumps(settings_payload)

    run_resp = client.get(f"/api/runs/{run_id}")
    assert run_resp.status_code == 200
    assert run_resp.json()["run_id"] == run_id

    summary_resp = client.get(f"/api/runs/{run_id}/summary")
    assert summary_resp.status_code == 200
    assert "summary" in summary_resp.json()

    graph_resp = client.get(f"/api/runs/{run_id}/graph", params={"mode": "theme_network", "edge_threshold": 0})
    assert graph_resp.status_code == 200
    graph_payload = graph_resp.json()
    assert "nodes" in graph_payload and "links" in graph_payload

    flow_resp = client.get(f"/api/runs/{run_id}/graph", params={"mode": "team_channel_flow"})
    assert flow_resp.status_code == 200

    conversations_resp = client.get(f"/api/runs/{run_id}/conversations")
    assert conversations_resp.status_code == 200
    conversations = conversations_resp.json()
    assert conversations

    first_conversation = conversations[0]
    first_node_id = "user:" + first_conversation["participants"].split("|")[0]
    node_resp = client.get(f"/api/runs/{run_id}/nodes/{first_node_id}")
    assert node_resp.status_code == 200
    assert "messages" in node_resp.json()

    edges = graph_payload["links"]
    if edges:
        edge_id = edges[0]["edge_id"]
        edge_resp = client.get(f"/api/runs/{run_id}/edges/{edge_id}")
        assert edge_resp.status_code == 200
        assert "conversations" in edge_resp.json()

    cluster_resp = client.get(f"/api/runs/{run_id}/clusters")
    assert cluster_resp.status_code == 200
    assert "summary" in cluster_resp.json()

    rec_resp = client.get(f"/api/runs/{run_id}/recommendations")
    assert rec_resp.status_code == 200
    assert "recommendations" in rec_resp.json()
    assert "taxonomy_markdown" in rec_resp.json()


@pytest.mark.integration
def test_api_post_run_demo_pipeline(configured_env, run_db):
    client = TestClient(create_app(configured_env))
    response = client.post(
        "/api/runs",
        json={"run_id": "api-demo-run", "pipeline": "demo", "background": False, "scope": {"source": "api"}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"] == "api-demo-run"
    detail = client.get("/api/runs/api-demo-run")
    assert detail.status_code == 200
    assert detail.json()["status"] in {"completed", "running"}
