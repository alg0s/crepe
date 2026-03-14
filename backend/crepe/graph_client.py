from __future__ import annotations

import json
import logging
import time
from typing import Any

import httpx

from crepe.config import Config
from crepe.ner import extract_message_text, extract_ner_tokens
from crepe.privacy import assert_payload_has_no_content
from crepe.storage.db import RunDatabase

LOGGER = logging.getLogger(__name__)

TRANSIENT_STATUS_CODES = {429, 502, 503, 504}
MESSAGE_RESOURCES = {"chat_messages", "channel_messages"}


class GraphClient:
    """Minimal Microsoft Graph client with pagination, retries, and raw payload capture."""

    def __init__(self, config: Config, token: str, database: RunDatabase, run_id: str) -> None:
        self.config = config
        self.database = database
        self.run_id = run_id
        self.client = httpx.Client(
            base_url="https://graph.microsoft.com/v1.0",
            headers={"Authorization": f"Bearer {token}"},
            timeout=config.request_timeout_seconds,
        )

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> "GraphClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def get_paginated(
        self,
        path: str,
        resource_name: str,
        *,
        params: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        collected: list[dict[str, Any]] = []
        next_url: str | None = path
        next_params = params.copy() if params else None
        page_index = 1
        while next_url:
            response = self._request_with_retry(next_url, params=next_params)
            payload = response.json()
            sanitized_payload = self._sanitize_payload(resource_name, payload)
            self._write_raw_page(resource_name, page_index, sanitized_payload, path, context)
            collected.extend(sanitized_payload.get("value", []))
            next_url = payload.get("@odata.nextLink")
            next_params = None
            page_index += 1
        return collected

    def _request_with_retry(self, path: str, params: dict[str, Any] | None = None) -> httpx.Response:
        for attempt in range(self.config.max_retries + 1):
            try:
                response = self.client.get(path, params=params)
            except httpx.ReadTimeout:
                if attempt >= self.config.max_retries:
                    raise
                sleep_seconds = 2 ** attempt
                LOGGER.warning(
                    "Graph read timed out on %s, retrying in %.1fs",
                    path,
                    sleep_seconds,
                )
                time.sleep(sleep_seconds)
                continue
            if response.status_code not in TRANSIENT_STATUS_CODES:
                response.raise_for_status()
                return response
            retry_after = response.headers.get("Retry-After")
            sleep_seconds = float(retry_after) if retry_after else 2 ** attempt
            LOGGER.warning(
                "Transient Graph error %s on %s, retrying in %.1fs",
                response.status_code,
                path,
                sleep_seconds,
            )
            time.sleep(sleep_seconds)
        response.raise_for_status()
        return response

    def _write_raw_page(
        self,
        resource_name: str,
        page_index: int,
        payload: dict[str, Any],
        request_path: str,
        context: dict[str, Any] | None,
    ) -> None:
        self.database.add_raw_page(
            self.run_id,
            resource_name,
            page_index=page_index,
            request_path=request_path,
            context=context,
            response=payload,
        )

    def _sanitize_payload(self, resource_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        if resource_name not in MESSAGE_RESOURCES:
            return payload
        safe_payload = dict(payload)
        safe_values: list[dict[str, Any]] = []
        for item in payload.get("value", []):
            safe_values.append(self._sanitize_message_item(item))
        safe_payload["value"] = safe_values
        if self.config.privacy_fail_on_content:
            assert_payload_has_no_content(safe_payload, f"sanitized:{resource_name}")
        return safe_payload

    def _sanitize_message_item(self, item: dict[str, Any]) -> dict[str, Any]:
        ner_tokens: list[str] = []
        if self.config.ner_enabled:
            try:
                message_text = extract_message_text(item)
                ner_tokens = extract_ner_tokens(message_text)
            except Exception:
                ner_tokens = []
        safe_item: dict[str, Any] = {}
        for key, value in item.items():
            if key in {"body", "subject", "summary", "messageHistory", "attachments", "hostedContents"}:
                continue
            if key == "mentions":
                safe_mentions = []
                for mention in value or []:
                    mention_obj = mention if isinstance(mention, dict) else {}
                    mentioned = mention_obj.get("mentioned", {})
                    mentioned_obj = mentioned if isinstance(mentioned, dict) else {}
                    user = mentioned_obj.get("user") or {}
                    safe_mentions.append(
                        {
                            "id": mention_obj.get("id"),
                            "mentionType": mention_obj.get("mentionType"),
                            "mentioned": {
                                "user": {
                                    "id": user.get("id"),
                                    "displayName": user.get("displayName"),
                                }
                            },
                        }
                    )
                safe_item[key] = safe_mentions
            elif key == "from":
                sender = value or {}
                user = (sender.get("user") or {}) if isinstance(sender, dict) else {}
                application = (sender.get("application") or {}) if isinstance(sender, dict) else {}
                safe_item[key] = {
                    "user": {"id": user.get("id"), "displayName": user.get("displayName")},
                    "application": {"id": application.get("id"), "displayName": application.get("displayName")},
                }
            elif key == "reactions":
                safe_item[key] = [
                    {
                        "reactionType": reaction.get("reactionType"),
                        "createdDateTime": reaction.get("createdDateTime"),
                        "user": {"id": (reaction.get("user") or {}).get("id")},
                    }
                    for reaction in (value or [])
                ]
            else:
                safe_item[key] = value
        safe_item["ner_entities"] = "|".join(ner_tokens)
        return safe_item
