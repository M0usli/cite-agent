import pytest

from app.ingestion.extract import InvalidPdfError, extract_pages
from tests.pdf_factory import make_pdf


def test_text_is_kept_with_its_page_number() -> None:
    """AC-03"""
    pdf = make_pdf(["Intro page.", "Methods page.", "Plants use photosynthesis."])

    result = extract_pages(pdf)

    assert result.page_count == 3
    page3 = next(p for p in result.pages if p.page_number == 3)
    assert "photosynthesis" in page3.text


def test_pages_without_text_are_skipped_and_reported() -> None:
    """AC-04"""
    pdf = make_pdf(["One", "", "Three", "Four", ""])

    result = extract_pages(pdf)

    assert result.skipped_pages == [2, 5]
    assert [p.page_number for p in result.pages] == [1, 3, 4]


def test_not_a_pdf_raises() -> None:
    with pytest.raises(InvalidPdfError):
        extract_pages(b"%PDF-1.7 this is not really a pdf")
