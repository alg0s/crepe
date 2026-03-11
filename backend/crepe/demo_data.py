from __future__ import annotations

import json
from pathlib import Path

from crepe.storage.files import RunPaths


def write_demo_raw_data(run_paths: RunPaths) -> None:
    """Seed a deterministic metadata-only demo dataset into the raw artifact tree."""

    for name in ("users", "teams", "channels", "chats", "chat_messages", "channel_messages"):
        (run_paths.raw_dir / name).mkdir(parents=True, exist_ok=True)

    _write_envelope(
        run_paths.raw_dir / "users" / "page_0001.json",
        "users",
        1,
        [
            {"id": "u1", "displayName": "Alice Wong", "mail": "alice@example.com", "userPrincipalName": "alice@example.com", "jobTitle": "Ops Lead"},
            {"id": "u2", "displayName": "Bob Tran", "mail": "bob@example.com", "userPrincipalName": "bob@example.com", "jobTitle": "Procurement"},
            {"id": "u3", "displayName": "Cara Lim", "mail": "cara@example.com", "userPrincipalName": "cara@example.com", "jobTitle": "Finance"},
            {"id": "u4", "displayName": "Diego Santos", "mail": "diego@example.com", "userPrincipalName": "diego@example.com", "jobTitle": "Sales Ops"},
        ],
    )
    _write_envelope(
        run_paths.raw_dir / "teams" / "page_0001.json",
        "teams",
        1,
        [
            {"id": "t1", "displayName": "Operations", "description": "Operations team", "isArchived": False},
            {"id": "t2", "displayName": "Commercial", "description": "Commercial team", "isArchived": False},
        ],
    )
    _write_envelope(
        run_paths.raw_dir / "channels" / "team_id-t1__page_0001.json",
        "channels",
        1,
        [
            {"id": "c-ops", "displayName": "Ops-General", "description": "Operational lane", "membershipType": "standard"},
            {"id": "c-buy", "displayName": "Procurement", "description": "Supplier lane", "membershipType": "standard"},
            {"id": "c-feed", "displayName": "Feed-Forecast", "description": "Forecast lane", "membershipType": "standard"},
        ],
        {"team_id": "t1"},
    )
    _write_envelope(
        run_paths.raw_dir / "channels" / "team_id-t2__page_0001.json",
        "channels",
        1,
        [
            {"id": "c-sales", "displayName": "Sales-Planning", "description": "Commercial planning lane", "membershipType": "standard"},
        ],
        {"team_id": "t2"},
    )
    _write_envelope(
        run_paths.raw_dir / "chats" / "page_0001.json",
        "chats",
        1,
        [
            {"id": "chat-1", "topic": "Coordination thread", "chatType": "group"},
            {"id": "chat-2", "topic": "Escalation thread", "chatType": "group"},
        ],
    )
    _write_envelope(
        run_paths.raw_dir / "channel_messages" / "channel_id-c_ops__team_id-t1__page_0001.json",
        "channel_messages",
        1,
        [
            _message("m1", "2025-01-10T09:00:00Z", "u1", importance="high", mentions=["u2"], reactions=["like"]),
            _message("m2", "2025-01-10T09:08:00Z", "u2", reply_to="m1", importance="normal", mentions=["u1"], reactions=["like"]),
            _message("m3", "2025-01-10T09:15:00Z", "u3", reply_to="m1", importance="normal", mentions=["u1"], reactions=[]),
            _message("m4", "2025-01-10T10:00:00Z", "u1", importance="normal", mentions=["u3"], reactions=[]),
        ],
        {"team_id": "t1", "channel_id": "c-ops"},
    )
    _write_envelope(
        run_paths.raw_dir / "channel_messages" / "channel_id-c_buy__team_id-t1__page_0001.json",
        "channel_messages",
        1,
        [
            _message("m5", "2025-01-10T11:00:00Z", "u2", importance="high", mentions=["u1"], reactions=["sad"]),
            _message("m6", "2025-01-10T11:05:00Z", "u1", reply_to="m5", importance="high", mentions=["u3"], reactions=["angry"]),
            _message("m7", "2025-01-10T11:15:00Z", "u3", reply_to="m5", importance="normal", mentions=["u2"], reactions=["like"]),
        ],
        {"team_id": "t1", "channel_id": "c-buy"},
    )
    _write_envelope(
        run_paths.raw_dir / "channel_messages" / "channel_id-c_feed__team_id-t1__page_0001.json",
        "channel_messages",
        1,
        [
            _message("m8", "2025-01-10T13:00:00Z", "u3", importance="high", mentions=["u4", "u2"], reactions=["like"]),
            _message("m9", "2025-01-10T13:07:00Z", "u4", reply_to="m8", importance="normal", mentions=["u3"], reactions=["heart"]),
            _message("m10", "2025-01-10T13:10:00Z", "u2", reply_to="m8", importance="normal", mentions=["u4"], reactions=[]),
        ],
        {"team_id": "t1", "channel_id": "c-feed"},
    )
    _write_envelope(
        run_paths.raw_dir / "channel_messages" / "channel_id-c_sales__team_id-t2__page_0001.json",
        "channel_messages",
        1,
        [
            _message("m11", "2025-01-10T14:00:00Z", "u4", importance="high", mentions=["u3"], reactions=["like"]),
            _message("m12", "2025-01-10T14:08:00Z", "u3", reply_to="m11", importance="normal", mentions=["u4"], reactions=[]),
        ],
        {"team_id": "t2", "channel_id": "c-sales"},
    )
    _write_envelope(
        run_paths.raw_dir / "chat_messages" / "chat_id-chat_1__page_0001.json",
        "chat_messages",
        1,
        [
            _message("cm1", "2025-01-10T08:00:00Z", "u1", importance="normal", mentions=["u3"], reactions=["like"]),
            _message("cm2", "2025-01-10T08:05:00Z", "u3", importance="normal", mentions=["u1"], reactions=["heart"]),
            _message("cm3", "2025-01-10T12:45:00Z", "u4", importance="high", mentions=["u2"], reactions=["sad"]),
        ],
        {"chat_id": "chat-1"},
    )
    _write_envelope(
        run_paths.raw_dir / "chat_messages" / "chat_id-chat_2__page_0001.json",
        "chat_messages",
        1,
        [
            _message("cm4", "2025-01-10T11:20:00Z", "u2", importance="high", mentions=["u1"], reactions=["angry"]),
            _message("cm5", "2025-01-10T11:25:00Z", "u1", importance="normal", mentions=["u2"], reactions=["sad"]),
        ],
        {"chat_id": "chat-2"},
    )


def _message(
    message_id: str,
    created_at: str,
    sender_id: str,
    *,
    reply_to: str | None = None,
    importance: str = "normal",
    mentions: list[str] | None = None,
    reactions: list[str] | None = None,
) -> dict:
    mention_rows = [
        {
            "mentionType": "person",
            "mentioned": {"user": {"id": mention_id, "displayName": mention_id}},
        }
        for mention_id in (mentions or [])
    ]
    reaction_rows = [{"reactionType": reaction, "user": {"id": sender_id}} for reaction in (reactions or [])]
    return {
        "id": message_id,
        "createdDateTime": created_at,
        "replyToId": reply_to,
        "importance": importance,
        "from": {"user": {"id": sender_id, "displayName": sender_id}},
        "mentions": mention_rows,
        "reactions": reaction_rows,
    }


def _write_envelope(path: Path, resource_name: str, page_index: int, value: list[dict], context: dict | None = None) -> None:
    envelope = {
        "meta": {
            "resource_name": resource_name,
            "request_path": f"/{resource_name}",
            "page_index": page_index,
            "context": context or {},
        },
        "response": {"value": value},
    }
    path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
