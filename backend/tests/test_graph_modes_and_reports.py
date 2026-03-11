from __future__ import annotations

import pandas as pd
import pytest

from crepe.analysis.graphing import derive_team_channel_flow, filter_graph
from crepe.analysis.taxonomy import build_taxonomy_markdown


@pytest.mark.unit
def test_filter_graph_modes_and_threshold():
    nodes = pd.DataFrame(
        [
            {"node_id": "user:u1", "node_type": "user", "label": "u1"},
            {"node_id": "user:u2", "node_type": "user", "label": "u2"},
            {"node_id": "channel:c1", "node_type": "channel", "label": "c1"},
            {"node_id": "cluster:0", "node_type": "cluster", "label": "cluster 0"},
        ]
    )
    edges = pd.DataFrame(
        [
            {"edge_id": "e1", "source": "user:u1", "target": "user:u2", "edge_type": "user_user_flow", "weight": 2, "conversation_count": 2},
            {"edge_id": "e2", "source": "user:u1", "target": "channel:c1", "edge_type": "user_channel_activity", "weight": 1, "conversation_count": 1},
            {"edge_id": "e3", "source": "cluster:0", "target": "channel:c1", "edge_type": "cluster_channel_affinity", "weight": 3, "conversation_count": 2},
        ]
    )

    user_nodes, user_edges = filter_graph(nodes, edges, mode="user_network", edge_threshold=2)
    assert len(user_edges) == 1
    assert user_edges.iloc[0]["edge_type"] == "user_user_flow"
    assert set(user_nodes["node_id"]) == {"user:u1", "user:u2"}

    theme_nodes, theme_edges = filter_graph(nodes, edges, mode="theme_network", edge_threshold=0)
    assert len(theme_edges) == 1
    assert set(theme_nodes["node_id"]) == {"cluster:0", "channel:c1"}


@pytest.mark.unit
def test_team_channel_flow_and_taxonomy_markdown():
    channels = pd.DataFrame(
        [
            {"team_id": "t1", "channel_id": "c1", "display_name": "Ops"},
            {"team_id": "t1", "channel_id": "c2", "display_name": "Sales"},
        ]
    )
    messages = pd.DataFrame(
        [
            {"channel_id": "c1"},
            {"channel_id": "c1"},
            {"channel_id": "c2"},
        ]
    )
    flow_nodes, flow_edges = derive_team_channel_flow(channels, messages)
    assert not flow_nodes.empty
    assert not flow_edges.empty
    assert flow_edges["weight"].sum() == 3

    summary = {"conversation_count": 4, "node_count": 6}
    recommendations = pd.DataFrame(
        [
            {
                "action": "merge",
                "proposed_channel_name": "Ops-Sales",
                "source_channels": "c1|c2",
                "rationale": "Overlap",
                "confidence": 0.7,
            }
        ]
    )
    cluster_summary = pd.DataFrame([{"cluster_id": 1, "keywords": "PERSON_u1", "conversation_count": 2, "top_channels": "c1"}])
    markdown = build_taxonomy_markdown(summary, recommendations, cluster_summary)
    assert "Proposed Teams Taxonomy" in markdown
    assert "Ops-Sales" in markdown
