from dataclasses import dataclass

import pymupdf


class InvalidPdfError(ValueError):
    """The upload is not a readable PDF."""


@dataclass(frozen=True)
class PageText:
    page_number: int  # 1-based, as shown to users in citations
    text: str


@dataclass(frozen=True)
class ExtractedPdf:
    page_count: int
    pages: list[PageText]  # only pages that have text
    skipped_pages: list[int]  # pages with no text (e.g. scanned images)


def open_pdf(data: bytes) -> pymupdf.Document:
    try:
        doc = pymupdf.open(stream=data, filetype="pdf")
    except Exception as exc:  # PyMuPDF raises several error types for bad files
        raise InvalidPdfError("The file is not a valid PDF.") from exc
    if doc.needs_pass:
        doc.close()
        raise InvalidPdfError("Password-protected PDFs are not supported.")
    return doc


def extract_pages(data: bytes) -> ExtractedPdf:
    """Extract text page by page, keeping page numbers (FR-02)."""
    with open_pdf(data) as doc:
        pages: list[PageText] = []
        skipped: list[int] = []
        for index, page in enumerate(doc):
            text = page.get_text("text")
            if text.strip():
                pages.append(PageText(page_number=index + 1, text=text))
            else:
                skipped.append(index + 1)
        return ExtractedPdf(page_count=len(doc), pages=pages, skipped_pages=skipped)
