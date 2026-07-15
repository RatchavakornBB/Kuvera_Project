"""Real server-side URL fetching for NotebookLM-style "add a link" sources
(Chat page Sources panel). Handles two real content shapes, not just HTML:

- HTML/text pages: extracts real readable text via BeautifulSoup (strips
  script/style tags, keeps only visible text) — the page's own real
  content, not a fabricated or AI-generated summary.
- A URL that points directly at a file Claude can read natively (PDF,
  Word .docx, or an image — the same set agents/documents.py already
  knows how to feed to Claude) — the raw bytes are returned as-is so the
  caller can store and analyze them exactly like an uploaded file, rather
  than rejecting the URL just because it isn't a webpage.

Anything else (audio/video, or any other binary type with no real
analysis pipeline in this codebase) is a real, honest failure — no silent
fallback to an empty or fabricated result.

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
from typing import Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from agents.documents import SUPPORTED_MEDIA_TYPES

MAX_CONTENT_BYTES = 5 * 1024 * 1024  # 5MB — nowhere near what a real article/page or PDF needs
REQUEST_TIMEOUT_SECONDS = 15.0
USER_AGENT = "Mozilla/5.0 (compatible; KuveraCapitalBot/1.0; +internal deal-ops research tool)"

# Reverse of agents/documents.py's extension->media_type map, minus txt
# (text/* is handled by the HTML/text branch below, not the binary one) —
# reusing that map rather than duplicating it keeps "what Claude can read"
# defined in exactly one place.
_EXT_BY_MEDIA_TYPE = {v: k for k, v in SUPPORTED_MEDIA_TYPES.items() if k != "txt"}


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


def _filename_from_url(url: str, ext: str) -> str:
    path = urlparse(url).path
    base = path.rsplit("/", 1)[-1] if path else ""
    if base and "." in base:
        return base
    hostname = urlparse(url).hostname or "download"
    return f"{hostname}.{ext}"


def fetch_url_content(url: str) -> dict[str, Any]:
    """Returns either {"kind": "text", "title": ..., "text": ...} for an
    HTML/text page, or {"kind": "file", "filename": ..., "content": bytes,
    "content_type": ...} for a directly-linked PDF/.docx/image. Raises
    UnsafeUrlError/ValueError on any real failure (bad scheme,
    unresolvable/private host, unsupported content type, oversized
    response, HTTP error)."""
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
            content_type_header = response.headers.get("content-type", "")
            content_type = content_type_header.split(";")[0].strip().lower()
            is_text = "html" in content_type or content_type.startswith("text/")
            ext = _EXT_BY_MEDIA_TYPE.get(content_type)

            if not is_text and ext is None:
                raise ValueError(
                    f"URL did not return a supported content type (got {content_type_header!r}) — "
                    "supported: HTML/text pages, PDF, Word (.docx), and images (png/jpg/gif/webp)"
                )

            chunks: list[bytes] = []
            total = 0
            for chunk in response.iter_bytes():
                total += len(chunk)
                if total > MAX_CONTENT_BYTES:
                    raise ValueError(f"Content exceeds {MAX_CONTENT_BYTES // (1024 * 1024)}MB limit")
                chunks.append(chunk)
            raw = b"".join(chunks)

    if not is_text:
        return {
            "kind": "file",
            "filename": _filename_from_url(url, ext),
            "content": raw,
            "content_type": content_type,
        }

    soup = BeautifulSoup(raw, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    title = soup.title.get_text(strip=True) if soup.title and soup.title.get_text(strip=True) else parsed.hostname
    text = soup.get_text(separator="\n")
    cleaned = "\n".join(line.strip() for line in text.splitlines() if line.strip())

    if not cleaned:
        raise ValueError("No readable text content found on the page")

    return {"kind": "text", "title": title, "text": cleaned}
