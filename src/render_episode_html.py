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
        # Shell
        '.video-stage-shell{width:100%;min-height:100vh;display:flex;align-items:center;'
        'justify-content:center;background:#050505;padding:24px;}',
        # Stage
        '.video-stage{position:relative;width:min(420px,92vw);aspect-ratio:9/16;overflow:hidden;'
        'border-radius:24px;background:#0a0000;box-shadow:0 24px 80px rgba(0,0,0,.55);}',
        # Bg
        '.stage-bg{position:absolute;inset:0;background:linear-gradient(160deg,#1a0000 0%,#0a0000 40%,#120000 100%);'
        'animation:stageBgPulse 6s ease-in-out infinite;}',
        '@keyframes stageBgPulse{0%,100%{opacity:1;}50%{opacity:.85;}}',
        # Topbar
        '.stage-topbar{position:absolute;top:0;left:0;right:0;z-index:20;display:flex;align-items:center;'
        'justify-content:space-between;padding:10px 16px;background:linear-gradient(180deg,rgba(0,0,0,.7) 0%,transparent 100%);}',
        '.stage-breaking-badge{background:#dc2626;color:#fff;font-size:10px;font-weight:900;'
        'letter-spacing:2px;padding:3px 10px;border-radius:4px;animation:breakingBlink 2s ease-in-out infinite;}',
        '@keyframes breakingBlink{0%,100%{opacity:1;}50%{opacity:.7;}}',
        '.stage-meta{color:#f87171;font-size:9px;font-family:monospace;}',
        # Title area
        '.stage-title-area{position:absolute;top:44px;left:0;right:0;z-index:15;padding:0 16px 12px;'
        'background:linear-gradient(180deg,transparent 0%,rgba(0,0,0,.3) 100%);}',
        '.stage-episode-title{color:#fff;font-size:14px;font-weight:800;line-height:1.3;'
        'text-shadow:0 2px 8px rgba(0,0,0,.8);margin-bottom:4px;}',
        '.stage-episode-subtitle{color:#fca5a5;font-size:10px;opacity:.9;line-height:1.3;}',
        # Main card
        '.stage-main-card{position:absolute;top:128px;left:100px;right:14px;z-index:12;'
        'background:rgba(20,0,0,.88);border:1px solid #dc2626;border-radius:14px;padding:16px;'
        'animation:cardEnter 0.5s ease-out both;}',
        '@keyframes cardEnter{from{opacity:0;transform:translateY(12px);}to{opacity:1;transform:translateY(0);}}',
        '.stage-lead-badge{display:inline-block;background:#dc2626;color:#fff;font-size:9px;font-weight:900;'
        'letter-spacing:1px;padding:2px 8px;border-radius:3px;margin-bottom:8px;}',
        '.stage-lead-headline{color:#fff;font-size:15px;font-weight:800;line-height:1.35;'
        'margin-bottom:8px;text-shadow:0 1px 4px rgba(0,0,0,.6);}',
        '.stage-lead-meta{display:flex;gap:8px;font-size:9px;color:#fca5a5;font-family:monospace;}',
        # Supporting
        '.stage-supporting{position:absolute;bottom:120px;right:14px;z-index:12;width:130px;'
        'display:flex;flex-direction:column;gap:6px;}',
        '.stage-support-card{background:rgba(15,0,0,.82);border:1px solid #7f1d1d;'
        'border-radius:8px;padding:8px 10px;}',
        '.stage-support-headline{color:#fecaca;font-size:10px;font-weight:600;line-height:1.3;'
        'display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;}',
        '.stage-support-meta{color:#f87171;font-size:8px;font-family:monospace;margin-top:4px;}',
        # Subtitle bar
        '.stage-subtitle-bar{position:absolute;bottom:70px;left:14px;right:14px;z-index:14;'
        'background:rgba(0,0,0,.75);border-radius:8px;padding:8px 12px;}',
        '.stage-subtitle-text{color:#f9f9f9;font-size:11px;line-height:1.4;'
        'display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;}',
        # Timeline
        '.stage-timeline{position:absolute;bottom:0;left:0;right:0;z-index:20;'
        'padding:10px 16px;background:linear-gradient(0deg,rgba(0,0,0,.8) 0%,transparent 100%);}',
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
        '.stage-anchor-enter{position:absolute;left:8px;bottom:112px;width:86px;height:130px;'
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
        '.stage-progress-wrap{position:absolute;bottom:6px;left:16px;right:16px;z-index:25;height:4px;}',
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
        '<div class="video-stage stage-9x16">\n'
        '<div class="stage-bg"></div>\n'
        # Topbar
        '<div class="stage-topbar stage-layer" data-appear-at="' + str(d["topbar"]) + '">'
        '<span class="stage-breaking-badge">🔴 BREAKING NEWS</span>'
        f'<span class="stage-meta">{news_count} 条 · {total_time_str}</span>'
        '</div>\n'
        # Shot label
        '<div class="stage-shot-label stage-layer" data-appear-at="' + str(d["shotLabel"]) + '">'
        'SHOT FLOW · 开场 → 主持人 → 主新闻 → 快讯 → 结尾</div>\n'
        # Recap
        f'{recap_html}\n'
        # Opening label
        f'{opening_label_html}\n'
        # Title area
        '<div class="stage-title-area stage-layer" data-appear-at="' + str(d["title"]) + '">'
        f'<div class="stage-episode-title">{escape_html(episode.get("title") or "")}</div>'
        f'<div class="stage-episode-subtitle">{escape_html(episode.get("subtitle") or "")}</div>'
        '</div>\n'
        # Lead card
        f'{lead_html}\n'
        # Supporting cards
        f'{support_html}\n'
        # Subtitle bar
        f'{subtitle_bar_html}\n'
        # Anchor
        f'{anchor_layer_html}\n'
        # Closing
        f'{closing_html}\n'
        # Timeline
        f'{timeline_html}\n'
        # Progress bar (always visible, data-appear-at=0)
        '<div class="stage-progress-wrap stage-layer" data-appear-at="0">'
        '<div class="stage-progress-track">'
        '<div class="stage-progress-fill" data-progress-fill="true"></div>'
        '</div>'
        '</div>\n'
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
# Public entry points
# ---------------------------------------------------------------------------

def render_episode_stage_html(contract: dict, style_id: str = "breaking_news_v1") -> str:
    """Render an episode stage HTML document.

    Args:
        contract: episode_template_v1 contract dict.
        style_id: Style identifier. Only ``"breaking_news_v1"`` is supported in CP40.0.

    Returns:
        Complete HTML string.
    """
    if style_id != "breaking_news_v1":
        raise ValueError(
            "Only breaking_news_v1 is supported by CP40.0. "
            f"Got: {style_id!r}"
        )
    return render_breaking_news_stage_episode_html(contract)


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
