"""Unit tests for document domain models and DTO mapping."""

from __future__ import annotations

import hashlib

from app.models.document import Chunk, ChunkMetadata, Document, DocumentStatus, new_id
from app.schemas.documents import DocumentOut


def test_new_id_is_prefixed_and_unique() -> None:
    a = new_id("doc")
    b = new_id("doc")
    assert a.startswith("doc_")
    assert a != b


def test_from_upload_computes_hash_and_defaults() -> None:
    data = b"hello world"
    doc = Document.from_upload(filename="a.txt", content_type="text/plain", data=data)

    assert doc.size_bytes == len(data)
    assert doc.content_hash == hashlib.sha256(data).hexdigest()
    assert doc.status is DocumentStatus.PENDING
    assert doc.chunk_count == 0
    assert doc.id.startswith("doc_")


def test_identical_bytes_hash_identically() -> None:
    d1 = Document.from_upload(filename="a.txt", content_type="text/plain", data=b"same")
    d2 = Document.from_upload(filename="b.txt", content_type="text/plain", data=b"same")
    assert d1.content_hash == d2.content_hash
    assert d1.id != d2.id  # different documents, same content


def test_mark_updates_status_and_error() -> None:
    doc = Document.from_upload(filename="a.txt", content_type="text/plain", data=b"x")
    before = doc.updated_at
    doc.mark(DocumentStatus.FAILED, error="boom")
    assert doc.status is DocumentStatus.FAILED
    assert doc.error == "boom"
    assert doc.updated_at >= before


def test_chunk_carries_metadata() -> None:
    meta = ChunkMetadata(document_id="doc_1", filename="a.txt", page=2, start_char=0, end_char=10)
    chunk = Chunk(document_id="doc_1", text="hello", ordinal=0, token_count=1, metadata=meta)
    assert chunk.id.startswith("chk_")
    assert chunk.metadata.page == 2


def test_document_out_maps_from_model() -> None:
    doc = Document.from_upload(filename="a.txt", content_type="text/plain", data=b"x")
    out = DocumentOut.from_model(doc)
    assert out.id == doc.id
    assert out.filename == "a.txt"
    assert out.status is DocumentStatus.PENDING
