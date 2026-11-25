# NyayaSetu Corpus Capacity Assessment

## 1. Current dataset baseline

The current dataset report was generated using:

`uv run python scripts/dataset_report.py --full-pages 2000`

The figures below are based on the regenerated `DATASET.md`.

| Metric | Current value |
|---|---:|
| Source inventory entries | 3 |
| Sources marked Permission pending | 0 |
| Sources with licence status Not stated | 3 |
| Downloaded manifest records | 31 |
| Files verified on disk | 31 |
| PDF files under data/raw/ | 31 |
| Readable PDF pages | 1,943 |
| Target PDF pages | 2,000 |
| Target completion | 97.15% |
| Pages remaining | 57 |

The 31 downloaded PDFs passed the reported integrity checks:
- Missing files: 0
- SHA-256 mismatches: 0
- Duplicate SHA-256 values: 0
- PDF page-reading errors: 0

The project notes record evaluator approval for academic-project use of the collected NALSA material. This approval must not be represented as an open reuse licence. The source inventory currently records the licence status as `Not stated`.

## 2. Can the current corpus support the target?

The current corpus contains 31 verified PDF files and 1,943 readable pages.

It has not yet reached the 2,000-page target. A further 57 readable pages are required.

Only verified PDF pages should contribute to this target. Sitemap candidates, public pages without reuse approval, research reference PDFs outside `data/raw/`, and synthetic test fixtures must not be counted.

## 3. Storage capacity

The current dataset report verifies the presence of 31 files, but does not provide a complete storage-capacity assessment.

Further measurements are required for:
- Total downloaded file size.
- Average document size.
- Storage used by extracted text.
- Storage used by derived data and processing artefacts.

These measurements should be recorded before estimating final production storage requirements.

## 4. Collection throughput

The downloader supports:
- Asynchronous URL downloads.
- Configurable concurrency, capped at four.
- Per-host request delays.
- Robots.txt checks.
- Manifest-based resume behaviour.
- SHA-256 integrity metadata.
- Git repository collection.
- Sitemap discovery without downloading document content.

The current corpus contains 31 downloaded PDF records. However, a formal production throughput benchmark has not yet been completed.

Synthetic local tests verify downloader behaviour but are not representative of external source performance.

## 5. Processing capacity

The project includes `pypdf` for PDF page inspection.

The regenerated dataset report confirms that all 31 referenced PDFs were readable for page counting, with no reported page-reading errors.

However, extraction throughput, OCR performance, and processing cost have not yet been benchmarked against a representative corpus.

Scanned PDFs may require OCR. Such documents should be identified and measured separately from text-based PDFs.

## 6. Main constraints and risks

1. **Reuse permission:** Evaluator approval for academic-project use is recorded in project notes. The source inventory still records the licence status as `Not stated`. This does not establish an open reuse licence or unrestricted redistribution rights.
2. **Source coverage:** The source inventory contains three NALSA entries, while the manifest records 31 downloaded PDFs. Direct-document provenance and source-specific restrictions must remain traceable.
3. **Document quality:** Page readability has been verified, but scanned-document quality and OCR requirements need separate assessment.
4. **Version control:** Legal documents may be amended or superseded. Publication dates and currentness must be verified.
5. **Storage:** Final capacity requirements depend on actual document sizes and derived artefacts.
6. **Collection policy:** Robots.txt, website terms, evaluator approval scope, and source-specific restrictions must be respected.

## 7. Conditions for reaching 2,000 pages

- Maintain evidence of the evaluator approval and its academic-project scope.
- Clarify source-specific reuse restrictions and third-party rights.
- Verify the current version and direct document URL.
- Maintain an approved source inventory with permission evidence or accurately stated licence status.
- Collect only documents within the approved project scope.
- Verify file hashes and PDF readability.
- Measure actual page count and storage.
- Document unreadable files, OCR requirements, and exclusions.
- Collect and verify at least 57 additional eligible pages.
- Regenerate `DATASET.md` after each approved collection batch.

## 8. Conclusion

NyayaSetu has a functioning collection foundation, including URL downloads, Git repository collection, and sitemap discovery workflows.

The current dataset contains 31 downloaded PDFs with 1,943 readable pages. All 31 files passed the reported file-integrity checks, with no missing files, hash mismatches, duplicate hashes, or PDF page-reading errors.

The corpus has reached 97.15% of the 2,000-page target. Another 57 verified pages are required.

The dataset report and project notes must continue to distinguish evaluator approval for academic-project use from an open reuse licence. Storage, OCR, and production processing benchmarks also remain to be completed.

The 2,000-page target must only be marked complete when a regenerated dataset report confirms at least 2,000 eligible, readable pages.
