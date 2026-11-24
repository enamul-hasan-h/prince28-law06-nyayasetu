"""Store parsed documents and parsing failures in PostgreSQL."""

import hashlib
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from nyayasetu.db.models import Document, Page, ParseFailure
from nyayasetu.ingest.parse import ParsedDoc, ParseError

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def file_sha256(path: Path) -> str:
    """Calculate a file's SHA-256 checksum."""
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def stored_path(path: Path) -> str:
    """Store project files with portable relative paths."""
    resolved = Path(path).resolve()

    try:
        return resolved.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


async def store_parsed(
    session: AsyncSession,
    path: Path,
    parsed: ParsedDoc,
    *,
    source_url: str | None = None,
    licence: str | None = None,
) -> Document:
    """Insert or update a parsed document and replace its pages."""
    path = Path(path)
    checksum = file_sha256(path)
    relative_path = stored_path(path)

    document = await session.scalar(select(Document).where(Document.external_id == checksum))

    if document is None:
        document = Document(
            external_id=checksum,
            title=parsed.title,
            source_url=source_url,
            licence=licence,
            doc_type=parsed.kind,
            sha256=checksum,
            metadata_={
                "path": relative_path,
                "parser": parsed.parser,
                "pages": len(parsed.pages),
                "tables": sum(page.tables for page in parsed.pages),
            },
        )
        session.add(document)
        await session.flush()
    else:
        document.title = parsed.title
        if source_url is not None:
            document.source_url = source_url
        if licence is not None:
            document.licence = licence
        document.doc_type = parsed.kind
        document.metadata_ = {
            "path": relative_path,
            "parser": parsed.parser,
            "pages": len(parsed.pages),
            "tables": sum(page.tables for page in parsed.pages),
        }

        await session.execute(delete(Page).where(Page.document_id == document.id))
        await session.flush()

    for parsed_page in parsed.pages:
        session.add(
            Page(
                document_id=document.id,
                page_no=parsed_page.page_no,
                text=parsed_page.text,
                headings=parsed_page.headings,
            )
        )

    await session.execute(delete(ParseFailure).where(ParseFailure.path == relative_path))

    await session.commit()
    return document


async def store_failure(
    session: AsyncSession,
    path: Path,
    error: ParseError,
    *,
    source_url: str | None = None,
) -> None:
    """Record or update a failed file in the dead-letter table."""
    path = Path(path)
    relative_path = stored_path(path)

    try:
        checksum = file_sha256(path) if path.is_file() else ""
    except OSError:
        checksum = ""

    failure = await session.scalar(select(ParseFailure).where(ParseFailure.path == relative_path))

    if failure is None:
        failure = ParseFailure(
            path=relative_path,
            sha256=checksum,
            source_url=source_url,
            reason=error.reason,
            detail=error.detail,
            attempts=1,
        )
        session.add(failure)
    else:
        failure.sha256 = checksum
        if source_url is not None:
            failure.source_url = source_url
        failure.reason = error.reason
        failure.detail = error.detail
        failure.attempts += 1

    await session.commit()
