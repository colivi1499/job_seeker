"""Query cleanup and exclude-term extraction before embedding."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

QUERY_MAX_CHARS = 3000
SHORT_QUERY_THRESHOLD = 200

# Capture phrases after negation cues, e.g. "not software engineer", "no sales roles"
_EXCLUDE_PATTERN = re.compile(
    r"\b(?:not|no|exclude|without|never|avoid)\s+([^.,;\n]+)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class PreparedQuery:
    raw: str
    embed_text: str
    exclude_terms: tuple[str, ...]


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_exclude_terms(text: str) -> list[str]:
    """Pull lowercase exclusion phrases from negation patterns in the query."""
    seen: set[str] = set()
    terms: list[str] = []
    for match in _EXCLUDE_PATTERN.finditer(text):
        phrase = _normalize_whitespace(match.group(1))
        if len(phrase) < 3:
            continue
        key = phrase.lower()
        if key not in seen:
            seen.add(key)
            terms.append(key)
    return terms


def strip_exclude_clauses(text: str) -> str:
    """Remove negation clauses so they do not pull the embedding toward excluded topics."""
    cleaned = _EXCLUDE_PATTERN.sub(" ", text)
    cleaned = re.sub(r"[,;:\-–—]+\s*", " ", cleaned)
    return _normalize_whitespace(cleaned)


def prepare_query_heuristic(query_text: str) -> PreparedQuery:
    """
    Regex-based normalization for embedding and title-level exclusion filters.

    Short job-seeking queries get a consistent prefix; long resume pastes are
    truncated. Exclusion phrases are stripped from the embed text but applied
    as post-ranking filters on job titles.
    """
    raw = _normalize_whitespace(query_text or "")
    exclude_terms = tuple(extract_exclude_terms(raw))
    positive = strip_exclude_clauses(raw)

    if len(positive) > QUERY_MAX_CHARS:
        positive = positive[:QUERY_MAX_CHARS].rsplit(" ", 1)[0] or positive[:QUERY_MAX_CHARS]

    if positive and len(positive) <= SHORT_QUERY_THRESHOLD:
        embed_text = f"Desired job: {positive}"
    else:
        embed_text = positive or " "

    return PreparedQuery(raw=raw, embed_text=embed_text, exclude_terms=exclude_terms)


def prepare_query(query_text: str) -> PreparedQuery:
    """Prepare query for embedding (LLM when configured, else heuristic)."""
    from backend.match.query_llm import prepare_query as _prepare

    return _prepare(query_text)


def job_matches_excludes(job: dict[str, Any], exclude_terms: tuple[str, ...]) -> bool:
    """True if the job title contains any excluded phrase (case-insensitive)."""
    if not exclude_terms:
        return False
    title = (job.get("title") or "").lower()
    if not title:
        return False
    return any(term in title for term in exclude_terms)
