"""Aggregate stats over a match set for chart payloads (POC viz contract)."""

from __future__ import annotations

from collections import Counter
from typing import Any


def _mid_salary(job: dict[str, Any]) -> float | None:
    lo = job.get("salary_min")
    hi = job.get("salary_max")
    if lo is None and hi is None:
        return None
    if lo is None:
        return float(hi)
    if hi is None:
        return float(lo)
    return (float(lo) + float(hi)) / 2.0


def build_viz(matches: list[dict[str, Any]], *, top_n_skills: int = 10, top_n_locations: int = 10) -> dict[str, Any]:
    """
    Build viz payload for /api/match:
      salary_hist: { bins: number[], counts: number[] }
      top_skills:  [{ skill: string, count: number }, ...]
      locations:   [{ location: string, count: number }, ...]
    """
    jobs = [m["job"] for m in matches if m.get("job")]

    # --- salary histogram ---
    salaries = [s for s in (_mid_salary(j) for j in jobs) if s is not None and s > 0]
    if salaries:
        # Fixed-ish bins across observed range (at least 1 bin)
        n_bins = min(8, max(1, len(set(salaries))))
        counts_arr, edges = _histogram(salaries, n_bins)
        # Use bin centers for a simple line/bar x-axis
        bins = [round((edges[i] + edges[i + 1]) / 2.0, 2) for i in range(len(counts_arr))]
        salary_hist = {"bins": bins, "counts": counts_arr}
    else:
        salary_hist = {"bins": [], "counts": []}

    # --- top skills ---
    skill_counter: Counter[str] = Counter()
    for job in jobs:
        for skill in job.get("skills") or []:
            name = str(skill).strip()
            if name:
                skill_counter[name] += 1
    top_skills = [
        {"skill": skill, "count": count}
        for skill, count in skill_counter.most_common(top_n_skills)
    ]

    # --- locations ---
    loc_counter: Counter[str] = Counter()
    for job in jobs:
        loc = (job.get("location") or "").strip() or "Unknown"
        # If multiple locations joined by comma, count each
        parts = [p.strip() for p in loc.split(",") if p.strip()]
        if len(parts) >= 2 and all(len(p) <= 3 or p.isupper() for p in parts[-1:]):
            # keep full "City, ST" as one label when it looks like city/state
            loc_counter[loc] += 1
        elif "," in loc and len(parts) > 2:
            for p in parts:
                loc_counter[p] += 1
        else:
            loc_counter[loc] += 1

    locations = [
        {"location": location, "count": count}
        for location, count in loc_counter.most_common(top_n_locations)
    ]

    return {
        "salary_hist": salary_hist,
        "top_skills": top_skills,
        "locations": locations,
    }


def _histogram(values: list[float], n_bins: int) -> tuple[list[int], list[float]]:
    lo = min(values)
    hi = max(values)
    if hi <= lo:
        return [len(values)], [lo, hi if hi > lo else lo + 1.0]

    width = (hi - lo) / n_bins
    edges = [lo + i * width for i in range(n_bins + 1)]
    edges[-1] = hi  # include max in last bin
    counts = [0] * n_bins
    for v in values:
        if v >= hi:
            counts[-1] += 1
            continue
        idx = int((v - lo) / width)
        idx = min(max(idx, 0), n_bins - 1)
        counts[idx] += 1
    return counts, edges
