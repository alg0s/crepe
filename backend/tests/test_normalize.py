from __future__ import annotations

from crepe.normalize.entities import normalize_entities


def test_normalize_entities_creates_flat_outputs(sample_run):
    _, run_paths, _ = sample_run
    frames = normalize_entities(run_paths)
    assert "messages" in frames
    assert len(frames["messages"]) == 9
    assert "Need feed pricing update" in frames["messages"]["body_text"].tolist()
    assert (run_paths.normalized_dir / "messages.csv").exists()

