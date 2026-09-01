# job_seeker

Paste a resume or job description and get semantically ranked job matches from a local SQLite database.

**Stack:** Next.js frontend, FastAPI backend, SQLite, Adzuna job ingest, MiniLM embeddings, optional GPT-4o-mini query parsing.

## Prerequisites

- Python 3.11+ (3.12 recommended)
- Node.js 18+

## Setup

### 1. Python backend

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Set Adzuna credentials in `.env` (or create `adzunaconfig.txt` in the repo root — gitignored):

```
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key
```

Get keys at [developer.adzuna.com](https://developer.adzuna.com/).

Optional: set `OPENAI_API_KEY` in `.env` for LLM query parsing (falls back to heuristics if missing).

### 2. Frontend

```bash
npm install
```

## Populate the job database

Initialize the schema and ingest jobs from Adzuna:

```bash
python -m backend.ingest.run --pages 20 --location "Utah" --query "software engineer"
```

- `--pages` — max pages to fetch (50 jobs/page; default 50)
- `--query` — search term (e.g. `software engineer`, `data science`)
- `--location` — location filter (e.g. `Utah`, `New York`)
- `--sleep` — seconds between API calls (default 0.25)

Or run the bundled multi-query script:

```bash
./populatedb.sh
```

Requires `ADZUNA_APP_ID` and `ADZUNA_APP_KEY` in the environment or `adzunaconfig.txt`.

## Build embeddings

After ingesting (or whenever job data changes), rebuild the embedding index:

```bash
python -m backend.match.embed_jobs
```

Writes `data/embeddings.npz` (gitignored).

## Run

**Terminal 1 — API** (port 8000):

```bash
python -m backend.api
```

**Terminal 2 — frontend** (port 3000):

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Paste text or upload a PDF resume, then search.

Health check: `GET http://127.0.0.1:8000/health`

## API

`POST /api/match`

```json
{ "query_text": "software engineer with Python experience" }
```

Returns ranked `matches`, a text `summary`, and `viz` aggregates (`salary_hist`, `top_skills`, `locations`).

## Project layout

```
app/                    # Next.js pages
frontend/src/           # React components (JobCard, types)
backend/
  api.py                # FastAPI app
  db.py                 # SQLite helpers
  ingest/
    adzuna.py           # Adzuna API client (active)
    muse.py             # The Muse client (legacy, unused)
    run.py              # Ingest CLI
  match/
    embeddings.py       # MiniLM embed + job text formatting
    embed_jobs.py       # Offline embedding CLI
    ranker.py           # Cosine similarity ranking
    query.py            # Heuristic query parsing
    query_llm.py        # Optional GPT query parsing
    summary.py          # Match-set summary
    viz.py              # Chart payloads
data/
  jobs.db               # SQLite (gitignored)
  embeddings.npz        # Precomputed vectors (gitignored)
```

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ADZUNA_APP_ID` | For ingest | Adzuna application ID |
| `ADZUNA_APP_KEY` | For ingest | Adzuna application key |
| `OPENAI_API_KEY` | Optional | Enables LLM query parsing |
| `OPENAI_MODEL` | Optional | Default `gpt-4o-mini` |
| `USE_LLM_QUERY_PARSE` | Optional | Default `true`; set `false` to use heuristics only |
