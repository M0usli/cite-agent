"""search_documents tool against a real Postgres + pgvector (FR-06)."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.providers.embeddings import HashingEmbedder
from app.tools.registry import ToolRegistry
from app.tools.search_documents import MAX_CHUNK_CHARS, SearchDocuments
from app.tools.sources import SourceRegistry
from tests.pdf_factory import make_pdf


def _upload(api: TestClient, name: str, pages: list[str]) -> None:
    api.post("/documents", files={"file": (name, make_pdf(pages), "application/pdf")})


def test_finds_passage_with_doc_name_page_and_source_id(
    api: TestClient, db_session_factory: sessionmaker[Session]
) -> None:
    """AC-09"""
    _upload(api, "smith2024.pdf", ["Introduction.", "The sample size was 412 participants."])
    sources = SourceRegistry()

    with db_session_factory() as session:
        registry = ToolRegistry([SearchDocuments(session, HashingEmbedder(), sources)])
        outcome = registry.execute("search_documents", {"query": "sample size", "top_k": 2})

    assert outcome.is_error is False
    top = outcome.content["results"][0]
    assert "sample size was 412" in top["text"]
    assert (top["document"], top["page"], top["source_id"]) == ("smith2024.pdf", 2, "D1")
    assert sources.get("D1").label == "smith2024.pdf, p. 2"


def test_no_documents_gives_empty_list_not_error(
    db_session_factory: sessionmaker[Session],
) -> None:
    """AC-10"""
    with db_session_factory() as session:
        registry = ToolRegistry([SearchDocuments(session, HashingEmbedder(), SourceRegistry())])
        outcome = registry.execute("search_documents", {"query": "anything"})

    assert outcome.is_error is False
    assert outcome.content == {"results": []}


def test_long_passages_are_capped(
    api: TestClient, db_session_factory: sessionmaker[Session]
) -> None:
    # A chunk is at most ~1,000 chars, so the cap is a safety net; check it holds.
    _upload(api, "long.pdf", [" ".join(["photosynthesis"] * 400)])

    with db_session_factory() as session:
        registry = ToolRegistry([SearchDocuments(session, HashingEmbedder(), SourceRegistry())])
        outcome = registry.execute("search_documents", {"query": "photosynthesis"})

    assert all(len(r["text"]) <= MAX_CHUNK_CHARS for r in outcome.content["results"])


def test_invalid_top_k_is_an_error_result(db_session_factory: sessionmaker[Session]) -> None:
    with db_session_factory() as session:
        registry = ToolRegistry([SearchDocuments(session, HashingEmbedder(), SourceRegistry())])
        outcome = registry.execute("search_documents", {"query": "x", "top_k": 99})

    assert outcome.is_error is True
    assert "top_k" in outcome.content["error"]
