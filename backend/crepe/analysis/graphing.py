from __future__ import annotations

from collections import Counter, defaultdict
from itertools import combinations
from typing import Iterable

import networkx as nx
import pandas as pd


def build_graph_artifacts(
    conversations: pd.DataFrame,
    messages: pd.DataFrame,
    channels: pd.DataFrame,
    teams: pd.DataFrame,
    conversation_clusters: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Build graph nodes, edges, and centrality metrics from conversation data."""

    nodes = _build_nodes(messages, channels, teams, conversation_clusters)
    edges = _build_edges(conversations, messages, channels, conversation_clusters)
    metrics = _build_metrics(nodes, edges)
    return nodes, edges, metrics


def _build_nodes(
    messages: pd.DataFrame,
    channels: pd.DataFrame,
    teams: pd.DataFrame,
    conversation_clusters: pd.DataFrame | None,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for sender_id, frame in messages.dropna(subset=["sender_id"]).groupby("sender_id"):
        rows.append(
            {
                "node_id": f"user:{sender_id}",
                "node_type": "user",
                "label": frame["sender_name"].dropna().iloc[0] if frame["sender_name"].dropna().any() else sender_id,
                "message_volume": int(len(frame)),
                "team_id": None,
                "channel_id": None,
            }
        )
    if not channels.empty:
        for record in channels.to_dict(orient="records"):
            rows.append(
                {
                    "node_id": f"channel:{record['channel_id']}",
                    "node_type": "channel",
                    "label": record.get("display_name") or record["channel_id"],
                    "message_volume": int((messages["channel_id"] == record["channel_id"]).sum()) if not messages.empty else 0,
                    "team_id": record.get("team_id"),
                    "channel_id": record["channel_id"],
                }
            )
    if not teams.empty:
        for record in teams.to_dict(orient="records"):
            rows.append(
                {
                    "node_id": f"team:{record['team_id']}",
                    "node_type": "team",
                    "label": record.get("display_name") or record["team_id"],
                    "message_volume": int((messages["team_id"] == record["team_id"]).sum()) if not messages.empty else 0,
                    "team_id": record["team_id"],
                    "channel_id": None,
                }
            )
    if conversation_clusters is not None and not conversation_clusters.empty:
        cluster_counts = conversation_clusters["cluster_id"].value_counts().to_dict()
        for cluster_id, count in cluster_counts.items():
            rows.append(
                {
                    "node_id": f"cluster:{cluster_id}",
                    "node_type": "cluster",
                    "label": f"Cluster {cluster_id}",
                    "message_volume": int(count),
                    "team_id": None,
                    "channel_id": None,
                }
            )
    return pd.DataFrame(rows).drop_duplicates(subset=["node_id"])


def _build_edges(
    conversations: pd.DataFrame,
    messages: pd.DataFrame,
    channels: pd.DataFrame,
    conversation_clusters: pd.DataFrame | None,
) -> pd.DataFrame:
    counters: dict[tuple[str, str, str], Counter[str]] = defaultdict(Counter)

    message_lookup = messages.set_index("message_id").to_dict(orient="index") if not messages.empty else {}

    for record in messages.to_dict(orient="records"):
        sender_id = record.get("sender_id")
        if not sender_id:
            continue
        for receiver_id in _split_ids(record.get("receiver_ids")):
            if receiver_id == sender_id:
                continue
            key = (f"user:{sender_id}", f"user:{receiver_id}", "user_user_flow")
            counters[key]["weight"] += 1
            counters[key]["conversation_count"] += 1
        channel_id = record.get("channel_id")
        if channel_id:
            key = (f"user:{sender_id}", f"channel:{channel_id}", "user_channel_activity")
            counters[key]["weight"] += 1
            counters[key]["conversation_count"] += 1
        reply_to_id = record.get("reply_to_id")
        if reply_to_id and reply_to_id in message_lookup:
            target = message_lookup[reply_to_id].get("sender_id")
            if target and target != sender_id:
                key = (f"user:{sender_id}", f"user:{target}", "user_user_reply")
                counters[key]["weight"] += 1
                counters[key]["conversation_count"] += 1

    for record in conversations.to_dict(orient="records"):
        participants = _split_ids(record.get("participants"))
        for first, second in combinations(sorted(set(participants)), 2):
            key = (f"user:{first}", f"user:{second}", "user_user_coparticipation")
            counters[key]["weight"] += 1
            counters[key]["conversation_count"] += 1

    channel_participants: dict[str, set[str]] = defaultdict(set)
    for record in messages.dropna(subset=["channel_id", "sender_id"]).to_dict(orient="records"):
        channel_participants[str(record["channel_id"])].add(str(record["sender_id"]))
    for first, second in combinations(sorted(channel_participants.keys()), 2):
        overlap = channel_participants[first] & channel_participants[second]
        if overlap:
            key = (f"channel:{first}", f"channel:{second}", "channel_channel_overlap")
            counters[key]["weight"] += len(overlap)
            counters[key]["conversation_count"] += 1

    if conversation_clusters is not None and not conversation_clusters.empty:
        merged = conversations.merge(conversation_clusters, on="conversation_id", how="left")
        for (cluster_id, channel_id), frame in merged.dropna(subset=["cluster_id", "channel_id"]).groupby(["cluster_id", "channel_id"]):
            key = (f"cluster:{int(cluster_id)}", f"channel:{channel_id}", "cluster_channel_affinity")
            counters[key]["weight"] += int(frame["message_count"].sum())
            counters[key]["conversation_count"] += int(len(frame))

    rows = []
    for (source, target, edge_type), counts in counters.items():
        rows.append(
            {
                "edge_id": f"{edge_type}:{source}->{target}",
                "source": source,
                "target": target,
                "edge_type": edge_type,
                "weight": float(counts["weight"]),
                "conversation_count": int(counts["conversation_count"]),
            }
        )
    return pd.DataFrame(rows)


def _build_metrics(nodes: pd.DataFrame, edges: pd.DataFrame) -> pd.DataFrame:
    graph = nx.DiGraph()
    for record in nodes.to_dict(orient="records"):
        graph.add_node(record["node_id"], node_type=record["node_type"], label=record["label"])
    for record in edges.to_dict(orient="records"):
        graph.add_edge(record["source"], record["target"], weight=record["weight"], edge_type=record["edge_type"])
    if graph.number_of_nodes() == 0:
        return pd.DataFrame(columns=["node_id", "degree_centrality", "betweenness_centrality", "pagerank"])
    degree = nx.degree_centrality(graph)
    betweenness = nx.betweenness_centrality(graph, weight="weight") if graph.number_of_edges() else {node: 0.0 for node in graph.nodes}
    pagerank = nx.pagerank(graph, weight="weight") if graph.number_of_edges() else {node: 0.0 for node in graph.nodes}
    return pd.DataFrame(
        [
            {
                "node_id": node,
                "degree_centrality": degree.get(node, 0.0),
                "betweenness_centrality": betweenness.get(node, 0.0),
                "pagerank": pagerank.get(node, 0.0),
            }
            for node in graph.nodes
        ]
    )


def filter_graph(
    nodes: pd.DataFrame,
    edges: pd.DataFrame,
    *,
    mode: str,
    edge_threshold: float = 0.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    mode_map = {
        "user_network": {"user_user_reply", "user_user_coparticipation", "user_user_flow"},
        "channel_overlap": {"channel_channel_overlap"},
        "theme_network": {"cluster_channel_affinity"},
        "activity_network": {"user_channel_activity"},
        "all": set(edges["edge_type"].unique()) if not edges.empty else set(),
    }
    edge_types = mode_map.get(mode, mode_map["all"])
    filtered_edges = edges[(edges["edge_type"].isin(edge_types)) & (edges["weight"] >= edge_threshold)].copy()
    visible_nodes = set(filtered_edges["source"]).union(set(filtered_edges["target"]))
    filtered_nodes = nodes[nodes["node_id"].isin(visible_nodes)].copy()
    return filtered_nodes, filtered_edges


def derive_team_channel_flow(channels: pd.DataFrame, messages: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    node_rows = []
    if channels.empty:
        return pd.DataFrame(columns=["node_id", "node_type", "label"]), pd.DataFrame(columns=["source", "target", "weight"])
    for team_id, frame in channels.groupby("team_id", dropna=False):
        if team_id:
            node_rows.append({"node_id": f"team:{team_id}", "node_type": "team", "label": str(team_id)})
        for channel in frame.to_dict(orient="records"):
            node_rows.append({"node_id": f"channel:{channel['channel_id']}", "node_type": "channel", "label": channel.get("display_name")})
            weight = int((messages["channel_id"] == channel["channel_id"]).sum()) if not messages.empty else 0
            rows.append(
                {
                    "edge_id": f"team_channel_flow:team:{team_id}->channel:{channel['channel_id']}",
                    "source": f"team:{team_id}",
                    "target": f"channel:{channel['channel_id']}",
                    "edge_type": "team_channel_flow",
                    "weight": weight,
                    "conversation_count": weight,
                }
            )
    return pd.DataFrame(node_rows).drop_duplicates(), pd.DataFrame(rows)


def _split_ids(value: object) -> list[str]:
    if value is None:
        return []
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return []
    return [item for item in text.split("|") if item and item.lower() != "nan"]
