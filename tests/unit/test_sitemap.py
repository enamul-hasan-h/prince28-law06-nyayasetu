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
