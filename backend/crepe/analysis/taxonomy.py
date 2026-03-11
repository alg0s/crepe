from __future__ import annotations

from collections import Counter
from itertools import combinations

import pandas as pd


def build_channel_taxonomy(
    channels: pd.DataFrame,
    conversations: pd.DataFrame,
    conversation_clusters: pd.DataFrame,
    cluster_summary: pd.DataFrame,
) -> pd.DataFrame:
    """Generate heuristic channel merge, split, and create recommendations."""

    columns = [
        "suggestion_id",
        "action",
        "proposed_channel_name",
        "team_id",
        "source_channels",
        "rationale",
        "confidence",
        "evidence_count",
    ]
    if channels.empty:
        return pd.DataFrame(columns=columns)
    merged = conversations.merge(conversation_clusters, on="conversation_id", how="left")
    merged["channel_id"] = merged["channel_id"].fillna("")
    participant_map = {
        channel_id: set("|".join(frame["participants"].fillna("")).split("|")) - {""}
        for channel_id, frame in merged.groupby("channel_id")
        if channel_id
    }
    cluster_map = {
        channel_id: Counter(frame["cluster_id"].dropna().astype(int).tolist())
        for channel_id, frame in merged.groupby("channel_id")
        if channel_id
    }
    rows: list[dict[str, object]] = []

    for first, second in combinations(sorted(participant_map.keys()), 2):
        participant_overlap = _jaccard(participant_map[first], participant_map[second])
        topic_overlap = _counter_overlap(cluster_map.get(first, Counter()), cluster_map.get(second, Counter()))
        if participant_overlap >= 0.3 and topic_overlap >= 0.3:
            rows.append(
                {
                    "suggestion_id": f"merge:{first}:{second}",
                    "action": "merge",
                    "proposed_channel_name": _merged_name(first, second, channels),
                    "team_id": _team_for_channels(channels, [first, second]),
                    "source_channels": "|".join([first, second]),
                    "rationale": f"High participant overlap ({participant_overlap:.2f}) and theme overlap ({topic_overlap:.2f}).",
                    "confidence": round((participant_overlap + topic_overlap) / 2, 2),
                    "evidence_count": int(sum(cluster_map[first].values()) + sum(cluster_map[second].values())),
                }
            )

    for channel_id, frame in merged.groupby("channel_id"):
        if not channel_id:
            continue
        cluster_counts = Counter(frame["cluster_id"].dropna().astype(int).tolist())
        total = len(frame)
        if total >= 6 and len(cluster_counts) >= 3:
            dominant_share = max(cluster_counts.values()) / total if total else 0
            if dominant_share < 0.6:
                rows.append(
                    {
                        "suggestion_id": f"split:{channel_id}",
                        "action": "split",
                        "proposed_channel_name": f"{_channel_name(channel_id, channels)}-focus",
                        "team_id": _team_for_channels(channels, [channel_id]),
                        "source_channels": channel_id,
                        "rationale": f"Channel has {total} conversations spanning {len(cluster_counts)} themes.",
                        "confidence": round(1 - dominant_share, 2),
                        "evidence_count": total,
                    }
                )

    for cluster_id, frame in merged.dropna(subset=["cluster_id"]).groupby("cluster_id"):
        channel_ids = sorted({channel for channel in frame["channel_id"].tolist() if channel})
        if len(channel_ids) >= 2 and len(frame) >= 2:
            summary_row = cluster_summary[cluster_summary["cluster_id"] == int(cluster_id)]
            keywords = summary_row["keywords"].iloc[0] if not summary_row.empty else "shared-work"
            rows.append(
                {
                    "suggestion_id": f"create:{int(cluster_id)}",
                    "action": "create",
                    "proposed_channel_name": _slug_to_name(keywords),
                    "team_id": _team_for_channels(channels, channel_ids),
                    "source_channels": "|".join(channel_ids),
                    "rationale": f"Recurring theme spans {len(channel_ids)} channels: {keywords}.",
                    "confidence": round(min(0.95, len(frame) / (len(channel_ids) * 4)), 2),
                    "evidence_count": int(len(frame)),
                }
            )
    recommendations = pd.DataFrame(rows, columns=columns)
    if recommendations.empty:
        busiest = merged[merged["channel_id"] != ""].groupby("channel_id").size().sort_values(ascending=False)
        if not busiest.empty:
            channel_id = str(busiest.index[0])
            recommendations = pd.DataFrame(
                [
                    {
                        "suggestion_id": f"review:{channel_id}",
                        "action": "review",
                        "proposed_channel_name": f"{_channel_name(channel_id, channels)}-review",
                        "team_id": _team_for_channels(channels, [channel_id]),
                        "source_channels": channel_id,
                        "rationale": "High activity channel with no clear merge/split candidate; review ownership and posting scope.",
                        "confidence": 0.4,
                        "evidence_count": int(busiest.iloc[0]),
                    }
                ],
                columns=columns,
            )
    return recommendations.drop_duplicates(subset=["suggestion_id"])


def build_taxonomy_markdown(summary: dict[str, int], recommendations: pd.DataFrame, cluster_summary: pd.DataFrame) -> str:
    lines = [
        "# Proposed Teams Taxonomy",
        "",
        f"- Conversations analyzed: {summary.get('conversation_count', 0)}",
        f"- Graph nodes: {summary.get('node_count', 0)}",
        f"- Recommendations: {len(recommendations)}",
        "",
        "## Top clusters",
        "",
    ]
    for record in cluster_summary.sort_values("conversation_count", ascending=False).head(10).to_dict(orient="records"):
        lines.append(
            f"- Cluster {record['cluster_id']}: {record['keywords']} "
            f"({record['conversation_count']} conversations, channels: {record['top_channels'] or 'n/a'})"
        )
    lines.extend(["", "## Proposed changes", ""])
    for record in recommendations.to_dict(orient="records"):
        lines.append(
            f"- [{record['action'].upper()}] `{record['proposed_channel_name']}` "
            f"from `{record['source_channels']}`. {record['rationale']} Confidence: {record['confidence']}."
        )
    return "\n".join(lines) + "\n"


def _jaccard(first: set[str], second: set[str]) -> float:
    if not first or not second:
        return 0.0
    return len(first & second) / len(first | second)


def _counter_overlap(first: Counter[int], second: Counter[int]) -> float:
    if not first or not second:
        return 0.0
    union = set(first) | set(second)
    numerator = sum(min(first.get(key, 0), second.get(key, 0)) for key in union)
    denominator = sum(max(first.get(key, 0), second.get(key, 0)) for key in union)
    return numerator / denominator if denominator else 0.0


def _channel_name(channel_id: str, channels: pd.DataFrame) -> str:
    match = channels[channels["channel_id"] == channel_id]
    if match.empty:
        return channel_id
    return str(match["display_name"].iloc[0] or channel_id)


def _merged_name(first: str, second: str, channels: pd.DataFrame) -> str:
    return f"{_channel_name(first, channels)}-{_channel_name(second, channels)}"


def _team_for_channels(channels: pd.DataFrame, channel_ids: list[str]) -> str | None:
    candidates = channels[channels["channel_id"].isin(channel_ids)]["team_id"].dropna()
    return str(candidates.mode().iloc[0]) if not candidates.empty else None


def _slug_to_name(value: str) -> str:
    head = value.split(",")[0].strip() or "proposed-channel"
    return head.replace(" ", "-")
