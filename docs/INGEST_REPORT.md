# Ingestion report

<!-- generated:start -->
_Generated 27 Nov 2026 19:37 from the database._

| What | Count |
|---|---|
| Documents in the database | 32 |
| Pages | 1475 |
| Tokens of text (characters Ã· 4) | 593,309 |
| Files the parser gave up on | 20 |
| Documents with an extracted record | 32 |
| Documents whose extraction failed | 0 |

| Queue | Count |
|---|---|
| Ingest jobs started | 7 |
| Items finished (done or skipped) | 32 |
| Items that needed more than one try | 9 |
| Items in the dead-letter list | 21 |

Model calls for extraction: 55 Â· tokens in 62,034 Â· tokens out 20,871 Â· cost at list price Rs 0.78

Last job `959a3bf17150425c938e36e9b1832b6c`: 15 requested, 14 ok, 1 failed, 5.1 minutes.

Dead-letter list by stage: parse 20, gave up 1
<!-- generated:end -->

## What I learnt

1. Downloaded PDF page counts and successfully processed database pages measure different stages of ingestion.
2. The parser identified 20 PDFs without a text layer, demonstrating why scanned documents may require OCR.
3. The worker uses retries and a dead-letter list to prevent unsuccessful ingestion items from being silently lost.
