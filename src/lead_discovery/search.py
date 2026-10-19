"""Public-web search adapters. Search results are leads to review, not verified intent."""
from __future__ import annotations

import os
import time
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

import requests
from bs4 import BeautifulSoup


def normalize_search_result_url(url: str) -> str:
    """Resolve common DuckDuckGo redirect links to the destination URL."""
    if url.startswith("//"):
        url = "https:" + url
    parsed = urlparse(url)
    if parsed.hostname and parsed.hostname.lower().endswith("duckduckgo.com"):
        target = parse_qs(parsed.query).get("uddg", [""])[0]
        if target:
            url = unquote(target)
    if url.startswith(("http://", "https://")):
        return url
    return ""


def search_web(query: str, limit: int = 8, timeout: int = 12, delay: float = 1.5,
               user_agent: str = "AxonixITLeadResearchBot/1.0") -> list[dict[str, str]]:
    """Search using SerpAPI when configured; otherwise try DuckDuckGo HTML best-effort."""
    api_key = os.getenv("SERPAPI_API_KEY")
    if api_key:
        response = requests.get(
            "https://serpapi.com/search.json",
            params={"engine": "google", "q": query, "api_key": api_key, "num": limit},
            timeout=timeout,
            headers={"User-Agent": user_agent},
        )
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
        rows = []
        for item in payload.get("organic_results", [])[:limit]:
            link = normalize_search_result_url(str(item.get("link", "")))
            if link:
                rows.append({
                    "title": str(item.get("title", "")),
                    "url": link,
                    "snippet": str(item.get("snippet", "")),
                    "query": query,
                })
        time.sleep(max(0.0, delay))
        return rows

    response = requests.get(
        "https://html.duckduckgo.com/html/",
        params={"q": query},
        timeout=timeout,
        headers={"User-Agent": user_agent},
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    rows = []
    for result in soup.select(".result")[:limit]:
        link = result.select_one(".result__a")
        snippet = result.select_one(".result__snippet")
        if not link:
            continue
        destination = normalize_search_result_url(str(link.get("href", "")))
        if not destination:
            continue
        rows.append({
            "title": link.get_text(" ", strip=True),
            "url": destination,
            "snippet": snippet.get_text(" ", strip=True) if snippet else "",
            "query": query,
        })
    time.sleep(max(0.0, delay))
    return rows
