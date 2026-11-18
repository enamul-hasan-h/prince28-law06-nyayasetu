"""Show how PostgreSQL executes a JSONB metadata filter.

Run:
    python scripts/explain.py <field> <value>
"""

import asyncio
import json
import sys

from sqlalchemy import text

from nyayasetu.db.session import engine

SQL = """
EXPLAIN ANALYZE
SELECT id, title
FROM documents
WHERE metadata @> CAST(:f AS jsonb)
"""


async def main(field: str, value: str) -> None:
    params = {"f": json.dumps({field: value})}

    try:
        async with engine.connect() as conn:
            print("-- 1) PostgreSQL's normal query plan:")
            result = await conn.execute(text(SQL), params)
            for line in result.scalars():
                print(line)

            print("\n-- 2) Query plan with sequential scans disabled:")
            await conn.execute(text("SET LOCAL enable_seqscan = off"))
            result = await conn.execute(text(SQL), params)
            for line in result.scalars():
                print(line)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: python scripts/explain.py <field> <value>")

    asyncio.run(main(sys.argv[1], sys.argv[2]))
