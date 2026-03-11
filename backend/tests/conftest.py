from __future__ import annotations

import json
from pathlib import Path

import pytest

from crepe.config import Config
from crepe.storage.db import RunDatabase
from crepe.storage.files import RunPaths, build_run_paths


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


def seed_raw_fixture(run_paths: RunPaths) -> None:
    (run_paths.raw_dir / "users").mkdir(parents=True, exist_ok=True)
    (run_paths.raw_dir / "teams").mkdir(parents=True, exist_ok=True)
    (run_paths.raw_dir / "channels").mkdir(parents=True, exist_ok=True)
    (run_paths.raw_dir / "chats").mkdir(parents=True, exist_ok=True)
    (run_paths.raw_dir / "chat_messages").mkdir(parents=True, exist_ok=True)
    (run_paths.raw_dir / "channel_messages").mkdir(parents=True, exist_ok=True)

    _write_envelope(
        run_paths.raw_dir / "users" / "page_0001.json",
        "users",
        1,
        [
            {"id": "u1", "displayName": "Alice Wong", "mail": "alice@example.com", "userPrincipalName": "alice@example.com", "jobTitle": "Ops Lead"},
            {"id": "u2", "displayName": "Bob Tran", "mail": "bob@example.com", "userPrincipalName": "bob@example.com", "jobTitle": "Procurement"},
            {"id": "u3", "displayName": "Cara Lim", "mail": "cara@example.com", "userPrincipalName": "cara@example.com", "jobTitle": "Finance"},
        ],
    )
    _write_envelope(
        run_paths.raw_dir / "teams" / "page_0001.json",
        "teams",
        1,
        [
            {"id": "t1", "displayName": "Operations", "description": "Operations team", "isArchived": False},
        ],
    )
    _write_envelope(
        run_paths.raw_dir / "channels" / "team_id-t1__page_0001.json",
        "channels",
        1,
        [
            {"id": "c-ops", "displayName": "Ops-General", "description": "Operational chat", "membershipType": "standard"},
            {"id": "c-buy", "displayName": "Procurement", "description": "Buying channel", "membershipType": "standard"},
        ],
        {"team_id": "t1"},
    )
    _write_envelope(
        run_paths.raw_dir / "chats" / "page_0001.json",
        "chats",
        1,
        [{"id": "chat-1", "topic": "Direct thread", "chatType": "group"}],
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
                "body": {"contentType": "html", "content": "<p>Need feed pricing update</p>"},
                "from": {"user": {"id": "u1", "displayName": "Alice Wong"}},
            },
            {
                "id": "m2",
                "createdDateTime": "2025-01-10T09:10:00Z",
                "replyToId": "m1",
                "body": {"contentType": "html", "content": "<p>Procurement prices from supplier A arrived</p>"},
                "from": {"user": {"id": "u2", "displayName": "Bob Tran"}},
            },
            {
                "id": "m3",
                "createdDateTime": "2025-01-10T10:00:00Z",
                "replyToId": None,
                "body": {"contentType": "html", "content": "<p>Margin variance review for next week</p>"},
                "from": {"user": {"id": "u3", "displayName": "Cara Lim"}},
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
                "id": "m4",
                "createdDateTime": "2025-01-10T11:00:00Z",
                "replyToId": None,
                "body": {"contentType": "html", "content": "<p>Supplier lead time issue on feed bags</p>"},
                "from": {"user": {"id": "u2", "displayName": "Bob Tran"}},
            },
            {
                "id": "m5",
                "createdDateTime": "2025-01-10T11:05:00Z",
                "replyToId": "m4",
                "body": {"contentType": "html", "content": "<p>Ops impacted if delay continues</p>"},
                "from": {"user": {"id": "u1", "displayName": "Alice Wong"}},
            },
            {
                "id": "m6",
                "createdDateTime": "2025-01-10T11:15:00Z",
                "replyToId": "m4",
                "body": {"contentType": "html", "content": "<p>Finance wants updated cost forecast</p>"},
                "from": {"user": {"id": "u3", "displayName": "Cara Lim"}},
            },
        ],
        {"team_id": "t1", "channel_id": "c-buy"},
    )
    _write_envelope(
        run_paths.raw_dir / "chat_messages" / "chat_id-chat_1__page_0001.json",
        "chat_messages",
        1,
        [
            {
                "id": "cm1",
                "createdDateTime": "2025-01-10T08:00:00Z",
                "body": {"contentType": "html", "content": "<p>Need the procurement workbook</p>"},
                "from": {"user": {"id": "u1", "displayName": "Alice Wong"}},
            },
            {
                "id": "cm2",
                "createdDateTime": "2025-01-10T08:05:00Z",
                "body": {"contentType": "html", "content": "<p>Sending it now</p>"},
                "from": {"user": {"id": "u3", "displayName": "Cara Lim"}},
            },
            {
                "id": "cm3",
                "createdDateTime": "2025-01-10T13:30:00Z",
                "body": {"contentType": "html", "content": "<p>Need forecast numbers too</p>"},
                "from": {"user": {"id": "u1", "displayName": "Alice Wong"}},
            },
        ],
        {"chat_id": "chat-1"},
    )


@pytest.fixture()
def configured_env(tmp_path, monkeypatch):
    base_dir = tmp_path / "data"
    db_path = base_dir / "crepe.sqlite3"
    monkeypatch.setenv("MS_TENANT_ID", "tenant")
    monkeypatch.setenv("MS_CLIENT_ID", "client")
    monkeypatch.setenv("MS_CLIENT_SECRET", "secret")
    config = Config(
        tenant_id="tenant",
        client_id="client",
        client_secret="secret",
        base_dir=base_dir,
        db_path=db_path,
        cluster_count=3,
        chat_gap_minutes=120,
    )
    config.ensure_directories()
    return config


@pytest.fixture()
def run_db(configured_env):
    return RunDatabase(configured_env.db_path)


@pytest.fixture()
def sample_run(configured_env, run_db):
    run_id = run_db.create_run(run_id="fixture-run")
    paths = build_run_paths(configured_env, run_id)
    seed_raw_fixture(paths)
    return run_id, paths, run_db
