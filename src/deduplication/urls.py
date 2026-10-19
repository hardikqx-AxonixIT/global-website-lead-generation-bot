from __future__ import annotations

from urllib.parse import urlparse


def domain_key(url: str) -> str:
    parsed = urlparse(url if "://" in url else "https://" + url)
    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def deduplicate(leads: list[dict]) -> list[dict]:
    """Keep the strongest record per domain, preserving evidence from duplicates."""
    by_domain: dict[str, dict] = {}
    for lead in leads:
        key = domain_key(lead.get("website") or lead.get("url") or "")
        if not key:
            key = (lead.get("url") or lead.get("title") or "").lower()
        if key not in by_domain:
            by_domain[key] = lead
            continue
        existing = by_domain[key]
        existing["source_urls"] = sorted(set(existing.get("source_urls", [existing.get("source_url", "")]) +
                                               lead.get("source_urls", [lead.get("source_url", "")])) - {""})
        existing["score"] = max(existing.get("score", 0), lead.get("score", 0))
        existing["signals"] = sorted(set(existing.get("signals", []) + lead.get("signals", [])))
        existing["evidence"] = " | ".join(dict.fromkeys(filter(None, [
            existing.get("evidence", ""), lead.get("evidence", "")
        ])))[:1500]
    return list(by_domain.values())
