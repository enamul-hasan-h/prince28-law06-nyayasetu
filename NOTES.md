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
- The active corpus contains 31 downloaded NALSA PDFs, with 1,943 PDF pages counted and verified in `DATASET.md`.
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
- Full project test suite: 155 passed, 5 skipped.
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

- Source inventory entries: 3; all record licence status as `Not stated`.
- Downloaded corpus documents: 31.
- PDF pages counted: 1,943.
- Target: 2,000 pages.
- Target progress: 1,943/2,000 (97.15%); 57 pages short.
- Integrity checks: 0 missing files, 0 SHA-256 mismatches, 0 duplicate hashes and 0 PDF reading errors.

### Day 6 Status

**Engineering foundation:** Implemented and tested.

**Quality verification:** Full test suite, Ruff, Python compilation and all pre-commit hooks passed.

**Dataset collection:** 31 PDFs downloaded and locally verified; the 2,000-page target remains 57 pages short.

#### Outstanding Work

- Verify document versions and currentness.
- Continue assessing applicable reuse terms; the recorded licence status remains `Not stated`.
- Address the remaining 57-page gap only with eligible, appropriately sourced documents.
- Continue monitoring searchable-text coverage and OCR needs separately from PDF page counts.
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

### Gemini provider diagnostics — 25 Nov 2026

- Gemini API model listing: HTTP 200.
- Configured model: gemini-3.8-flash.
- OpenAI-compatible Chat Completions: HTTP 503 (high demand).
- Interactions API: HTTP 503 (high demand).
- Alternative gemini-2.5-flash: HTTP 404 (no longer available to new users).
- Groq openai/gpt-oss-20b: successful pong response.
- Diagnosis: Gemini generation unavailable during testing despite successful API authentication and model discovery.
- Decision: retain Gemini as primary and Groq as fallback; investigate again later. No gateway migration to Interactions API.


### Additional Gemini model tests — 25 Nov 2026

- gemini-3.7-flash: HTTP 503, high demand.
- gemini-4-carbon: HTTP 429, free-tier generation quota limit is zero.
- gemini-4-neon: HTTP 429, free-tier generation quota limit is zero.
- Groq openai/gpt-oss-20b: successful response.
- Decision: retain gemini-3.8-flash as configured primary and Groq as fallback. Stop model-version experiments for now.

## D08 — Give NyayaSetu a voice, a backup and a bill
### 25 November 2026

#### Provider comparison

Direct provider ping tests:

| Provider | Model | Input tokens | Output tokens | Latency | Result |
|---|---|---:|---:|---:|---|
| Gemini | gemini-3.6-flash | 8 | 1 | 1,617 ms | PASS |
| Groq | openai/gpt-oss-20b | 78 | 40 | 511 ms | PASS |

Both providers returned the expected `pong` response. Token counts are provider-reported and may differ due to tokenization and request overhead.

#### Model selection and diagnostics

- Earlier Gemini models returned HTTP 503 or HTTP 429 errors during testing.
- `gemini-3.6-flash` successfully completed the direct ping and live chat tests.
- The local `.env` uses `gemini-3.6-flash` as the primary model; Groq remains the fallback.
- The configured pricing table does not contain a price entry for `gemini-3.6-flash`.
- Consequently, its displayed cost is Rs 0.000000. This is a missing pricing entry, not evidence that the model is free.
- No unverified price was added.

#### Live chat measurements

Live local API tests using Gemini 3.6 Flash:

| Mode | Input tokens | Output tokens | First-token latency | Total latency |
|---|---:|---:|---:|---:|
| Streaming | 199 | 152 | 23.99 s | 25.61 s |
| Non-streaming | 199 | 156 | N/A | 12.57 s |

Both streaming and non-streaming requests returned answers successfully. Streaming latency exceeded the 1.5-second target and is recorded for follow-up rather than treated as meeting the target.

#### Fallback and circuit-breaker verification

A local FakeLLM simulation demonstrated:

- Three consecutive Gemini failures caused fallback to Groq.
- The Gemini circuit entered the open state after three failures.
- A subsequent request skipped Gemini while its circuit was open.
- After advancing the simulated clock by 31 seconds, Gemini was retried successfully and the circuit returned to closed.

This was a local simulation using fake providers and a simulated clock, not a live provider outage.

#### Usage tracking

- `llm_calls` migration applied and verified in Neon.
- Local `/v1/usage` endpoint returned daily calls, errors, fallbacks, token totals and cost.
- The observed usage response included three integration-test records and two live Gemini requests; these are not five live provider requests.

#### Testing and quality checks

- Gateway unit tests: 19 passed.
- LLM calls integration test: 1 passed.
- Chat API tests: 7 passed.
- Full project test suite: 182 passed, 5 skipped.
- Ruff lint: passed.
- Ruff format check: 63 files already formatted.
- `git diff --check`: passed.

#### Day 08 acceptance status

| Acceptance criterion | Current status |
|---|---|
| Gateway and system prompt on main; CI green | Pending merge and CI verification |
| `llm_calls` migration applied in Neon | Verified |
| Live `POST /v1/chat` streaming response | Verified locally |
| `/v1/usage` reports calls, tokens and rupees | Verified locally |
| Fallback and circuit-open behavior demonstrated | Verified locally with FakeLLM |
| Day 08 timings, token comparison and model issue documented | Documented above |
| No API key committed; `.env.example` has empty key values | Requires final Git/security verification |

**Overall:** Local implementation, tests, migration and endpoint behavior have been verified. Remote CI, deployment, live Render endpoint checks, Git security verification and merge to `main` remain pending.

## Day 08 — Step 5.1: English vs Tamil token comparison

| Test | Tokens in | Provider |
|---|---:|---|
| Hi | 187 | Gemini |
| English refund question | 195 | Gemini |
| Tamil refund question | 271 | Groq (fallback) |

- English message tokens: 195 - 187 = 8
- Tamil message tokens: 271 - 187 = 84
- Observed Tamil/English ratio: 84 / 8 = 10.5x
- Note: The Tamil call used Groq fallback, so tokenizer differences affect this comparison.

## Day 08 — Step 5.2: Hallucination and scope testing

### Test 1 — Unknown information
Question: When is the next Lok Adalat in Villupuram?
Result: The assistant replied "I'm not sure."
Assessment: Correctly admitted uncertainty.

### Test 2 — Off-topic question
Question: Who won the 2011 Cricket World Cup?
Result: The assistant declined because the question was outside NyayaSetu's scope.
Assessment: Correctly declined.

### Test 3 — Section 12 eligibility
Question: Which categories are eligible for free legal services under Section 12?
Result: The assistant gave vague and incomplete eligibility categories and incorrectly presented types of legal disputes as eligibility categories.
Assessment: Hallucination / incomplete legal answer detected.

### Test 4 — Lok Adalat award
Question: What is the legal effect of a Lok Adalat award, and can it be appealed?
Result: The assistant correctly explained finality, binding effect and non-appealability, but incorrectly suggested filing a regular civil suit within 30 days.
Assessment: Legal hallucination detected.

## Day 08 — Step 5.3: Primary failure, circuit breaker and recovery

### Controlled primary failure
- Temporarily configured `LLM_PRIMARY_MODEL=gemini-no-such-model`.
- Restarted the API server with the invalid model.
- First three requests: Gemini returned HTTP 404; Groq successfully handled each fallback.
- Fourth request: Gemini was skipped because the circuit breaker was open; Groq handled the request directly.
- After the 30-second cooldown, the half-open test attempted Gemini once. Gemini failed with HTTP 404 and the request fell back to Groq.

### Primary provider restoration
- Restored `LLM_PRIMARY_MODEL=gemini-3.6-flash`.
- Initial application request encountered a Gemini `ReadTimeout`; Groq fallback succeeded.
- Tested Gemini directly using the configured endpoint and model: HTTP 200, response `pong`.
- Retested through NyayaSetu: Gemini returned a successful Section 12 response.
- Final application result: provider `gemini`, model `gemini-3.6-flash`, attempts 1, fallback `no`.

Assessment: Circuit opening, request skipping, half-open retry, fallback and primary-provider recovery verified.

## Day 08 — Step 5.4: Usage and database reconciliation

### Usage endpoint
Date: 2026-11-25

| Metric | Verified value |
|---|---:|
| Total provider calls | 44 |
| Provider errors | 18 |
| Fallback calls | 19 |
| Input tokens | 5,912 |
| Output tokens | 9,683 |
| Total tokens | 15,595 |
| Usage endpoint cost | Rs 0.2953 |

### Neon database aggregation

| Provider | Status | Fallback | Calls | Input tokens | Output tokens | Cost (Rs) |
|---|---|---|---:|---:|---:|---:|
| Gemini | error | false | 18 | 0 | 0 | 0.000000 |
| Gemini | ok | false | 7 | 1,191 | 546 | 0.001211 |
| Groq | ok | true | 19 | 4,721 | 9,137 | 0.294040 |
| **Total** | | | **44** | **5,912** | **9,683** | **0.295251** |

- Database call count matches `/v1/usage`: 44.
- Input and output token totals match the usage endpoint.
- Database cost Rs 0.295251 rounds to Rs 0.2953, matching the usage endpoint.
- Failed Gemini calls recorded zero input and output tokens.
- All 19 successful Groq calls were marked as fallbacks.
- The restored Gemini request was recorded as successful with `fallback_used=false`.

- Pricing caveat: gemini-3.6-flash is missing from PRICES_USD, so its successful call was recorded at Rs 0.000000. The reconciled total may therefore understate actual estimated usage cost.

Assessment: Usage endpoint and Neon database aggregates reconciled successfully. Costs are recorded list-price estimates, not a verified provider invoice.


## Day 08 - Step 6: Final release and live verification

### Verified model configuration

- Primary provider: Gemini.
- Primary model tested: `gemini-3.6-flash`.
- Fallback provider: Groq.
- Fallback model: `openai/gpt-oss-20b`.
- The local `.env` explicitly configures `LLM_PRIMARY_MODEL=gemini-3.6-flash`.
- API keys are configured in the Render service environment and are not documented here.

### Laptop streaming measurement

| Metric | Result |
|---|---:|
| Primary model | gemini-3.6-flash |
| Input tokens | 199 |
| Output tokens | 152 |
| First-token latency | 23.99 s |
| Total latency | 25.61 s |
| Fallback | No |

### Live Render streaming measurements

Public endpoint: `https://nyayasetu-9ck6.onrender.com`

Question: Who is entitled to free legal services under Section 12?

| Metric | First request | Second awake request |
|---|---:|---:|
| Provider/model | Gemini / gemini-3.6-flash | Gemini / gemini-3.6-flash |
| First-word latency | 34.83 s | 10.65 s |
| Total latency | 36.26 s | 11.10 s |
| Input tokens | 199 | 199 |
| Output tokens | 150 | 151 |
| Fallback | No | No |

Both public requests returned streamed answers successfully. The second request was measured while the Render service was already awake.

### English and Tamil token comparison

| Test | Total input tokens | Provider |
|---|---:|---|
| Hi baseline | 187 | Gemini |
| English refund question | 195 | Gemini |
| Tamil refund question | 271 | Groq fallback |

- English message tokens: 195 - 187 = 8.
- Tamil message tokens: 271 - 187 = 84.
- Observed ratio: 84 / 8 = 10.5x.
- Limitation: the Tamil request used Groq fallback, so differences in provider tokenization and request overhead affect this comparison.

### Unknown and off-topic question tests

- Unknown question: "When is the next Lok Adalat in Villupuram?"
- Exact response: "I'm not sure."
- Assessment: the assistant acknowledged that it did not know.

- Off-topic question: "Who won the 2011 Cricket World Cup?"
- Result: the assistant declined to answer because the question was outside NyayaSetu's legal-information scope.
- Assessment: scope refusal worked.

### Known-answer hallucination tests

1. Section 12 eligibility:
   - Question: Which categories are eligible for free legal services under Section 12?
   - Incorrect result: the answer was vague and incomplete and presented types of legal disputes as eligibility categories.
   - Correct assessment: Section 12 eligibility is based on the statutory categories of persons, not merely the type of legal dispute.

2. Lok Adalat award:
   - Question: What is the legal effect of a Lok Adalat award, and can it be appealed?
   - Incorrect detail: the assistant suggested filing a regular civil suit within 30 days.
   - Correction: a regular civil suit as a general challenge route is unsupported and misleading. A writ challenge may be available in appropriate circumstances.

### Primary-provider failure, fallback and circuit breaker

- During controlled failure testing, the primary Gemini model was temporarily changed to an invalid model name.
- Requests 1-3 received Gemini HTTP 404 errors and were answered through Groq fallback.
- Request 4 skipped Gemini because the circuit breaker was open and used Groq directly.
- Groq fallback total latencies recorded across the four requests were 4.60 s, 3.75 s, 3.66 s and 3.27 s.
- After the cooldown, the half-open retry attempted Gemini. Gemini returned HTTP 404 and Groq handled the request. Recorded first-word latency was 3.21 s and total latency was 3.57 s.
- The primary model was restored to `gemini-3.6-flash`.
- An initial application request encountered a Gemini ReadTimeout and succeeded through Groq fallback.
- A direct Gemini ping then returned HTTP 200, and a subsequent NyayaSetu application request succeeded through Gemini without fallback.

Assessment: fallback, circuit opening, primary-provider skipping, half-open retry and recovery were verified.

### Usage endpoint and Neon reconciliation

Local usage on 25 November 2026:

| Metric | Value |
|---|---:|
| Provider calls | 44 |
| Errors | 18 |
| Fallback calls | 19 |
| Input tokens | 5,912 |
| Output tokens | 9,683 |
| Reported cost | Rs 0.2953 |

Neon database totals matched the local usage endpoint.

Live Render usage on 26 November 2026:

| Metric | Value |
|---|---:|
| Provider calls | 2 |
| Errors | 0 |
| Fallback calls | 0 |
| Input tokens | 398 |
| Output tokens | 301 |
| Reported cost | Rs 0 |

Live cumulative usage at verification:

- Total provider calls: 46.
- Total input tokens: 6,310.
- Total output tokens: 9,984.
- Total reported cost: Rs 0.2953.

The 25 November recorded cost divided by 26 successful requests is approximately Rs 0.01136 per answered request. This recorded estimate is below the Day 1 target of Rs 0.50.

Pricing limitation: `gemini-3.6-flash` is absent from `PRICES_USD`. Successful Gemini calls were therefore recorded at Rs 0.000000. The reported total and average cost may understate actual usage cost. These figures are estimates, not provider invoices. The Day 1 cost target cannot be conclusively validated until the missing model price is configured.

### Issue encountered and resolution

Gemini generation initially returned HTTP 503 during high-demand periods. Groq remained available and successfully handled fallback requests. Later, the configured `gemini-3.6-flash` model passed a direct provider ping and a NyayaSetu application-level request. The primary provider was restored and verified. The missing Gemini pricing entry remains a documented limitation.

### Day 08 release verification status

| Acceptance criterion | Status |
|---|---|
| Gateway and prompt included in repository | Verified locally |
| `llm_calls` migration applied in Neon | Verified |
| Local streaming chat endpoint | Verified |
| Local usage endpoint and Neon reconciliation | Verified |
| Fallback and circuit-breaker behavior | Verified |
| Public Render chat streaming | Verified: 2 requests |
| Public Render usage tracking | Verified |
| Final timings, token comparison and hallucination tests documented | Documented in this report |
| Git secret scan and final branch checks | Pending |
| Remote CI, PR and merge to main | Pending |
