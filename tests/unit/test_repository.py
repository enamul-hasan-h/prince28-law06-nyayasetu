from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock

from nyayasetu.db.repository import (
    DocumentRepository,
    _value_candidates,
    to_dict,
)


def make_document():
    return SimpleNamespace(
        external_id="doc-001",
        metadata_={"category": "legal", "year": 2025},
        title="Legal Aid",
        doc_type="pdf",
        source_url="https://example.com/legal.pdf",
        licence="CC BY 4.0",
        published_on=date(2025, 1, 15),
    )


def test_to_dict_converts_document_fields():
    result = to_dict(make_document())

    assert result["id"] == "doc-001"
    assert result["title"] == "Legal Aid"
    assert result["category"] == "legal"
    assert result["published_on"] == "2025-01-15"


def test_to_dict_handles_missing_publication_date():
    doc = make_document()
    doc.published_on = None

    assert to_dict(doc)["published_on"] is None


def test_value_candidates_for_string():
    assert _value_candidates("legal") == ["legal", ["legal"]]


def test_value_candidates_for_booleans():
    assert _value_candidates("true") == ["true", ["true"], True]
    assert _value_candidates("false") == ["false", ["false"], False]


def test_value_candidates_for_numbers():
    assert _value_candidates("42") == ["42", ["42"], 42]
    assert _value_candidates("-3.5") == ["-3.5", ["-3.5"], -3.5]


async def test_repository_list_without_query_or_filters():
    doc = make_document()
    session = SimpleNamespace(
        scalar=AsyncMock(return_value=1),
        scalars=AsyncMock(return_value=[doc]),
    )

    repository = DocumentRepository(session)

    total, results = await repository.list(
        q=None,
        filters={},
        limit=10,
        offset=0,
    )

    assert total == 1
    assert len(results) == 1
    assert results[0]["id"] == "doc-001"
    session.scalar.assert_awaited_once()
    session.scalars.assert_awaited_once()


async def test_repository_list_with_query_and_filters():
    doc = make_document()
    session = SimpleNamespace(
        scalar=AsyncMock(return_value=1),
        scalars=AsyncMock(return_value=[doc]),
    )

    repository = DocumentRepository(session)

    total, results = await repository.list(
        q="Legal",
        filters={"category": "legal", "year": "2025"},
        limit=5,
        offset=2,
    )

    assert total == 1
    assert results[0]["title"] == "Legal Aid"
    session.scalar.assert_awaited_once()
    session.scalars.assert_awaited_once()


async def test_repository_list_returns_zero_when_count_is_none():
    session = SimpleNamespace(
        scalar=AsyncMock(return_value=None),
        scalars=AsyncMock(return_value=[]),
    )

    repository = DocumentRepository(session)

    total, results = await repository.list(
        q=None,
        filters={},
        limit=10,
        offset=0,
    )

    assert total == 0
    assert results == []


async def test_repository_get_existing_document():
    doc = make_document()
    session = SimpleNamespace(scalar=AsyncMock(return_value=doc))

    repository = DocumentRepository(session)

    result = await repository.get("doc-001")

    assert result is not None
    assert result["id"] == "doc-001"
    session.scalar.assert_awaited_once()


async def test_repository_get_missing_document():
    session = SimpleNamespace(scalar=AsyncMock(return_value=None))

    repository = DocumentRepository(session)

    result = await repository.get("missing")

    assert result is None
    session.scalar.assert_awaited_once()
