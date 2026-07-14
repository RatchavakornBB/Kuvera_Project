"""Real server-side URL fetching for NotebookLM-style "add a link" sources
(Chat page Sources panel). Fetches the actual page and extracts real
readable text via BeautifulSoup (strips script/style tags, keeps only
visible text) — this is the page's own real content, not a fabricated or
AI-generated summary.

SSRF note: this endpoint fetches arbitrary user-supplied URLs server-side,
so the target host is resolved and rejected up front if it's
private/loopback/link-local/reserved (blocks the common case of pointing
this at localhost, an internal service, or a cloud metadata endpoint like
169.254.169.254). The final URL after redirects is re-checked too. This is
a best-effort mitigation appropriate for a single-user local app, not an
exhaustive per-redirect-hop validator — a hop that only 302s through a
private host mid-chain before landing back on a public one would not be
caught, since httpx follows the whole chain before this code sees the
final response."""

import ipaddress
import socket
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

MAX_CONTENT_BYTES = 5 * 1024 * 1024  # 5MB — nowhere near what a real article/page needs
REQUEST_TIMEOUT_SECONDS = 15.0
USER_AGENT = "Mozilla/5.0 (compatible; KuveraCapitalBot/1.0; +internal deal-ops research tool)"


class UnsafeUrlError(ValueError):
    pass


def _assert_public_host(hostname: str) -> None:
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as e:
        raise UnsafeUrlError(f"Could not resolve host: {hostname}") from e
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise UnsafeUrlError(f"URL resolves to a non-public address ({ip}) — refusing to fetch")


def fetch_url_as_text(url: str) -> tuple[str, str]:
    """Returns (title, extracted_text). Raises UnsafeUrlError/ValueError on
    any real failure (bad scheme, unresolvable/private host, non-HTML
    content, oversized response, HTTP error) — no silent fallback to an
    empty or fabricated result."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Unsupported URL scheme: {parsed.scheme!r} (only http/https)")
    if not parsed.hostname:
        raise ValueError("URL has no hostname")
    _assert_public_host(parsed.hostname)

    with httpx.Client(
        follow_redirects=True,
        timeout=REQUEST_TIMEOUT_SECONDS,
        headers={"User-Agent": USER_AGENT},
        max_redirects=5,
    ) as client:
        with client.stream("GET", url) as response:
            if response.url.host:
                _assert_public_host(response.url.host)

            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            if "html" not in content_type and "text" not in content_type:
                raise ValueError(f"URL did not return HTML/text content (got {content_type!r})")

            chunks: list[bytes] = []
            total = 0
            for chunk in response.iter_bytes():
                total += len(chunk)
                if total > MAX_CONTENT_BYTES:
                    raise ValueError(f"Page content exceeds {MAX_CONTENT_BYTES // (1024 * 1024)}MB limit")
                chunks.append(chunk)
            raw = b"".join(chunks)

    soup = BeautifulSoup(raw, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    title = soup.title.get_text(strip=True) if soup.title and soup.title.get_text(strip=True) else parsed.hostname
    text = soup.get_text(separator="\n")
    cleaned = "\n".join(line.strip() for line in text.splitlines() if line.strip())

    if not cleaned:
        raise ValueError("No readable text content found on the page")

    return title, cleaned
