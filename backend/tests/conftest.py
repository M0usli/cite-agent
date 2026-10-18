import os
from collections.abc import Iterator
from pathlib import Path

# Point the app at a separate test database and the no-download embedder BEFORE app imports.
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://cite:cite@localhost:5432/cite_test"
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["EMBEDDING_PROVIDER"] = "hashing"
os.environ["SEARCH_PROVIDER"] = "fake"  # no real web calls in tests (NFR-09)

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, make_url, text  # noqa: E402
from sqlalchemy.exc import OperationalError  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from app.db.session import get_engine  # noqa: E402
from app.main import app  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _create_database_if_missing(url: str) -> None:
    parsed = make_url(url)
    admin = create_engine(parsed.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": parsed.database}
        )
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{parsed.database}"'))
    admin.dispose()


@pytest.fixture(scope="session")
def migrated_db() -> None:
    """Create the test DB and run the real Alembic migrations once per test session."""
    try:
        _create_database_if_missing(TEST_DATABASE_URL)
    except OperationalError as exc:
        if os.environ.get("CI"):
            raise
        pytest.skip(f"Postgres not reachable at {TEST_DATABASE_URL}: {exc}")
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    command.upgrade(config, "head")


@pytest.fixture
def db_session_factory(migrated_db: None) -> sessionmaker[Session]:
    """Empty tables before each DB test."""
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE chunks, documents CASCADE"))
    return sessionmaker(bind=engine)


@pytest.fixture
def api(db_session_factory: sessionmaker[Session]) -> Iterator[TestClient]:
    """Client against the real app and test database. Background tasks run before it returns."""
    with TestClient(app) as client:
        yield client
