"""Shared fixtures for API unit tests."""

import pytest
from fastapi.testclient import TestClient

from nyayasetu.api.deps import get_repository, get_session
from nyayasetu.api.main import create_app
from nyayasetu.config import Settings

SAMPLE = [
    {"id": "001", "title": "Alpha guideline", "year": 2023, "kind": "guideline"},
    {"id": "002", "title": "Beta circular", "year": 2024, "kind": "circular"},
    {"id": "003", "title": "Gamma notice", "year": 2025, "kind": "circular"},
]


class FakeRepo:
    """In-memory replacement for DocumentRepository."""

    def __init__(self, rows):
        self.rows = rows

    async def list(self, *, q, filters, limit, offset):
        rows = [
            row
            for row in self.rows
            if (not q or q.lower() in str(row).lower())
            and all(str(row.get(key)) == value for key, value in filters.items())
        ]
        return len(rows), rows[offset : offset + limit]

    async def get(self, external_id):
        return next(
            (row for row in self.rows if row["id"] == external_id),
            None,
        )


class FakeSession:
    """Minimal fake database session for readiness tests."""

    async def execute(self, statement):
        return None


@pytest.fixture
def settings():
    return Settings(
        app_env="ci",
        database_url="",
        _env_file=None,
    )


@pytest.fixture
def client(settings):
    app = create_app(settings)

    async def fake_session():
        yield FakeSession()

    app.dependency_overrides[get_repository] = lambda: FakeRepo(SAMPLE)
    app.dependency_overrides[get_session] = fake_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
