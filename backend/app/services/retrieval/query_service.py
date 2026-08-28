"""Baseline (non-agentic) retrieval-augmented query service."""

from __future__ import annotations

from app.core.config import Settings
from app.core.logging import get_logger
from app.services.ingestion.embeddings import Embedder
from app.services.retrieval.answerer import Answerer, GeneratedAnswer
from app.services.retrieval.context import AssembledContext, assemble_context
from app.services.vector_store import VectorStore

logger = get_logger(__name__)


class QueryService:
    def __init__(
        self,
        *,
        embedder: Embedder,
        vector_store: VectorStore,
        answerer: Answerer,
        settings: Settings,
    ) -> None:
        self._embedder = embedder
        self._vectors = vector_store
        self._answerer = answerer
        self._settings = settings

    def answer_query(
        self,
        *,
        question: str,
        document_id: str | None = None,
        top_k: int | None = None,
    ) -> tuple[GeneratedAnswer, AssembledContext]:
        vector = self._embedder.embed_query(question)
        filter_ = {"document_id": document_id} if document_id else None
        results = self._vectors.query(
            vector,
            top_k=top_k or self._settings.retrieval_top_k,
            filter=filter_,
        )
        context = assemble_context(
            results, token_budget=self._settings.context_token_budget
        )
        answer = self._answerer.answer(question=question, context=context)
        logger.info(
            "query_answered",
            retrieved=len(results),
            used=len(context.passages),
            citations=len(answer.citations),
        )
        return answer, context
