"""Public-web search adapters. Search results are leads to review, not verified intent."""
from __future__ import annotations

import os
import time
from typing import Any
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup


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
            link = item.get("link")
            if link and link.startswith(("http://", "https://")):
                rows.append({
                    "title": str(item.get("title", "")),
                    "url": str(link),
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
        url = link.get("href", "")
        if not url.startswith(("http://", "https://")):
            continue
        rows.append({
            "title": link.get_text(" ", strip=True),
            "url": url,
            "snippet": snippet.get_text(" ", strip=True) if snippet else "",
            "query": query,
        })
    time.sleep(max(0.0, delay))
    return rows
