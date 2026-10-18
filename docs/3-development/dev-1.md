# Dev-1 — Skeleton, Docker Compose, CI

**Implements:** NFR-05 (keys from env vars, `.env` gitignored), NFR-09 (CI with mocked tests), NFR-10 (`docker compose up`). Groundwork for every FR.

## What was built
- **Backend** (`backend/`): FastAPI app with settings from env vars (`app/config.py`), a SQLAlchemy engine (`app/db/session.py`), and `GET /health`, which runs `SELECT 1` and returns 503 if the database is down. CORS allows the frontend origin.
- **Frontend** (`frontend/`): Next.js 16 (App Router, TypeScript strict, Tailwind). The home page has a "System status" card that calls `/health` from the browser, which shows the two apps talking.
- **Docker Compose**: `db` (pgvector/pgvector:pg17 with a healthcheck), `backend` (port 8000, hot reload), `frontend` (port 3000, hot reload). The backend waits until the DB is healthy.
- **CI** (`.github/workflows/ci.yml`): on every push and PR, the backend job runs ruff and pytest, and the frontend job runs ESLint, tsc, and Vitest.

## How to run
```bash
cp .env.example .env        # optional for now; no keys needed until Dev-3
docker compose up --build
```
- Frontend: http://localhost:3000 → "API: ok, Database: ok"
- API: http://localhost:8000/health and interactive docs at http://localhost:8000/docs

Local checks without Docker:
```bash
cd backend && python -m venv .venv && .venv/Scripts/pip install -e ".[dev]" && .venv/Scripts/ruff check . && .venv/Scripts/pytest
cd frontend && npm ci && npm run lint && npm run typecheck && npm test
```

## Tests
| Test | Checks |
|---|---|
| `backend/tests/test_health.py` (3) | 200 when DB answers, 503 when DB down (mocked session), CORS header for the frontend |
| `frontend/src/components/BackendStatus.test.tsx` (2) | Shows API/DB status from a mocked `/health`, shows an error when fetch fails |

## Notes
- `npm run typecheck` runs `next typegen` first, because Next 16 generates route types such as `LayoutProps`.
- `@types/node` is pinned to v24 to match Node 24 and Vitest's peer range.
- `frontend/AGENTS.md` is written by Next.js itself (`next dev` re-adds it), so it's committed.
