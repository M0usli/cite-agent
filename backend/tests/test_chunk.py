import pytest

from app.ingestion.chunk import chunk_pages, split_text
from app.ingestion.extract import PageText

WORDS = " ".join(f"word{i}" for i in range(600))  # about 4,500 characters


def test_short_text_is_one_chunk() -> None:
    assert split_text("Hello   world.\nNew line.", size=1000, overlap=200) == [
        "Hello world. New line."
    ]


def test_empty_text_gives_no_chunks() -> None:
    assert split_text("   \n  ", size=1000, overlap=200) == []


def test_long_text_chunks_respect_size_and_overlap() -> None:
    pieces = split_text(WORDS, size=1000, overlap=200)

    assert len(pieces) > 1
    assert all(len(p) <= 1000 for p in pieces)
    for prev, nxt in zip(pieces, pieces[1:], strict=False):
        # The next chunk starts with words that ended the previous chunk (AC-06).
        first_word = nxt.split()[0]
        assert first_word in prev.split()


def test_chunks_do_not_split_words() -> None:
    pieces = split_text(WORDS, size=1000, overlap=200)
    all_words = set(WORDS.split())
    for piece in pieces:
        assert set(piece.split()) <= all_words


def test_every_word_is_covered() -> None:
    pieces = split_text(WORDS, size=1000, overlap=200)
    covered = {w for p in pieces for w in p.split()}
    assert covered == set(WORDS.split())


def test_overlap_too_large_is_rejected() -> None:
    with pytest.raises(ValueError):
        split_text(WORDS, size=100, overlap=50)


def test_chunk_pages_keeps_page_numbers_and_global_index() -> None:
    pages = [PageText(1, "Short first page."), PageText(3, WORDS)]

    chunks = chunk_pages(pages, size=1000, overlap=200)

    assert chunks[0].page_number == 1
    assert {c.page_number for c in chunks[1:]} == {3}
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))
