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

---

## D06 – Corpus Collection Foundation

### Part 1: Source Research and Permission Review

Created a provisional inventory of 10 NALSA legal-service schemes.

Reviewed official NALSA source pages and website reuse policies.

Research findings:
- Three official NALSA page references recorded in `data/sources.csv`.
- All three sources remain marked `Permission pending`.
- Reuse permission must be clarified before automated collection or reproduction.
- Research reference PDFs are kept outside the active corpus and excluded from Git.
- No legal documents have been approved for active corpus inclusion.

### Part 2: URL, Git Repository and Manual Downloader

Implemented the corpus collection foundation in:
- `src/nyayasetu/ingest/fetch.py`
- `scripts/fetch.py`

Implemented:
- Robots.txt checks with fail-closed handling for relevant network failures.
- Per-host request delays.
- Configurable asynchronous downloads.
- Concurrency limits capped at four.
- Permission confirmation safeguards.
- Manifest-based resume behaviour.
- SHA-256 integrity metadata.
- Git repository collection with path and extension filters.
- Manual local-file collection with supported file-type validation.
- Permission and licence validation for manual collection.
- Duplicate/resume checks using manifest records.
- Protection against overwriting unrecorded destination files.
- Temporary `.part` file cleanup.

The CLI now provides four collection modes:
- `urls`: Collect approved URLs.
- `repo`: Collect eligible files from a Git repository.
- `manual`: Collect an explicitly supplied local document.
- `sitemap`: Discover candidate URLs without downloading content.

### Part 3: Sitemap Discovery

Created `src/nyayasetu/ingest/sitemap.py`.

Implemented:
- Sitemap URL validation.
- Sitemap index discovery.
- Robots.txt permission checks.
- Sitemap and candidate URL deduplication.
- Sitemap count and candidate limits.
- Discovery-only CSV output.
- Permission-pending status for discovered candidates.

Sitemap discovery does not download document content.

### Part 4: Offline Testing

Created and extended unit tests for downloader, repository CLI, manual collection CLI and sitemap functionality.

#### Verification

- Fetch module tests: 19 passed.
- Sitemap tests: 7 passed.
- CLI tests: 17 passed.
- Full project test suite: 60 passed, 3 skipped.
- Ruff lint: All checks passed.
- Python compilation checks: Passed.
- Pre-commit hooks: All 9 passed.

The manual collection CLI tests cover:
- Successful local-file collection and manifest metadata.
- SHA-256 metadata recording.
- Resume behaviour when a file is already recorded.
- Refusal without permission confirmation.
- Refusal when permission is pending.
- Missing-file handling.
- Unsupported file extension handling.
- Protection against overwriting existing unrecorded files.
- Cleanup of temporary `.part` files.

A local synthetic Git repository verified:
- Matching file downloads.
- Extension filtering.
- Manifest metadata and SHA-256 values.
- Resume behaviour on a second run.
- No leftover partial files.

Synthetic test data was removed after verification.

### Part 5: Dataset Reporting and Capacity Assessment

Created `scripts/dataset_report.py` and generated `DATASET.md`.

The report measures:
- Source inventory and permission status.
- Manifest records and collection status.
- Files present and verified.
- PDF page counts.
- SHA-256 mismatches and duplicate hashes.
- Missing files and PDF reading errors.

Created `docs/CAPACITY.md` to document collection throughput, storage considerations, processing capacity, constraints and the 2,000-page target.

#### Current Measured Dataset Baseline

- Source inventory entries: 3.
- Permission-pending sources: 3.
- Downloaded corpus documents: 0.
- PDF pages collected: 0.
- Target: 2,000 pages.
- Target progress: 0%.

### Day 6 Status

**Engineering foundation:** Implemented and tested.

**Quality verification:** Full test suite, Ruff, Python compilation and all pre-commit hooks passed.

**Dataset collection:** Not completed; source reuse permission and document verification remain pending.

#### Outstanding Work

- Obtain written reuse permissions.
- Complete the approved direct-document source inventory.
- Collect only authorised documents.
- Work toward the 2,000-page target.
- Verify document versions, readability and corpus integrity.
- Complete final Git review, commit, pull request, merge and CI/CD verification.

The corpus target is not marked complete. Public accessibility and sitemap discovery do not constitute reuse permission.

## D07 – Document Parsing and Storage

### Part 1: Parser Implementation

Created `src/nyayasetu/ingest/parse.py`.

Implemented:
- PDF text extraction using PyMuPDF.
- Alternative PDF extraction using pypdf.
- Optional OCR fallback using Tesseract.
- HTML content extraction using Trafilatura.
- Text, Markdown, RST and AsciiDoc parsing.
- CSV, JSON, YAML and XML data-file handling.
- Text cleaning and repeated-line removal.
- Page splitting and page-number preservation.
- Heading detection and section-path tracking.
- Markdown table extraction where supported.

### Part 2: Database Storage

Updated `src/nyayasetu/db/models.py`.

Added:
- `Page.headings` JSONB field for section information.
- `ParseFailure` model for tracking parsing failures.
- Unique failure paths and indexed failure reasons.
- Retry-attempt tracking.

Created migration:
`f236359a39e6_add_page_headings_and_parse_failures.py`

Applied successfully using Alembic.

Created `src/nyayasetu/ingest/store.py`.

Implemented:
- Parsed document storage.
- Page-by-page database storage.
- SHA-256 fingerprinting.
- Existing document update handling.
- Parse failure storage and retry tracking.
- Removal of resolved failures after successful parsing.

### Part 3: Corpus Parsing CLI

Created `scripts/parse_corpus.py`.

Implemented:
- Manifest-based downloaded document discovery.
- Safe project-relative path validation.
- SHA-256 integrity verification.
- Parsing and database storage.
- Dead-letter failure recording.
- `--limit` processing option.
- `--retry-failed` retry option.
- Optional `--ocr` fallback.

### Part 4: Parser Comparison

Created `scripts/compare_parsers.py`.

Implemented:
- Discovery of the largest PDF files.
- PyMuPDF and pypdf comparison.
- Extracted page, character, heading and table counts.
- Parser error reporting.

Actual comparison remains pending because no approved PDF documents are available.

### Part 5: Verification

- Parser unit tests: 9 passed.
- Complete unit test suite: 36 passed.
- Ruff check for parser CLI: Passed.
- Ruff check for comparison script: Passed.
- Parser CLI help: Passed.
- Empty-corpus handling: Passed.
- Parser comparison CLI: Passed with zero available PDFs.

### D07 Status

**Parser implementation:** Completed.

**Database migration:** Applied.

**Unit testing:** Passed.

**Real corpus parsing:** Pending authorised documents.

**Parser comparison:** Implemented; real-document comparison pending.

**OCR verification:** Pending scanned PDF availability and Tesseract verification.

### Dataset Limitation

- Approved source documents: 0.
- Downloaded corpus documents: 0.
- PDFs available for comparison: 0.

No synthetic test fixtures are counted as collected legal corpus documents. Collection remains dependent on written reuse permission.
