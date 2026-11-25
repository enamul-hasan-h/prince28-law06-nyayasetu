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
| PDF pages counted | 1,943 |
| Target PDF pages | 2,000 |
| Target completion | 97.15% |
| Pages remaining | 57 |

The 31 downloaded PDFs passed the reported integrity checks:
- Missing files: 0
- SHA-256 mismatches: 0
- Duplicate SHA-256 values: 0
- PDF page-reading errors: 0

The source inventory currently records the licence status as `Not stated`. This status must not be represented as an open reuse licence.

## 2. Can the current corpus support the target?

The current corpus contains 31 verified PDF files and 1,943 PDF pages counted.

It has not yet reached the 2,000-page target. A further 57 readable pages are required.

Only verified PDF pages should contribute to this target. Sitemap candidates, public pages without reuse approval, research reference PDFs outside `data/raw/`, and synthetic test fixtures must not be counted.

## 3. Storage capacity

Measured storage for the 31 downloaded PDFs is:

| Metric | Measured value |
|---|---:|
| Total PDF storage | 187.04 MB |
| Average PDF size | 6.03 MB |
| Average storage per counted page | 100,941.45 bytes |
| Estimated PDF storage at 2,000 pages | 192.53 MB |

The 2,000-page estimate is a linear projection based on the current average bytes per page. It is an estimate, not a measured final storage requirement. Storage for extracted text, OCR output, indexes, databases, and other derived artefacts has not yet been measured.

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

The regenerated dataset report confirms that all 31 referenced PDFs could be read for page counting, with no reported page-reading errors. Page counting does not establish searchable-text coverage.

However, extraction throughput, OCR performance, and processing cost have not yet been benchmarked against a representative corpus.

Scanned PDFs may require OCR. Such documents should be identified and measured separately from text-based PDFs.

## 6. Main constraints and risks

1. **Reuse restrictions:** The source inventory records the licence status as `Not stated`. This does not establish an open reuse licence or unrestricted redistribution rights.
2. **Source coverage:** The source inventory contains three NALSA entries, while the manifest records 31 downloaded PDFs. Direct-document provenance and source-specific restrictions must remain traceable.
3. **Document quality:** Page readability has been verified, but scanned-document quality and OCR requirements need separate assessment.
4. **Version control:** Legal documents may be amended or superseded. Publication dates and currentness must be verified.
5. **Storage:** Final capacity requirements depend on actual document sizes and derived artefacts.
6. **Collection policy:** Robots.txt, website terms, and source-specific restrictions must be respected.

## 7. Conditions for reaching 2,000 pages

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

The source inventory must continue to report licence status accurately. OCR, derived-storage, and production processing benchmarks remain to be completed.

The 2,000-page target must only be marked complete when a regenerated dataset report confirms at least 2,000 eligible, readable pages.
