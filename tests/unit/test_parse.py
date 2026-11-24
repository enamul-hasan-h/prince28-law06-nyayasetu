from pathlib import Path

import pytest

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
