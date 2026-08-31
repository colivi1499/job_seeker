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

    parts = [p for p in (title, company, location, description) if p]
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
) -> np.ndarray:
    """Embed a single user query → shape (d,)."""
    text = (query_text or "").strip() or " "
    return embed_texts([text], model_name=model_name, normalize=True)[0]
