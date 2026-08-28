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

## Phase 1 — Ingestion Pipeline ✅

**Goal:** turn raw documents into searchable vectors.

- [x] `POST /documents` upload (PDF, DOCX, TXT, MD) with validation *(1f)*
- [x] Parsers per file type → normalized text + metadata *(1b)*
- [x] Chunking (recursive, token-aware, with overlap) + chunk metadata (source, page, offsets) *(1c)*
- [x] Embeddings via Voyage (`voyage-3`), batched *(1d)*
- [x] Upsert to Pinecone with metadata; idempotent by content hash *(1e, 1f)*
- [x] `GET /documents`, `GET /documents/{id}`, `DELETE /documents/{id}` *(1f)*
- [x] Tests: models, parsers, chunker, embeddings, vector store, API *(40 tests)*
- [ ] Background task / job status for large files *(deferred to Phase 6)*

**Delivered as chunks:** 1a models · 1b parsers · 1c chunker · 1d embeddings · 1e vector store · 1f service + API.

**Demo:** upload a PDF, see chunks appear in Pinecone, list & delete it.

---

## Phase 2 — Retrieval RAG ✅

**Goal:** answer a question grounded in the corpus, with citations.

- [x] `POST /query` (non-agentic baseline) *(2c)*
- [x] Query embedding → Pinecone top-k with metadata filters *(2c)*
- [x] Context assembly: dedupe, rerank, token-budget packing *(2a)*
- [x] Answer generation with Claude + citation-enforcing prompt *(2b)*
- [x] Response schema: `answer`, `citations[]`, `sources[]` *(2c)*
- [x] Streaming variant (`/query/stream`, SSE) *(2d)*
- [x] Tests: context, citation extraction, prompt contract, query + stream APIs

**Delivered as chunks:** 2a context assembly · 2b answerer + LLM client · 2c query API · 2d streaming SSE.

**Demo:** ask a question, get an answer that cites the uploaded doc.

---

## Phase 3 — Agentic Orchestration (LangGraph) ✅

**Goal:** an agent that plans, selects tools, and re-queries.

- [x] LangGraph state graph: `plan → tools → assemble → generate` + re-query edge *(3a, 3e)*
- [x] Tools: `vector_search` *(3b)*, `web_search` (Tavily) *(3c)* behind a uniform `Tool` interface
- [x] Router/planner node chooses tools per query *(3d)*
- [x] Re-query loop when context is insufficient (bounded by `max_iterations`) *(3e)*
- [x] `POST /agent/query` returning answer, citations, sources, `tools_run`, `iterations` *(3f)*
- [x] Tests: loop control, tool contracts, planner parsing, merge, tool-switch re-query, API *(91 tests)*
- [ ] `structured_api` tool (function calling) *(deferred; interface is ready)*

**Delivered as chunks:** 3a state+graph · 3b vector tool · 3c web tool · 3d planner · 3e merge+orchestrator · 3f API.

**Demo:** a query needing live info triggers web search + vector search, merged, with a bounded re-query.

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
