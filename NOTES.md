
## Day 3 – Part 3: Idempotent Database Loader

Created `scripts/load_db.py` to load legal scheme records from `data/sample_records.json` into PostgreSQL.

Implemented:
- SHA256 fingerprints for change detection.
- Canonical JSON serialization for consistent fingerprints.
- Insert new records.
- Update records when their fingerprints change.
- Skip unchanged records.
- Transaction-based database operations.

### Test Results

1. Initial load:
   `records=20 inserted=20 updated=0 unchanged=0`

2. Second load:
   `records=20 inserted=0 updated=0 unchanged=20`

3. After editing record 001:
   `records=20 inserted=0 updated=1 unchanged=19`

**Status:** All three tests passed.

## Day 3 - Part 5: Automated Tests

Implemented API unit tests using a fake repository and fake database session.

### Unit Test Results

- 16 unit tests passed.
- API health and readiness checks tested.
- Document listing, pagination, search and metadata filters tested.
- Document retrieval and 404 responses tested.
- Invalid query parameters and request IDs tested.

### Integration Test Results

- 3 PostgreSQL integration tests created.
- Skipped because TEST_DATABASE_URL is not configured.
- Tests cover filtered listing, document retrieval and missing documents.

**Test command:** `python -m pytest -v`

**Result:** 16 passed, 3 skipped.

**Ruff:** All checks passed.

## Day 3 - Part 6: PostgreSQL EXPLAIN

Created `scripts/explain.py` to inspect PostgreSQL query plans for JSONB metadata filters.

### EXPLAIN Results

Query:
`metadata @> '{"section": "Section 12"}'::jsonb`

Normal planner:
- Seq Scan on documents
- 1 matching row
- Execution time: 0.040 ms

With sequential scans disabled:
- Bitmap Heap Scan
- Bitmap Index Scan on ix_documents_metadata_gin
- 1 matching row
- Execution time: 0.107 ms

### Why did PostgreSQL choose a Seq Scan?

The documents table contains only 20 records. Reading the entire small table is cheaper than using an index and fetching matching rows.

### When would PostgreSQL use the GIN index?

As the table grows and JSONB filtering becomes more selective, PostgreSQL may choose the GIN index when its estimated cost is lower.

**Status:** GIN index usage successfully verified.
