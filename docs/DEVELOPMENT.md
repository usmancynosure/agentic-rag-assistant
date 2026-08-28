# Development Guide

## Prerequisites

- Python 3.11+
- Docker (optional, for containerized run)
- API keys: **Anthropic**, **Voyage AI**, **Pinecone**

## Local setup

```bash
cd backend
cp .env.example .env
# edit .env and add your keys

python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

uvicorn app.main:app --reload
```

Open http://localhost:8000/docs for the interactive API.

Health check:

```bash
curl localhost:8000/api/v1/health
curl localhost:8000/api/v1/ready
```

## Quality gates

```bash
ruff check .        # lint
black .             # format
mypy app            # types
pytest              # tests + coverage
```

All four run in CI on every PR.

## Docker

```bash
docker compose up --build
```

## Project structure

```
backend/app/
├── main.py            # app factory
├── core/              # config, logging, errors, middleware
├── api/               # routers (health now; documents/query later)
├── services/          # ingestion + retrieval (Phase 1/2)
├── agent/             # LangGraph orchestrator (Phase 3)
├── models/            # domain models
└── schemas/           # request/response DTOs
```

## Branching & commits

- Work on `phase-N/<feature>` branches.
- Keep CI green before merging to `main`.
- Record notable decisions as ADRs in `docs/adr/`.
