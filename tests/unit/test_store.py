import hashlib
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from nyayasetu.db.models import Document, Page, ParseFailure
from nyayasetu.ingest import store
from nyayasetu.ingest.parse import ParsedDoc, ParsedPage, ParseError


def make_parsed_doc():
    return ParsedDoc(
        parser="plain",
        kind="text",
        title="Test Document",
        pages=[
            ParsedPage(
                page_no=1,
                text="Test page content",
                headings=["Introduction"],
                tables=0,
            )
        ],
    )


def make_session(scalar_result=None):
    session = MagicMock()
    session.scalar = AsyncMock(return_value=scalar_result)
    session.flush = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.add = MagicMock()
    return session


def test_file_sha256(tmp_path):
    path = tmp_path / "sample.txt"
    path.write_bytes(b"NyayaSetu test content")

    expected = hashlib.sha256(b"NyayaSetu test content").hexdigest()

    assert store.file_sha256(path) == expected


def test_stored_path_inside_project(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "PROJECT_ROOT", tmp_path)

    path = tmp_path / "data" / "sample.pdf"

    assert store.stored_path(path) == "data/sample.pdf"


def test_stored_path_outside_project(tmp_path, monkeypatch):
    project = tmp_path / "project"
    external = tmp_path / "external" / "sample.pdf"
    monkeypatch.setattr(store, "PROJECT_ROOT", project)

    assert store.stored_path(external) == external.resolve().as_posix()


@pytest.mark.asyncio
async def test_store_parsed_new_document(tmp_path):
    path = tmp_path / "document.txt"
    path.write_text("Test document content", encoding="utf-8")

    session = make_session()
    parsed = make_parsed_doc()

    document = await store.store_parsed(
        session,
        path,
        parsed,
        source_url="https://example.com/document",
        licence="CC BY 4.0",
    )

    added = [call.args[0] for call in session.add.call_args_list]

    saved_document = next(item for item in added if isinstance(item, Document))
    saved_page = next(item for item in added if isinstance(item, Page))

    assert document is saved_document
    assert saved_document.title == "Test Document"
    assert saved_document.source_url == "https://example.com/document"
    assert saved_document.licence == "CC BY 4.0"
    assert saved_document.doc_type == "text"
    assert saved_document.metadata_["pages"] == 1
    assert saved_page.page_no == 1
    assert saved_page.text == "Test page content"
    assert saved_page.headings == ["Introduction"]

    session.flush.assert_awaited_once()
    session.execute.assert_awaited_once()
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_store_parsed_existing_document(tmp_path):
    path = tmp_path / "document.txt"
    path.write_text("Updated document content", encoding="utf-8")

    existing = SimpleNamespace(
        id=42,
        title="Old title",
        source_url="https://old.example.com",
        licence="Old licence",
        doc_type="record",
        metadata_={},
    )

    session = make_session(existing)

    document = await store.store_parsed(
        session,
        path,
        make_parsed_doc(),
    )

    added = [call.args[0] for call in session.add.call_args_list]

    assert document is existing
    assert existing.title == "Test Document"
    assert existing.source_url == "https://old.example.com"
    assert existing.licence == "Old licence"
    assert existing.doc_type == "text"
    assert existing.metadata_["pages"] == 1
    assert any(isinstance(item, Page) for item in added)

    session.flush.assert_awaited_once()
    assert session.execute.await_count == 2
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_store_parsed_updates_source_and_licence(tmp_path):
    path = tmp_path / "document.txt"
    path.write_text("Updated document content", encoding="utf-8")

    existing = SimpleNamespace(
        id=43,
        title="Old title",
        source_url="https://old.example.com",
        licence="Old licence",
        doc_type="record",
        metadata_={},
    )

    session = make_session(existing)

    await store.store_parsed(
        session,
        path,
        make_parsed_doc(),
        source_url="https://new.example.com",
        licence="CC0",
    )

    assert existing.source_url == "https://new.example.com"
    assert existing.licence == "CC0"


@pytest.mark.asyncio
async def test_store_failure_new_record(tmp_path):
    path = tmp_path / "broken.pdf"
    path.write_bytes(b"broken PDF content")

    session = make_session()
    error = ParseError("corrupt", "Invalid PDF")

    await store.store_failure(
        session,
        path,
        error,
        source_url="https://example.com/broken.pdf",
    )

    added = [call.args[0] for call in session.add.call_args_list]
    failure = next(item for item in added if isinstance(item, ParseFailure))

    assert failure.path == store.stored_path(path)
    assert failure.sha256 == store.file_sha256(path)
    assert failure.reason == "corrupt"
    assert failure.detail == "Invalid PDF"
    assert failure.attempts == 1
    assert failure.source_url == "https://example.com/broken.pdf"

    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_store_failure_updates_existing_record(tmp_path):
    path = tmp_path / "broken.pdf"
    path.write_bytes(b"updated broken PDF")

    existing = SimpleNamespace(
        sha256="old-hash",
        source_url="https://old.example.com",
        reason="old-error",
        detail="Old detail",
        attempts=1,
    )

    session = make_session(existing)

    await store.store_failure(
        session,
        path,
        ParseError("corrupt", "Updated detail"),
    )

    assert existing.sha256 == store.file_sha256(path)
    assert existing.source_url == "https://old.example.com"
    assert existing.reason == "corrupt"
    assert existing.detail == "Updated detail"
    assert existing.attempts == 2

    session.add.assert_not_called()
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_store_failure_updates_source_url(tmp_path):
    path = tmp_path / "broken.pdf"
    path.write_bytes(b"broken PDF")

    existing = SimpleNamespace(
        sha256="old-hash",
        source_url=None,
        reason="old-error",
        detail="Old detail",
        attempts=1,
    )

    session = make_session(existing)

    await store.store_failure(
        session,
        path,
        ParseError("corrupt", "Updated detail"),
        source_url="https://example.com/retry.pdf",
    )

    assert existing.source_url == "https://example.com/retry.pdf"
    assert existing.attempts == 2


@pytest.mark.asyncio
async def test_store_failure_missing_file(tmp_path):
    path = tmp_path / "missing.pdf"
    session = make_session()

    await store.store_failure(
        session,
        path,
        ParseError("missing", "File not found"),
    )

    failure = session.add.call_args.args[0]

    assert isinstance(failure, ParseFailure)
    assert failure.sha256 == ""
    assert failure.attempts == 1


@pytest.mark.asyncio
async def test_store_failure_checksum_oserror(tmp_path, monkeypatch):
    path = tmp_path / "unreadable.pdf"
    path.write_bytes(b"content")

    def raise_oserror(_path):
        raise OSError("Cannot read file")

    monkeypatch.setattr(store, "file_sha256", raise_oserror)

    session = make_session()

    await store.store_failure(
        session,
        path,
        ParseError("read_error", "Cannot read file"),
    )

    failure = session.add.call_args.args[0]

    assert failure.sha256 == ""
    assert failure.reason == "read_error"
