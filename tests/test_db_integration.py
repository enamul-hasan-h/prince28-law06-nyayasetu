"""Optional integration tests against a dedicated PostgreSQL database."""

import asyncio
import os
from uuid import uuid4

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from nyayasetu.db.models import Document
from nyayasetu.db.repository import DocumentRepository
from nyayasetu.db.url import to_asyncpg_url


@pytest.fixture
def test_database_url():
    raw_url = os.getenv("TEST_DATABASE_URL")
    if not raw_url:
        pytest.skip("TEST_DATABASE_URL is not configured")

    return to_asyncpg_url(raw_url)


def run_db_test(database_url, operation):
    async def run():
        engine = create_async_engine(database_url, pool_pre_ping=True)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        try:
            async with session_factory() as session:
                await operation(session)
        finally:
            await engine.dispose()

    asyncio.run(run())


def test_repository_lists_filtered_documents(test_database_url):
    async def operation(session):
        external_id = f"it-{uuid4().hex}"
        document = Document(
            external_id=external_id,
            title="Integration Test Guideline",
            sha256=uuid4().hex,
            metadata_={"scheme": "Integration Test Scheme"},
        )

        session.add(document)
        await session.commit()

        try:
            total, items = await DocumentRepository(session).list(
                q=None,
                filters={"scheme": "Integration Test Scheme"},
                limit=20,
                offset=0,
            )

            assert total >= 1
            assert any(item["id"] == external_id for item in items)
        finally:
            await session.execute(delete(Document).where(Document.external_id == external_id))
            await session.commit()

    run_db_test(test_database_url, operation)


def test_repository_gets_document(test_database_url):
    async def operation(session):
        external_id = f"it-{uuid4().hex}"
        document = Document(
            external_id=external_id,
            title="Integration Test Document",
            sha256=uuid4().hex,
            metadata_={"scheme": "Integration Test"},
        )

        session.add(document)
        await session.commit()

        try:
            result = await DocumentRepository(session).get(external_id)

            assert result is not None
            assert result["id"] == external_id
            assert result["title"] == "Integration Test Document"
        finally:
            await session.execute(delete(Document).where(Document.external_id == external_id))
            await session.commit()

    run_db_test(test_database_url, operation)


def test_repository_returns_none_for_missing_document(test_database_url):
    async def operation(session):
        result = await DocumentRepository(session).get(f"missing-{uuid4().hex}")
        assert result is None

    run_db_test(test_database_url, operation)
