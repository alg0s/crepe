from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


FORBIDDEN_CONTENT_KEYS = {
    "body",
    "subject",
    "summary",
    "messagehistory",
    "attachments",
    "hostedcontents",
    "content",
    "contenttype",
    "messagepreview",
}

FORBIDDEN_COLUMNS = {
    "body_text",
    "body_html",
    "body_content_type",
    "combined_text",
    "subject",
    "content",
    "message_body",
    "raw_text",
}


@dataclass(slots=True)
class PrivacyViolation:
    location: str
    keys: list[str]


class PrivacyViolationError(RuntimeError):
    pass


def find_forbidden_keys(obj: Any) -> set[str]:
    hits: set[str] = set()
    if isinstance(obj, dict):
        for key, value in obj.items():
            normalized = str(key).strip().lower()
            if normalized in FORBIDDEN_CONTENT_KEYS:
                hits.add(normalized)
            hits.update(find_forbidden_keys(value))
        return hits
    if isinstance(obj, list):
        for item in obj:
            hits.update(find_forbidden_keys(item))
    return hits


def assert_payload_has_no_content(payload: dict[str, Any], location: str) -> None:
    violations: list[PrivacyViolation] = []
    for idx, item in enumerate(payload.get("value", [])):
        keys = sorted(find_forbidden_keys(item))
        if keys:
            violations.append(PrivacyViolation(location=f"{location}[{idx}]", keys=keys))
    if violations:
        details = "; ".join(f"{violation.location}: {','.join(violation.keys)}" for violation in violations)
        raise PrivacyViolationError(f"Privacy guard blocked content-bearing keys: {details}")


def assert_no_forbidden_columns(frame: pd.DataFrame, frame_name: str) -> None:
    if frame.empty:
        return
    columns = {col.lower() for col in frame.columns}
    hits = sorted(columns & FORBIDDEN_COLUMNS)
    if hits:
        raise PrivacyViolationError(f"Privacy guard blocked forbidden columns in {frame_name}: {', '.join(hits)}")


def strip_sensitive_columns(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    drop_cols = []
    for column in frame.columns:
        lowered = column.lower()
        if lowered in FORBIDDEN_COLUMNS or lowered.startswith("body_") or lowered.endswith("_content"):
            drop_cols.append(column)
    return frame.drop(columns=drop_cols, errors="ignore")
