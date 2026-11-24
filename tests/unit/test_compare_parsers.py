import importlib.util
import sys
from pathlib import Path

import pytest

from nyayasetu.ingest.parse import ParsedDoc, ParsedPage, ParseError

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "compare_parsers.py"
SPEC = importlib.util.spec_from_file_location("compare_parsers", SCRIPT_PATH)
compare_parsers = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = compare_parsers
SPEC.loader.exec_module(compare_parsers)


def make_parsed_doc():
    return ParsedDoc(
        parser="test",
        kind="pdf",
        title="Test PDF",
        pages=[
            ParsedPage(
                page_no=1,
                text="Legal aid information",
                headings=["Eligibility"],
                tables=1,
            ),
            ParsedPage(
                page_no=2,
                text="Application procedure",
                headings=["Application"],
                tables=0,
            ),
        ],
    )


def test_find_pdfs_returns_largest_files_first(tmp_path, monkeypatch):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    small = raw_dir / "small.pdf"
    large = raw_dir / "large.pdf"
    medium = raw_dir / "medium.PDF"

    small.write_bytes(b"a" * 10)
    large.write_bytes(b"b" * 30)
    medium.write_bytes(b"c" * 20)

    monkeypatch.setattr(compare_parsers, "ROOT", tmp_path)
    monkeypatch.setattr(compare_parsers, "RAW_DIR", raw_dir)

    result = compare_parsers.find_pdfs(limit=2)

    assert result == [large, medium]


def test_find_pdfs_returns_empty_when_directory_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(compare_parsers, "RAW_DIR", tmp_path / "missing")

    assert compare_parsers.find_pdfs(limit=10) == []


def test_find_pdfs_ignores_non_pdf_files(tmp_path, monkeypatch):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "document.txt").write_text("Not a PDF", encoding="utf-8")
    (raw_dir / "document.pdf").write_bytes(b"%PDF-test")

    monkeypatch.setattr(compare_parsers, "ROOT", tmp_path)
    monkeypatch.setattr(compare_parsers, "RAW_DIR", raw_dir)

    assert compare_parsers.find_pdfs(limit=10) == [raw_dir / "document.pdf"]


def test_compare_parser_returns_extraction_statistics():
    result = compare_parsers.compare_parser(
        Path("sample.pdf"),
        "PyMuPDF",
        lambda _: make_parsed_doc(),
    )

    assert result == {
        "parser": "PyMuPDF",
        "status": "success",
        "pages": 2,
        "characters": len("Legal aid information") + len("Application procedure"),
        "headings": 2,
        "tables": 1,
        "error": "",
    }


def test_compare_parser_records_parse_error():
    def broken_parser(_):
        raise ParseError("corrupt", "Invalid PDF")

    result = compare_parsers.compare_parser(
        Path("broken.pdf"),
        "pypdf",
        broken_parser,
    )

    assert result["status"] == "failed"
    assert result["error"] == "corrupt: Invalid PDF"
    assert result["pages"] == 0


def test_compare_parser_records_unexpected_error():
    def broken_parser(_):
        raise RuntimeError("Unexpected failure")

    result = compare_parsers.compare_parser(
        Path("broken.pdf"),
        "pypdf",
        broken_parser,
    )

    assert result["status"] == "failed"
    assert result["error"] == "RuntimeError: Unexpected failure"


def test_main_handles_empty_corpus(tmp_path, monkeypatch, capsys):
    report_path = tmp_path / "parser_comparison.md"

    monkeypatch.setattr(compare_parsers, "RAW_DIR", tmp_path / "missing")
    monkeypatch.setattr(
        sys,
        "argv",
        ["compare_parsers.py", "--report", str(report_path)],
    )

    compare_parsers.main()

    output = capsys.readouterr().out

    assert "No PDF files found in data/raw." in output
    assert "PDF parser comparison files: 0" in output
    assert not report_path.exists()


def test_main_rejects_zero_limit(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["compare_parsers.py", "--limit", "0"])

    with pytest.raises(SystemExit) as exc:
        compare_parsers.main()

    assert exc.value.code == 2


def test_main_compares_both_parsers(tmp_path, monkeypatch, capsys):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    pdf_path = raw_dir / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-test")

    report_path = tmp_path / "parser_comparison.md"

    monkeypatch.setattr(compare_parsers, "ROOT", tmp_path)
    monkeypatch.setattr(compare_parsers, "RAW_DIR", raw_dir)
    monkeypatch.setattr(
        sys,
        "argv",
        ["compare_parsers.py", "--limit", "1", "--report", str(report_path)],
    )
    monkeypatch.setattr(
        compare_parsers,
        "parse_pdf_pymupdf",
        lambda _: make_parsed_doc(),
    )
    monkeypatch.setattr(
        compare_parsers,
        "parse_pdf_pypdf",
        lambda _: make_parsed_doc(),
    )

    compare_parsers.main()

    output = capsys.readouterr().out

    assert "Comparing 1 PDF file(s)." in output
    assert "PyMuPDF: success" in output
    assert "pypdf: success" in output
    assert "Parser comparison completed." in output

    assert report_path.exists()

    report = report_path.read_text(encoding="utf-8")

    assert "| PDF | Size (bytes) | PyMuPDF | pypdf | Manual verdict |" in report
    assert "Pending review" in report
    assert "sample.pdf" in report


def test_generate_report_writes_comparison_table(tmp_path):
    report_path = tmp_path / "reports" / "comparison.md"

    comparisons = [
        {
            "file": "data/raw/sample.pdf",
            "size": 1024,
            "pymupdf": {
                "parser": "PyMuPDF",
                "status": "success",
                "pages": 2,
                "characters": 500,
                "headings": 4,
                "tables": 1,
                "error": "",
            },
            "pypdf": {
                "parser": "pypdf",
                "status": "success",
                "pages": 2,
                "characters": 450,
                "headings": 3,
                "tables": 0,
                "error": "",
            },
        }
    ]

    compare_parsers.generate_report(comparisons, report_path)

    report = report_path.read_text(encoding="utf-8")

    assert "# PDF Parser Comparison" in report
    assert "data/raw/sample.pdf" in report
    assert "1,024" in report
    assert "pages=2" in report
    assert "chars=500" in report
    assert "chars=450" in report
    assert "Pending review" in report
    assert "Files compared:** 1" in report


def test_generate_report_escapes_markdown_table_values(tmp_path):
    report_path = tmp_path / "comparison.md"

    comparisons = [
        {
            "file": "data/raw/file|name.pdf",
            "size": 100,
            "pymupdf": {
                "parser": "PyMuPDF",
                "status": "failed",
                "pages": 0,
                "characters": 0,
                "headings": 0,
                "tables": 0,
                "error": "corrupt | invalid PDF",
            },
            "pypdf": {
                "parser": "pypdf",
                "status": "success",
                "pages": 1,
                "characters": 100,
                "headings": 1,
                "tables": 0,
                "error": "",
            },
        }
    ]

    compare_parsers.generate_report(comparisons, report_path)

    report = report_path.read_text(encoding="utf-8")

    assert r"file\|name.pdf" in report
    assert r"corrupt \| invalid PDF" in report


def test_generate_report_preserves_existing_manual_verdicts(tmp_path):
    report_path = tmp_path / "comparison.md"
    report_path.write_text(
        "\n".join(
            [
                "# PDF Parser Comparison",
                "| PDF | Size (bytes) | PyMuPDF | pypdf | Manual verdict |",
                "|---|---:|---|---|---|",
                "| data/raw/sample.pdf | 1,024 | old result | old result | PyMuPDF - verified |",
            ]
        ),
        encoding="utf-8",
    )

    parser_result = {
        "parser": "PyMuPDF",
        "status": "success",
        "pages": 2,
        "characters": 500,
        "headings": 4,
        "tables": 1,
        "error": "",
    }

    comparisons = [
        {
            "file": "data/raw/sample.pdf",
            "size": 1024,
            "pymupdf": parser_result,
            "pypdf": parser_result,
        },
        {
            "file": "data/raw/new.pdf",
            "size": 2048,
            "pymupdf": parser_result,
            "pypdf": parser_result,
        },
    ]

    compare_parsers.generate_report(comparisons, report_path)

    report = report_path.read_text(encoding="utf-8")

    assert "PyMuPDF - verified" in report
    assert "data/raw/new.pdf" in report
    assert report.count("Pending review") == 1
