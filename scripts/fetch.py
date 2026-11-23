"""Command-line entry point for NyayaSetu corpus collection."""

import argparse
import asyncio
import csv
import hashlib
import shutil
import subprocess
import tempfile
import time
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

from nyayasetu.ingest.fetch import (
    Manifest,
    fetch_all,
    now_iso,
    read_sources,
    slug,
)
from nyayasetu.ingest.sitemap import SitemapError, discover_sitemap


def report_result(record: dict, number: int) -> None:
    """Print one completed URL result."""
    status = record["status"]
    url = record["url"]

    if status == "downloaded":
        size_kb = record["bytes"] / 1024
        print(f"[{number}] downloaded {size_kb:.1f} KB {record['path']}")
    elif status == "blocked":
        print(f"[{number}] blocked by robots.txt: {url}")
    else:
        print(f"[{number}] {status}: {url} ({record.get('error', '')})")


def approved_licence(licence: str) -> bool:
    """Reject empty or explicitly unapproved licence descriptions."""
    if not licence.strip():
        return False

    blocked_terms = (
        "pending",
        "not approved",
        "not authorised",
        "not authorized",
        "permission required",
        "permission not granted",
        "research reference only",
    )

    return not any(term in licence.casefold() for term in blocked_terms)


async def run_urls(args: argparse.Namespace) -> int:
    """Run the URL-list downloader."""
    root = Path.cwd()
    sources_path = root / "data" / "sources.csv"

    if not sources_path.is_file():
        print(f"Source inventory not found: {sources_path}")
        return 1

    try:
        sources = read_sources(sources_path)
    except (ValueError, OSError) as exc:
        print(f"Source inventory rejected: {exc}")
        return 1

    if not sources:
        print("No approved sources found in data/sources.csv.")
        return 1

    if not 1 <= args.max_concurrency <= 4:
        print("--max-concurrency must be between 1 and 4.")
        return 1

    print(f"Starting URL collection: {len(sources)} source(s)")
    print(f"Concurrency: {args.max_concurrency}")
    print(f"Per-host delay: {args.delay} seconds")

    started = time.monotonic()
    completed = 0

    def on_result(record: dict) -> None:
        nonlocal completed
        completed += 1
        report_result(record, completed)

    counts = await fetch_all(
        sources,
        root=root,
        max_concurrency=args.max_concurrency,
        per_host_delay=args.delay,
        on_result=on_result,
    )

    elapsed = time.monotonic() - started

    print("\nCollection summary")
    print("------------------")
    print(f"Sources:    {len(sources)}")
    print(f"Downloaded: {counts['downloaded']}")
    print(f"Skipped:    {counts['skipped']}")
    print(f"Blocked:    {counts['blocked']}")
    print(f"Failed:     {counts['failed']}")
    print(f"Duration:   {elapsed:.2f} seconds")

    return 1 if counts["failed"] else 0


def validate_extensions(values: list[str]) -> set[str]:
    """Normalize and validate file extensions."""
    extensions = set()

    for value in values:
        extension = value.strip().lower()
        if not extension.startswith("."):
            extension = f".{extension}"

        if not extension[1:].isalnum():
            raise ValueError(f"Invalid extension: {value}")

        extensions.add(extension)

    return extensions


def run_repo(args: argparse.Namespace) -> int:
    """Collect matching files from a permitted Git repository."""
    if not args.permission_confirmed:
        print(
            "Repository collection refused: verify the repository licence "
            "and content rights, then pass --permission-confirmed."
        )
        return 1

    licence = args.licence.strip()

    if not approved_licence(licence):
        print("Repository collection refused: permission is not approved.")
        return 1

    parts = args.repository.split("/")

    if len(parts) != 2 or not all(parts):
        print("Repository must be OWNER/REPO.")
        return 2

    owner, repository = parts

    if not all(char.isalnum() or char in "-_." for char in owner + repository):
        print("Invalid repository name.")
        return 2

    try:
        extensions = validate_extensions(args.ext)
    except ValueError as exc:
        print(exc)
        return 2

    requested_path = args.path.strip("/")

    if requested_path and ".." in PurePosixPath(requested_path).parts:
        print("Invalid repository path.")
        return 2

    if args.local_path:
        local_path = Path(args.local_path).expanduser().resolve()

        if not local_path.is_dir():
            print(f"Local repository does not exist: {local_path}")
            return 1

        url = str(local_path)
    else:
        url = f"https://github.com/{owner}/{repository}.git"

    root = Path.cwd()
    raw_dir = root / "data" / "raw" / slug(args.source)
    manifest_path = root / "data" / "manifest.jsonl"

    print(f"Repository: {args.repository}")
    print(f"Path filter: {requested_path or '(repository root)'}")
    print(f"Extensions: {', '.join(sorted(extensions))}")

    try:
        with tempfile.TemporaryDirectory(prefix="nyayasetu-repo-") as temp:
            checkout = Path(temp) / "repository"

            command = [
                "git",
                "clone",
                "--depth",
                "1",
                "--filter=blob:none",
                "--no-checkout",
            ]

            if args.ref:
                command.extend(["--branch", args.ref])

            command.extend([url, str(checkout)])

            subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
            )

            if requested_path:
                subprocess.run(
                    [
                        "git",
                        "-C",
                        str(checkout),
                        "sparse-checkout",
                        "init",
                        "--cone",
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )

                subprocess.run(
                    [
                        "git",
                        "-C",
                        str(checkout),
                        "sparse-checkout",
                        "set",
                        requested_path,
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )

            subprocess.run(
                ["git", "-C", str(checkout), "checkout"],
                check=True,
                capture_output=True,
                text=True,
            )

            commit = subprocess.run(
                ["git", "-C", str(checkout), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()

            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest = Manifest(manifest_path)

            files = [
                path
                for path in checkout.rglob("*")
                if path.is_file() and ".git" not in path.parts and path.suffix.lower() in extensions
            ]

            downloaded = 0
            skipped = 0

            for source_file in files:
                relative = source_file.relative_to(checkout)
                destination = raw_dir / relative
                destination.parent.mkdir(parents=True, exist_ok=True)

                record_url = f"git+{args.repository}@{commit}#{relative.as_posix()}"

                if manifest.done(record_url, root):
                    skipped += 1
                    continue

                if destination.exists():
                    print(f"Refusing to overwrite existing file: {destination}")
                    return 1

                temporary = destination.with_name(destination.name + ".part")

                try:
                    shutil.copy2(source_file, temporary)
                    digest = hashlib.sha256(temporary.read_bytes()).hexdigest()
                    size = temporary.stat().st_size
                    temporary.replace(destination)
                finally:
                    temporary.unlink(missing_ok=True)

                record = {
                    "url": record_url,
                    "source": args.source,
                    "licence": licence,
                    "title": relative.name,
                    "via": "git",
                    "repository": args.repository,
                    "commit": commit,
                    "path": destination.relative_to(root).as_posix(),
                    "bytes": size,
                    "sha256": digest,
                    "status": "downloaded",
                    "fetched_at": now_iso(),
                }

                manifest.add(record)
                downloaded += 1
                print(f"downloaded {relative.as_posix()} ({size} bytes)")

            print("\nRepository summary")
            print("------------------")
            print(f"Commit:     {commit}")
            print(f"Matched:    {len(files)}")
            print(f"Downloaded: {downloaded}")
            print(f"Skipped:    {skipped}")

            return 0

    except subprocess.CalledProcessError as exc:
        print(f"Git operation failed: {exc.stderr.strip()}")
        return 1
    except OSError as exc:
        print(f"Repository collection failed: {exc}")
        return 1


def run_manual(args: argparse.Namespace) -> int:
    """Collect one permitted local document."""
    if not args.permission_confirmed:
        print(
            "Manual collection refused: verify the document's reuse rights "
            "and pass --permission-confirmed."
        )
        return 1

    licence = args.licence.strip()

    if not approved_licence(licence):
        print("Manual collection refused: permission is not approved.")
        return 1

    try:
        source_file = Path(args.file).expanduser().resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        print(f"Manual collection failed: {exc}")
        return 1

    if not source_file.is_file():
        print(f"Not a regular file: {source_file}")
        return 1

    allowed_extensions = {
        ".pdf",
        ".txt",
        ".md",
        ".html",
        ".htm",
        ".docx",
        ".doc",
        ".rtf",
    }

    if source_file.suffix.lower() not in allowed_extensions:
        print(f"Unsupported document type: {source_file.suffix or '(no extension)'}")
        return 2

    root = Path.cwd()
    raw_dir = root / "data" / "raw" / slug(args.source)
    destination = raw_dir / source_file.name
    manifest_path = root / "data" / "manifest.jsonl"
    record_url = f"manual+{source_file.as_uri()}"

    manifest = Manifest(manifest_path)

    if manifest.done(record_url, root):
        print(f"Already collected; skipping: {destination}")
        return 0

    if destination.exists():
        print(f"Refusing to overwrite existing file: {destination}")
        return 1

    raw_dir.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".part")

    if temporary.exists():
        print(f"Temporary file already exists; refusing to overwrite: {temporary}")
        return 1

    try:
        shutil.copy2(source_file, temporary)
        digest = hashlib.sha256(temporary.read_bytes()).hexdigest()
        size = temporary.stat().st_size
        temporary.replace(destination)

        record = {
            "url": record_url,
            "source": args.source,
            "licence": licence,
            "title": source_file.name,
            "via": "manual",
            "path": destination.relative_to(root).as_posix(),
            "bytes": size,
            "sha256": digest,
            "status": "downloaded",
            "fetched_at": now_iso(),
        }

        manifest.add(record)

    except OSError as exc:
        print(f"Manual collection failed: {exc}")
        return 1

    finally:
        temporary.unlink(missing_ok=True)

    print("\nManual collection summary")
    print("-------------------------")
    print(f"Source:  {source_file}")
    print(f"Saved:   {destination.relative_to(root)}")
    print(f"Size:    {size} bytes")
    print(f"SHA-256: {digest}")
    print("Status:  downloaded")

    return 0


async def run_sitemap(args: argparse.Namespace) -> int:
    """Discover sitemap URLs and save them as unapproved candidates."""
    if not args.permission_confirmed:
        print(
            "Sitemap discovery refused: verify that automated sitemap "
            "access is permitted, then pass --permission-confirmed."
        )
        return 1

    try:
        extensions = validate_extensions(args.ext)
    except ValueError as exc:
        print(exc)
        return 2

    requested_path = args.path.strip("/")
    if requested_path and ".." in PurePosixPath(requested_path).parts:
        print("Invalid path filter.")
        return 2

    root = Path.cwd()
    candidates_path = root / "data" / "sitemap_candidates.csv"
    candidates_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        print(f"Reading sitemap: {args.sitemap}")
        discovered = await discover_sitemap(
            args.sitemap,
            delay=args.delay,
            max_sitemaps=args.max_sitemaps,
            limit=args.limit,
        )
    except (SitemapError, OSError, ValueError) as exc:
        print(f"Sitemap discovery stopped: {exc}")
        return 1

    filtered = []
    for url in discovered:
        parts = urlsplit(url)
        path = parts.path

        if requested_path and not (
            path.lstrip("/") == requested_path or path.lstrip("/").startswith(requested_path + "/")
        ):
            continue

        if Path(path).suffix.lower() not in extensions:
            continue

        filtered.append(url)

    existing: set[str] = set()
    if candidates_path.exists():
        with candidates_path.open("r", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                if row.get("url"):
                    existing.add(row["url"])

    new_urls = [url for url in filtered if url not in existing]

    fieldnames = ["url", "source", "licence", "title", "status"]
    needs_header = not candidates_path.exists() or candidates_path.stat().st_size == 0

    with candidates_path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if needs_header:
            writer.writeheader()

        for url in new_urls:
            writer.writerow(
                {
                    "url": url,
                    "source": args.source,
                    "licence": "Permission pending",
                    "title": Path(urlsplit(url).path).name or "Untitled",
                    "status": "discovery only",
                }
            )

    print("\nSitemap discovery summary")
    print("-------------------------")
    print(f"Discovered:       {len(discovered)}")
    print(f"After filtering:  {len(filtered)}")
    print(f"New candidates:   {len(new_urls)}")
    print(f"Already recorded: {len(filtered) - len(new_urls)}")
    print(f"Candidate file:   {candidates_path.relative_to(root)}")
    print("No document content was downloaded.")
    print("All candidates remain permission pending.")

    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line interface."""
    parser = argparse.ArgumentParser(description="Collect permitted NyayaSetu corpus sources.")

    subparsers = parser.add_subparsers(
        dest="door",
        required=True,
    )

    urls_parser = subparsers.add_parser(
        "urls",
        help="Download approved URLs from data/sources.csv.",
    )
    urls_parser.add_argument("--delay", type=float, default=2.0)
    urls_parser.add_argument("--max-concurrency", type=int, default=2)

    repo_parser = subparsers.add_parser(
        "repo",
        help="Collect permitted files from a Git repository.",
    )
    repo_parser.add_argument("repository", help="GitHub OWNER/REPO")
    repo_parser.add_argument("--local-path", default="")
    repo_parser.add_argument("--path", default="")
    repo_parser.add_argument(
        "--ext",
        nargs="+",
        default=[".md", ".pdf", ".txt"],
    )
    repo_parser.add_argument("--source", required=True)
    repo_parser.add_argument("--licence", required=True)
    repo_parser.add_argument("--ref", default="")
    repo_parser.add_argument(
        "--permission-confirmed",
        action="store_true",
        help="Confirm that repository content reuse rights were verified.",
    )

    manual_parser = subparsers.add_parser(
        "manual",
        help="Collect one permitted local document.",
    )
    manual_parser.add_argument("file", help="Path to the local document")
    manual_parser.add_argument("--source", required=True)
    manual_parser.add_argument("--licence", required=True)
    manual_parser.add_argument(
        "--permission-confirmed",
        action="store_true",
        help="Confirm that document reuse rights were verified.",
    )

    sitemap_parser = subparsers.add_parser(
        "sitemap",
        help="Discover URLs from a permitted XML sitemap.",
    )
    sitemap_parser.add_argument("sitemap", help="Sitemap XML URL")
    sitemap_parser.add_argument("--source", required=True)
    sitemap_parser.add_argument("--path", default="")
    sitemap_parser.add_argument(
        "--ext",
        nargs="+",
        default=[".pdf", ".html", ".htm"],
    )
    sitemap_parser.add_argument("--delay", type=float, default=2.0)
    sitemap_parser.add_argument("--limit", type=int, default=1000)
    sitemap_parser.add_argument("--max-sitemaps", type=int, default=20)
    sitemap_parser.add_argument(
        "--permission-confirmed",
        action="store_true",
        help="Confirm that automated sitemap access is permitted.",
    )

    return parser


def main() -> int:
    """Parse arguments and dispatch the selected collection door."""
    parser = build_parser()
    args = parser.parse_args()

    if args.door == "urls":
        if args.delay < 0:
            parser.error("--delay cannot be negative.")

        if not 1 <= args.max_concurrency <= 4:
            parser.error("--max-concurrency must be between 1 and 4.")

        return asyncio.run(run_urls(args))

    if args.door == "repo":
        return run_repo(args)

    if args.door == "manual":
        return run_manual(args)

    if args.door == "sitemap":
        if args.delay < 0:
            parser.error("--delay cannot be negative.")
        if args.limit < 1 or args.max_sitemaps < 1:
            parser.error("--limit and --max-sitemaps must be positive.")
        return asyncio.run(run_sitemap(args))

    parser.error(f"Unsupported collection door: {args.door}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
