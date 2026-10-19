from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse

from src.deduplication.urls import deduplicate
from src.lead_discovery.inspect import inspect_site
from src.lead_discovery.search import search_web
from src.lead_scoring.scorer import score_lead
from src.reporting.export import export_csv, export_markdown


def business_name(title: str, url: str) -> str:
    cleaned = re.split(r"\s[|–—-]\s", title or "")[0].strip()
    return cleaned or (urlparse(url).hostname or url)


def run(config_path: str, output_dir: str) -> list[dict]:
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    queries = []
    for region in config.get("regions", []):
        for category in config.get("business_categories", []):
            for template in config.get("search_queries", []):
                queries.append(template.format(region=region, category=category))
    max_queries = int(config.get("max_queries", 30))
    results_per_query = int(config.get("results_per_query", 8))
    user_agent = config.get("user_agent", "AxonixITLeadResearchBot/1.0")
    timeout = int(config.get("request_timeout_seconds", 12))
    delay = float(config.get("polite_delay_seconds", 1.5))

    search_results = []
    for query in queries[:max_queries]:
        try:
            search_results.extend(search_web(query, results_per_query, timeout, delay, user_agent))
        except Exception as exc:
            print(f"[WARN] Search failed for {query!r}: {type(exc).__name__}: {exc}")

    # Exclude search engines, social networks and obvious directories; prioritize actual business sites.
    excluded = ("duckduckgo.com", "google.com", "bing.com", "facebook.com", "instagram.com",
                "linkedin.com", "youtube.com", "reddit.com", "yelp.com", "yellowpages.com")
    candidates = []
    seen_urls = set()
    for item in search_results:
        host = (urlparse(item["url"]).hostname or "").lower()
        if not host or any(host == domain or host.endswith("." + domain) for domain in excluded):
            continue
        if item["url"] in seen_urls:
            continue
        seen_urls.add(item["url"])
        candidates.append(item)
    candidates = candidates[:int(config.get("max_sites_to_inspect", 60))]

    leads = []
    for item in candidates:
        site = inspect_site(item["url"], timeout, user_agent)
        signals = site.get("signals", [])
        score, confidence, reasons = score_lead(item["title"], item["snippet"], signals,
                                                 site.get("website", item["url"]), site.get("emails", []))
        leads.append({
            "business_name": business_name(item["title"], item["url"]),
            "website": site.get("website", item["url"]),
            "source_url": item["url"],
            "source_urls": [item["url"]],
            "evidence": item.get("snippet", "") or item.get("title", ""),
            "score": score,
            "confidence": confidence,
            "signals": signals + reasons,
            "public_emails": site.get("emails", []),
            "public_phones": site.get("phones", []),
            "contact_page": site.get("contact_page", ""),
            "inspection_status": site.get("inspection_status", "not_checked"),
            "suggested_next_step": "Manually verify fit and contact page" if score >= int(config.get("minimum_score", 20))
                                   else "Low priority; review only if relevant",
        })
    leads = deduplicate(leads)
    output = Path(output_dir)
    export_csv(leads, output / "leads.csv")
    export_markdown(leads, output / "daily_report.md")
    print(f"Finished: {len(leads)} candidate leads. Output: {output.resolve()}")
    return leads


def main() -> None:
    parser = argparse.ArgumentParser(description="Discover and score public business website leads.")
    parser.add_argument("--config", default="config/settings.example.json")
    parser.add_argument("--output-dir", default="output")
    args = parser.parse_args()
    run(args.config, args.output_dir)


if __name__ == "__main__":
    main()
