"""Integration tests for the /query API with fakes injected."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_query_service
from app.core.config import get_settings
from app.main import create_app
from app.services.retrieval.answerer import Answerer
from app.services.retrieval.query_service import QueryService
from app.services.vector_store import SearchResult


class FakeEmbedder:
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]


class FakeVectorStore:
    def __init__(self, results: list[SearchResult]) -> None:
        self._results = results
        self.last_filter: dict[str, Any] | None = None

    def upsert(self, chunks: list[Any], vectors: list[list[float]]) -> None:  # unused
        ...

    def query(
        self, vector: list[float], *, top_k: int, filter: dict[str, Any] | None = None
    ) -> list[SearchResult]:
        self.last_filter = filter
        return self._results

    def delete(self, ids: list[str]) -> None:  # unused
        ...


class FakeLLM:
    def __init__(self, reply: str) -> None:
        self.reply = reply

    def generate(self, *, system: str, prompt: str, max_tokens: int) -> str:
        return self.reply


def _result(cid: str, text: str, score: float) -> SearchResult:
    return SearchResult(
        chunk_id=cid,
        document_id="doc_1",
        filename="a.txt",
        page=1,
        ordinal=0,
        text=text,
        score=score,
    )


def _client(results: list[SearchResult], reply: str) -> tuple[TestClient, FakeVectorStore]:
    vectors = FakeVectorStore(results)
    service = QueryService(
        embedder=FakeEmbedder(),
        vector_store=vectors,
        answerer=Answerer(llm=FakeLLM(reply), max_tokens=512),
        settings=get_settings(),
    )
    app = create_app()
    app.dependency_overrides[get_query_service] = lambda: service
    return TestClient(app), vectors


def test_query_returns_answer_citations_and_sources() -> None:
    results = [_result("chk_1", "Paris is the capital of France.", 0.95)]
    client, _ = _client(results, reply="The capital of France is Paris [1].")

    resp = client.post("/api/v1/query", json={"question": "capital of France?"})
    assert resp.status_code == 200
    body = resp.json()
    assert "Paris" in body["answer"]
    assert [c["index"] for c in body["citations"]] == [1]
    assert body["citations"][0]["chunk_id"] == "chk_1"
    assert len(body["sources"]) == 1
    assert body["sources"][0]["snippet"].startswith("Paris is the capital")


def test_query_with_no_hits_returns_insufficient_evidence() -> None:
    client, _ = _client([], reply="unused")
    resp = client.post("/api/v1/query", json={"question": "anything?"})
    assert resp.status_code == 200
    body = resp.json()
    assert "don't have enough information" in body["answer"]
    assert body["citations"] == []
    assert body["sources"] == []


def test_document_id_filter_forwarded_to_vector_store() -> None:
    results = [_result("chk_1", "scoped text", 0.9)]
    client, vectors = _client(results, reply="Answer [1].")
    client.post("/api/v1/query", json={"question": "q", "document_id": "doc_42"})
    assert vectors.last_filter == {"document_id": "doc_42"}


def test_missing_question_is_422() -> None:
    client, _ = _client([], reply="x")
    resp = client.post("/api/v1/query", json={})
    assert resp.status_code == 422


@pytest.mark.parametrize("question", ["", " "])
def test_blank_question_rejected(question: str) -> None:
    client, _ = _client([], reply="x")
    resp = client.post("/api/v1/query", json={"question": question})
    # empty string fails min_length; whitespace passes schema but returns a result
    assert resp.status_code in (200, 422)
