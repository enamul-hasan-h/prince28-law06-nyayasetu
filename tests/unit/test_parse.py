from pathlib import Path
from unittest.mock import MagicMock

import pytest

from nyayasetu.ingest import parse
from nyayasetu.ingest.parse import (
    ParseError,
    markup_to_markdown,
    parse_file,
    parse_html,
    parse_text,
    split_pages,
)


def test_parse_plain_text(tmp_path: Path):
    path = tmp_path / "sample.txt"
    path.write_text(
        "# Eligibility\n\nApplicants must be residents.",
        encoding="utf-8",
    )

    result = parse_text(path)

    assert result.kind == "text"
    assert len(result.pages) >= 1
    assert "Applicants must be residents." in result.pages[0].text


def test_parse_html_with_table(tmp_path: Path):
    path = tmp_path / "sample.html"
    path.write_text(
        """
        <html><head><title>Legal Aid</title></head>
        <body>
        <h1>Eligibility</h1>
        <p>Applicants must be residents.</p>
        <table>
          <tr><th>Scheme</th><th>Benefit</th></tr>
          <tr><td>Legal Aid</td><td>Free advice</td></tr>
        </table>
        </body></html>
        """,
        encoding="utf-8",
    )

    result = parse_html(path)

    assert result.kind == "html"
    assert len(result.pages) >= 1
    assert "Eligibility" in result.pages[0].text
    assert "Legal Aid" in result.pages[0].text


def test_parse_csv_as_data(tmp_path: Path):
    path = tmp_path / "sample.csv"
    path.write_text(
        "Scheme,Benefit\nLegal Aid,Free advice\n",
        encoding="utf-8",
    )

    result = parse_file(path)

    assert result.kind == "data"
    assert "Legal Aid" in result.pages[0].text


def test_parse_json_as_data(tmp_path: Path):
    path = tmp_path / "sample.json"
    path.write_text(
        '{"scheme": "Legal Aid", "benefit": "Free advice"}',
        encoding="utf-8",
    )

    result = parse_file(path)

    assert result.kind == "data"
    assert "Legal Aid" in result.pages[0].text


def test_parse_file_dispatches_text(tmp_path: Path):
    path = tmp_path / "sample.txt"
    path.write_text("NyayaSetu parser test.", encoding="utf-8")

    result = parse_file(path)

    assert result.kind == "text"
    assert "NyayaSetu parser test." in result.pages[0].text


def test_unsupported_file_type_raises_parse_error(tmp_path: Path):
    path = tmp_path / "sample.xyz"
    path.write_text("unsupported", encoding="utf-8")

    with pytest.raises(ParseError) as exc:
        parse_file(path)

    assert exc.value.reason == "unsupported_type"


def test_rst_heading_conversion():
    result = markup_to_markdown(
        "Eligibility\n===========\n\nApplicants qualify.",
        ".rst",
    )

    assert "# Eligibility" in result


def test_adoc_heading_conversion():
    result = markup_to_markdown("= Eligibility\n\nApplicants qualify.", ".adoc")

    assert "# Eligibility" in result


def test_split_pages():
    result = split_pages("First paragraph.\n\nSecond paragraph.", size=20)

    assert len(result) == 2
    assert "First paragraph." in result[0]
    assert "Second paragraph." in result[1]


def test_clean_text_normalizes_and_repairs_text():
    result = parse.clean_text("  Hello   world\x00\n treat-\nment \n\n\nEnd  ")

    assert result == "Hello world\ntreatment\n\nEnd"


def test_drop_repeated_lines_removes_headers_and_footers():
    pages = [
        (f"Legal Report\nMetadata\nContent page {i}\nDetailed information {i}\nPage {i} of 4")
        for i in range(1, 5)
    ]

    result = parse.drop_repeated_lines(pages)

    assert all("Legal Report" not in page for page in result)
    assert all("Page " not in page for page in result)
    assert all("Content page" in page for page in result)


def test_drop_repeated_lines_keeps_short_documents():
    pages = ["Header\nContent", "Header\nContent", "Header\nContent"]

    assert parse.drop_repeated_lines(pages) == pages


def test_heading_title_removes_anchor():
    assert parse.heading_title("First Steps { #first-steps }") == "First Steps"


def test_headings_in_ignores_code_blocks():
    text = """# Introduction
```python
# Not a heading
```
## Methods
"""

    found, in_code = parse.headings_in(text)

    assert found == [(1, "Introduction"), (2, "Methods")]
    assert in_code is False


def test_headings_in_tracks_open_code_fence():
    found, in_code = parse.headings_in("```python\n# Not a heading")

    assert found == []
    assert in_code is True


def test_with_heading_paths_tracks_sections_across_pages():
    pages = parse.with_heading_paths(
        [
            "# Introduction\nFirst page",
            "Second page\n## Background",
            "Third page",
        ]
    )

    assert pages[0].page_no == 1
    assert pages[0].headings == []
    assert pages[1].headings == ["Introduction"]
    assert pages[2].headings == ["Introduction", "Background"]


def test_with_heading_paths_counts_markdown_tables():
    pages = parse.with_heading_paths(["# Results\n\n| Name | Value |\n|---|---|\n| A | 1 |"])

    assert pages[0].tables == 1


def test_finish_uses_first_heading_as_document_title():
    result = parse.finish(
        "plain",
        "text",
        "Old filename",
        ["# Actual Title\n\nSome useful document content."],
    )

    assert result.title == "Actual Title"
    assert result.parser == "plain"
    assert result.kind == "text"


def test_finish_uses_metadata_when_no_heading():
    result = parse.finish(
        "plain",
        "text",
        "Metadata title",
        ["Some useful document content without a heading."],
    )

    assert result.title == "Metadata title"


def test_finish_rejects_empty_content():
    with pytest.raises(ParseError) as exc:
        parse.finish("plain", "text", "", [" \n  "])

    assert exc.value.reason == "empty"


def test_body_size_uses_most_common_font_size():
    def span(size, text):
        return {"size": size, "text": text}

    page = MagicMock()
    page.get_text.return_value = {
        "blocks": [
            {
                "lines": [
                    {"spans": [span(12, "Body text here")]},
                    {"spans": [span(12, "More body text")]},
                    {"spans": [span(20, "Title")]},
                ]
            }
        ]
    }

    doc = MagicMock()
    doc.__iter__.return_value = [page]

    assert parse._body_size(doc) == 12


def test_body_size_defaults_when_no_text():
    page = MagicMock()
    page.get_text.return_value = {"blocks": []}

    doc = MagicMock()
    doc.__iter__.return_value = [page]

    assert parse._body_size(doc) == 10.0


def test_heading_level_detects_heading_sizes():
    assert parse._heading_level("Main Heading", 20, False, 10) == 1
    assert parse._heading_level("Section Heading", 14, False, 10) == 2
    assert parse._heading_level("Bold Heading", 10, True, 10) == 3
    assert parse._heading_level("ordinary sentence.", 10, False, 10) == 0


def test_heading_level_rejects_invalid_text():
    assert parse._heading_level("A", 20, True, 10) == 0
    assert parse._heading_level("12345", 20, True, 10) == 0


def test_open_pdf_rejects_invalid_file(tmp_path):
    path = tmp_path / "broken.pdf"
    path.write_text("not a PDF", encoding="utf-8")

    with pytest.raises(ParseError) as exc:
        parse._open_pdf(path)

    assert exc.value.reason == "corrupt"


def test_open_pdf_rejects_empty_pdf(monkeypatch):
    doc = MagicMock()
    doc.needs_pass = False
    doc.page_count = 0

    monkeypatch.setattr(parse.pymupdf, "open", lambda _path: doc)

    with pytest.raises(ParseError) as exc:
        parse._open_pdf("empty.pdf")

    assert exc.value.reason == "empty"


def test_open_pdf_rejects_encrypted_pdf(monkeypatch):
    doc = MagicMock()
    doc.needs_pass = True

    monkeypatch.setattr(parse.pymupdf, "open", lambda _path: doc)

    with pytest.raises(ParseError) as exc:
        parse._open_pdf("encrypted.pdf")

    assert exc.value.reason == "encrypted"


def test_parse_pdf_pymupdf_extracts_text_and_skips_images(monkeypatch, tmp_path):
    page = MagicMock()
    page.get_cdrawings.return_value = []
    page.get_text.return_value = {
        "blocks": [
            {
                "type": 0,
                "bbox": (0, 0, 100, 20),
                "lines": [{"spans": [{"text": "A" * 70, "size": 10, "flags": 0}]}],
            },
            {"type": 1, "bbox": (0, 30, 100, 100)},
        ]
    }

    doc = MagicMock()
    doc.__enter__.return_value = doc
    doc.__iter__.return_value = [page]
    doc.metadata = {"title": "PDF Metadata"}
    monkeypatch.setattr(parse, "_open_pdf", lambda _: doc)

    result = parse.parse_pdf_pymupdf(tmp_path / "sample.pdf")

    assert result.parser == "pymupdf"
    assert result.title == "PDF Metadata"
    assert "A" * 70 in result.pages[0].text


def test_parse_pdf_pymupdf_rejects_scanned_pdf(monkeypatch, tmp_path):
    page = MagicMock()
    page.get_cdrawings.return_value = []
    page.get_text.return_value = {"blocks": []}

    doc = MagicMock()
    doc.__enter__.return_value = doc
    doc.__iter__.return_value = [page]
    doc.metadata = {}
    monkeypatch.setattr(parse, "_open_pdf", lambda _: doc)

    with pytest.raises(ParseError) as exc:
        parse.parse_pdf_pymupdf(tmp_path / "scan.pdf")

    assert exc.value.reason == "no_text_layer"


def test_parse_pdf_pymupdf_extracts_table_once(monkeypatch, tmp_path):
    table = MagicMock()
    table.bbox = parse.pymupdf.Rect(0, 0, 100, 20)
    table.to_markdown.return_value = "| Scheme | Benefit |\n|---|---|\n| Legal Aid | Free advice |"

    page = MagicMock()
    page.get_cdrawings.return_value = [1, 2, 3, 4]
    page.find_tables.return_value.tables = [table]
    page.get_text.return_value = {
        "blocks": [
            {"type": 0, "bbox": (0, 0, 100, 20), "lines": []},
            {"type": 0, "bbox": (0, 0, 100, 20), "lines": []},
            {
                "type": 0,
                "bbox": (150, 150, 250, 170),
                "lines": [{"spans": [{"text": "A" * 70, "size": 10, "flags": 0}]}],
            },
        ]
    }

    doc = MagicMock()
    doc.__enter__.return_value = doc
    doc.__iter__.return_value = [page]
    doc.metadata = {}
    monkeypatch.setattr(parse, "_open_pdf", lambda _: doc)

    result = parse.parse_pdf_pymupdf(tmp_path / "table.pdf")

    assert result.pages[0].text.count("| Scheme | Benefit |") == 1
    table.to_markdown.assert_called_once()


def test_parse_pdf_ocr_success(monkeypatch, tmp_path):
    page = MagicMock()
    page.get_textpage_ocr.return_value = MagicMock()
    page.get_text.return_value = "Recognized legal document text " * 5

    doc = MagicMock()
    doc.__enter__.return_value = doc
    doc.__iter__.return_value = [page]
    monkeypatch.setattr(parse, "_open_pdf", lambda _: doc)

    result = parse.parse_pdf_ocr(tmp_path / "scan.pdf")

    assert result.parser == "ocr-eng"
    assert result.kind == "pdf"
    assert "Recognized legal document text" in result.pages[0].text


def test_parse_pdf_ocr_wraps_tesseract_failure(monkeypatch, tmp_path):
    page = MagicMock()
    page.get_textpage_ocr.side_effect = RuntimeError("Tesseract unavailable")

    doc = MagicMock()
    doc.__enter__.return_value = doc
    doc.__iter__.return_value = [page]
    monkeypatch.setattr(parse, "_open_pdf", lambda _: doc)

    with pytest.raises(ParseError) as exc:
        parse.parse_pdf_ocr(tmp_path / "scan.pdf")

    assert exc.value.reason == "ocr_unavailable"


def test_parse_pdf_pypdf_rejects_encrypted_document(monkeypatch, tmp_path):
    reader = MagicMock()
    reader.is_encrypted = True
    reader.decrypt.return_value = 0
    monkeypatch.setattr(parse, "PdfReader", lambda _: reader)

    with pytest.raises(ParseError) as exc:
        parse.parse_pdf_pypdf(tmp_path / "encrypted.pdf")

    assert exc.value.reason == "encrypted"


def test_parse_pdf_pypdf_rejects_empty_document(monkeypatch, tmp_path):
    reader = MagicMock()
    reader.is_encrypted = False
    reader.pages = []
    monkeypatch.setattr(parse, "PdfReader", lambda _: reader)

    with pytest.raises(ParseError) as exc:
        parse.parse_pdf_pypdf(tmp_path / "empty.pdf")

    assert exc.value.reason == "empty"


def test_parse_pdf_pypdf_rejects_scanned_document(monkeypatch, tmp_path):
    page = MagicMock()
    page.extract_text.return_value = ""

    reader = MagicMock()
    reader.is_encrypted = False
    reader.pages = [page]
    monkeypatch.setattr(parse, "PdfReader", lambda _: reader)

    with pytest.raises(ParseError) as exc:
        parse.parse_pdf_pypdf(tmp_path / "scan.pdf")

    assert exc.value.reason == "no_text_layer"


def test_parse_pdf_pypdf_wraps_reader_errors(monkeypatch, tmp_path):
    def broken_reader(_):
        raise ValueError("Invalid PDF")

    monkeypatch.setattr(parse, "PdfReader", broken_reader)

    with pytest.raises(ParseError) as exc:
        parse.parse_pdf_pypdf(tmp_path / "broken.pdf")

    assert exc.value.reason == "corrupt"


def test_parse_html_rejects_missing_content(monkeypatch, tmp_path):
    path = tmp_path / "empty.html"
    path.write_text("<html></html>", encoding="utf-8")
    monkeypatch.setattr(parse.trafilatura, "extract", lambda *a, **kw: None)

    with pytest.raises(ParseError) as exc:
        parse_html(path)

    assert exc.value.reason == "empty"


def test_parse_html_handles_missing_metadata(monkeypatch, tmp_path):
    path = tmp_path / "article.html"
    path.write_text("<html><body>Article</body></html>", encoding="utf-8")
    monkeypatch.setattr(
        parse.trafilatura,
        "extract",
        lambda *a, **kw: "A" * 60,
    )
    monkeypatch.setattr(parse.trafilatura, "extract_metadata", lambda _: None)

    result = parse_html(path)

    assert result.kind == "html"
    assert result.title == ""


def test_parse_file_wraps_unexpected_parser_errors(monkeypatch, tmp_path):
    path = tmp_path / "sample.txt"
    path.write_text("content", encoding="utf-8")

    def broken_parser(_):
        raise RuntimeError("Unexpected failure")

    monkeypatch.setattr(parse, "parse_text", broken_parser)

    with pytest.raises(ParseError) as exc:
        parse_file(path)

    assert exc.value.reason == "crash"
    assert "RuntimeError" in exc.value.detail


def test_parse_file_wraps_unknown_pdf_parser(tmp_path):
    path = tmp_path / "sample.pdf"

    with pytest.raises(ParseError) as exc:
        parse_file(path, pdf_parser="unknown")

    assert exc.value.reason == "crash"


def test_markup_to_markdown_preserves_unsupported_suffix():
    text = "Heading\n========\nContent"

    assert markup_to_markdown(text, ".unknown") == text


def test_markup_to_markdown_handles_rst_without_heading_rule():
    text = "Heading without underline\nContent"

    assert markup_to_markdown(text, ".rst") == text
