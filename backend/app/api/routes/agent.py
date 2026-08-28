"""Agentic query endpoint (orchestrated multi-tool RAG)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.agent.orchestrator import AgentOrchestrator
from app.api.deps import get_orchestrator
from app.schemas.agent import AgentQueryRequest, AgentQueryResponse
from app.schemas.query import CitationOut, SourceOut

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/query", response_model=AgentQueryResponse)
async def agent_query(
    request: AgentQueryRequest,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
) -> AgentQueryResponse:
    result = orchestrator.run(
        question=request.question,
        document_id=request.document_id,
        max_iterations=request.max_iterations,
    )
    return AgentQueryResponse(
        answer=result.answer,
        citations=[CitationOut.from_citation(c) for c in result.citations],
        sources=[SourceOut.from_passage(p) for p in result.sources],
        tools_run=result.tools_run,
        iterations=result.iterations,
    )
