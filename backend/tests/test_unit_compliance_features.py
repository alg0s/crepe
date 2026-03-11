from __future__ import annotations

import pandas as pd
import pytest

from crepe.extractors.messages import MESSAGE_SELECT_FIELDS, extract_chat_messages, extract_channel_messages
from crepe.graph_client import GraphClient
from crepe.normalize.entities import _enrich_message_routes, _message_columns, _sentiment_from_metadata
from crepe.storage.files import build_run_paths


class FakePaginatedClient:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def get_paginated(self, path, resource_name, params=None, context=None):
        self.calls.append({"path": path, "resource_name": resource_name, "params": params, "context": context})
        return []


@pytest.mark.unit
def test_sentiment_scoring_metadata_only():
    pos_score, pos_label = _sentiment_from_metadata("high", ["like", "heart"])
    neg_score, neg_label = _sentiment_from_metadata("low", ["angry", "sad"])
    neu_score, neu_label = _sentiment_from_metadata("normal", [])
    assert pos_score > 0 and pos_label == "positive"
    assert neg_score < 0 and neg_label == "negative"
    assert neu_score == 0 and neu_label == "neutral"


@pytest.mark.unit
def test_route_enrichment_derives_receivers_and_entities():
    records = [
        {
            "message_id": "m1",
            "source_type": "chat",
            "chat_id": "chat-1",
            "team_id": None,
            "channel_id": None,
            "thread_root_id": "m1",
            "reply_to_id": None,
            "sender_id": "u1",
            "sender_name": "u1",
            "importance": "normal",
            "created_at": "2025-01-10T10:00:00Z",
            "last_modified_at": None,
            "mention_ids": "u2",
            "receiver_ids": "",
            "entity_ids": "",
            "reaction_types": "",
            "sentiment_score": 0.0,
            "sentiment_label": "neutral",
        },
        {
            "message_id": "m2",
            "source_type": "chat",
            "chat_id": "chat-1",
            "team_id": None,
            "channel_id": None,
            "thread_root_id": "m2",
            "reply_to_id": "m1",
            "sender_id": "u2",
            "sender_name": "u2",
            "importance": "normal",
            "created_at": "2025-01-10T10:01:00Z",
            "last_modified_at": None,
            "mention_ids": "",
            "receiver_ids": "",
            "entity_ids": "",
            "reaction_types": "",
            "sentiment_score": 0.0,
            "sentiment_label": "neutral",
        },
    ]
    frame = pd.DataFrame(records, columns=_message_columns())
    enriched = _enrich_message_routes(frame)
    first = enriched[enriched["message_id"] == "m1"].iloc[0].to_dict()
    second = enriched[enriched["message_id"] == "m2"].iloc[0].to_dict()
    assert "u2" in str(first["receiver_ids"])
    assert "u1" in str(second["receiver_ids"])
    assert "PERSON:u1" in str(second["entity_ids"])
    assert "PERSON:u2" in str(second["entity_ids"])


@pytest.mark.unit
def test_message_extractors_use_select_projection():
    fake = FakePaginatedClient()
    extract_chat_messages(fake, [{"id": "chat-1"}])
    extract_channel_messages(fake, [{"id": "channel-1", "team_id": "team-1"}])
    assert len(fake.calls) == 2
    for call in fake.calls:
        assert call["params"]["$select"] == MESSAGE_SELECT_FIELDS


@pytest.mark.unit
def test_graph_client_sanitizes_message_payload(configured_env, run_db):
    run_id = run_db.create_run(run_id="unit-sanitize")
    run_paths = build_run_paths(configured_env, run_id)
    client = GraphClient(configured_env, "token", run_paths)
    payload = {
        "value": [
            {
                "id": "m1",
                "subject": "secret",
                "body": {"contentType": "html", "content": "<p>secret text</p>"},
                "mentions": [
                    {
                        "mentionText": "@u2",
                        "mentioned": {"user": {"id": "u2", "displayName": "User 2"}},
                    }
                ],
                "from": {"user": {"id": "u1", "displayName": "User 1"}},
                "reactions": [{"reactionType": "like", "user": {"id": "u2"}}],
            }
        ]
    }
    sanitized = client._sanitize_payload("chat_messages", payload)
    item = sanitized["value"][0]
    assert "body" not in item
    assert "subject" not in item
    assert "mentionText" not in str(item["mentions"][0])
    assert item["from"]["user"]["id"] == "u1"
