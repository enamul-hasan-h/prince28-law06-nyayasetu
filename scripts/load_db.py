"""Load legal scheme records into PostgreSQL idempotently."""

import asyncio
import hashlib
import json
from datetime import date

from sqlalchemy import select

from nyayasetu.config import get_settings
from nyayasetu.db.models import Document
from nyayasetu.db.session import SessionLocal, engine

TITLE_FIELD = "scheme"

KNOWN = {
    "id",
    "scheme",
    "title",
    "source_url",
    "licence",
    "doc_type",
    "published_on",
}


def fingerprint(record: dict) -> str:
    """Generate a stable SHA256 fingerprint for a record."""
    canonical = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def to_row(record: dict) -> dict:
    """Convert a JSON record into a database row."""
    published_on = record.get("published_on")

    return {
        "external_id": record["id"],
        "title": record[TITLE_FIELD],
        "source_url": record["source_url"],
        "licence": record.get("licence"),
        "doc_type": record.get("doc_type", "scheme"),
        "published_on": (date.fromisoformat(published_on) if published_on else None),
        "sha256": fingerprint(record),
        "metadata_": {key: value for key, value in record.items() if key not in KNOWN},
    }


async def main() -> None:
    settings = get_settings()
    records = json.loads(settings.data_file.read_text(encoding="utf-8"))

    inserted = 0
    updated = 0
    unchanged = 0

    async with SessionLocal() as session, session.begin():
        for record in records:
            row = to_row(record)

            existing = await session.scalar(
                select(Document).where(Document.external_id == row["external_id"])
            )

            if existing is None:
                session.add(Document(**row))
                inserted += 1

            elif existing.sha256 != row["sha256"]:
                for key, value in row.items():
                    setattr(existing, key, value)
                updated += 1

            else:
                unchanged += 1

    print(f"records={len(records)} inserted={inserted} updated={updated} unchanged={unchanged}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
