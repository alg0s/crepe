from __future__ import annotations

import pytest

from crepe.nlp import analyze_sentiment, extract_ner_tokens


def test_extract_ner_tokens_spacy():
    spacy = pytest.importorskip("spacy")
    if not spacy.util.is_package("en_core_web_sm"):
        pytest.skip("spaCy model en_core_web_sm not installed")
    tokens = extract_ner_tokens("Meet Alice in London on 2025-03-01.")
    assert any(token.startswith("NER:PERSON:Alice") for token in tokens)
    assert any(token.startswith("NER:GPE:London") for token in tokens)


def test_analyze_sentiment_vader():
    pytest.importorskip("vaderSentiment")
    result = analyze_sentiment("This is fantastic and helpful.")
    assert result is not None
    assert result.label in {"positive", "neutral", "negative"}
