"""Integration tests for the streaming /query/stream endpoint."""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

from fastapi.testclient import TestClient

from app.api.deps import get_query_service
from app.core.config import get_settings
from app.main import create_app
from app.services.retrieval.answerer import Answerer
from app.services.retrieval.query_service import QueryService
from app.services.vector_store import SearchResult


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


class FakeStreamingLLM:
    """Yields the reply split into word tokens; also supports generate()."""

    def __init__(self, reply: str) -> None:
        self.reply = reply

    def generate(self, *, system: str, prompt: str, max_tokens: int) -> str:
        return self.reply

    def stream(self, *, system: str, prompt: str, max_tokens: int) -> Iterator[str]:
        for word in self.reply.split(" "):
            yield word + " "


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


def _client(results: list[SearchResult], reply: str) -> TestClient:
    service = QueryService(
        embedder=FakeEmbedder(),
        vector_store=FakeVectorStore(results),
        answerer=Answerer(llm=FakeStreamingLLM(reply), max_tokens=256),
        settings=get_settings(),
    )
    app = create_app()
    app.dependency_overrides[get_query_service] = lambda: service
    return TestClient(app)


def _parse_sse(body: str) -> list[tuple[str, dict]]:
    events: list[tuple[str, dict]] = []
    for block in body.strip().split("\n\n"):
        if not block.strip():
            continue
        lines = block.split("\n")
        event = next(x[len("event: ") :] for x in lines if x.startswith("event: "))
        data = next(x[len("data: ") :] for x in lines if x.startswith("data: "))
        events.append((event, json.loads(data)))
    return events


def test_stream_emits_sources_tokens_and_done() -> None:
    results = [_result("chk_1", "Paris is the capital of France.", 0.9)]
    client = _client(results, reply="The capital is Paris [1].")

    resp = client.post("/api/v1/query/stream", json={"question": "capital?"})
    assert resp.status_code == 200
    events = _parse_sse(resp.text)

    kinds = [e[0] for e in events]
    assert kinds[0] == "sources"
    assert "token" in kinds
    assert kinds[-1] == "done"

    # sources event lists the retrieved passage
    sources_evt = events[0][1]
    assert sources_evt["sources"][0]["chunk_id"] == "chk_1"

    # tokens reconstruct the answer
    tokens = "".join(e[1]["text"] for e in events if e[0] == "token").strip()
    assert tokens == "The capital is Paris [1]."

    # done event carries the full answer and mapped citation
    done_evt = events[-1][1]
    assert done_evt["answer"] == "The capital is Paris [1]."
    assert [c["index"] for c in done_evt["citations"]] == [1]
    assert done_evt["citations"][0]["chunk_id"] == "chk_1"


def test_stream_no_hits_yields_insufficient_evidence() -> None:
    client = _client([], reply="unused")
    resp = client.post("/api/v1/query/stream", json={"question": "q"})
    events = _parse_sse(resp.text)

    assert events[0][0] == "sources"
    assert events[0][1]["sources"] == []
    tokens = "".join(e[1]["text"] for e in events if e[0] == "token")
    assert "don't have enough information" in tokens
    assert events[-1][1]["citations"] == []
