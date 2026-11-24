"""Unit tests for the polite, resumable corpus downloader."""

import hashlib
import json

import httpx
import pytest

from nyayasetu.ingest.fetch import (
    DownloadError,
    Manifest,
    Robots,
    Source,
    _download,
    backoff_delay,
    fetch_all,
    file_stem,
    pick_ext,
    read_sources,
    retry_after_seconds,
    slug,
)

pytestmark = pytest.mark.unit


def test_slug_creates_safe_filename():
    assert slug("Legal Services Act 1987!") == "legal-services-act-1987"


def test_file_stem_is_stable():
    url = "https://example.org/documents/Act.pdf"
    assert file_stem(url) == file_stem(url)
    assert file_stem(url).startswith("act-")


def test_pick_ext_uses_url_extension():
    assert pick_ext("https://example.org/file.pdf", "") == ".pdf"


def test_pick_ext_uses_content_type():
    assert pick_ext("https://example.org/file", "application/pdf") == ".pdf"


def test_backoff_delay_stays_within_cap(monkeypatch):
    monkeypatch.setattr(
        "nyayasetu.ingest.fetch.random.uniform",
        lambda low, high: high,
    )
    assert backoff_delay(5, cap=10) == 10


def test_retry_after_parses_seconds():
    assert retry_after_seconds("15") == 15.0


def test_retry_after_rejects_invalid_value():
    assert retry_after_seconds("not-a-date") is None


def test_read_sources_accepts_authorised_source_and_removes_duplicates(tmp_path):
    path = tmp_path / "sources.csv"
    path.write_text(
        "url,source,licence,title\n"
        "https://example.org/a.pdf,Example,CC BY 4.0,Document A\n"
        "https://example.org/a.pdf,Example,CC BY 4.0,Document A\n",
        encoding="utf-8",
    )

    sources = read_sources(path)

    assert len(sources) == 1
    assert sources[0].source == "Example"
    assert sources[0].licence == "CC BY 4.0"


def test_read_sources_rejects_invalid_url(tmp_path):
    path = tmp_path / "sources.csv"
    path.write_text(
        "url,source,licence,title\nftp://example.org/a.pdf,Example,CC BY 4.0,Document A\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="not an http"):
        read_sources(path)


def test_read_sources_rejects_missing_licence(tmp_path):
    path = tmp_path / "sources.csv"
    path.write_text(
        "url,source,licence,title\nhttps://example.org/a.pdf,Example,,Document A\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="source and licence are required"):
        read_sources(path)


def test_read_sources_rejects_pending_permission(tmp_path):
    path = tmp_path / "sources.csv"
    path.write_text(
        "url,source,licence,title\n"
        "https://nalsa.gov.in/example.pdf,NALSA,Permission pending,Document A\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="permission is not approved"):
        read_sources(path)


def test_manifest_add_and_done(tmp_path):
    root = tmp_path
    document = root / "data" / "raw" / "example" / "document.pdf"
    document.parent.mkdir(parents=True)
    document.write_bytes(b"sample")

    manifest = Manifest(root / "data" / "manifest.jsonl")
    record = {
        "url": "https://example.org/document.pdf",
        "status": "downloaded",
        "path": "data/raw/example/document.pdf",
    }

    manifest.add(record)

    assert manifest.done(record["url"], root)
    assert len((root / "data" / "manifest.jsonl").read_text().splitlines()) == 1


def test_manifest_ignores_broken_line_and_repairs_final_newline(tmp_path):
    path = tmp_path / "manifest.jsonl"
    record = {
        "url": "https://example.org/a.pdf",
        "status": "failed",
    }

    path.write_text(
        json.dumps(record) + "\n" + '{"broken":',
        encoding="utf-8",
    )

    manifest = Manifest(path)

    assert record["url"] in manifest.records
    assert path.read_text(encoding="utf-8").endswith("\n")


@pytest.mark.asyncio
async def test_robots_allows_permitted_url_and_reads_delay():
    async def handler(request):
        return httpx.Response(
            200,
            text="User-agent: *\nCrawl-delay: 2\n",
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        robots = Robots(client)
        allowed, delay = await robots.check("https://example.org/public/file.pdf")

    assert allowed is True
    assert delay == 2.0


@pytest.mark.asyncio
async def test_robots_blocks_disallowed_url():
    async def handler(request):
        return httpx.Response(
            200,
            text="User-agent: *\nDisallow: /private/\n",
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        robots = Robots(client)
        allowed, _ = await robots.check("https://example.org/private/file.pdf")

    assert allowed is False


@pytest.mark.asyncio
async def test_robots_fails_closed_when_unreachable():
    async def handler(request):
        raise httpx.ConnectError("Connection failed", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        robots = Robots(client)
        allowed, _ = await robots.check("https://example.org/file.pdf")

    assert allowed is False


@pytest.mark.asyncio
async def test_download_saves_file_and_calculates_hash(tmp_path):
    content = b"NyayaSetu test document"

    async def handler(request):
        return httpx.Response(
            200,
            headers={"Content-Type": "application/pdf"},
            content=content,
        )

    source = Source(
        url="https://example.org/document.pdf",
        source="Example",
        licence="CC BY 4.0",
        title="Test document",
    )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await _download(
            client,
            source,
            tmp_path,
            tmp_path / "data" / "raw",
        )

    saved_file = tmp_path / result["path"]

    assert saved_file.read_bytes() == content
    assert result["sha256"] == hashlib.sha256(content).hexdigest()
    assert result["bytes"] == len(content)
    assert not saved_file.with_name(saved_file.name + ".part").exists()


@pytest.mark.asyncio
async def test_download_rejects_non_200_response(tmp_path):
    async def handler(request):
        return httpx.Response(404, text="Not found")

    source = Source(
        url="https://example.org/missing.pdf",
        source="Example",
        licence="CC BY 4.0",
    )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(DownloadError, match="HTTP 404"):
            await _download(
                client,
                source,
                tmp_path,
                tmp_path / "data" / "raw",
            )


@pytest.mark.asyncio
async def test_fetch_all_skips_completed_download(tmp_path):
    source = Source(
        url="https://example.org/document.pdf",
        source="Example",
        licence="CC BY 4.0",
    )

    document = tmp_path / "data" / "raw" / "example" / "document.pdf"
    document.parent.mkdir(parents=True)
    document.write_bytes(b"already downloaded")

    manifest = Manifest(tmp_path / "data" / "manifest.jsonl")
    manifest.add(
        {
            "url": source.url,
            "status": "downloaded",
            "path": "data/raw/example/document.pdf",
        }
    )

    requests = []

    async def handler(request):
        requests.append(request)
        return httpx.Response(200)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        counts = await fetch_all(
            [source],
            root=tmp_path,
            client=client,
        )

    assert counts["skipped"] == 1
    assert counts["downloaded"] == 0
    assert requests == []


@pytest.mark.asyncio
async def test_robots_returns_fail_closed_for_server_error():
    async def handler(request):
        return httpx.Response(503)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        allowed, delay = await Robots(client).check("https://example.org/file.pdf")

    assert allowed is False
    assert delay == 0.0


@pytest.mark.asyncio
async def test_robots_treats_missing_robots_as_no_restrictions():
    async def handler(request):
        return httpx.Response(404)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        allowed, _ = await Robots(client).check("https://example.org/file.pdf")

    assert allowed is True


@pytest.mark.asyncio
async def test_host_gate_waits_when_host_is_still_throttled(monkeypatch):
    from nyayasetu.ingest import fetch

    moments = iter([100.0, 100.0, 105.0, 105.0])
    monkeypatch.setattr(fetch.time, "monotonic", lambda: next(moments, 105.0))
    pauses = []

    async def fake_sleep(seconds):
        pauses.append(seconds)

    gate = fetch.HostGate(10.0, fake_sleep)
    await gate.wait("example.org")
    await gate.wait("example.org")

    assert pauses == [5.0]


@pytest.mark.asyncio
async def test_download_removes_partial_file_when_size_limit_is_exceeded(tmp_path, monkeypatch):
    from nyayasetu.ingest import fetch

    monkeypatch.setattr(fetch, "MAX_BYTES", 5)

    async def handler(request):
        return httpx.Response(
            200,
            headers={"Content-Type": "application/pdf"},
            content=b"123456",
        )

    source = Source(
        url="https://example.org/large.pdf",
        source="Example",
        licence="CC BY 4.0",
    )
    raw_dir = tmp_path / "data" / "raw"

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(DownloadError, match="larger than"):
            await _download(client, source, tmp_path, raw_dir)

    target_dir = raw_dir / "example"
    assert not list(target_dir.glob("*.part"))


@pytest.mark.asyncio
async def test_fetch_one_returns_blocked_record_for_disallowed_url():
    import asyncio

    async def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /\n")
        return httpx.Response(200, content=b"document")

    source = Source("https://example.org/file.pdf", "Example", "CC BY 4.0")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        from nyayasetu.ingest.fetch import HostGate, fetch_one

        result = await fetch_one(
            client,
            source,
            root=__import__("pathlib").Path("."),
            raw_dir=__import__("pathlib").Path("data/raw"),
            robots=Robots(client),
            gate=HostGate(0, asyncio.sleep),
            slots=asyncio.Semaphore(1),
            max_attempts=2,
            sleep=asyncio.sleep,
        )

    assert result["status"] == "blocked"
    assert result["error"] == "robots.txt"


@pytest.mark.asyncio
async def test_fetch_one_downloads_permitted_source(tmp_path):
    import asyncio

    from nyayasetu.ingest.fetch import HostGate, fetch_one

    async def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        return httpx.Response(
            200,
            headers={"Content-Type": "application/pdf"},
            content=b"legal document",
        )

    source = Source("https://example.org/file.pdf", "Example", "CC BY 4.0")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await fetch_one(
            client,
            source,
            root=tmp_path,
            raw_dir=tmp_path / "data" / "raw",
            robots=Robots(client),
            gate=HostGate(0, asyncio.sleep),
            slots=asyncio.Semaphore(1),
            max_attempts=2,
            sleep=asyncio.sleep,
        )

    assert result["status"] == "downloaded"
    assert result["attempts"] == 1
    assert (tmp_path / result["path"]).read_bytes() == b"legal document"


@pytest.mark.asyncio
async def test_fetch_one_stops_retrying_non_retryable_http_error(tmp_path):
    import asyncio

    from nyayasetu.ingest.fetch import HostGate, fetch_one

    async def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        return httpx.Response(404)

    source = Source("https://example.org/missing.pdf", "Example", "CC BY 4.0")
    sleeps = []

    async def fake_sleep(seconds):
        sleeps.append(seconds)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await fetch_one(
            client,
            source,
            root=tmp_path,
            raw_dir=tmp_path / "data" / "raw",
            robots=Robots(client),
            gate=HostGate(0, fake_sleep),
            slots=asyncio.Semaphore(1),
            max_attempts=3,
            sleep=fake_sleep,
        )

    assert result["status"] == "failed"
    assert result["http_status"] == 404
    assert result["attempts"] == 1
    assert sleeps == []


@pytest.mark.asyncio
async def test_fetch_one_retries_server_error_then_succeeds(tmp_path, monkeypatch):
    import asyncio

    from nyayasetu.ingest import fetch
    from nyayasetu.ingest.fetch import HostGate, fetch_one

    monkeypatch.setattr(fetch, "backoff_delay", lambda attempt: 0.0)
    requests = []

    async def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        requests.append(request)
        if len(requests) == 1:
            return httpx.Response(503)
        return httpx.Response(200, content=b"recovered")

    source = Source("https://example.org/file.pdf", "Example", "CC BY 4.0")
    sleeps = []

    async def fake_sleep(seconds):
        sleeps.append(seconds)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await fetch_one(
            client,
            source,
            root=tmp_path,
            raw_dir=tmp_path / "data" / "raw",
            robots=Robots(client),
            gate=HostGate(0, fake_sleep),
            slots=asyncio.Semaphore(1),
            max_attempts=2,
            sleep=fake_sleep,
        )

    assert result["status"] == "downloaded"
    assert result["attempts"] == 2
    assert len(requests) == 2
    assert len(sleeps) == 1
