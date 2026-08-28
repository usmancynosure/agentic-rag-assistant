"""Grounded answer generation with enforced citations."""

from __future__ import annotations

import re

from pydantic import BaseModel

from app.services.llm import LLMClient
from app.services.retrieval.context import AssembledContext, ContextPassage

INSUFFICIENT_EVIDENCE = (
    "I don't have enough information in the provided sources to answer that."
)

SYSTEM_PROMPT = (
    "You are a precise research assistant. Answer the user's question using ONLY "
    "the numbered sources provided.\n"
    "Rules:\n"
    "- Cite every factual claim with its source number(s) in square brackets, "
    "e.g. [1] or [2][3].\n"
    "- Use only information present in the sources. Do not use outside knowledge.\n"
    "- If the sources do not contain enough information to answer, reply exactly: "
    f'"{INSUFFICIENT_EVIDENCE}" and cite nothing.\n'
    "- Be concise and answer the question directly."
)

_CITATION_RE = re.compile(r"\[(\d+)\]")


class Citation(BaseModel):
    index: int
    chunk_id: str
    document_id: str
    filename: str
    page: int | None

    @classmethod
    def from_passage(cls, p: ContextPassage) -> "Citation":
        return cls(
            index=p.index,
            chunk_id=p.chunk_id,
            document_id=p.document_id,
            filename=p.filename,
            page=p.page,
        )


class GeneratedAnswer(BaseModel):
    answer: str
    citations: list[Citation]


def build_user_prompt(question: str, context_block: str) -> str:
    return f"Question: {question}\n\nSources:\n{context_block}\n\nAnswer:"


def _extract_cited_indices(text: str) -> list[int]:
    """Unique cited indices, in first-appearance order."""
    seen: dict[int, None] = {}
    for match in _CITATION_RE.finditer(text):
        seen.setdefault(int(match.group(1)), None)
    return list(seen)


class Answerer:
    def __init__(self, *, llm: LLMClient, max_tokens: int) -> None:
        self._llm = llm
        self._max_tokens = max_tokens

    def answer(self, *, question: str, context: AssembledContext) -> GeneratedAnswer:
        if context.is_empty:
            return GeneratedAnswer(answer=INSUFFICIENT_EVIDENCE, citations=[])

        prompt = build_user_prompt(question, context.to_prompt_block())
        text = self._llm.generate(
            system=SYSTEM_PROMPT, prompt=prompt, max_tokens=self._max_tokens
        ).strip()

        by_index = {p.index: p for p in context.passages}
        citations = [
            Citation.from_passage(by_index[i])
            for i in _extract_cited_indices(text)
            if i in by_index  # drop hallucinated / out-of-range markers
        ]
        return GeneratedAnswer(answer=text, citations=citations)
