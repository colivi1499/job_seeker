"""Parse user query/resume intent via GPT-4o-mini before embedding."""

from __future__ import annotations

import backend.env  # noqa: F401 — load .env

import json
import logging
import os
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from backend.match.query import (
    PreparedQuery,
    QUERY_MAX_CHARS,
    SHORT_QUERY_THRESHOLD,
    _normalize_whitespace,
    prepare_query_heuristic,
)

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-4o-mini"
MAX_INPUT_CHARS = 8000

SYSTEM_PROMPT = """You extract job-search intent from user input for a semantic job matcher.

The user may paste a resume OR describe a job they want. Return JSON only with:
- embed_text: 1-3 concise sentences describing the IDEAL job to search for (roles, skills, domain, location preferences). Omit negated roles. No markdown.
- exclude_titles: array of lowercase job title phrases to EXCLUDE (from explicit "not/no/avoid" language). Empty array if none.

Examples:
Input: "not software engineer, want nursing hospital care"
Output: {"embed_text": "Registered nurse or LPN roles in hospital inpatient care.", "exclude_titles": ["software engineer"]}

Input: "Senior Python backend engineer, remote US, 5 years Django AWS"
Output: {"embed_text": "Senior Python backend engineer with Django and AWS experience, remote in the United States.", "exclude_titles": []}
"""


class QueryIntent(BaseModel):
    embed_text: str = Field(min_length=1)
    exclude_titles: list[str] = Field(default_factory=list)


def _llm_enabled() -> bool:
    flag = os.environ.get("USE_LLM_QUERY_PARSE", "true").lower()
    if flag in ("0", "false", "no", "off"):
        return False
    return bool(os.environ.get("OPENAI_API_KEY", "").strip())


def _format_embed_text(text: str) -> str:
    positive = _normalize_whitespace(text)
    if len(positive) > QUERY_MAX_CHARS:
        positive = positive[:QUERY_MAX_CHARS].rsplit(" ", 1)[0] or positive[:QUERY_MAX_CHARS]
    if positive and len(positive) <= SHORT_QUERY_THRESHOLD:
        return f"Desired job: {positive}"
    return positive or " "


def _normalize_exclude_titles(values: list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in values:
        term = _normalize_whitespace(raw).lower()
        if len(term) < 3 or term in seen:
            continue
        seen.add(term)
        out.append(term)
    return tuple(out)


def parse_query_with_llm(raw: str) -> PreparedQuery:
    """Call OpenAI to produce embed_text and exclude_titles. Raises on failure."""
    from openai import OpenAI

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    model = os.environ.get("OPENAI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    user_content = raw[:MAX_INPUT_CHARS]
    if len(raw) > MAX_INPUT_CHARS:
        user_content += "\n\n[truncated for parsing]"

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    )

    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("Empty response from OpenAI")

    data: dict[str, Any] = json.loads(content)
    intent = QueryIntent.model_validate(data)

    return PreparedQuery(
        raw=raw,
        embed_text=_format_embed_text(intent.embed_text),
        exclude_terms=_normalize_exclude_titles(intent.exclude_titles),
    )


def prepare_query(raw_input: str) -> PreparedQuery:
    """
    Prepare query for embedding: LLM parse when enabled and keyed, else regex heuristic.
    """
    raw = _normalize_whitespace(raw_input or "")
    if not raw:
        return prepare_query_heuristic("")

    if not _llm_enabled():
        return prepare_query_heuristic(raw)

    try:
        return parse_query_with_llm(raw)
    except (ValidationError, json.JSONDecodeError, RuntimeError, Exception) as exc:
        logger.warning("LLM query parse failed, using heuristic fallback: %s", exc)
        return prepare_query_heuristic(raw)
