"""Reliable Source Registry (CP44).

Maintains a curated list of trusted news sources (official blogs, research papers).
Used by the URL input workflow to assign trust levels, default tags, and source metadata
without making any network requests.

No real LLM, no real TTS, no web crawler.
"""

from __future__ import annotations

from urllib.parse import urlparse

RELIABLE_SOURCES = [
    {
        "id": "openai_blog",
        "name": "OpenAI Blog",
        "type": "official_blog",
        "domain": "openai.com",
        "trust_level": "official",
        "default_tags": ["openai", "official"],
    },
    {
        "id": "anthropic_news",
        "name": "Anthropic News",
        "type": "official_blog",
        "domain": "anthropic.com",
        "trust_level": "official",
        "default_tags": ["anthropic", "official"],
    },
    {
        "id": "google_ai_blog",
        "name": "Google AI Blog",
        "type": "official_blog",
        "domain": "blog.google",
        "trust_level": "official",
        "default_tags": ["google", "official"],
    },
    {
        "id": "deepmind_blog",
        "name": "Google DeepMind Blog",
        "type": "official_blog",
        "domain": "deepmind.google",
        "trust_level": "official",
        "default_tags": ["deepmind", "official"],
    },
    {
        "id": "meta_ai_blog",
        "name": "Meta AI Blog",
        "type": "official_blog",
        "domain": "ai.meta.com",
        "trust_level": "official",
        "default_tags": ["meta", "official"],
    },
    {
        "id": "microsoft_ai_blog",
        "name": "Microsoft AI Blog",
        "type": "official_blog",
        "domain": "blogs.microsoft.com",
        "trust_level": "official",
        "default_tags": ["microsoft", "official"],
    },
    {
        "id": "arxiv",
        "name": "arXiv",
        "type": "paper",
        "domain": "arxiv.org",
        "trust_level": "research",
        "default_tags": ["research", "paper"],
    },
]


def list_reliable_sources() -> list[dict]:
    """Return all registered reliable sources (read-only copies)."""
    return [dict(s) for s in RELIABLE_SOURCES]


def get_reliable_source(source_id: str) -> dict | None:
    """Return a single source by id, or None if not found."""
    for s in RELIABLE_SOURCES:
        if s["id"] == source_id:
            return dict(s)
    return None


def infer_source_from_url(url: str) -> dict | None:
    """Attempt to infer the reliable source from a URL's domain.

    Returns the matching source dict or None.
    """
    if not url:
        return None
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
    except Exception:
        return None

    # Strip leading www. for matching
    match_domain = domain.removeprefix("www.")

    for source in RELIABLE_SOURCES:
        source_domain = source["domain"].lower()
        if match_domain == source_domain or match_domain.endswith("." + source_domain):
            return dict(source)

    return None


def validate_source_url(url: str) -> tuple[bool, str | None]:
    """Validate a user-provided source URL.

    Returns (True, None) if valid, or (False, error_message) if invalid.
    Rules:
      - Must be non-empty
      - Must start with http:// or https://
      - Must not be a javascript: URI
      - file:// is rejected
      - Must include a valid domain (netloc)
    """
    if not url or not url.strip():
        return False, "URL cannot be empty"

    url_stripped = url.strip()
    lower = url_stripped.lower()

    if lower.startswith("javascript:"):
        return False, "javascript: URLs are not allowed"

    if lower.startswith("file://"):
        return False, "file:// URLs are not allowed"

    if not lower.startswith(("http://", "https://")):
        return False, "URL must start with http:// or https://"

    parsed = urlparse(url_stripped)
    if not parsed.netloc:
        return False, "URL must include a valid domain"

    return True, None
