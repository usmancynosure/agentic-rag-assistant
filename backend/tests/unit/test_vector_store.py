"""Unit tests for the Pinecone vector store (with a fake index)."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from app.models.document import Chunk, ChunkMetadata
from app.services.vector_store import PineconeVectorStore, SearchResult, VectorStore


class FakeIndex:
    def __init__(self) -> None:
        self.upserts: list[list[dict[str, Any]]] = []
        self.deleted: list[list[str]] = []
        self._query_response: Any = SimpleNamespace(matches=[])

    def upsert(self, *, vectors: list[dict[str, Any]]) -> None:
        self.upserts.append(vectors)

    def delete(self, *, ids: list[str]) -> None:
        self.deleted.append(ids)

    def set_matches(self, matches: list[Any]) -> None:
        self._query_response = SimpleNamespace(matches=matches)

    def query(self, *, vector: list[float], top_k: int, include_metadata: bool, filter: Any) -> Any:
        self.last_query = {"vector": vector, "top_k": top_k, "filter": filter}
        return self._query_response


def _chunk(cid: str, *, page: int | None = 1, ordinal: int = 0) -> Chunk:
    return Chunk(
        id=cid,
        document_id="doc_1",
        text=f"text of {cid}",
        ordinal=ordinal,
        token_count=3,
        metadata=ChunkMetadata(document_id="doc_1", filename="a.txt", page=page),
    )


def _store(index: FakeIndex) -> PineconeVectorStore:
    return PineconeVectorStore(
        api_key="x", index_name="test", dimension=3, index=index
    )


def test_satisfies_protocol() -> None:
    assert isinstance(_store(FakeIndex()), VectorStore)


def test_upsert_builds_payload_with_text_metadata() -> None:
    index = FakeIndex()
    store = _store(index)
    chunks = [_chunk("chk_1", ordinal=0), _chunk("chk_2", ordinal=1)]
    vectors = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]

    store.upsert(chunks, vectors)

    payload = index.upserts[0]
    assert payload[0]["id"] == "chk_1"
    assert payload[0]["values"] == [0.1, 0.2, 0.3]
    assert payload[0]["metadata"]["text"] == "text of chk_1"
    assert payload[0]["metadata"]["document_id"] == "doc_1"
    assert payload[0]["metadata"]["page"] == 1


def test_upsert_omits_null_page() -> None:
    index = FakeIndex()
    store = _store(index)
    store.upsert([_chunk("chk_1", page=None)], [[0.1, 0.2, 0.3]])
    assert "page" not in index.upserts[0][0]["metadata"]


def test_upsert_batches_at_100() -> None:
    index = FakeIndex()
    store = _store(index)
    chunks = [_chunk(f"chk_{i}", ordinal=i) for i in range(250)]
    vectors = [[0.0, 0.0, 0.0] for _ in range(250)]

    store.upsert(chunks, vectors)

    assert [len(b) for b in index.upserts] == [100, 100, 50]


def test_query_maps_matches_to_results() -> None:
    index = FakeIndex()
    index.set_matches(
        [
            SimpleNamespace(
                id="chk_1",
                score=0.92,
                metadata={
                    "document_id": "doc_1",
                    "filename": "a.txt",
                    "ordinal": 0,
                    "text": "hello",
                    "page": 2,
                },
            )
        ]
    )
    store = _store(index)

    results = store.query([0.1, 0.2, 0.3], top_k=5, filter={"document_id": "doc_1"})

    assert len(results) == 1
    r = results[0]
    assert isinstance(r, SearchResult)
    assert r.chunk_id == "chk_1"
    assert r.score == 0.92
    assert r.page == 2
    assert index.last_query["top_k"] == 5
    assert index.last_query["filter"] == {"document_id": "doc_1"}


def test_delete_forwards_ids() -> None:
    index = FakeIndex()
    store = _store(index)
    store.delete(["chk_1", "chk_2"])
    assert index.deleted == [["chk_1", "chk_2"]]


def test_delete_empty_is_noop() -> None:
    index = FakeIndex()
    store = _store(index)
    store.delete([])
    assert index.deleted == []
