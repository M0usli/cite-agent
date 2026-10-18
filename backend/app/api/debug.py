import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.providers.embeddings import Embedder, get_embedder
from app.retrieval import search_chunks

# Only mounted when DEBUG_ENDPOINTS=true (see app.main).
router = APIRouter(prefix="/debug", tags=["debug"])


class ChunkHitOut(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_name: str
    page_number: int
    text: str
    score: float


@router.get("/search", response_model=list[ChunkHitOut])
def debug_search(
    db: Annotated[Session, Depends(get_db)],
    embedder: Annotated[Embedder, Depends(get_embedder)],
    q: Annotated[str, Query(min_length=1, max_length=1000)],
    k: Annotated[int, Query(ge=1, le=20)] = 5,
) -> list[ChunkHitOut]:
    """Raw vector search over stored chunks, to check retrieval quality by hand."""
    return [ChunkHitOut(**vars(hit)) for hit in search_chunks(db, embedder, q, k)]
