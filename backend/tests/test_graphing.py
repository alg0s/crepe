from __future__ import annotations

from crepe.analysis.clustering import cluster_conversations
from crepe.analysis.conversations import build_conversations
from crepe.analysis.graphing import build_graph_artifacts
from crepe.normalize.entities import normalize_entities


def test_graph_metrics_are_generated(sample_run):
    _, run_paths, _ = sample_run
    frames = normalize_entities(run_paths)
    conversations = build_conversations(frames["messages"], chat_gap_minutes=120)
    conversation_clusters, _ = cluster_conversations(conversations, 3)
    nodes, edges, metrics = build_graph_artifacts(
        conversations,
        frames["messages"],
        frames["channels"],
        frames["teams"],
        conversation_clusters,
    )
    assert not nodes.empty
    assert not edges.empty
    assert not metrics.empty
    assert {"degree_centrality", "betweenness_centrality", "pagerank"}.issubset(metrics.columns)

