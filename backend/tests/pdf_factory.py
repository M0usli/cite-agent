import pymupdf


def make_pdf(pages: list[str]) -> bytes:
    """Build a PDF in memory. An empty string makes a page with no text (like a scan)."""
    doc = pymupdf.open()
    for text in pages:
        page = doc.new_page()
        if text:
            overflow = page.insert_textbox(page.rect + (40, 40, -40, -40), text, fontsize=9)
            assert overflow >= 0, "test text does not fit on one page"
    data = doc.tobytes()
    doc.close()
    return data
