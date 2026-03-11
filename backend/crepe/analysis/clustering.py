from __future__ import annotations

from collections import Counter

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans


def cluster_conversations(conversations: pd.DataFrame, n_clusters: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Cluster conversation metadata tokens with TF-IDF and KMeans."""

    if conversations.empty:
        empty = pd.DataFrame(columns=["conversation_id", "cluster_id", "cluster_label"])
        return empty, pd.DataFrame(columns=["cluster_id", "keywords", "conversation_count", "participant_count", "top_participants", "top_channels"])
    working = conversations.copy()
    working["entity_tokens"] = working["entity_tokens"].fillna("").astype(str)
    if len(working) == 1:
        clustered = working[["conversation_id"]].assign(cluster_id=0, cluster_label="general")
        summary = _build_cluster_summary(clustered.merge(working, on="conversation_id"), None, None)
        return clustered, summary
    cluster_count = max(1, min(n_clusters, len(working)))
    vectorizer = TfidfVectorizer(stop_words="english", max_features=2000)
    matrix = vectorizer.fit_transform(working["entity_tokens"])
    if matrix.shape[1] == 0:
        clustered = working[["conversation_id"]].assign(cluster_id=0, cluster_label="general")
        summary = _build_cluster_summary(clustered.merge(working, on="conversation_id"), None, None)
        return clustered, summary
    model = KMeans(n_clusters=cluster_count, n_init="auto", random_state=42)
    labels = model.fit_predict(matrix)
    clustered = working[["conversation_id"]].assign(cluster_id=labels)
    summary = _build_cluster_summary(clustered.merge(working, on="conversation_id"), vectorizer, model)
    label_map = {row["cluster_id"]: row["keywords"] for row in summary.to_dict(orient="records")}
    clustered["cluster_label"] = clustered["cluster_id"].map(label_map)
    return clustered, summary


def _build_cluster_summary(
    joined: pd.DataFrame,
    vectorizer: TfidfVectorizer | None,
    model: KMeans | None,
) -> pd.DataFrame:
    rows = []
    keyword_map = _cluster_keywords(vectorizer, model)
    for cluster_id, frame in joined.groupby("cluster_id"):
        participants = Counter()
        channels = Counter()
        for record in frame.to_dict(orient="records"):
            for participant in filter(None, (record.get("participants") or "").split("|")):
                participants[participant] += 1
            if record.get("channel_id"):
                channels[str(record["channel_id"])] += 1
        rows.append(
            {
                "cluster_id": int(cluster_id),
                "keywords": keyword_map.get(int(cluster_id), "general"),
                "conversation_count": int(len(frame)),
                "participant_count": int(sum(participants.values())),
                "top_participants": "|".join(name for name, _ in participants.most_common(5)),
                "top_channels": "|".join(channel for channel, _ in channels.most_common(5)),
            }
        )
    return pd.DataFrame(rows)


def _cluster_keywords(vectorizer: TfidfVectorizer | None, model: KMeans | None) -> dict[int, str]:
    if vectorizer is None or model is None:
        return {}
    feature_names = vectorizer.get_feature_names_out()
    labels = {}
    for cluster_id, centroid in enumerate(model.cluster_centers_):
        top_indices = centroid.argsort()[::-1][:5]
        labels[cluster_id] = ", ".join(feature_names[index] for index in top_indices if centroid[index] > 0)
    return labels
