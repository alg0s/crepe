from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

from crepe.storage.files import RunPaths

TAG_RE = re.compile(r"<[^>]+>")


def read_envelopes(resource_dir: Path) -> list[dict[str, Any]]:
    if not resource_dir.exists():
        return []
    envelopes: list[dict[str, Any]] = []
    for path in sorted(resource_dir.glob("*.json")):
        envelopes.append(json.loads(path.read_text(encoding="utf-8")))
    return envelopes


def clean_body_text(content: str | None) -> str:
    if not content:
        return ""
    text = html.unescape(TAG_RE.sub(" ", content))
    return re.sub(r"\s+", " ", text).strip()


def _sender_fields(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    sender = payload.get("from") or {}
    user = sender.get("user") or {}
    application = sender.get("application") or {}
    sender_id = user.get("id") or application.get("id")
    sender_name = user.get("displayName") or application.get("displayName")
    return sender_id, sender_name


def normalize_entities(run_paths: RunPaths) -> dict[str, pd.DataFrame]:
    users = _normalize_users(read_envelopes(run_paths.raw_dir / "users"))
    teams = _normalize_teams(read_envelopes(run_paths.raw_dir / "teams"))
    channels = _normalize_channels(read_envelopes(run_paths.raw_dir / "channels"))
    chats = _normalize_chats(read_envelopes(run_paths.raw_dir / "chats"))
    chat_messages = _normalize_messages(read_envelopes(run_paths.raw_dir / "chat_messages"), "chat")
    channel_messages = _normalize_messages(read_envelopes(run_paths.raw_dir / "channel_messages"), "channel")
    messages = pd.concat([chat_messages, channel_messages], ignore_index=True) if not chat_messages.empty or not channel_messages.empty else pd.DataFrame()
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
        csv_path = run_paths.normalized_dir / f"{name}.csv"
        jsonl_path = run_paths.normalized_dir / f"{name}.jsonl"
        frame.to_csv(csv_path, index=False)
        frame.to_json(jsonl_path, orient="records", lines=True)
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
            mentions = item.get("mentions") or []
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
                    "subject": item.get("subject"),
                    "importance": item.get("importance"),
                    "created_at": item.get("createdDateTime"),
                    "last_modified_at": item.get("lastModifiedDateTime"),
                    "body_content_type": (item.get("body") or {}).get("contentType"),
                    "body_html": (item.get("body") or {}).get("content"),
                    "body_text": clean_body_text((item.get("body") or {}).get("content")),
                    "mention_ids": "|".join(
                        mention.get("mentioned", {}).get("user", {}).get("id", "")
                        for mention in mentions
                        if mention.get("mentioned", {}).get("user", {}).get("id")
                    ),
                }
            )
    return pd.DataFrame(rows)


def _normalize_participants(messages: pd.DataFrame) -> pd.DataFrame:
    if messages.empty:
        return pd.DataFrame(columns=["message_id", "participant_id", "participant_type"])
    rows = []
    for record in messages.to_dict(orient="records"):
        if record.get("sender_id"):
            rows.append(
                {
                    "message_id": record["message_id"],
                    "participant_id": record["sender_id"],
                    "participant_type": "sender",
                }
            )
        for mention_id in filter(None, (record.get("mention_ids") or "").split("|")):
            rows.append(
                {
                    "message_id": record["message_id"],
                    "participant_id": mention_id,
                    "participant_type": "mention",
                }
            )
    return pd.DataFrame(rows).drop_duplicates()
