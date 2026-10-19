"""Inspect publicly accessible business pages for basic opportunity signals."""
from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d .()\-]{7,}\d)(?!\w)")
SIGNALS = {
    "no_https": ("http",),
    "mentions_redesign_or_outdated": ("outdated", "redesign", "old website", "website redesign"),
    "mentions_seo_need": ("need seo", "seo services", "improve seo", "search engine optimization"),
    "mentions_website_need": ("need a website", "looking for a website", "website development"),
    "has_mobile_warning": ("viewport missing",),
}


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme:
        url = "https://" + url
        parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return ""
    return f"{parsed.scheme}://{parsed.netloc}/"


def inspect_site(url: str, timeout: int = 12,
                 user_agent: str = "AxonixITLeadResearchBot/1.0") -> dict:
    base = normalize_url(url)
    result = {
        "website": base or url, "site_title": "", "emails": [], "phones": [],
        "signals": [], "inspection_status": "not_checked", "page_text": "",
    }
    if not base:
        result["inspection_status"] = "invalid_url"
        return result
    try:
        response = requests.get(
            base, timeout=timeout, allow_redirects=True,
            headers={"User-Agent": user_agent},
        )
        result["website"] = response.url
        result["inspection_status"] = f"http_{response.status_code}"
        if response.status_code >= 400:
            return result
        soup = BeautifulSoup(response.text[:1_500_000], "html.parser")
        title = soup.title.get_text(" ", strip=True) if soup.title else ""
        for tag in soup(["script", "style", "noscript", "svg"]):
            tag.decompose()
        text = " ".join(soup.get_text(" ", strip=True).split())
        result["site_title"] = title
        result["page_text"] = text[:4000]
        result["emails"] = sorted(set(EMAIL_RE.findall(response.text)))[:10]
        result["phones"] = sorted(set(PHONE_RE.findall(text)))[:5]
        lowered = (title + " " + text).lower()
        if urlparse(response.url).scheme != "https":
            result["signals"].append("site_not_using_https")
        if any(term in lowered for term in ("outdated", "redesign", "old website", "website redesign")):
            result["signals"].append("website_redesign_keyword")
        if any(term in lowered for term in ("seo services", "improve seo", "search engine optimization")):
            result["signals"].append("seo_keyword")
        if not soup.find("meta", attrs={"name": re.compile("^viewport$", re.I)}):
            result["signals"].append("missing_viewport_meta")
        if not soup.find("meta", attrs={"name": re.compile("^description$", re.I)}):
            result["signals"].append("missing_meta_description")
        if not soup.find("h1"):
            result["signals"].append("missing_h1")
        if not soup.find("link", rel=lambda v: v and "icon" in str(v).lower()):
            result["signals"].append("no_detected_favicon")
        # Look for contact pages; do not crawl arbitrary site paths.
        for a in soup.find_all("a", href=True):
            if "contact" in a.get_text(" ", strip=True).lower() or "contact" in a["href"].lower():
                contact_url = urljoin(response.url, a["href"])
                if urlparse(contact_url).netloc == urlparse(response.url).netloc:
                    result["contact_page"] = contact_url
                    break
        result.pop("page_text", None)
    except requests.RequestException as exc:
        result["inspection_status"] = f"error:{type(exc).__name__}"
        result.pop("page_text", None)
    return result
