"""SQLite accessors for the canonical Job schema (POC Sec. 4.3)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable, Sequence

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = ROOT / "data" / "jobs.db"
SCHEMA_PATH = ROOT / "data" / "schema.sql"


def connect(db_path: Path | str | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path | str | None = None) -> Path:
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    with connect(path) as conn:
        conn.executescript(schema)
        conn.commit()
    return path


def _skills_to_json(skills: Any) -> str:
    if skills is None:
        return "[]"
    if isinstance(skills, str):
        try:
            parsed = json.loads(skills)
            if isinstance(parsed, list):
                return json.dumps(parsed)
        except json.JSONDecodeError:
            return json.dumps([skills] if skills else [])
        return json.dumps([skills] if skills else [])
    if isinstance(skills, (list, tuple)):
        return json.dumps([str(s) for s in skills if s])
    return "[]"


def job_to_row(job: dict[str, Any]) -> tuple[Any, ...]:
    """Flatten a Job dict into a DB insert tuple."""
    return (
        job.get("id"),
        job.get("title") or "",
        job.get("company"),
        job.get("location"),
        job.get("description"),
        job.get("url"),
        job.get("source") or "unknown",
        job.get("salary_min"),
        job.get("salary_max"),
        job.get("posted_date"),
        _skills_to_json(job.get("skills")),
    )


def row_to_job(row: sqlite3.Row | Sequence[Any]) -> dict[str, Any]:
    """Convert a DB row into the canonical Job JSON object."""
    if isinstance(row, sqlite3.Row):
        data = dict(row)
    else:
        data = dict(zip(
            (
                "id",
                "title",
                "company",
                "location",
                "description",
                "url",
                "source",
                "salary_min",
                "salary_max",
                "posted_date",
                "skills_json",
            ),
            row,
        ))

    skills_raw = data.get("skills_json", "[]")
    try:
        skills = json.loads(skills_raw) if skills_raw else []
    except json.JSONDecodeError:
        skills = []
    if not isinstance(skills, list):
        skills = []

    return {
        "id": data.get("id"),
        "title": data.get("title"),
        "company": data.get("company"),
        "location": data.get("location"),
        "description": data.get("description"),
        "url": data.get("url"),
        "source": data.get("source"),
        "salary_min": data.get("salary_min"),
        "salary_max": data.get("salary_max"),
        "posted_date": data.get("posted_date"),
        "skills": skills,
    }


UPSERT_SQL = """
INSERT INTO jobs (
  id, title, company, location, description, url, source,
  salary_min, salary_max, posted_date, skills_json
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(id) DO UPDATE SET
  title = excluded.title,
  company = excluded.company,
  location = excluded.location,
  description = excluded.description,
  url = excluded.url,
  source = excluded.source,
  salary_min = excluded.salary_min,
  salary_max = excluded.salary_max,
  posted_date = excluded.posted_date,
  skills_json = excluded.skills_json
"""


def upsert_jobs(
    jobs: Iterable[dict[str, Any]],
    db_path: Path | str | None = None,
) -> int:
    """Insert or update jobs. Returns number of rows written."""
    rows = [job_to_row(job) for job in jobs if job.get("id") and job.get("title")]
    if not rows:
        return 0
    with connect(db_path) as conn:
        conn.executemany(UPSERT_SQL, rows)
        conn.commit()
    return len(rows)


def count_jobs(db_path: Path | str | None = None, source: str | None = None) -> int:
    with connect(db_path) as conn:
        if source:
            cur = conn.execute("SELECT COUNT(*) FROM jobs WHERE source = ?", (source,))
        else:
            cur = conn.execute("SELECT COUNT(*) FROM jobs")
        return int(cur.fetchone()[0])


def get_jobs(
    db_path: Path | str | None = None,
    *,
    source: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    sql = "SELECT * FROM jobs"
    params: list[Any] = []
    if source:
        sql += " WHERE source = ?"
        params.append(source)
    sql += " ORDER BY posted_date IS NULL, posted_date DESC, id"
    if limit is not None:
        sql += " LIMIT ?"
        params.append(limit)
    with connect(db_path) as conn:
        rows = conn.execute(sql, params).fetchall()
    return [row_to_job(r) for r in rows]


def get_job(job_id: str, db_path: Path | str | None = None) -> dict[str, Any] | None:
    with connect(db_path) as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return row_to_job(row) if row else None
