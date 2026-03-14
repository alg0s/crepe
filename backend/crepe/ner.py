from __future__ import annotations

import re
from html import unescape
from typing import Iterable


EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
URL_RE = re.compile(r"(https?://[^\s]+|www\.[^\s]+)")
PHONE_RE = re.compile(r"\+?\d[\d\-\s()]{7,}\d")
MONEY_RE = re.compile(r"(?:USD|VND|EUR|GBP|JPY|SGD|\$|€|£|¥)\s?\d+(?:[.,]\d+)?", re.IGNORECASE)
DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b")
DOC_RE = re.compile(r"\b(?:PO|PI|CI|PL|B-?L|BL|INV|INVOICE|TECHPACK|TS|SOP)[-#:]*\s?[A-Za-z0-9]+\b", re.IGNORECASE)

SYSTEM_KEYWORDS = {
    "sharepoint": "SharePoint",
    "odoo": "Odoo",
    "planner": "Planner",
    "excel": "Excel",
    "xero": "Xero",
    "misa": "MISA",
    "teams": "Teams",
}


def extract_message_text(payload: dict) -> str:
    body = payload.get("body") or {}
    body_text = ""
    if isinstance(body, dict):
        body_text = body.get("content") or ""
    subject = payload.get("subject") or ""
    summary = payload.get("summary") or ""
    text = f"{subject}\n{summary}\n{body_text}"
    return _strip_html(unescape(text)).strip()


def extract_ner_tokens(text: str) -> list[str]:
    if not text:
        return []
    tokens = set()
    for value in EMAIL_RE.findall(text):
        tokens.add(f"NER:EMAIL:{value}")
    for value in URL_RE.findall(text):
        tokens.add(f"NER:URL:{value}")
    for value in PHONE_RE.findall(text):
        tokens.add(f"NER:PHONE:{_normalize_ws(value)}")
    for value in MONEY_RE.findall(text):
        tokens.add(f"NER:MONEY:{_normalize_ws(value)}")
    for value in DATE_RE.findall(text):
        tokens.add(f"NER:DATE:{value}")
    for value in DOC_RE.findall(text):
        tokens.add(f"NER:DOC:{_normalize_ws(value.upper())}")
    lowered = text.lower()
    for key, label in SYSTEM_KEYWORDS.items():
        if key in lowered:
            tokens.add(f"NER:SYSTEM:{label}")
    return sorted(tokens)


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text)


def _normalize_ws(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()
