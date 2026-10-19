from __future__ import annotations

import csv
from pathlib import Path


FIELDS = [
    "business_name", "website", "source_url", "source_urls", "evidence",
    "score", "confidence", "signals", "public_emails", "public_phones",
    "contact_page", "inspection_status", "suggested_next_step"
]


def export_csv(leads: list[dict], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        for lead in leads:
            row = dict(lead)
            for key in ("source_urls", "signals", "public_emails", "public_phones"):
                if isinstance(row.get(key), list):
                    row[key] = "; ".join(row[key])
            writer.writerow(row)


def export_markdown(leads: list[dict], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Daily Website Lead Report", "", f"Candidate leads: **{len(leads)}**", "",
             "> Search-derived candidates only. Review source evidence and verify before outreach.", "",
             "| Score | Business/site | Website | Signals | Suggested next step |",
             "|---:|---|---|---|---|"]
    for lead in sorted(leads, key=lambda item: item.get("score", 0), reverse=True):
        name = (lead.get("business_name") or lead.get("site_title") or "Unidentified business").replace("|", "\\|")
        website = lead.get("website", "")
        signals = ", ".join(lead.get("signals", [])) or "No strong signals detected"
        step = lead.get("suggested_next_step", "Manually review")
        lines.append(f"| {lead.get('score', 0)} | {name} | [{website}]({website}) | {signals} | {step} |")
        lines.append("")
        lines.append(f"Evidence: {lead.get('evidence', 'No snippet available')}")
        lines.append(f"Source: {lead.get('source_url', '')}")
        lines.append("")
    target.write_text("\n".join(lines), encoding="utf-8")
