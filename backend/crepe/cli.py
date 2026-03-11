from __future__ import annotations

import argparse
import json

from crepe.config import load_config
from crepe.logging_utils import configure_logging
from crepe.pipeline import PipelineRunner
from crepe.storage.db import RunDatabase


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="crepe Teams communication analyzer")
    parser.add_argument("--base-dir", default=None, help="Override artifact base directory")
    parser.add_argument("--db-path", default=None, help="Override SQLite database path")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command in ("extract", "normalize", "analyze", "suggest", "all", "demo"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--run-id", default=None)
        subparser.add_argument("--scope-json", default="{}", help="Optional scope payload for the run")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    config = load_config(args.base_dir, args.db_path)
    configure_logging(config.log_level)
    database = RunDatabase(config.db_path)
    runner = PipelineRunner(config, database)
    scope = json.loads(args.scope_json)

    if args.command == "extract":
        run_id = runner.run_extract(args.run_id, scope)
    elif args.command == "normalize":
        if not args.run_id:
            parser.error("normalize requires --run-id")
        run_id = runner.run_normalize(args.run_id)
    elif args.command == "analyze":
        if not args.run_id:
            parser.error("analyze requires --run-id")
        run_id = runner.run_analyze(args.run_id)
    elif args.command == "suggest":
        if not args.run_id:
            parser.error("suggest requires --run-id")
        run_id = runner.run_suggest(args.run_id)
    elif args.command == "demo":
        run_id = runner.run_demo(args.run_id, scope)
    else:
        run_id = runner.run_all(args.run_id, scope)
    print(run_id)


if __name__ == "__main__":
    main()
