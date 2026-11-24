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


def main() -> None:
    argument_parser = argparse.ArgumentParser(description="Compare PDF parser extraction quality.")
    argument_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of PDFs to compare (default: 10)",
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

    for path in files:
        print(f"FILE: {path.relative_to(ROOT).as_posix()}")
        print(f"SIZE: {path.stat().st_size:,} bytes")

        results = [
            compare_parser(path, "PyMuPDF", parse_pdf_pymupdf),
            compare_parser(path, "pypdf", parse_pdf_pypdf),
        ]

        for result in results:
            print(
                f"{result['parser']}: {result['status']} | "
                f"pages={result['pages']} | "
                f"chars={result['characters']} | "
                f"headings={result['headings']} | "
                f"tables={result['tables']}"
            )

            if result["error"]:
                print(f"  Error: {result['error']}")

        print()

    print("Parser comparison completed.")


if __name__ == "__main__":
    main()
