#!/usr/bin/env python3
"""CP42: News Source to Episode Contract Pipeline — Test Suite

Tests the complete source-to-episode-contract pipeline:
  inline_text → normalize → news_item
  manual_items → normalize → news_item
  sample_pack → news_items
  news_items → build_episode_items_from_news → selected items with roles
  selected items → build_episode_contract_from_news_items → episode_template_v1

Run:
    python scripts/test_news_source_to_episode_contract.py
"""

import sys
import os

# Add project root to path so imports work when run from any directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.news_source_pipeline import (
    normalize_inline_text,
    normalize_manual_items,
    load_sample_news_pack,
    score_news_item,
    build_episode_items_from_news,
    build_episode_contract_from_news_items,
    build_contract_from_inline_text,
    build_contract_from_sample_pack,
    contract_has_secrets,
    DEFAULT_TEMPLATE_ID,
    DEFAULT_EPISODE_TITLE,
    MAX_EPISODE_ITEMS,
    PER_SEGMENT_DURATION_SEC,
    OPENING_DURATION_SEC,
    CLOSING_DURATION_SEC,
    TRANSITION_DURATION_SEC,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fail(msg: str) -> None:
    print(f"  [FAIL] {msg}")
    global passed, failed
    failed += 1


def pass_(msg: str) -> None:
    print(f"  [PASS] {msg}")
    global passed
    passed += 1


passed = 0
failed = 0


# ---------------------------------------------------------------------------
# Test 1: normalize_inline_text — basic conversion
# ---------------------------------------------------------------------------

def test_inline_text_basic():
    print("\nTest 1: normalize_inline_text — basic conversion")
    text = "OpenAI 发布新的开发者工具\n这是关于新工具的详细描述。"
    item = normalize_inline_text(text, source="TestSource")

    assert "id" in item, fail("id field missing")
    assert item["id"].startswith("news_"), fail(f"id format wrong: {item['id']}")
    assert item["title"] == "OpenAI 发布新的开发者工具", fail(f"title wrong: {item['title']}")
    assert "summary" in item, fail("summary field missing")
    assert item["source"] == "TestSource", fail(f"source wrong: {item['source']}")
    assert item["source_type"] == "inline_text", fail("source_type wrong")
    assert isinstance(item["final_score"], float), fail("final_score not float")
    assert "tags" in item, fail("tags field missing")
    pass_("basic inline_text → news_item")


# ---------------------------------------------------------------------------
# Test 2: normalize_inline_text — title truncated at 80 chars
# ---------------------------------------------------------------------------

def test_inline_text_title_truncated():
    print("\nTest 2: normalize_inline_text — long title truncation")
    long_title = "A" * 100
    item = normalize_inline_text(long_title + "\nbody")
    assert len(item["title"]) <= 80, fail(f"title not truncated: {len(item['title'])}")
    assert item["title"].endswith("..."), fail("truncated title should end with ...")
    pass_("long title truncated to 80 chars")


# ---------------------------------------------------------------------------
# Test 3: normalize_inline_text — empty text raises
# ---------------------------------------------------------------------------

def test_inline_text_empty_raises():
    print("\nTest 3: normalize_inline_text — empty text raises ValueError")
    try:
        normalize_inline_text("")
        fail("did not raise ValueError for empty text")
    except ValueError:
        pass_("raises ValueError for empty text")


# ---------------------------------------------------------------------------
# Test 4: normalize_manual_items — basic conversion
# ---------------------------------------------------------------------------

def test_manual_items_basic():
    print("\nTest 4: normalize_manual_items — basic conversion")
    raw = [
        {
            "title": "Test News 1",
            "summary": "Summary of test news 1",
            "source": "MySource",
            "url": "https://example.com/1",
            "final_score": 8.5,
            "points": 200,
            "comments": 10,
            "tags": ["ai", "model"],
        },
        {
            "title": "Test News 2",
            "summary": "Summary of test news 2",
        },
    ]
    items = normalize_manual_items(raw)

    assert len(items) == 2, fail(f"expected 2 items, got {len(items)}")
    assert items[0]["title"] == "Test News 1", fail("first item title wrong")
    assert items[0]["source"] == "MySource", fail("source not preserved")
    assert items[0]["points"] == 200, fail("points not preserved")
    assert items[1]["source"] == "Manual", fail("default source not set")
    assert items[1]["final_score"] == 0.0, fail("default score not 0")
    pass_("manual_items normalized correctly")


# ---------------------------------------------------------------------------
# Test 5: normalize_manual_items — missing title raises
# ---------------------------------------------------------------------------

def test_manual_items_missing_title():
    print("\nTest 5: normalize_manual_items — missing title raises")
    try:
        normalize_manual_items([{"summary": "no title here"}])
        fail("did not raise for missing title")
    except (ValueError, TypeError):
        pass_("raises for missing title")


# ---------------------------------------------------------------------------
# Test 6: load_sample_news_pack — returns at least 3 items
# ---------------------------------------------------------------------------

def test_sample_pack_count():
    print("\nTest 6: load_sample_news_pack — returns at least 3 items")
    pack = load_sample_news_pack()
    assert isinstance(pack, list), fail("not a list")
    assert len(pack) >= 3, fail(f"only {len(pack)} items, expected >= 3")
    assert all(item.get("source_type") == "sample_pack" for item in pack), fail("source_type not sample_pack")
    pass_(f"sample pack has {len(pack)} items")


# ---------------------------------------------------------------------------
# Test 7: score_news_item — returns 0–10 range
# ---------------------------------------------------------------------------

def test_score_range():
    print("\nTest 7: score_news_item — returns 0–10 range")
    item = {"title": "Test", "summary": "", "source": "", "tags": []}
    for _ in range(10):
        item["title"] += " model "  # accumulate keywords
    score = score_news_item(item)
    assert 0.0 <= score <= 10.0, fail(f"score {score} out of range")
    pass_(f"score {score} within 0–10 range")


# ---------------------------------------------------------------------------
# Test 8: score_news_item — same input gives same output
# ---------------------------------------------------------------------------

def test_score_deterministic():
    print("\nTest 8: score_news_item — deterministic")
    item = {"title": "OpenAI model benchmark", "summary": "AI model launch", "source": "", "tags": ["openai", "model"]}
    s1 = score_news_item(item)
    s2 = score_news_item(item)
    assert s1 == s2, fail("score not deterministic")
    pass_(f"deterministic: {s1}")


# ---------------------------------------------------------------------------
# Test 9: build_episode_items_from_news — sorted by score, first is lead
# ---------------------------------------------------------------------------

def test_episode_items_sorted_and_lead():
    print("\nTest 9: build_episode_items_from_news — sorted by score, first is lead")
    items = [
        {"title": "Low Score", "final_score": 3.0, "points": 50},
        {"title": "High Score", "final_score": 9.0, "points": 100},
        {"title": "Mid Score", "final_score": 6.0, "points": 80},
    ]
    selected = build_episode_items_from_news(items)

    assert selected[0]["title"] == "High Score", fail("not sorted by score descending")
    assert selected[0]["role"] == "lead", fail("first item not marked lead")
    for item in selected[1:]:
        assert item["role"] == "supporting", fail(f"non-lead item has role {item['role']}")
    pass_("items sorted by score, first is lead")


# ---------------------------------------------------------------------------
# Test 10: build_episode_items_from_news — respects limit and max cap
# ---------------------------------------------------------------------------

def test_episode_items_limit():
    print("\nTest 10: build_episode_items_from_news — respects limit")
    items = [{"title": f"Item {i}", "final_score": 10.0 - i * 0.1, "points": 100 - i}
             for i in range(8)]
    selected = build_episode_items_from_news(items, limit=3)
    assert len(selected) == 3, fail(f"expected 3, got {len(selected)}")

    # Also verify the hard cap
    selected_all = build_episode_items_from_news(items, limit=99)
    assert len(selected_all) == MAX_EPISODE_ITEMS, fail(f"hard cap {MAX_EPISODE_ITEMS} violated")
    pass_(f"limit respected: {len(selected)}, hard cap: {MAX_EPISODE_ITEMS}")


# ---------------------------------------------------------------------------
# Test 11: build_episode_contract_from_news_items — outputs episode_template_v1
# ---------------------------------------------------------------------------

def test_contract_schema_version():
    print("\nTest 11: build_episode_contract_from_news_items — schema_version")
    items = [
        {"title": "News 1", "role": "lead", "final_score": 9.0, "summary": "Summary 1", "source": "S", "tags": []},
        {"title": "News 2", "role": "supporting", "final_score": 7.0, "summary": "Summary 2", "source": "S", "tags": []},
    ]
    contract = build_episode_contract_from_news_items(items)

    assert contract.get("schema_version") == "episode_template_v1", \
        fail(f"schema_version wrong: {contract.get('schema_version')}")
    assert contract.get("template_id") == DEFAULT_TEMPLATE_ID, \
        fail(f"template_id wrong: {contract.get('template_id')}")
    pass_("schema_version is episode_template_v1")


# ---------------------------------------------------------------------------
# Test 12: contract template_id defaults to breaking_news_v1
# ---------------------------------------------------------------------------

def test_contract_default_template_id():
    print("\nTest 12: contract — default template_id is breaking_news_v1")
    items = [{"title": "News 1", "role": "lead", "final_score": 8.0, "summary": "", "source": "", "tags": []}]
    contract = build_episode_contract_from_news_items(items)
    assert contract["template_id"] == "breaking_news_v1", \
        fail(f"default template_id: {contract['template_id']}")
    pass_("default template_id is breaking_news_v1")


# ---------------------------------------------------------------------------
# Test 13: contract — news_cards count equals input items
# ---------------------------------------------------------------------------

def test_contract_news_cards_count():
    print("\nTest 13: contract — news_cards count matches input items")
    for n in [1, 2, 3, 4, 5]:
        items = [
            {"title": f"News {i}", "role": "lead" if i == 0 else "supporting",
             "final_score": 9.0 - i * 0.5, "summary": "", "source": "", "tags": []}
            for i in range(n)
        ]
        contract = build_episode_contract_from_news_items(items)
        news_cards = contract.get("sections", {}).get("news_cards", [])
        assert len(news_cards) == n, \
            fail(f"n={n}: expected {n} news_cards, got {len(news_cards)}")
    pass_("news_cards count matches input items")


# ---------------------------------------------------------------------------
# Test 14: contract — timeline markers non-empty
# ---------------------------------------------------------------------------

def test_contract_timeline_markers():
    print("\nTest 14: contract — timeline markers non-empty")
    items = [
        {"title": "News 1", "role": "lead", "final_score": 8.0, "summary": "", "source": "", "tags": []},
        {"title": "News 2", "role": "supporting", "final_score": 7.0, "summary": "", "source": "", "tags": []},
    ]
    contract = build_episode_contract_from_news_items(items)
    markers = contract.get("timeline", {}).get("markers", [])

    assert len(markers) >= 3, fail(f"too few markers: {len(markers)}")  # at least open+2seg+close
    marker_types = {m["type"] for m in markers}
    assert "opening" in marker_types, fail("no opening marker")
    assert "closing" in marker_types, fail("no closing marker")
    pass_(f"timeline has {len(markers)} markers: {marker_types}")


# ---------------------------------------------------------------------------
# Test 15: contract — constraints all present and no_mp4 is False
# ---------------------------------------------------------------------------

def test_contract_constraints():
    print("\nTest 15: contract — constraints are present")
    items = [{"title": "News 1", "role": "lead", "final_score": 8.0, "summary": "", "source": "", "tags": []}]
    contract = build_episode_contract_from_news_items(items)
    constraints = contract.get("constraints", {})

    for key in ["no_external_assets", "no_script", "no_real_render", "no_audio", "no_mp4"]:
        assert key in constraints, fail(f"missing constraint: {key}")

    assert constraints["no_mp4"] is False, fail("no_mp4 should be False (exportable)")
    assert constraints["no_external_assets"] is True, fail("no_external_assets should be True")
    pass_(f"constraints: {constraints}")


# ---------------------------------------------------------------------------
# Test 16: contract — no API key / voice_id leakage
# ---------------------------------------------------------------------------

def test_contract_no_secrets():
    print("\nTest 16: contract — no API key / voice_id leakage")
    items = [{"title": "News 1", "role": "lead", "final_score": 8.0,
              "summary": "Model score and benchmark details", "source": "", "tags": []}]
    contract = build_episode_contract_from_news_items(items)
    assert not contract_has_secrets(contract), \
        fail("contract_has_secrets returned True for clean contract")
    pass_("no API key / voice_id in clean contract")


# ---------------------------------------------------------------------------
# Test 17: contract — can be rendered by Python HTML generator
# ---------------------------------------------------------------------------

def test_contract_renders_html():
    print("\nTest 17: contract — compatible with render_episode_html")
    items = [
        {"title": "Lead News Story", "role": "lead", "final_score": 9.0,
         "summary": "This is the main news.", "source": "Sample", "tags": ["ai"]},
        {"title": "Supporting News", "role": "supporting", "final_score": 7.0,
         "summary": "Secondary story.", "source": "Sample", "tags": []},
    ]
    contract = build_episode_contract_from_news_items(items)

    try:
        from src.render_episode_html import render_episode_stage_html
        html = render_episode_stage_html(contract, style_id="breaking_news_v1")
        assert "<html" in html, fail("output is not HTML")
        assert "Lead News Story" in html, fail("lead headline missing from HTML")
        assert "video-stage" in html, fail("video-stage class missing from HTML")
        pass_(f"rendered {len(html)} char HTML successfully")
    except Exception as e:
        fail(f"render_episode_html raised: {e}")


# ---------------------------------------------------------------------------
# Test 18: build_contract_from_inline_text — full shortcut
# ---------------------------------------------------------------------------

def test_full_shortcut_inline():
    print("\nTest 18: build_contract_from_inline_text — full shortcut")
    text = "Anthropic 发布新的 Claude 安全更新\n详细描述了该更新的内容和影响。"
    contract = build_contract_from_inline_text(text, title="AI 安全更新", subtitle="最新动态")

    assert contract["schema_version"] == "episode_template_v1", fail("wrong schema_version")
    assert contract["episode"]["title"] == "AI 安全更新", fail("title not set")
    assert contract["episode"]["subtitle"] == "最新动态", fail("subtitle not set")
    news_cards = contract["sections"]["news_cards"]
    assert len(news_cards) >= 1, fail("no news_cards")
    pass_("build_contract_from_inline_text shortcut works")


# ---------------------------------------------------------------------------
# Test 19: build_contract_from_sample_pack — full shortcut
# ---------------------------------------------------------------------------

def test_full_shortcut_sample():
    print("\nTest 19: build_contract_from_sample_pack — full shortcut")
    contract = build_contract_from_sample_pack(title="AI 周刊", subtitle="本周要闻")

    assert contract["schema_version"] == "episode_template_v1", fail("wrong schema_version")
    assert contract["episode"]["title"] == "AI 周刊", fail("title not set")
    news_cards = contract["sections"]["news_cards"]
    assert len(news_cards) >= 3, fail(f"only {len(news_cards)} news_cards")
    pass_(f"build_contract_from_sample_pack shortcut works with {len(news_cards)} cards")


# ---------------------------------------------------------------------------
# Test 20: episode contract estimated_duration matches marker timeline
# ---------------------------------------------------------------------------

def test_contract_duration_consistency():
    print("\nTest 20: contract — estimated_duration matches formula sum")
    items = [
        {"title": f"News {i}", "role": "lead" if i == 0 else "supporting",
         "final_score": 9.0 - i * 0.5, "summary": "", "source": "", "tags": []}
        for i in range(3)
    ]
    contract = build_episode_contract_from_news_items(items)
    est = contract["episode"]["estimated_duration_sec"]

    # Verify estimated_duration matches the expected formula
    n = 3
    expected = OPENING_DURATION_SEC + n * PER_SEGMENT_DURATION_SEC + (n - 1) * TRANSITION_DURATION_SEC + CLOSING_DURATION_SEC
    assert est == expected, fail(f"estimated_duration={est} but expected {expected}")
    pass_(f"estimated_duration={est}s matches formula sum")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    global passed, failed
    print("=" * 60)
    print("CP42: News Source to Episode Contract Pipeline — Test Suite")
    print("=" * 60)

    tests = [
        test_inline_text_basic,
        test_inline_text_title_truncated,
        test_inline_text_empty_raises,
        test_manual_items_basic,
        test_manual_items_missing_title,
        test_sample_pack_count,
        test_score_range,
        test_score_deterministic,
        test_episode_items_sorted_and_lead,
        test_episode_items_limit,
        test_contract_schema_version,
        test_contract_default_template_id,
        test_contract_news_cards_count,
        test_contract_timeline_markers,
        test_contract_constraints,
        test_contract_no_secrets,
        test_contract_renders_html,
        test_full_shortcut_inline,
        test_full_shortcut_sample,
        test_contract_duration_consistency,
    ]

    for test in tests:
        try:
            test()
        except Exception as e:
            fail(f"raised {type(e).__name__}: {e}")

    print("\n" + "=" * 60)
    if failed == 0:
        print(f"ALL CP42 NEWS SOURCE PIPELINE TESTS PASSED ({passed}/{passed})")
        print("=" * 60)
        return 0
    else:
        print(f"FAILED: {failed} / {passed + failed}")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
