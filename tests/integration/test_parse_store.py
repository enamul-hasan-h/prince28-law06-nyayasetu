import asyncio
import os
from pathlib import Path

import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from nyayasetu.db.models import Document, Page, ParseFailure
from nyayasetu.db.url import to_asyncpg_url
from nyayasetu.ingest.parse import ParseError, parse_text
from nyayasetu.ingest.store import store_failure, store_parsed

pytestmark = pytest.mark.integration


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


def test_store_parsed_document(test_database_url, tmp_path: Path):
    async def operation(session):
        path = tmp_path / "integration.txt"
        path.write_text(
            "# Eligibility\n\nApplicants qualify for legal aid.",
            encoding="utf-8",
        )
        parsed = parse_text(path)
        document = None

        try:
            document = await store_parsed(
                session,
                path,
                parsed,
                source_url="https://example.org/test",
            )

            result = await session.scalar(select(Document).where(Document.id == document.id))
            pages = (
                await session.scalars(select(Page).where(Page.document_id == document.id))
            ).all()

            assert result is not None
            assert result.doc_type == "text"
            assert len(pages) >= 1
            assert "Applicants qualify" in pages[0].text

        finally:
            if document is not None:
                await session.execute(delete(Document).where(Document.id == document.id))
                await session.commit()

    run_db_test(test_database_url, operation)


def test_store_parse_failure(test_database_url, tmp_path: Path):
    async def operation(session):
        path = tmp_path / "broken.xyz"
        path.write_text("Unsupported file", encoding="utf-8")

        try:
            await store_failure(
                session,
                path,
                ParseError("unsupported_type", ".xyz"),
            )

            failure = await session.scalar(
                select(ParseFailure).where(ParseFailure.path == path.as_posix())
            )

            assert failure is not None
            assert failure.reason == "unsupported_type"
            assert failure.attempts == 1

        finally:
            await session.execute(delete(ParseFailure).where(ParseFailure.path == path.as_posix()))
            await session.commit()

    run_db_test(test_database_url, operation)
