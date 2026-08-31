"""Normalize source-specific payloads into the canonical Job record."""

from __future__ import annotations

import html
import re
from typing import Any

from bs4 import BeautifulSoup

_WHITESPACE_RE = re.compile(r"\s+")


def html_to_text(raw: str | None) -> str | None:
    if not raw:
        return None
    soup = BeautifulSoup(raw, "lxml")
    text = soup.get_text(separator=" ", strip=True)
    text = html.unescape(text)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text or None


def _named_list(items: Any, key: str = "name") -> list[str]:
    if not isinstance(items, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        if isinstance(item, dict):
            value = item.get(key) or item.get("short_name")
        else:
            value = item
        if not value:
            continue
        name = str(value).strip()
        if name and name.lower() not in seen:
            seen.add(name.lower())
            out.append(name)
    return out


def empty_job(**overrides: Any) -> dict[str, Any]:
    """Canonical Job with all keys present (POC Sec. 4.3)."""
    job = {
        "id": None,
        "title": None,
        "company": None,
        "location": None,
        "description": None,
        "url": None,
        "source": None,
        "salary_min": None,
        "salary_max": None,
        "posted_date": None,
        "skills": [],
    }
    job.update(overrides)
    return job


def normalize_muse_job(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Map a Muse API job object to the canonical Job schema."""
    muse_id = raw.get("id")
    title = (raw.get("name") or "").strip()
    if muse_id is None or not title:
        return None

    company_obj = raw.get("company") or {}
    company = None
    if isinstance(company_obj, dict):
        company = company_obj.get("name")
    elif isinstance(company_obj, str):
        company = company_obj

    locations = _named_list(raw.get("locations"))
    location = ", ".join(locations) if locations else None

    refs = raw.get("refs") or {}
    url = None
    if isinstance(refs, dict):
        url = refs.get("landing_page") or refs.get("internal")

    # Muse has no salary fields; leave null. Skills ≈ tags ∪ categories.
    skills = _named_list(raw.get("tags")) + _named_list(raw.get("categories"))
    # de-dupe while preserving order
    seen: set[str] = set()
    deduped_skills: list[str] = []
    for s in skills:
        key = s.lower()
        if key not in seen:
            seen.add(key)
            deduped_skills.append(s)

    return empty_job(
        id=f"muse-{muse_id}",
        title=title,
        company=company,
        location=location,
        description=html_to_text(raw.get("contents")),
        url=url,
        source="themuse",
        salary_min=None,
        salary_max=None,
        posted_date=raw.get("publication_date"),
        skills=deduped_skills,
    )
