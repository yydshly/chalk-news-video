"""CP61 test: LLM episode mapping (mocked LLM, no real API).

Verifies generate_episode_contract_from_text() maps LLM JSON into a valid
episode_template_v1 contract with narration embedded, and that _normalize_cards
clamps to exactly one lead / max 4 cards.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import src.llm.client as llm_client_mod
from src import llm_episode
from src.episode_tts import build_narration_script


class _FakeClient:
    def __init__(self, payload):
        self._payload = payload

    def generate_text(self, system_prompt, user_prompt):
        # Wrap in a code fence + prose to exercise extract_json_object robustness.
        return "好的，这是结果：\n```json\n" + json.dumps(self._payload, ensure_ascii=False) + "\n```"


def _patch_client(payload):
    llm_client_mod.create_llm_client = lambda profile=None, **kw: _FakeClient(payload)


def test_basic_mapping():
    _patch_client({
        "episode_title": "测试标题",
        "episode_subtitle": "测试副标题",
        "opening_narration": "开场旁白。",
        "cards": [
            {"role": "lead", "headline": "主线标题", "summary": "主线摘要", "narration": "主线旁白。"},
            {"role": "supporting", "headline": "补充标题", "summary": "补充摘要", "narration": "补充旁白。"},
        ],
        "closing_title": "结语标题",
        "closing_narration": "结尾旁白。",
    })
    out = llm_episode.generate_episode_contract_from_text("一些新闻文本")
    c = out["contract"]
    assert c["schema_version"] == "episode_template_v1", c.get("schema_version")
    assert c["episode"]["title"] == "测试标题"
    assert c.get("content_source") == "llm"
    cards = c["sections"]["news_cards"]
    assert len(cards) == 2
    assert cards[0]["role"] == "lead"
    assert cards[0]["narration"] == "主线旁白。"
    assert c["sections"]["opening"]["narration"] == "开场旁白。"
    assert c["sections"]["closing"]["narration"] == "结尾旁白。"
    # Narration script must use the LLM narration, not headline stitching.
    segs = build_narration_script(c)
    texts = [s["text"] for s in segs]
    assert "开场旁白。" in texts
    assert "主线旁白。" in texts
    assert "结尾旁白。" in texts
    print("[PASS] test_basic_mapping")


def test_forces_single_lead():
    # Two leads provided -> only the first stays lead.
    _patch_client({
        "episode_title": "T", "episode_subtitle": "S", "opening_narration": "o",
        "cards": [
            {"role": "supporting", "headline": "A", "summary": "a", "narration": "na"},
            {"role": "lead", "headline": "B", "summary": "b", "narration": "nb"},
            {"role": "lead", "headline": "C", "summary": "c", "narration": "nc"},
        ],
        "closing_title": "c", "closing_narration": "cn",
    })
    c = llm_episode.generate_episode_contract_from_text("x")["contract"]
    roles = [card["role"] for card in c["sections"]["news_cards"]]
    assert roles.count("lead") == 1, roles
    assert roles[0] == "lead", roles
    # The first declared lead (B) should be promoted to front.
    assert c["sections"]["news_cards"][0]["headline"] == "B"
    print("[PASS] test_forces_single_lead")


def test_caps_and_promotes_lead_when_missing():
    # No lead + more than 4 cards -> first becomes lead, capped at 4.
    _patch_client({
        "episode_title": "T", "episode_subtitle": "S", "opening_narration": "o",
        "cards": [
            {"role": "supporting", "headline": f"H{i}", "summary": f"s{i}", "narration": f"n{i}"}
            for i in range(6)
        ],
        "closing_title": "c", "closing_narration": "cn",
    })
    c = llm_episode.generate_episode_contract_from_text("x")["contract"]
    cards = c["sections"]["news_cards"]
    assert len(cards) == llm_episode.MAX_CARDS
    assert sum(1 for x in cards if x["role"] == "lead") == 1
    assert cards[0]["role"] == "lead"
    print("[PASS] test_caps_and_promotes_lead_when_missing")


def test_empty_cards_raises():
    _patch_client({"episode_title": "T", "cards": [], "closing_title": "c"})
    try:
        llm_episode.generate_episode_contract_from_text("x")
        assert False, "should have raised"
    except ValueError:
        print("[PASS] test_empty_cards_raises")


if __name__ == "__main__":
    test_basic_mapping()
    test_forces_single_lead()
    test_caps_and_promotes_lead_when_missing()
    test_empty_cards_raises()
    print("\nAll CP61 llm_episode tests passed.")
