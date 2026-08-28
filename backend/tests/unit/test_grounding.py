"""Unit tests for the grounding verifier."""

from __future__ import annotations

from app.services.retrieval.answerer import INSUFFICIENT_EVIDENCE
from app.services.retrieval.context import AssembledContext, ContextPassage
from app.services.verification.grounding import GroundingVerifier


class FakeLLM:
    def __init__(self, reply: str) -> None:
        self.reply = reply
        self.calls = 0

    def generate(self, *, system: str, prompt: str, max_tokens: int) -> str:
        self.calls += 1
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
                score=0.9,
            )
            for i, t in enumerate(texts)
        ]
    )


def test_supported_answer_is_grounded() -> None:
    llm = FakeLLM('{"grounded": true, "score": 1.0, "unsupported_claims": [], "reasoning": "ok"}')
    v = GroundingVerifier(llm=llm)
    report = v.verify(question="q", answer="Paris is the capital [1].", context=_ctx("Paris..."))
    assert report.grounded is True
    assert report.score == 1.0
    assert report.unsupported_claims == []


def test_unsupported_claim_detected() -> None:
    llm = FakeLLM(
        '{"grounded": false, "score": 0.5, '
        '"unsupported_claims": ["population is 10M"], "reasoning": "not in sources"}'
    )
    v = GroundingVerifier(llm=llm)
    report = v.verify(question="q", answer="Paris has 10M people [1].", context=_ctx("Paris..."))
    assert report.grounded is False
    assert report.unsupported_claims == ["population is 10M"]


def test_malformed_json_returns_neutral() -> None:
    llm = FakeLLM("I think it's mostly fine honestly")
    v = GroundingVerifier(llm=llm)
    report = v.verify(question="q", answer="Some answer [1].", context=_ctx("src"))
    assert report.score == 0.5
    assert "could not be parsed" in report.reasoning


def test_score_is_clamped() -> None:
    llm = FakeLLM('{"grounded": true, "score": 5, "unsupported_claims": []}')
    v = GroundingVerifier(llm=llm)
    report = v.verify(question="q", answer="a [1]", context=_ctx("src"))
    assert report.score == 1.0


def test_insufficient_evidence_short_circuits() -> None:
    llm = FakeLLM("should not be called")
    v = GroundingVerifier(llm=llm)
    report = v.verify(question="q", answer=INSUFFICIENT_EVIDENCE, context=_ctx("src"))
    assert report.grounded is True
    assert report.score == 1.0
    assert llm.calls == 0


def test_empty_context_short_circuits() -> None:
    llm = FakeLLM("should not be called")
    v = GroundingVerifier(llm=llm)
    report = v.verify(question="q", answer="anything", context=AssembledContext(passages=[]))
    assert report.score == 1.0
    assert llm.calls == 0
