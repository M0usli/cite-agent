from collections.abc import Sequence
from dataclasses import dataclass

from app.ingestion.extract import PageText


@dataclass(frozen=True)
class TextChunk:
    page_number: int
    chunk_index: int  # position within the whole document
    text: str


def split_text(text: str, size: int, overlap: int) -> list[str]:
    """Split text into pieces of at most `size` characters that share about `overlap` characters.

    Cuts happen at spaces where possible, so words are not broken in half.
    """
    if overlap * 2 >= size:
        raise ValueError("overlap must be less than half of size")

    text = " ".join(text.split())  # collapse whitespace and line breaks from the PDF
    if len(text) <= size:
        return [text] if text else []

    pieces: list[str] = []
    start = 0
    while True:
        end = min(start + size, len(text))
        if end < len(text):
            cut = text.rfind(" ", start + size // 2, end)
            if cut != -1:
                end = cut
        pieces.append(text[start:end].strip())
        if end >= len(text):
            return pieces
        # Step back by `overlap`, then forward to the next word start.
        next_start = end - overlap
        space = text.find(" ", next_start, end)
        start = space + 1 if space != -1 else next_start


def chunk_pages(pages: Sequence[PageText], size: int, overlap: int) -> list[TextChunk]:
    """Chunk each page separately so every chunk has one exact page number (FR-03)."""
    chunks: list[TextChunk] = []
    for page in pages:
        for piece in split_text(page.text, size, overlap):
            chunks.append(
                TextChunk(page_number=page.page_number, chunk_index=len(chunks), text=piece)
            )
    return chunks
