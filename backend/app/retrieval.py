import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Chunk, Document, DocumentStatus
from app.providers.embeddings import Embedder


@dataclass(frozen=True)
class ChunkHit:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_name: str
    page_number: int
    text: str
    score: float  # cosine similarity: 1 = same meaning, 0 = unrelated


def search_chunks(session: Session, embedder: Embedder, query: str, top_k: int) -> list[ChunkHit]:
    """Vector search over chunks of Ready documents, most similar first (FR-06)."""
    distance = Chunk.embedding.cosine_distance(embedder.embed_query(query)).label("distance")
    rows = session.execute(
        select(Chunk, Document.filename, distance)
        .join(Document)
        .where(Document.status == DocumentStatus.READY)
        .order_by(distance)
        .limit(top_k)
    ).all()
    return [
        ChunkHit(
            chunk_id=chunk.id,
            document_id=chunk.document_id,
            document_name=filename,
            page_number=chunk.page_number,
            text=chunk.text,
            score=round(1 - dist, 4),
        )
        for chunk, filename, dist in rows
    ]
