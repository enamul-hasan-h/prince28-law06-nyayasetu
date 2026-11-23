"""Robots-aware sitemap discovery for NyayaSetu."""

import asyncio
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit

import httpx

from nyayasetu.ingest.fetch import HostGate, Robots, make_client


class SitemapError(Exception):
    """Raised when sitemap discovery cannot safely continue."""


def _valid_http_url(url: str) -> bool:
    parts = urlsplit(url)
    return (
        parts.scheme in {"http", "https"}
        and bool(parts.netloc)
        and not parts.username
        and not parts.password
    )


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


async def discover_sitemap(
    sitemap_url: str,
    *,
    client: httpx.AsyncClient | None = None,
    delay: float = 2.0,
    max_sitemaps: int = 20,
    limit: int = 1000,
) -> list[str]:
    """Discover permitted document URLs without downloading documents."""
    if not _valid_http_url(sitemap_url):
        raise SitemapError("A valid HTTP(S) sitemap URL is required.")

    if delay < 0 or max_sitemaps < 1 or limit < 1:
        raise SitemapError("Invalid discovery limits.")

    own_client = client is None
    client = client or make_client(max_concurrency=1)
    robots = Robots(client)
    gate = HostGate(delay, asyncio.sleep)

    queue = [sitemap_url]
    visited: set[str] = set()
    candidates: list[str] = []
    candidate_set: set[str] = set()

    try:
        while queue and len(visited) < max_sitemaps:
            current = queue.pop(0)

            if current in visited:
                continue
            visited.add(current)

            allowed, crawl_delay = await robots.check(current)
            if not allowed:
                raise SitemapError(f"Sitemap is not permitted by robots.txt: {current}")

            parts = urlsplit(current)
            await gate.wait(parts.netloc.lower(), crawl_delay)

            try:
                response = await client.get(current)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise SitemapError(f"Could not retrieve sitemap {current}: {exc}") from exc

            try:
                root = ET.fromstring(response.content)
            except ET.ParseError as exc:
                raise SitemapError(f"Invalid sitemap XML: {current}") from exc

            root_type = _local_name(root.tag)

            if root_type not in {"urlset", "sitemapindex"}:
                raise SitemapError(f"Unsupported sitemap root element: {root_type}")

            for element in root.iter():
                if _local_name(element.tag) != "loc" or not element.text:
                    continue

                discovered = element.text.strip()
                if not _valid_http_url(discovered):
                    continue

                if root_type == "sitemapindex":
                    if discovered not in visited and discovered not in queue:
                        queue.append(discovered)
                    continue

                if discovered in candidate_set:
                    continue

                permitted, _ = await robots.check(discovered)
                if permitted:
                    candidate_set.add(discovered)
                    candidates.append(discovered)

                if len(candidates) >= limit:
                    return candidates

        if queue and len(visited) >= max_sitemaps:
            raise SitemapError(
                f"Sitemap limit reached ({max_sitemaps}); "
                "discovery stopped before all sitemaps were checked."
            )

        return candidates

    finally:
        if own_client:
            await client.aclose()
