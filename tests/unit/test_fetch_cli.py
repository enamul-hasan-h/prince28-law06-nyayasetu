"""Offline tests for the corpus collection CLI."""

import importlib.util
import json
import subprocess
from pathlib import Path

CLI_PATH = Path(__file__).resolve().parents[2] / "scripts" / "fetch.py"

SPEC = importlib.util.spec_from_file_location("nyayasetu_fetch_cli", CLI_PATH)
CLI = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CLI)

main = CLI.main


def create_git_repo(path: Path) -> str:
    """Create a small local Git repository for testing."""
    path.mkdir(parents=True)

    (path / "docs").mkdir()
    (path / "docs" / "act.md").write_text("Test Act document", encoding="utf-8")
    (path / "docs" / "scheme.md").write_text("Test Scheme document", encoding="utf-8")
    (path / "docs" / "sample.pdf").write_text("PDF placeholder", encoding="utf-8")

    subprocess.run(["git", "init", str(path)], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(path), "add", "."],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(path),
            "-c",
            "user.name=NyayaSetu Test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "-m",
            "Create test fixture",
        ],
        check=True,
        capture_output=True,
    )

    return subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def run_repo_command(
    monkeypatch,
    tmp_path: Path,
    repository: Path,
    extra_args: list[str] | None = None,
) -> int:
    """Run the repository CLI against a local test repository."""
    monkeypatch.chdir(tmp_path)

    args = [
        "fetch.py",
        "repo",
        "local/testrepo",
        "--local-path",
        str(repository),
        "--path",
        "docs",
        "--ext",
        ".md",
        "--source",
        "Local synthetic test fixture",
        "--licence",
        "MIT (synthetic test fixture only)",
        "--permission-confirmed",
    ]

    if extra_args:
        args.extend(extra_args)

    monkeypatch.setattr("sys.argv", args)
    return main()


def test_repo_downloads_matching_files(monkeypatch, tmp_path, capsys):
    """Only files matching the requested extension are downloaded."""
    repository = tmp_path / "fixture"
    commit = create_git_repo(repository)

    result = run_repo_command(monkeypatch, tmp_path, repository)

    assert result == 0

    raw = tmp_path / "data" / "raw" / "local-synthetic-test-fixture" / "docs"

    assert (raw / "act.md").read_text(encoding="utf-8") == ("Test Act document")
    assert (raw / "scheme.md").read_text(encoding="utf-8") == ("Test Scheme document")
    assert not (raw / "sample.pdf").exists()

    output = capsys.readouterr().out
    assert f"Commit:     {commit}" in output
    assert "Matched:    2" in output
    assert "Downloaded: 2" in output


def test_repo_resume_skips_existing_files(monkeypatch, tmp_path, capsys):
    """A second run skips files already recorded in the manifest."""
    repository = tmp_path / "fixture"
    create_git_repo(repository)

    assert run_repo_command(monkeypatch, tmp_path, repository) == 0
    capsys.readouterr()

    assert run_repo_command(monkeypatch, tmp_path, repository) == 0

    output = capsys.readouterr().out
    assert "Downloaded: 0" in output
    assert "Skipped:    2" in output


def test_repo_records_manifest_metadata(monkeypatch, tmp_path):
    """Manifest records include commit, size, hash and source metadata."""
    repository = tmp_path / "fixture"
    commit = create_git_repo(repository)

    assert run_repo_command(monkeypatch, tmp_path, repository) == 0

    manifest = tmp_path / "data" / "manifest.jsonl"
    records = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines()]

    assert len(records) == 2

    for record in records:
        assert record["commit"] == commit
        assert record["via"] == "git"
        assert record["status"] == "downloaded"
        assert record["bytes"] > 0
        assert len(record["sha256"]) == 64
        assert record["licence"] == "MIT (synthetic test fixture only)"


def test_repo_refuses_without_permission_confirmation(monkeypatch, tmp_path, capsys):
    """Repository collection requires explicit permission confirmation."""
    repository = tmp_path / "fixture"
    create_git_repo(repository)
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(
        "sys.argv",
        [
            "fetch.py",
            "repo",
            "local/testrepo",
            "--local-path",
            str(repository),
            "--source",
            "Test",
            "--licence",
            "MIT",
        ],
    )

    assert main() == 1
    assert "collection refused" in capsys.readouterr().out


def test_repo_refuses_pending_permission(monkeypatch, tmp_path, capsys):
    """Permission-pending sources must not be collected."""
    repository = tmp_path / "fixture"
    create_git_repo(repository)
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(
        "sys.argv",
        [
            "fetch.py",
            "repo",
            "local/testrepo",
            "--local-path",
            str(repository),
            "--source",
            "Test",
            "--licence",
            "Permission pending",
            "--permission-confirmed",
        ],
    )

    assert main() == 1
    assert "permission is not approved" in capsys.readouterr().out


def test_repo_leaves_no_part_files(monkeypatch, tmp_path):
    """Successful collection must not leave temporary partial files."""
    repository = tmp_path / "fixture"
    create_git_repo(repository)

    assert run_repo_command(monkeypatch, tmp_path, repository) == 0

    raw = tmp_path / "data" / "raw"
    assert list(raw.rglob("*.part")) == []


def run_sitemap_command(
    monkeypatch,
    tmp_path: Path,
    urls: list[str],
    extra_args: list[str] | None = None,
) -> int:
    """Run sitemap CLI with mocked, offline discovery."""

    async def fake_discover(*args, **kwargs):
        return urls

    monkeypatch.setattr(CLI, "discover_sitemap", fake_discover)
    monkeypatch.chdir(tmp_path)

    args = [
        "fetch.py",
        "sitemap",
        "https://example.test/sitemap.xml",
        "--source",
        "Synthetic sitemap fixture",
        "--path",
        "docs",
        "--ext",
        ".pdf",
        "--permission-confirmed",
    ]

    if extra_args:
        args.extend(extra_args)

    monkeypatch.setattr("sys.argv", args)
    return main()


def test_sitemap_refuses_without_permission_confirmation(monkeypatch, tmp_path, capsys):
    """Sitemap discovery requires explicit permission confirmation."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sys.argv",
        [
            "fetch.py",
            "sitemap",
            "https://example.test/sitemap.xml",
            "--source",
            "Synthetic fixture",
        ],
    )

    assert main() == 1
    assert "Sitemap discovery refused" in capsys.readouterr().out


def test_sitemap_filters_and_records_pending_candidates(monkeypatch, tmp_path, capsys):
    """Only matching URLs are recorded, without downloading documents."""
    urls = [
        "https://example.test/docs/act.pdf",
        "https://example.test/docs/nested/scheme.pdf",
        "https://example.test/docs/page.html",
        "https://example.test/other/act.pdf",
    ]

    assert run_sitemap_command(monkeypatch, tmp_path, urls) == 0

    candidate_file = tmp_path / "data" / "sitemap_candidates.csv"

    import csv

    with candidate_file.open("r", encoding="utf-8", newline="") as handle:
        records = list(csv.DictReader(handle))

    assert len(records) == 2
    assert {record["url"] for record in records} == {
        urls[0],
        urls[1],
    }

    for record in records:
        assert record["source"] == "Synthetic sitemap fixture"
        assert record["licence"] == "Permission pending"
        assert record["status"] == "discovery only"

    output = capsys.readouterr().out
    assert "New candidates:   2" in output
    assert "No document content was downloaded." in output


def test_sitemap_rerun_does_not_duplicate_candidates(monkeypatch, tmp_path, capsys):
    """Repeated discovery does not duplicate candidate CSV entries."""
    urls = [
        "https://example.test/docs/act.pdf",
        "https://example.test/docs/scheme.pdf",
    ]

    assert run_sitemap_command(monkeypatch, tmp_path, urls) == 0
    capsys.readouterr()

    assert run_sitemap_command(monkeypatch, tmp_path, urls) == 0

    output = capsys.readouterr().out
    assert "New candidates:   0" in output
    assert "Already recorded: 2" in output

    candidate_file = tmp_path / "data" / "sitemap_candidates.csv"

    import csv

    with candidate_file.open("r", encoding="utf-8", newline="") as handle:
        records = list(csv.DictReader(handle))

    assert len(records) == 2


def run_manual_command(
    monkeypatch,
    tmp_path: Path,
    source_file: Path,
    extra_args: list[str] | None = None,
) -> int:
    """Run manual collection against an isolated temporary directory."""
    monkeypatch.chdir(tmp_path)

    args = [
        "fetch.py",
        "manual",
        str(source_file),
        "--source",
        "Synthetic manual fixture",
        "--licence",
        "MIT (synthetic test fixture only)",
        "--permission-confirmed",
    ]

    if extra_args:
        args.extend(extra_args)

    monkeypatch.setattr("sys.argv", args)
    return main()


def test_manual_collects_file_and_records_metadata(monkeypatch, tmp_path, capsys):
    """Manual collection copies a document and records its metadata."""
    import hashlib

    source_file = tmp_path / "input" / "act.md"
    source_file.parent.mkdir()
    content = "Synthetic Act document"
    source_file.write_text(content, encoding="utf-8")

    assert run_manual_command(monkeypatch, tmp_path, source_file) == 0

    destination = tmp_path / "data" / "raw" / "synthetic-manual-fixture" / "act.md"

    assert destination.read_text(encoding="utf-8") == content

    manifest = tmp_path / "data" / "manifest.jsonl"
    records = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines()]

    assert len(records) == 1

    record = records[0]
    assert record["via"] == "manual"
    assert record["status"] == "downloaded"
    assert record["source"] == "Synthetic manual fixture"
    assert record["licence"] == "MIT (synthetic test fixture only)"
    assert record["path"] == destination.relative_to(tmp_path).as_posix()
    assert record["bytes"] == len(content.encode("utf-8"))
    assert record["sha256"] == hashlib.sha256(content.encode("utf-8")).hexdigest()

    assert "Status:  downloaded" in capsys.readouterr().out


def test_manual_resume_skips_existing_manifest_record(monkeypatch, tmp_path, capsys):
    """A repeated manual collection skips an already recorded document."""
    source_file = tmp_path / "input" / "act.md"
    source_file.parent.mkdir()
    source_file.write_text("Synthetic Act document", encoding="utf-8")

    assert run_manual_command(monkeypatch, tmp_path, source_file) == 0
    capsys.readouterr()

    assert run_manual_command(monkeypatch, tmp_path, source_file) == 0

    assert "Already collected; skipping" in capsys.readouterr().out

    manifest = tmp_path / "data" / "manifest.jsonl"
    records = manifest.read_text(encoding="utf-8").splitlines()
    assert len(records) == 1


def test_manual_refuses_without_permission_confirmation(monkeypatch, tmp_path, capsys):
    """Manual collection requires explicit permission confirmation."""
    source_file = tmp_path / "act.md"
    source_file.write_text("Synthetic Act document", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(
        "sys.argv",
        [
            "fetch.py",
            "manual",
            str(source_file),
            "--source",
            "Synthetic fixture",
            "--licence",
            "MIT",
        ],
    )

    assert main() == 1
    assert "Manual collection refused" in capsys.readouterr().out


def test_manual_refuses_pending_permission(monkeypatch, tmp_path, capsys):
    """Manual collection rejects permission-pending documents."""
    source_file = tmp_path / "act.md"
    source_file.write_text("Synthetic Act document", encoding="utf-8")

    assert (
        run_manual_command(
            monkeypatch,
            tmp_path,
            source_file,
            ["--licence", "Permission pending"],
        )
        == 1
    )

    assert "permission is not approved" in capsys.readouterr().out
    assert not (tmp_path / "data" / "manifest.jsonl").exists()


def test_manual_refuses_missing_file(monkeypatch, tmp_path, capsys):
    """Manual collection rejects a missing local document."""
    missing_file = tmp_path / "missing.md"

    assert run_manual_command(monkeypatch, tmp_path, missing_file) == 1
    assert "Manual collection failed" in capsys.readouterr().out


def test_manual_refuses_unsupported_file_type(monkeypatch, tmp_path, capsys):
    """Manual collection accepts only supported document extensions."""
    source_file = tmp_path / "program.exe"
    source_file.write_text("Synthetic fixture", encoding="utf-8")

    assert run_manual_command(monkeypatch, tmp_path, source_file) == 2
    assert "Unsupported document type" in capsys.readouterr().out


def test_manual_refuses_to_overwrite_existing_file(monkeypatch, tmp_path, capsys):
    """Manual collection never overwrites an unrecorded destination."""
    first_file = tmp_path / "first" / "act.md"
    second_file = tmp_path / "second" / "act.md"
    first_file.parent.mkdir()
    second_file.parent.mkdir()
    first_file.write_text("First synthetic document", encoding="utf-8")
    second_file.write_text("Second synthetic document", encoding="utf-8")

    assert run_manual_command(monkeypatch, tmp_path, first_file) == 0

    assert run_manual_command(monkeypatch, tmp_path, second_file) == 1
    assert "Refusing to overwrite existing file" in capsys.readouterr().out

    destination = tmp_path / "data" / "raw" / "synthetic-manual-fixture" / "act.md"
    assert destination.read_text(encoding="utf-8") == "First synthetic document"


def test_manual_leaves_no_part_files(monkeypatch, tmp_path):
    """Successful manual collection leaves no temporary partial files."""
    source_file = tmp_path / "act.md"
    source_file.write_text("Synthetic Act document", encoding="utf-8")

    assert run_manual_command(monkeypatch, tmp_path, source_file) == 0

    raw = tmp_path / "data" / "raw"
    assert list(raw.rglob("*.part")) == []
