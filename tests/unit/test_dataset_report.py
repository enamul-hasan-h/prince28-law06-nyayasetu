"""Offline tests for the dataset reporting script."""

import importlib.util
import json
from pathlib import Path

import pymupdf

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "dataset_report.py"

SPEC = importlib.util.spec_from_file_location("nyayasetu_dataset_report", SCRIPT_PATH)
REPORT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REPORT)


def test_report_labels_pdf_page_count_accurately(tmp_path):
    """PDF page totals must not be presented as searchable-text totals."""
    data_dir = tmp_path / "data"
    raw_dir = data_dir / "raw"
    raw_dir.mkdir(parents=True)

    pdf_path = raw_dir / "sample.pdf"
    with pymupdf.open() as document:
        document.new_page()
        document.new_page()
        document.save(pdf_path)

    (data_dir / "manifest.jsonl").write_text(
        json.dumps(
            {
                "status": "downloaded",
                "path": "data/raw/sample.pdf",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (data_dir / "sources.csv").write_text(
        "url,source,licence,title\n",
        encoding="utf-8",
    )

    report = REPORT.build_report(tmp_path, full_pages_target=2000)

    assert "| PDF pages counted | 2 |" in report
    assert "PDF pages readable" not in report
    assert "does not measure searchable-text coverage" in report
