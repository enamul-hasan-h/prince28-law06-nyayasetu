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
- Three official NALSA page references are recorded in `data/sources.csv`.
- All three source inventory entries currently record their licence status as `Not stated`.
- Evaluator approval for academic-project use of the collected NALSA material is recorded in the project notes. This approval is not an open reuse licence or unrestricted redistribution permission.
- The active corpus contains 31 downloaded NALSA PDFs, with 1,943 readable pages verified in `DATASET.md`.
- Research reference PDFs remain separate from the active corpus and are excluded from corpus totals and Git.
- Source-specific restrictions and third-party rights must continue to be respected.

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

Updated `src/nyayasetu/db/models.py` and created the migration:

`f236359a39e6_add_page_headings_and_parse_failures.py`

Added:
- `pages.headings` as a JSONB field.
- `parse_failures` for recording parsing errors.
- Failure reason, detail, attempt count and timestamps.
- Retry tracking and removal of resolved failures after successful parsing.

**Neon verification:**
- Alembic version: `f236359a39e6`.
- `pages.headings` exists and is non-nullable.
- `parse_failures` table and its expected columns exist.

### Part 3: Corpus Collection and Parsing

The academic project corpus was collected from official NALSA source pages after the project evaluator approved its use for this academic project. This approval is not recorded as an open reuse licence; source licence values remain `Not stated`.

Collected 31 PDF documents.

**Download and integrity verification:**
- Candidate PDF URLs: 31.
- Successfully downloaded: 31.
- Blocked or failed downloads: 0.
- Verified files: 31.
- Missing files: 0.
- SHA-256 mismatches: 0.
- Unsafe manifest paths: 0.

Created `scripts/parse_corpus.py`.

Implemented:
- Manifest-based document discovery.
- Safe project-relative path validation.
- SHA-256 integrity verification.
- Parsing and database storage.
- Failure recording and retry handling.
- `--limit`, `--retry-failed` and optional `--ocr` arguments.

**Initial parsing:**
- Total processed: 31.
- Parsed: 12.
- Failed: 19.
- All 19 initial failures were classified as `no_text_layer`.

Installed and verified Tesseract OCR (English language support). Retried the failed documents using:

`uv run python .\scripts\parse_corpus.py --retry-failed --ocr eng`

Retry result:
- Retried: 19.
- Parsed successfully: 19.
- Failed: 0.

### Part 4: Neon Corpus Verification

Verified the parsed NALSA corpus directly in Neon.

| Measurement | Verified result |
|---|---:|
| Parsed documents | 31 |
| Stored pages | 1,943 |
| Documents with pages | 31 |
| Pages containing text | 1,839 |
| Pages with heading data | 1,306 |
| Remaining NALSA parse failures | 0 |

A per-document SQL check confirmed that all 31 documents have the expected number of stored pages. Page numbering starts at 1 and reaches the expected final page for every document.

Real page records were inspected in the SQL editor, including page text and heading JSON.

Some OCR-extracted pages have empty heading arrays. Heading paths were confirmed in text-based PyMuPDF records; OCR heading detection is not assumed where no heading was extracted.

The empty-page query returned 104 records. Two pages were visually checked against their PDFs and confirmed to be blank. The remaining empty-page records have not all been individually classified. Empty pages are retained to preserve original page numbering.

### Part 5: Parser Comparison

Created `scripts/compare_parsers.py`.

Implemented:
- Selection of the largest available PDFs.
- PyMuPDF and pypdf extraction comparison.
- Page, character, heading and table counts.
- Error reporting.
- Markdown report generation.

Compared the 10 largest corpus PDFs:

| PDF | PyMuPDF | pypdf | Manual verdict |
|---|---|---|---|
| `1756544763-ddfff673.pdf` | no text layer | no text layer | Inconclusive - OCR required |
| `1756544777-fea03c6b.pdf` | no text layer | no text layer | Inconclusive - OCR required |
| `202505142178608-0e5ae2e9.pdf` | no text layer | no text layer | Inconclusive - OCR required |
| `20250409258379504-8e8276b9.pdf` | no text layer | no text layer | Inconclusive - OCR required |
| `20250408408064338-3434fcd0.pdf` | no text layer | no text layer | Inconclusive - OCR required |
| `2025040925439249-c7a90332.pdf` | 131 pages; 146,962 characters; 309 headings; 8 tables | 131 pages; 144,200 characters; 0 headings; 0 tables | PyMuPDF |
| `202504081834821576-35eb6f80.pdf` | no text layer | no text layer | Inconclusive - OCR required |
| `202504081540884465-660db624.pdf` | no text layer | no text layer | Inconclusive - OCR required |
| `2025040866630099-49d08f01.pdf` | no text layer | no text layer | Inconclusive - OCR required |
| `202504091237499824-db27697c.pdf` | 176 pages; 330,842 characters; 331 headings; 27 tables | 176 pages; 328,438 characters; 0 headings; 0 tables | PyMuPDF |

**Comparison verdict:**
- Eight scanned PDFs: neither native parser could extract a usable text layer. OCR is required; these results do not establish a winner.
- Two text-based PDFs: PyMuPDF extracted more text and preserved heading/table structure better than pypdf in the measured results and inspected first-page samples.
- Preferred native PDF parser: PyMuPDF.
- OCR remains the fallback for scanned PDFs.

The comparison report is generated at `data/parser_comparison.md`.

### Part 6: Testing and Quality Verification

The parser and comparison implementation were tested.

Latest recorded project checks:
- Ruff lint: passed.
- Ruff format check: 52 files already formatted.
- Full test suite: 154 passed, 5 skipped.
- Parser comparison tests: included in the full test suite.
- Parser CLI and comparison CLI: executed successfully.

The optional PySocks dependency warning from urllib3 does not indicate a parser test failure. The PyMuPDF fontTools warning was also observed during comparison; no parser failure was attributed to it.

### D07 Acceptance Criteria Status

| Acceptance criterion | Status |
|---|---|
| Parser implementation merged into `main`; CI green | Verified |
| Migration adds `parse_failures` and `pages.headings`; applied in Neon | Verified |
| Entire 31-document corpus represented in `documents` or `parse_failures` | Verified: 31 documents, 0 remaining failures |
| Page numbers and heading data checked in real SQL records | Verified by SQL spot checks; OCR heading extraction has limitations |
| 10-file parser comparison table and verdicts documented | Documented above |
| Failures recorded by reason and at least one fixed | Verified: 19 `no_text_layer` failures resolved through OCR |

**Overall:** The Day 07 parser, storage migration, corpus processing, OCR recovery and comparison work have been implemented and verified against the recorded results. The OCR heading limitation and unclassified empty-page records remain documented rather than being treated as fully verified.
