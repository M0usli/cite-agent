# Dev-2 — PDF ingestion and vector search

**Implements:** FR-01 (upload + validation), FR-02 (page-by-page extraction), FR-03 (chunking with overlap), FR-04 (embeddings in pgvector), FR-05 (document list), FR-17 backend part (status endpoint for polling). Groundwork for FR-06 (`search_chunks`, used by the `search_documents` tool in Dev-3). NFR-11 (embedder behind an interface).

## What was built
| Piece | File | Notes |
|---|---|---|
| Tables + migration | `app/db/models.py`, `alembic/versions/0001_…py` | `documents`, `chunks` with `vector(384)` and an HNSW cosine index. Migrations run on container start. |
| Upload API | `app/api/documents.py` | `POST /documents` checks size (≤ 20 MB), PDF signature, readability, and pages (≤ 50), then returns **202** and processes in the background. `GET /documents`, `GET /documents/{id}`. |
| Extraction | `app/ingestion/extract.py` | PyMuPDF, one entry per page, 1-based page numbers. Pages with no text are listed in `skipped_pages`. |
| Chunking | `app/ingestion/chunk.py` | Each page is chunked on its own (so page numbers are exact). About 1,000 chars per chunk, 200 overlap, cuts at spaces. |
| Embeddings | `app/providers/embeddings.py` | `Embedder` interface. `BgeEmbedder` (bge-small-en-v1.5, CPU, normalized, query prefix) and `HashingEmbedder` (fake, used by tests/CI). Chosen with `EMBEDDING_PROVIDER`. |
| Pipeline | `app/ingestion/pipeline.py` | extract → chunk → embed → store → status `ready`. No text → `failed` with a clear message. Any exception → `failed` with the error. |
| Search | `app/retrieval.py`, `app/api/debug.py` | Cosine search over chunks of Ready documents only. `GET /debug/search?q=&k=` exists only when `DEBUG_ENDPOINTS=true` (on in Docker, off by default). |

## Try it
1. `docker compose up --build` (the first build downloads CPU PyTorch; the first upload downloads the ~130 MB model into the `models` volume).
2. Open http://localhost:8000/docs → **POST /documents** → *Try it out* → choose a PDF → *Execute*.
3. **GET /documents** shows status `processing` → `ready`, plus `chunk_count` and `skipped_pages`.
4. **GET /debug/search** with a question in your own words. Results show document name, page, and score.

Manual check with the real model (a 4-page test PDF, page 3 blank):

| Query | Top hit | Score |
|---|---|---|
| "how many people took part in the study" | p. 2: "We recruited 412 undergraduate volunteers…" | 0.74 |
| "does losing sleep hurt recall" | p. 1: "Effects of sleep on memory in university students." | 0.75 |

The first query matched on **meaning**: the passage never says "people" or "took part". Page 3 was reported in `skipped_pages`.

## Tests (30 total, all passing locally and in the container)
| Test file | ACs |
|---|---|
| `test_extract.py` | AC-03, AC-04 |
| `test_chunk.py` | AC-06 (overlap, page numbers, no broken words, full coverage) |
| `test_documents_api.py` | AC-01, AC-02 (non-PDF, > 50 pages, > 20 MB, corrupt), AC-04, AC-05, AC-06, AC-07, AC-08 |
| `test_search.py` | AC-09, AC-10 (via debug endpoint), failed docs not searched, debug off when disabled |
| `test_embeddings.py` | HashingEmbedder deterministic, normalized, shared words rank higher |

DB tests run against a real Postgres + pgvector (`cite_test` database, created automatically, migrated with Alembic). In CI it's a Postgres service container. Locally, tests are skipped if Postgres isn't running.

Run tests: `docker compose exec backend pytest` or `cd backend && .venv/Scripts/pytest`.

## Notes / decisions
- **202 + background task** instead of waiting: embedding 50 pages can take a while on CPU, and the UI polls `GET /documents/{id}` (design D5).
- **`chunk_count` column** was added to `documents` (needed for AC-07). `design.md` is updated.
- **CI does not install PyTorch:** `sentence-transformers` is an optional extra (`.[embeddings]`), and CI uses `HashingEmbedder`. This keeps CI fast and needs no model download.
- The Docker image installs the **CPU-only** PyTorch wheel, which is much smaller than the default CUDA build.
- The original PDF file is not stored, only its text chunks. Document citations will show the stored passage (FR-15).
