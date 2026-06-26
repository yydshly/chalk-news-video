"""Episode stage HTML generator: render episode_template_v1 contracts to self-contained HTML.

Supports breaking_news_v1 fixed 9:16 video stage.
Can be called from the export pipeline to produce HTML for Playwright capture.

CP40.0 — Python Episode Stage HTML Generator
"""

from __future__ import annotations

import html
import math
import re
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def escape_html(value: object) -> str:
    """Escape a value for safe embedding in HTML text content."""
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def format_timecode(seconds: float | int | None) -> str:
    """Format seconds as MM:SS timecode string."""
    if seconds is None:
        return "00:00"
    try:
        total = float(seconds)
    except (TypeError, ValueError):
        return "00:00"
    m = int(total // 60)
    s = int(total % 60)
    return f"{m:02d}:{s:02d}"


# ---------------------------------------------------------------------------
# Shot timeline
# ---------------------------------------------------------------------------

def build_breaking_news_shot_timeline(contract: dict) -> list[dict]:
    """Build shot timeline for breaking_news_v1 stage.

    Returns list of shot dicts with keys: shot_id, label, start_sec, duration_sec.
    """
    sections = contract.get("sections") or {}
    news_cards: list[dict] = sections.get("news_cards") or []
    episode = contract.get("episode") or {}
    total_sec = float(episode.get("estimated_duration_sec") or 30)

    return [
        {
            "shot_id": "opening",
            "label": "开场",
            "start_sec": 0.0,
            "duration_sec": 3.0,
            "layer_targets": ["stage-title-area", "stage-topbar"],
        },
        {
            "shot_id": "anchor_intro",
            "label": "主持人导入",
            "start_sec": 1.0,
            "duration_sec": 3.0,
            "layer_targets": ["stage-anchor-layer"],
        },
        {
            "shot_id": "lead_news",
            "label": "主新闻",
            "start_sec": 3.0,
            "duration_sec": 6.0,
            "layer_targets": ["stage-main-card", "stage-subtitle-bar"],
        },
        {
            "shot_id": "supporting_news",
            "label": "补充快讯",
            "start_sec": 7.0,
            "duration_sec": 6.0,
            "layer_targets": ["stage-supporting"],
        },
        {
            "shot_id": "closing",
            "label": "结尾",
            "start_sec": 11.0,
            "duration_sec": 3.0,
            "layer_targets": ["stage-closing-chip", "stage-timeline"],
        },
    ]


def get_shot_by_id(shot_timeline: list[dict], shot_id: str) -> dict | None:
    """Return the shot dict with the given shot_id, or None."""
    for shot in shot_timeline:
        if shot.get("shot_id") == shot_id:
            return shot
    return None


def get_shot_start(
    shot_timeline: list[dict], shot_id: str, fallback: float = 0.0
) -> float:
    """Return start_sec for a shot, or fallback."""
    shot = get_shot_by_id(shot_timeline, shot_id)
    return float(shot["start_sec"]) if shot and shot.get("start_sec") is not None else fallback


def get_shot_duration(
    shot_timeline: list[dict], shot_id: str, fallback: float = 3.0
) -> float:
    """Return duration_sec for a shot, or fallback."""
    shot = get_shot_by_id(shot_timeline, shot_id)
    return float(shot["duration_sec"]) if shot and shot.get("duration_sec") is not None else fallback


def get_shot_timeline_total_duration(shot_timeline: list[dict]) -> float:
    """Return the end time of the last shot in the timeline."""
    if not shot_timeline:
        return 14.0
    last = shot_timeline[-1]
    start = float(last.get("start_sec", 0))
    dur = float(last.get("duration_sec", 3))
    return start + dur


# ---------------------------------------------------------------------------
# Stage timing
# ---------------------------------------------------------------------------

def build_breaking_news_stage_timing(contract: dict) -> dict:
    """Build timing object for breaking_news_v1 stage.

    Returns dict with:
      - shot_timeline: list of shot dicts
      - totalDurationSec: total duration in seconds
      - delays: dict mapping delay key to delay value in seconds
    """
    shot_timeline = build_breaking_news_shot_timeline(contract)
    total_sec = get_shot_timeline_total_duration(shot_timeline)

    def m(val: float) -> float:
        return max(0.0, val)

    return {
        "shotTimeline": shot_timeline,
        "totalDurationSec": total_sec,
        "delays": {
            "topbar": m(get_shot_start(shot_timeline, "opening", 0.0) + 0.1),
            "title": m(get_shot_start(shot_timeline, "opening", 0.0) + 0.2),
            "openingLabel": m(get_shot_start(shot_timeline, "opening", 0.0) + 0.15),
            "recap": m(get_shot_start(shot_timeline, "opening", 0.0) + 0.3),
            "shotLabel": m(get_shot_start(shot_timeline, "opening", 0.0) + 0.1),
            "anchor": m(get_shot_start(shot_timeline, "anchor_intro", 1.0)),
            "mainCard": m(get_shot_start(shot_timeline, "lead_news", 3.0) - 0.5),
            "subtitle": m(get_shot_start(shot_timeline, "lead_news", 3.0) + 0.2),
            "supporting": m(get_shot_start(shot_timeline, "supporting_news", 7.0) - 2.0),
            "support1": m(get_shot_start(shot_timeline, "supporting_news", 7.0) - 1.8),
            "support2": m(get_shot_start(shot_timeline, "supporting_news", 7.0) - 1.45),
            "support3": m(get_shot_start(shot_timeline, "supporting_news", 7.0) - 1.1),
            "closing": m(get_shot_start(shot_timeline, "closing", 11.0) - 1.5),
        },
    }


# ---------------------------------------------------------------------------
# Anchor inference
# ---------------------------------------------------------------------------

def infer_news_context_from_contract(contract: dict) -> dict:
    """Infer news context type and severity from contract text fields.

    Keyword-based, no LLM.
    """
    episode = contract.get("episode") or {}
    sections = contract.get("sections") or {}
    cards: list[dict] = sections.get("news_cards") or []

    parts = [
        episode.get("title") or "",
        episode.get("subtitle") or "",
        (sections.get("opening") or {}).get("title") or "",
        (sections.get("closing") or {}).get("title") or "",
    ]
    for card in cards:
        parts.extend([
            card.get("headline") or "",
            card.get("emphasis") or "",
            " ".join(card.get("badges") or []),
            card.get("layout") or "",
        ])

    text = " ".join(parts).lower()

    context_type = "general"
    severity = "normal"

    if re.search(
        r"breaking|outage|security|risk|lawsuit|ban|regulation|alert|emergency|crisis|scandal",
        text,
        re.IGNORECASE,
    ):
        context_type = "alert"
        severity = "high"
    elif re.search(
        r"launch|release|announce|unveil|model|product|feature|debut|coming soon",
        text,
        re.IGNORECASE,
    ):
        context_type = "launch"
        severity = "normal"
    elif re.search(
        r"benchmark|score|ranking|leaderboard|funding|valuation|revenue|profit|market|percent|%",
        text,
        re.IGNORECASE,
    ):
        context_type = "data"
        severity = "normal"
    elif re.search(
        r"research|paper|arxiv|study|reasoning|method|dataset|experiment|result|finding",
        text,
        re.IGNORECASE,
    ):
        context_type = "research"
        severity = "low"

    return {"context_type": context_type, "severity": severity}


def infer_episode_anchor_cue(contract: dict) -> dict:
    """Map context to anchor expression, action, and tone."""
    ctx = infer_news_context_from_contract(contract)
    context_type = ctx["context_type"]
    severity = ctx["severity"]

    expression = "neutral"
    action = "talk"
    tone = "normal"

    if context_type == "alert":
        expression = "serious" if severity == "high" else "focused"
        action = "alert_point"
        tone = "breaking"
    elif context_type == "launch":
        expression = "excited"
        action = "introduce"
        tone = "energetic"
    elif context_type == "data":
        expression = "focused"
        action = "point_right"
        tone = "analytical"
    elif context_type == "research":
        expression = "thinking"
        action = "explain"
        tone = "calm"

    return {
        "role": "anchor",
        "position": "left",
        "expression": expression,
        "action": action,
        "tone": tone,
    }


# ---------------------------------------------------------------------------
# Cartoon anchor SVG
# ---------------------------------------------------------------------------

def _render_cartoon_anchor_svg_expression(expr: str) -> dict:
    """Return SVG config dict for an anchor expression."""
    configs = {
        "neutral": {
            "mouth": '<path class="anchor-mouth" d="M50 82 Q60 90 70 82" stroke="#2d1b0e" stroke-width="2.5" fill="none" stroke-linecap="round"/>',
            "brows": '<path class="anchor-brow anchor-brow-left" d="M40 59 Q48 56 55 59" stroke="#3d2517" stroke-width="2.5" fill="none" stroke-linecap="round"/><path class="anchor-brow anchor-brow-right" d="M65 59 Q72 56 80 59" stroke="#3d2517" stroke-width="2.5" fill="none" stroke-linecap="round"/>',
            "pupilDx": 0,
            "cheek": "",
        },
        "serious": {
            "mouth": '<path class="anchor-mouth" d="M50 84 Q60 82 70 84" stroke="#2d1b0e" stroke-width="3" fill="none" stroke-linecap="round"/>',
            "brows": '<path class="anchor-brow anchor-brow-left" d="M40 57 Q48 53 55 57" stroke="#3d2517" stroke-width="3" fill="none" stroke-linecap="round"/><path class="anchor-brow anchor-brow-right" d="M65 57 Q72 53 80 57" stroke="#3d2517" stroke-width="3" fill="none" stroke-linecap="round"/>',
            "pupilDx": 0,
            "cheek": "",
        },
        "excited": {
            "mouth": '<path class="anchor-mouth" d="M47 80 Q60 94 73 80 Q60 86 47 80 Z" fill="#2d1b0e" stroke="#2d1b0e" stroke-width="1"/>',
            "brows": '<path class="anchor-brow anchor-brow-left" d="M40 58 Q48 54 55 58" stroke="#3d2517" stroke-width="2.5" fill="none" stroke-linecap="round"/><path class="anchor-brow anchor-brow-right" d="M65 58 Q72 54 80 58" stroke="#3d2517" stroke-width="2.5" fill="none" stroke-linecap="round"/>',
            "pupilDx": 0,
            "cheek": '<ellipse cx="36" cy="76" rx="8" ry="5" fill="#fca5a5" opacity=".45"/><ellipse cx="84" cy="76" rx="8" ry="5" fill="#fca5a5" opacity=".45"/>',
        },
        "focused": {
            "mouth": '<path class="anchor-mouth" d="M50 82 Q60 88 70 82" stroke="#2d1b0e" stroke-width="2.5" fill="none" stroke-linecap="round"/>',
            "brows": '<path class="anchor-brow anchor-brow-left" d="M40 58 Q48 55 55 58" stroke="#3d2517" stroke-width="2.5" fill="none" stroke-linecap="round"/><path class="anchor-brow anchor-brow-right" d="M65 58 Q72 55 80 58" stroke="#3d2517" stroke-width="2.5" fill="none" stroke-linecap="round"/>',
            "pupilDx": 1.5,
            "cheek": "",
        },
        "thinking": {
            "mouth": '<path class="anchor-mouth" d="M53 84 Q60 81 67 84" stroke="#2d1b0e" stroke-width="2" fill="none" stroke-linecap="round"/>',
            "brows": '<path class="anchor-brow anchor-brow-left" d="M40 60 Q48 58 55 60" stroke="#3d2517" stroke-width="2" fill="none" stroke-linecap="round"/><path class="anchor-brow anchor-brow-right" d="M65 56 Q72 54 80 56" stroke="#3d2517" stroke-width="2" fill="none" stroke-linecap="round"/>',
            "pupilDx": -1,
            "cheek": "",
        },
    }
    return configs.get(expr, configs["neutral"])


def render_cartoon_anchor_svg(anchor_cue: dict) -> str:
    """Render the cartoon anchor character as an inline SVG string."""
    expr = anchor_cue.get("expression", "neutral")
    cfg = _render_cartoon_anchor_svg_expression(expr)

    hair_color = "#2d1b0e"
    skin_color = "#f5c9a0"
    suit_color = "#1a1a2e"
    tie_color = "#dc2626"
    pd = cfg["pupilDx"]

    parts = [
        '<svg class="cartoon-anchor-svg" viewBox="0 0 120 180" aria-hidden="true" style="width:100%;height:100%;overflow:visible;">',
        # Ground shadow
        '<ellipse cx="60" cy="176" rx="28" ry="4" fill="rgba(0,0,0,.28)"/>',
        # Torso
        f'<rect x="28" y="96" width="64" height="78" rx="10" fill="{suit_color}"/>',
        # Shirt front
        '<path d="M52 96 L60 124 L68 96" fill="#e8e8f0"/>',
        # Lapels
        '<path d="M48 96 L60 126 L72 96" fill="#252540"/>',
        # Red tie
        '<path d="M56 96 L64 96 L62 144 L60 150 L58 144 Z" fill="' + tie_color + '"/>',
        # Left arm
        '<path class="anchor-arm anchor-arm-left" d="M28 100 Q10 122 14 154" stroke="' + suit_color + '" stroke-width="15" fill="none" stroke-linecap="round"/>',
        f'<circle cx="14" cy="156" r="8" fill="{skin_color}"/>',
        # Right arm
        '<path class="anchor-arm anchor-arm-right" d="M92 100 Q110 122 106 154" stroke="' + suit_color + '" stroke-width="15" fill="none" stroke-linecap="round"/>',
        f'<circle cx="106" cy="156" r="8" fill="{skin_color}"/>',
        # Neck
        f'<rect x="50" y="82" width="20" height="16" fill="{skin_color}"/>',
        # Head
        f'<ellipse cx="60" cy="60" rx="30" ry="32" fill="{skin_color}"/>',
        # Hair
        f'<path d="M31 52 Q34 22 60 18 Q86 22 89 52 Q84 38 60 34 Q36 38 31 52Z" fill="{hair_color}"/>',
        # Ears
        f'<ellipse cx="31" cy="60" rx="6" ry="8" fill="{skin_color}"/>',
        f'<ellipse cx="89" cy="60" rx="6" ry="8" fill="{skin_color}"/>',
        # Left eye white
        '<circle cx="47" cy="60" r="8" fill="#fff"/>',
        # Right eye white
        '<circle cx="73" cy="60" r="8" fill="#fff"/>',
        # Left iris
        '<circle cx="48" cy="61" r="5.5" fill="#3a5f8a"/>',
        # Right iris
        '<circle cx="74" cy="61" r="5.5" fill="#3a5f8a"/>',
        # Left pupil
        f'<circle class="anchor-pupil" cx="{49 + pd}" cy="61" r="3" fill="#1a1a2e"/>',
        # Right pupil
        f'<circle class="anchor-pupil" cx="{75 + pd}" cy="61" r="3" fill="#1a1a2e"/>',
        # Shine left
        '<circle cx="50" cy="59" r="1.5" fill="#fff"/>',
        '<circle cx="46" cy="63" r="0.8" fill="#fff" opacity=".6"/>',
        # Shine right
        '<circle cx="76" cy="59" r="1.5" fill="#fff"/>',
        '<circle cx="72" cy="63" r="0.8" fill="#fff" opacity=".6"/>',
        # Brows
        cfg["brows"],
        # Nose
        '<ellipse cx="60" cy="68" rx="2.5" ry="3.5" fill="#d4a882" opacity=".6"/>',
        # Mouth
        cfg["mouth"],
        # Cheek blush
        cfg["cheek"],
    ]
    if expr == "thinking":
        parts.append(
            '<circle cx="86" cy="44" r="3" fill="#f5c9a0" stroke="#d4a882" stroke-width="1"/>'
            '<path d="M86 41 Q88 38 90 41" stroke="#3d2517" stroke-width="1.2" fill="none" stroke-linecap="round"/>'
        )
    parts.append("</svg>")
    svg = "".join(parts)
    return svg


def get_anchor_action_class(action: str) -> str:
    """Return CSS class name for an anchor action."""
    return {
        "talk": "anchor-action-talk",
        "point_right": "anchor-action-point-right",
        "alert_point": "anchor-action-alert-point",
        "introduce": "anchor-action-introduce",
        "explain": "anchor-action-explain",
    }.get(action, "anchor-action-talk")


def get_anchor_expression_class(expression: str) -> str:
    """Return CSS class name for an anchor expression."""
    return {
        "neutral": "anchor-expression-neutral",
        "serious": "anchor-expression-serious",
        "excited": "anchor-expression-excited",
        "focused": "anchor-expression-focused",
        "thinking": "anchor-expression-thinking",
    }.get(expression, "anchor-expression-neutral")


def render_cartoon_anchor_layer(anchor_cue: dict, delay_sec: float = 1.0) -> str:
    """Render the full cartoon anchor layer HTML (entrance wrapper + action layer + SVG)."""
    action_class = get_anchor_action_class(anchor_cue.get("action", "talk"))
    expression_class = get_anchor_expression_class(anchor_cue.get("expression", "neutral"))
    svg = render_cartoon_anchor_svg(anchor_cue)
    delay = float(delay_sec) if delay_sec is not None else 1.0
    appear_str = str(delay)

    return (
        f'<div class="stage-anchor-enter stage-layer" '
        f'data-appear-at="{appear_str}" style="animation-delay:{delay}s">'
        f'<div class="stage-anchor-layer {action_class} {expression_class}">'
        f'{svg}</div></div>'
    )


# ---------------------------------------------------------------------------
# Timeline rail markers
# ---------------------------------------------------------------------------

def render_shared_timeline_markers_html(timeline: dict | None) -> str:
    """Render compact timeline marker rail HTML from a timeline dict.

    timeline format: {"markers": [{"type": "...", "label": "...", "timecode": "..."}]}
    """
    if not timeline:
        return ""
    markers = timeline.get("markers") or []
    if not markers:
        return ""

    parts = []
    for marker in markers:
        m_type = marker.get("type", "")
        label = escape_html(marker.get("label") or "")
        timecode = marker.get("timecode") or "00:00"

        if m_type == "opening":
            dot_class = "tl-dot tl-dot-opening"
        elif m_type == "news_segment":
            role = marker.get("role")
            dot_class = "tl-dot " + ("tl-dot-lead" if role == "lead" else "tl-dot-supporting")
        elif m_type == "transition":
            dot_class = "tl-dot tl-dot-trans"
        elif m_type == "closing":
            dot_class = "tl-dot tl-dot-closing"
        else:
            dot_class = "tl-dot"

        parts.append(
            '<div class="tl-marker">'
            f'<div class="{dot_class}"></div>'
            '<div class="tl-label">'
            f'<span class="tl-time">{escape_html(timecode)}</span>'
            f'<span class="tl-name">{label}</span>'
            '</div>'
            '</div>'
        )
    return "".join(parts)


# ---------------------------------------------------------------------------
# Main breaking_news_v1 stage renderer
# ---------------------------------------------------------------------------

def _build_lead_card_html(lead_card: dict | None, appear_at: float = 2.5) -> str:
    """Build the main-lead-card HTML block with seek-layer markers."""
    if not lead_card:
        return ""
    headline = escape_html(lead_card.get("headline") or "")
    time_range = escape_html(lead_card.get("time_range") or "")
    duration = escape_html(str(lead_card.get("duration_hint_sec") or ""))
    layout = escape_html(lead_card.get("layout") or "")
    appear_str = str(appear_at)

    return (
        '<div class="mock-news-card mock-news-card-lead" data-section-type="news_segment" style="display:none"></div>'
        '<div class="stage-main-card mock-news-card mock-news-card-lead stage-layer" '
        f'data-appear-at="{appear_str}" data-section-type="news_segment">'
        '<div class="stage-lead-badge">★ 主线</div>'
        f'<div class="stage-lead-headline">{headline}</div>'
        '<div class="stage-lead-meta">'
        f'<span>{time_range}</span>'
        f'<span>{duration}s</span>'
        f'<span>{layout}</span>'
        '</div>'
        '</div>'
    )


def _build_supporting_cards_html(
    support_cards: list[dict],
    delays: dict | None = None,
) -> str:
    """Build the supporting cards stacked on the right side with seek-layer markers."""
    if not support_cards:
        return ""
    d = delays or {}
    container_appear = str(d.get("supporting", 5.0))
    parts = []
    for i, card in enumerate(support_cards[:3]):
        appear_key = f"support{i + 1}"
        appear_str = str(d.get(appear_key, d.get("supporting", 5.0) + i * 0.35))
        headline = escape_html(card.get("headline") or "")
        time_range = escape_html(card.get("time_range") or "")
        parts.append(
            '<div class="stage-support-card mock-news-card stage-layer" '
            f'data-appear-at="{appear_str}" data-section-type="news_segment">'
            f'<div class="stage-support-headline">{headline}</div>'
            f'<div class="stage-support-meta">{time_range}</div>'
            '</div>'
        )
    return (
        '<div class="stage-supporting stage-layer" data-appear-at="'
        + container_appear + '">'
        + "".join(parts)
        + '</div>'
    )


def _build_closing_html(closing: dict | None, appear_at: float = 9.5) -> str:
    """Build the closing chip HTML with seek-layer markers."""
    title = escape_html((closing or {}).get("title") or "")
    appear_str = str(appear_at)
    return (
        '<div class="stage-closing-chip stage-layer" '
        f'data-appear-at="{appear_str}">'
        '<div class="stage-closing-dot"></div>'
        f'<span>📍 结尾 — {title}</span>'
        '</div>'
    )


def render_breaking_news_stage_episode_html(contract: dict) -> str:
    """Render a self-contained breaking_news_v1 fixed 9:16 video stage HTML document.

    This is the Python port of web/app.js renderBreakingNewsStageEpisodeHtml().
    The output HTML is self-contained with inline CSS, inline SVG, and a minimal
    inline timing shim for compatibility with export_video.py.

    Args:
        contract: episode_template_v1 contract dict.

    Returns:
        Complete HTML string.
    """
    episode = contract.get("episode") or {}
    timeline = contract.get("timeline") or {}
    sections = contract.get("sections") or {}

    title = escape_html(episode.get("title") or "Episode Preview")
    subtitle = escape_html(episode.get("subtitle") or "")
    estimated_sec = float(episode.get("estimated_duration_sec") or 30)
    total_time_str = format_timecode(estimated_sec)

    # Build lead / supporting card lists
    news_cards: list[dict] = sections.get("news_cards") or []
    lead_card: dict | None = None
    support_cards: list[dict] = []
    for card in news_cards:
        if card.get("is_lead") and lead_card is None:
            lead_card = card
        else:
            support_cards.append(card)
    if lead_card is None and news_cards:
        lead_card = news_cards[0]
        support_cards = news_cards[1:]

    # Timing
    timing = build_breaking_news_stage_timing(contract)
    delays = timing["delays"]
    total_dur = timing["totalDurationSec"]

    # Pre-compute delay values (also needed by helpers)
    d = {
        k: float(delays.get(k, v))
        for k, v in {
            "recap": 0.3,
            "openingLabel": 0.15,
            "closing": 9.5,
            "shotLabel": 0.1,
            "topbar": 0.1,
            "title": 0.2,
            "mainCard": 2.5,
            "subtitle": 3.2,
            "supporting": 5.0,
            "support1": 5.2,
            "support2": 5.55,
            "support3": 5.9,
        }.items()
    }

    # Build sub-components
    lead_html = _build_lead_card_html(lead_card, d["mainCard"])
    support_html = _build_supporting_cards_html(support_cards, d)

    opening = sections.get("opening") or {}
    subtitle_text = escape_html(
        opening.get("title") or (lead_card.get("headline") if lead_card else "")
    )
    subtitle_bar_html = (
        '<div class="stage-subtitle-bar stage-layer" '
        f'data-appear-at="{d["subtitle"]}">'
        f'<div class="stage-subtitle-text">{subtitle_text}</div>'
        '</div>'
    )

    closing = sections.get("closing") or {}
    closing_html = _build_closing_html(closing, d["closing"])
    timeline_html = (
        '<div class="stage-timeline stage-layer" data-appear-at="0">'
        '<div class="tl-rail"><div class="tl-track">'
        + render_shared_timeline_markers_html(timeline)
        + '</div></div></div>'
    )

    recap_html = (
        '<div class="stage-recap stage-layer" data-appear-at="' + str(d["recap"]) + '">RECAP</div>'
    )
    opening_label_html = (
        '<div class="stage-opening-label stage-layer" data-appear-at="'
        + str(d["openingLabel"]) + '">📍 开场</div>'
    )

    # Anchor — pass appear_at so the outer div can be marked as stage-layer
    anchor_appear = delays.get("anchor", 1.0)
    anchor_cue = infer_episode_anchor_cue(contract)
    anchor_layer_html = render_cartoon_anchor_layer(anchor_cue, anchor_appear)

    # Shot timeline string for stage-shot-meta
    shot_timeline = timing["shotTimeline"]
    meta_parts = ";".join(
        f'{s["shot_id"]}|{s["start_sec"]}|{s["duration_sec"]}'
        for s in shot_timeline
    )

    # ---- CSS ----
    css_parts = [
        # Shell — fill the export frame (16:9 primary)
        '.video-stage-shell{width:100vw;height:100vh;background:#0a0000;overflow:hidden;}',
        # Stage — fill + flex column
        '.video-stage{position:relative;width:100%;height:100%;overflow:hidden;background:#0a0000;'
        'display:flex;flex-direction:column;'
        "font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;}",
        # Bg
        '.stage-bg{position:absolute;inset:0;background:linear-gradient(160deg,#1a0000 0%,#0a0000 40%,#120000 100%);'
        'animation:stageBgPulse 6s ease-in-out infinite;}',
        '@keyframes stageBgPulse{0%,100%{opacity:1;}50%{opacity:.85;}}',
        # Topbar
        '.stage-topbar{position:relative;z-index:20;display:flex;align-items:center;'
        'justify-content:space-between;padding:14px 24px 10px;background:linear-gradient(180deg,rgba(0,0,0,.7) 0%,transparent 100%);}',
        '.stage-breaking-badge{background:#dc2626;color:#fff;font-size:13px;font-weight:900;'
        'letter-spacing:2px;padding:5px 14px;border-radius:5px;animation:breakingBlink 2s ease-in-out infinite;}',
        '@keyframes breakingBlink{0%,100%{opacity:1;}50%{opacity:.7;}}',
        '.stage-meta{color:#f87171;font-size:12px;font-family:monospace;}',
        # Title area
        '.stage-title-area{position:relative;z-index:15;padding:0 24px 8px;}',
        '.stage-episode-title{color:#fff;font-size:24px;font-weight:800;line-height:1.25;'
        'text-shadow:0 2px 8px rgba(0,0,0,.8);margin-bottom:4px;}',
        '.stage-episode-subtitle{color:#fca5a5;font-size:13px;opacity:.9;line-height:1.3;}',
        # Main row — horizontal: anchor (left) + content (right)
        '.stage-main-row{position:relative;z-index:12;flex:1 1 auto;min-height:0;'
        'display:flex;gap:18px;padding:6px 24px 0;}',
        '.stage-anchor-col{flex:0 0 22%;max-width:200px;display:flex;align-items:flex-end;justify-content:center;}',
        '.stage-content-col{flex:1 1 auto;min-width:0;display:flex;flex-direction:column;gap:12px;}',
        # Main card
        '.stage-main-card{position:relative;z-index:12;'
        'background:rgba(20,0,0,.88);border:1px solid #dc2626;border-radius:14px;padding:18px 20px;'
        'animation:cardEnter 0.5s ease-out both;}',
        '@keyframes cardEnter{from{opacity:0;transform:translateY(12px);}to{opacity:1;transform:translateY(0);}}',
        '.stage-lead-badge{display:inline-block;background:#dc2626;color:#fff;font-size:12px;font-weight:900;'
        'letter-spacing:1px;padding:3px 10px;border-radius:4px;margin-bottom:10px;}',
        '.stage-lead-headline{color:#fff;font-size:26px;font-weight:800;line-height:1.3;'
        'margin-bottom:10px;text-shadow:0 1px 4px rgba(0,0,0,.6);}',
        '.stage-lead-meta{display:flex;gap:12px;font-size:12px;color:#fca5a5;font-family:monospace;}',
        # Supporting — horizontal row of cards
        '.stage-supporting{position:relative;z-index:12;display:flex;flex-direction:row;gap:10px;}',
        '.stage-support-card{flex:1 1 0;min-width:0;background:rgba(15,0,0,.82);border:1px solid #7f1d1d;'
        'border-radius:10px;padding:10px 12px;}',
        '.stage-support-headline{color:#fecaca;font-size:14px;font-weight:600;line-height:1.3;'
        'display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;}',
        '.stage-support-meta{color:#f87171;font-size:11px;font-family:monospace;margin-top:5px;}',
        # Subtitle bar
        '.stage-subtitle-bar{position:relative;z-index:14;margin:10px 24px 0;'
        'background:rgba(0,0,0,.75);border-radius:8px;padding:9px 14px;}',
        '.stage-subtitle-text{color:#f9f9f9;font-size:15px;line-height:1.4;'
        'display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;}',
        # Timeline
        '.stage-timeline{position:relative;z-index:20;margin-top:auto;'
        'padding:8px 24px;background:linear-gradient(0deg,rgba(0,0,0,.8) 0%,transparent 100%);}',
        '.tl-rail{padding:0;}',
        '.tl-track{min-width:0;position:relative;}',
        '.tl-track::before{background:#4a0000;}',
        '.tl-dot{width:8px;height:8px;border-radius:50%;border:2px solid #dc2626;background:#0a0000;}',
        '.tl-dot-opening{background:#dc2626;border-color:#dc2626;}',
        '.tl-dot-lead{background:#dc2626;border-color:#dc2626;box-shadow:0 0 6px #dc262680;}',
        '.tl-dot-supporting{background:#7f1d1d;border-color:#dc2626;}',
        '.tl-dot-closing{background:#f87171;border-color:#f87171;animation:pulseLine 2s infinite;}',
        '@keyframes pulseLine{0%,100%{opacity:1;}50%{opacity:.5;}}',
        '.tl-marker{flex:.5;min-width:30px;}',
        '.tl-label{text-align:center;margin-top:2px;}',
        '.tl-time{color:#fca5a5;font-size:8px;font-family:monospace;display:block;}',
        '.tl-name{color:#f87171;font-size:8px;display:block;white-space:nowrap;overflow:hidden;'
        'text-overflow:ellipsis;max-width:40px;}',
        # Recap chip
        '.stage-recap{position:absolute;top:44px;right:14px;z-index:18;'
        'background:rgba(220,38,38,.85);border-radius:6px;padding:3px 8px;'
        'font-size:9px;color:#fff;font-weight:700;opacity:0;'
        'animation:shotFadeIn 0.4s ' + str(d["recap"]) + 's ease-out both;}',
        # Opening label
        '.stage-opening-label{position:absolute;top:44px;left:14px;z-index:18;'
        'color:#fca5a5;font-size:9px;font-weight:700;letter-spacing:1px;opacity:0;'
        'animation:shotFadeIn 0.4s ' + str(d["openingLabel"]) + 's ease-out both;}',
        # Closing chip
        '.stage-closing-chip{position:absolute;bottom:96px;left:14px;z-index:15;'
        'display:flex;align-items:center;gap:6px;font-size:9px;color:#fca5a5;opacity:0;'
        'animation:shotFadeIn 0.5s ' + str(d["closing"]) + 's ease-out both;}',
        '.stage-closing-dot{width:6px;height:6px;border-radius:50%;background:#dc2626;}',
        # Anchor layers
        '.stage-anchor-enter{position:relative;width:100%;height:100%;max-height:230px;'
        'z-index:16;pointer-events:none;opacity:0;'
        'animation:anchorEnter 0.7s ease-out forwards;}',
        '.stage-anchor-layer{width:100%;height:100%;}',
        '.cartoon-anchor-svg{width:100%;height:100%;filter:drop-shadow(0 6px 18px rgba(0,0,0,.6));}',
        # Anchor animations
        '@keyframes anchorFloat{0%,100%{transform:translateY(0);}50%{transform:translateY(-5px);}}',
        '@keyframes anchorAlert{0%,100%{transform:rotate(0deg);}25%{transform:rotate(-6deg);}75%{transform:rotate(4deg);}}',
        '@keyframes anchorTilt{0%,100%{transform:rotate(0deg);}50%{transform:rotate(-4deg);}}',
        '@keyframes armWave{0%,100%{transform:rotate(0deg);}50%{transform:rotate(-10deg);}}',
        '@keyframes armPointR{0%,100%{transform:rotate(0deg);}50%{transform:rotate(-10deg);}}',
        '@keyframes armAlert{0%,100%{transform:rotate(0deg);}40%{transform:rotate(-12deg);}}',
        '@keyframes armIntro{0%,100%{transform:rotate(0deg) scaleX(1);}50%{transform:rotate(-6deg) scaleX(1.05);}}',
        '@keyframes mouthOpen{0%,100%{transform:scaleY(1);}50%{transform:scaleY(1.5);}}',
        '@keyframes pupilLook{0%,100%{transform:translate(0,0);}33%{transform:translate(1.5px,0);}66%{transform:translate(-1px,0);}}',
        '.anchor-action-talk{animation:anchorFloat 2.2s ease-in-out infinite;transform-origin:60px 176px;}',
        '.anchor-action-talk .anchor-arm-right{animation:armWave 1.8s ease-in-out infinite;transform-origin:92px 100px;}',
        '.anchor-action-talk .anchor-mouth{animation:mouthOpen 1s ease-in-out infinite;transform-origin:60px 82px;}',
        '.anchor-action-point-right{animation:anchorFloat 2.2s ease-in-out infinite;transform-origin:60px 176px;}',
        '.anchor-action-point-right .anchor-arm-right{animation:armPointR 1.4s ease-in-out infinite;transform-origin:92px 100px;}',
        '.anchor-action-point-right .anchor-pupil{animation:pupilLook 3s ease-in-out infinite;}',
        '.anchor-action-alert-point{animation:anchorTilt 1s ease-in-out infinite;transform-origin:60px 176px;}',
        '.anchor-action-alert-point .anchor-arm-right{animation:armAlert .7s ease-in-out infinite;transform-origin:92px 100px;}',
        '.anchor-action-introduce{animation:anchorFloat 2.2s ease-in-out infinite;transform-origin:60px 176px;}',
        '.anchor-action-introduce .anchor-arm-right{animation:armIntro 2s ease-in-out infinite;transform-origin:92px 100px;}',
        '.anchor-action-explain{animation:anchorFloat 3s ease-in-out infinite;transform-origin:60px 176px;}',
        '.anchor-action-explain .anchor-arm-right{animation:armWave 2.5s ease-in-out infinite;transform-origin:92px 100px;}',
        '.anchor-pupil{animation:pupilLook 4s ease-in-out infinite;}',
        '.anchor-expression-excited .cartoon-anchor-svg{filter:drop-shadow(0 8px 20px rgba(0,0,0,.5)) brightness(1.08);}',
        '.anchor-expression-serious .anchor-brow{animation:seriousBrow 2s ease-in-out infinite;}',
        '@keyframes seriousBrow{0%,100%{transform:translateY(0);}50%{transform:translateY(-1px);}}',
        '.anchor-expression-thinking .cartoon-anchor-svg{animation:thinkTilt 3s ease-in-out infinite;transform-origin:60px 60px;}',
        '@keyframes thinkTilt{0%,100%{transform:rotate(0deg);}30%{transform:rotate(-3deg);}70%{transform:rotate(1deg);}}',
        '.anchor-expression-focused .anchor-pupil{animation:focusPupil 3s ease-in-out infinite;}',
        '@keyframes focusPupil{0%,100%{transform:translate(0,0);}50%{transform:translate(1.5px,0);}}',
        # Shot entrance animations (delay values pre-computed in `d`)
        '.stage-topbar{opacity:0;animation:shotFadeIn 0.5s ' + str(d["topbar"]) + 's ease-out both;}',
        '.stage-title-area{opacity:0;animation:shotFadeIn 0.6s ' + str(d["title"]) + 's ease-out both;}',
        '@keyframes shotFadeIn{from{opacity:0;transform:translateY(-6px);}to{opacity:1;transform:translateY(0);}}',
        '@keyframes anchorEnter{from{opacity:0;transform:translateX(-14px) translateY(8px);}'
        'to{opacity:1;transform:translateX(0) translateY(0);}}',
        '.stage-main-card{opacity:0;animation:shotCardIn 0.6s ' + str(d["mainCard"]) + 's ease-out both;}',
        '@keyframes shotCardIn{from{opacity:0;transform:translateY(14px) scale(0.97);}'
        'to{opacity:1;transform:translateY(0) scale(1);}}',
        '.stage-subtitle-bar{opacity:0;animation:shotFadeIn 0.5s ' + str(d["subtitle"]) + 's ease-out both;}',
        '.stage-supporting{opacity:0;animation:shotFadeIn 0.5s ' + str(d["supporting"]) + 's ease-out both;}',
        '.stage-support-card:nth-child(1){animation:shotCardIn 0.5s ' + str(d["support1"]) + 's ease-out both;}',
        '.stage-support-card:nth-child(2){animation:shotCardIn 0.5s ' + str(d["support2"]) + 's ease-out both;}',
        '.stage-support-card:nth-child(3){animation:shotCardIn 0.5s ' + str(d["support3"]) + 's ease-out both;}',
        # Progress bar
        '.stage-progress-wrap{position:relative;margin:0 24px 12px;z-index:25;height:4px;}',
        '.stage-progress-track{width:100%;height:100%;background:rgba(255,255,255,.15);'
        'border-radius:999px;overflow:hidden;}',
        '.stage-progress-fill{width:0%;height:100%;background:linear-gradient(90deg,#dc2626,#f87171);'
        'border-radius:999px;animation:mockProgressFill ' + str(total_dur) + 's linear forwards;}',
        '@keyframes mockProgressFill{0%{width:0%;}100%{width:100%;}}',
        # Shot label
        '.stage-shot-label{position:absolute;top:38px;left:50%;transform:translateX(-50%);z-index:22;'
        'background:rgba(0,0,0,.55);border-radius:20px;padding:2px 10px;font-size:8px;color:#fca5a5;'
        'white-space:nowrap;letter-spacing:0.5px;opacity:0;'
        'animation:shotFadeIn 0.4s ' + str(d["shotLabel"]) + 's ease-out both;}',
        # ---- Seek-mode overrides ----
        # When data-export-seek="1", pause CSS animations and use JS-driven visibility.
        # This gives Playwright deterministic frame capture.
        'html[data-export-seek="1"] .stage-layer{opacity:0!important;visibility:hidden!important;'
        'animation-play-state:paused!important;}',
        'html[data-export-seek="1"] .stage-layer.is-visible{opacity:1!important;visibility:visible!important;}',
        # Pause progress bar CSS animation during seek mode
        'html[data-export-seek="1"] .stage-progress-fill{animation:none!important;}',
    ]
    stage_css = "<style>\n" + "\n".join(css_parts) + "\n</style>\n"

    # ---- Timing shim (inline JS) ----
    # This shim is required for export_video.py compatibility.
    # It is a controlled, self-contained script with no external dependencies.
    # __prepareSeekMode__() puts the DOM into deterministic seek mode (no CSS animation delays).
    # __setTime__(t) controls which stage layers are visible based on data-appear-at.
    timing_shim = (
        '<script>\n'
        'window.__ANIMATION_READY__ = true;\n'
        f'window.__getTotalDuration__ = function () {{ return {total_dur}; }};\n'
        'window.__prepareSeekMode__ = function () {\n'
        '  var root = document.documentElement;\n'
        '  if (root.setAttribute) root.setAttribute("data-export-seek", "1");\n'
        '};\n'
        'window.__setTime__ = function (t) {\n'
        '  window.__prepareSeekMode__();\n'
        '  t = Number(t || 0);\n'
        '  var root = document.documentElement;\n'
        '  if (root.setAttribute) root.setAttribute("data-shot-time", String(t));\n'
        '  document.querySelectorAll("[data-appear-at]").forEach(function(el) {\n'
        '    var appear = Number(el.getAttribute("data-appear-at") || "0");\n'
        '    if (t >= appear) el.classList.add("is-visible");\n'
        '    else el.classList.remove("is-visible");\n'
        '  });\n'
        '  var fill = document.querySelector("[data-progress-fill]");\n'
        '  if (fill) {\n'
        '    var total = window.__getTotalDuration__() || 1;\n'
        '    var pct = Math.max(0, Math.min(100, (t / total) * 100));\n'
        '    fill.style.width = pct + "%";\n'
        '  }\n'
        '};\n'
        '</script>\n'
    )

    # ---- Assemble document ----
    news_count = len(news_cards)
    return (
        '<!DOCTYPE html>\n'
        '<html lang="zh-CN">\n'
        '<head>\n'
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        f'<title>{title}</title>\n'
        f'{stage_css}'
        '</head>\n'
        '<body>\n'
        '<div class="video-stage-shell">\n'
        '<div class="video-stage stage-16x9">\n'
        '<div class="stage-bg"></div>\n'
        # Topbar
        '<div class="stage-topbar stage-layer" data-appear-at="' + str(d["topbar"]) + '">'
        '<span class="stage-breaking-badge">🔴 BREAKING NEWS</span>'
        f'<span class="stage-meta">{news_count} 条 · {total_time_str}</span>'
        '</div>\n'
        # Title area
        '<div class="stage-title-area stage-layer" data-appear-at="' + str(d["title"]) + '">'
        f'<div class="stage-episode-title">{escape_html(episode.get("title") or "")}</div>'
        f'<div class="stage-episode-subtitle">{escape_html(episode.get("subtitle") or "")}</div>'
        '</div>\n'
        # Main row: anchor (left) + content (lead + supporting) (right)
        '<div class="stage-main-row">\n'
        f'<div class="stage-anchor-col">{anchor_layer_html}</div>\n'
        '<div class="stage-content-col">\n'
        f'{lead_html}\n'
        f'{support_html}\n'
        '</div>\n'
        '</div>\n'
        # Progress bar (always visible, data-appear-at=0)
        '<div class="stage-progress-wrap stage-layer" data-appear-at="0">'
        '<div class="stage-progress-track">'
        '<div class="stage-progress-fill" data-progress-fill="true"></div>'
        '</div>'
        '</div>\n'
        # Recap chip (overlay, top-right)
        f'{recap_html}\n'
        # Shot metadata
        f'<div class="stage-shot-meta" data-shot-count="{len(shot_timeline)}" '
        f'data-duration="{total_dur}" style="display:none">{meta_parts}</div>\n'
        '</div>\n'
        '</div>\n'
        # Timing shim (must be after DOM is defined)
        f'{timing_shim}'
        '</body>\n'
        '</html>\n'
    )


# ---------------------------------------------------------------------------
# Shared animation contract (reused by every exportable style)
# ---------------------------------------------------------------------------

def _seek_mode_css_rules() -> list[str]:
    """CSS rules that make a style deterministically seekable by export_video.py.

    Any element with class ``stage-layer`` is hidden until JS adds ``is-visible``.
    The progress fill's CSS animation is paused so __setTime__ can drive its width.
    """
    return [
        'html[data-export-seek="1"] .stage-layer{opacity:0!important;visibility:hidden!important;'
        'animation-play-state:paused!important;}',
        'html[data-export-seek="1"] .stage-layer.is-visible{opacity:1!important;visibility:visible!important;}',
        'html[data-export-seek="1"] .stage-progress-fill{animation:none!important;}',
    ]


def _timing_shim(total_dur: float) -> str:
    """Inline JS shim implementing the export contract.

    Exposes __ANIMATION_READY__, __getTotalDuration__, __prepareSeekMode__ and
    __setTime__(t). __setTime__ toggles ``.is-visible`` on ``[data-appear-at]``
    elements and drives ``[data-progress-fill]`` width. Style-agnostic.
    """
    return (
        '<script>\n'
        'window.__ANIMATION_READY__ = true;\n'
        f'window.__getTotalDuration__ = function () {{ return {total_dur}; }};\n'
        'window.__prepareSeekMode__ = function () {\n'
        '  var root = document.documentElement;\n'
        '  if (root.setAttribute) root.setAttribute("data-export-seek", "1");\n'
        '};\n'
        'window.__setTime__ = function (t) {\n'
        '  window.__prepareSeekMode__();\n'
        '  t = Number(t || 0);\n'
        '  var root = document.documentElement;\n'
        '  if (root.setAttribute) root.setAttribute("data-shot-time", String(t));\n'
        '  document.querySelectorAll("[data-appear-at]").forEach(function(el) {\n'
        '    var appear = Number(el.getAttribute("data-appear-at") || "0");\n'
        '    if (t >= appear) el.classList.add("is-visible");\n'
        '    else el.classList.remove("is-visible");\n'
        '  });\n'
        '  var fill = document.querySelector("[data-progress-fill]");\n'
        '  if (fill) {\n'
        '    var total = window.__getTotalDuration__() || 1;\n'
        '    var pct = Math.max(0, Math.min(100, (t / total) * 100));\n'
        '    fill.style.width = pct + "%";\n'
        '  }\n'
        '};\n'
        '</script>\n'
    )


def _split_lead_support(contract: dict) -> tuple[dict | None, list[dict]]:
    """Return (lead_card, support_cards) from a contract's news_cards."""
    news_cards: list[dict] = (contract.get("sections") or {}).get("news_cards") or []
    lead_card: dict | None = None
    support_cards: list[dict] = []
    for card in news_cards:
        if card.get("is_lead") and lead_card is None:
            lead_card = card
        else:
            support_cards.append(card)
    if lead_card is None and news_cards:
        lead_card = news_cards[0]
        support_cards = news_cards[1:]
    return lead_card, support_cards


def _stage_delays(contract: dict) -> tuple[dict, float]:
    """Resolve concrete per-layer appear delays + total duration for any style."""
    timing = build_breaking_news_stage_timing(contract)
    delays = timing["delays"]
    total_dur = timing["totalDurationSec"]
    defaults = {
        "recap": 0.3, "openingLabel": 0.15, "closing": 9.5, "shotLabel": 0.1,
        "topbar": 0.1, "title": 0.2, "mainCard": 2.5, "subtitle": 3.2,
        "supporting": 5.0, "support1": 5.2, "support2": 5.55, "support3": 5.9,
    }
    d = {k: float(delays.get(k, v)) for k, v in defaults.items()}
    return d, total_dur


# ---------------------------------------------------------------------------
# Style: timeline_daily_v1 (时间线日报风) — clean light editorial brief
# ---------------------------------------------------------------------------

def render_timeline_daily_stage_episode_html(contract: dict) -> str:
    """Render a self-contained timeline_daily_v1 9:16 stage.

    Light "daily brief" look: paper background, a vertical timeline with the lead
    item highlighted and supporting items appearing in sequence. Reuses the shared
    seek contract (data-appear-at / is-visible / data-progress-fill).
    """
    episode = contract.get("episode") or {}
    sections = contract.get("sections") or {}

    title = escape_html(episode.get("title") or "今日速览")
    subtitle = escape_html(episode.get("subtitle") or "")
    estimated_sec = float(episode.get("estimated_duration_sec") or 30)
    total_time_str = format_timecode(estimated_sec)

    lead_card, support_cards = _split_lead_support(contract)
    d, total_dur = _stage_delays(contract)

    news_cards = sections.get("news_cards") or []
    news_count = len(news_cards)

    # ---- Item rows ----
    rows = []
    if lead_card:
        rows.append(
            '<div class="td-item td-item-lead stage-layer" data-appear-at="' + str(d["mainCard"]) + '">'
            '<div class="td-dot td-dot-lead"></div>'
            '<div class="td-card">'
            '<div class="td-badge">★ 头条</div>'
            '<div class="td-headline">' + escape_html(lead_card.get("headline") or "") + '</div>'
            '<div class="td-meta">' + escape_html(lead_card.get("time_range") or "")
            + ' · ' + escape_html(str(lead_card.get("duration_hint_sec") or "")) + 's</div>'
            '</div>'
            '</div>'
        )
    support_delays = [d["support1"], d["support2"], d["support3"]]
    for i, card in enumerate(support_cards[:3]):
        appear = support_delays[i] if i < len(support_delays) else d["supporting"] + i * 0.4
        rows.append(
            '<div class="td-item stage-layer" data-appear-at="' + str(appear) + '">'
            '<div class="td-dot"></div>'
            '<div class="td-card td-card-support">'
            '<div class="td-headline-sm">' + escape_html(card.get("headline") or "") + '</div>'
            '<div class="td-meta">' + escape_html(card.get("source") or card.get("time_range") or "") + '</div>'
            '</div>'
            '</div>'
        )
    rows_html = "".join(rows)

    closing = sections.get("closing") or {}
    closing_html = (
        '<div class="td-closing stage-layer" data-appear-at="' + str(d["closing"]) + '">'
        '<span class="td-closing-tag">结语</span>'
        '<span>' + escape_html(closing.get("title") or "") + '</span>'
        '</div>'
    )

    # ---- CSS (plain strings; delays concatenated to avoid f-string brace clash) ----
    css_parts = [
        '*{box-sizing:border-box;margin:0;padding:0;}',
        '.video-stage-shell{width:100vw;height:100vh;background:#faf8f2;overflow:hidden;}',
        '.video-stage{position:relative;width:100%;height:100%;overflow:hidden;background:#faf8f2;'
        'display:flex;flex-direction:column;'
        "font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;}",
        '.td-bg{position:absolute;inset:0;background:'
        'repeating-linear-gradient(0deg,transparent,transparent 38px,rgba(15,23,42,.04) 39px);}',
        # Header
        '.td-header{position:relative;z-index:15;padding:5% 22px 14px;'
        'background:linear-gradient(180deg,#faf8f2 70%,rgba(250,248,242,0) 100%);}',
        '.td-kicker{display:flex;align-items:center;gap:8px;margin-bottom:8px;}',
        '.td-date-pill{background:#1d4ed8;color:#fff;font-size:10px;font-weight:700;'
        'letter-spacing:1px;padding:3px 10px;border-radius:999px;}',
        '.td-count{color:#64748b;font-size:10px;font-family:monospace;}',
        '.td-title{color:#0f172a;font-size:19px;font-weight:800;line-height:1.25;margin-bottom:4px;}',
        '.td-subtitle{color:#475569;font-size:11px;line-height:1.4;}',
        # Timeline list
        '.td-list{position:relative;z-index:12;flex:1 1 auto;min-height:0;'
        'padding:8px 22px 8px 30px;overflow:hidden;}',
        '.td-item{position:relative;display:flex;gap:12px;padding:8px 0;}',
        '.td-item::before{content:"";position:absolute;left:4px;top:0;bottom:-8px;width:2px;'
        'background:#d6d0c4;}',
        '.td-item:last-child::before{display:none;}',
        '.td-dot{flex:0 0 10px;width:10px;height:10px;border-radius:50%;background:#94a3b8;'
        'border:2px solid #faf8f2;margin-left:-1px;margin-top:4px;z-index:1;position:relative;}',
        '.td-dot-lead{background:#1d4ed8;box-shadow:0 0 0 4px rgba(29,78,216,.15);}',
        '.td-card{flex:1;background:#fff;border:1px solid #e7e2d6;border-radius:12px;padding:12px 14px;'
        'box-shadow:0 2px 8px rgba(15,23,42,.05);}',
        '.td-item-lead .td-card{border-left:4px solid #1d4ed8;}',
        '.td-card-support{padding:10px 12px;}',
        '.td-badge{display:inline-block;background:#dbeafe;color:#1d4ed8;font-size:9px;font-weight:800;'
        'letter-spacing:1px;padding:2px 8px;border-radius:4px;margin-bottom:6px;}',
        '.td-headline{color:#0f172a;font-size:15px;font-weight:800;line-height:1.35;margin-bottom:6px;}',
        '.td-headline-sm{color:#1e293b;font-size:12px;font-weight:600;line-height:1.35;margin-bottom:4px;'
        'display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;}',
        '.td-meta{color:#94a3b8;font-size:9px;font-family:monospace;}',
        # Closing
        '.td-closing{position:relative;z-index:14;margin:0 22px 8px;'
        'display:flex;align-items:center;gap:8px;color:#1e293b;font-size:11px;font-weight:600;'
        'background:#f1ede3;border-radius:10px;padding:8px 12px;}',
        '.td-closing-tag{background:#1d4ed8;color:#fff;font-size:9px;font-weight:800;'
        'padding:2px 8px;border-radius:4px;}',
        # Footer / progress
        '.td-footer{position:relative;z-index:20;padding:12px 22px 14px;margin-top:auto;'
        'background:linear-gradient(0deg,#faf8f2 60%,rgba(250,248,242,0) 100%);}',
        '.stage-progress-track{width:100%;height:4px;background:#e0dbcf;border-radius:999px;overflow:hidden;}',
        '.stage-progress-fill{width:0%;height:100%;background:linear-gradient(90deg,#1d4ed8,#60a5fa);'
        'border-radius:999px;animation:tdProgress ' + str(total_dur) + 's linear forwards;}',
        '@keyframes tdProgress{0%{width:0%;}100%{width:100%;}}',
        # Live (non-seek) entrance animation
        '.td-item,.td-closing{opacity:0;animation:tdFadeIn .5s ease-out both;}',
        '.td-header{opacity:0;animation:tdFadeIn .6s ' + str(d["title"]) + 's ease-out both;}',
        '@keyframes tdFadeIn{from{opacity:0;transform:translateY(10px);}to{opacity:1;transform:translateY(0);}}',
    ] + _seek_mode_css_rules()
    stage_css = "<style>\n" + "\n".join(css_parts) + "\n</style>\n"

    return (
        '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        f'<title>{title}</title>\n{stage_css}</head>\n<body>\n'
        '<div class="video-stage-shell">\n<div class="video-stage stage-9x16">\n'
        '<div class="td-bg"></div>\n'
        '<div class="td-header stage-layer" data-appear-at="' + str(d["title"]) + '">'
        '<div class="td-kicker"><span class="td-date-pill">今日 AI 速览</span>'
        f'<span class="td-count">{news_count} 条 · {total_time_str}</span></div>'
        f'<div class="td-title">{title}</div>'
        f'<div class="td-subtitle">{subtitle}</div>'
        '</div>\n'
        f'<div class="td-list">{rows_html}</div>\n'
        f'{closing_html}\n'
        '<div class="td-footer stage-layer" data-appear-at="0">'
        '<div class="stage-progress-track"><div class="stage-progress-fill" data-progress-fill="true"></div></div>'
        '</div>\n'
        '</div>\n</div>\n'
        f'{_timing_shim(total_dur)}'
        '</body>\n</html>\n'
    )


# ---------------------------------------------------------------------------
# Style: data_dashboard_v1 (数据仪表盘风) — dark dashboard with real bar chart
# ---------------------------------------------------------------------------

def render_data_dashboard_stage_episode_html(contract: dict) -> str:
    """Render a self-contained data_dashboard_v1 9:16 stage.

    Dark "control room" look: header with a LIVE dot, a row of stat tiles, and a
    horizontal bar chart whose bars are driven by each news card's real
    duration_hint_sec from the contract. Reuses the shared seek contract.
    """
    episode = contract.get("episode") or {}
    sections = contract.get("sections") or {}

    title = escape_html(episode.get("title") or "数据简报")
    subtitle = escape_html(episode.get("subtitle") or "")
    estimated_sec = float(episode.get("estimated_duration_sec") or 30)
    total_time_str = format_timecode(estimated_sec)

    lead_card, support_cards = _split_lead_support(contract)
    d, total_dur = _stage_delays(contract)

    news_cards = sections.get("news_cards") or []
    news_count = len(news_cards)
    lead_source = escape_html((lead_card or {}).get("source")
                              or (lead_card or {}).get("role") or "头条")

    # ---- Stat tiles (derived from contract) ----
    avg_sec = (estimated_sec / news_count) if news_count else estimated_sec
    stats = [
        ("新闻条数", str(news_count), "条"),
        ("总时长", total_time_str, ""),
        ("平均段长", str(int(round(avg_sec))), "s"),
    ]
    stat_html = "".join(
        '<div class="dd-stat">'
        '<div class="dd-stat-val">' + escape_html(val) + '<span class="dd-stat-unit">' + escape_html(unit) + '</span></div>'
        '<div class="dd-stat-label">' + escape_html(label) + '</div>'
        '</div>'
        for label, val, unit in stats
    )

    # ---- Bar chart rows (real duration_hint_sec per card) ----
    ordered = sorted(
        [c for c in news_cards if isinstance(c, dict)],
        key=lambda c: c.get("order", 0),
    )
    max_dur = max((float(c.get("duration_hint_sec") or 0) for c in ordered), default=1.0) or 1.0
    support_delays = [d["mainCard"], d["support1"], d["support2"], d["support3"]]
    bar_rows = []
    for i, card in enumerate(ordered[:4]):
        dur = float(card.get("duration_hint_sec") or 0)
        pct = max(8, int(round((dur / max_dur) * 100)))
        appear = support_delays[i] if i < len(support_delays) else d["supporting"] + i * 0.4
        is_lead = bool(card.get("is_lead")) or (lead_card is not None and card is lead_card)
        bar_cls = "dd-bar-fill dd-bar-lead" if is_lead else "dd-bar-fill"
        bar_rows.append(
            '<div class="dd-bar-row stage-layer" data-appear-at="' + str(appear) + '">'
            '<div class="dd-bar-head">'
            '<span class="dd-bar-label">' + escape_html(card.get("headline") or "") + '</span>'
            '<span class="dd-bar-val">' + escape_html(str(int(dur))) + 's</span>'
            '</div>'
            '<div class="dd-bar-track"><div class="' + bar_cls + '" style="width:' + str(pct) + '%"></div></div>'
            '</div>'
        )
    bars_html = "".join(bar_rows)

    closing = sections.get("closing") or {}
    closing_html = (
        '<div class="dd-closing stage-layer" data-appear-at="' + str(d["closing"]) + '">'
        '<span class="dd-closing-tag">▎结论</span>'
        '<span>' + escape_html(closing.get("title") or "") + '</span>'
        '</div>'
    )

    css_parts = [
        '*{box-sizing:border-box;margin:0;padding:0;}',
        '.video-stage-shell{width:100vw;height:100vh;background:#0a0f1a;overflow:hidden;}',
        '.video-stage{position:relative;width:100%;height:100%;overflow:hidden;background:#0a0f1a;'
        'display:flex;flex-direction:column;'
        "font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;}",
        '.dd-bg{position:absolute;inset:0;background-image:'
        'linear-gradient(rgba(34,211,238,.06) 1px,transparent 1px),'
        'linear-gradient(90deg,rgba(34,211,238,.06) 1px,transparent 1px);'
        'background-size:28px 28px;}',
        # Header
        '.dd-header{position:relative;z-index:15;padding:5% 20px 12px;'
        'background:linear-gradient(180deg,#0a0f1a 70%,rgba(10,15,26,0) 100%);}',
        '.dd-kicker{display:flex;align-items:center;gap:8px;margin-bottom:8px;}',
        '.dd-live{display:flex;align-items:center;gap:5px;background:rgba(16,185,129,.15);'
        'border:1px solid #10b981;color:#34d399;font-size:9px;font-weight:800;letter-spacing:1px;'
        'padding:2px 8px;border-radius:999px;}',
        '.dd-live-dot{width:6px;height:6px;border-radius:50%;background:#34d399;'
        'animation:ddBlink 1.4s ease-in-out infinite;}',
        '@keyframes ddBlink{0%,100%{opacity:1;}50%{opacity:.3;}}',
        '.dd-count{color:#64748b;font-size:10px;font-family:monospace;}',
        '.dd-title{color:#f1f5f9;font-size:18px;font-weight:800;line-height:1.25;margin-bottom:3px;}',
        '.dd-subtitle{color:#7c8aa0;font-size:10px;line-height:1.4;}',
        # Stat tiles
        '.dd-stats{position:relative;z-index:12;display:flex;gap:8px;margin:0 20px;}',
        '.dd-stat{flex:1;background:rgba(20,28,44,.85);border:1px solid #1e293b;border-radius:10px;'
        'padding:10px 8px;text-align:center;}',
        '.dd-stat-val{color:#22d3ee;font-size:20px;font-weight:800;font-family:monospace;line-height:1;}',
        '.dd-stat-unit{color:#475569;font-size:10px;font-weight:600;margin-left:2px;}',
        '.dd-stat-label{color:#7c8aa0;font-size:9px;margin-top:5px;}',
        # Bar chart
        '.dd-chart{position:relative;z-index:12;margin:16px 20px 0;flex:1 1 auto;min-height:0;overflow:hidden;}',
        '.dd-chart-title{color:#94a3b8;font-size:10px;font-weight:700;letter-spacing:1px;'
        'margin-bottom:10px;text-transform:uppercase;}',
        '.dd-bar-row{margin-bottom:14px;}',
        '.dd-bar-head{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:5px;gap:8px;}',
        '.dd-bar-label{color:#cbd5e1;font-size:11px;font-weight:600;line-height:1.3;'
        'display:-webkit-box;-webkit-line-clamp:1;-webkit-box-orient:vertical;overflow:hidden;}',
        '.dd-bar-val{color:#22d3ee;font-size:10px;font-family:monospace;flex:0 0 auto;}',
        '.dd-bar-track{height:8px;background:rgba(30,41,59,.8);border-radius:999px;overflow:hidden;}',
        '.dd-bar-fill{height:100%;background:linear-gradient(90deg,#0891b2,#22d3ee);'
        'border-radius:999px;animation:ddBarGrow .7s ease-out both;}',
        '.dd-bar-lead{background:linear-gradient(90deg,#10b981,#34d399);'
        'box-shadow:0 0 10px rgba(52,211,153,.4);}',
        '@keyframes ddBarGrow{from{transform:scaleX(0);transform-origin:left;}to{transform:scaleX(1);transform-origin:left;}}',
        # Closing
        '.dd-closing{position:relative;z-index:14;margin:10px 20px 0;'
        'display:flex;align-items:center;gap:8px;color:#cbd5e1;font-size:11px;font-weight:600;'
        'background:rgba(20,28,44,.85);border:1px solid #1e293b;border-radius:10px;padding:9px 12px;}',
        '.dd-closing-tag{color:#34d399;font-weight:800;font-size:10px;}',
        # Footer / progress
        '.dd-footer{position:relative;z-index:20;padding:12px 20px 14px;margin-top:auto;'
        'background:linear-gradient(0deg,#0a0f1a 60%,rgba(10,15,26,0) 100%);}',
        '.stage-progress-track{width:100%;height:4px;background:#1e293b;border-radius:999px;overflow:hidden;}',
        '.stage-progress-fill{width:0%;height:100%;background:linear-gradient(90deg,#0891b2,#22d3ee);'
        'border-radius:999px;animation:ddProgress ' + str(total_dur) + 's linear forwards;}',
        '@keyframes ddProgress{0%{width:0%;}100%{width:100%;}}',
        # Live (non-seek) entrance
        '.dd-bar-row,.dd-closing,.dd-stats{opacity:0;animation:ddFadeIn .5s ease-out both;}',
        '.dd-header{opacity:0;animation:ddFadeIn .6s ' + str(d["title"]) + 's ease-out both;}',
        '.dd-stats{animation-delay:' + str(d["title"] + 0.2) + 's;}',
        '@keyframes ddFadeIn{from{opacity:0;transform:translateY(10px);}to{opacity:1;transform:translateY(0);}}',
    ] + _seek_mode_css_rules()
    stage_css = "<style>\n" + "\n".join(css_parts) + "\n</style>\n"

    return (
        '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        f'<title>{title}</title>\n{stage_css}</head>\n<body>\n'
        '<div class="video-stage-shell">\n<div class="video-stage stage-9x16">\n'
        '<div class="dd-bg"></div>\n'
        '<div class="dd-header stage-layer" data-appear-at="' + str(d["title"]) + '">'
        '<div class="dd-kicker"><span class="dd-live"><span class="dd-live-dot"></span>LIVE 数据简报</span>'
        f'<span class="dd-count">{news_count} 条 · {total_time_str} · {lead_source}</span></div>'
        f'<div class="dd-title">{title}</div>'
        f'<div class="dd-subtitle">{subtitle}</div>'
        '</div>\n'
        '<div class="dd-stats stage-layer" data-appear-at="' + str(d["title"] + 0.2) + '">'
        f'{stat_html}'
        '</div>\n'
        '<div class="dd-chart">'
        '<div class="dd-chart-title stage-layer" data-appear-at="' + str(d["mainCard"]) + '">各条目时长分布</div>'
        f'{bars_html}'
        '</div>\n'
        f'{closing_html}\n'
        '<div class="dd-footer stage-layer" data-appear-at="0">'
        '<div class="stage-progress-track"><div class="stage-progress-fill" data-progress-fill="true"></div></div>'
        '</div>\n'
        '</div>\n</div>\n'
        f'{_timing_shim(total_dur)}'
        '</body>\n</html>\n'
    )


# ---------------------------------------------------------------------------
# Style: podcast_cards_v1 (播客卡片风) — two-speaker "now playing" look
# ---------------------------------------------------------------------------

def render_podcast_cards_stage_episode_html(contract: dict) -> str:
    """Render a self-contained podcast_cards_v1 9:16 stage.

    Podcast aesthetic: violet gradient, host/guest speaker chips, a "now playing"
    card for the lead topic with a frozen waveform, and an up-next queue for the
    supporting items. Reuses the shared seek contract.
    """
    episode = contract.get("episode") or {}
    sections = contract.get("sections") or {}

    title = escape_html(episode.get("title") or "AI 播客")
    subtitle = escape_html(episode.get("subtitle") or "")
    estimated_sec = float(episode.get("estimated_duration_sec") or 30)
    total_time_str = format_timecode(estimated_sec)

    lead_card, support_cards = _split_lead_support(contract)
    d, total_dur = _stage_delays(contract)
    news_cards = sections.get("news_cards") or []
    news_count = len(news_cards)

    # Frozen waveform (static varied heights → deterministic frames)
    wave_heights = [40, 70, 95, 55, 80, 35, 90, 60, 100, 45, 75, 50, 85, 30, 65]
    wave_html = "".join(
        '<span class="pc-wave-bar" style="height:' + str(h) + '%"></span>' for h in wave_heights
    )

    now_playing = (
        '<div class="pc-now stage-layer" data-appear-at="' + str(d["mainCard"]) + '">'
        '<div class="pc-now-tag">▶ 正在讨论</div>'
        '<div class="pc-now-headline">' + escape_html((lead_card or {}).get("headline") or "") + '</div>'
        '<div class="pc-wave">' + wave_html + '</div>'
        '</div>'
    )

    queue_delays = [d["support1"], d["support2"], d["support3"]]
    queue_rows = []
    for i, card in enumerate(support_cards[:3]):
        appear = queue_delays[i] if i < len(queue_delays) else d["supporting"] + i * 0.4
        queue_rows.append(
            '<div class="pc-queue-item stage-layer" data-appear-at="' + str(appear) + '">'
            '<span class="pc-queue-num">' + str(i + 2) + '</span>'
            '<span class="pc-queue-text">' + escape_html(card.get("headline") or "") + '</span>'
            '</div>'
        )
    queue_html = "".join(queue_rows)

    closing = sections.get("closing") or {}
    closing_html = (
        '<div class="pc-closing stage-layer" data-appear-at="' + str(d["closing"]) + '">'
        '<span class="pc-closing-tag">尾声</span>'
        '<span>' + escape_html(closing.get("title") or "") + '</span>'
        '</div>'
    )

    css_parts = [
        '*{box-sizing:border-box;margin:0;padding:0;}',
        '.video-stage-shell{width:100vw;height:100vh;background:#160c30;overflow:hidden;}',
        '.video-stage{position:relative;width:100%;height:100%;overflow:hidden;'
        'background:linear-gradient(165deg,#2a1758 0%,#160c30 55%,#0d0820 100%);'
        'display:flex;flex-direction:column;'
        "font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;}",
        '.pc-bg{position:absolute;inset:0;background:radial-gradient(circle at 70% 12%,rgba(139,92,246,.28),transparent 45%);}',
        # Header
        '.pc-header{position:relative;z-index:15;padding:5% 20px 10px;}',
        '.pc-kicker{display:flex;align-items:center;gap:8px;margin-bottom:8px;}',
        '.pc-badge{background:rgba(139,92,246,.25);border:1px solid #8b5cf6;color:#c4b5fd;'
        'font-size:9px;font-weight:800;letter-spacing:2px;padding:3px 10px;border-radius:999px;}',
        '.pc-count{color:#8b7bb8;font-size:10px;font-family:monospace;}',
        '.pc-title{color:#f5f3ff;font-size:18px;font-weight:800;line-height:1.25;margin-bottom:3px;}',
        '.pc-subtitle{color:#a99fd0;font-size:10px;line-height:1.4;}',
        # Speakers
        '.pc-speakers{position:relative;z-index:12;display:flex;gap:10px;margin:0 20px;}',
        '.pc-speaker{flex:1;display:flex;align-items:center;gap:8px;background:rgba(255,255,255,.06);'
        'border:1px solid rgba(139,92,246,.3);border-radius:12px;padding:8px 10px;}',
        '.pc-avatar{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;'
        'justify-content:center;font-size:14px;flex:0 0 auto;}',
        '.pc-avatar-host{background:#8b5cf6;}',
        '.pc-avatar-guest{background:#ec4899;}',
        '.pc-speaker-name{color:#ede9fe;font-size:11px;font-weight:700;}',
        '.pc-speaker-role{color:#9d92c4;font-size:8px;}',
        # Now playing
        '.pc-now{position:relative;z-index:12;margin:14px 20px 0;'
        'background:rgba(255,255,255,.07);border:1px solid rgba(196,181,253,.35);border-radius:16px;padding:16px;}',
        '.pc-now-tag{display:inline-block;background:#8b5cf6;color:#fff;font-size:9px;font-weight:800;'
        'letter-spacing:1px;padding:2px 8px;border-radius:4px;margin-bottom:10px;}',
        '.pc-now-headline{color:#fff;font-size:15px;font-weight:800;line-height:1.4;margin-bottom:14px;}',
        '.pc-wave{display:flex;align-items:center;gap:3px;height:36px;}',
        '.pc-wave-bar{flex:1;background:linear-gradient(180deg,#c4b5fd,#8b5cf6);border-radius:999px;min-height:6px;}',
        # Queue
        '.pc-queue{position:relative;z-index:12;margin:16px 20px 0;flex:1 1 auto;min-height:0;overflow:hidden;}',
        '.pc-queue-title{color:#a99fd0;font-size:10px;font-weight:700;letter-spacing:1px;'
        'text-transform:uppercase;margin-bottom:10px;}',
        '.pc-queue-item{display:flex;align-items:center;gap:10px;padding:9px 0;'
        'border-bottom:1px solid rgba(255,255,255,.07);}',
        '.pc-queue-num{flex:0 0 22px;height:22px;border-radius:50%;background:rgba(139,92,246,.25);'
        'color:#c4b5fd;font-size:11px;font-weight:800;display:flex;align-items:center;justify-content:center;}',
        '.pc-queue-text{color:#d6cef0;font-size:12px;font-weight:600;line-height:1.3;'
        'display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;}',
        # Closing
        '.pc-closing{position:relative;z-index:14;margin:10px 20px 0;'
        'display:flex;align-items:center;gap:8px;color:#ede9fe;font-size:11px;font-weight:600;'
        'background:rgba(139,92,246,.18);border:1px solid rgba(139,92,246,.35);border-radius:10px;padding:9px 12px;}',
        '.pc-closing-tag{background:#8b5cf6;color:#fff;font-size:9px;font-weight:800;padding:2px 8px;border-radius:4px;}',
        # Footer / progress
        '.pc-footer{position:relative;z-index:20;padding:12px 20px 14px;margin-top:auto;}',
        '.stage-progress-track{width:100%;height:4px;background:rgba(255,255,255,.12);border-radius:999px;overflow:hidden;}',
        '.stage-progress-fill{width:0%;height:100%;background:linear-gradient(90deg,#8b5cf6,#ec4899);'
        'border-radius:999px;animation:pcProgress ' + str(total_dur) + 's linear forwards;}',
        '@keyframes pcProgress{0%{width:0%;}100%{width:100%;}}',
        '.pc-now,.pc-queue-item,.pc-closing,.pc-speakers{opacity:0;animation:pcFadeIn .5s ease-out both;}',
        '.pc-header{opacity:0;animation:pcFadeIn .6s ' + str(d["title"]) + 's ease-out both;}',
        '@keyframes pcFadeIn{from{opacity:0;transform:translateY(10px);}to{opacity:1;transform:translateY(0);}}',
    ] + _seek_mode_css_rules()
    stage_css = "<style>\n" + "\n".join(css_parts) + "\n</style>\n"

    return (
        '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        f'<title>{title}</title>\n{stage_css}</head>\n<body>\n'
        '<div class="video-stage-shell">\n<div class="video-stage stage-9x16">\n'
        '<div class="pc-bg"></div>\n'
        '<div class="pc-header stage-layer" data-appear-at="' + str(d["title"]) + '">'
        '<div class="pc-kicker"><span class="pc-badge">🎙 PODCAST</span>'
        f'<span class="pc-count">{news_count} 话题 · {total_time_str}</span></div>'
        f'<div class="pc-title">{title}</div>'
        f'<div class="pc-subtitle">{subtitle}</div>'
        '</div>\n'
        '<div class="pc-speakers stage-layer" data-appear-at="' + str(d["title"] + 0.15) + '">'
        '<div class="pc-speaker"><span class="pc-avatar pc-avatar-host">🧑‍💼</span>'
        '<span><div class="pc-speaker-name">主持人</div><div class="pc-speaker-role">提问 · 串场</div></span></div>'
        '<div class="pc-speaker"><span class="pc-avatar pc-avatar-guest">🧠</span>'
        '<span><div class="pc-speaker-name">嘉宾</div><div class="pc-speaker-role">分析 · 讲解</div></span></div>'
        '</div>\n'
        f'{now_playing}\n'
        '<div class="pc-queue">'
        '<div class="pc-queue-title stage-layer" data-appear-at="' + str(d["support1"]) + '">UP NEXT · 待讨论</div>'
        f'{queue_html}'
        '</div>\n'
        f'{closing_html}\n'
        '<div class="pc-footer stage-layer" data-appear-at="0">'
        '<div class="stage-progress-track"><div class="stage-progress-fill" data-progress-fill="true"></div></div>'
        '</div>\n'
        '</div>\n</div>\n'
        f'{_timing_shim(total_dur)}'
        '</body>\n</html>\n'
    )


# ---------------------------------------------------------------------------
# Style: research_briefing_v1 (研究室简报风) — academic numbered findings
# ---------------------------------------------------------------------------

def render_research_briefing_stage_episode_html(contract: dict) -> str:
    """Render a self-contained research_briefing_v1 9:16 stage.

    Lab-briefing aesthetic: slate background, monospace kicker, an abstract block
    for the lead, and numbered findings for the supporting items. Reuses the
    shared seek contract.
    """
    episode = contract.get("episode") or {}
    sections = contract.get("sections") or {}

    title = escape_html(episode.get("title") or "研究简报")
    subtitle = escape_html(episode.get("subtitle") or "")
    estimated_sec = float(episode.get("estimated_duration_sec") or 30)
    total_time_str = format_timecode(estimated_sec)

    lead_card, support_cards = _split_lead_support(contract)
    d, total_dur = _stage_delays(contract)
    news_cards = sections.get("news_cards") or []
    news_count = len(news_cards)

    abstract = (
        '<div class="rb-abstract stage-layer" data-appear-at="' + str(d["mainCard"]) + '">'
        '<div class="rb-abstract-label">ABSTRACT · 核心要点</div>'
        '<div class="rb-abstract-text">' + escape_html((lead_card or {}).get("headline") or "") + '</div>'
        '</div>'
    )

    finding_delays = [d["support1"], d["support2"], d["support3"]]
    finding_rows = []
    for i, card in enumerate(support_cards[:3]):
        appear = finding_delays[i] if i < len(finding_delays) else d["supporting"] + i * 0.4
        finding_rows.append(
            '<div class="rb-finding stage-layer" data-appear-at="' + str(appear) + '">'
            '<span class="rb-finding-num">' + ("%02d" % (i + 2)) + '</span>'
            '<div class="rb-finding-body">'
            '<div class="rb-finding-text">' + escape_html(card.get("headline") or "") + '</div>'
            '<div class="rb-finding-meta">' + escape_html(card.get("source") or card.get("time_range") or "") + '</div>'
            '</div></div>'
        )
    findings_html = "".join(finding_rows)

    closing = sections.get("closing") or {}
    closing_html = (
        '<div class="rb-closing stage-layer" data-appear-at="' + str(d["closing"]) + '">'
        '<span class="rb-closing-tag">CONCLUSION</span>'
        '<span>' + escape_html(closing.get("title") or "") + '</span>'
        '</div>'
    )

    css_parts = [
        '*{box-sizing:border-box;margin:0;padding:0;}',
        '.video-stage-shell{width:100vw;height:100vh;background:#11151d;overflow:hidden;}',
        '.video-stage{position:relative;width:100%;height:100%;overflow:hidden;background:#11151d;'
        'display:flex;flex-direction:column;'
        "font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;}",
        '.rb-bg{position:absolute;inset:0;background-image:linear-gradient(rgba(251,191,36,.05) 1px,transparent 1px);'
        'background-size:100% 32px;}',
        '.rb-frame{position:absolute;inset:14px;border:1px solid #2a313d;border-radius:14px;pointer-events:none;}',
        # Header
        '.rb-header{position:relative;z-index:15;padding:5% 28px 12px;}',
        '.rb-kicker{display:flex;align-items:center;gap:8px;margin-bottom:10px;'
        'font-family:monospace;font-size:9px;letter-spacing:2px;color:#fbbf24;}',
        '.rb-kicker-line{flex:1;height:1px;background:#3a3320;}',
        '.rb-count{color:#5d6675;font-size:9px;font-family:monospace;}',
        '.rb-title{color:#f1f5f9;font-size:18px;font-weight:800;line-height:1.3;margin-bottom:4px;}',
        '.rb-subtitle{color:#8a93a3;font-size:10px;line-height:1.45;}',
        # Abstract
        '.rb-abstract{position:relative;z-index:12;margin:0 28px;'
        'border-left:3px solid #fbbf24;background:rgba(251,191,36,.06);border-radius:0 10px 10px 0;padding:12px 14px;}',
        '.rb-abstract-label{color:#fbbf24;font-size:9px;font-family:monospace;letter-spacing:1px;margin-bottom:6px;}',
        '.rb-abstract-text{color:#e8edf4;font-size:14px;font-weight:700;line-height:1.4;}',
        # Findings
        '.rb-findings{position:relative;z-index:12;margin:18px 28px 0;flex:1 1 auto;min-height:0;overflow:hidden;}',
        '.rb-findings-title{color:#8a93a3;font-size:9px;font-family:monospace;letter-spacing:2px;margin-bottom:12px;}',
        '.rb-finding{display:flex;gap:12px;padding:10px 0;border-top:1px solid #232a35;}',
        '.rb-finding-num{flex:0 0 auto;color:#fbbf24;font-size:13px;font-weight:800;font-family:monospace;}',
        '.rb-finding-text{color:#dbe2ec;font-size:12px;font-weight:600;line-height:1.4;'
        'display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;}',
        '.rb-finding-meta{color:#5d6675;font-size:9px;font-family:monospace;margin-top:3px;}',
        # Closing
        '.rb-closing{position:relative;z-index:14;margin:0 28px;'
        'display:flex;align-items:center;gap:8px;color:#dbe2ec;font-size:11px;font-weight:600;'
        'background:rgba(251,191,36,.08);border:1px solid #3a3320;border-radius:10px;padding:9px 12px;}',
        '.rb-closing-tag{color:#fbbf24;font-family:monospace;font-size:9px;font-weight:800;letter-spacing:1px;}',
        # Footer / progress
        '.rb-footer{position:relative;z-index:20;padding:12px 28px 16px;margin-top:auto;}',
        '.stage-progress-track{width:100%;height:3px;background:#232a35;border-radius:999px;overflow:hidden;}',
        '.stage-progress-fill{width:0%;height:100%;background:linear-gradient(90deg,#d97706,#fbbf24);'
        'border-radius:999px;animation:rbProgress ' + str(total_dur) + 's linear forwards;}',
        '@keyframes rbProgress{0%{width:0%;}100%{width:100%;}}',
        '.rb-abstract,.rb-finding,.rb-closing{opacity:0;animation:rbFadeIn .5s ease-out both;}',
        '.rb-header{opacity:0;animation:rbFadeIn .6s ' + str(d["title"]) + 's ease-out both;}',
        '@keyframes rbFadeIn{from{opacity:0;transform:translateY(8px);}to{opacity:1;transform:translateY(0);}}',
    ] + _seek_mode_css_rules()
    stage_css = "<style>\n" + "\n".join(css_parts) + "\n</style>\n"

    return (
        '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        f'<title>{title}</title>\n{stage_css}</head>\n<body>\n'
        '<div class="video-stage-shell">\n<div class="video-stage stage-9x16">\n'
        '<div class="rb-bg"></div>\n<div class="rb-frame"></div>\n'
        '<div class="rb-header stage-layer" data-appear-at="' + str(d["title"]) + '">'
        '<div class="rb-kicker">RESEARCH BRIEFING<span class="rb-kicker-line"></span>'
        f'<span class="rb-count">{news_count} ITEMS · {total_time_str}</span></div>'
        f'<div class="rb-title">{title}</div>'
        f'<div class="rb-subtitle">{subtitle}</div>'
        '</div>\n'
        f'{abstract}\n'
        '<div class="rb-findings">'
        '<div class="rb-findings-title stage-layer" data-appear-at="' + str(d["support1"]) + '">FINDINGS · 要点清单</div>'
        f'{findings_html}'
        '</div>\n'
        f'{closing_html}\n'
        '<div class="rb-footer stage-layer" data-appear-at="0">'
        '<div class="stage-progress-track"><div class="stage-progress-fill" data-progress-fill="true"></div></div>'
        '</div>\n'
        '</div>\n</div>\n'
        f'{_timing_shim(total_dur)}'
        '</body>\n</html>\n'
    )


# ---------------------------------------------------------------------------
# Style: illustrated_v1 (插画解说) — full-bleed AI illustration per scene
# ---------------------------------------------------------------------------

def _img_data_uri(path: Any) -> str:
    """Read a local image and return a base64 data URI (self-contained HTML)."""
    import base64
    try:
        raw = Path(str(path)).read_bytes()
        b64 = base64.b64encode(raw).decode("ascii")
        return "data:image/jpeg;base64," + b64
    except Exception:
        return ""


def render_illustrated_stage_episode_html(contract: dict) -> str:
    """Render a self-contained illustrated_v1 stage.

    Each news card becomes a full-bleed scene: an AI-generated illustration
    (base64-embedded) with a bottom gradient + headline + caption. Scenes are
    stacked and revealed in sequence via the shared seek contract — later scenes
    cover earlier ones, giving a narrated slideshow synced to the voiceover.
    Falls back to a colored placeholder when a card has no illustration.
    """
    episode = contract.get("episode") or {}
    sections = contract.get("sections") or {}

    title = escape_html(episode.get("title") or "今日要闻")
    subtitle = escape_html(episode.get("subtitle") or "")
    estimated_sec = float(episode.get("estimated_duration_sec") or 30)
    total_time_str = format_timecode(estimated_sec)

    d, total_dur = _stage_delays(contract)

    cards = [c for c in (sections.get("news_cards") or []) if isinstance(c, dict)]
    cards.sort(key=lambda c: c.get("order", 0))
    scene_delays = [d["mainCard"], d["support1"], d["support2"], d["support3"]]

    scenes = []
    for i, card in enumerate(cards[:4]):
        appear = scene_delays[i] if i < len(scene_delays) else d["supporting"] + i * 0.4
        data_uri = _img_data_uri(card.get("image_path")) if card.get("image_path") else ""
        bg = ("background-image:url(" + data_uri + ");") if data_uri else ""
        placeholder = "" if data_uri else " il-img-empty"
        is_lead = bool(card.get("is_lead")) or card.get("role") == "lead"
        badge = "★ 头条" if is_lead else ("要点 " + str(i + 1))
        caption = escape_html(card.get("narration") or card.get("description") or "")
        scenes.append(
            '<div class="il-scene stage-layer" data-appear-at="' + str(appear) + '" style="z-index:' + str(10 + i) + '">'
            '<div class="il-img' + placeholder + '" style="' + bg + '"></div>'
            '<div class="il-overlay"></div>'
            '<div class="il-text">'
            '<div class="il-badge">' + badge + '</div>'
            '<div class="il-headline">' + escape_html(card.get("headline") or "") + '</div>'
            '<div class="il-caption">' + caption + '</div>'
            '</div>'
            '</div>'
        )
    scenes_html = "".join(scenes)

    css_parts = [
        '*{box-sizing:border-box;margin:0;padding:0;}',
        '.video-stage-shell{width:100vw;height:100vh;background:#05060a;overflow:hidden;}',
        '.video-stage{position:relative;width:100%;height:100%;overflow:hidden;background:#05060a;'
        "font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;}",
        # Scene (full-bleed, stacked)
        '.il-scene{position:absolute;inset:0;}',
        '.il-img{position:absolute;inset:0;background-size:cover;background-position:center;'
        'animation:ilZoom ' + str(max(6.0, total_dur)) + 's ease-out both;}',
        '.il-img-empty{background:linear-gradient(135deg,#1e293b,#0b1220);}',
        '@keyframes ilZoom{from{transform:scale(1.08);}to{transform:scale(1);}}',
        '.il-overlay{position:absolute;inset:0;background:linear-gradient(0deg,'
        'rgba(5,6,10,.92) 0%,rgba(5,6,10,.55) 28%,rgba(5,6,10,0) 55%);}',
        '.il-text{position:absolute;left:0;right:0;bottom:0;padding:0 7% 9%;}',
        '.il-badge{display:inline-block;background:#6366f1;color:#fff;font-size:13px;font-weight:800;'
        'letter-spacing:1px;padding:4px 12px;border-radius:6px;margin-bottom:14px;}',
        '.il-headline{color:#fff;font-size:34px;font-weight:800;line-height:1.2;'
        'text-shadow:0 2px 14px rgba(0,0,0,.7);margin-bottom:14px;max-width:88%;}',
        '.il-caption{color:#e8ecf5;font-size:17px;line-height:1.55;max-width:80%;'
        'text-shadow:0 1px 8px rgba(0,0,0,.8);'
        'display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;}',
        # Persistent top bar
        '.il-topbar{position:absolute;top:0;left:0;right:0;z-index:30;padding:22px 7% 30px;'
        'background:linear-gradient(180deg,rgba(5,6,10,.85) 0%,rgba(5,6,10,0) 100%);}',
        '.il-kicker{display:inline-block;background:rgba(99,102,241,.25);border:1px solid #6366f1;'
        'color:#c7d2fe;font-size:11px;font-weight:700;letter-spacing:2px;padding:3px 10px;border-radius:999px;margin-bottom:8px;}',
        '.il-title{color:#fff;font-size:18px;font-weight:700;text-shadow:0 2px 10px rgba(0,0,0,.8);}',
        '.il-sub{color:#aab3c5;font-size:12px;margin-top:2px;}',
        # Progress
        '.il-footer{position:absolute;bottom:0;left:0;right:0;z-index:31;padding:0 7% 18px;}',
        '.stage-progress-track{width:100%;height:4px;background:rgba(255,255,255,.18);border-radius:999px;overflow:hidden;}',
        '.stage-progress-fill{width:0%;height:100%;background:linear-gradient(90deg,#6366f1,#a855f7);'
        'border-radius:999px;animation:ilProgress ' + str(total_dur) + 's linear forwards;}',
        '@keyframes ilProgress{0%{width:0%;}100%{width:100%;}}',
        # Live (non-seek) entrance
        '.il-scene{opacity:0;animation:ilFade .6s ease-out both;}',
        '@keyframes ilFade{from{opacity:0;}to{opacity:1;}}',
    ] + _seek_mode_css_rules()
    stage_css = "<style>\n" + "\n".join(css_parts) + "\n</style>\n"

    news_count = len(cards)
    return (
        '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        f'<title>{title}</title>\n{stage_css}</head>\n<body>\n'
        '<div class="video-stage-shell">\n<div class="video-stage stage-16x9">\n'
        f'{scenes_html}\n'
        '<div class="il-topbar stage-layer" data-appear-at="' + str(d["title"]) + '">'
        f'<div class="il-kicker">AI 新闻解说 · {news_count} 段 · {total_time_str}</div>'
        f'<div class="il-title">{title}</div>'
        f'<div class="il-sub">{subtitle}</div>'
        '</div>\n'
        '<div class="il-footer stage-layer" data-appear-at="0">'
        '<div class="stage-progress-track"><div class="stage-progress-fill" data-progress-fill="true"></div></div>'
        '</div>\n'
        '</div>\n</div>\n'
        f'{_timing_shim(total_dur)}'
        '</body>\n</html>\n'
    )


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------

# Registry of style_id -> renderer function. Adding an entry here makes a style
# exportable; episode_export.ALLOWED_STYLE_IDS must list the same id.
EPISODE_STYLE_RENDERERS = {
    "breaking_news_v1": render_breaking_news_stage_episode_html,
    "timeline_daily_v1": render_timeline_daily_stage_episode_html,
    "data_dashboard_v1": render_data_dashboard_stage_episode_html,
    "podcast_cards_v1": render_podcast_cards_stage_episode_html,
    "research_briefing_v1": render_research_briefing_stage_episode_html,
    "illustrated_v1": render_illustrated_stage_episode_html,
}


def render_episode_stage_html(contract: dict, style_id: str = "breaking_news_v1") -> str:
    """Render an episode stage HTML document for a supported style.

    Args:
        contract: episode_template_v1 contract dict.
        style_id: Style identifier present in EPISODE_STYLE_RENDERERS.

    Returns:
        Complete HTML string.
    """
    renderer = EPISODE_STYLE_RENDERERS.get(style_id)
    if renderer is None:
        raise ValueError(
            f"Unsupported style_id {style_id!r}. "
            f"Supported: {', '.join(sorted(EPISODE_STYLE_RENDERERS))}"
        )
    return renderer(contract)


def render_episode_stage_html_to_file(
    contract: dict,
    output_path: str | Path,
    style_id: str = "breaking_news_v1",
) -> Path:
    """Render an episode stage HTML document and write it to a file.

    Args:
        contract: episode_template_v1 contract dict.
        output_path: Destination file path.
        style_id: Style identifier. Only ``"breaking_news_v1"`` is supported.

    Returns:
        The resolved Path to the written file.
    """
    html_content = render_episode_stage_html(contract, style_id)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html_content)
    return out.resolve()
