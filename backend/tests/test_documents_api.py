"""Upload → background processing → status, against a real Postgres + pgvector."""

import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import Chunk
from tests.pdf_factory import make_pdf

LONG_PAGE = " ".join(f"Sentence {i} about plant biology and light." for i in range(80))


def _upload(api: TestClient, data: bytes, name: str = "paper.pdf", mime: str = "application/pdf"):
    return api.post("/documents", files={"file": (name, data, mime)})


def test_valid_pdf_is_accepted_and_becomes_ready(api: TestClient) -> None:
    """AC-01, AC-07"""
    res = _upload(api, make_pdf([f"Page {i} text." for i in range(1, 11)]))

    assert res.status_code == 202
    body = res.json()
    assert body["status"] == "processing"
    assert body["page_count"] == 10

    doc = api.get(f"/documents/{body['id']}").json()
    assert doc["status"] == "ready"
    assert doc["chunk_count"] > 0


def test_non_pdf_is_rejected_and_nothing_stored(api: TestClient) -> None:
    """AC-02"""
    docx_bytes = b"PK\x03\x04 fake word document"

    res = _upload(api, docx_bytes, name="notes.docx", mime="application/octet-stream")

    assert res.status_code == 400
    assert "PDF" in res.json()["detail"]
    assert api.get("/documents").json() == []


def test_pdf_over_page_limit_is_rejected(api: TestClient) -> None:
    """AC-02"""
    res = _upload(api, make_pdf(["x"] * 51))

    assert res.status_code == 413
    assert "51 pages" in res.json()["detail"]
    assert api.get("/documents").json() == []


def test_pdf_over_size_limit_is_rejected(api: TestClient) -> None:
    """AC-02"""
    res = _upload(api, b"%PDF-" + b"0" * (20 * 1024 * 1024))

    assert res.status_code == 413
    assert api.get("/documents").json() == []


def test_corrupt_pdf_is_rejected(api: TestClient) -> None:
    res = _upload(api, b"%PDF-1.7 truncated garbage")

    assert res.status_code == 400


def test_blank_pages_are_reported(api: TestClient) -> None:
    """AC-04"""
    doc_id = _upload(api, make_pdf(["One", "", "Three", "Four", ""])).json()["id"]

    doc = api.get(f"/documents/{doc_id}").json()

    assert doc["status"] == "ready"
    assert doc["skipped_pages"] == [2, 5]


def test_pdf_with_no_text_fails(api: TestClient) -> None:
    """AC-05"""
    doc_id = _upload(api, make_pdf(["", ""])).json()["id"]

    doc = api.get(f"/documents/{doc_id}").json()

    assert doc["status"] == "failed"
    assert "No text found" in doc["error"]
    assert doc["chunk_count"] == 0


def test_chunks_store_document_and_page_with_overlap(
    api: TestClient, db_session_factory: sessionmaker[Session]
) -> None:
    """AC-03, AC-06"""
    doc_id = _upload(api, make_pdf(["Intro.", "Methods.", LONG_PAGE])).json()["id"]

    with db_session_factory() as session:
        chunks = session.scalars(
            select(Chunk).where(Chunk.document_id == uuid.UUID(doc_id)).order_by(Chunk.chunk_index)
        ).all()
        filenames = {c.document.filename for c in chunks}

    assert filenames == {"paper.pdf"}
    assert [c.page_number for c in chunks[:2]] == [1, 2]
    page3 = [c for c in chunks if c.page_number == 3]
    assert len(page3) > 1
    for prev, nxt in zip(page3, page3[1:], strict=False):
        assert nxt.text.split()[0] in prev.text.split()


def test_list_documents_shows_name_pages_and_status(api: TestClient) -> None:
    """AC-08"""
    _upload(api, make_pdf(["a", "b"]), name="first.pdf")
    _upload(api, make_pdf(["c"]), name="second.pdf")

    docs = api.get("/documents").json()

    assert [(d["filename"], d["page_count"], d["status"]) for d in docs] == [
        ("second.pdf", 1, "ready"),
        ("first.pdf", 2, "ready"),
    ]


def test_unknown_document_is_404(api: TestClient) -> None:
    assert api.get(f"/documents/{uuid.uuid4()}").status_code == 404
