"""CLI: init SQLite and ingest jobs from The Muse API."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Allow `python -m backend.ingest.run` and `python backend/ingest/run.py`
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.db import count_jobs, init_db, upsert_jobs
from backend.ingest.muse import MuseAPIError, iter_muse_jobs
from backend.ingest.normalize import normalize_muse_job


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Initialize SQLite and ingest jobs from The Muse API.",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help="Path to SQLite file (default: data/jobs.db)",
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=15,
        help="Max Muse pages to fetch (20 jobs/page). Default 15 ≈ 300 jobs.",
    )
    parser.add_argument("--start-page", type=int, default=0, help="First page index.")
    parser.add_argument(
        "--api-key",
        default=os.environ.get("MUSE_API_KEY"),
        help="Optional Muse API key (or set MUSE_API_KEY). Raises rate limit.",
    )
    parser.add_argument("--category", default=None, help="Optional Muse category filter.")
    parser.add_argument("--level", default=None, help="Optional Muse level filter.")
    parser.add_argument("--location", default=None, help="Optional Muse location filter.")
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Ignore and rewrite local page cache under data/cache/.",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.25,
        help="Seconds between live API calls (default 0.25).",
    )
    parser.add_argument(
        "--init-only",
        action="store_true",
        help="Create the DB schema and exit without fetching.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    db_path = init_db(args.db)
    print(f"Database ready: {db_path}")

    if args.init_only:
        print(f"Job count: {count_jobs(db_path)}")
        return 0

    print(f"Fetching up to {args.pages} page(s) from The Muse…")
    jobs = []
    skipped = 0
    try:
        for raw in iter_muse_jobs(
            max_pages=args.pages,
            start_page=args.start_page,
            api_key=args.api_key,
            sleep_s=args.sleep,
            category=args.category,
            level=args.level,
            location=args.location,
            use_cache=not args.no_cache,
        ):
            job = normalize_muse_job(raw)
            if job is None:
                skipped += 1
                continue
            jobs.append(job)
    except MuseAPIError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # network / JSON failures
        print(f"ERROR fetching Muse jobs: {exc}", file=sys.stderr)
        return 1

    written = upsert_jobs(jobs, db_path)
    total = count_jobs(db_path)
    muse_total = count_jobs(db_path, source="themuse")

    print(f"Normalized {len(jobs)} jobs (skipped {skipped}).")
    print(f"Upserted {written} rows.")
    print(f"DB totals — all sources: {total}, themuse: {muse_total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
