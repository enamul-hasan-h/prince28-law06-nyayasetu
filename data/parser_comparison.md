# PDF Parser Comparison

Comparison of PyMuPDF and pypdf on the largest available corpus PDFs.

Statistics show extraction quantities, not extraction quality.
Inspect the extracted text against each original PDF before assigning a verdict.

| PDF | Size (bytes) | PyMuPDF | pypdf | Manual verdict |
|---|---:|---|---|---|
| data/raw/nalsa/1756544763-ddfff673.pdf | 29,921,893 | failed; pages=0; chars=0; headings=0; tables=0; error=no_text_layer: 0 characters on 36 pages: needs OCR | failed; pages=0; chars=0; headings=0; tables=0; error=no_text_layer: almost no text on 36 pages: needs OCR | Inconclusive - OCR required |
| data/raw/nalsa/1756544777-fea03c6b.pdf | 18,664,311 | failed; pages=0; chars=0; headings=0; tables=0; error=no_text_layer: 0 characters on 28 pages: needs OCR | failed; pages=0; chars=0; headings=0; tables=0; error=no_text_layer: almost no text on 28 pages: needs OCR | Inconclusive - OCR required |
| data/raw/nalsa/202505142178608-0e5ae2e9.pdf | 10,403,410 | failed; pages=0; chars=0; headings=0; tables=0; error=no_text_layer: 0 characters on 140 pages: needs OCR | failed; pages=0; chars=0; headings=0; tables=0; error=no_text_layer: almost no text on 140 pages: needs OCR | Inconclusive - OCR required |
| data/raw/nalsa/20250409258379504-8e8276b9.pdf | 10,242,355 | failed; pages=0; chars=0; headings=0; tables=0; error=no_text_layer: 0 characters on 84 pages: needs OCR | failed; pages=0; chars=0; headings=0; tables=0; error=no_text_layer: almost no text on 84 pages: needs OCR | Inconclusive - OCR required |
| data/raw/nalsa/20250408408064338-3434fcd0.pdf | 10,093,103 | failed; pages=0; chars=0; headings=0; tables=0; error=no_text_layer: 0 characters on 55 pages: needs OCR | failed; pages=0; chars=0; headings=0; tables=0; error=no_text_layer: almost no text on 55 pages: needs OCR | Inconclusive - OCR required |
| data/raw/nalsa/2025040925439249-c7a90332.pdf | 9,972,780 | success; pages=131; chars=146962; headings=309; tables=8 | success; pages=131; chars=144200; headings=0; tables=0 | PyMuPDF - better text and structure |
| data/raw/nalsa/202504081834821576-35eb6f80.pdf | 9,963,056 | failed; pages=0; chars=0; headings=0; tables=0; error=no_text_layer: 0 characters on 63 pages: needs OCR | failed; pages=0; chars=0; headings=0; tables=0; error=no_text_layer: almost no text on 63 pages: needs OCR | Inconclusive - OCR required |
| data/raw/nalsa/202504081540884465-660db624.pdf | 9,887,042 | failed; pages=0; chars=0; headings=0; tables=0; error=no_text_layer: 0 characters on 21 pages: needs OCR | failed; pages=0; chars=0; headings=0; tables=0; error=no_text_layer: almost no text on 21 pages: needs OCR | Inconclusive - OCR required |
| data/raw/nalsa/2025040866630099-49d08f01.pdf | 8,983,229 | failed; pages=0; chars=0; headings=0; tables=0; error=no_text_layer: 0 characters on 16 pages: needs OCR | failed; pages=0; chars=0; headings=0; tables=0; error=no_text_layer: almost no text on 16 pages: needs OCR | Inconclusive - OCR required |
| data/raw/nalsa/202504091237499824-db27697c.pdf | 8,403,139 | success; pages=176; chars=330842; headings=331; tables=27 | success; pages=176; chars=328438; headings=0; tables=0 | PyMuPDF - better text and structure |

**Files compared:** 10

**Verdict guidance:** Record PyMuPDF, pypdf, Tie, or Inconclusive, with a short reason based on manual inspection of extraction quality.
