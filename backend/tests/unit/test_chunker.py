"""Unit tests for the token-aware chunker."""

from __future__ import annotations

from app.services.ingestion import tokenizer
from app.services.ingestion.chunker import chunk_document
from app.services.ingestion.parsers import ParsedDocument, ParsedPage


def _doc(*texts_with_pages: tuple[str, int | None]) -> ParsedDocument:
    return ParsedDocument(pages=[ParsedPage(page=p, text=t) for t, p in texts_with_pages])


def test_short_text_single_chunk() -> None:
    parsed = _doc(("Just a short paragraph.", None))
    chunks = chunk_document(
        parsed, document_id="doc_1", filename="a.txt", max_tokens=512, overlap_tokens=64
    )
    assert len(chunks) == 1
    assert chunks[0].ordinal == 0
    assert chunks[0].text == "Just a short paragraph."
    assert chunks[0].token_count > 0


def test_multiple_paragraphs_split_within_budget() -> None:
    paragraphs = [f"Paragraph number {i} " + "word " * 40 for i in range(20)]
    parsed = _doc(("\n\n".join(paragraphs), None))
    chunks = chunk_document(
        parsed, document_id="doc_1", filename="a.txt", max_tokens=200, overlap_tokens=30
    )
    assert len(chunks) > 1
    # Body stays within budget + overlap allowance.
    for c in chunks:
        assert c.token_count <= 200 + 30 + 5


def test_overlap_present_between_consecutive_chunks() -> None:
    paragraphs = [f"Sentence {i} alpha beta gamma delta epsilon zeta." for i in range(30)]
    parsed = _doc(("\n\n".join(paragraphs), None))
    chunks = chunk_document(
        parsed, document_id="doc_1", filename="a.txt", max_tokens=60, overlap_tokens=20
    )
    assert len(chunks) >= 2
    # The start of chunk N+1 should share some tokens with the end of chunk N.
    first_tail = set(tokenizer.encode(chunks[0].text)[-20:])
    second_head = set(tokenizer.encode(chunks[1].text)[:20])
    assert first_tail & second_head


def test_oversized_paragraph_is_hard_split() -> None:
    big = "token " * 1000  # one giant paragraph
    parsed = _doc((big, None))
    chunks = chunk_document(
        parsed, document_id="doc_1", filename="a.txt", max_tokens=100, overlap_tokens=0
    )
    assert len(chunks) > 1
    for c in chunks:
        assert c.token_count <= 100 + 5


def test_page_numbers_and_ordinals_preserved() -> None:
    parsed = _doc(("Page one content.", 1), ("Page two content.", 2))
    chunks = chunk_document(
        parsed, document_id="doc_1", filename="r.pdf", max_tokens=512, overlap_tokens=64
    )
    assert [c.metadata.page for c in chunks] == [1, 2]
    assert [c.ordinal for c in chunks] == [0, 1]
    assert all(c.document_id == "doc_1" for c in chunks)


def test_char_offsets_are_set() -> None:
    parsed = _doc(("First para.\n\nSecond para.", None))
    chunks = chunk_document(
        parsed, document_id="doc_1", filename="a.txt", max_tokens=512, overlap_tokens=0
    )
    assert chunks[0].metadata.start_char == 0
    assert chunks[0].metadata.end_char is not None
    assert chunks[0].metadata.end_char > chunks[0].metadata.start_char
