import uuid
from datetime import datetime
from pathlib import PurePath
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings, get_settings
from app.db.models import Document, DocumentStatus
from app.db.session import get_db, get_session_factory
from app.ingestion.extract import InvalidPdfError, open_pdf
from app.ingestion.pipeline import process_document
from app.providers.embeddings import Embedder, get_embedder

router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    page_count: int
    status: DocumentStatus
    skipped_pages: list[int]
    chunk_count: int
    error: str | None
    created_at: datetime


@router.post("", status_code=202, response_model=DocumentOut)
def upload_document(
    file: UploadFile,
    background: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
    session_factory: Annotated[sessionmaker[Session], Depends(get_session_factory)],
    embedder: Annotated[Embedder, Depends(get_embedder)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Document:
    """Validate and save the upload, then process it in the background (FR-01)."""
    max_bytes = settings.max_upload_mb * 1024 * 1024
    data = file.file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(413, f"File is larger than {settings.max_upload_mb} MB.")
    if not data.startswith(b"%PDF-"):
        raise HTTPException(400, "Only PDF files are accepted.")
    try:
        with open_pdf(data) as pdf:
            page_count = len(pdf)
    except InvalidPdfError as exc:
        raise HTTPException(400, str(exc)) from exc
    if page_count > settings.max_pages:
        raise HTTPException(413, f"PDF has {page_count} pages; the limit is {settings.max_pages}.")

    filename = PurePath(file.filename or "document.pdf").name[:255]
    document = Document(filename=filename, page_count=page_count)
    db.add(document)
    db.commit()
    db.refresh(document)

    background.add_task(
        process_document,
        document.id,
        data,
        session_factory,
        embedder,
        settings.chunk_size,
        settings.chunk_overlap,
    )
    return document


@router.get("", response_model=list[DocumentOut])
def list_documents(db: Annotated[Session, Depends(get_db)]) -> list[Document]:
    """All documents, newest first (FR-05)."""
    return list(db.scalars(select(Document).order_by(Document.created_at.desc())))


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: uuid.UUID, db: Annotated[Session, Depends(get_db)]) -> Document:
    """One document's status; the UI polls this until Ready or Failed (FR-17)."""
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(404, "Document not found.")
    return document
