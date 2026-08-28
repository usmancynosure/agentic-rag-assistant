"""Integration tests for verification wired into /query and /agent/query."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from app.api.deps import get_query_service, get_verification_service
from app.core.config import get_settings
from app.main import create_app
from app.services.retrieval.answerer import Answerer
from app.services.retrieval.query_service import QueryService
from app.services.vector_store import SearchResult
from app.services.verification.grounding import GroundingVerifier
from app.services.verification.service import VerificationService


class FakeEmbedder:
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.0, 0.0, 0.0] for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        return [0.0, 0.0, 0.0]


class FakeVectorStore:
    def __init__(self, results: list[SearchResult]) -> None:
        self._results = results

    def upsert(self, chunks: list[Any], vectors: list[list[float]]) -> None: ...

    def query(
        self, vector: list[float], *, top_k: int, filter: dict[str, Any] | None = None
    ) -> list[SearchResult]:
        return self._results

    def delete(self, ids: list[str]) -> None: ...


class FakeLLM:
    def __init__(self, reply: str) -> None:
        self.reply = reply
        self.calls = 0

    def generate(self, *, system: str, prompt: str, max_tokens: int) -> str:
        self.calls += 1
        return self.reply


def _result() -> SearchResult:
    return SearchResult(
        chunk_id="chk_1",
        document_id="doc_1",
        filename="a.txt",
        page=1,
        ordinal=0,
        text="Paris is the capital of France.",
        score=0.95,
    )


def _client(answer_reply: str, grounding_reply: str) -> tuple[TestClient, FakeLLM]:
    query_service = QueryService(
        embedder=FakeEmbedder(),
        vector_store=FakeVectorStore([_result()]),
        answerer=Answerer(llm=FakeLLM(answer_reply), max_tokens=256),
        settings=get_settings(),
    )
    grounding_llm = FakeLLM(grounding_reply)
    verification = VerificationService(grounding_verifier=GroundingVerifier(llm=grounding_llm))

    app = create_app()
    app.dependency_overrides[get_query_service] = lambda: query_service
    app.dependency_overrides[get_verification_service] = lambda: verification
    return TestClient(app), grounding_llm


def test_query_without_verify_has_null_verification_and_no_judge_call() -> None:
    client, grounding_llm = _client(
        "The capital is Paris [1].", '{"grounded": true, "score": 1.0, "unsupported_claims": []}'
    )
    resp = client.post("/api/v1/query", json={"question": "capital?"})
    body = resp.json()
    assert body["verification"] is None
    assert grounding_llm.calls == 0  # verifier not invoked


def test_query_with_verify_includes_verification_block() -> None:
    client, grounding_llm = _client(
        "The capital of France is Paris [1].",
        '{"grounded": true, "score": 1.0, "unsupported_claims": [], "reasoning": "ok"}',
    )
    resp = client.post("/api/v1/query", json={"question": "capital?", "verify": True})
    body = resp.json()
    v = body["verification"]
    assert v is not None
    assert v["trustworthy"] is True
    assert v["verdict"] == "high"
    assert v["confidence"] == 1.0
    assert v["grounded"] is True
    assert grounding_llm.calls == 1


def test_query_with_verify_flags_hallucination() -> None:
    client, _ = _client(
        "Paris has exactly 12 million residents [1].",
        '{"grounded": false, "score": 0.2, "unsupported_claims": ["12 million residents"]}',
    )
    resp = client.post("/api/v1/query", json={"question": "population?", "verify": True})
    v = resp.json()["verification"]
    assert v["grounded"] is False
    assert v["trustworthy"] is False
    assert "12 million residents" in v["unsupported_claims"]
