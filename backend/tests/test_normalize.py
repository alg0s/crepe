from __future__ import annotations

from crepe.normalize.entities import normalize_entities


def test_normalize_entities_creates_flat_outputs(sample_run):
    run_id, run_db = sample_run
    frames = normalize_entities(run_db, run_id)
    assert "messages" in frames
    assert len(frames["messages"]) == 9
    assert "entity_ids" in frames["messages"].columns
    assert "ner_entities" in frames["messages"].columns
    assert "sentiment_score" in frames["messages"].columns
    assert "receiver_ids" in frames["messages"].columns
    assert "body_text" not in frames["messages"].columns
    assert not run_db.read_dataset(run_id, "messages").empty
