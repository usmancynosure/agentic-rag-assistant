"""Unit tests for deterministic citation validation."""

from __future__ import annotations

from app.services.retrieval.answerer import INSUFFICIENT_EVIDENCE
from app.services.retrieval.context import AssembledContext, ContextPassage
from app.services.verification.citations import validate_citations


def _ctx(n: int) -> AssembledContext:
    return AssembledContext(
        passages=[
            ContextPassage(
                index=i + 1,
                chunk_id=f"chk_{i+1}",
                document_id="doc_1",
                filename="a.txt",
                page=None,
                text=f"source {i+1}",
                score=0.9,
            )
            for i in range(n)
        ]
    )


def test_fully_cited_answer_is_valid_full_coverage() -> None:
    answer = "The capital of France is Paris [1]. It sits on the Seine river [2]."
    report = validate_citations(answer, _ctx(2))
    assert report.valid is True
    assert report.invalid_indices == []
    assert report.uncited_sentences == []
    assert report.coverage == 1.0


def test_out_of_range_citation_is_invalid() -> None:
    answer = "Paris has ten million people [9]."
    report = validate_citations(answer, _ctx(2))
    assert report.valid is False
    assert report.invalid_indices == [9]


def test_uncited_factual_sentence_lowers_coverage() -> None:
    answer = "The capital of France is Paris [1]. The population is exactly ten million."
    report = validate_citations(answer, _ctx(1))
    assert report.valid is True  # no invalid indices
    assert len(report.uncited_sentences) == 1
    assert report.coverage == 0.5


def test_short_fragments_ignored_for_coverage() -> None:
    answer = "Yes. The capital of France is Paris [1]."
    report = validate_citations(answer, _ctx(1))
    # "Yes." is below the factual threshold and doesn't count against coverage
    assert report.coverage == 1.0


def test_insufficient_evidence_is_valid() -> None:
    report = validate_citations(INSUFFICIENT_EVIDENCE, _ctx(0))
    assert report.valid is True
    assert report.coverage == 1.0


def test_citation_with_no_sources_is_invalid() -> None:
    report = validate_citations("Some factual claim here [1].", _ctx(0))
    assert report.valid is False
    assert report.invalid_indices == [1]
