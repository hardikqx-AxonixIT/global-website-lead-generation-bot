"""Public-web search adapters with multiple HTML search fallbacks."""
from __future__ import annotations

import os
import time
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

import requests
from bs4 import BeautifulSoup


def normalize_search_result_url(url: str) -> str:
    """Resolve common search-engine redirect links to destination URLs."""
    if url.startswith("//"):
        url = "https:" + url
    parsed = urlparse(url)
    if parsed.hostname and parsed.hostname.lower().endswith("duckduckgo.com"):
        target = parse_qs(parsed.query).get("uddg", [""])[0]
        if target:
            url = unquote(target)
    return url if url.startswith(("http://", "https://")) else ""


def _row(title: str, url: str, snippet: str, query: str) -> dict[str, str] | None:
    destination = normalize_search_result_url(url)
    if not destination:
        return None
    host = (urlparse(destination).hostname or "").lower()
    if not host or host.endswith(("duckduckgo.com", "bing.com", "microsoft.com")):
        return None
    return {"title": title.strip(), "url": destination, "snippet": snippet.strip(), "query": query}


def _search_serpapi(query: str, limit: int, timeout: int, user_agent: str, api_key: str) -> list[dict[str, str]]:
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
        row = _row(str(item.get("title", "")), str(item.get("link", "")),
                   str(item.get("snippet", "")), query)
        if row:
            rows.append(row)
    return rows


def _search_duckduckgo(query: str, limit: int, timeout: int, user_agent: str) -> list[dict[str, str]]:
    response = requests.get(
        "https://html.duckduckgo.com/html/", params={"q": query}, timeout=timeout,
        headers={"User-Agent": user_agent},
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    rows = []
    for result in soup.select(".result")[:limit]:
        link = result.select_one(".result__a")
        snippet = result.select_one(".result__snippet")
        if link:
            row = _row(link.get_text(" ", strip=True), str(link.get("href", "")),
                       snippet.get_text(" ", strip=True) if snippet else "", query)
            if row:
                rows.append(row)
    return rows


def _search_bing(query: str, limit: int, timeout: int, user_agent: str) -> list[dict[str, str]]:
    response = requests.get(
        "https://www.bing.com/search", params={"q": query, "count": limit}, timeout=timeout,
        headers={"User-Agent": user_agent},
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    rows = []
    for result in soup.select("li.b_algo")[:limit]:
        link = result.select_one("h2 a")
        snippet = result.select_one("p")
        if link:
            row = _row(link.get_text(" ", strip=True), str(link.get("href", "")),
                       snippet.get_text(" ", strip=True) if snippet else "", query)
            if row:
                rows.append(row)
    return rows


def search_web(query: str, limit: int = 8, timeout: int = 12, delay: float = 1.5,
               user_agent: str = "AxonixITLeadResearchBot/1.0") -> list[dict[str, str]]:
    """Use SerpAPI if configured; otherwise try DuckDuckGo and Bing HTML results."""
    api_key = os.getenv("SERPAPI_API_KEY")
    if api_key:
        rows = _search_serpapi(query, limit, timeout, user_agent, api_key)
        time.sleep(max(0.0, delay))
        return rows

    errors = []
    for provider, search_fn in (("DuckDuckGo", _search_duckduckgo), ("Bing", _search_bing)):
        try:
            rows = search_fn(query, limit, timeout, user_agent)
            if rows:
                time.sleep(max(0.0, delay))
                return rows
            errors.append(f"{provider}: response parsed but no organic results")
        except requests.RequestException as exc:
            errors.append(f"{provider}: {type(exc).__name__}: {exc}")
        except Exception as exc:
            errors.append(f"{provider}: {type(exc).__name__}: {exc}")

    raise RuntimeError("All search providers failed for query "
                       f"{query!r}. " + " | ".join(errors))
