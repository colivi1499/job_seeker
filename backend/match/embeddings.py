"""Shared embedding helpers for offline job vectors and online query vectors."""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Sequence

import numpy as np

DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DESCRIPTION_MAX_CHARS = 2000


def job_to_embed_text(job: dict[str, Any]) -> str:
    """Build the text used for a job embedding."""
    title = (job.get("title") or "").strip()
    company = (job.get("company") or "").strip()
    location = (job.get("location") or "").strip()
    description = (job.get("description") or "").strip()
    if len(description) > DESCRIPTION_MAX_CHARS:
        description = description[:DESCRIPTION_MAX_CHARS]

    skills_raw = job.get("skills") or []
    if isinstance(skills_raw, str):
        skills_str = skills_raw.strip()
    else:
        skills_str = ", ".join(str(s).strip() for s in skills_raw if s)

    parts: list[str] = []
    if title:
        parts.extend([title, title])  # repeat title to up-weight role in the vector
    if company:
        parts.append(company)
    if location:
        parts.append(location)
    if skills_str:
        parts.append(f"Skills: {skills_str}")
    if description:
        parts.append(description)

    return ". ".join(parts) if parts else title or "unknown job"


@lru_cache(maxsize=2)
def load_model(model_name: str = DEFAULT_MODEL_NAME):
    """Load sentence-transformers model once (cached)."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def embed_texts(
    texts: Sequence[str],
    *,
    model_name: str = DEFAULT_MODEL_NAME,
    batch_size: int = 32,
    normalize: bool = True,
) -> np.ndarray:
    """
    Embed texts into an (n, d) float32 matrix.
    When normalize=True, rows are L2-normalized so cosine == dot product.
    """
    model = load_model(model_name)
    if not texts:
        dim = int(model.get_sentence_embedding_dimension())
        return np.zeros((0, dim), dtype=np.float32)

    vectors = model.encode(
        list(texts),
        batch_size=batch_size,
        show_progress_bar=len(texts) > 16,
        convert_to_numpy=True,
        normalize_embeddings=normalize,
    )
    return np.asarray(vectors, dtype=np.float32)


def embed_query(
    query_text: str,
    *,
    model_name: str = DEFAULT_MODEL_NAME,
    embed_text: str | None = None,
) -> np.ndarray:
    """Embed a single user query → shape (d,). Pass embed_text to skip re-parsing."""
    if embed_text is None:
        from backend.match.query import prepare_query

        embed_text = prepare_query(query_text).embed_text
    text = (embed_text or "").strip() or " "
    return embed_texts([text], model_name=model_name, normalize=True)[0]
