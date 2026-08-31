"""Fetch job postings from The Muse public API."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Iterator

import requests

MUSE_JOBS_URL = "https://www.themuse.com/api/public/jobs"
DEFAULT_CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "cache"


class MuseAPIError(RuntimeError):
    pass


def fetch_muse_page(
    page: int,
    *,
    session: requests.Session | None = None,
    api_key: str | None = None,
    timeout: float = 30.0,
    category: str | None = None,
    level: str | None = None,
    location: str | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {"page": page}
    if api_key:
        params["api_key"] = api_key
    if category:
        params["category"] = category
    if level:
        params["level"] = level
    if location:
        params["location"] = location

    http = session or requests.Session()
    resp = http.get(MUSE_JOBS_URL, params=params, timeout=timeout)
    if resp.status_code == 403:
        raise MuseAPIError(
            f"Rate limited by The Muse API (page={page}). "
            "Wait for X-RateLimit-Reset or pass --api-key."
        )
    if resp.status_code >= 400:
        raise MuseAPIError(f"Muse API error {resp.status_code}: {resp.text[:300]}")
    return resp.json()


def iter_muse_jobs(
    *,
    max_pages: int = 15,
    start_page: int = 0,
    api_key: str | None = None,
    sleep_s: float = 0.25,
    category: str | None = None,
    level: str | None = None,
    location: str | None = None,
    cache_dir: Path | None = DEFAULT_CACHE_DIR,
    use_cache: bool = True,
) -> Iterator[dict[str, Any]]:
    """
    Yield raw Muse job dicts across pages.

    Caches each page JSON under data/cache/ so re-runs do not re-hit the API.
    """
    cache_path = Path(cache_dir) if cache_dir else None
    if use_cache and cache_path:
        cache_path.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({"User-Agent": "job-seeker-poc/0.1 (hackathon)"})

    pages_fetched = 0
    page = start_page
    while pages_fetched < max_pages:
        cache_file = None
        payload: dict[str, Any] | None = None

        if use_cache and cache_path:
            filter_bits = []
            if category:
                filter_bits.append(f"cat-{category.replace(' ', '_')}")
            if level:
                filter_bits.append(f"lvl-{level.replace(' ', '_')}")
            if location:
                filter_bits.append(f"loc-{location.replace(' ', '_')}")
            suffix = ("_" + "_".join(filter_bits)) if filter_bits else ""
            cache_file = cache_path / f"muse_page_{page}{suffix}.json"
            if cache_file.exists():
                payload = json.loads(cache_file.read_text(encoding="utf-8"))

        if payload is None:
            payload = fetch_muse_page(
                page,
                session=session,
                api_key=api_key,
                category=category,
                level=level,
                location=location,
            )
            if use_cache and cache_file is not None:
                cache_file.write_text(json.dumps(payload), encoding="utf-8")
            if sleep_s > 0:
                time.sleep(sleep_s)

        results = payload.get("results") or []
        if not results:
            break

        for job in results:
            if isinstance(job, dict):
                yield job

        pages_fetched += 1
        page_count = payload.get("page_count")
        if page_count is not None and page + 1 >= int(page_count):
            break
        page += 1
