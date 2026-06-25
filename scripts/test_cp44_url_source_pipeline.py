#!/usr/bin/env python3
"""CP44: Test reliable source registry and URL input pipeline.

Tests:
  - reliable_sources module functions
  - normalize_url_item()
  - GET /api/reliable-sources
  - POST /api/episode/source-contract with url_input
  - Contract output format and security

Uses FastAPI TestClient — no real outputs, no real LLM/TTS, no web crawler.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fastapi.testclient import TestClient
from server import app
from reliable_sources import (
    list_reliable_sources,
    get_reliable_source,
    infer_source_from_url,
    validate_source_url,
)
from news_source_pipeline import (
    normalize_url_item,
    contract_has_secrets,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# reliable_sources module tests
# ---------------------------------------------------------------------------

def test_list_reliable_sources_returns_items():
    """1. list_reliable_sources() returns non-empty list."""
    items = list_reliable_sources()
    assert isinstance(items, list), f"expected list, got {type(items)}"
    assert len(items) > 0, "list_reliable_sources returned empty"
    print("  [PASS] list_reliable_sources() returns non-empty list")


def test_reliable_source_has_required_fields():
    """2. Each source has id/name/domain/trust_level."""
    items = list_reliable_sources()
    for item in items:
        assert "id" in item, f"missing id in {item}"
        assert "name" in item, f"missing name in {item}"
        assert "domain" in item, f"missing domain in {item}"
        assert "trust_level" in item, f"missing trust_level in {item}"
    print("  [PASS] each source has id/name/domain/trust_level")


def test_infer_source_from_openai_url():
    """3. infer_source_from_url() recognizes openai.com domain."""
    result = infer_source_from_url("https://openai.com/blog/new-api-features")
    assert result is not None, "failed to infer openai source"
    assert result["id"] == "openai_blog", f"wrong id: {result}"
    assert result["trust_level"] == "official", f"wrong trust_level: {result}"
    print("  [PASS] infer_source_from_url recognizes openai.com")


def test_infer_source_from_arxiv_url():
    """4. infer_source_from_url() recognizes arxiv.org domain."""
    result = infer_source_from_url("https://arxiv.org/abs/2301.12345")
    assert result is not None, "failed to infer arxiv source"
    assert result["id"] == "arxiv", f"wrong id: {result}"
    assert result["trust_level"] == "research", f"wrong trust_level: {result}"
    print("  [PASS] infer_source_from_url recognizes arxiv.org")


def test_infer_source_unknown_domain():
    """5. infer_source_from_url() returns None for unknown domain."""
    result = infer_source_from_url("https://example.com/news/article")
    assert result is None, f"unexpected match: {result}"
    print("  [PASS] infer_source_from_url returns None for unknown domain")


def test_validate_source_url_empty():
    """6. validate_source_url() rejects empty URL."""
    ok, err = validate_source_url("")
    assert ok is False, "empty URL should be rejected"
    assert err is not None, "error message should be provided"
    print("  [PASS] validate_source_url rejects empty URL")


def test_validate_source_url_javascript():
    """7. validate_source_url() rejects javascript: URLs."""
    ok, err = validate_source_url("javascript:alert(1)")
    assert ok is False, "javascript: URL should be rejected"
    print("  [PASS] validate_source_url rejects javascript: URL")


def test_validate_source_url_file():
    """8. validate_source_url() rejects file:// URLs."""
    ok, err = validate_source_url("file:///etc/passwd")
    assert ok is False, "file:// URL should be rejected"
    print("  [PASS] validate_source_url rejects file:// URL")


def test_validate_source_url_valid():
    """9. validate_source_url() accepts valid https URLs."""
    ok, err = validate_source_url("https://openai.com/blog")
    assert ok is True, f"valid https URL rejected: {err}"
    assert err is None
    ok2, err2 = validate_source_url("http://example.com")
    assert ok2 is True, f"valid http URL rejected: {err2}"
    print("  [PASS] validate_source_url accepts valid http/https URLs")


# ---------------------------------------------------------------------------
# normalize_url_item tests
# ---------------------------------------------------------------------------

def test_normalize_url_item_basic():
    """10. normalize_url_item() returns standard news_item with url_input source_type."""
    item = normalize_url_item(
        url="https://openai.com/blog/new-feature",
        title="OpenAI 发布新功能",
        summary="这是一项重要更新。",
    )
    assert item["source_type"] == "url_input", f"wrong source_type: {item['source_type']}"
    assert item["title"] == "OpenAI 发布新功能"
    assert item["url"] == "https://openai.com/blog/new-feature"
    assert "final_score" in item
    print("  [PASS] normalize_url_item returns url_input news_item")


def test_normalize_url_item_infers_source():
    """11. url_input news_item includes matched_source_id and trust_level from registry."""
    item = normalize_url_item(
        url="https://anthropic.com/news/model-update",
        title="Anthropic 模型更新",
    )
    assert item["matched_source_id"] == "anthropic_news", f"wrong matched_source_id: {item}"
    assert item["trust_level"] == "official", f"wrong trust_level: {item}"
    assert item["source"] == "Anthropic News", f"wrong source name: {item}"
    print("  [PASS] normalize_url_item infers source from domain")


def test_normalize_url_item_uses_source_id():
    """12. url_input with explicit source_id uses registry metadata."""
    item = normalize_url_item(
        url="https://example.com/paper",
        title="arXiv 论文",
        source_id="arxiv",
    )
    assert item["source_id"] == "arxiv", f"wrong source_id: {item}"
    assert item["matched_source_id"] == "arxiv", f"wrong matched_source_id: {item}"
    assert item["trust_level"] == "research", f"wrong trust_level: {item}"
    print("  [PASS] normalize_url_item uses explicit source_id")


def test_normalize_url_item_tags_merged():
    """13. url_input tags include registry defaults + user tags."""
    item = normalize_url_item(
        url="https://deepmind.google/blog/breakthrough",
        title="DeepMind 突破性研究",
        tags=["breakthrough", "research"],
    )
    tags = item["tags"]
    assert "deepmind" in tags, f"missing registry default tag: {tags}"
    assert "official" in tags, f"missing registry default tag: {tags}"
    assert "breakthrough" in tags, f"missing user tag: {tags}"
    assert "research" in tags, f"missing user tag: {tags}"
    print("  [PASS] normalize_url_item merges registry and user tags")


def test_normalize_url_item_missing_title():
    """14. normalize_url_item() raises ValueError for missing title."""
    try:
        normalize_url_item(url="https://example.com", title="")
        assert False, "should have raised ValueError"
    except ValueError as e:
        assert "title" in str(e).lower()
    print("  [PASS] normalize_url_item raises ValueError for missing title")


def test_normalize_url_item_invalid_url():
    """15. normalize_url_item() raises ValueError for invalid URL."""
    try:
        normalize_url_item(url="javascript:alert(1)", title="Bad URL")
        assert False, "should have raised ValueError"
    except ValueError as e:
        assert "url" in str(e).lower() or "javascript" in str(e).lower()
    print("  [PASS] normalize_url_item raises ValueError for invalid URL")


# ---------------------------------------------------------------------------
# API tests
# ---------------------------------------------------------------------------

def test_get_reliable_sources_api():
    """16. GET /api/reliable-sources returns ok=True and items."""
    resp = client.get("/api/reliable-sources")
    assert resp.status_code == 200, f"status {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data.get("ok") is True, f"ok not True: {data}"
    assert "items" in data, f"items missing: {data}"
    assert isinstance(data["items"], list), f"items not list: {data}"
    assert len(data["items"]) >= 7, f"expected >=7 sources, got {len(data['items'])}"
    assert data["count"] == len(data["items"]), "count mismatch"
    print("  [PASS] GET /api/reliable-sources returns ok=True and items")


def test_url_input_api_success():
    """17. POST /api/episode/source-contract with url_input succeeds."""
    resp = client.post("/api/episode/source-contract", json={
        "source_type": "url_input",
        "url": "https://openai.com/blog/gpt-5-release",
        "news_title": "OpenAI 发布 GPT-5",
        "news_summary": "这是官方公告。",
        "source_id": "openai_blog",
        "tags": ["gpt-5", "release"],
        "limit": 1,
        "template_id": "breaking_news_v1",
        "episode_title": "官方来源快讯",
        "episode_subtitle": "URL 输入生成",
    })
    assert resp.status_code == 200, f"status {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data.get("ok") is True, f"ok not True: {data}"
    assert data.get("source_type") == "url_input"
    print("  [PASS] url_input source_type returns ok=True")


def test_url_input_api_returns_news_item():
    """18. url_input returns a news_item with url and source_type=url_input."""
    resp = client.post("/api/episode/source-contract", json={
        "source_type": "url_input",
        "url": "https://anthropic.com/news/claude-update",
        "news_title": "Claude 更新说明",
        "limit": 1,
        "template_id": "breaking_news_v1",
    })
    data = resp.json()
    assert "news_items" in data, f"news_items missing: {data}"
    assert len(data["news_items"]) >= 1, "news_items is empty"
    item = data["news_items"][0]
    assert item["source_type"] == "url_input", f"wrong source_type: {item}"
    assert item["url"] == "https://anthropic.com/news/claude-update", f"wrong url: {item}"
    assert "matched_source_id" in item, f"matched_source_id missing: {item}"
    print("  [PASS] url_input news_item has url and source_type")


def test_url_input_api_returns_contract():
    """19. url_input returns episode_template_v1 contract."""
    resp = client.post("/api/episode/source-contract", json={
        "source_type": "url_input",
        "url": "https://deepmind.google/blog/ai-breakthrough",
        "news_title": "DeepMind AI 突破",
        "limit": 1,
        "template_id": "breaking_news_v1",
    })
    data = resp.json()
    assert "contract" in data, f"contract missing: {data}"
    assert data["contract"]["schema_version"] == "episode_template_v1"
    assert data["contract"]["template_id"] == "breaking_news_v1"
    assert "episode" in data["contract"]
    print("  [PASS] url_input returns episode_template_v1 contract")


def test_url_input_missing_url():
    """20. url_input without url returns ok=False."""
    resp = client.post("/api/episode/source-contract", json={
        "source_type": "url_input",
        "news_title": "测试新闻",
        "limit": 1,
        "template_id": "breaking_news_v1",
    })
    data = resp.json()
    assert data.get("ok") is False, f"should be ok=False: {data}"
    print("  [PASS] missing url returns ok=False")


def test_url_input_missing_news_title():
    """21. url_input without news_title returns ok=False."""
    resp = client.post("/api/episode/source-contract", json={
        "source_type": "url_input",
        "url": "https://example.com/article",
        "limit": 1,
        "template_id": "breaking_news_v1",
    })
    data = resp.json()
    assert data.get("ok") is False, f"should be ok=False: {data}"
    print("  [PASS] missing news_title returns ok=False")


def test_url_input_unsupported_template():
    """22. url_input with unsupported template_id returns ok=False."""
    resp = client.post("/api/episode/source-contract", json={
        "source_type": "url_input",
        "url": "https://example.com/article",
        "news_title": "测试",
        "limit": 1,
        "template_id": "timeline_brief_v1",
    })
    data = resp.json()
    assert data.get("ok") is False, f"should be ok=False: {data}"
    print("  [PASS] unsupported template_id returns ok=False")


def test_url_input_contract_no_secrets():
    """23. url_input contract contains no api_key/voice_id."""
    resp = client.post("/api/episode/source-contract", json={
        "source_type": "url_input",
        "url": "https://example.com/article",
        "news_title": "测试新闻标题",
        "limit": 1,
        "template_id": "breaking_news_v1",
    })
    data = resp.json()
    assert data.get("ok") is True
    contract_str = str(data["contract"])
    assert "api_key" not in contract_str.lower(), "api_key leaked into contract"
    assert "voice_id" not in contract_str.lower(), "voice_id leaked into contract"
    print("  [PASS] url_input contract contains no secrets")


def test_url_input_uses_episode_title_fields():
    """24. url_input respects episode_title and episode_subtitle."""
    resp = client.post("/api/episode/source-contract", json={
        "source_type": "url_input",
        "url": "https://microsoft.com/blog/ai-news",
        "news_title": "微软 AI 新闻",
        "limit": 1,
        "template_id": "breaking_news_v1",
        "episode_title": "微软官方公告",
        "episode_subtitle": "来自微软博客",
    })
    data = resp.json()
    assert data.get("ok") is True
    assert data["contract"]["episode"]["title"] == "微软官方公告"
    assert data["contract"]["episode"]["subtitle"] == "来自微软博客"
    print("  [PASS] url_input uses episode_title/episode_subtitle")


def test_url_input_contract_renderable():
    """25. url_input contract can be rendered by render_episode_stage_html."""
    from render_episode_html import render_episode_stage_html

    resp = client.post("/api/episode/source-contract", json={
        "source_type": "url_input",
        "url": "https://google.com/blog/ai-news",
        "news_title": "Google AI 新闻",
        "limit": 1,
        "template_id": "breaking_news_v1",
    })
    data = resp.json()
    assert data.get("ok") is True
    contract = data["contract"]

    # Should not raise
    html = render_episode_stage_html(contract, style_id="breaking_news_v1")
    assert isinstance(html, str), f"render returned non-string: {type(html)}"
    assert len(html) > 100, f"rendered HTML too short: {len(html)}"
    assert "<html" in html.lower(), "not valid HTML"
    print("  [PASS] url_input contract renders valid HTML")


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

def run_all():
    tests = [
        # reliable_sources module
        test_list_reliable_sources_returns_items,
        test_reliable_source_has_required_fields,
        test_infer_source_from_openai_url,
        test_infer_source_from_arxiv_url,
        test_infer_source_unknown_domain,
        test_validate_source_url_empty,
        test_validate_source_url_javascript,
        test_validate_source_url_file,
        test_validate_source_url_valid,
        # normalize_url_item
        test_normalize_url_item_basic,
        test_normalize_url_item_infers_source,
        test_normalize_url_item_uses_source_id,
        test_normalize_url_item_tags_merged,
        test_normalize_url_item_missing_title,
        test_normalize_url_item_invalid_url,
        # API
        test_get_reliable_sources_api,
        test_url_input_api_success,
        test_url_input_api_returns_news_item,
        test_url_input_api_returns_contract,
        test_url_input_missing_url,
        test_url_input_missing_news_title,
        test_url_input_unsupported_template,
        test_url_input_contract_no_secrets,
        test_url_input_uses_episode_title_fields,
        test_url_input_contract_renderable,
    ]

    print("=" * 60)
    print("CP44: Reliable Source Registry / URL Input MVP — Test Suite")
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
        print(f"ALL CP44 URL SOURCE PIPELINE TESTS PASSED ({passed}/{len(tests)})")
    else:
        print(f"FAILED: {failed} test(s) failed, {passed} passed out of {len(tests)}")
    print("=" * 60)
    return failed == 0


if __name__ == "__main__":
    ok = run_all()
    sys.exit(0 if ok else 1)
