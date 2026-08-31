"""Match-set summary generation. Stub now; swap in one LLM call later."""

from __future__ import annotations

from typing import Any


def summarize_matches(query_text: str, matches: list[dict[str, Any]]) -> str:
    """
    Produce a short natural-language summary of the match set (not per-job).

    Stub: deterministic template so /api/match works without an API key.
    Replace with one Claude Haiku / GPT-4o-mini call when ready.
    """
    query = (query_text or "").strip()
    if not matches:
        return (
            f"No strong matches found for your query"
            f"{f' ({query[:120]}…)' if len(query) > 120 else (f' ({query})' if query else '')}. "
            "Try broader skills, a different role title, or a less specific location."
        )

    n = len(matches)
    scores = [float(m.get("score") or 0.0) for m in matches]
    avg = sum(scores) / n if n else 0.0
    best = matches[0]
    best_job = best.get("job") or {}
    best_title = best_job.get("title") or "a role"
    best_company = best_job.get("company") or "an employer"
    best_score = float(best.get("score") or 0.0)

    companies = []
    seen = set()
    for m in matches:
        company = (m.get("job") or {}).get("company")
        if company and company not in seen:
            seen.add(company)
            companies.append(company)
        if len(companies) >= 3:
            break
    company_phrase = ", ".join(companies)
    if len(seen) > 3:
        company_phrase += ", and others"

    locations = []
    seen_loc = set()
    for m in matches:
        loc = (m.get("job") or {}).get("location")
        if loc and loc not in seen_loc:
            seen_loc.add(loc)
            locations.append(loc)
        if len(locations) >= 3:
            break

    loc_bit = ""
    if locations:
        loc_bit = f" Locations in this set include {', '.join(locations)}."

    return (
        f"Found {n} relevant postings (avg similarity {avg:.2f}). "
        f"Top match: {best_title} at {best_company} (score {best_score:.2f}). "
        f"Other employers in the set: {company_phrase}."
        f"{loc_bit}"
    )
