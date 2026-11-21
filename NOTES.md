# NyayaSetu Implementation Notes

## D03 – PostgreSQL Implementation

### Day 3 – Part 2: Database Migrations

Created two Alembic migrations for the PostgreSQL database.

1. `ac53a5fd3d76` – Create documents and pages.
2. `e27f96b16ce8` – Add GIN index on metadata.

#### Migration Verification

- `python -m alembic history`: Both migrations listed; `e27f96b16ce8` is head.
- `python -m alembic current`: `e27f96b16ce8 (head)`.
- `python -m alembic downgrade -1`: Successfully downgraded from `e27f96b16ce8` to `ac53a5fd3d76`.
- `python -m alembic current` after downgrade: `ac53a5fd3d76`.
- `python -m alembic upgrade head`: Successfully upgraded from `ac53a5fd3d76` to `e27f96b16ce8`.
- Final `python -m alembic current`: `e27f96b16ce8 (head)`.

**Status:** Migration history, downgrade, and upgrade verified successfully.

### Day 3 – Part 3: Idempotent Database Loader

Created `scripts/load_db.py` to load legal scheme records from `data/sample_records.json` into PostgreSQL.

Implemented:
- SHA256 fingerprints for change detection.
- Canonical JSON serialization for consistent fingerprints.
- Insert new records.
- Update records when their fingerprints change.
- Skip unchanged records.
- Transaction-based database operations.

#### Test Results

1. Initial load:

   `records=20 inserted=20 updated=0 unchanged=0`

2. Second load:

   `records=20 inserted=0 updated=0 unchanged=20`

3. After editing record 001:

   `records=20 inserted=0 updated=1 unchanged=19`

**Status:** All three tests passed.

### Day 3 – Part 5: Automated Tests

Implemented API unit tests using a fake repository and fake database session.

#### Unit Test Results

- 16 unit tests passed.
- API health and readiness checks tested.
- Document listing, pagination, search and metadata filters tested.
- Document retrieval and 404 responses tested.
- Invalid query parameters and request IDs tested.

#### Integration Test Results

- 3 PostgreSQL integration tests created.
- Skipped because `TEST_DATABASE_URL` was not configured at that stage.
- Tests cover filtered listing, document retrieval and missing documents.

**Test command:** `python -m pytest -v`

**Result:** 16 passed, 3 skipped.

**Ruff:** All checks passed.

### Day 3 – Part 6: PostgreSQL EXPLAIN

Created `scripts/explain.py` to inspect PostgreSQL query plans for JSONB metadata filters.

#### EXPLAIN Results

Query:

`metadata @> '{"section": "Section 12"}'::jsonb`

Normal planner:
- Seq Scan on documents.
- 1 matching row.
- Execution time: 0.040 ms.

With sequential scans disabled:
- Bitmap Heap Scan.
- Bitmap Index Scan on `ix_documents_metadata_gin`.
- 1 matching row.
- Execution time: 0.107 ms.

#### Why did PostgreSQL choose a Seq Scan?

The documents table contains only 20 records. Reading the entire small table is cheaper than using an index and fetching matching rows.

#### When would PostgreSQL use the GIN index?

As the table grows and JSONB filtering becomes more selective, PostgreSQL may choose the GIN index when its estimated cost is lower.

**Status:** GIN index usage successfully verified.

---

## D04 – Docker, Testing and Quality Automation

### Part 1: Production Dockerfile

Created a multi-stage Dockerfile.

Implemented:
- Python 3.12 slim runtime image.
- uv for dependency installation.
- Separate builder and runtime stages.
- Production dependencies only in the runtime image.
- Non-root application user.
- Uvicorn application startup.

#### Docker Verification

- Image built successfully: `nyayasetu:dev`.
- Runtime user verified as `app` (UID 999).
- Docker build cache verified.

### Part 2: Docker Compose

Created `docker-compose.yml` with the following services:

- `api`: FastAPI application.
- `db`: PostgreSQL 17 with pgvector.
- `redis`: Redis 7.
- `migrate`: Runs Alembic migrations and loads sample data.

Created `docker/initdb/01-create-test-db.sql` to initialize the dedicated `app_test` database.

#### Docker Verification

- `docker compose config`: Successful.
- PostgreSQL health check: Healthy.
- Redis health check: Healthy.
- Migration service: Exited with code 0.
- API health check: Healthy.
- `/health`: Returns `{"status":"ok"}`.
- `/ready`: Returns database readiness successfully.

### Part 3: Unit and Integration Tests

Organized tests into separate directories:

- `tests/unit/test_api.py`
- `tests/integration/test_db_integration.py`
- `tests/conftest.py`

Configured pytest markers:
- `unit`
- `integration`

#### Test Results

- Unit tests: 16 passed.
- Integration tests: 3 passed.
- Total: 19 passed.
- Full test suite: 19 passed.

Integration tests verified:
- Filtered document listing.
- Document retrieval.
- Missing document handling.

### Part 4: Coverage and Quality Automation

Added development dependencies:
- pytest-asyncio
- pytest-cov
- poethepoet

Configured pytest coverage:
- Branch coverage enabled.
- Minimum required coverage: 70%.
- Missing lines displayed in reports.

#### Coverage Results

- Total statements: 239.
- Missed statements: 17.
- Total coverage: 91.32%.
- Required coverage: 70%.
- Result: Passed.

#### Poe Tasks

Configured commands:
- `uv run poe test`
- `uv run poe test-unit`
- `uv run poe test-integration`
- `uv run poe coverage`
- `uv run poe lint`
- `uv run poe format`
- `uv run poe check`

Ruff lint and formatting checks passed.

### Part 5: Makefile and Documentation

Created a Makefile with targets for:
- Installation.
- Unit and integration tests.
- Coverage.
- Linting and formatting.
- Docker Compose startup, shutdown and logs.

GNU Make is not available in the current Windows PowerShell environment. Poe commands are used locally instead.

Updated README.md with:
- Technology stack.
- Local setup instructions.
- Docker Compose instructions.
- Health check commands.
- Testing and coverage commands.
- Code quality commands.
- Makefile usage.

**Day 4 status:** Docker image, Compose services, database migrations, unit tests, integration tests, coverage, linting, formatting and documentation completed successfully.

---

## D05 – CI/CD and Live Deployment

### Live Deployment

- Live URL: https://nyayasetu-9ck6.onrender.com
- API documentation: https://nyayasetu-9ck6.onrender.com/docs
- Health endpoint: https://nyayasetu-9ck6.onrender.com/health
- Readiness endpoint: https://nyayasetu-9ck6.onrender.com/ready
- CI workflow: https://github.com/enamul-hasan-h/prince28-law06-nyayasetu/actions/workflows/ci.yml
- CD workflow: https://github.com/enamul-hasan-h/prince28-law06-nyayasetu/actions/workflows/cd.yml

### CI/CD Verification

- CI pipeline: Lint, tests and Docker image build.
- Main branch protection: Enabled.
- CD pipeline: Database migrations, Render deployment and live smoke test.
- Latest live health check: HTTP 200.
- Latest observed deployed Git SHA: `3ab59f65b0e559f15cbf80635a6a7fd79e96e461`
- Deployment lead time: Not recorded; requires timestamp verification.

### Rollback Drill

- Rolled back to SHA: `61349462d3f0f81802f202150a8121cbedcf98fd` – Successful.
- Rollback start time: Not recorded.
- Smoke test: Passed.
- Rolled forward to SHA: `3ab59f65b0e559f15cbf80635a6a7fd79e96e461` – Successful.
- Roll-forward duration: Not recorded.

### Secrets Management

- Neon database URL: GitHub Secret `DATABASE_URL` and Render environment.
- Render deploy hook: GitHub Secret `RENDER_DEPLOY_HOOK`.
- Secret values are not stored in Git or Docker images.

### Monitoring

- UptimeRobot monitor: NyayaSetu Health.
- Endpoint monitored: `/health`.
- Check interval: 5 minutes.
- Email alerts configured.
- Status: Direct health endpoint verified HTTP 200; UptimeRobot alert delivery remains unverified.

### First-Request Performance

Render Free service may take time to wake after inactivity.
