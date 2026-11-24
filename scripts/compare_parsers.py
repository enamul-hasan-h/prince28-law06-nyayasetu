"""Compare PyMuPDF and pypdf on the largest available PDF files."""

import argparse
from pathlib import Path

from nyayasetu.ingest.parse import (
    ParseError,
    parse_pdf_pymupdf,
    parse_pdf_pypdf,
)

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
DEFAULT_REPORT = ROOT / "data" / "parser_comparison.md"


def find_pdfs(limit: int) -> list[Path]:
    """Return the largest PDF files inside the raw corpus."""
    if not RAW_DIR.exists():
        return []

    files = [
        path for path in RAW_DIR.rglob("*") if path.is_file() and path.suffix.lower() == ".pdf"
    ]

    return sorted(files, key=lambda path: path.stat().st_size, reverse=True)[:limit]


def compare_parser(path: Path, parser_name: str, parser_func) -> dict:
    """Run one parser and collect comparable statistics."""
    try:
        parsed = parser_func(path)
        return {
            "parser": parser_name,
            "status": "success",
            "pages": len(parsed.pages),
            "characters": sum(len(page.text) for page in parsed.pages),
            "headings": sum(len(page.headings) for page in parsed.pages),
            "tables": sum(page.tables for page in parsed.pages),
            "error": "",
        }
    except ParseError as error:
        return {
            "parser": parser_name,
            "status": "failed",
            "pages": 0,
            "characters": 0,
            "headings": 0,
            "tables": 0,
            "error": str(error),
        }
    except Exception as error:
        return {
            "parser": parser_name,
            "status": "failed",
            "pages": 0,
            "characters": 0,
            "headings": 0,
            "tables": 0,
            "error": f"{type(error).__name__}: {error}",
        }


def escape_markdown(value: str) -> str:
    """Escape characters that could break a Markdown table."""
    return value.replace("|", r"\|").replace("\n", " ")


def format_parser_result(result: dict) -> str:
    """Format parser statistics for one Markdown table cell."""
    summary = (
        f"{result['status']}; "
        f"pages={result['pages']}; "
        f"chars={result['characters']}; "
        f"headings={result['headings']}; "
        f"tables={result['tables']}"
    )

    if result["error"]:
        summary += f"; error={escape_markdown(result['error'])}"

    return summary


def generate_report(comparisons: list[dict], report_path: Path) -> None:
    """Write parser comparison results while preserving manual verdicts."""
    existing_verdicts = {}

    if report_path.exists():
        for line in report_path.read_text(encoding="utf-8").splitlines():
            if not line.startswith("|"):
                continue

            cells = [cell.strip() for cell in line.split("|")]
            if len(cells) != 7:
                continue

            filename = cells[1]
            verdict = cells[-2]

            if filename.lower().endswith(".pdf"):
                existing_verdicts[filename] = verdict

    lines = [
        "# PDF Parser Comparison",
        "",
        "Comparison of PyMuPDF and pypdf on the largest available corpus PDFs.",
        "",
        "Statistics show extraction quantities, not extraction quality.",
        "Inspect the extracted text against each original PDF before assigning a verdict.",
        "",
        "| PDF | Size (bytes) | PyMuPDF | pypdf | Manual verdict |",
        "|---|---:|---|---|---|",
    ]

    for comparison in comparisons:
        filename = comparison["file"]
        verdict = existing_verdicts.get(filename, "Pending review")

        lines.append(
            f"| {escape_markdown(filename)} "
            f"| {comparison['size']:,} "
            f"| {format_parser_result(comparison['pymupdf'])} "
            f"| {format_parser_result(comparison['pypdf'])} "
            f"| {escape_markdown(verdict)} |"
        )

    lines.extend(
        [
            "",
            f"**Files compared:** {len(comparisons)}",
            "",
            "**Verdict guidance:** Record PyMuPDF, pypdf, Tie, or Inconclusive, "
            "with a short reason based on manual inspection of extraction quality.",
            "",
        ]
    )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    argument_parser = argparse.ArgumentParser(description="Compare PDF parser extraction quality.")
    argument_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of PDFs to compare (default: 10)",
    )
    argument_parser.add_argument(
        "--report",
        type=Path,
        default=DEFAULT_REPORT,
        help="Markdown report output path (default: data/parser_comparison.md)",
    )
    args = argument_parser.parse_args()

    if args.limit < 1:
        argument_parser.error("--limit must be at least 1")

    files = find_pdfs(args.limit)

    if not files:
        print("No PDF files found in data/raw.")
        print("PDF parser comparison files: 0")
        return

    print(f"Comparing {len(files)} PDF file(s).\n")

    comparisons = []

    for path in files:
        print(f"FILE: {path.relative_to(ROOT).as_posix()}")
        print(f"SIZE: {path.stat().st_size:,} bytes")

        results = {
            "pymupdf": compare_parser(path, "PyMuPDF", parse_pdf_pymupdf),
            "pypdf": compare_parser(path, "pypdf", parse_pdf_pypdf),
        }

        for result in results.values():
            print(
                f"{result['parser']}: {result['status']} | "
                f"pages={result['pages']} | "
                f"chars={result['characters']} | "
                f"headings={result['headings']} | "
                f"tables={result['tables']}"
            )

            if result["error"]:
                print(f"  Error: {result['error']}")

        comparisons.append(
            {
                "file": path.relative_to(ROOT).as_posix(),
                "size": path.stat().st_size,
                **results,
            }
        )
        print()

    generate_report(comparisons, args.report)

    print("Parser comparison completed.")
    print(f"Markdown report saved to: {args.report}")


if __name__ == "__main__":
    main()
