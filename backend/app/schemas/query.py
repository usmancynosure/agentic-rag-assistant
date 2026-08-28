"""API DTOs for the query endpoint."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.services.retrieval.answerer import Citation
from app.services.retrieval.context import ContextPassage

_SNIPPET_CHARS = 500


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
    document_id: str | None = None  # optional scope to a single document
    top_k: int | None = None


class CitationOut(BaseModel):
    index: int
    chunk_id: str
    document_id: str
    filename: str
    page: int | None

    @classmethod
    def from_citation(cls, c: Citation) -> "CitationOut":
        return cls(
            index=c.index,
            chunk_id=c.chunk_id,
            document_id=c.document_id,
            filename=c.filename,
            page=c.page,
        )


class SourceOut(BaseModel):
    index: int
    chunk_id: str
    document_id: str
    filename: str
    page: int | None
    score: float
    snippet: str

    @classmethod
    def from_passage(cls, p: ContextPassage) -> "SourceOut":
        snippet = p.text if len(p.text) <= _SNIPPET_CHARS else p.text[:_SNIPPET_CHARS] + "…"
        return cls(
            index=p.index,
            chunk_id=p.chunk_id,
            document_id=p.document_id,
            filename=p.filename,
            page=p.page,
            score=p.score,
            snippet=snippet,
        )


class QueryResponse(BaseModel):
    answer: str
    citations: list[CitationOut]
    sources: list[SourceOut]
