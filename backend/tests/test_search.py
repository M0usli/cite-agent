"""Vector search over stored chunks (groundwork for FR-06 / search_documents in Dev-3)."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings
from app.main import create_app
from tests.pdf_factory import make_pdf


@pytest.fixture
def debug_api(db_session_factory: sessionmaker[Session]) -> Iterator[TestClient]:
    with TestClient(create_app(Settings(debug_endpoints=True))) as client:
        yield client


def test_search_returns_matching_chunk_with_doc_and_page(debug_api: TestClient) -> None:
    """AC-09 (via the debug endpoint)"""
    pdf = make_pdf(
        [
            "Background on the research area.",
            "We recruited volunteers. The sample size was 412 participants.",
            "Results were significant.",
        ]
    )
    debug_api.post("/documents", files={"file": ("smith2024.pdf", pdf, "application/pdf")})

    hits = debug_api.get("/debug/search", params={"q": "sample size", "k": 3}).json()

    top = hits[0]
    assert "sample size was 412" in top["text"]
    assert top["document_name"] == "smith2024.pdf"
    assert top["page_number"] == 2
    assert top["score"] > hits[-1]["score"]


def test_search_with_no_documents_returns_empty_list(debug_api: TestClient) -> None:
    """AC-10"""
    res = debug_api.get("/debug/search", params={"q": "anything"})

    assert res.status_code == 200
    assert res.json() == []


def test_failed_documents_are_not_searched(debug_api: TestClient) -> None:
    debug_api.post("/documents", files={"file": ("scan.pdf", make_pdf([""]), "application/pdf")})

    assert debug_api.get("/debug/search", params={"q": "anything"}).json() == []


def test_debug_endpoint_is_off_when_disabled() -> None:
    client = TestClient(create_app(Settings(debug_endpoints=False)))

    assert client.get("/debug/search", params={"q": "x"}).status_code == 404
