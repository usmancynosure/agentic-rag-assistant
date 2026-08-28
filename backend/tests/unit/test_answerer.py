"""Unit tests for grounded answer generation."""

from __future__ import annotations

from app.services.llm import LLMClient
from app.services.retrieval.answerer import INSUFFICIENT_EVIDENCE, Answerer
from app.services.retrieval.context import AssembledContext, ContextPassage


class FakeLLM:
    def __init__(self, reply: str) -> None:
        self.reply = reply
        self.last_system: str | None = None
        self.last_prompt: str | None = None
        self.calls = 0

    def generate(self, *, system: str, prompt: str, max_tokens: int) -> str:
        self.calls += 1
        self.last_system = system
        self.last_prompt = prompt
        return self.reply


def _ctx(*texts: str) -> AssembledContext:
    return AssembledContext(
        passages=[
            ContextPassage(
                index=i + 1,
                chunk_id=f"chk_{i+1}",
                document_id="doc_1",
                filename="a.txt",
                page=None,
                text=t,
                score=1.0 - i * 0.1,
            )
            for i, t in enumerate(texts)
        ]
    )


def test_satisfies_llm_protocol() -> None:
    assert isinstance(FakeLLM("x"), LLMClient)


def test_extracts_and_maps_citations() -> None:
    llm = FakeLLM("The sky is blue [1] and grass is green [2].")
    answerer = Answerer(llm=llm, max_tokens=1024)
    result = answerer.answer(question="colors?", context=_ctx("sky", "grass"))

    assert result.answer.startswith("The sky is blue")
    assert [c.index for c in result.citations] == [1, 2]
    assert result.citations[0].chunk_id == "chk_1"


def test_empty_context_short_circuits_without_calling_llm() -> None:
    llm = FakeLLM("should not be used")
    answerer = Answerer(llm=llm, max_tokens=1024)
    result = answerer.answer(question="q", context=AssembledContext(passages=[]))

    assert result.answer == INSUFFICIENT_EVIDENCE
    assert result.citations == []
    assert llm.calls == 0


def test_out_of_range_citation_is_dropped() -> None:
    llm = FakeLLM("Fact [1] and a bogus one [9].")
    answerer = Answerer(llm=llm, max_tokens=1024)
    result = answerer.answer(question="q", context=_ctx("only one source"))
    assert [c.index for c in result.citations] == [1]


def test_prompt_contains_question_and_context() -> None:
    llm = FakeLLM("answer [1]")
    answerer = Answerer(llm=llm, max_tokens=1024)
    answerer.answer(question="what color?", context=_ctx("blue fact"))
    assert "what color?" in (llm.last_prompt or "")
    assert "blue fact" in (llm.last_prompt or "")
    assert "ONLY" in (llm.last_system or "")


def test_duplicate_citations_deduped_in_order() -> None:
    llm = FakeLLM("A [2] B [1] C [2] again.")
    answerer = Answerer(llm=llm, max_tokens=1024)
    result = answerer.answer(question="q", context=_ctx("s1", "s2"))
    assert [c.index for c in result.citations] == [2, 1]
