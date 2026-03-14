from __future__ import annotations

from crepe.ner import extract_ner_tokens


def test_extract_ner_tokens_basic_patterns():
    text = "Email alpha@example.com visit https://example.com PO-1234 $500 2025-03-01 SharePoint"
    tokens = extract_ner_tokens(text)
    assert "NER:EMAIL:alpha@example.com" in tokens
    assert "NER:URL:https://example.com" in tokens
    assert "NER:DOC:PO-1234" in tokens
    assert "NER:MONEY:$500" in tokens
    assert "NER:DATE:2025-03-01" in tokens
    assert "NER:SYSTEM:SharePoint" in tokens
