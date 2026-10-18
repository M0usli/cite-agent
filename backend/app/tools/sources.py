import uuid
from dataclasses import dataclass
from typing import Literal

from app.retrieval import ChunkHit

SourceKind = Literal["document", "web"]
PREFIX: dict[SourceKind, str] = {"document": "D", "web": "W"}


@dataclass(frozen=True)
class Source:
    """Something a tool returned that the final answer may cite (design D3)."""

    source_id: str  # "D1", "W2", ...
    kind: SourceKind
    label: str  # "smith2024.pdf, p. 4" or the web page title
    text: str
    url: str | None = None
    chunk_id: uuid.UUID | None = None


class SourceRegistry:
    """Hands out source IDs for one agent run.

    IDs are numbered across the whole run, and the same chunk or URL always keeps the
    same ID, so "[D2]" can never mean two different things.
    """

    def __init__(self) -> None:
        self._sources: dict[str, Source] = {}
        self._id_by_key: dict[str, str] = {}
        self._counts: dict[SourceKind, int] = {"document": 0, "web": 0}

    def _next_id(self, kind: SourceKind) -> str:
        self._counts[kind] += 1
        return f"{PREFIX[kind]}{self._counts[kind]}"

    def _remember(self, key: str, source: Source) -> Source:
        self._sources[source.source_id] = source
        self._id_by_key[key] = source.source_id
        return source

    def add_document(self, hit: ChunkHit) -> Source:
        key = f"chunk:{hit.chunk_id}"
        if key in self._id_by_key:
            return self._sources[self._id_by_key[key]]
        return self._remember(
            key,
            Source(
                source_id=self._next_id("document"),
                kind="document",
                label=f"{hit.document_name}, p. {hit.page_number}",
                text=hit.text,
                chunk_id=hit.chunk_id,
            ),
        )

    def add_web(self, title: str, url: str, snippet: str) -> Source:
        key = f"url:{url}"
        if key in self._id_by_key:
            return self._sources[self._id_by_key[key]]
        return self._remember(
            key,
            Source(source_id=self._next_id("web"), kind="web", label=title, text=snippet, url=url),
        )

    def get(self, source_id: str) -> Source | None:
        return self._sources.get(source_id)

    def all(self) -> list[Source]:
        return list(self._sources.values())
