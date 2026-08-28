"""Unit tests for context assembly."""

from __future__ import annotations

from app.services.retrieval.context import assemble_context
from app.services.vector_store import SearchResult


def _r(chunk_id: str, text: str, score: float, *, page: int | None = None) -> SearchResult:
    return SearchResult(
        chunk_id=chunk_id,
        document_id="doc_1",
        filename="a.txt",
        page=page,
        ordinal=0,
        text=text,
        score=score,
    )


def test_ranks_by_score_and_assigns_indices() -> None:
    results = [_r("c1", "low", 0.2), _r("c2", "high", 0.9), _r("c3", "mid", 0.5)]
    ctx = assemble_context(results, token_budget=1000)
    assert [p.text for p in ctx.passages] == ["high", "mid", "low"]
    assert [p.index for p in ctx.passages] == [1, 2, 3]


def test_dedupes_by_chunk_id_keeping_higher_score() -> None:
    results = [_r("c1", "text", 0.4), _r("c1", "text", 0.8)]
    ctx = assemble_context(results, token_budget=1000)
    assert len(ctx.passages) == 1
    assert ctx.passages[0].score == 0.8


def test_dedupes_exact_duplicate_text() -> None:
    results = [_r("c1", "same body", 0.9), _r("c2", "same body", 0.8)]
    ctx = assemble_context(results, token_budget=1000)
    assert len(ctx.passages) == 1


def test_token_budget_limits_passages() -> None:
    # Each passage ~ many tokens; a tiny budget keeps only the first.
    big = "word " * 200
    results = [_r("c1", big, 0.9), _r("c2", big + " x", 0.8)]
    ctx = assemble_context(results, token_budget=210)
    assert len(ctx.passages) == 1  # second would exceed budget


def test_always_keeps_at_least_first_passage_over_budget() -> None:
    big = "word " * 500
    results = [_r("c1", big, 0.9)]
    ctx = assemble_context(results, token_budget=10)
    assert len(ctx.passages) == 1  # never drop the top hit to zero


def test_max_passages_caps_count() -> None:
    results = [_r(f"c{i}", f"text {i}", 1.0 - i * 0.1) for i in range(5)]
    ctx = assemble_context(results, token_budget=10_000, max_passages=2)
    assert len(ctx.passages) == 2


def test_empty_results_gives_empty_context() -> None:
    ctx = assemble_context([], token_budget=1000)
    assert ctx.is_empty
    assert ctx.to_prompt_block() == ""


def test_prompt_block_has_citation_markers_and_labels() -> None:
    results = [_r("c1", "body one", 0.9, page=3)]
    ctx = assemble_context(results, token_budget=1000)
    block = ctx.to_prompt_block()
    assert "[1]" in block
    assert "a.txt, p.3" in block
    assert "body one" in block
