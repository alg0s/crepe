from __future__ import annotations

from crepe.analysis.clustering import cluster_conversations
from crepe.analysis.conversations import build_conversations
from crepe.normalize.entities import normalize_entities


def test_cluster_summary_contains_keywords(sample_run):
    _, run_paths, _ = sample_run
    frames = normalize_entities(run_paths)
    conversations = build_conversations(frames["messages"], chat_gap_minutes=120)
    assignments, summary = cluster_conversations(conversations, 3)
    assert len(assignments) == len(conversations)
    assert not summary.empty
    assert "keywords" in summary.columns

