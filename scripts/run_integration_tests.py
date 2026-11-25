"""Reset the integration test database, migrate it, and run integration tests."""

import asyncio
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

import asyncpg
import pytest

ROOT = Path(__file__).resolve().parents[1]
TEST_DATABASE_NAME = "app_test"


async def reset_test_database(admin_url: str) -> None:
    """Drop and recreate the dedicated test database."""
    connection = await asyncpg.connect(admin_url)

    try:
        await connection.execute(f"DROP DATABASE IF EXISTS {TEST_DATABASE_NAME} WITH (FORCE)")
        await connection.execute(f"CREATE DATABASE {TEST_DATABASE_NAME}")
    finally:
        await connection.close()


def main() -> int:
    admin_url = os.getenv("TEST_DATABASE_ADMIN_URL")
    test_url = os.getenv("TEST_DATABASE_URL")

    if not admin_url or not test_url:
        print("Set TEST_DATABASE_ADMIN_URL and TEST_DATABASE_URL before running.")
        return 1

    admin = urlsplit(admin_url)
    test = urlsplit(test_url)

    if (
        admin.path.lstrip("/") != "postgres"
        or test.path.lstrip("/") != TEST_DATABASE_NAME
        or (admin.hostname, admin.port, admin.username) != (test.hostname, test.port, test.username)
    ):
        print("Unsafe database configuration. Check both test database URLs.")
        return 1

    asyncio.run(reset_test_database(admin_url))

    os.environ["DATABASE_URL"] = test_url
    environment = os.environ.copy()

    migration = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=ROOT,
        env=environment,
        check=False,
    )

    if migration.returncode != 0:
        return migration.returncode

    return int(pytest.main(["-m", "integration"]))


if __name__ == "__main__":
    raise SystemExit(main())
