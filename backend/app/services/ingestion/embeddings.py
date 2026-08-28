"""Embedding generation via Voyage AI.

An ``Embedder`` protocol decouples callers from the concrete provider. The
Voyage implementation batches requests and retries transient failures. The
underlying client is injectable so tests need neither an API key nor the SDK.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.logging import get_logger

logger = get_logger(__name__)

# Voyage accepts up to 128 inputs per request.
_MAX_BATCH = 128


@runtime_checkable
class Embedder(Protocol):
    """Provider-agnostic embedding interface."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class VoyageEmbeddings:
    """Voyage-backed embedder with batching and retry."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        batch_size: int = _MAX_BATCH,
        client: Any | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._batch_size = min(batch_size, _MAX_BATCH)
        self._client = client  # injected in tests; lazily created otherwise

    def _get_client(self) -> Any:
        if self._client is None:
            import voyageai  # lazy: only needed for real calls

            self._client = voyageai.Client(api_key=self._api_key)
        return self._client

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
        reraise=True,
    )
    def _raw_embed(self, texts: list[str], *, input_type: str) -> list[list[float]]:
        result = self._get_client().embed(texts, model=self._model, input_type=input_type)
        return list(result.embeddings)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors: list[list[float]] = []
        for start in range(0, len(texts), self._batch_size):
            batch = texts[start : start + self._batch_size]
            vectors.extend(self._raw_embed(batch, input_type="document"))
        logger.info("embedded_documents", count=len(texts), model=self._model)
        return vectors

    def embed_query(self, text: str) -> list[float]:
        return self._raw_embed([text], input_type="query")[0]
