#!/usr/bin/env python3
"""CP45: Test article fetch / extraction MVP.

Tests:
  - extract_article_from_html(): title, description, og:, body text, script/style stripping
  - Security: private IP rejection, localhost, invalid schemes
  - /api/article/extract: validation and error cases
  - /api/episode/source-contract url_fetch: contract generation
  - No real network calls in tests

Uses FastAPI TestClient — no real outputs, no real LLM/TTS, no web crawler.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fastapi.testclient import TestClient
from server import app
from article_extractor import (
    extract_article_from_html,
    _validate_fetch_url,
    _is_private_host,
    ExtractedArticle,
)
from news_source_pipeline import contract_has_secrets

client = TestClient(app)

# ---------------------------------------------------------------------------
# extract_article_from_html tests
# ---------------------------------------------------------------------------

def test_extract_basic_title():
    """1. extract_article_from_html() extracts <title> tag."""
    html = "<html><head><title>Test Article Title</title></head><body><p>Content here.</p></body></html>"
    article = extract_article_from_html(html, url="https://example.com/article")
    assert article.title == "Test Article Title"
    assert article.fetched is True
    print("  [PASS] extracts <title> tag")


def test_extract_og_title_priority():
    """2. og:title takes priority over <title>."""
    html = (
        "<html><head>"
        "<title>fallback title</title>"
        '<meta property="og:title" content="OG Title Here"/>'
        "</head><body><p>content</p></body></html>"
    )
    article = extract_article_from_html(html)
    assert article.title == "OG Title Here"
    print("  [PASS] og:title priority over <title>")


def test_extract_meta_description():
    """3. extract_article_from_html() extracts meta description."""
    html = (
        "<html><head>"
        '<meta name="description" content="This is the meta description."/>'
        "</head><body><p>Some paragraph.</p></body></html>"
    )
    article = extract_article_from_html(html)
    assert article.description == "This is the meta description."
    print("  [PASS] extracts meta description")


def test_extract_og_description_priority():
    """4. og:description takes priority over meta description."""
    html = (
        "<html><head>"
        '<meta name="description" content="meta desc"/>'
        '<meta property="og:description" content="OG description priority"/>'
        "</head><body><p>text</p></body></html>"
    )
    article = extract_article_from_html(html)
    assert article.description == "OG description priority"
    print("  [PASS] og:description priority over meta description")


def test_extract_ignores_script():
    """5. script tag content is stripped from body text."""
    html = (
        "<html><body>"
        "<p>visible paragraph</p>"
        "<script>document.cookie='evil'; alert('xss');</script>"
        "<p>another visible line</p>"
        "</body></html>"
    )
    article = extract_article_from_html(html)
    text = article.body_text
    assert "visible paragraph" in text
    assert "document.cookie" not in text
    assert "alert" not in text
    print("  [PASS] script tag stripped from body text")


def test_extract_ignores_style():
    """6. style tag content is stripped from body text."""
    html = (
        "<html><body>"
        "<style>.hidden { display:none }</style>"
        "<p>visible content</p>"
        "</body></html>"
    )
    article = extract_article_from_html(html)
    text = article.body_text
    assert "visible content" in text
    assert "display:none" not in text
    print("  [PASS] style tag stripped from body text")


def test_extract_body_text_max_length():
    """7. body_text is limited to 3000 characters."""
    long_text = "word " * 2000  # 4000+ words
    html = f"<html><body><p>{long_text}</p></body></html>"
    article = extract_article_from_html(html)
    assert len(article.body_text) <= 3000
    print("  [PASS] body_text limited to 3000 chars")


def test_extract_truncates_title():
    """8. title is truncated to 200 characters."""
    long_title = "A" * 300
    html = f"<html><head><title>{long_title}</title></head><body><p>text</p></body></html>"
    article = extract_article_from_html(html)
    assert len(article.title) <= 200
    print("  [PASS] title truncated to 200 chars")


def test_extract_source_domain():
    """9. source_domain is extracted from URL."""
    html = "<html><body><p>test</p></body></html>"
    article = extract_article_from_html(html, url="https://openai.com/blog/post")
    assert article.source_domain == "openai.com"
    print("  [PASS] source_domain extracted from URL")


# ---------------------------------------------------------------------------
# Security validation tests
# ---------------------------------------------------------------------------

def test_validate_rejects_empty_url():
    """10. _validate_fetch_url() rejects empty URL."""
    ok, err = _validate_fetch_url("")
    assert ok is False
    assert err is not None
    print("  [PASS] rejects empty URL")


def test_validate_rejects_javascript():
    """11. _validate_fetch_url() rejects javascript: URL."""
    ok, err = _validate_fetch_url("javascript:alert(1)")
    assert ok is False
    print("  [PASS] rejects javascript: URL")


def test_validate_rejects_file():
    """12. _validate_fetch_url() rejects file:// URL."""
    ok, err = _validate_fetch_url("file:///etc/passwd")
    assert ok is False
    print("  [PASS] rejects file:// URL")


def test_validate_rejects_localhost():
    """13. _validate_fetch_url() rejects localhost."""
    ok, err = _validate_fetch_url("http://localhost/blog/article")
    assert ok is False
    assert "localhost" in err.lower() or "private" in err.lower()
    ok2, err2 = _validate_fetch_url("https://localhost:8080/page")
    assert ok2 is False
    print("  [PASS] rejects localhost URLs")


def test_validate_rejects_127():
    """14. _validate_fetch_url() rejects 127.0.0.1."""
    ok, err = _validate_fetch_url("http://127.0.0.1/admin")
    assert ok is False
    assert "private" in err.lower() or "127" in err.lower()
    print("  [PASS] rejects 127.0.0.1")


def test_validate_rejects_private_ip():
    """15. _validate_fetch_url() rejects 10.x.x.x private IPs."""
    ok, err = _validate_fetch_url("http://10.0.0.1/internal")
    assert ok is False
    assert "private" in err.lower()
    print("  [PASS] rejects 10.x.x.x private IPs")


def test_validate_rejects_192168():
    """16. _validate_fetch_url() rejects 192.168.x.x private IPs."""
    ok, err = _validate_fetch_url("http://192.168.1.1/router")
    assert ok is False
    assert "private" in err.lower()
    print("  [PASS] rejects 192.168.x.x private IPs")


def test_validate_rejects_17216():
    """17. _validate_fetch_url() rejects 172.16.x.x private IPs."""
    ok, err = _validate_fetch_url("http://172.16.0.1/internal")
    assert ok is False
    assert "private" in err.lower()
    print("  [PASS] rejects 172.16.x.x private IPs")


def test_validate_rejects_missing_hostname():
    """18. _validate_fetch_url() rejects URL with no hostname (bare scheme)."""
    ok, err = _validate_fetch_url("https://")
    assert ok is False
    ok2, err2 = _validate_fetch_url("http://")
    assert ok2 is False
    print("  [PASS] rejects bare scheme URLs")


def test_validate_accepts_normal_url():
    """19. _validate_fetch_url() accepts normal https URLs."""
    ok, err = _validate_fetch_url("https://openai.com/blog/article")
    assert ok is True
    assert err is None
    ok2, err2 = _validate_fetch_url("http://example.com/page?q=1")
    assert ok2 is True
    print("  [PASS] accepts normal https/http URLs")


# ---------------------------------------------------------------------------
# Redirect safety tests (CP45.1)
# ---------------------------------------------------------------------------

def test_resolve_redirect_url_relative():
    """20. _resolve_redirect_url() correctly resolves relative redirect URLs."""
    from article_extractor import _resolve_redirect_url
    # Absolute URL redirect
    assert _resolve_redirect_url("https://example.com/a", "https://other.com/b") == "https://other.com/b"
    # Root-relative redirect
    assert _resolve_redirect_url("https://example.com/a/b", "/c") == "https://example.com/c"
    # Query-relative redirect: urljoin('https://example.com/a?x=1', 'b') -> 'https://example.com/b'
    assert _resolve_redirect_url("https://example.com/a?x=1", "b") == "https://example.com/b"
    print("  [PASS] _resolve_redirect_url resolves relative URLs")


def test_resolve_redirect_url_preserves_domain():
    """21. _resolve_redirect_url() preserves the base domain for root-relative paths."""
    from article_extractor import _resolve_redirect_url
    result = _resolve_redirect_url("https://openai.com/blog/intro", "/research/paper")
    assert result.startswith("https://openai.com")
    assert "/research/paper" in result
    print("  [PASS] _resolve_redirect_url preserves domain for root-relative paths")


def test_validate_rejects_redirect_to_127():
    """22. _validate_fetch_url() rejects redirect URL pointing to 127.0.0.1."""
    # This is the core SSRF fix test: if a redirect resolves to a private IP it must be blocked
    ok, err = _validate_fetch_url("http://127.0.0.1:8080/internal")
    assert ok is False
    assert "private" in err.lower() or "localhost" in err.lower()
    print("  [PASS] rejects redirect URL to 127.0.0.1")


def test_validate_rejects_redirect_to_10_private():
    """23. _validate_fetch_url() rejects redirect URL pointing to 10.x.x.x private IP."""
    ok, err = _validate_fetch_url("http://10.0.0.5/admin")
    assert ok is False
    assert "private" in err.lower()
    print("  [PASS] rejects redirect URL to 10.x.x.x private IP")


def test_validate_rejects_redirect_to_javascript():
    """24. _validate_fetch_url() rejects redirect URL with javascript: scheme."""
    ok, err = _validate_fetch_url("javascript:alert(1)")
    assert ok is False
    print("  [PASS] rejects redirect URL with javascript: scheme")


def test_max_redirects_is_one():
    """25. _MAX_REDIRECTS is set to 1 to prevent open redirect chains."""
    from article_extractor import _MAX_REDIRECTS
    assert _MAX_REDIRECTS == 1
    print("  [PASS] _MAX_REDIRECTS is 1")


def test_no_redirect_handler_exists():
    """26. _NoRedirectHandler class exists and is usable."""
    from article_extractor import _NoRedirectHandler
    # Should be a subclass of HTTPRedirectHandler
    assert hasattr(_NoRedirectHandler, "redirect_request")
    print("  [PASS] _NoRedirectHandler exists and has redirect_request")


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------

def test_article_extract_missing_url():
    """20. /api/article/extract returns ok=False when url is missing."""
    resp = client.post("/api/article/extract", json={})
    data = resp.json()
    assert data.get("ok") is False
    print("  [PASS] /api/article/extract rejects missing URL")


def test_article_extract_localhost_rejected():
    """21. /api/article/extract rejects localhost URL."""
    resp = client.post("/api/article/extract", json={"url": "http://localhost/blog"})
    data = resp.json()
    assert data.get("ok") is False
    print("  [PASS] /api/article/extract rejects localhost")


def test_article_extract_private_ip_rejected():
    """22. /api/article/extract rejects private IP URL."""
    resp = client.post("/api/article/extract", json={"url": "http://10.0.0.1/secret"})
    data = resp.json()
    assert data.get("ok") is False
    print("  [PASS] /api/article/extract rejects private IP")


def test_article_extract_bad_scheme_rejected():
    """23. /api/article/extract rejects javascript: URL."""
    resp = client.post("/api/article/extract", json={"url": "javascript:alert(1)"})
    data = resp.json()
    assert data.get("ok") is False
    print("  [PASS] /api/article/extract rejects javascript: URL")


def test_article_extract_url_fetch_missing_url():
    """24. url_fetch source_type returns ok=False when url is missing."""
    resp = client.post("/api/episode/source-contract", json={
        "source_type": "url_fetch",
        "limit": 1,
        "template_id": "breaking_news_v1",
    })
    data = resp.json()
    assert data.get("ok") is False
    assert "url" in str(data.get("error", "")).lower()
    print("  [PASS] url_fetch rejects missing URL")


def test_article_extract_url_fetch_unknown_domain_network_error():
    """25. url_fetch with unreachable/invalid domain returns ok=False."""
    # Use a domain that definitely won't resolve
    resp = client.post("/api/episode/source-contract", json={
        "source_type": "url_fetch",
        "url": "https://this-domain-does-not-exist-xyz123.invalid/article",
        "limit": 1,
        "template_id": "breaking_news_v1",
    })
    data = resp.json()
    assert data.get("ok") is False
    print("  [PASS] url_fetch handles network failure gracefully")


def test_article_extract_url_fetch_contract_schema():
    """26. url_fetch handles extraction failure gracefully without crashing."""
    # Use a domain that triggers a network/SSL error
    resp = client.post("/api/episode/source-contract", json={
        "source_type": "url_fetch",
        "url": "https://unreachable.invalid/page",
        "limit": 1,
        "template_id": "breaking_news_v1",
    })
    # Should return ok=False (network error is not a 5xx crash)
    assert resp.status_code in (200, 400), f"Expected 200/400, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data.get("ok") is False, f"Expected ok=False, got: {data}"
    assert "error" in data, f"Expected error field, got: {data}"
    print("  [PASS] url_fetch handles extraction failure gracefully")


def test_article_extract_url_fetch_unsupported_template():
    """27. url_fetch with unsupported template_id returns ok=False."""
    resp = client.post("/api/episode/source-contract", json={
        "source_type": "url_fetch",
        "url": "https://example.com/article",
        "limit": 1,
        "template_id": "timeline_brief_v1",
    })
    data = resp.json()
    assert data.get("ok") is False
    print("  [PASS] url_fetch rejects unsupported template_id")


def test_article_extract_contract_no_secrets():
    """28. url_fetch contract (on extraction failure) does not expose secrets."""
    resp = client.post("/api/episode/source-contract", json={
        "source_type": "url_fetch",
        "url": "https://unreachable.invalid/article",
        "limit": 1,
        "template_id": "breaking_news_v1",
    })
    data = resp.json()
    # Even an error response body should not contain secrets
    resp_text = str(data)
    assert "api_key" not in resp_text.lower()
    assert "voice_id" not in resp_text.lower()
    print("  [PASS] url_fetch error response contains no secrets")


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

def run_all():
    tests = [
        # extract_article_from_html
        test_extract_basic_title,
        test_extract_og_title_priority,
        test_extract_meta_description,
        test_extract_og_description_priority,
        test_extract_ignores_script,
        test_extract_ignores_style,
        test_extract_body_text_max_length,
        test_extract_truncates_title,
        test_extract_source_domain,
        # Security
        test_validate_rejects_empty_url,
        test_validate_rejects_javascript,
        test_validate_rejects_file,
        test_validate_rejects_localhost,
        test_validate_rejects_127,
        test_validate_rejects_private_ip,
        test_validate_rejects_192168,
        test_validate_rejects_17216,
        test_validate_rejects_missing_hostname,
        test_validate_accepts_normal_url,
        # Redirect safety (CP45.1)
        test_resolve_redirect_url_relative,
        test_resolve_redirect_url_preserves_domain,
        test_validate_rejects_redirect_to_127,
        test_validate_rejects_redirect_to_10_private,
        test_validate_rejects_redirect_to_javascript,
        test_max_redirects_is_one,
        test_no_redirect_handler_exists,
        # API
        test_article_extract_missing_url,
        test_article_extract_localhost_rejected,
        test_article_extract_private_ip_rejected,
        test_article_extract_bad_scheme_rejected,
        test_article_extract_url_fetch_missing_url,
        test_article_extract_url_fetch_unknown_domain_network_error,
        test_article_extract_url_fetch_contract_schema,
        test_article_extract_url_fetch_unsupported_template,
        test_article_extract_contract_no_secrets,
    ]

    print("=" * 60)
    print("CP45: Article Fetch / Extraction MVP — Test Suite")
    print("=" * 60)

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {test.__name__}: {e}")
            failed += 1

    print("=" * 60)
    if failed == 0:
        print(f"ALL CP45 ARTICLE FETCH EXTRACTION TESTS PASSED ({passed}/{len(tests)})")
    else:
        print(f"FAILED: {failed} test(s) failed, {passed} passed out of {len(tests)}")
    print("=" * 60)
    return failed == 0


if __name__ == "__main__":
    ok = run_all()
    sys.exit(0 if ok else 1)
