"""Verify the Neon PostgreSQL database connection."""

import asyncio

from sqlalchemy import text

from nyayasetu.db.session import engine


async def main() -> None:
    async with engine.connect() as connection:
        result = await connection.execute(
            text("SELECT current_database(), version(), inet_server_addr()")
        )

        database, version, server = result.one()

        print(f"Connected to database: {database}")
        print(f"PostgreSQL version: {version}")
        print(f"Server address: {server}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
