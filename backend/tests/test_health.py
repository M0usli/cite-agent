from collections.abc import Iterator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.db.session import get_db
from app.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    yield TestClient(app)
    app.dependency_overrides.clear()


def _override_db(session: MagicMock) -> None:
    app.dependency_overrides[get_db] = lambda: session


def test_health_ok_when_database_answers(client: TestClient) -> None:
    _override_db(MagicMock())

    res = client.get("/health")

    assert res.status_code == 200
    assert res.json() == {"status": "ok", "database": "ok"}


def test_health_503_when_database_down(client: TestClient) -> None:
    session = MagicMock()
    session.execute.side_effect = OperationalError("SELECT 1", {}, Exception("down"))
    _override_db(session)

    res = client.get("/health")

    assert res.status_code == 503
    assert res.json() == {"status": "degraded", "database": "unreachable"}


def test_cors_allows_frontend_origin(client: TestClient) -> None:
    _override_db(MagicMock())

    res = client.get("/health", headers={"Origin": "http://localhost:3000"})

    assert res.headers["access-control-allow-origin"] == "http://localhost:3000"
