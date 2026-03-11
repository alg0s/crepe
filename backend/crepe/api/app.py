from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from crepe.analysis.graphing import derive_team_channel_flow, filter_graph
from crepe.config import Config, load_config
from crepe.logging_utils import configure_logging
from crepe.pipeline import PipelineRunner
from crepe.storage.db import RunDatabase
from crepe.storage.files import build_run_paths


class RunCreateRequest(BaseModel):
    run_id: str | None = None
    scope: dict[str, Any] = Field(default_factory=dict)
    pipeline: str = "all"
    background: bool = True


def create_app(config: Config | None = None) -> FastAPI:
    resolved_config = config or load_config()
    configure_logging(resolved_config.log_level)
    database = RunDatabase(resolved_config.db_path)
    runner = PipelineRunner(resolved_config, database)

    app = FastAPI(title="crepe API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/runs")
    def list_runs() -> list[dict[str, Any]]:
        return [_run_payload(run, database) for run in database.list_runs()]

    @app.post("/api/runs")
    def create_run(request: RunCreateRequest, background_tasks: BackgroundTasks) -> dict[str, Any]:
        run_id, _ = runner.ensure_run(request.run_id, request.scope)
        action = _pipeline_callable(runner, request.pipeline, run_id, request.scope)
        if request.background:
            background_tasks.add_task(action)
        else:
            action()
        run = database.get_run(run_id)
        return _run_payload(run, database)

    @app.get("/api/runs/{run_id}")
    def get_run(run_id: str) -> dict[str, Any]:
        run = database.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")
        return _run_payload(run, database)

    @app.get("/api/runs/{run_id}/summary")
    def get_summary(run_id: str) -> dict[str, Any]:
        run = _require_run(database, run_id)
        run_paths = build_run_paths(resolved_config, run_id)
        cluster_summary = _read_csv(run_paths.processed_dir / "cluster_summary.csv")
        recommendations = _read_csv(run_paths.processed_dir / "proposed_channels.csv")
        return {
            "run": _run_payload(run, database),
            "summary": run.summary(),
            "top_clusters": cluster_summary.sort_values("conversation_count", ascending=False).head(10).to_dict(orient="records"),
            "recommendation_count": int(len(recommendations)),
        }

    @app.get("/api/runs/{run_id}/graph")
    def get_graph(
        run_id: str,
        mode: str = Query(default="all"),
        edge_threshold: float = Query(default=0.0),
    ) -> dict[str, Any]:
        _require_run(database, run_id)
        run_paths = build_run_paths(resolved_config, run_id)
        nodes = _read_csv(run_paths.processed_dir / "graph_nodes.csv")
        edges = _read_csv(run_paths.processed_dir / "graph_edges.csv")
        messages = _read_csv(run_paths.normalized_dir / "messages.csv")
        channels = _read_csv(run_paths.normalized_dir / "channels.csv")
        if mode == "team_channel_flow":
            graph_nodes, graph_edges = derive_team_channel_flow(channels, messages)
        else:
            graph_nodes, graph_edges = filter_graph(nodes, edges, mode=mode, edge_threshold=edge_threshold)
        return {
            "run_id": run_id,
            "mode": mode,
            "nodes": graph_nodes.fillna("").to_dict(orient="records"),
            "links": graph_edges.fillna("").to_dict(orient="records"),
        }

    @app.get("/api/runs/{run_id}/nodes/{node_id}")
    def get_node_detail(run_id: str, node_id: str) -> dict[str, Any]:
        _require_run(database, run_id)
        run_paths = build_run_paths(resolved_config, run_id)
        nodes = _read_csv(run_paths.processed_dir / "graph_nodes.csv")
        metrics = _read_csv(run_paths.processed_dir / "graph_metrics.csv")
        conversations = _read_csv(run_paths.processed_dir / "conversations.csv")
        messages = _read_csv(run_paths.normalized_dir / "messages.csv")
        node = nodes[nodes["node_id"] == node_id]
        if node.empty:
            raise HTTPException(status_code=404, detail="Node not found")
        detail = node.iloc[0].to_dict()
        metric_row = metrics[metrics["node_id"] == node_id]
        related_conversations = _conversations_for_node(conversations, node_id)
        related_messages = _messages_for_node(messages, node_id)
        return {
            "node": detail,
            "metrics": metric_row.iloc[0].to_dict() if not metric_row.empty else {},
            "conversations": related_conversations.head(20).fillna("").to_dict(orient="records"),
            "messages": related_messages.head(25).fillna("").to_dict(orient="records"),
        }

    @app.get("/api/runs/{run_id}/edges/{edge_id}")
    def get_edge_detail(run_id: str, edge_id: str) -> dict[str, Any]:
        _require_run(database, run_id)
        run_paths = build_run_paths(resolved_config, run_id)
        edges = _read_csv(run_paths.processed_dir / "graph_edges.csv")
        conversations = _read_csv(run_paths.processed_dir / "conversations.csv")
        edge = edges[edges["edge_id"] == edge_id]
        if edge.empty:
            raise HTTPException(status_code=404, detail="Edge not found")
        record = edge.iloc[0].to_dict()
        related = _conversations_for_edge(conversations, record["source"], record["target"])
        return {"edge": record, "conversations": related.head(25).fillna("").to_dict(orient="records")}

    @app.get("/api/runs/{run_id}/conversations")
    def get_conversations(run_id: str) -> list[dict[str, Any]]:
        _require_run(database, run_id)
        conversations = _read_csv(build_run_paths(resolved_config, run_id).processed_dir / "conversations.csv")
        return conversations.fillna("").to_dict(orient="records")

    @app.get("/api/runs/{run_id}/clusters")
    def get_clusters(run_id: str) -> dict[str, Any]:
        _require_run(database, run_id)
        run_paths = build_run_paths(resolved_config, run_id)
        cluster_summary = _read_csv(run_paths.processed_dir / "cluster_summary.csv")
        conversation_clusters = _read_csv(run_paths.processed_dir / "conversation_clusters.csv")
        return {
            "summary": cluster_summary.fillna("").to_dict(orient="records"),
            "conversations": conversation_clusters.fillna("").to_dict(orient="records"),
        }

    @app.get("/api/runs/{run_id}/recommendations")
    def get_recommendations(run_id: str) -> dict[str, Any]:
        _require_run(database, run_id)
        run_paths = build_run_paths(resolved_config, run_id)
        recommendations = _read_csv(run_paths.processed_dir / "proposed_channels.csv")
        taxonomy_path = run_paths.reports_dir / "taxonomy.md"
        return {
            "recommendations": recommendations.fillna("").to_dict(orient="records"),
            "taxonomy_markdown": taxonomy_path.read_text(encoding="utf-8") if taxonomy_path.exists() else "",
        }

    return app


def _pipeline_callable(runner: PipelineRunner, pipeline: str, run_id: str, scope: dict[str, Any]):
    if pipeline == "extract":
        return lambda: runner.run_extract(run_id, scope)
    if pipeline == "normalize":
        return lambda: runner.run_normalize(run_id)
    if pipeline == "analyze":
        return lambda: runner.run_analyze(run_id)
    if pipeline == "suggest":
        return lambda: runner.run_suggest(run_id)
    if pipeline == "demo":
        return lambda: runner.run_demo(run_id, scope)
    return lambda: runner.run_all(run_id, scope)


def _require_run(database: RunDatabase, run_id: str):
    run = database.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


def _run_payload(run, database: RunDatabase) -> dict[str, Any]:
    return {
        "run_id": run.run_id,
        "status": run.status,
        "stage": run.stage,
        "created_at": run.created_at,
        "updated_at": run.updated_at,
        "scope": run.scope(),
        "summary": run.summary(),
        "error_message": run.error_message,
        "artifacts": database.list_artifacts(run.run_id),
    }


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    frame = pd.read_csv(path)
    return _strip_sensitive_columns(frame)


def _strip_sensitive_columns(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    forbidden = {
        "body_text",
        "body_html",
        "body_content_type",
        "combined_text",
        "subject",
        "content",
    }
    drop_cols = []
    for column in frame.columns:
        lowered = column.lower()
        if lowered in forbidden or lowered.startswith("body_") or lowered.endswith("_content"):
            drop_cols.append(column)
    return frame.drop(columns=drop_cols, errors="ignore")


def _conversations_for_node(conversations: pd.DataFrame, node_id: str) -> pd.DataFrame:
    if conversations.empty:
        return pd.DataFrame()
    if node_id.startswith("user:"):
        actor = node_id.split(":", 1)[1]
        return conversations[conversations["participants"].fillna("").str.contains(actor, regex=False)]
    if node_id.startswith("channel:"):
        channel_id = node_id.split(":", 1)[1]
        return conversations[conversations["channel_id"].astype(str) == channel_id]
    if node_id.startswith("cluster:"):
        return conversations
    if node_id.startswith("team:"):
        team_id = node_id.split(":", 1)[1]
        return conversations[conversations["team_id"].astype(str) == team_id]
    return pd.DataFrame()


def _messages_for_node(messages: pd.DataFrame, node_id: str) -> pd.DataFrame:
    if messages.empty:
        return pd.DataFrame()
    if node_id.startswith("user:"):
        actor = node_id.split(":", 1)[1]
        return messages[messages["sender_id"].astype(str) == actor]
    if node_id.startswith("channel:"):
        channel_id = node_id.split(":", 1)[1]
        return messages[messages["channel_id"].astype(str) == channel_id]
    if node_id.startswith("team:"):
        team_id = node_id.split(":", 1)[1]
        return messages[messages["team_id"].astype(str) == team_id]
    return pd.DataFrame()


def _conversations_for_edge(conversations: pd.DataFrame, source: str, target: str) -> pd.DataFrame:
    if conversations.empty:
        return pd.DataFrame()
    if source.startswith("user:") and target.startswith("user:"):
        first = source.split(":", 1)[1]
        second = target.split(":", 1)[1]
        mask = conversations["participants"].fillna("").str.contains(first, regex=False) & conversations["participants"].fillna("").str.contains(second, regex=False)
        return conversations[mask]
    if source.startswith("user:") and target.startswith("channel:"):
        actor = source.split(":", 1)[1]
        channel_id = target.split(":", 1)[1]
        mask = conversations["participants"].fillna("").str.contains(actor, regex=False) & (conversations["channel_id"].astype(str) == channel_id)
        return conversations[mask]
    if source.startswith("cluster:") and target.startswith("channel:"):
        channel_id = target.split(":", 1)[1]
        return conversations[conversations["channel_id"].astype(str) == channel_id]
    return conversations.head(25)
