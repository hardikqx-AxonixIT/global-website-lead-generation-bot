"""Transparent heuristic scoring; score is prioritization, not verified purchase intent."""
from __future__ import annotations


def score_lead(search_title: str, snippet: str, signals: list[str], website: str,
               emails: list[str] | None = None) -> tuple[int, str, list[str]]:
    title = (search_title or "").lower()
    text = (snippet or "").lower()
    score = 0
    reasons: list[str] = []

    explicit_intent = ("looking for", "seeking", "need a", "request for proposal",
                       "hiring", "recommend a web", "website redesign")
    if any(term in text or term in title for term in explicit_intent):
        score += 35
        reasons.append("search result may indicate explicit service need (+35)")
    if any(term in text or term in title for term in ("outdated website", "no website", "poor website")):
        score += 25
        reasons.append("search result indicates possible website gap (+25)")
    if "site_not_using_https" in signals:
        score += 12
        reasons.append("website did not resolve on HTTPS (+12)")
    technical = {"missing_viewport_meta": 8, "missing_meta_description": 6,
                 "missing_h1": 5, "no_detected_favicon": 2}
    for signal, points in technical.items():
        if signal in signals:
            score += points
            reasons.append(f"{signal} (+{points})")
    if "website_redesign_keyword" in signals or "seo_keyword" in signals:
        score += 8
        reasons.append("website contains redesign/SEO-related language (+8)")
    if emails:
        score += 3
        reasons.append("public email detected on website (+3)")
    score = min(score, 100)
    confidence = "high" if score >= 55 else "medium" if score >= 30 else "low"
    return score, confidence, reasons
