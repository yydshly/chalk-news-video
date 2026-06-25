"""News Source to Episode Contract Pipeline (CP42).

Provides a local, controllable, testable pipeline:
  input sources → normalized news_items → episode_template_v1 contract

Supported source types:
  - inline_text: user-pasted raw news text
  - manual_items: manually provided structured news items
  - sample_pack: built-in sample news pack (mock only)

No real LLM, no real TTS, no web crawler, no real news API.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_TEMPLATE_ID = "breaking_news_v1"
DEFAULT_EPISODE_TITLE = "今日 AI 前沿速览"
DEFAULT_EPISODE_SUBTITLE = "多条热门 AI 新闻合集"
MAX_EPISODE_ITEMS = 5
DEFAULT_EPISODE_ITEM_LIMIT = 4
PER_SEGMENT_DURATION_SEC = 32
OPENING_DURATION_SEC = 12
CLOSING_DURATION_SEC = 12
TRANSITION_DURATION_SEC = 4

# Keyword patterns for scoring (simple rule-based)
_SCORE_PATTERNS = [
    (re.compile(r"\bopenai\b"), 1.5),
    (re.compile(r"\banthropic\b"), 1.5),
    (re.compile(r"\bgoogle\b|\bdeepmind\b|\bgemini\b"), 1.0),
    (re.compile(r"\bmeta\b|\bllama\b"), 1.0),
    (re.compile(r"\bmicrosoft\b"), 0.8),
    (re.compile(r"\bmodel\b|\bllm\b|\bgpt\b|\bclaude\b"), 1.2),
    (re.compile(r"\bbenchmark\b|\bscore\b"), 0.5),
    (re.compile(r"\blaunch\b|\brelease\b|\bannounce\b|\bunveil\b"), 1.0),
    (re.compile(r"\bregulation\b|\bgovernment\b|\bEU\b|\bchina\b"), 0.7),
    (re.compile(r"\bsecurity\b|\boutage\b|\bbreach\b"), 0.8),
    (re.compile(r"\bresearch\b|\barxiv\b|\bpaper\b|\bstudy\b"), 0.6),
    (re.compile(r"\bfunding\b|\bvaluation\b"), 0.6),
    (re.compile(r"\bopensource\b|\brepo\b"), 0.5),
]

_TAG_PATTERNS = [
    (re.compile(r"\bopenai\b", re.I), "openai"),
    (re.compile(r"\banthropic\b", re.I), "anthropic"),
    (re.compile(r"\bgoogle\b|\bdeepmind\b|\bgemini\b", re.I), "google"),
    (re.compile(r"\bmeta\b|\bllama\b", re.I), "meta"),
    (re.compile(r"\bmicrosoft\b", re.I), "microsoft"),
    (re.compile(r"\bmodel\b|\bllm\b|\bgpt\b|\bclaude\b", re.I), "model"),
    (re.compile(r"\blaunch\b|\brelease\b|\bannounce\b|\bunveil\b", re.I), "launch"),
    (re.compile(r"\bregulation\b|\bgovernment\b|\bEU\b", re.I), "regulation"),
    (re.compile(r"\bsecurity\b|\boutage\b", re.I), "security"),
    (re.compile(r"\bresearch\b|\barxiv\b|\bpaper\b", re.I), "research"),
    (re.compile(r"\bfunding\b|\bvaluation\b", re.I), "funding"),
    (re.compile(r"\bopensource\b", re.I), "opensource"),
    (re.compile(r"\bmultimodal\b|\bvision\b", re.I), "multimodal"),
    (re.compile(r"\bagent\b|\btool\b", re.I), "agent"),
]


# ---------------------------------------------------------------------------
# ID generation
# ---------------------------------------------------------------------------

def _stable_id(text: str, salt: str = "") -> str:
    """Generate a stable hex ID from a string using SHA256 (first 12 chars)."""
    data = (salt + text).encode("utf-8")
    return hashlib.sha256(data).hexdigest()[:12]


def _item_id(prefix: str, item: dict) -> str:
    """Generate a stable news item ID from title/source/url."""
    title = item.get("title") or ""
    source = item.get("source") or ""
    url = item.get("url") or ""
    raw = f"{title}|{source}|{url}"
    return f"news_{_stable_id(raw, prefix)}"


# ---------------------------------------------------------------------------
# News item normalization
# ---------------------------------------------------------------------------

def normalize_inline_text(text: str, *, source: str = "Manual", url: str | None = None) -> dict:
    """Convert raw inline text into a normalized news_item dict.

    Rules (no LLM):
      - title: first non-empty line, max 80 chars
      - summary: next 180 chars of body, or derived from title if no body
      - tags: rule-based keyword detection
      - score: weighted keyword scoring
    """
    if not text or not text.strip():
        raise ValueError("inline text cannot be empty")

    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    if not lines:
        raise ValueError("inline text has no non-empty lines")

    title = lines[0]
    if len(title) > 80:
        title = title[:77] + "..."

    # Body is everything after the title line
    body_lines = lines[1:]
    body_text = " ".join(body_lines)

    if body_text:
        summary = body_text[:180]
        if len(body_text) > 180:
            summary = summary.rstrip() + "…"
    else:
        # Derive summary from title
        summary = f"关于「{title}」的新闻。" if title else ""

    item = {
        "id": _item_id("inline", {"title": title, "source": source}),
        "title": title,
        "summary": summary,
        "source": source,
        "url": url or "",
        "published_at": None,
        "final_score": 0.0,
        "points": 0,
        "comments": 0,
        "tags": _extract_tags(title + " " + body_text),
        "source_type": "inline_text",
    }
    item["final_score"] = score_news_item(item)
    return item


def normalize_manual_items(items: list[dict]) -> list[dict]:
    """Normalize a list of manually-provided news items to standard schema.

    Validates required fields and fills defaults. Does not overwrite user-provided values.
    """
    if not isinstance(items, list):
        raise TypeError("items must be a list")

    normalized = []
    for i, raw in enumerate(items):
        if not isinstance(raw, dict):
            raise TypeError(f"item[{i}] must be a dict")

        if not raw.get("title"):
            raise ValueError(f"item[{i}] is missing a 'title' field")

        item = {
            "id": raw.get("id") or _item_id("manual", raw),
            "title": raw["title"][:200],
            "summary": raw.get("summary", "")[:500],
            "source": raw.get("source") or "Manual",
            "url": raw.get("url") or "",
            "published_at": raw.get("published_at"),
            "final_score": float(raw["final_score"]) if raw.get("final_score") is not None else 0.0,
            "points": int(raw["points"]) if raw.get("points") is not None else 0,
            "comments": int(raw["comments"]) if raw.get("comments") is not None else 0,
            "tags": list(raw.get("tags") or [])[:10],
            "source_type": "manual_items",
        }
        normalized.append(item)

    return normalized


def normalize_url_item(
    *,
    url: str,
    title: str,
    summary: str = "",
    source_id: str | None = None,
    source: str | None = None,
    tags: list[str] | None = None,
    published_at: str | None = None,
) -> dict:
    """Normalize a URL-based news item into the standard news_item schema.

    This does NOT fetch or crawl the URL. URL is stored as provenance metadata.
    title and summary are provided by the user.

    Rules:
      - title: required, max 200 chars
      - summary: optional; if empty, derived from title
      - source_id: if provided and valid, use registry source name/tags/trust_level
      - source_id not provided: attempt domain inference via infer_source_from_url()
      - tags: merged from registry defaults + user tags + rule-based extraction
      - final_score: scored via score_news_item() with a small official/research bonus

    Returns a standard news_item dict.
    """
    # Import here to avoid circular imports; reliable_sources is pure logic
    from src.reliable_sources import (
        get_reliable_source, infer_source_from_url, validate_source_url,
    )

    if not title or not title.strip():
        raise ValueError("news title cannot be empty")

    # Validate URL
    url_valid, url_error = validate_source_url(url)
    if not url_valid:
        raise ValueError(f"Invalid URL: {url_error}")

    # Resolve source metadata
    registry_source = None
    final_source_name = source or "Manual"
    trust_level = "unknown"
    registry_tags: list[str] = []

    if source_id:
        reg = get_reliable_source(source_id)
        if reg:
            registry_source = reg
            final_source_name = reg["name"]
            trust_level = reg["trust_level"]
            registry_tags = list(reg.get("default_tags") or [])

    if not registry_source:
        # Try to infer from domain
        inferred = infer_source_from_url(url)
        if inferred:
            registry_source = inferred
            final_source_name = inferred["name"]
            trust_level = inferred["trust_level"]
            registry_tags = list(inferred.get("default_tags") or [])

    # Build tags: registry defaults + user tags + rule-based
    user_tags = [str(t).strip() for t in (tags or []) if t]
    extracted_tags = _extract_tags(title + " " + summary)
    merged_tags = registry_tags + user_tags + extracted_tags
    # Deduplicate while preserving order
    seen = set()
    deduped_tags = []
    for t in merged_tags:
        if t not in seen:
            seen.add(t)
            deduped_tags.append(t)
    final_tags = deduped_tags[:10]

    # Derive summary from title if not provided
    final_summary = summary.strip() if summary else title[:120]

    # Build base item
    item: dict[str, object] = {
        "id": _item_id("url", {"title": title, "source": final_source_name, "url": url}),
        "title": title[:200],
        "summary": final_summary[:500],
        "source": final_source_name,
        "url": url,
        "published_at": published_at,
        "final_score": 0.0,
        "points": 0,
        "comments": 0,
        "tags": final_tags,
        "source_type": "url_input",
        "source_id": source_id or "",
        "matched_source_id": registry_source["id"] if registry_source else "",
        "trust_level": trust_level,
    }

    # Compute score with small official/research bonus
    item["final_score"] = score_news_item(item)
    if trust_level == "official":
        item["final_score"] = min(10.0, round(item["final_score"] + 0.3, 1))
    elif trust_level == "research":
        item["final_score"] = min(10.0, round(item["final_score"] + 0.2, 1))

    return item


def load_sample_news_pack() -> list[dict]:
    """Return the built-in sample news pack (mock only — not real news).

    Returns 5 sample AI news items with realistic titles and scores.
    """
    samples = [
        {
            "title": "OpenAI 发布新的开发者工具能力",
            "summary": "OpenAI 宣布推出一系列新的开发者工具，包括增强的 API 管理和安全控制功能。",
            "source": "Sample",
            "url": "",
            "final_score": 8.5,
            "points": 420,
            "comments": 38,
            "tags": ["openai", "model", "launch"],
        },
        {
            "title": "Anthropic 更新模型安全研究报告",
            "summary": "Anthropic 发布了关于 Claude 模型安全性的最新研究报告，详细说明了安全措施和限制。",
            "source": "Sample",
            "url": "",
            "final_score": 8.0,
            "points": 310,
            "comments": 22,
            "tags": ["anthropic", "research", "model"],
        },
        {
            "title": "Google 推出 AI 搜索体验更新",
            "summary": "Google 在搜索结果中集成了新的 AI 生成的摘要卡片，提供更丰富的信息展示。",
            "source": "Sample",
            "url": "",
            "final_score": 7.5,
            "points": 280,
            "comments": 55,
            "tags": ["google", "launch"],
        },
        {
            "title": "Meta 开源新的多模态研究模型",
            "summary": "Meta 宣布开源一个支持图像和文本的多模态模型，旨在推动多模态 AI 研究。",
            "source": "Sample",
            "url": "",
            "final_score": 8.2,
            "points": 390,
            "comments": 41,
            "tags": ["meta", "opensource", "multimodal"],
        },
        {
            "title": "欧盟发布 AI 合规相关进展",
            "summary": "欧盟委员会公布了 AI 法案的最新实施进展，涵盖模型透明度要求和禁止使用场景。",
            "source": "Sample",
            "url": "",
            "final_score": 7.0,
            "points": 190,
            "comments": 14,
            "tags": ["regulation", "EU"],
        },
    ]

    # Normalize to ensure all required fields
    normalized = []
    for i, s in enumerate(samples):
        item = {
            "id": f"news_sample_{i + 1:02d}",
            "title": s["title"],
            "summary": s["summary"],
            "source": s["source"],
            "url": s.get("url") or "",
            "published_at": None,
            "final_score": float(s["final_score"]),
            "points": int(s["points"]),
            "comments": int(s["comments"]),
            "tags": s.get("tags", [])[:10],
            "source_type": "sample_pack",
        }
        normalized.append(item)

    return normalized


# ---------------------------------------------------------------------------
# Scoring and tagging
# ---------------------------------------------------------------------------

def score_news_item(item: dict) -> float:
    """Compute a final_score (0–10) for a news item using simple keyword rules.

    No LLM. Score is deterministic and based on keyword presence and text features.
    """
    text = " ".join([
        item.get("title") or "",
        item.get("summary") or "",
        item.get("source") or "",
        " ".join(item.get("tags") or []),
    ]).lower()

    score = 5.0  # base score

    for pattern, weight in _SCORE_PATTERNS:
        if pattern.search(text):
            score += weight

    # Length bonus: longer summaries suggest richer content
    summary = item.get("summary") or ""
    if len(summary) > 100:
        score += 0.3
    if len(summary) > 200:
        score += 0.3

    # Numeric data suggests specific/quantitative news
    if re.search(r"\d+%", text):
        score += 0.4
    if re.search(r"\$[\d,]+", text):
        score += 0.4

    # Penalize very short titles
    title = item.get("title") or ""
    if len(title) < 20:
        score -= 0.5

    return max(0.0, min(10.0, round(score, 1)))


def _extract_tags(text: str) -> list[str]:
    """Extract tags from text using simple keyword patterns."""
    text_lower = text.lower()
    tags = []
    for pattern, tag in _TAG_PATTERNS:
        if pattern.search(text_lower):
            if tag not in tags:
                tags.append(tag)
    return tags[:8]  # cap at 8 tags


# ---------------------------------------------------------------------------
# Episode item selection
# ---------------------------------------------------------------------------

def build_episode_items_from_news(
    news_items: list[dict], *, limit: int = DEFAULT_EPISODE_ITEM_LIMIT
) -> list[dict]:
    """Select and order the best news items for an episode.

    Rules:
      1. Filter out items with empty title
      2. Sort by final_score descending, then points descending
      3. Cap at min(limit, MAX_EPISODE_ITEMS) items
      4. Mark first item as 'lead', rest as 'supporting'
    """
    limit = max(1, min(limit, MAX_EPISODE_ITEMS))

    # Filter
    filtered = [item for item in news_items if item.get("title") and item["title"].strip()]

    # Sort
    filtered.sort(key=lambda x: (x.get("final_score") or 0, x.get("points") or 0), reverse=True)

    # Cap and assign roles
    selected = filtered[:limit]
    for i, item in enumerate(selected):
        item = dict(item)  # shallow copy to avoid mutating original
        item["role"] = "lead" if i == 0 else "supporting"
        item["order"] = i + 1
        selected[i] = item

    return selected


# ---------------------------------------------------------------------------
# Episode contract generation
# ---------------------------------------------------------------------------

def build_episode_contract_from_news_items(
    news_items: list[dict],
    *,
    template_id: str = DEFAULT_TEMPLATE_ID,
    title: str = DEFAULT_EPISODE_TITLE,
    subtitle: str = DEFAULT_EPISODE_SUBTITLE,
) -> dict:
    """Build an episode_template_v1 contract from a list of selected news items.

    This contract is compatible with:
      - render_episode_html.render_episode_stage_html() (breaking_news_v1)
      - episode_export.start_episode_export_background()

    Args:
        news_items: selected episode items from build_episode_items_from_news()
        template_id: must be "breaking_news_v1" for current MP4 export
        title: episode title
        subtitle: episode subtitle

    Returns:
        episode_template_v1 contract dict
    """
    if template_id != DEFAULT_TEMPLATE_ID:
        raise ValueError(f"Only {DEFAULT_TEMPLATE_ID!r} is supported for MP4 export")

    # Estimate total duration
    n = len(news_items)
    estimated_sec = (
        OPENING_DURATION_SEC
        + n * PER_SEGMENT_DURATION_SEC
        + max(0, n - 1) * TRANSITION_DURATION_SEC
        + CLOSING_DURATION_SEC
    )

    # Determine lead count
    lead_count = sum(1 for item in news_items if item.get("role") == "lead")

    # Build timeline markers
    markers = []
    cursor = 0.0

    # Opening
    markers.append({
        "type": "opening",
        "label": "开场",
        "timecode": _format_timecode(cursor),
        "role": None,
        "section_id": "section_opening",
    })
    cursor += OPENING_DURATION_SEC

    # Per-segment markers + transitions
    for i, item in enumerate(news_items):
        markers.append({
            "type": "news_segment",
            "label": (item.get("role") == "lead" and "主线 " or "补充 ") + str(i + 1),
            "timecode": _format_timecode(cursor),
            "role": item.get("role"),
            "section_id": f"section_seg_{i + 1:02d}",
        })
        cursor += PER_SEGMENT_DURATION_SEC

        if i < len(news_items) - 1:
            markers.append({
                "type": "transition",
                "label": "转场",
                "timecode": _format_timecode(cursor),
                "role": None,
                "section_id": f"section_trans_{i + 1:02d}",
            })
            cursor += TRANSITION_DURATION_SEC

    # Closing — advance cursor past the last segment before placing the marker
    cursor += CLOSING_DURATION_SEC
    markers.append({
        "type": "closing",
        "label": "结尾",
        "timecode": _format_timecode(cursor),
        "role": None,
        "section_id": "section_closing",
    })

    # Build news_cards (mirrors what render_episode_html expects)
    news_cards = []
    card_cursor = 0.0

    # Opening card
    card_cursor += OPENING_DURATION_SEC

    for i, item in enumerate(news_items):
        is_lead = item.get("role") == "lead"
        badges = _make_badges(item)
        emphasis = "breaking" if is_lead else "standard"

        start_offset = card_cursor
        card_cursor += PER_SEGMENT_DURATION_SEC
        end_offset = card_cursor
        time_range = f"{_format_timecode(start_offset)} – {_format_timecode(end_offset)}"

        news_cards.append({
            "section_id": f"section_seg_{i + 1:02d}",
            "order": i + 1,
            "role": item.get("role"),
            "headline": item.get("title") or "",
            "description": item.get("summary") or "",
            "layout": "full" if is_lead else "compact",
            "emphasis": emphasis,
            "badges": badges,
            "audio_clip_count": 2 if is_lead else 1,
            "duration_hint_sec": PER_SEGMENT_DURATION_SEC,
            "time_range": time_range,
            "is_lead": is_lead,
            "section_type": "news_segment",
        })

        # Transition after card (except last)
        if i < len(news_items) - 1:
            card_cursor += TRANSITION_DURATION_SEC

    # Build sections dict
    sections = {
        "opening": {
            "type": "opening",
            "section_id": "section_opening",
            "title": title,
            "duration_hint_sec": OPENING_DURATION_SEC,
        },
        "news_cards": news_cards,
        "transitions": [
            {
                "type": "transition",
                "section_id": f"section_trans_{i + 1:02d}",
                "duration_hint_sec": TRANSITION_DURATION_SEC,
            }
            for i in range(max(0, len(news_items) - 1))
        ],
        "closing": {
            "type": "closing",
            "section_id": "section_closing",
            "title": "本期小结",
            "duration_hint_sec": CLOSING_DURATION_SEC,
        },
    }

    contract = {
        "schema_version": "episode_template_v1",
        "template_id": template_id,
        "episode": {
            "title": title,
            "subtitle": subtitle,
            "theme_id": template_id,
            "theme_name": "快讯大屏风",
            "estimated_duration_sec": estimated_sec,
            "news_count": len(news_items),
            "lead_count": lead_count or 1,
        },
        "timeline": {
            "markers": markers,
        },
        "sections": sections,
        "constraints": {
            "no_external_assets": True,
            "no_script": True,
            "no_real_render": True,
            "no_audio": True,
            "no_mp4": False,  # can be exported via episode_export
        },
    }

    return contract


def _format_timecode(seconds: float) -> str:
    """Format seconds as MM:SS timecode."""
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"


def _make_badges(item: dict) -> list[str]:
    """Generate badge list from item tags and source."""
    badges = []
    for tag in (item.get("tags") or [])[:3]:
        badges.append(f"#{tag}")
    source = item.get("source", "")
    if source and source not in badges:
        badges.append(source[:10])
    return badges


# ---------------------------------------------------------------------------
# Full pipeline shortcut
# ---------------------------------------------------------------------------

def build_contract_from_inline_text(
    text: str,
    *,
    source: str = "Manual",
    url: str | None = None,
    template_id: str = DEFAULT_TEMPLATE_ID,
    title: str = DEFAULT_EPISODE_TITLE,
    subtitle: str = DEFAULT_EPISODE_SUBTITLE,
    limit: int = DEFAULT_EPISODE_ITEM_LIMIT,
) -> dict:
    """Convenience: normalize inline text → episode item → episode_template_v1 contract.

    Use this as a single-call shortcut for the full pipeline.
    """
    item = normalize_inline_text(text, source=source, url=url)
    episode_items = build_episode_items_from_news([item], limit=limit)
    return build_episode_contract_from_news_items(
        episode_items,
        template_id=template_id,
        title=title,
        subtitle=subtitle,
    )


def build_contract_from_sample_pack(
    *,
    template_id: str = DEFAULT_TEMPLATE_ID,
    title: str = DEFAULT_EPISODE_TITLE,
    subtitle: str = DEFAULT_EPISODE_SUBTITLE,
    limit: int = DEFAULT_EPISODE_ITEM_LIMIT,
) -> dict:
    """Convenience: load sample pack → select items → episode_template_v1 contract."""
    samples = load_sample_news_pack()
    episode_items = build_episode_items_from_news(samples, limit=limit)
    return build_episode_contract_from_news_items(
        episode_items,
        template_id=template_id,
        title=title,
        subtitle=subtitle,
    )


# ---------------------------------------------------------------------------
# Security: reject API keys / voice IDs
# ---------------------------------------------------------------------------

SECRET_PATTERNS = re.compile(
    r"(api[_-]?key|voice[_-]?id|secret|token|password)\s*[=:]\s*[\w-]", re.I
)


def contract_has_secrets(contract: dict) -> bool:
    """Return True if the contract contains any API keys or voice IDs."""
    text = str(contract)
    return bool(SECRET_PATTERNS.search(text))
