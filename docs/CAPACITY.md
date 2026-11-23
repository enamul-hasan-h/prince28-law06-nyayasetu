# NyayaSetu Corpus Capacity Assessment

## 1. Current dataset baseline

The current dataset report was generated using:

`uv run python scripts/dataset_report.py --full-pages 2000`

| Metric | Current value |
|---|---:|
| Source inventory entries | 3 |
| Permission-pending sources | 3 |
| Approved corpus documents | 0 |
| Downloaded documents | 0 |
| PDF pages collected | 0 |
| Target PDF pages | 2,000 |
| Target completion | 0% |

The three inventory entries are official NALSA research references. They are not approved for automated collection or reproduction.

## 2. Can the current corpus support the target?

No. The current approved corpus contains zero documents and zero PDF pages.

The 2,000-page target remains outstanding. It must not be represented as achieved by counting sitemap candidates, public pages without reuse approval, research reference PDFs outside `data/raw/`, or synthetic test fixtures.

## 3. Storage capacity

Actual storage requirements cannot be estimated reliably until an approved sample corpus is available.

After permission is obtained, measure total downloaded bytes, average document size, total PDF page count, and storage used by extracted text and derived data.

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

No production collection throughput has been measured. Synthetic local tests verify downloader behaviour but are not representative of external source performance.

## 5. Processing capacity

The project includes `pypdf` for PDF page inspection. Actual extraction throughput, OCR performance, and processing cost have not yet been benchmarked against an approved representative corpus.

Scanned PDFs may require OCR. Such documents should be identified and measured separately from text-based PDFs.

## 6. Main constraints and risks

1. **Reuse permission:** NALSA material is permission pending. Written permission and any third-party rights must be clarified before collection or reproduction.
2. **Source coverage:** The current inventory contains three page references, not the complete target list of direct document URLs.
3. **Document quality:** Scanned PDFs may require OCR and manual quality checks.
4. **Version control:** Legal documents may be amended or superseded. Publication dates and currentness must be verified.
5. **Storage:** Final capacity requirements depend on actual document sizes and derived artefacts.
6. **Collection policy:** Robots.txt, website terms, and source-specific restrictions must be respected.

## 7. Conditions for reaching 2,000 pages

- Obtain and record reuse permission for each source.
- Verify the current version and direct document URL.
- Build an approved source inventory with licence or permission evidence.
- Collect only approved documents.
- Verify file hashes and PDF readability.
- Measure actual page count and storage.
- Document unreadable files, OCR requirements, and exclusions.
- Regenerate `DATASET.md` after each approved collection batch.

## 8. Conclusion

NyayaSetu has a tested collection foundation, including URL, Git repository, and sitemap discovery workflows. Unit tests and lint checks pass.

However, the corpus itself is not yet populated. The immediate blocker is source permission and verification, not downloader functionality.

The 2,000-page target remains an explicit future milestone and must only be marked complete when the dataset report confirms it.
