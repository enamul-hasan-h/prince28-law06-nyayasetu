
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
