from __future__ import annotations

import json
from pathlib import Path

from crepe.storage.files import RunPaths


def write_demo_raw_data(run_paths: RunPaths) -> None:
    """Seed a deterministic demo dataset into the raw artifact tree."""

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
            {"id": "c-ops", "displayName": "Ops-General", "description": "Operational chat", "membershipType": "standard"},
            {"id": "c-buy", "displayName": "Procurement", "description": "Buying channel", "membershipType": "standard"},
            {"id": "c-feed", "displayName": "Feed-Forecast", "description": "Forecast and pricing", "membershipType": "standard"},
        ],
        {"team_id": "t1"},
    )
    _write_envelope(
        run_paths.raw_dir / "channels" / "team_id-t2__page_0001.json",
        "channels",
        1,
        [
            {"id": "c-sales", "displayName": "Sales-Planning", "description": "Commercial planning", "membershipType": "standard"},
        ],
        {"team_id": "t2"},
    )
    _write_envelope(
        run_paths.raw_dir / "chats" / "page_0001.json",
        "chats",
        1,
        [
            {"id": "chat-1", "topic": "Forecast follow-up", "chatType": "group"},
            {"id": "chat-2", "topic": "Supplier escalation", "chatType": "group"},
        ],
    )
    _write_envelope(
        run_paths.raw_dir / "channel_messages" / "channel_id-c_ops__team_id-t1__page_0001.json",
        "channel_messages",
        1,
        [
            {
                "id": "m1",
                "createdDateTime": "2025-01-10T09:00:00Z",
                "replyToId": None,
                "body": {"contentType": "html", "content": "<p>Need feed pricing update for the next production cycle</p>"},
                "from": {"user": {"id": "u1", "displayName": "Alice Wong"}},
            },
            {
                "id": "m2",
                "createdDateTime": "2025-01-10T09:08:00Z",
                "replyToId": "m1",
                "body": {"contentType": "html", "content": "<p>Procurement got a revised supplier sheet this morning</p>"},
                "from": {"user": {"id": "u2", "displayName": "Bob Tran"}},
            },
            {
                "id": "m3",
                "createdDateTime": "2025-01-10T09:15:00Z",
                "replyToId": "m1",
                "body": {"contentType": "html", "content": "<p>Finance needs the new margin assumption before noon</p>"},
                "from": {"user": {"id": "u3", "displayName": "Cara Lim"}},
            },
            {
                "id": "m4",
                "createdDateTime": "2025-01-10T10:00:00Z",
                "replyToId": None,
                "body": {"contentType": "html", "content": "<p>Shipment delay at the mill affects feed planning next week</p>"},
                "from": {"user": {"id": "u1", "displayName": "Alice Wong"}},
            },
        ],
        {"team_id": "t1", "channel_id": "c-ops"},
    )
    _write_envelope(
        run_paths.raw_dir / "channel_messages" / "channel_id-c_buy__team_id-t1__page_0001.json",
        "channel_messages",
        1,
        [
            {
                "id": "m5",
                "createdDateTime": "2025-01-10T11:00:00Z",
                "replyToId": None,
                "body": {"contentType": "html", "content": "<p>Supplier lead time issue on feed bags remains unresolved</p>"},
                "from": {"user": {"id": "u2", "displayName": "Bob Tran"}},
            },
            {
                "id": "m6",
                "createdDateTime": "2025-01-10T11:05:00Z",
                "replyToId": "m5",
                "body": {"contentType": "html", "content": "<p>Ops is exposed if the bags do not land by Tuesday</p>"},
                "from": {"user": {"id": "u1", "displayName": "Alice Wong"}},
            },
            {
                "id": "m7",
                "createdDateTime": "2025-01-10T11:15:00Z",
                "replyToId": "m5",
                "body": {"contentType": "html", "content": "<p>We should model the cost impact and escalate to commercial</p>"},
                "from": {"user": {"id": "u3", "displayName": "Cara Lim"}},
            },
        ],
        {"team_id": "t1", "channel_id": "c-buy"},
    )
    _write_envelope(
        run_paths.raw_dir / "channel_messages" / "channel_id-c_feed__team_id-t1__page_0001.json",
        "channel_messages",
        1,
        [
            {
                "id": "m8",
                "createdDateTime": "2025-01-10T13:00:00Z",
                "replyToId": None,
                "body": {"contentType": "html", "content": "<p>Forecast needs feed price update and volume scenario by farm</p>"},
                "from": {"user": {"id": "u3", "displayName": "Cara Lim"}},
            },
            {
                "id": "m9",
                "createdDateTime": "2025-01-10T13:07:00Z",
                "replyToId": "m8",
                "body": {"contentType": "html", "content": "<p>Sales planning also needs the same forecast assumptions</p>"},
                "from": {"user": {"id": "u4", "displayName": "Diego Santos"}},
            },
            {
                "id": "m10",
                "createdDateTime": "2025-01-10T13:10:00Z",
                "replyToId": "m8",
                "body": {"contentType": "html", "content": "<p>Procurement has overlapping supplier and forecast inputs here</p>"},
                "from": {"user": {"id": "u2", "displayName": "Bob Tran"}},
            },
        ],
        {"team_id": "t1", "channel_id": "c-feed"},
    )
    _write_envelope(
        run_paths.raw_dir / "channel_messages" / "channel_id-c_sales__team_id-t2__page_0001.json",
        "channel_messages",
        1,
        [
            {
                "id": "m11",
                "createdDateTime": "2025-01-10T14:00:00Z",
                "replyToId": None,
                "body": {"contentType": "html", "content": "<p>Commercial forecast depends on feed pricing and farm volume alignment</p>"},
                "from": {"user": {"id": "u4", "displayName": "Diego Santos"}},
            },
            {
                "id": "m12",
                "createdDateTime": "2025-01-10T14:08:00Z",
                "replyToId": "m11",
                "body": {"contentType": "html", "content": "<p>Finance is already asking for a margin sensitivity sheet</p>"},
                "from": {"user": {"id": "u3", "displayName": "Cara Lim"}},
            },
        ],
        {"team_id": "t2", "channel_id": "c-sales"},
    )
    _write_envelope(
        run_paths.raw_dir / "chat_messages" / "chat_id-chat_1__page_0001.json",
        "chat_messages",
        1,
        [
            {
                "id": "cm1",
                "createdDateTime": "2025-01-10T08:00:00Z",
                "body": {"contentType": "html", "content": "<p>Need the forecast workbook before the supplier call</p>"},
                "from": {"user": {"id": "u1", "displayName": "Alice Wong"}},
            },
            {
                "id": "cm2",
                "createdDateTime": "2025-01-10T08:05:00Z",
                "body": {"contentType": "html", "content": "<p>Sending the workbook and margin tabs now</p>"},
                "from": {"user": {"id": "u3", "displayName": "Cara Lim"}},
            },
            {
                "id": "cm3",
                "createdDateTime": "2025-01-10T12:45:00Z",
                "body": {"contentType": "html", "content": "<p>Need a fresh pricing scenario for procurement and sales</p>"},
                "from": {"user": {"id": "u4", "displayName": "Diego Santos"}},
            },
        ],
        {"chat_id": "chat-1"},
    )
    _write_envelope(
        run_paths.raw_dir / "chat_messages" / "chat_id-chat_2__page_0001.json",
        "chat_messages",
        1,
        [
            {
                "id": "cm4",
                "createdDateTime": "2025-01-10T11:20:00Z",
                "body": {"contentType": "html", "content": "<p>Escalating the bag supply issue to the vendor manager</p>"},
                "from": {"user": {"id": "u2", "displayName": "Bob Tran"}},
            },
            {
                "id": "cm5",
                "createdDateTime": "2025-01-10T11:25:00Z",
                "body": {"contentType": "html", "content": "<p>Ops needs ETA before tomorrow morning</p>"},
                "from": {"user": {"id": "u1", "displayName": "Alice Wong"}},
            },
        ],
        {"chat_id": "chat-2"},
    )


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
