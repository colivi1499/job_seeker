"""In-memory cosine similarity ranking against precomputed job embeddings."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from backend.db import get_job, get_jobs
from backend.match.embed_jobs import DEFAULT_EMBEDDINGS_PATH, load_embeddings
from backend.match.embeddings import DEFAULT_MODEL_NAME, embed_query


@dataclass
class MatchIndex:
    ids: list[str]
    vectors: np.ndarray  # (n, d), L2-normalized
    model_name: str
    jobs_by_id: dict[str, dict[str, Any]]

    @classmethod
    def load(
        cls,
        embeddings_path: Path | str = DEFAULT_EMBEDDINGS_PATH,
        db_path: Path | str | None = None,
    ) -> "MatchIndex":
        blob = load_embeddings(embeddings_path)
        ids: list[str] = blob["ids"]
        vectors: np.ndarray = blob["vectors"]
        model_name: str = blob["model_name"]

        # Prefer full job rows from DB; fall back to empty if missing.
        jobs = get_jobs(db_path)
        jobs_by_id = {str(j["id"]): j for j in jobs}
        # Ensure every embedding id has an entry (may be None → skip later)
        for job_id in ids:
            if job_id not in jobs_by_id:
                row = get_job(job_id, db_path)
                if row:
                    jobs_by_id[job_id] = row

        # L2-normalize in case file was saved without normalization
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms = np.maximum(norms, 1e-12)
        vectors = vectors / norms

        return cls(ids=ids, vectors=vectors.astype(np.float32), model_name=model_name, jobs_by_id=jobs_by_id)

    def rank(self, query_text: str, *, top_k: int = 15) -> list[dict[str, Any]]:
        """Return top_k matches: [{job, score}, ...] sorted by score desc."""
        if not self.ids:
            return []

        query_vec = embed_query(query_text, model_name=self.model_name or DEFAULT_MODEL_NAME)
        # cosine == dot when both sides are L2-normalized
        scores = self.vectors @ query_vec  # (n,)
        k = min(top_k, len(self.ids))
        # argpartition for speed, then sort the top slice
        if k < len(scores):
            idx = np.argpartition(-scores, k)[:k]
            idx = idx[np.argsort(-scores[idx])]
        else:
            idx = np.argsort(-scores)

        matches: list[dict[str, Any]] = []
        for i in idx:
            job_id = self.ids[int(i)]
            job = self.jobs_by_id.get(job_id)
            if not job:
                continue
            matches.append({
                "job": job,
                "score": float(round(float(scores[int(i)]), 4)),
            })
        return matches
