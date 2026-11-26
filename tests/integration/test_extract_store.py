import asyncio
import json
import os

import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from nyayasetu.db.models import Document, Page
from nyayasetu.db.url import to_asyncpg_url
from nyayasetu.llm.doc_meta import DocMeta
from nyayasetu.llm.extract import run
from nyayasetu.llm.gateway import FakeLLM, LLMGateway

pytestmark = pytest.mark.integration


@pytest.fixture
def test_database_url():
    raw_url = os.getenv("TEST_DATABASE_URL")
    if not raw_url:
        pytest.skip("TEST_DATABASE_URL is not configured")

    return to_asyncpg_url(raw_url)


def run_db_test(database_url, operation):
    async def run_test():
        engine = create_async_engine(database_url, pool_pre_ping=True)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        try:
            async with session_factory() as session:
                await operation(session)
        finally:
            await engine.dispose()

    asyncio.run(run_test())


def test_extract_metadata_is_stored(test_database_url):
    async def operation(session):
        external_id = "extract-integration-test"
        document = Document(
            external_id=external_id,
            title="Integration test legal aid document",
            doc_type="text",
            sha256="extract-integration-test-sha256",
            metadata_={"source": "integration-test"},
        )
        session.add(document)
        await session.flush()

        session.add(
            Page(
                document_id=document.id,
                page_no=1,
                text="This guideline explains eligibility for free legal aid.",
                headings=[],
            )
        )
        await session.commit()

        reply = {
            "doc_kind": "guideline",
            "year": 2024,
            "language": "en",
            "summary": "Explains eligibility for free legal aid services.",
            "topics": ["Legal aid"],
            "scheme": [],
            "section": [],
            "eligible_group": ["Applicants"],
            "benefit": ["Free legal assistance"],
            "authority_level": ["District"],
        }
        llm = FakeLLM(script=[json.dumps(reply)])
        gateway = LLMGateway([llm])

        try:
            counts = await run(
                async_sessionmaker(
                    session.bind,
                    expire_on_commit=False,
                ),
                gateway,
                DocMeta,
                "Extract metadata.",
                "extract_v1",
                limit=5,
                sleep=lambda _: asyncio.sleep(0),
                echo=lambda _: None,
            )

            await session.refresh(document)
            stored = await session.scalar(select(Document).where(Document.id == document.id))

            assert counts["pending"] == 1
            assert counts["ok"] == 1
            assert stored.metadata_["doc_kind"] == "guideline"
            assert stored.metadata_["year"] == 2024
            assert stored.metadata_["source"] == "integration-test"
            assert stored.metadata_["extract"]["prompt"] == "extract_v1"

        finally:
            await session.execute(delete(Document).where(Document.id == document.id))
            await session.commit()

    run_db_test(test_database_url, operation)
