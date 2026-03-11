from __future__ import annotations

from crepe.analysis.clustering import cluster_conversations
from crepe.analysis.conversations import build_conversations
from crepe.analysis.taxonomy import build_channel_taxonomy
from crepe.normalize.entities import normalize_entities


def test_taxonomy_produces_recommendations(sample_run):
    _, run_paths, _ = sample_run
    frames = normalize_entities(run_paths)
    conversations = build_conversations(frames["messages"], chat_gap_minutes=120)
    conversation_clusters, cluster_summary = cluster_conversations(conversations, 3)
    recommendations = build_channel_taxonomy(frames["channels"], conversations, conversation_clusters, cluster_summary)
    assert not recommendations.empty
    assert {"action", "proposed_channel_name", "source_channels"}.issubset(recommendations.columns)

