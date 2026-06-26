"""LLM-backed episode generation (CP61).

Turns a raw pasted news text into a structured episode_template_v1 contract using
a real LLM (via src.llm.client). The LLM breaks the news into a lead + supporting
points and writes a spoken narration script per section. The narration is embedded
back into the contract so episode_tts reads the real script (not headline stitching).

Reuses:
  - src.llm.client.create_llm_client / generate_text
  - src.llm.json_utils.extract_json_object
  - src.news_source_pipeline.build_episode_contract_from_news_items
  - src.news_source_pipeline.contract_has_secrets

On any failure (LLM unavailable, bad JSON, network blocked) the caller is expected
to fall back to the rule-based pipeline — this module raises rather than guessing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROMPT_PATH = PROJECT_ROOT / "prompts" / "news_to_episode.md"

MAX_CARDS = 4


def _load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _clean(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _normalize_cards(raw_cards: Any) -> list[dict]:
    """Coerce LLM cards into a clean list with exactly one lead, max MAX_CARDS."""
    cards = []
    for c in (raw_cards or []):
        if not isinstance(c, dict):
            continue
        headline = _clean(c.get("headline"))
        if not headline:
            continue
        cards.append({
            "role": "lead" if _clean(c.get("role")).lower() == "lead" else "supporting",
            "headline": headline,
            "summary": _clean(c.get("summary")),
            "narration": _clean(c.get("narration")),
            "image_prompt": _clean(c.get("image_prompt")),
        })
        if len(cards) >= MAX_CARDS:
            break

    if not cards:
        raise ValueError("LLM produced no usable cards")

    # Force exactly one lead, at position 0.
    leads = [i for i, c in enumerate(cards) if c["role"] == "lead"]
    if leads:
        first_lead = leads[0]
        if first_lead != 0:
            cards.insert(0, cards.pop(first_lead))
    for i, c in enumerate(cards):
        c["role"] = "lead" if i == 0 else "supporting"
    return cards


def generate_episode_contract_from_text(
    text: str,
    *,
    profile: Optional[str] = None,
) -> dict[str, Any]:
    """Generate an episode_template_v1 contract from raw news text via real LLM.

    Returns a dict: {"contract": <episode_template_v1>, "model": <profile>,
    "script": <full narration text>}.

    Raises ValueError / RuntimeError on any failure (caller falls back to rules).
    """
    from src.llm.client import create_llm_client
    from src.llm.json_utils import extract_json_object
    from src.news_source_pipeline import (
        build_episode_contract_from_news_items,
        contract_has_secrets,
        DEFAULT_TEMPLATE_ID,
    )

    text = _clean(text)
    if not text:
        raise ValueError("text is empty")

    client = create_llm_client(profile)
    system_prompt = _load_prompt()

    # LLM output can occasionally be truncated/unparseable — retry a couple times.
    data = None
    last_err: Optional[Exception] = None
    for _ in range(3):
        try:
            response = client.generate_text(system_prompt, text)
            data = extract_json_object(response)
            break
        except Exception as exc:  # parse error or transient API error
            last_err = exc
    if data is None:
        raise ValueError(f"LLM did not return parseable JSON: {last_err}")

    cards = _normalize_cards(data.get("cards"))

    episode_title = _clean(data.get("episode_title")) or (cards[0]["headline"] if cards else "今日要闻")
    episode_subtitle = _clean(data.get("episode_subtitle")) or "AI 拆解 · 发布前请人工核实"

    # Map LLM cards -> news_items for the shared contract builder.
    news_items = [
        {
            "id": f"llm_{i + 1}",
            "title": c["headline"],
            "summary": c["summary"],
            "role": c["role"],
            "order": i + 1,
            "source": "LLM",
        }
        for i, c in enumerate(cards)
    ]

    contract = build_episode_contract_from_news_items(
        news_items,
        template_id=DEFAULT_TEMPLATE_ID,
        title=episode_title,
        subtitle=episode_subtitle,
    )

    # Embed narration back into the contract so episode_tts uses the real script.
    sections = contract.setdefault("sections", {})
    opening = sections.setdefault("opening", {})
    opening["narration"] = _clean(data.get("opening_narration"))

    news_cards = sections.get("news_cards") or []
    for i, card in enumerate(news_cards):
        if i < len(cards):
            card["narration"] = cards[i]["narration"]
            card["image_prompt"] = cards[i].get("image_prompt", "")
            if not _clean(card.get("description")) and cards[i]["summary"]:
                card["description"] = cards[i]["summary"]

    closing = sections.setdefault("closing", {})
    closing_title = _clean(data.get("closing_title"))
    if closing_title:
        closing["title"] = closing_title
    closing["narration"] = _clean(data.get("closing_narration"))

    # Mark provenance + facts-guard for the UI / downstream.
    contract["content_source"] = "llm"
    contract["facts_guard"] = "AI 摘要，发布前请人工核实"

    if contract_has_secrets(contract):
        raise ValueError("Generated contract contains disallowed secrets")

    # Full narration text (for convenience / preview).
    parts = [opening.get("narration", "")]
    parts += [c.get("narration", "") for c in cards]
    parts.append(closing.get("narration", ""))
    full_script = " ".join(p for p in parts if p).strip()

    return {
        "contract": contract,
        "model": profile or "default",
        "script": full_script,
    }
