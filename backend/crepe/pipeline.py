from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from crepe.analysis.clustering import cluster_conversations
from crepe.analysis.conversations import build_conversations
from crepe.analysis.graphing import build_graph_artifacts
from crepe.analysis.taxonomy import build_channel_taxonomy, build_taxonomy_markdown
from crepe.config import Config, validate_credentials
from crepe.demo_data import write_demo_raw_data
from crepe.extractors.channels import extract_channels
from crepe.extractors.chats import extract_chats
from crepe.extractors.messages import extract_channel_messages, extract_chat_messages
from crepe.extractors.teams import extract_teams
from crepe.extractors.users import extract_users
from crepe.graph_auth import GraphAuthenticator
from crepe.graph_client import GraphClient
from crepe.normalize.entities import normalize_entities
from crepe.storage.db import RunDatabase
from crepe.storage.files import RunPaths, build_run_paths

LOGGER = logging.getLogger(__name__)


class PipelineRunner:
    def __init__(self, config: Config, database: RunDatabase) -> None:
        self.config = config
        self.database = database

    def ensure_run(self, run_id: str | None, scope: dict[str, Any] | None = None) -> tuple[str, RunPaths]:
        resolved_run_id = run_id or self.database.create_run(scope=scope)
        if self.database.get_run(resolved_run_id) is None:
            self.database.create_run(run_id=resolved_run_id, scope=scope)
        return resolved_run_id, build_run_paths(self.config, resolved_run_id)

    def run_extract(self, run_id: str | None = None, scope: dict[str, Any] | None = None) -> str:
        validate_credentials(self.config)
        run_id, run_paths = self.ensure_run(run_id, scope)
        self.database.update_run(run_id, status="running", stage="extract")
        auth = GraphAuthenticator(self.config)
        token = auth.get_access_token()
        try:
            with GraphClient(self.config, token, run_paths) as client:
                users = extract_users(client)
                teams = extract_teams(client)
                channels = extract_channels(client, teams)
                chats = extract_chats(client)
                extract_chat_messages(client, chats)
                extract_channel_messages(client, channels)
        except Exception as exc:
            self.database.update_run(run_id, status="failed", stage="extract", error_message=str(exc))
            raise
        self._register_tree("extract", run_paths.raw_dir, run_id)
        self.database.update_run(run_id, status="completed", stage="extract")
        return run_id

    def run_normalize(self, run_id: str) -> str:
        run_paths = build_run_paths(self.config, run_id)
        self.database.update_run(run_id, status="running", stage="normalize")
        try:
            frames = normalize_entities(run_paths)
            summary = {"normalized_tables": {name: int(len(frame)) for name, frame in frames.items()}}
        except Exception as exc:
            self.database.update_run(run_id, status="failed", stage="normalize", error_message=str(exc))
            raise
        self._register_tree("normalize", run_paths.normalized_dir, run_id)
        self.database.update_run(run_id, status="completed", stage="normalize", summary=summary)
        return run_id

    def run_analyze(self, run_id: str) -> str:
        run_paths = build_run_paths(self.config, run_id)
        self.database.update_run(run_id, status="running", stage="analyze")
        try:
            channels = _load_csv(run_paths.normalized_dir / "channels.csv")
            teams = _load_csv(run_paths.normalized_dir / "teams.csv")
            messages = _load_csv(run_paths.normalized_dir / "messages.csv")
            conversations = build_conversations(messages, self.config.chat_gap_minutes)
            conversation_clusters, cluster_summary = cluster_conversations(conversations, self.config.cluster_count)
            nodes, edges, metrics = build_graph_artifacts(conversations, messages, channels, teams, conversation_clusters)
            _write_frame(conversations, run_paths.processed_dir / "conversations.csv")
            _write_frame(conversation_clusters, run_paths.processed_dir / "conversation_clusters.csv")
            _write_frame(cluster_summary, run_paths.processed_dir / "cluster_summary.csv")
            _write_frame(nodes, run_paths.processed_dir / "graph_nodes.csv")
            _write_frame(edges, run_paths.processed_dir / "graph_edges.csv")
            _write_frame(metrics, run_paths.processed_dir / "graph_metrics.csv")
            summary = {
                "conversation_count": int(len(conversations)),
                "node_count": int(len(nodes)),
                "edge_count": int(len(edges)),
            }
            (run_paths.processed_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        except Exception as exc:
            self.database.update_run(run_id, status="failed", stage="analyze", error_message=str(exc))
            raise
        self._register_tree("analyze", run_paths.processed_dir, run_id)
        self.database.update_run(run_id, status="completed", stage="analyze", summary=summary)
        return run_id

    def run_suggest(self, run_id: str) -> str:
        run_paths = build_run_paths(self.config, run_id)
        self.database.update_run(run_id, status="running", stage="suggest")
        try:
            channels = _load_csv(run_paths.normalized_dir / "channels.csv")
            conversations = _load_csv(run_paths.processed_dir / "conversations.csv")
            conversation_clusters = _load_csv(run_paths.processed_dir / "conversation_clusters.csv")
            cluster_summary = _load_csv(run_paths.processed_dir / "cluster_summary.csv")
            summary = json.loads((run_paths.processed_dir / "summary.json").read_text(encoding="utf-8"))
            recommendations = build_channel_taxonomy(channels, conversations, conversation_clusters, cluster_summary)
            _write_frame(recommendations, run_paths.processed_dir / "proposed_channels.csv")
            markdown = build_taxonomy_markdown(summary, recommendations, cluster_summary)
            taxonomy_path = run_paths.reports_dir / "taxonomy.md"
            taxonomy_path.write_text(markdown, encoding="utf-8")
            report_path = run_paths.reports_dir / "summary.md"
            report_path.write_text(_build_summary_markdown(summary, recommendations, cluster_summary), encoding="utf-8")
        except Exception as exc:
            self.database.update_run(run_id, status="failed", stage="suggest", error_message=str(exc))
            raise
        self._register_tree("suggest", run_paths.reports_dir, run_id)
        self.database.add_artifact(run_id, "suggest", "proposed_channels.csv", run_paths.processed_dir / "proposed_channels.csv")
        self.database.update_run(
            run_id,
            status="completed",
            stage="suggest",
            summary={**summary, "recommendation_count": int(len(recommendations))},
        )
        return run_id

    def run_all(self, run_id: str | None = None, scope: dict[str, Any] | None = None) -> str:
        resolved_run_id = self.run_extract(run_id, scope)
        self.run_normalize(resolved_run_id)
        self.run_analyze(resolved_run_id)
        self.run_suggest(resolved_run_id)
        self.database.update_run(resolved_run_id, status="completed", stage="all")
        return resolved_run_id

    def run_demo(self, run_id: str | None = None, scope: dict[str, Any] | None = None) -> str:
        resolved_run_id, run_paths = self.ensure_run(run_id, scope or {"source": "demo"})
        self.database.update_run(resolved_run_id, status="running", stage="demo")
        try:
            write_demo_raw_data(run_paths)
            self._register_tree("demo", run_paths.raw_dir, resolved_run_id)
            self.run_normalize(resolved_run_id)
            self.run_analyze(resolved_run_id)
            self.run_suggest(resolved_run_id)
        except Exception as exc:
            self.database.update_run(resolved_run_id, status="failed", stage="demo", error_message=str(exc))
            raise
        self.database.update_run(
            resolved_run_id,
            status="completed",
            stage="demo",
            summary={**(self.database.get_run(resolved_run_id).summary()), "demo": True},
        )
        return resolved_run_id

    def _register_tree(self, stage: str, root: Path, run_id: str) -> None:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                self.database.add_artifact(run_id, stage, path.name, path)


def _write_frame(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, index=False)


def _load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _build_summary_markdown(summary: dict[str, Any], recommendations: pd.DataFrame, cluster_summary: pd.DataFrame) -> str:
    lines = [
        "# crepe summary",
        "",
        f"- Conversations: {summary.get('conversation_count', 0)}",
        f"- Graph nodes: {summary.get('node_count', 0)}",
        f"- Graph edges: {summary.get('edge_count', 0)}",
        f"- Recommendations: {len(recommendations)}",
        "",
        "## Cluster overview",
        "",
    ]
    for record in cluster_summary.sort_values("conversation_count", ascending=False).head(10).to_dict(orient="records"):
        lines.append(
            f"- Cluster {record['cluster_id']}: {record['keywords']} "
            f"({record['conversation_count']} conversations, participants: {record['top_participants'] or 'n/a'})"
        )
    lines.extend(["", "## Recommendation overview", ""])
    for record in recommendations.to_dict(orient="records"):
        lines.append(f"- {record['action']}: {record['proposed_channel_name']} -> {record['rationale']}")
    return "\n".join(lines) + "\n"
