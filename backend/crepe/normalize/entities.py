from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from crepe.privacy import assert_no_forbidden_columns, assert_payload_has_no_content
from crepe.storage.db import RunDatabase

POSITIVE_REACTIONS = {"like", "heart", "laugh", "surprised"}
NEGATIVE_REACTIONS = {"angry", "sad"}


def read_envelopes(database: RunDatabase, run_id: str, resource_name: str) -> list[dict[str, Any]]:
    envelopes: list[dict[str, Any]] = []
    for record in database.list_raw_pages(run_id, resource_name):
        envelope = {
            "meta": {
                "resource_name": record.resource_name,
                "request_path": record.request_path,
                "page_index": record.page_index,
                "context": record.context(),
            },
            "response": record.response(),
        }
        if resource_name in {"chat_messages", "channel_messages"}:
            assert_payload_has_no_content(envelope.get("response", {}), f"normalize:{resource_name}:{record.page_index}")
        envelopes.append(envelope)
    return envelopes


def normalize_entities(database: RunDatabase, run_id: str) -> dict[str, pd.DataFrame]:
    users = _normalize_users(read_envelopes(database, run_id, "users"))
    teams = _normalize_teams(read_envelopes(database, run_id, "teams"))
    channels = _normalize_channels(read_envelopes(database, run_id, "channels"))
    chats = _normalize_chats(read_envelopes(database, run_id, "chats"))
    chat_messages = _normalize_messages(read_envelopes(database, run_id, "chat_messages"), "chat")
    channel_messages = _normalize_messages(read_envelopes(database, run_id, "channel_messages"), "channel")

    if not chat_messages.empty or not channel_messages.empty:
        messages = pd.concat([chat_messages, channel_messages], ignore_index=True)
        messages = _enrich_message_routes(messages)
    else:
        messages = pd.DataFrame(columns=_message_columns())

    channel_threads = (
        channel_messages.assign(thread_root_id=channel_messages["reply_to_id"].fillna(channel_messages["message_id"]))
        [["message_id", "thread_root_id", "team_id", "channel_id", "sender_id", "created_at"]]
        if not channel_messages.empty
        else pd.DataFrame(columns=["message_id", "thread_root_id", "team_id", "channel_id", "sender_id", "created_at"])
    )
    participants = _normalize_participants(messages)
    frames = {
        "users": users,
        "teams": teams,
        "channels": channels,
        "chats": chats,
        "messages": messages,
        "message_participants": participants,
        "channel_threads": channel_threads,
    }
    for name, frame in frames.items():
        if name in {"messages", "conversations", "conversation_clusters", "cluster_summary"}:
            assert_no_forbidden_columns(frame, name)
        database.replace_dataset(run_id, name, frame)
    return frames


def _normalize_users(envelopes: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for envelope in envelopes:
        for item in envelope.get("response", {}).get("value", []):
            rows.append(
                {
                    "user_id": item.get("id"),
                    "display_name": item.get("displayName"),
                    "mail": item.get("mail"),
                    "user_principal_name": item.get("userPrincipalName"),
                    "job_title": item.get("jobTitle"),
                }
            )
    return pd.DataFrame(rows)


def _normalize_teams(envelopes: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for envelope in envelopes:
        for item in envelope.get("response", {}).get("value", []):
            rows.append(
                {
                    "team_id": item.get("id"),
                    "display_name": item.get("displayName"),
                    "description": item.get("description"),
                    "is_archived": item.get("isArchived", False),
                }
            )
    return pd.DataFrame(rows)


def _normalize_channels(envelopes: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for envelope in envelopes:
        team_id = envelope.get("meta", {}).get("context", {}).get("team_id")
        for item in envelope.get("response", {}).get("value", []):
            rows.append(
                {
                    "channel_id": item.get("id"),
                    "team_id": team_id,
                    "display_name": item.get("displayName"),
                    "description": item.get("description"),
                    "membership_type": item.get("membershipType"),
                    "web_url": item.get("webUrl"),
                }
            )
    return pd.DataFrame(rows)


def _normalize_chats(envelopes: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for envelope in envelopes:
        for item in envelope.get("response", {}).get("value", []):
            rows.append(
                {
                    "chat_id": item.get("id"),
                    "topic": item.get("topic"),
                    "chat_type": item.get("chatType"),
                    "web_url": item.get("webUrl"),
                }
            )
    return pd.DataFrame(rows)


def _normalize_messages(envelopes: list[dict[str, Any]], source_type: str) -> pd.DataFrame:
    rows = []
    for envelope in envelopes:
        context = envelope.get("meta", {}).get("context", {})
        for item in envelope.get("response", {}).get("value", []):
            sender_id, sender_name = _sender_fields(item)
            mention_ids = _mention_ids(item)
            reaction_types = _reaction_types(item)
            sentiment_score, sentiment_label = _sentiment_from_metadata(item.get("importance"), reaction_types)
            sentiment_source = "metadata"
            nlp_score = item.get("nlp_sentiment_score")
            nlp_label = item.get("nlp_sentiment_label")
            if nlp_score is not None and nlp_label:
                sentiment_score = float(nlp_score)
                sentiment_label = str(nlp_label)
                sentiment_source = "nlp"
            rows.append(
                {
                    "message_id": item.get("id"),
                    "source_type": source_type,
                    "chat_id": context.get("chat_id") or item.get("chatId"),
                    "team_id": context.get("team_id"),
                    "channel_id": context.get("channel_id"),
                    "thread_root_id": item.get("replyToId") or item.get("id"),
                    "reply_to_id": item.get("replyToId"),
                    "sender_id": sender_id,
                    "sender_name": sender_name,
                    "importance": item.get("importance"),
                    "created_at": item.get("createdDateTime"),
                    "last_modified_at": item.get("lastModifiedDateTime"),
                    "mention_ids": "|".join(mention_ids),
                    "receiver_ids": "",
                    "entity_ids": "",
                    "ner_entities": _join_ner_tokens(item.get("ner_entities")),
                    "reaction_types": "|".join(reaction_types),
                    "sentiment_score": sentiment_score,
                    "sentiment_label": sentiment_label,
                    "sentiment_source": sentiment_source,
                }
            )
    return pd.DataFrame(rows, columns=_message_columns())


def _enrich_message_routes(messages: pd.DataFrame) -> pd.DataFrame:
    if messages.empty:
        return messages
    working = messages.copy()
    sender_by_message = working.set_index("message_id")["sender_id"].to_dict()

    # Build receiver list from direct mentions and explicit replies.
    receiver_rows: list[str] = []
    for record in working.to_dict(orient="records"):
        receivers = set(filter(None, str(record.get("mention_ids") or "").split("|")))
        reply_to = record.get("reply_to_id")
        reply_target = sender_by_message.get(reply_to)
        if reply_target and reply_target != record.get("sender_id"):
            receivers.add(str(reply_target))
        receiver_rows.append("|".join(sorted(receivers)))
    working["receiver_ids"] = receiver_rows

    chat_sender_index = {
        key: set(frame["sender_id"].dropna().astype(str).tolist())
        for key, frame in working[working["source_type"] == "chat"].groupby("chat_id", dropna=False)
    }
    thread_sender_index = {
        key: set(frame["sender_id"].dropna().astype(str).tolist())
        for key, frame in working[working["source_type"] == "channel"].groupby(["team_id", "channel_id", "thread_root_id"], dropna=False)
    }

    fallback_receivers: list[str] = []
    for record in working.to_dict(orient="records"):
        existing = set(filter(None, str(record.get("receiver_ids") or "").split("|")))
        if existing:
            fallback_receivers.append("|".join(sorted(existing)))
            continue
        sender = str(record.get("sender_id") or "")
        if record.get("source_type") == "chat":
            peers = set(chat_sender_index.get(record.get("chat_id"), set()))
        else:
            peers = set(
                thread_sender_index.get(
                    (record.get("team_id"), record.get("channel_id"), record.get("thread_root_id")),
                    set(),
                )
            )
        peers.discard(sender)
        fallback_receivers.append("|".join(sorted(peers)))
    working["receiver_ids"] = fallback_receivers

    entities: list[str] = []
    for record in working.to_dict(orient="records"):
        tokens = set()
        for ner_token in filter(None, str(record.get("ner_entities") or "").split("|")):
            tokens.add(ner_token if ner_token.startswith("NER:") else f"NER:{ner_token}")
        for participant in filter(None, str(record.get("receiver_ids") or "").split("|")):
            tokens.add(f"PERSON:{participant}")
        for participant in filter(None, str(record.get("mention_ids") or "").split("|")):
            tokens.add(f"PERSON:{participant}")
        if record.get("sender_id"):
            tokens.add(f"PERSON:{record['sender_id']}")
        if record.get("channel_id"):
            tokens.add(f"CHANNEL:{record['channel_id']}")
        if record.get("team_id"):
            tokens.add(f"TEAM:{record['team_id']}")
        if record.get("chat_id"):
            tokens.add(f"CHAT:{record['chat_id']}")
        entities.append("|".join(sorted(tokens)))
    working["entity_ids"] = entities
    return working[_message_columns()]


def _normalize_participants(messages: pd.DataFrame) -> pd.DataFrame:
    if messages.empty:
        return pd.DataFrame(columns=["message_id", "participant_id", "participant_type"])
    rows = []
    for record in messages.to_dict(orient="records"):
        if record.get("sender_id"):
            rows.append({"message_id": record["message_id"], "participant_id": record["sender_id"], "participant_type": "sender"})
        for receiver_id in filter(None, str(record.get("receiver_ids") or "").split("|")):
            rows.append({"message_id": record["message_id"], "participant_id": receiver_id, "participant_type": "receiver"})
        for mention_id in filter(None, str(record.get("mention_ids") or "").split("|")):
            rows.append({"message_id": record["message_id"], "participant_id": mention_id, "participant_type": "mention"})
    return pd.DataFrame(rows).drop_duplicates()


def _sender_fields(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    sender = payload.get("from") or {}
    user = sender.get("user") or {}
    application = sender.get("application") or {}
    sender_id = user.get("id") or application.get("id")
    sender_name = user.get("displayName") or application.get("displayName")
    return sender_id, sender_name


def _mention_ids(payload: dict[str, Any]) -> list[str]:
    mentions = payload.get("mentions") or []
    return sorted(
        {
            str(mention.get("mentioned", {}).get("user", {}).get("id"))
            for mention in mentions
            if mention.get("mentioned", {}).get("user", {}).get("id")
        }
    )


def _reaction_types(payload: dict[str, Any]) -> list[str]:
    reactions = payload.get("reactions") or []
    return [str(reaction.get("reactionType", "")).lower() for reaction in reactions if reaction.get("reactionType")]


def _sentiment_from_metadata(importance: str | None, reactions: list[str]) -> tuple[float, str]:
    score = 0.0
    normalized_importance = (importance or "").lower()
    if normalized_importance == "high":
        score += 0.25
    elif normalized_importance == "low":
        score -= 0.1
    counts = Counter(reactions)
    score += 0.12 * sum(counts[reaction] for reaction in POSITIVE_REACTIONS)
    score -= 0.18 * sum(counts[reaction] for reaction in NEGATIVE_REACTIONS)
    score = max(-1.0, min(1.0, round(score, 4)))
    if score > 0.15:
        label = "positive"
    elif score < -0.15:
        label = "negative"
    else:
        label = "neutral"
    return score, label


def _message_columns() -> list[str]:
    return [
        "message_id",
        "source_type",
        "chat_id",
        "team_id",
        "channel_id",
        "thread_root_id",
        "reply_to_id",
        "sender_id",
        "sender_name",
        "importance",
        "created_at",
        "last_modified_at",
        "mention_ids",
        "receiver_ids",
        "entity_ids",
        "ner_entities",
        "reaction_types",
        "sentiment_score",
        "sentiment_label",
        "sentiment_source",
    ]


def _join_ner_tokens(value: Any) -> str:
    if not value:
        return ""
    if isinstance(value, list):
        return "|".join(str(token) for token in value if token)
    return str(value)
