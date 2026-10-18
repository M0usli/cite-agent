import math

from app.db.models import EMBEDDING_DIM
from app.providers.embeddings import HashingEmbedder


def _cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def test_hashing_embedder_is_deterministic_and_normalized() -> None:
    embedder = HashingEmbedder()

    v1 = embedder.embed_query("sample size of the study")
    v2 = embedder.embed_query("sample size of the study")

    assert v1 == v2
    assert len(v1) == EMBEDDING_DIM
    assert math.isclose(math.sqrt(sum(x * x for x in v1)), 1.0)


def test_shared_words_score_higher_than_unrelated_text() -> None:
    embedder = HashingEmbedder()
    query = embedder.embed_query("sample size")
    related, unrelated = embedder.embed_documents(
        ["The sample size was 412 participants.", "Bananas are yellow fruit."]
    )

    assert _cosine(query, related) > _cosine(query, unrelated)


def test_empty_text_gives_zero_vector() -> None:
    assert HashingEmbedder().embed_query("") == [0.0] * EMBEDDING_DIM
