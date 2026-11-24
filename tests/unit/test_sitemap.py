import httpx
import pytest

from nyayasetu.ingest.sitemap import SitemapError, discover_sitemap


@pytest.mark.asyncio
async def test_discovers_urls_from_sitemap():
    sitemap = """<?xml version="1.0"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url><loc>https://example.org/docs/act.pdf</loc></url>
        <url><loc>https://example.org/docs/scheme.pdf</loc></url>
    </urlset>"""

    async def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        if request.url.path == "/sitemap.xml":
            return httpx.Response(200, text=sitemap)
        return httpx.Response(404)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await discover_sitemap(
            "https://example.org/sitemap.xml",
            client=client,
            delay=0,
        )

    assert result == [
        "https://example.org/docs/act.pdf",
        "https://example.org/docs/scheme.pdf",
    ]


@pytest.mark.asyncio
async def test_discovers_urls_from_sitemap_index():
    index = """<sitemapindex>
        <sitemap><loc>https://example.org/part.xml</loc></sitemap>
    </sitemapindex>"""

    child = """<urlset>
        <url><loc>https://example.org/docs/act.pdf</loc></url>
    </urlset>"""

    async def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        if request.url.path == "/sitemap.xml":
            return httpx.Response(200, text=index)
        if request.url.path == "/part.xml":
            return httpx.Response(200, text=child)
        return httpx.Response(404)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await discover_sitemap(
            "https://example.org/sitemap.xml",
            client=client,
            delay=0,
        )

    assert result == ["https://example.org/docs/act.pdf"]


@pytest.mark.asyncio
async def test_robots_disallowed_document_is_excluded():
    sitemap = """<urlset>
        <url><loc>https://example.org/public/act.pdf</loc></url>
        <url><loc>https://example.org/private/file.pdf</loc></url>
    </urlset>"""

    async def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(
                200,
                text="User-agent: *\nDisallow: /private/\n",
            )
        if request.url.path == "/sitemap.xml":
            return httpx.Response(200, text=sitemap)
        return httpx.Response(404)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await discover_sitemap(
            "https://example.org/sitemap.xml",
            client=client,
            delay=0,
        )

    assert result == ["https://example.org/public/act.pdf"]


@pytest.mark.asyncio
async def test_duplicate_urls_are_returned_once():
    sitemap = """<urlset>
        <url><loc>https://example.org/act.pdf</loc></url>
        <url><loc>https://example.org/act.pdf</loc></url>
    </urlset>"""

    async def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        if request.url.path == "/sitemap.xml":
            return httpx.Response(200, text=sitemap)
        return httpx.Response(404)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await discover_sitemap(
            "https://example.org/sitemap.xml",
            client=client,
            delay=0,
        )

    assert result == ["https://example.org/act.pdf"]


@pytest.mark.asyncio
async def test_invalid_xml_is_rejected():
    async def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        if request.url.path == "/sitemap.xml":
            return httpx.Response(200, text="<urlset><broken>")
        return httpx.Response(404)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(SitemapError, match="Invalid sitemap XML"):
            await discover_sitemap(
                "https://example.org/sitemap.xml",
                client=client,
                delay=0,
            )


@pytest.mark.asyncio
async def test_invalid_sitemap_url_is_rejected():
    with pytest.raises(SitemapError, match="valid HTTP"):
        await discover_sitemap("file:///private/sitemap.xml")


@pytest.mark.asyncio
async def test_robots_failure_stops_discovery():
    async def handler(request):
        raise httpx.ConnectError("Connection failed", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(SitemapError, match="not permitted"):
            await discover_sitemap(
                "https://example.org/sitemap.xml",
                client=client,
                delay=0,
            )


@pytest.mark.parametrize(
    "url",
    [
        "ftp://example.org/sitemap.xml",
        "https://{}:{}@example.org/sitemap.xml".format("user", "pass"),
        "https:///sitemap.xml",
    ],
)
@pytest.mark.asyncio
async def test_rejects_unsafe_sitemap_urls(url):
    with pytest.raises(SitemapError, match="valid HTTP"):
        await discover_sitemap(url)


@pytest.mark.parametrize(
    "options",
    [
        {"delay": -1},
        {"max_sitemaps": 0},
        {"limit": 0},
    ],
)
@pytest.mark.asyncio
async def test_rejects_invalid_discovery_limits(options):
    with pytest.raises(SitemapError, match="Invalid discovery limits"):
        await discover_sitemap("https://example.org/sitemap.xml", **options)


@pytest.mark.asyncio
async def test_rejects_unsupported_sitemap_root():
    async def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        return httpx.Response(200, text="<feed><entry /></feed>")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(SitemapError, match="Unsupported sitemap root"):
            await discover_sitemap(
                "https://example.org/sitemap.xml",
                client=client,
                delay=0,
            )


@pytest.mark.asyncio
async def test_wraps_http_errors_as_sitemap_errors():
    async def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        return httpx.Response(404)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(SitemapError, match="Could not retrieve sitemap"):
            await discover_sitemap(
                "https://example.org/sitemap.xml",
                client=client,
                delay=0,
            )


@pytest.mark.asyncio
async def test_sitemap_index_respects_max_sitemaps_limit():
    index = """<sitemapindex>
        <sitemap><loc>https://example.org/part.xml</loc></sitemap>
    </sitemapindex>"""

    async def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        return httpx.Response(200, text=index)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(SitemapError, match="Sitemap limit reached"):
            await discover_sitemap(
                "https://example.org/sitemap.xml",
                client=client,
                delay=0,
                max_sitemaps=1,
            )


@pytest.mark.asyncio
async def test_sitemap_skips_invalid_and_duplicate_locations():
    sitemap = """<urlset>
        <url><loc>not-a-url</loc></url>
        <url><loc>https://example.org/act.pdf</loc></url>
        <url><loc>https://example.org/act.pdf</loc></url>
    </urlset>"""

    async def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        return httpx.Response(200, text=sitemap)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await discover_sitemap(
            "https://example.org/sitemap.xml",
            client=client,
            delay=0,
        )

    assert result == ["https://example.org/act.pdf"]


@pytest.mark.asyncio
async def test_sitemap_stops_when_candidate_limit_is_reached():
    sitemap = """<urlset>
        <url><loc>https://example.org/one.pdf</loc></url>
        <url><loc>https://example.org/two.pdf</loc></url>
    </urlset>"""

    async def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        return httpx.Response(200, text=sitemap)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await discover_sitemap(
            "https://example.org/sitemap.xml",
            client=client,
            delay=0,
            limit=1,
        )

    assert result == ["https://example.org/one.pdf"]
