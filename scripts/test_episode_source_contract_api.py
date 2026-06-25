#!/usr/bin/env python3
"""CP43: Test POST /api/episode/source-contract API endpoint.

Tests all source types, validation, and contract output format.
Uses FastAPI TestClient — no real outputs, no real LLM/TTS.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fastapi.testclient import TestClient
from server import app

client = TestClient(app)


def test_sample_pack_success():
    """1. POST /api/episode/source-contract sample_pack succeeds."""
    resp = client.post("/api/episode/source-contract", json={
        "source_type": "sample_pack",
        "limit": 4,
        "template_id": "breaking_news_v1",
        "title": "今日 AI 前沿速览",
        "subtitle": "样例新闻栏目",
    })
    assert resp.status_code == 200, f"status {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data.get("ok") is True, f"ok not True: {data}"
    assert data.get("source_type") == "sample_pack"
    print("  [PASS] sample_pack returns ok=True")


def test_sample_pack_returns_news_items():
    """2. sample_pack returns news_items."""
    resp = client.post("/api/episode/source-contract", json={
        "source_type": "sample_pack",
        "limit": 4,
        "template_id": "breaking_news_v1",
        "title": "今日 AI 前沿速览",
        "subtitle": "样例新闻栏目",
    })
    data = resp.json()
    assert "news_items" in data, f"news_items missing: {data}"
    assert isinstance(data["news_items"], list), f"news_items not list: {data}"
    assert len(data["news_items"]) > 0, "news_items is empty"
    print(f"  [PASS] returns {len(data['news_items'])} news_items")


def test_sample_pack_returns_episode_items():
    """3. sample_pack returns episode_items."""
    resp = client.post("/api/episode/source-contract", json={
        "source_type": "sample_pack",
        "limit": 4,
        "template_id": "breaking_news_v1",
        "title": "今日 AI 前沿速览",
        "subtitle": "样例新闻栏目",
    })
    data = resp.json()
    assert "episode_items" in data, f"episode_items missing: {data}"
    assert isinstance(data["episode_items"], list), f"episode_items not list: {data}"
    print(f"  [PASS] returns {len(data['episode_items'])} episode_items")


def test_sample_pack_contract_schema():
    """4. contract.schema_version == episode_template_v1."""
    resp = client.post("/api/episode/source-contract", json={
        "source_type": "sample_pack",
        "limit": 4,
        "template_id": "breaking_news_v1",
        "title": "今日 AI 前沿速览",
        "subtitle": "样例新闻栏目",
    })
    data = resp.json()
    contract = data.get("contract", {})
    assert contract.get("schema_version") == "episode_template_v1", \
        f"schema_version wrong: {contract.get('schema_version')}"
    print("  [PASS]contract.schema_version == episode_template_v1")


def test_sample_pack_template_id():
    """5. contract.template_id == breaking_news_v1."""
    resp = client.post("/api/episode/source-contract", json={
        "source_type": "sample_pack",
        "limit": 4,
        "template_id": "breaking_news_v1",
        "title": "今日 AI 前沿速览",
        "subtitle": "样例新闻栏目",
    })
    data = resp.json()
    contract = data.get("contract", {})
    assert contract.get("template_id") == "breaking_news_v1", \
        f"template_id wrong: {contract.get('template_id')}"
    print("  [PASS]contract.template_id == breaking_news_v1")


def test_inline_text_success():
    """6. inline_text succeeds."""
    resp = client.post("/api/episode/source-contract", json={
        "source_type": "inline_text",
        "text": "OpenAI 发布新的开发者工具能力\n这是正文内容。",
        "source": "Manual",
        "url": "",
        "limit": 1,
        "template_id": "breaking_news_v1",
        "title": "单条新闻快讯",
        "subtitle": "粘贴文本生成",
    })
    assert resp.status_code == 200, f"status {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data.get("ok") is True, f"ok not True: {data}"
    assert data.get("source_type") == "inline_text"
    print("  [PASS]inline_text returns ok=True")


def test_manual_items_success():
    """7. manual_items succeeds."""
    resp = client.post("/api/episode/source-contract", json={
        "source_type": "manual_items",
        "items": [
            {
                "title": "测试新闻标题",
                "summary": "这是测试摘要内容",
                "source": "Manual",
                "url": "",
                "final_score": 8.0,
                "points": 100,
                "comments": 10,
                "tags": ["test"],
            }
        ],
        "limit": 1,
        "template_id": "breaking_news_v1",
        "title": "手动输入栏目",
        "subtitle": "手动输入测试",
    })
    assert resp.status_code == 200, f"status {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data.get("ok") is True, f"ok not True: {data}"
    assert data.get("source_type") == "manual_items"
    print("  [PASS]manual_items returns ok=True")


def test_invalid_source_type():
    """8. invalid source_type returns 400 or ok=False."""
    resp = client.post("/api/episode/source-contract", json={
        "source_type": "unknown_type",
        "limit": 4,
        "template_id": "breaking_news_v1",
    })
    data = resp.json()
    # Accept either HTTP 400 or 200 with ok=False
    assert resp.status_code == 400 or data.get("ok") is False, \
        f"expected 400 or ok=False, got {resp.status_code}: {data}"
    print("  [PASS]invalid source_type returns error")


def test_empty_inline_text():
    """9. empty inline_text returns failure."""
    resp = client.post("/api/episode/source-contract", json={
        "source_type": "inline_text",
        "text": "",
        "limit": 1,
        "template_id": "breaking_news_v1",
    })
    data = resp.json()
    assert data.get("ok") is False, f"expected ok=False for empty text: {data}"
    print("  [PASS]empty inline_text returns ok=False")


def test_overly_long_inline_text():
    """10. overly long inline_text returns failure."""
    long_text = "x" * 25_000
    resp = client.post("/api/episode/source-contract", json={
        "source_type": "inline_text",
        "text": long_text,
        "limit": 1,
        "template_id": "breaking_news_v1",
    })
    data = resp.json()
    assert data.get("ok") is False, f"expected ok=False for long text: {data}"
    print("  [PASS]overly long inline_text returns ok=False")


def test_manual_items_over_limit():
    """11. manual_items exceeding MAX_MANUAL_ITEMS returns failure."""
    items = [
        {
            "title": f"新闻标题 {i}",
            "summary": "摘要",
            "source": "Manual",
            "final_score": 7.0,
        }
        for i in range(15)
    ]
    resp = client.post("/api/episode/source-contract", json={
        "source_type": "manual_items",
        "items": items,
        "limit": 5,
        "template_id": "breaking_news_v1",
    })
    data = resp.json()
    assert data.get("ok") is False, f"expected ok=False for >10 items: {data}"
    print("  [PASS]manual_items over limit returns ok=False")


def test_unsupported_template_id():
    """12. unsupported template_id returns failure."""
    resp = client.post("/api/episode/source-contract", json={
        "source_type": "sample_pack",
        "limit": 4,
        "template_id": "timeline_brief_v1",
        "title": "测试",
        "subtitle": "测试副标题",
    })
    data = resp.json()
    assert data.get("ok") is False, f"expected ok=False for unsupported template_id: {data}"
    print("  [PASS]unsupported template_id returns ok=False")


def test_contract_no_secrets():
    """13. contract contains no api_key / voice_id."""
    resp = client.post("/api/episode/source-contract", json={
        "source_type": "sample_pack",
        "limit": 4,
        "template_id": "breaking_news_v1",
        "title": "今日 AI 前沿速览",
        "subtitle": "样例新闻栏目",
    })
    data = resp.json()
    import json as _json
    contract_str = _json.dumps(data.get("contract", {}))
    has_secret = (
        "api_key" in contract_str.lower() or
        "voice_id" in contract_str.lower()
    )
    assert not has_secret, "contract contains api_key or voice_id"
    print("  [PASS]contract contains no api_key/voice_id")


def test_contract_can_render():
    """14. contract can be passed to render_episode_stage_html()."""
    resp = client.post("/api/episode/source-contract", json={
        "source_type": "sample_pack",
        "limit": 4,
        "template_id": "breaking_news_v1",
        "title": "今日 AI 前沿速览",
        "subtitle": "样例新闻栏目",
    })
    data = resp.json()
    contract = data.get("contract", {})

    # Verify it has required fields for rendering
    assert contract.get("schema_version") == "episode_template_v1"
    assert "episode" in contract
    assert "sections" in contract
    assert "news_cards" in contract["sections"]
    assert len(contract["sections"]["news_cards"]) > 0

    # Try calling render_episode_stage_html
    from render_episode_html import render_episode_stage_html
    html = render_episode_stage_html(contract, style_id="breaking_news_v1")
    assert isinstance(html, str) and len(html) > 100
    assert "<!DOCTYPE html>" in html or "<html" in html
    print("  [PASS]contract renders valid HTML via render_episode_stage_html()")


def test_limit_clamped_to_5():
    """15. limit > 5 is clamped to 5."""
    resp = client.post("/api/episode/source-contract", json={
        "source_type": "sample_pack",
        "limit": 99,
        "template_id": "breaking_news_v1",
        "title": "测试",
        "subtitle": "测试",
    })
    data = resp.json()
    episode_items = data.get("episode_items", [])
    assert len(episode_items) <= 5, f"episode_items > 5: {len(episode_items)}"
    print(f"  [PASS] limit clamped: {len(episode_items)} episode_items (max 5)")


def run_all():
    tests = [
        test_sample_pack_success,
        test_sample_pack_returns_news_items,
        test_sample_pack_returns_episode_items,
        test_sample_pack_contract_schema,
        test_sample_pack_template_id,
        test_inline_text_success,
        test_manual_items_success,
        test_invalid_source_type,
        test_empty_inline_text,
        test_overly_long_inline_text,
        test_manual_items_over_limit,
        test_unsupported_template_id,
        test_contract_no_secrets,
        test_contract_can_render,
        test_limit_clamped_to_5,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL] {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  [ERROR] {t.__name__}: {e}")
            failed += 1

    print()
    if failed == 0:
        print("ALL CP43 SOURCE CONTRACT API TESTS PASSED")
    else:
        print(f"CP43 TESTS: {passed} passed, {failed} failed")
        sys.exit(1)


if __name__ == "__main__":
    run_all()
