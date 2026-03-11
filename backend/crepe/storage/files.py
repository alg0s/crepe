from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from crepe.config import Config


def sanitize_for_filename(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value)[:120]


@dataclass(slots=True)
class RunPaths:
    run_id: str
    raw_dir: Path
    normalized_dir: Path
    processed_dir: Path
    reports_dir: Path

    def ensure(self) -> None:
        for path in (self.raw_dir, self.normalized_dir, self.processed_dir, self.reports_dir):
            path.mkdir(parents=True, exist_ok=True)


def build_run_paths(config: Config, run_id: str) -> RunPaths:
    paths = RunPaths(
        run_id=run_id,
        raw_dir=config.raw_root / run_id,
        normalized_dir=config.normalized_root / run_id,
        processed_dir=config.processed_root / run_id,
        reports_dir=config.reports_root / run_id,
    )
    paths.ensure()
    return paths

