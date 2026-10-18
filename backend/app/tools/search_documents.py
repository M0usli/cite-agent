from typing import Any, ClassVar

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.providers.embeddings import Embedder
from app.retrieval import search_chunks
from app.tools.sources import SourceRegistry

MAX_CHUNK_CHARS = 1200  # keep tool results small; they use up the context window


class SearchDocumentsInput(BaseModel):
    query: str = Field(min_length=1, max_length=500, description="What to look for.")
    top_k: int = Field(default=5, ge=1, le=10, description="How many passages to return.")


class SearchDocuments:
    """FR-06: vector search over the user's uploaded PDFs."""

    name: ClassVar[str] = "search_documents"
    description: ClassVar[str] = (
        "Search the user's uploaded PDF documents by meaning. Use this first for any "
        "question about the user's documents, papers, notes or reports. Returns passages "
        "with a source_id, document name and page number. Returns an empty list if nothing "
        "has been uploaded."
    )
    Input: ClassVar[type[BaseModel]] = SearchDocumentsInput

    def __init__(self, session: Session, embedder: Embedder, sources: SourceRegistry) -> None:
        self._session = session
        self._embedder = embedder
        self._sources = sources

    def run(self, args: SearchDocumentsInput) -> dict[str, Any]:
        hits = search_chunks(self._session, self._embedder, args.query, args.top_k)
        results = []
        for hit in hits:
            source = self._sources.add_document(hit)
            results.append(
                {
                    "source_id": source.source_id,
                    "document": hit.document_name,
                    "page": hit.page_number,
                    "text": hit.text[:MAX_CHUNK_CHARS],
                    "score": hit.score,
                }
            )
        return {"results": results}
