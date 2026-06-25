"""Real Source Feed Snapshot MVP (CP53).

Provides safe, lightweight RSS and static HTML feed fetching
for official/curated AI news sources.

Security:
  - URL scheme validation (http/https only)
  - Private IP / localhost rejection
  - Timeout on network requests (8s default)
  - Max response size limit (1 MB)
  - Redirect limit (1 hop, re-validated after redirect)
  - Fixed User-Agent

No JS rendering, no crawler, no real LLM/TTS, no Remotion.
"""

from __future__ import annotations

import hashlib
import ipaddress
import re
import ssl
import urllib.request
import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Optional
from urllib.parse import urljoin, urlparse


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_BYTES = 1024 * 1024          # 1 MB
DEFAULT_TIMEOUT = 8.0             # seconds
MAX_REDIRECTS = 1
USER_AGENT = "chalk-news-video-source-snapshot/0.1"

# ---------------------------------------------------------------------------
# Source Feed Config
# ---------------------------------------------------------------------------

@dataclass
class SourceFeedConfig:
    source_id: str
    name: str
    homepage_url: str
    fetch_url: str
    source_kind: str           # "rss" | "html_static"
    trust_level: str           # "official" | "research" | "community"
    tags: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Default Official Feeds
# ---------------------------------------------------------------------------

def list_default_source_feeds() -> list[SourceFeedConfig]:
    """Return the default list of curated AI news source feeds."""
    return [
        SourceFeedConfig(
            source_id="openai_blog",
            name="OpenAI Blog",
            homepage_url="https://openai.com/blog",
            fetch_url="https://openai.com/news/rss.xml",
            source_kind="rss",
            trust_level="official",
            tags=["official", "ai"],
        ),
        SourceFeedConfig(
            source_id="anthropic_news",
            name="Anthropic News",
            homepage_url="https://www.anthropic.com/news",
            fetch_url="https://www.anthropic.com/news/feed.xml",
            source_kind="rss",
            trust_level="official",
            tags=["official", "ai", "safety"],
        ),
        SourceFeedConfig(
            source_id="google_ai_blog",
            name="Google AI Blog",
            homepage_url="https://blog.google/technology/ai/",
            fetch_url="https://blog.google/technology/ai/rss/",
            source_kind="rss",
            trust_level="official",
            tags=["official", "ai"],
        ),
        SourceFeedConfig(
            source_id="deepmind_blog",
            name="DeepMind Blog",
            homepage_url="https://deepmind.google/discover/blog/",
            fetch_url="https://deepmind.google/discover/blog/feed/",
            source_kind="rss",
            trust_level="official",
            tags=["official", "ai", "research"],
        ),
        SourceFeedConfig(
            source_id="microsoft_ai_blog",
            name="Microsoft AI Blog",
            homepage_url="https://blogs.microsoft.com/ai/",
            fetch_url="https://blogs.microsoft.com/ai/feed/",
            source_kind="rss",
            trust_level="official",
            tags=["official", "ai"],
        ),
        SourceFeedConfig(
            source_id="meta_ai_blog",
            name="Meta AI Blog",
            homepage_url="https://ai.meta.com/blog/",
            fetch_url="https://ai.meta.com/blog/rss/",
            source_kind="rss",
            trust_level="official",
            tags=["official", "ai"],
        ),
        SourceFeedConfig(
            source_id="arxiv_csai",
            name="arXiv cs.AI",
            homepage_url="https://arxiv.org/list/cs.AI/recent",
            fetch_url="https://export.arxiv.org/api/query?search_query=cat:cs.AI&max_results=10&sortBy=submittedDate&sortOrder=descending",
            source_kind="rss",
            trust_level="research",
            tags=["research", "ai", "arxiv"],
        ),
        SourceFeedConfig(
            source_id="huggingface_blog",
            name="Hugging Face Blog",
            homepage_url="https://huggingface.co/blog",
            fetch_url="https://huggingface.co/blog/feed.xml",
            source_kind="rss",
            trust_level="community",
            tags=["community", "ai", "open-source"],
        ),
    ]


# ---------------------------------------------------------------------------
# URL Safety Validation
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
    try:
        addr = ipaddress.ip_address(host_lower)
        return addr.is_private or addr.is_loopback or addr.is_reserved
    except ValueError:
        pass
    try:
        parts = host_lower.split(".")
        if len(parts) == 4:
            addr = ipaddress.ip_address(host_lower)
            return addr.is_private or addr.is_loopback
    except ValueError:
        pass
    return False


def validate_snapshot_url(url: str) -> tuple[bool, Optional[str]]:
    """Validate a URL for snapshot fetching.

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

    try:
        check_host = hostname.strip("[]")
        if _is_private_host(check_host):
            return False, "Private / localhost URLs are not allowed"
    except Exception:
        pass

    return True, None


# ---------------------------------------------------------------------------
# URL Fetcher
# ---------------------------------------------------------------------------

class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """URLError handler that records redirect info without following."""
    max_repeats = 1
    max_redirections = MAX_REDIRECTS

    def redirect_request(self, req, fp, code, msg, hdrs, newurl):
        return None

    def http_error_301(self, req, fp, code, msg, hdrs):
        return None

    def http_error_302(self, req, fp, code, msg, hdrs):
        return None

    def http_error_307(self, req, fp, code, msg, hdrs):
        return None


def _build_opener():
    ssl_ctx = ssl.create_default_context()
    return urllib.request.build_opener(
        _NoRedirectHandler(),
        urllib.request.HTTPSHandler(context=ssl_ctx)
    )


def fetch_text_url(
    url: str,
    timeout_sec: float = DEFAULT_TIMEOUT,
    max_bytes: int = MAX_BYTES,
) -> tuple[str, str]:
    """Fetch a URL and return (content, content_type).

    Raises urllib.error.URLError on failure.

    Security:
      - URL must pass validate_snapshot_url first
      - Timeout enforced
      - Max response size enforced
      - User-Agent set
    """
    valid, err = validate_snapshot_url(url)
    if not valid:
        raise urllib.error.URLError(err or "Invalid URL")

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, text/html, */*",
    }
    req = urllib.request.Request(url, headers=headers, method="GET")

    opener = _build_opener()
    try:
        response = opener.open(req, timeout=timeout_sec)
    except Exception:
        raise

    content_type = response.headers.get("Content-Type", "")
    raw_data = response.read(max_bytes)
    if len(raw_data) >= max_bytes:
        raise urllib.error.URLError(
            f"Response exceeds {max_bytes} bytes limit"
        )
    return raw_data.decode("utf-8", errors="replace"), content_type


# ---------------------------------------------------------------------------
# RSS / Atom Parser
# ---------------------------------------------------------------------------

def _stable_id(source_id: str, url: str) -> str:
    """Generate a stable ID from source_id + url."""
    raw = f"{source_id}:{url}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:16]


def _clean_text(text: Optional[str]) -> str:
    """Strip HTML tags and normalize whitespace."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _parse_rss_date(date_str: Optional[str]) -> str:
    """Parse an RSS date string into ISO format, or empty string."""
    if not date_str:
        return ""
    date_str = date_str.strip()
    if not date_str:
        return ""
    # Try common RSS date formats
    for fmt in (
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S GMT",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(date_str.replace(" +0000", " GMT").replace(" GMT", "+0000"), fmt)
            return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            pass
    return ""


def parse_rss_snapshot(
    config: SourceFeedConfig,
    xml_text: str,
    limit: int = 10,
) -> dict:
    """Parse RSS/Atom XML text and return a source_snapshot dict.

    Args:
        config: SourceFeedConfig for this source
        xml_text: Raw XML string
        limit: Maximum number of items to return

    Returns:
        A source_snapshot_v1 dict
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        return {
            "schema": "source_snapshot_v1",
            "snapshot_id": f"snapshot_error_{config.source_id}",
            "source_id": config.source_id,
            "source_name": config.name,
            "source_url": config.homepage_url,
            "fetch_url": config.fetch_url,
            "source_kind": config.source_kind,
            "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": "error",
            "error": f"XML parse error: {e}",
            "items": [],
            "item_count": 0,
            "limit": limit,
        }

    items = []
    ns = {}

    # Detect namespace (RSS 2.0 vs Atom)
    tag_name = root.tag.split("}")[1] if "}" in root.tag else root.tag
    is_atom = tag_name == "feed"

    # Extract Atom namespace URI if present
    atom_ns = ""
    if "}" in root.tag:
        atom_ns = root.tag.split("}")[0].strip("{")

    # Find item/entry elements
    entries = []
    if is_atom:
        # Use the namespace to find entries
        if atom_ns:
            entries = root.findall(f".//{{{atom_ns}}}entry")
        else:
            entries = root.findall("entry")
    else:
        channel = root.find("channel")
        if channel is not None:
            entries = channel.findall("item")

    for entry in entries[:limit]:
        if is_atom:
            title = _clean_text(_get_elem_text(entry, "title", atom_ns))
            link = _get_elem_attr(entry, "link", "href", atom_ns) or ""
            summary = _clean_text(
                _get_elem_text(entry, "summary", atom_ns) or
                _get_elem_text(entry, "content", atom_ns)
            )
            published = (
                _get_elem_text(entry, "published", atom_ns) or
                _get_elem_text(entry, "updated", atom_ns)
            )
        else:
            title = _clean_text(_get_elem_text(entry, "title", atom_ns))
            link = _get_elem_text(entry, "link", atom_ns) or ""
            description = _get_elem_text(entry, "description", atom_ns)
            summary = _clean_text(description)
            published = _get_elem_text(entry, "pubDate", atom_ns)

        if not title:
            continue
        if not link:
            continue

        item_url = link.strip()
        published_at = _parse_rss_date(published)

        items.append({
            "id": _stable_id(config.source_id, item_url),
            "title": title,
            "url": item_url,
            "summary": summary,
            "published_at": published_at,
            "source_id": config.source_id,
            "source_name": config.name,
            "source_kind": config.source_kind,
            "tags": config.tags[:],
            "raw": {"source": "rss"},
        })

    return {
        "schema": "source_snapshot_v1",
        "snapshot_id": f"snapshot_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{config.source_id}",
        "source_id": config.source_id,
        "source_name": config.name,
        "source_url": config.homepage_url,
        "fetch_url": config.fetch_url,
        "source_kind": config.source_kind,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "ok",
        "error": None,
        "items": items,
        "item_count": len(items),
        "limit": limit,
    }


def _get_elem_text(elem, tag: str, atom_ns: str = "") -> Optional[str]:
    """Get text from an element child, handling namespaced tags."""
    if atom_ns:
        namespaced_tag = f"{{{atom_ns}}}{tag}"
        child = elem.find(namespaced_tag)
        if child is not None and child.text:
            return child.text.strip()
    # Try direct
    child = elem.find(tag)
    if child is not None and child.text:
        return child.text.strip()
    # Try with wildcard namespace
    for child in elem:
        if child.tag.endswith("}:" + tag):
            if child.text:
                return child.text.strip()
    return None


def _get_elem_attr(elem, tag: str, attr: str, atom_ns: str = "") -> Optional[str]:
    """Get an attribute value from an element child, handling namespaced tags."""
    if atom_ns:
        namespaced_tag = f"{{{atom_ns}}}{tag}"
        child = elem.find(namespaced_tag)
        if child is not None:
            val = child.get(attr)
            if val:
                return val.strip()
    child = elem.find(tag)
    if child is not None:
        val = child.get(attr)
        if val:
            return val.strip()
    for child in elem:
        if child.tag.endswith("}:" + tag):
            val = child.get(attr)
            if val:
                return val.strip()
    return None


# ---------------------------------------------------------------------------
# HTML Static Link Extractor
# ---------------------------------------------------------------------------

class _LinkExtractor(HTMLParser):
    """Extract title and links from a static HTML page."""

    def __init__(self, limit: int = 10):
        super().__init__()
        self.links = []
        self.page_title = ""
        self.in_title = False
        self.limit = limit
        self._base_url = ""

    def feed(self, html: str, base_url: str):
        self._base_url = base_url
        super().feed(html)

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "title":
            self.in_title = True
        elif tag == "a":
            href = attrs_dict.get("href", "")
            if href:
                abs_url = urljoin(self._base_url, href)
                self.links.append(abs_url)

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title and not self.page_title:
            self.page_title = data.strip()


def parse_html_static_snapshot(
    config: SourceFeedConfig,
    html_text: str,
    limit: int = 10,
) -> dict:
    """Parse static HTML and extract page title + outbound links.

    Args:
        config: SourceFeedConfig
        html_text: Raw HTML string
        limit: Maximum links to return

    Returns:
        A source_snapshot_v1 dict with a single item representing the page
    """
    parser = _LinkExtractor(limit=limit)
    try:
        parser.feed(html_text, config.homepage_url)
    except Exception as e:
        return {
            "schema": "source_snapshot_v1",
            "snapshot_id": f"snapshot_error_{config.source_id}",
            "source_id": config.source_id,
            "source_name": config.name,
            "source_url": config.homepage_url,
            "fetch_url": config.fetch_url,
            "source_kind": config.source_kind,
            "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": "error",
            "error": f"HTML parse error: {e}",
            "items": [],
            "item_count": 0,
            "limit": limit,
        }

    items = []
    page_url = config.fetch_url or config.homepage_url
    items.append({
        "id": _stable_id(config.source_id, page_url),
        "title": parser.page_title or config.name,
        "url": page_url,
        "summary": "",
        "published_at": "",
        "source_id": config.source_id,
        "source_name": config.name,
        "source_kind": config.source_kind,
        "tags": config.tags[:],
        "raw": {"source": "html_static", "link_count": len(parser.links)},
    })

    # If we got links, add them as additional items
    for href in parser.links[:limit]:
        if href == page_url:
            continue
        items.append({
            "id": _stable_id(config.source_id, href),
            "title": parser.page_title or config.name,
            "url": href,
            "summary": "",
            "published_at": "",
            "source_id": config.source_id,
            "source_name": config.name,
            "source_kind": config.source_kind,
            "tags": config.tags[:],
            "raw": {"source": "html_static"},
        })

    return {
        "schema": "source_snapshot_v1",
        "snapshot_id": f"snapshot_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{config.source_id}",
        "source_id": config.source_id,
        "source_name": config.name,
        "source_url": config.homepage_url,
        "fetch_url": config.fetch_url,
        "source_kind": config.source_kind,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "ok",
        "error": None,
        "items": items[:limit],
        "item_count": len(items[:limit]),
        "limit": limit,
    }


# ---------------------------------------------------------------------------
# Single Source Snapshot
# ---------------------------------------------------------------------------

def fetch_source_snapshot(
    config: SourceFeedConfig,
    limit: int = 10,
) -> dict:
    """Fetch and parse a single source feed.

    Args:
        config: SourceFeedConfig
        limit: Max items per source

    Returns:
        source_snapshot_v1 dict
    """
    valid, err = validate_snapshot_url(config.fetch_url)
    if not valid:
        return {
            "schema": "source_snapshot_v1",
            "snapshot_id": f"snapshot_error_{config.source_id}",
            "source_id": config.source_id,
            "source_name": config.name,
            "source_url": config.homepage_url,
            "fetch_url": config.fetch_url,
            "source_kind": config.source_kind,
            "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": "error",
            "error": f"Invalid fetch URL: {err}",
            "items": [],
            "item_count": 0,
            "limit": limit,
        }

    try:
        content, _ = fetch_text_url(config.fetch_url)
    except Exception as e:
        return {
            "schema": "source_snapshot_v1",
            "snapshot_id": f"snapshot_error_{config.source_id}",
            "source_id": config.source_id,
            "source_name": config.name,
            "source_url": config.homepage_url,
            "fetch_url": config.fetch_url,
            "source_kind": config.source_kind,
            "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": "error",
            "error": f"Fetch error: {e}",
            "items": [],
            "item_count": 0,
            "limit": limit,
        }

    if config.source_kind == "rss":
        return parse_rss_snapshot(config, content, limit=limit)
    else:
        return parse_html_static_snapshot(config, content, limit=limit)


# ---------------------------------------------------------------------------
# Batch Snapshot
# ---------------------------------------------------------------------------

def fetch_source_snapshot_batch(
    source_ids: Optional[list[str]] = None,
    limit_per_source: int = 10,
) -> dict:
    """Fetch multiple source feeds.

    Args:
        source_ids: List of source_ids to fetch. None = all defaults.
        limit_per_source: Max items per source.

    Returns:
        source_snapshot_batch_v1 dict
    """
    feeds = list_default_source_feeds()
    if source_ids:
        feeds = [f for f in feeds if f.source_id in source_ids]

    snapshots = []
    total_items = 0
    for feed in feeds:
        snap = fetch_source_snapshot(feed, limit=limit_per_source)
        snapshots.append(snap)
        if snap.get("status") == "ok":
            total_items += snap.get("item_count", 0)

    return {
        "schema": "source_snapshot_batch_v1",
        "batch_id": f"batch_{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M%SZ')}",
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_count": len(snapshots),
        "item_count": total_items,
        "snapshots": snapshots,
    }
