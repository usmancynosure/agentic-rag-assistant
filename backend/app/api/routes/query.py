"""Retrieval-augmented query endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_query_service
from app.schemas.query import CitationOut, QueryRequest, QueryResponse, SourceOut
from app.services.retrieval.query_service import QueryService

router = APIRouter(tags=["query"])


@router.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    service: QueryService = Depends(get_query_service),
) -> QueryResponse:
    answer, context = service.answer_query(
        question=request.question,
        document_id=request.document_id,
        top_k=request.top_k,
    )
    return QueryResponse(
        answer=answer.answer,
        citations=[CitationOut.from_citation(c) for c in answer.citations],
        sources=[SourceOut.from_passage(p) for p in context.passages],
    )
