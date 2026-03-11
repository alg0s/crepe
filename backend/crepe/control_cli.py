from __future__ import annotations

import argparse
import json

from crepe.config import load_config
from crepe.storage.db import RunDatabase, RunRecord


ACTIVE_STATUSES = ("running", "paused")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="crepe control CLI")
    parser.add_argument("--base-dir", default=None, help="Override artifact base directory")
    parser.add_argument("--db-path", default=None, help="Override SQLite database path")
    subparsers = parser.add_subparsers(dest="command", required=True)

    pause = subparsers.add_parser("pause", help="Pause the active run")
    pause.add_argument("--run-id", default=None, help="Optional run id override")

    cancel = subparsers.add_parser("cancel", help="Cancel the active run")
    cancel.add_argument("--run-id", default=None, help="Optional run id override")

    resume = subparsers.add_parser("resume", help="Resume the latest paused run")
    resume.add_argument("--run-id", default=None, help="Optional run id override")

    status = subparsers.add_parser("status", help="Show running/not running and recent run log")
    status.add_argument("--limit", type=int, default=10)
    status.add_argument("--json", action="store_true")
    return parser


def _resolve_target_run(database: RunDatabase, run_id: str | None, *, preferred_statuses: tuple[str, ...]) -> RunRecord | None:
    if run_id:
        return database.get_run(run_id)
    return database.latest_run_by_status(preferred_statuses)


def _run_log(database: RunDatabase, limit: int) -> list[dict[str, object]]:
    runs = database.list_runs()[: max(limit, 1)]
    return [
        {
            "run_id": run.run_id,
            "status": run.status,
            "stage": run.stage,
            "updated_at": run.updated_at,
            "scope": run.scope(),
            "error_message": run.error_message,
        }
        for run in runs
    ]


def _fail(message: str) -> None:
    raise SystemExit(message)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    config = load_config(args.base_dir, args.db_path)
    database = RunDatabase(config.db_path)

    if args.command == "pause":
        run = _resolve_target_run(database, args.run_id, preferred_statuses=("running",))
        if run is None:
            _fail("No running job found")
        if run.status != "running":
            _fail(f"Run {run.run_id} is not running (current status={run.status})")
        database.update_run(
            run.run_id,
            status="paused",
            stage=run.stage,
            error_message="Paused by operator via CLI",
        )
        print(f"Paused {run.run_id} at stage={run.stage}")
        return

    if args.command == "cancel":
        run = _resolve_target_run(database, args.run_id, preferred_statuses=ACTIVE_STATUSES)
        if run is None:
            _fail("No active job found")
        if run.status not in ACTIVE_STATUSES:
            _fail(f"Run {run.run_id} is not active (current status={run.status})")
        database.update_run(
            run.run_id,
            status="cancelled",
            stage=run.stage,
            error_message="Cancelled by operator via CLI",
        )
        print(f"Cancelled {run.run_id} at stage={run.stage}")
        return

    if args.command == "resume":
        run = _resolve_target_run(database, args.run_id, preferred_statuses=("paused",))
        if run is None:
            _fail("No paused job found")
        if run.status != "paused":
            _fail(f"Run {run.run_id} is not paused (current status={run.status})")
        database.update_run(run.run_id, status="created", error_message=None)
        print(f"Resumed {run.run_id}; you can re-run the pipeline.")
        return

    running_run = database.latest_run_by_status(("running",))
    active_run = running_run or database.latest_run_by_status(("paused",))
    payload = {
        "db_path": str(config.db_path),
        "is_running": running_run is not None,
        "active_run": {
            "run_id": active_run.run_id,
            "status": active_run.status,
            "stage": active_run.stage,
            "updated_at": active_run.updated_at,
        }
        if active_run
        else None,
        "runs": _run_log(database, args.limit),
    }

    if args.json:
        print(json.dumps(payload, indent=2))
        return

    print(f"DB: {payload['db_path']}")
    if payload["is_running"]:
        current = payload["active_run"]
        print(f"Running: yes ({current['run_id']} at stage={current['stage']})")
    else:
        print("Running: no")

    if not payload["runs"]:
        print("No runs found.")
        return

    print("\nrun_id | status | stage | updated_at")
    print("-" * 72)
    for item in payload["runs"]:
        print(f"{item['run_id']} | {item['status']} | {item['stage']} | {item['updated_at']}")


if __name__ == "__main__":
    main()
