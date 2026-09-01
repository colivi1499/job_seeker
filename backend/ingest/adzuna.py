from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Iterator

import requests

ADZUNA_JOBS_URL = "https://api.adzuna.com/v1/api/jobs/us/search"
DEFAULT_CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "cache"


class AdzunaAPIError(RuntimeError):
    pass


def fetch_adzuna_page(
    page: int,
    *,
    app_id: str,
    app_key: str,
    session: requests.Session | None = None,
    timeout: float = 30.0,
    query: str | None = None,
    location: str | None = None,
    results_per_page: int = 50,
) -> dict[str, Any]:

    url = f"{ADZUNA_JOBS_URL}/{page}"

    params: dict[str, Any] = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": results_per_page,
    }

    if query:
        params["what"] = query

    if location:
        params["where"] = location

    http = session or requests.Session()

    for attempt in range(3):
        resp = http.get(
            url,
            params=params,
            timeout=timeout,
        )

        if resp.status_code == 503:
            if attempt < 2:
                time.sleep(2 ** attempt)
                continue

            raise AdzunaAPIError(
                "Adzuna API returned 503 after 3 attempts."
            )

        if resp.status_code >= 400:
            raise AdzunaAPIError(
                f"Adzuna API error {resp.status_code}: {resp.text[:300]}"
            )

        return resp.json()

    raise AdzunaAPIError("Adzuna request failed.")


def iter_adzuna_jobs(
    *,
    app_id: str,
    app_key: str,
    max_pages: int = 15,
    start_page: int = 1,
    query: str | None = None,
    location: str | None = None,
    sleep_s: float = 0.25,
    cache_dir: Path | None = DEFAULT_CACHE_DIR,
    use_cache: bool = True,
) -> Iterator[dict[str, Any]]:

    cache_path = Path(cache_dir) if cache_dir else None

    if use_cache and cache_path:
        cache_path.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({
        "User-Agent": "job-seeker-poc/0.1 (hackathon)"
    })

    pages_fetched = 0
    page = start_page

    while pages_fetched < max_pages:

        cache_file = None
        payload: dict[str, Any] | None = None

        if use_cache and cache_path:
            query_bit = query.replace(" ", "_") if query else "all"
            location_bit = location.replace(" ", "_") if location else "all"

            cache_file = (
                cache_path
                / f"adzuna_page_{page}_{query_bit}_{location_bit}.json"
            )

            if cache_file.exists():
                payload = json.loads(
                    cache_file.read_text(encoding="utf-8")
                )

        if payload is None:
            payload = fetch_adzuna_page(
                page,
                app_id=app_id,
                app_key=app_key,
                session=session,
                query=query,
                location=location,
            )

            if use_cache and cache_file is not None:
                cache_file.write_text(
                    json.dumps(payload),
                    encoding="utf-8",
                )

            if sleep_s > 0:
                time.sleep(sleep_s)

        results = payload.get("results") or []

        if not results:
            break

        for job in results:
            if isinstance(job, dict):
                yield job

        pages_fetched += 1

        total = payload.get("count", 0)

        if page * 50 >= total:
            break

        page += 1