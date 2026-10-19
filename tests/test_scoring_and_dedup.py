from src.deduplication.urls import deduplicate, domain_key
from src.lead_scoring.scorer import score_lead


def test_domain_key_removes_www():
    assert domain_key("https://www.example.com/about") == "example.com"


def test_deduplicate_keeps_one_per_domain():
    leads = [
        {"website": "https://example.com", "score": 12, "signals": ["a"], "source_url": "https://search/a", "evidence": "one"},
        {"website": "http://www.example.com/about", "score": 24, "signals": ["b"], "source_url": "https://search/b", "evidence": "two"},
    ]
    result = deduplicate(leads)
    assert len(result) == 1
    assert result[0]["score"] == 24
    assert set(result[0]["signals"]) == {"a", "b"}


def test_explicit_intent_scores_higher():
    score, confidence, reasons = score_lead(
        "Website redesign needed",
        "A business is looking for a website redesign",
        ["missing_h1"],
        "https://example.com",
    )
    assert score >= 35
    assert confidence in {"medium", "high"}
    assert reasons
