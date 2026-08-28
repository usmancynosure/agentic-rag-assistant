"""Unit tests for the vector_search agent tool."""

from __future__ import annotations

from typing import Any

from app.agent.tools.base import Tool
from app.agent.tools.vector_search import VectorSearchTool
from app.services.vector_store import SearchResult


class FakeEmbedder:
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.0, 0.0, 0.0] for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]


class FakeVectorStore:
    def __init__(self, results: list[SearchResult]) -> None:
        self._results = results
        self.last: dict[str, Any] = {}

    def upsert(self, chunks: list[Any], vectors: list[list[float]]) -> None: ...

    def query(
        self, vector: list[float], *, top_k: int, filter: dict[str, Any] | None = None
    ) -> list[SearchResult]:
        self.last = {"top_k": top_k, "filter": filter}
        return self._results

    def delete(self, ids: list[str]) -> None: ...


def _result(cid: str, score: float) -> SearchResult:
    return SearchResult(
        chunk_id=cid,
        document_id="doc_1",
        filename="a.txt",
        page=2,
        ordinal=0,
        text=f"body {cid}",
        score=score,
    )


def _tool(results: list[SearchResult], top_k: int = 5) -> tuple[VectorSearchTool, FakeVectorStore]:
    store = FakeVectorStore(results)
    return VectorSearchTool(embedder=FakeEmbedder(), vector_store=store, top_k=top_k), store


def test_satisfies_tool_protocol() -> None:
    tool, _ = _tool([])
    assert isinstance(tool, Tool)
    assert tool.name == "vector_search"
    assert tool.description


def test_run_maps_results_to_vector_evidence() -> None:
    tool, _ = _tool([_result("chk_1", 0.9), _result("chk_2", 0.7)])
    evidence = tool.run("what is x?")
    assert [e.origin for e in evidence] == ["vector", "vector"]
    assert evidence[0].source_id == "chk_1"
    assert evidence[0].title == "a.txt"
    assert evidence[0].page == 2
    assert evidence[0].document_id == "doc_1"


def test_run_forwards_top_k_and_document_filter() -> None:
    tool, store = _tool([_result("chk_1", 0.9)], top_k=3)
    tool.run("q", document_id="doc_42")
    assert store.last["top_k"] == 3
    assert store.last["filter"] == {"document_id": "doc_42"}


def test_run_no_filter_when_document_id_absent() -> None:
    tool, store = _tool([])
    tool.run("q")
    assert store.last["filter"] is None
