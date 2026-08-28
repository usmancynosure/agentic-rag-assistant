"""Unit tests for the Voyage embeddings client (with a fake provider)."""

from __future__ import annotations

from typing import Any

from app.services.ingestion.embeddings import Embedder, VoyageEmbeddings


class _Result:
    def __init__(self, embeddings: list[list[float]]) -> None:
        self.embeddings = embeddings


class FakeVoyageClient:
    """Records calls and returns deterministic vectors."""

    def __init__(self, *, fail_times: int = 0) -> None:
        self.calls: list[dict[str, Any]] = []
        self._fail_times = fail_times

    def embed(self, texts: list[str], *, model: str, input_type: str) -> _Result:
        self.calls.append({"n": len(texts), "model": model, "input_type": input_type})
        if self._fail_times > 0:
            self._fail_times -= 1
            raise RuntimeError("transient")
        # one 3-dim vector per text, encoding its length so order is checkable
        return _Result([[float(len(t)), 0.0, 0.0] for t in texts])


def _make(client: FakeVoyageClient, batch_size: int = 128) -> VoyageEmbeddings:
    return VoyageEmbeddings(api_key="x", model="voyage-3", batch_size=batch_size, client=client)


def test_satisfies_protocol() -> None:
    assert isinstance(_make(FakeVoyageClient()), Embedder)


def test_embed_documents_batches_and_preserves_order() -> None:
    client = FakeVoyageClient()
    emb = _make(client, batch_size=128)
    texts = [f"{'a' * i}" for i in range(200)]  # lengths 0..199

    vectors = emb.embed_documents(texts)

    assert len(vectors) == 200
    assert [v[0] for v in vectors] == [float(i) for i in range(200)]  # order preserved
    assert len(client.calls) == 2  # 200 / 128 -> 2 batches
    assert all(c["input_type"] == "document" for c in client.calls)


def test_embed_query_uses_query_input_type() -> None:
    client = FakeVoyageClient()
    emb = _make(client)
    vec = emb.embed_query("hello")
    assert vec == [5.0, 0.0, 0.0]
    assert client.calls[-1]["input_type"] == "query"


def test_empty_documents_short_circuits() -> None:
    client = FakeVoyageClient()
    emb = _make(client)
    assert emb.embed_documents([]) == []
    assert client.calls == []


def test_retry_recovers_from_transient_failure() -> None:
    client = FakeVoyageClient(fail_times=2)  # fail twice, succeed on 3rd
    emb = _make(client)
    vec = emb.embed_query("abc")
    assert vec == [3.0, 0.0, 0.0]
    assert len(client.calls) == 3
