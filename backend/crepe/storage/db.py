from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


@dataclass(slots=True)
class RunRecord:
    run_id: str
    status: str
    stage: str
    created_at: str
    updated_at: str
    scope_json: str
    error_message: str | None
    summary_json: str

    def summary(self) -> dict[str, Any]:
        return json.loads(self.summary_json or "{}")

    def scope(self) -> dict[str, Any]:
        return json.loads(self.scope_json or "{}")


class RunDatabase:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _init_db(self) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    scope_json TEXT NOT NULL,
                    error_message TEXT,
                    summary_json TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS artifacts (
                    artifact_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    name TEXT NOT NULL,
                    path TEXT NOT NULL
                )
                """
            )

    def create_run(self, run_id: str | None = None, scope: dict[str, Any] | None = None) -> str:
        resolved_run_id = run_id or f"run-{uuid4().hex[:12]}"
        now = utc_now()
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO runs (run_id, status, stage, created_at, updated_at, scope_json, error_message, summary_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (resolved_run_id, "created", "init", now, now, json.dumps(scope or {}), None, "{}"),
            )
        return resolved_run_id

    def update_run(
        self,
        run_id: str,
        *,
        status: str | None = None,
        stage: str | None = None,
        error_message: str | None = None,
        summary: dict[str, Any] | None = None,
    ) -> None:
        current = self.get_run(run_id)
        if current is None:
            raise KeyError(f"Unknown run_id: {run_id}")
        next_status = status or current.status
        next_stage = stage or current.stage
        next_error = error_message if error_message is not None else current.error_message
        next_summary = summary if summary is not None else current.summary()
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE runs
                SET status = ?, stage = ?, updated_at = ?, error_message = ?, summary_json = ?
                WHERE run_id = ?
                """,
                (
                    next_status,
                    next_stage,
                    utc_now(),
                    next_error,
                    json.dumps(next_summary),
                    run_id,
                ),
            )

    def add_artifact(self, run_id: str, stage: str, name: str, path: Path) -> None:
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO artifacts (run_id, stage, name, path) VALUES (?, ?, ?, ?)",
                (run_id, stage, name, str(path)),
            )

    def list_runs(self) -> list[RunRecord]:
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM runs ORDER BY created_at DESC").fetchall()
        return [RunRecord(**dict(row)) for row in rows]

    def get_run(self, run_id: str) -> RunRecord | None:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        return RunRecord(**dict(row)) if row else None

    def list_artifacts(self, run_id: str) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT stage, name, path FROM artifacts WHERE run_id = ? ORDER BY artifact_id",
                (run_id,),
            ).fetchall()
        return [dict(row) for row in rows]

