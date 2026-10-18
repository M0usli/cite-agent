import logging
import uuid

from sqlalchemy.orm import Session, sessionmaker

from app.db.models import Chunk, Document, DocumentStatus
from app.ingestion.chunk import chunk_pages
from app.ingestion.extract import extract_pages
from app.providers.embeddings import Embedder

logger = logging.getLogger(__name__)

NO_TEXT_ERROR = "No text found in this PDF. It may be a scanned image (OCR is not supported)."


def process_document(
    document_id: uuid.UUID,
    data: bytes,
    session_factory: sessionmaker[Session],
    embedder: Embedder,
    chunk_size: int,
    chunk_overlap: int,
) -> None:
    """Extract → chunk → embed → store. Runs as a background task after upload (FR-02–FR-04)."""
    with session_factory() as session:
        document = session.get(Document, document_id)
        if document is None:
            logger.warning("Document %s disappeared before processing", document_id)
            return
        try:
            extracted = extract_pages(data)
            chunks = chunk_pages(extracted.pages, chunk_size, chunk_overlap)
            document.skipped_pages = extracted.skipped_pages

            if not chunks:
                document.status = DocumentStatus.FAILED
                document.error = NO_TEXT_ERROR
                session.commit()
                return

            vectors = embedder.embed_documents([c.text for c in chunks])
            session.add_all(
                Chunk(
                    document_id=document.id,
                    page_number=c.page_number,
                    chunk_index=c.chunk_index,
                    text=c.text,
                    embedding=vector,
                )
                for c, vector in zip(chunks, vectors, strict=True)
            )
            document.chunk_count = len(chunks)
            document.status = DocumentStatus.READY
            session.commit()
        except Exception as exc:
            logger.exception("Processing failed for document %s", document_id)
            session.rollback()
            document.status = DocumentStatus.FAILED
            document.error = f"Processing failed: {exc}"[:500]
            session.commit()
