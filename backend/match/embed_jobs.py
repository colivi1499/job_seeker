"""Offline CLI: embed all jobs from SQLite into data/embeddings.npz."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.db import DEFAULT_DB_PATH, count_jobs, get_jobs
from backend.match.embeddings import (
    DEFAULT_MODEL_NAME,
    embed_texts,
    job_to_embed_text,
)

DEFAULT_EMBEDDINGS_PATH = ROOT / "data" / "embeddings.npz"


def save_embeddings(
    ids: list[str],
    vectors: np.ndarray,
    path: Path,
    *,
    model_name: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        ids=np.asarray(ids, dtype=object),
        vectors=vectors.astype(np.float32),
        model_name=np.asarray(model_name),
    )


def load_embeddings(path: Path | str = DEFAULT_EMBEDDINGS_PATH) -> dict:
    """Load embeddings.npz → {ids: list[str], vectors: ndarray, model_name: str}."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Embeddings not found at {path}. Run: python -m backend.match.embed_jobs"
        )
    data = np.load(path, allow_pickle=True)
    ids = [str(x) for x in data["ids"].tolist()]
    vectors = np.asarray(data["vectors"], dtype=np.float32)
    model_name = str(data["model_name"].item()) if "model_name" in data.files else DEFAULT_MODEL_NAME
    return {"ids": ids, "vectors": vectors, "model_name": model_name}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Embed jobs from SQLite into embeddings.npz")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--out", type=Path, default=DEFAULT_EMBEDDINGS_PATH)
    parser.add_argument("--model", default=DEFAULT_MODEL_NAME)
    parser.add_argument("--batch-size", type=int, default=32)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    n = count_jobs(args.db)
    if n == 0:
        print(f"No jobs in {args.db}. Run ingestion first.", file=sys.stderr)
        return 1

    jobs = get_jobs(args.db)
    print(f"Embedding {len(jobs)} jobs with {args.model}…")
    texts = [job_to_embed_text(j) for j in jobs]
    ids = [str(j["id"]) for j in jobs]
    vectors = embed_texts(texts, model_name=args.model, batch_size=args.batch_size)

    save_embeddings(ids, vectors, args.out, model_name=args.model)
    print(f"Wrote {vectors.shape[0]} vectors (dim={vectors.shape[1]}) → {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
