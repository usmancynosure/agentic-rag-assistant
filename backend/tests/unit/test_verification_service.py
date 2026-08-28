"""Unit tests for the verification service (confidence + verdict)."""

from __future__ import annotations

from app.services.retrieval.context import AssembledContext, ContextPassage
from app.services.verification.grounding import GroundingVerifier
from app.services.verification.service import VerificationService


class FakeLLM:
    def __init__(self, reply: str) -> None:
        self.reply = reply

    def generate(self, *, system: str, prompt: str, max_tokens: int) -> str:
        return self.reply


def _ctx() -> AssembledContext:
    return AssembledContext(
        passages=[
            ContextPassage(
                index=1,
                chunk_id="chk_1",
                document_id="doc_1",
                filename="a.txt",
                page=None,
                text="Paris is the capital of France.",
                score=0.9,
            )
        ]
    )


def _service(grounding_reply: str) -> VerificationService:
    return VerificationService(grounding_verifier=GroundingVerifier(llm=FakeLLM(grounding_reply)))


def test_perfect_answer_is_high_and_trustworthy() -> None:
    svc = _service('{"grounded": true, "score": 1.0, "unsupported_claims": []}')
    result = svc.verify(
        question="capital?", answer="The capital of France is Paris [1].", context=_ctx()
    )
    assert result.confidence == 1.0
    assert result.verdict == "high"
    assert result.trustworthy is True


def test_uncited_claim_lowers_confidence() -> None:
    svc = _service('{"grounded": true, "score": 1.0, "unsupported_claims": []}')
    # second sentence is factual but uncited -> coverage 0.5
    answer = "The capital is Paris [1]. The population is exactly ten million people."
    result = svc.verify(question="q", answer=answer, context=_ctx())
    # 0.7*1.0 + 0.3*0.5 = 0.85
    assert result.confidence == 0.85
    assert result.verdict == "high"


def test_invalid_citation_penalizes_and_untrusts() -> None:
    svc = _service('{"grounded": true, "score": 1.0, "unsupported_claims": []}')
    result = svc.verify(question="q", answer="A bad reference here [9].", context=_ctx())
    # citations invalid -> penalty 0.5 ; coverage 1.0 -> (0.7+0.3)*0.5 = 0.5
    assert result.confidence == 0.5
    assert result.trustworthy is False  # invalid citations block trust


def test_ungrounded_answer_not_trustworthy() -> None:
    svc = _service('{"grounded": false, "score": 0.3, "unsupported_claims": ["made up"]}')
    result = svc.verify(question="q", answer="Fabricated fact [1].", context=_ctx())
    assert result.grounding.grounded is False
    assert result.trustworthy is False
    assert result.verdict == "low"
