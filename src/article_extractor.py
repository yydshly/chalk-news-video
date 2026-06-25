"""Article Fetch / Extraction MVP (CP45).

Provides a limited, safe, testable static HTML article extractor.
Uses only stdlib (urllib.request + html.parser).
No JS rendering, no crawler, no real LLM/TTS.

Security:
  - URL scheme validation (http/https only)
  - Private IP / localhost rejection via ipaddress
  - Timeout on network requests
  - Max response size limit (512 KB)
  - Content-type enforcement (text/html or application/xhtml+xml only)
  - No file:// / javascript: URLs
  - User-Agent set to a neutral crawler identifier
"""

from __future__ import annotations

import ipaddress
import re
import ssl
import urllib.request
import uuid
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Optional
from urllib.parse import urljoin, urlparse

# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------

@dataclass
class ExtractedArticle:
    """Result of an article extraction attempt."""
    url: str
    title: str
    description: str
    body_text: str
    source_domain: str
    content_type: str
    fetched: bool
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# HTML Text Extractor (inner content only, no tags)
# ---------------------------------------------------------------------------

class _HtmlTextExtractor(HTMLParser):
    """Collects readable text from HTML, stripping script/style/svg etc."""

    def __init__(self) -> None:
        super().__init__()
        self.text_parts: list[str] = []
        self._skip_depth = 0  # nesting level inside skip-tags
        self._skip_tags = {"script", "style", "noscript", "svg", "math"}
        self._last_was_text = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        if tag in self._skip_tags:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in self._skip_tags and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            stripped = data.strip()
            if stripped:
                if self._last_was_text:
                    self.text_parts.append(" " + stripped)
                else:
                    self.text_parts.append(stripped)
                self._last_was_text = True
            else:
                self._last_was_text = False

    def get_text(self) -> str:
        return "".join(self.text_parts)


# ---------------------------------------------------------------------------
# Meta tag extractor
# ---------------------------------------------------------------------------

class _MetaExtractor(HTMLParser):
    """Extracts title, meta description, og:title, og:description from HTML head."""

    def __init__(self) -> None:
        super().__init__()
        self.title: str = ""
        self.meta_description: str = ""
        self.og_title: str = ""
        self.og_description: str = ""
        self._in_head = False
        self._title_from_tag: bool = False  # was <title> tag used directly

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        attrs_dict = {k: (v or "") for k, v in attrs}

        if tag == "head":
            self._in_head = True
        elif tag == "title" and self._in_head:
            self._title_from_tag = True
        elif tag == "meta":
            name = attrs_dict.get("name", "").lower()
            prop = attrs_dict.get("property", "").lower()
            content = attrs_dict.get("content", "")

            if name == "description":
                self.meta_description = content
            elif prop == "og:title":
                self.og_title = content
            elif prop == "og:description":
                self.og_description = content

    def handle_endtag(self, tag: str) -> None:
        if tag == "head":
            self._in_head = False
        elif tag == "title":
            self._title_from_tag = False

    def handle_data(self, data: str) -> None:
        if self._title_from_tag and self._in_head:
            self.title = data.strip()


# ---------------------------------------------------------------------------
# Extraction from raw HTML (pure function, no network)
# ---------------------------------------------------------------------------

def extract_article_from_html(
    html: str,
    *,
    url: str = "",
    content_type: str = "text/html",
) -> ExtractedArticle:
    """Extract article fields from raw HTML text.

    Title priority: og:title > <title> > first <h1>
    Description priority: og:description > meta description > first paragraph
    Body: all readable text from body, max 3000 chars.

    Returns an ExtractedArticle with fetched=True.
    """
    domain = ""
    if url:
        try:
            domain = urlparse(url).netloc
        except Exception:
            domain = ""

    # Extract meta info
    meta_parser = _MetaExtractor()
    try:
        meta_parser.feed(html)
    except Exception:
        pass

    title = meta_parser.og_title or meta_parser.title
    description = meta_parser.og_description or meta_parser.meta_description

    # Extract body text
    body_text = ""
    body_start = html.lower().find("<body")
    if body_start == -1:
        body_start = 0
    body_html = html[body_start:]

    text_parser = _HtmlTextExtractor()
    try:
        text_parser.feed(body_html)
    except Exception:
        pass

    raw_text = text_parser.get_text()
    # Collapse multiple spaces
    raw_text = re.sub(r"\s+", " ", raw_text).strip()
    body_text = raw_text[:3000]

    # Fallback title from h1 if still empty
    if not title:
        h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.IGNORECASE | re.DOTALL)
        if h1_match:
            title = re.sub(r"<[^>]+>", "", h1_match.group(1)).strip()
            title = re.sub(r"\s+", " ", title)

    # Fallback description from first paragraph
    if not description:
        p_match = re.search(r"<p[^>]*>(.*?)</p>", body_html, re.IGNORECASE | re.DOTALL)
        if p_match:
            description = re.sub(r"<[^>]+>", "", p_match.group(1)).strip()
            description = re.sub(r"\s+", " ", description)

    # Truncate
    title = title[:200]
    description = description[:500]

    return ExtractedArticle(
        url=url or "",
        title=title,
        description=description,
        body_text=body_text,
        source_domain=domain,
        content_type=content_type,
        fetched=True,
        error=None,
    )


# ---------------------------------------------------------------------------
# Security helpers
# ---------------------------------------------------------------------------

BLOCKED_HOSTNAMES = frozenset([
    "localhost", "localhost.localdomain",
    "127.0.0.1", "::1", "0.0.0.0",
])


def _is_private_host(host: str) -> bool:
    """Return True if host is a private/localhost IP or hostname."""
    host_lower = host.lower().strip()
    if host_lower in BLOCKED_HOSTNAMES:
        return True
    # Try parsing as IP
    try:
        addr = ipaddress.ip_address(host_lower)
        return addr.is_private or addr.is_loopback or addr.is_reserved
    except ValueError:
        pass
    # Check if it looks like a private IP range (dotted notation)
    try:
        parts = host_lower.split(".")
        if len(parts) == 4:
            addr = ipaddress.ip_address(host_lower)
            return addr.is_private or addr.is_loopback
    except ValueError:
        pass
    return False


def _validate_fetch_url(url: str) -> tuple[bool, Optional[str]]:
    """Validate a URL for article fetching.

    Returns (True, None) if valid, or (False, error_message) if blocked.
    """
    if not url or not url.strip():
        return False, "URL cannot be empty"

    stripped = url.strip()
    lower = stripped.lower()

    if lower.startswith(("javascript:", "file:", "data:", "ftp:")):
        return False, f"URL scheme '{lower.split(':')[0]}:' is not allowed"

    if not lower.startswith(("http://", "https://")):
        return False, "URL must start with http:// or https://"

    try:
        parsed = urlparse(stripped)
    except Exception:
        return False, "Invalid URL"

    hostname = parsed.hostname or ""
    if not hostname:
        return False, "URL must include a valid hostname"

    if _is_private_host(hostname):
        return False, "Private / localhost URLs are not allowed"

    # Additional check: no IP literals in URL (covers IPv6 brackets)
    try:
        # Strip brackets for IPv6
        check_host = hostname.strip("[]")
        if _is_private_host(check_host):
            return False, "Private / localhost URLs are not allowed"
    except Exception:
        pass

    return True, None


def _resolve_redirect_url(current_url: str, location: str) -> str:
    """Resolve a redirect Location header against the current URL (handles relative URLs)."""
    return urljoin(current_url, location)


# ---------------------------------------------------------------------------
# Network fetch
# ---------------------------------------------------------------------------

_USER_AGENT = "chalk-news-video/0.1 (article-extractor; +https://github.com/yydshly/chalk-news-video)"
_ACCEPTED_CONTENT_TYPES = frozenset(["text/html", "application/xhtml+xml"])
_MAX_BYTES = 512_000  # 512 KB
_MAX_REDIRECTS = 1


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """URLOpener handler that suppresses all automatic redirects."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _build_no_redirect_opener(ctx: ssl.SSLContext):
    """Build an opener that does not follow redirects automatically."""
    https_handler = urllib.request.HTTPSHandler(context=ctx)
    return urllib.request.build_opener(_NoRedirectHandler, https_handler)


def fetch_and_extract_article(
    url: str,
    *,
    timeout_sec: float = 6.0,
    max_bytes: int = _MAX_BYTES,
) -> ExtractedArticle:
    """Fetch a URL and extract article content.

    Security:
      - URL validated before fetching (scheme, private IP, hostname)
      - Timeout enforced
      - Max response size enforced
      - Content-Type checked (text/html or application/xhtml+xml)
      - At most 1 redirect allowed; redirect target is re-validated
      - No JS rendering, no crawler, no real LLM/TTS

    Returns ExtractedArticle on success, or ExtractedArticle with error on failure.
    """
    # Security check first
    ok, err = _validate_fetch_url(url)
    if not ok:
        return ExtractedArticle(
            url=url,
            title="",
            description="",
            body_text="",
            source_domain="",
            content_type="",
            fetched=False,
            error=err or "Invalid URL",
        )

    ctx = ssl.create_default_context()
    headers = {
        "User-Agent": _USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,*/*",
        "Accept-Language": "en-US,en;q=0.9",
    }

    current_url = url
    redirect_count = 0

    while True:
        # Revalidate URL on every iteration (initial + after redirect)
        ok, err = _validate_fetch_url(current_url)
        if not ok:
            return ExtractedArticle(
                url=url,
                title="",
                description="",
                body_text="",
                source_domain="",
                content_type="",
                fetched=False,
                error=err or "Invalid URL",
            )

        req = urllib.request.Request(current_url, headers=headers)
        opener = _build_no_redirect_opener(ctx)

        try:
            resp = opener.open(req, timeout=timeout_sec)
            break  # Success — proceed to extraction
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 303, 307, 308):
                if redirect_count >= _MAX_REDIRECTS:
                    return ExtractedArticle(
                        url=url,
                        title="",
                        description="",
                        body_text="",
                        source_domain="",
                        content_type="",
                        fetched=False,
                        error="Too many redirects (max 1 allowed)",
                    )
                location = e.headers.get("Location")
                if not location:
                    return ExtractedArticle(
                        url=url,
                        title="",
                        description="",
                        body_text="",
                        source_domain="",
                        content_type="",
                        fetched=False,
                        error="Redirect without Location header",
                    )
                next_url = _resolve_redirect_url(current_url, location)
                ok2, err2 = _validate_fetch_url(next_url)
                if not ok2:
                    return ExtractedArticle(
                        url=url,
                        title="",
                        description="",
                        body_text="",
                        source_domain="",
                        content_type="",
                        fetched=False,
                        error="Redirect URL rejected: " + (err2 or "unsafe"),
                    )
                current_url = next_url
                redirect_count += 1
                continue
            return ExtractedArticle(
                url=url,
                title="",
                description="",
                body_text="",
                source_domain="",
                content_type="",
                fetched=False,
                error=f"HTTP error {e.code}: {e.reason}",
            )
        except urllib.error.URLError as e:
            return ExtractedArticle(
                url=url,
                title="",
                description="",
                body_text="",
                source_domain="",
                content_type="",
                fetched=False,
                error=f"URL fetch failed: {e.reason}",
            )

    # No redirect followed — current_url is the final URL (validated above)
    final_url = current_url
    try:
        parsed_final = urlparse(final_url)
        hostname = parsed_final.hostname or ""
    except Exception:
        hostname = ""

    content_type = resp.headers.get("Content-Type", "").split(";")[0].strip()
    if content_type.lower() not in _ACCEPTED_CONTENT_TYPES:
        return ExtractedArticle(
            url=url,
            title="",
            description="",
            body_text="",
            source_domain=hostname,
            content_type=content_type,
            fetched=False,
            error=f"Content-Type '{content_type}' is not supported. Only text/html is supported.",
        )

    # Read with size limit
    raw = resp.read(max_bytes + 1)
    if len(raw) > max_bytes:
        return ExtractedArticle(
            url=url,
            title="",
            description="",
            body_text="",
            source_domain=hostname,
            content_type=content_type,
            fetched=False,
            error=f"Response exceeds maximum size of {max_bytes} bytes",
        )

    # Detect encoding
    charset = "utf-8"
    ct_full = resp.headers.get("Content-Type", "")
    if "charset=" in ct_full.lower():
        charset = ct_full.lower().split("charset=")[-1].strip().split(";")[0].strip()

    try:
        html = raw.decode(charset, errors="replace")
    except Exception:
        html = raw.decode("utf-8", errors="replace")

    # Use final_url (after any redirects) for extraction
    return extract_article_from_html(html, url=final_url, content_type=content_type)
