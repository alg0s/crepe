from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from html import unescape
from typing import Any


class NlpSetupError(RuntimeError):
    pass


@dataclass(frozen=True)
class SentimentResult:
    score: float
    label: str


def extract_message_text(payload: dict[str, Any]) -> str:
    body = payload.get("body") or {}
    body_text = ""
    if isinstance(body, dict):
        body_text = body.get("content") or ""
    subject = payload.get("subject") or ""
    summary = payload.get("summary") or ""
    text = f"{subject}\n{summary}\n{body_text}"
    return _strip_html(unescape(text)).strip()


def extract_ner_tokens(text: str, *, language: str = "en", strict: bool = True) -> list[str]:
    if not text:
        return []
    if language != "en":
        if strict:
            raise NlpSetupError(f"Unsupported NLP language: {language}. Only 'en' is supported.")
        return []
    nlp = _load_spacy_model(strict)
    if nlp is None:
        return []
    doc = nlp(text)
    tokens = {f"NER:{ent.label_}:{ent.text}" for ent in doc.ents if ent.text}
    return sorted(tokens)


def analyze_sentiment(text: str, *, language: str = "en", strict: bool = True) -> SentimentResult | None:
    if not text:
        return None
    if language != "en":
        if strict:
            raise NlpSetupError(f"Unsupported NLP language: {language}. Only 'en' is supported.")
        return None
    analyzer = _load_vader(strict)
    if analyzer is None:
        return None
    compound = float(analyzer.polarity_scores(text).get("compound", 0.0))
    if compound >= 0.15:
        label = "positive"
    elif compound <= -0.15:
        label = "negative"
    else:
        label = "neutral"
    return SentimentResult(score=compound, label=label)


@lru_cache(maxsize=1)
def _load_spacy_model(strict: bool) -> Any | None:
    try:
        import spacy
    except Exception as exc:
        if strict:
            raise NlpSetupError("spaCy is not installed. Run `pip install spacy` and `python -m spacy download en_core_web_sm`.") from exc
        return None
    try:
        return spacy.load(
            "en_core_web_sm",
            disable=["parser", "lemmatizer", "textcat"],
        )
    except Exception as exc:
        if strict:
            raise NlpSetupError(
                "spaCy model en_core_web_sm is not installed. Run `python -m spacy download en_core_web_sm`."
            ) from exc
        return None


@lru_cache(maxsize=1)
def _load_vader(strict: bool) -> Any | None:
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    except Exception as exc:
        if strict:
            raise NlpSetupError("vaderSentiment is not installed. Run `pip install vaderSentiment`.") from exc
        return None
    return SentimentIntensityAnalyzer()


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text)
