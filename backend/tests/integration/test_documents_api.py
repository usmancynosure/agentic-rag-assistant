"""Integration tests for the /documents API with fake embedder + vector store."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_document_store, get_ingestion_service
from app.core.config import get_settings
from app.main import create_app
from app.models.document import Chunk
from app.services.document_store import DocumentStore
from app.services.ingestion.service import IngestionService
from app.services.vector_store import SearchResult


class FakeEmbedder:
    def __init__(self) -> None:
        self.calls = 0

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.calls += 1
        return [[0.1, 0.2, 0.3] for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]


class FakeVectorStore:
    def __init__(self) -> None:
        self.upserted: list[Chunk] = []
        self.deleted: list[str] = []

    def upsert(self, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        self.upserted.extend(chunks)

    def query(
        self, vector: list[float], *, top_k: int, filter: dict[str, Any] | None = None
    ) -> list[SearchResult]:
        return []

    def delete(self, ids: list[str]) -> None:
        self.deleted.extend(ids)


@pytest.fixture
def client() -> Any:
    store = DocumentStore()
    embedder = FakeEmbedder()
    vectors = FakeVectorStore()
    service = IngestionService(
        embedder=embedder,
        vector_store=vectors,
        document_store=store,
        settings=get_settings(),
    )

    app = create_app()
    app.dependency_overrides[get_document_store] = lambda: store
    app.dependency_overrides[get_ingestion_service] = lambda: service

    test_client = TestClient(app)
    test_client.embedder = embedder  # type: ignore[attr-defined]
    test_client.vectors = vectors  # type: ignore[attr-defined]
    return test_client


def _upload(client: Any, name: str, content: bytes, ctype: str = "text/plain") -> Any:
    return client.post("/api/v1/documents", files={"file": (name, content, ctype)})


def test_upload_then_list_and_get(client: Any) -> None:
    resp = _upload(client, "notes.txt", b"Alpha paragraph.\n\nBeta paragraph.")
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "ready"
    doc_id = body["document_id"]

    listing = client.get("/api/v1/documents").json()
    assert listing["total"] == 1
    assert listing["items"][0]["id"] == doc_id
    assert listing["items"][0]["chunk_count"] >= 1

    one = client.get(f"/api/v1/documents/{doc_id}").json()
    assert one["filename"] == "notes.txt"
    assert one["status"] == "ready"


def test_delete_removes_document_and_vectors(client: Any) -> None:
    doc_id = _upload(client, "a.txt", b"content here").json()["document_id"]

    resp = client.delete(f"/api/v1/documents/{doc_id}")
    assert resp.status_code == 204
    assert client.vectors.deleted  # vector store delete was called
    assert client.get(f"/api/v1/documents/{doc_id}").status_code == 404


def test_unsupported_type_returns_422(client: Any) -> None:
    resp = _upload(client, "image.png", b"\x89PNG", ctype="image/png")
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "unsupported_file_type"


def test_empty_file_returns_422(client: Any) -> None:
    resp = _upload(client, "empty.txt", b"")
    assert resp.status_code == 422


def test_duplicate_upload_is_idempotent(client: Any) -> None:
    data = b"identical content for hashing"
    first = _upload(client, "one.txt", data).json()["document_id"]
    assert client.embedder.calls == 1

    second = _upload(client, "two.txt", data).json()["document_id"]
    assert second == first  # same document returned
    assert client.embedder.calls == 1  # not re-embedded
    assert client.get("/api/v1/documents").json()["total"] == 1


def test_get_missing_document_returns_404(client: Any) -> None:
    assert client.get("/api/v1/documents/doc_missing").status_code == 404
