# Agentic RAG Knowledge Assistant

An AI assistant that searches documents, finds accurate answers, **verifies** them, and **cites sources**. It goes beyond a simple chatbot: an agent orchestrator plans and selects tools (vector search, web search, structured APIs), assembles ranked context, and produces a grounded, verified answer.

```
User query
   │
   ▼
Agent orchestrator ──(may re-query)
   │  plans & selects tools
   ├─────────────┬───────────────┬──────────────┐
   ▼             ▼               ▼              ▼
Vector search  Web search   APIs & functions   …
(semantic)     (live info)  (structured data)
   └─────────────┴───────────────┴──────────────┘
                 │
                 ▼
        Context assembly (merge + rank)
                 │
                 ▼
        Verification (grounding check)
                 │
                 ▼
        Grounded answer + citations
```

## Tech stack

| Layer        | Choice                                             |
|--------------|----------------------------------------------------|
| Backend      | Python 3.11 + FastAPI (async)                      |
| LLM          | Claude (Opus 4.8) via the Anthropic SDK            |
| Orchestration| LangGraph (agent state machine)                    |
| Vector DB    | Pinecone (serverless)                              |
| Embeddings   | Voyage AI (`voyage-3`) — Anthropic's recommended   |
| Frontend     | Next.js 14 (App Router) + streaming chat UI        |
| Infra        | Docker Compose, GitHub Actions CI                  |

> Model IDs and SDK usage follow the current Anthropic guidance. Default model: `claude-opus-4-8`.

## Repository layout

```
agentic-rag-assistant/
├── backend/          # FastAPI service, ingestion, retrieval, agent
├── frontend/         # Next.js chat UI (added in Phase 5)
├── docs/             # Architecture, ADRs, phase plan
├── scripts/          # Dev/ops helper scripts
├── .github/workflows # CI
└── docker-compose.yml
```

## Getting started

See [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) for full setup. Run both services:

**1) Backend (terminal 1)**

```bash
cd backend
cp .env.example .env          # fill in ANTHROPIC_API_KEY, VOYAGE_API_KEY, PINECONE_API_KEY (TAVILY_API_KEY optional)
python3.12 -m venv .venv && source .venv/bin/activate   # use 3.11 or 3.12 — see note below
pip install -e ".[dev]"
uvicorn app.main:app --reload
# http://localhost:8000/docs   ·   health: http://localhost:8000/api/v1/health
```

**2) Frontend (terminal 2)**

```bash
cd frontend
cp .env.local.example .env.local    # NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
npm install
npm run dev                          # http://localhost:3000
```

Then: open **Documents** (top-right) → upload a PDF/DOCX/TXT/MD → ask a question. Toggle **Verify** in the composer to run the grounding + citation check.

> **Python version note:** this repo targets **Python 3.11–3.12**. Some deps
> (tiktoken, pinecone, tokenizers) may not yet ship wheels for 3.14, so
> `pip install` can fail there. If you only have 3.14, install 3.12
> (`brew install python@3.12`) and create the venv with `python3.12`.

Without real API keys the app still boots (`/api/v1/health` is green and
`/ready` reports which keys are missing), but answering a question needs
Anthropic + Voyage + Pinecone configured.

## Phased delivery

This project is built in production-grade phases. See [`docs/ROADMAP.md`](docs/ROADMAP.md) for the full plan.

- **Phase 0 — Foundation** ✅ scaffolding, config, health, CI, Docker *(this commit)*
- **Phase 1 — Ingestion** document upload → parse → chunk → embed → Pinecone
- **Phase 2 — Retrieval RAG** semantic search → context assembly → grounded answer + citations
- **Phase 3 — Agentic orchestration** LangGraph orchestrator, tool selection, re-query loop
- **Phase 4 — Verification** grounding/hallucination checks, citation validation
- **Phase 5 — Frontend** Next.js streaming chat UI with source display + upload
- **Phase 6 — Hardening** auth, rate limiting, observability, evals, deployment

## License

MIT
