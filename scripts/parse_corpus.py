"""Parse downloaded corpus files and store pages or dead-letter failures."""

import argparse
import asyncio
import hashlib
import json
from pathlib import Path

from sqlalchemy import select

from nyayasetu.db.models import ParseFailure
from nyayasetu.db.session import SessionLocal, engine
from nyayasetu.ingest.parse import ParseError, parse_file, parse_pdf_ocr
from nyayasetu.ingest.store import store_failure, store_parsed

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "manifest.jsonl"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_manifest() -> list[dict]:
    if not MANIFEST_PATH.exists():
        return []

    records = []
    for line in MANIFEST_PATH.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue

        if (
            isinstance(record, dict)
            and record.get("status") == "downloaded"
            and isinstance(record.get("path"), str)
            and record["path"].strip()
        ):
            records.append(record)

    return records


def safe_path(value: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ParseError("invalid_path", "path must be a non-empty string")

    path = (ROOT / value).resolve()

    try:
        path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ParseError(
            "unsafe_path",
            "path is outside the project root",
        ) from exc

    return path


async def process_record(record: dict, ocr_language: str | None) -> str:
    record_path = record.get("path")

    if not isinstance(record_path, str) or not record_path.strip():
        print("FAILED  Manifest record has no valid path.")
        return "failed"

    try:
        path = safe_path(record_path)
    except ParseError as error:
        print(f"FAILED  {record_path}: {error}")
        return "failed"

    try:
        if not path.is_file():
            raise ParseError("missing_file", str(path))

        expected_hash = record.get("sha256", "")
        actual_hash = sha256_file(path)

        if expected_hash and actual_hash != expected_hash:
            raise ParseError(
                "hash_mismatch",
                "SHA-256 does not match manifest",
            )

        try:
            parsed = parse_file(path)
        except ParseError as error:
            if ocr_language and path.suffix.lower() == ".pdf" and error.reason == "no_text_layer":
                parsed = parse_pdf_ocr(path, language=ocr_language)
            else:
                raise

        async with SessionLocal() as session:
            await store_parsed(
                session,
                path,
                parsed,
                source_url=record.get("url"),
                licence=record.get("licence"),
            )

        char_count = sum(len(page.text) for page in parsed.pages)
        print(f"PARSED  {record_path} ({len(parsed.pages)} pages, {char_count} chars)")
        return "parsed"

    except ParseError as error:
        async with SessionLocal() as session:
            await store_failure(
                session,
                path,
                error,
                source_url=record.get("url"),
            )

        print(f"FAILED  {record_path}: {error}")
        return "failed"

    except Exception as error:
        parse_error = ParseError(
            "crash",
            f"{type(error).__name__}: {error}",
        )

        async with SessionLocal() as session:
            await store_failure(
                session,
                path,
                parse_error,
                source_url=record.get("url"),
            )

        print(f"FAILED  {record_path}: {parse_error}")
        return "failed"


async def retry_failed_records() -> list[dict]:
    manifest_records = read_manifest()
    manifest_by_path = {}

    for record in manifest_records:
        try:
            manifest_path = safe_path(record["path"])
        except (ParseError, KeyError):
            continue
        manifest_by_path[manifest_path.as_posix()] = record

    async with SessionLocal() as session:
        failures = (
            await session.scalars(select(ParseFailure).order_by(ParseFailure.created_at))
        ).all()

        records = []

        for failure in failures:
            try:
                path = safe_path(failure.path)
            except ParseError:
                print(f"SKIPPED unsafe failure path: {failure.path}")
                continue

            original = manifest_by_path.get(path.as_posix(), {})
            records.append(
                {
                    "path": path.relative_to(ROOT).as_posix(),
                    "url": failure.source_url or original.get("url"),
                    "sha256": failure.sha256 or original.get("sha256", ""),
                    "licence": original.get("licence"),
                }
            )

        return records


async def main() -> None:
    parser = argparse.ArgumentParser(description="Parse the downloaded document corpus.")
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Maximum files to process",
    )
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Retry paths currently recorded in parse_failures",
    )
    parser.add_argument(
        "--ocr",
        metavar="LANGUAGE",
        help="Enable OCR fallback for scanned PDFs (for example: eng)",
    )
    args = parser.parse_args()

    if args.limit < 0:
        parser.error("--limit must be zero or greater")

    try:
        records = await retry_failed_records() if args.retry_failed else read_manifest()

        if args.limit:
            records = records[: args.limit]

        if not records:
            print("No documents to parse.")

            if args.retry_failed:
                print("No failed records to retry.")
            else:
                print("Downloaded corpus records: 0")

            return

        counts = {"parsed": 0, "failed": 0}

        for record in records:
            result = await process_record(record, args.ocr)
            counts[result] += 1

        print("\nParsing summary")
        print(f"Total processed: {sum(counts.values())}")
        print(f"Parsed:          {counts['parsed']}")
        print(f"Failed:          {counts['failed']}")

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
