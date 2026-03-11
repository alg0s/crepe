from __future__ import annotations

from crepe.analysis.conversations import build_conversations
from crepe.normalize.entities import normalize_entities


def test_chat_gap_segmentation_and_channel_threading(sample_run):
    _, run_paths, _ = sample_run
    frames = normalize_entities(run_paths)
    conversations = build_conversations(frames["messages"], chat_gap_minutes=120)
    channel_conversations = conversations[conversations["source_type"] == "channel"]
    chat_conversations = conversations[conversations["source_type"] == "chat"]
    assert len(channel_conversations) == 3
    assert len(chat_conversations) == 2

