import hashlib
import math
import re
from collections.abc import Sequence
from functools import lru_cache
from typing import Protocol

from app.config import get_settings
from app.db.models import EMBEDDING_DIM


class Embedder(Protocol):
    """Turns text into vectors. Swap implementations without touching callers (NFR-11)."""

    dim: int

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class BgeEmbedder:
    """Local BAAI/bge-small-en-v1.5 model via sentence-transformers (runs on CPU)."""

    # bge models work best when search queries (not passages) get this prefix.
    QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer  # heavy import, only when used

        self._model = SentenceTransformer(model_name, device="cpu")
        self.dim = len(self.embed_query("dimension check"))

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        vectors = self._model.encode(list(texts), batch_size=32, normalize_embeddings=True)
        return vectors.tolist()

    def embed_query(self, text: str) -> list[float]:
        return self._model.encode(self.QUERY_PREFIX + text, normalize_embeddings=True).tolist()


class HashingEmbedder:
    """Deterministic fake for tests and CI: no model download, no network.

    Each word is hashed into one of `dim` slots, so texts that share words get similar
    vectors. It matches words, not meaning ("car" and "automobile" are unrelated here).
    """

    def __init__(self, dim: int = EMBEDDING_DIM) -> None:
        self.dim = dim

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dim
        for token in re.findall(r"[a-z0-9]+", text.lower()):
            slot = int(hashlib.md5(token.encode()).hexdigest(), 16) % self.dim
            vector[slot] += 1.0
        norm = math.sqrt(sum(v * v for v in vector))
        if norm == 0:
            return vector
        return [v / norm for v in vector]

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


@lru_cache
def get_embedder() -> Embedder:
    settings = get_settings()
    embedder: Embedder
    if settings.embedding_provider == "hashing":
        embedder = HashingEmbedder()
    else:
        embedder = BgeEmbedder(settings.embedding_model)
    if embedder.dim != EMBEDDING_DIM:
        raise RuntimeError(
            f"Embedding model returns {embedder.dim} dims but the database expects "
            f"{EMBEDDING_DIM}. Add a migration before switching models."
        )
    return embedder
