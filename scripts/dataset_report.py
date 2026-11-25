"""Generate a factual inventory of the NyayaSetu corpus."""

import argparse
import csv
import hashlib
import json
from collections import Counter
from io import StringIO
from pathlib import Path

from pypdf import PdfReader


def read_manifest(path: Path) -> list[dict]:
    """Read non-empty JSON Lines manifest records."""
    if not path.exists():
        return []

    records = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid manifest JSON on line {line_number}: {exc}") from exc

    return records


def read_sources(path: Path) -> list[dict]:
    """Read source inventory while ignoring its comment lines."""
    if not path.exists():
        return []

    content = path.read_text(encoding="utf-8-sig")
    rows = [
        line for line in content.splitlines() if line.strip() and not line.lstrip().startswith("#")
    ]

    if not rows:
        return []

    return list(csv.DictReader(StringIO("\n".join(rows))))


def sha256_file(path: Path) -> str:
    """Calculate a file's SHA-256 digest."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_report(root: Path, full_pages_target: int) -> str:
    """Build a Markdown report from local metadata and files."""
    manifest_path = root / "data" / "manifest.jsonl"
    sources_path = root / "data" / "sources.csv"
    raw_path = root / "data" / "raw"

    records = read_manifest(manifest_path)
    sources = read_sources(sources_path)

    statuses = Counter(str(record.get("status", "unknown")) for record in records)
    pending_sources = [
        source for source in sources if "pending" in str(source.get("licence", "")).lower()
    ]

    raw_files = (
        sorted(path for path in raw_path.rglob("*") if path.is_file()) if raw_path.exists() else []
    )

    downloaded = [record for record in records if record.get("status") == "downloaded"]

    verified_files = []
    missing_files = []
    hash_mismatches = []
    page_errors = []
    total_pages = 0
    pdf_count = 0

    for record in downloaded:
        relative_path = record.get("path", "")
        if not relative_path:
            missing_files.append("(manifest record has no path)")
            continue

        file_path = (root / relative_path).resolve()
        if not file_path.is_relative_to(root.resolve()) or not file_path.is_file():
            missing_files.append(relative_path)
            continue

        verified_files.append(file_path)

        expected_hash = record.get("sha256")
        if expected_hash and sha256_file(file_path) != expected_hash:
            hash_mismatches.append(relative_path)

        if file_path.suffix.lower() == ".pdf":
            pdf_count += 1
            try:
                total_pages += len(PdfReader(str(file_path)).pages)
            except Exception as exc:  # Report unreadable PDFs without hiding them.
                page_errors.append(f"{relative_path}: {exc}")

    hashes = [str(record.get("sha256")) for record in downloaded if record.get("sha256")]
    duplicate_hashes = len(hashes) - len(set(hashes))

    raw_pdf_count = sum(path.suffix.lower() == ".pdf" for path in raw_files)

    lines = [
        "# NyayaSetu Dataset Report",
        "",
        "> Generated from the local manifest, source inventory, and `data/raw/`.",
        "> This report does not establish copyright permission or legal approval.",
        "",
        "## Collection summary",
        "",
        "| Metric | Count |",
        "|---|---:|",
        f"| Source inventory entries | {len(sources)} |",
        f"| Sources marked permission pending | {len(pending_sources)} |",
        f"| Manifest records | {len(records)} |",
        f"| Downloaded manifest records | {len(downloaded)} |",
        f"| Files verified on disk | {len(verified_files)} |",
        f"| Files physically present under `data/raw/` | {len(raw_files)} |",
        f"| PDF files under `data/raw/` | {raw_pdf_count} |",
        f"| PDF files referenced by downloaded records | {pdf_count} |",
        f"| PDF pages counted | {total_pages} |",
        f"| Page target | {full_pages_target} |",
        f"| Progress toward page target | {total_pages}/{full_pages_target} |",
        "",
        "> Page count reflects PDF page objects that could be read. "
        "It does not measure searchable-text coverage or OCR completeness.",
        "",
        "## Manifest status breakdown",
        "",
        "| Status | Records |",
        "|---|---:|",
    ]

    if statuses:
        lines.extend(f"| {status} | {count} |" for status, count in sorted(statuses.items()))
    else:
        lines.append("| No records | 0 |")

    lines.extend(
        [
            "",
            "## Source inventory",
            "",
            "| Source | Title | Licence / permission status |",
            "|---|---|---|",
        ]
    )

    if sources:
        for source in sources:
            name = str(source.get("source", "")).replace("|", "\\|")
            title = str(source.get("title", "")).replace("|", "\\|")
            licence = str(source.get("licence", "")).replace("|", "\\|")
            lines.append(f"| {name} | {title} | {licence} |")
    else:
        lines.append("| No source entries | | |")

    lines.extend(
        [
            "",
            "## Integrity checks",
            "",
            f"- Manifest records with missing files: {len(missing_files)}",
            f"- SHA-256 mismatches: {len(hash_mismatches)}",
            f"- Duplicate SHA-256 values: {duplicate_hashes}",
            f"- PDFs with page-reading errors: {len(page_errors)}",
            "",
        ]
    )

    if missing_files:
        lines.append("### Missing files")
        lines.extend(f"- `{item}`" for item in missing_files)
        lines.append("")

    if hash_mismatches:
        lines.append("### Hash mismatches")
        lines.extend(f"- `{item}`" for item in hash_mismatches)
        lines.append("")

    if page_errors:
        lines.append("### PDF page-reading errors")
        lines.extend(f"- `{item}`" for item in page_errors)
        lines.append("")

    lines.extend(
        [
            "## Collection and permission notes",
            "",
            "- Discovery candidates are not collected corpus documents.",
            "- Sources marked `Permission pending` are not approved for collection.",
            "- Public accessibility does not by itself establish reuse permission.",
            "- Research reference PDFs outside `data/raw/` are excluded from these totals.",
            "- Synthetic test fixtures must not be counted as legal corpus material.",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> int:
    """Generate DATASET.md."""
    parser = argparse.ArgumentParser(
        description="Report NyayaSetu corpus files, pages, and integrity."
    )
    parser.add_argument(
        "--full-pages",
        type=int,
        default=2000,
        help="Target number of PDF pages (default: 2000).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("DATASET.md"),
        help="Markdown report output path.",
    )
    args = parser.parse_args()

    if args.full_pages < 1:
        parser.error("--full-pages must be positive.")

    root = Path.cwd().resolve()
    try:
        report = build_report(root, args.full_pages)
        output = args.output
        if not output.is_absolute():
            output = root / output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report, encoding="utf-8")
    except (OSError, ValueError) as exc:
        print(f"Dataset report failed: {exc}")
        return 1

    print(f"Dataset report written to: {output}")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
