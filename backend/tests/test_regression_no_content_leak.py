from __future__ import annotations

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from crepe.api.app import create_app
from crepe.storage.files import build_run_paths


@pytest.mark.regression
def test_api_strips_legacy_sensitive_columns(configured_env, run_db):
    run_id = run_db.create_run(run_id="legacy-sensitive")
    paths = build_run_paths(configured_env, run_id)
    paths.ensure()

    pd.DataFrame(
        [
            {
                "node_id": "user:u1",
                "node_type": "user",
                "label": "u1",
                "message_volume": 3,
                "team_id": "",
                "channel_id": "",
            }
        ]
    ).to_csv(paths.processed_dir / "graph_nodes.csv", index=False)
    pd.DataFrame(columns=["edge_id", "source", "target", "edge_type", "weight", "conversation_count"]).to_csv(
        paths.processed_dir / "graph_edges.csv",
        index=False,
    )
    pd.DataFrame([{"node_id": "user:u1", "degree_centrality": 0.1, "betweenness_centrality": 0.0, "pagerank": 0.2}]).to_csv(
        paths.processed_dir / "graph_metrics.csv",
        index=False,
    )
    pd.DataFrame(
        [
            {
                "conversation_id": "c1",
                "source_type": "chat",
                "chat_id": "chat-1",
                "team_id": "",
                "channel_id": "",
                "start_at": "2025-01-01T00:00:00Z",
                "end_at": "2025-01-01T00:01:00Z",
                "message_count": 1,
                "participant_count": 1,
                "participants": "u1",
                "message_ids": "m1",
                "combined_text": "should-be-redacted",
                "dominant_entities": "PERSON:u1",
            }
        ]
    ).to_csv(paths.processed_dir / "conversations.csv", index=False)
    pd.DataFrame(
        [
            {
                "message_id": "m1",
                "source_type": "chat",
                "chat_id": "chat-1",
                "sender_id": "u1",
                "receiver_ids": "u2",
                "entity_ids": "PERSON:u1|PERSON:u2",
                "sentiment_score": 0.0,
                "sentiment_label": "neutral",
                "body_text": "should-be-redacted",
            }
        ]
    ).to_csv(paths.normalized_dir / "messages.csv", index=False)

    client = TestClient(create_app(configured_env))
    node_detail = client.get(f"/api/runs/{run_id}/nodes/user:u1")
    assert node_detail.status_code == 200
    payload = node_detail.json()
    assert "body_text" not in str(payload)
    assert "combined_text" not in str(payload)

    conversations = client.get(f"/api/runs/{run_id}/conversations")
    assert conversations.status_code == 200
    assert "combined_text" not in str(conversations.json())
