from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import httpx

from crepe.config import Config
from crepe.storage.files import RunPaths, sanitize_for_filename

LOGGER = logging.getLogger(__name__)

TRANSIENT_STATUS_CODES = {429, 502, 503, 504}


class GraphClient:
    """Minimal Microsoft Graph client with pagination, retries, and raw payload capture."""

    def __init__(self, config: Config, token: str, run_paths: RunPaths) -> None:
        self.config = config
        self.run_paths = run_paths
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
            self._write_raw_page(resource_name, page_index, payload, path, context)
            collected.extend(payload.get("value", []))
            next_url = payload.get("@odata.nextLink")
            next_params = None
            page_index += 1
        return collected

    def _request_with_retry(self, path: str, params: dict[str, Any] | None = None) -> httpx.Response:
        for attempt in range(self.config.max_retries + 1):
            response = self.client.get(path, params=params)
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
    ) -> Path:
        resource_dir = self.run_paths.raw_dir / resource_name
        resource_dir.mkdir(parents=True, exist_ok=True)
        context_slug = ""
        if context:
            context_slug = "__".join(
                f"{sanitize_for_filename(str(key))}-{sanitize_for_filename(str(value))}"
                for key, value in sorted(context.items())
            )
        prefix = f"{context_slug}__" if context_slug else ""
        output_path = resource_dir / f"{prefix}page_{page_index:04d}.json"
        envelope = {
            "meta": {
                "resource_name": resource_name,
                "request_path": request_path,
                "page_index": page_index,
                "context": context or {},
            },
            "response": payload,
        }
        output_path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
        return output_path

