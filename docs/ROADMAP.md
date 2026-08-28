# Delivery Roadmap

Each phase is independently shippable, testable, and demoable. A phase is "done" only when it has: working code, tests, docs updated, and a manual verification path.

---

## Phase 0 — Foundation & Scaffolding ✅

**Goal:** a running, well-structured service skeleton with production hygiene from day one.

- [x] Monorepo layout (backend / frontend / docs / scripts)
- [x] `pyproject.toml` with pinned deps, dev extras, tooling (ruff, black, mypy, pytest)
- [x] Typed settings via `pydantic-settings` (`app/core/config.py`)
- [x] Structured logging (`app/core/logging.py`)
- [x] FastAPI app factory + `/health` and `/ready` endpoints
- [x] Global error handling & request-id middleware
- [x] `.env.example`, `.gitignore`, `.dockerignore`
- [x] Dockerfile + docker-compose
- [x] GitHub Actions CI (lint + type + test)

**Demo:** `GET /health` returns `{"status": "ok"}`, `/docs` renders.

---

## Phase 1 — Ingestion Pipeline

**Goal:** turn raw documents into searchable vectors.

- [ ] `POST /documents` upload (PDF, DOCX, TXT, MD) with validation
- [ ] Parsers per file type → normalized text + metadata
- [ ] Chunking (recursive, token-aware, with overlap) + chunk metadata (source, page, offsets)
- [ ] Embeddings via Voyage (`voyage-3`), batched
- [ ] Upsert to Pinecone with metadata; idempotent by content hash
- [ ] `GET /documents`, `DELETE /documents/{id}`
- [ ] Background task / job status for large files
- [ ] Tests: parser fixtures, chunker boundaries, mocked embed+upsert

**Demo:** upload a PDF, see chunks appear in Pinecone, list & delete it.

---

## Phase 2 — Retrieval RAG

**Goal:** answer a question grounded in the corpus, with citations.

- [ ] `POST /query` (non-agentic baseline)
- [ ] Query embedding → Pinecone top-k with metadata filters
- [ ] Context assembly: dedupe, rerank, token-budget packing
- [ ] Answer generation with Claude + citation-enforcing prompt
- [ ] Response schema: `answer`, `citations[]`, `usage`
- [ ] Streaming variant (`/query/stream`)
- [ ] Tests: retrieval ranking, citation extraction, prompt contract

**Demo:** ask a question, get an answer that cites the uploaded doc.

---

## Phase 3 — Agentic Orchestration (LangGraph)

**Goal:** an agent that plans, selects tools, and re-queries.

- [ ] LangGraph state graph: `plan → route → tools → assemble → generate`
- [ ] Tools: `vector_search`, `web_search`, `structured_api` (function calling)
- [ ] Router/planner node chooses tools per query
- [ ] Re-query loop when context is insufficient (bounded)
- [ ] Trace/telemetry per node
- [ ] Tests: routing decisions, loop termination, tool contracts

**Demo:** a query needing live info triggers web search + vector search, merged.

---

## Phase 4 — Verification & Citations

**Goal:** trust. Catch hallucinations; guarantee citations map to real sources.

- [ ] Grounding check: each claim ↔ supporting chunk (LLM-as-judge)
- [ ] Citation validation: cited spans exist in retrieved context
- [ ] Confidence scoring + "insufficient evidence" path
- [ ] Optional self-correction re-query on low grounding
- [ ] Tests: adversarial hallucination cases, citation integrity

**Demo:** an unanswerable question returns "insufficient evidence" instead of a made-up answer.

---

## Phase 5 — Frontend (Next.js)

**Goal:** a polished chat UI.

- [ ] Next.js 14 App Router + Tailwind
- [ ] Streaming chat with token rendering
- [ ] Source/citation panel (click to view chunk)
- [ ] Document upload + management UI
- [ ] Agent "reasoning steps" / trace view
- [ ] Env-based API client, error/loading states

**Demo:** end-to-end chat with visible citations and upload.

---

## Phase 6 — Production Hardening

**Goal:** ship it.

- [ ] AuthN/Z (API keys or OAuth), per-tenant isolation
- [ ] Rate limiting + request quotas
- [ ] Observability: structured logs, metrics, tracing (OpenTelemetry)
- [ ] Eval suite (retrieval recall, answer faithfulness) in CI
- [ ] Caching (prompt cache, embedding cache)
- [ ] Deployment (container registry + IaC), secrets management
- [ ] Load test + cost dashboard

**Demo:** deployed URL, dashboards, passing eval gate.

---

## Conventions

- **Branches:** `phase-N/<feature>`; PR into `main` with CI green.
- **ADRs:** significant decisions recorded in `docs/adr/`.
- **Definition of done:** code + tests + docs + manual verify.
