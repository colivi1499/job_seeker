"""FastAPI app: POST /api/match against precomputed job embeddings."""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.match.ranker import MatchIndex
from backend.match.summary import summarize_matches
from backend.match.viz import build_viz

_index: MatchIndex | None = None


class MatchRequest(BaseModel):
    query_text: str = Field(..., min_length=1, description="Resume text or desired-job description")


class MatchResponse(BaseModel):
    matches: list[dict[str, Any]]
    summary: str
    viz: dict[str, Any]


def get_index() -> MatchIndex:
    if _index is None:
        raise HTTPException(
            status_code=503,
            detail="Match index not loaded. Run: python -m backend.match.embed_jobs",
        )
    return _index


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _index
    try:
        _index = MatchIndex.load()
        print(f"Loaded match index: {len(_index.ids)} jobs, model={_index.model_name}")
    except FileNotFoundError as exc:
        print(f"WARNING: {exc}")
        _index = None
    yield
    _index = None


app = FastAPI(title="Job Seeker Matching API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "index_loaded": _index is not None,
        "n_jobs": len(_index.ids) if _index else 0,
    }


@app.post("/api/match", response_model=MatchResponse)
def match(req: MatchRequest, top_k: int = 15) -> MatchResponse:
    index = get_index()
    top_k = max(1, min(top_k, 50))
    matches = index.rank(req.query_text, top_k=top_k)
    summary = summarize_matches(req.query_text, matches)
    viz = build_viz(matches)
    return MatchResponse(matches=matches, summary=summary, viz=viz)


def main() -> None:
    import uvicorn

    uvicorn.run("backend.api:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    main()
