#!/usr/bin/env python3
"""CP40.0 smoke test: verify the Python episode stage HTML generator produces valid output.

Run from the project root:
    python scripts/smoke_test_render_episode_html.py

No outputs are written to the project directory. Temp files go to the system temp dir.
"""

import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from render_episode_html import (
    render_episode_stage_html,
    render_episode_stage_html_to_file,
    escape_html,
    format_timecode,
    build_breaking_news_shot_timeline,
    build_breaking_news_stage_timing,
    infer_episode_anchor_cue,
    render_cartoon_anchor_svg,
)


# ---- Minimal mock contract ----
MOCK_CONTRACT = {
    "schema_version": "episode_template_v1",
    "template_id": "breaking_news_v1",
    "episode": {
        "title": "今日 AI 前沿速览",
        "subtitle": "多条热门 AI 新闻合集",
        "theme_name": "突发新闻快讯",
        "estimated_duration_sec": 14,
        "news_count": 3,
        "lead_count": 1,
    },
    "timeline": {
        "markers": [
            {"type": "opening", "label": "开场", "timecode": "00:00"},
            {"type": "news_segment", "role": "lead", "label": "主新闻", "timecode": "00:03"},
            {"type": "news_segment", "role": "supporting", "label": "补充", "timecode": "00:07"},
            {"type": "closing", "label": "结尾", "timecode": "00:11"},
        ]
    },
    "sections": {
        "opening": {
            "title": "今天我们快速看几条值得关注的 AI 新闻",
        },
        "news_cards": [
            {
                "section_id": "segment_001",
                "order": 1,
                "role": "lead",
                "headline": "OpenAI 发布 GPT-5.5 重大更新",
                "layout": "breaking_news",
                "emphasis": "hot",
                "badges": ["AI", "热门"],
                "audio_clip_count": 1,
                "time_range": "00:03-00:09",
                "duration_hint_sec": 6,
                "is_lead": True,
                "section_type": "news_segment",
            },
            {
                "section_id": "segment_002",
                "order": 2,
                "role": "supporting",
                "headline": "Anthropic 发布 Claude 4 系列",
                "layout": "news_card",
                "emphasis": "",
                "badges": ["AI"],
                "audio_clip_count": 1,
                "time_range": "00:09-00:12",
                "duration_hint_sec": 3,
                "is_lead": False,
                "section_type": "news_segment",
            },
        ],
        "closing": {
            "title": "最值得关注的是 GPT-5.5 更新",
            "focus_news_id": "segment_001",
        },
    },
}


def check(condition: bool, msg: str) -> None:
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {msg}")
    if not condition:
        global failures
        failures += 1


failures = 0


def main() -> None:
    print("CP40.0 smoke test: render_episode_html")
    print("=" * 50)

    # 1. Helpers
    print("\n[Helpers]")
    check(escape_html("<test>&") == "&lt;test&gt;&amp;", "escape_html")
    check(format_timecode(90) == "01:30", "format_timecode 90s")
    check(format_timecode(None) == "00:00", "format_timecode None")
    check(format_timecode(0) == "00:00", "format_timecode 0")

    # 2. Shot timeline
    print("\n[Shot timeline]")
    timeline = build_breaking_news_shot_timeline(MOCK_CONTRACT)
    check(len(timeline) == 5, f"shot timeline has 5 shots (got {len(timeline)})")
    check(timeline[0]["shot_id"] == "opening", "first shot is opening")
    check(timeline[-1]["shot_id"] == "closing", "last shot is closing")

    # 3. Stage timing
    print("\n[Stage timing]")
    timing = build_breaking_news_stage_timing(MOCK_CONTRACT)
    check(isinstance(timing, dict), "timing is a dict")
    check("delays" in timing, "timing has delays")
    check("shotTimeline" in timing, "timing has shotTimeline")
    check("totalDurationSec" in timing, "timing has totalDurationSec")
    delays = timing["delays"]
    check("topbar" in delays, "delays has topbar")
    check("anchor" in delays, "delays has anchor")
    check("mainCard" in delays, "delays has mainCard")

    # 4. Anchor inference
    print("\n[Anchor inference]")
    cue = infer_episode_anchor_cue(MOCK_CONTRACT)
    check(isinstance(cue, dict), "anchor_cue is a dict")
    check("expression" in cue, "cue has expression")
    check("action" in cue, "cue has action")
    check(cue["role"] == "anchor", "cue role is anchor")

    # 5. Anchor SVG
    print("\n[Anchor SVG]")
    svg = render_cartoon_anchor_svg(cue)
    check("<svg" in svg, "SVG starts with <svg")
    check("cartoon-anchor-svg" in svg, "SVG has cartoon-anchor-svg class")
    check("<path" in svg, "SVG has path elements")

    # 6. Full HTML render
    print("\n[Full HTML render]")
    html = render_episode_stage_html(MOCK_CONTRACT, style_id="breaking_news_v1")
    checks = [
        ("<!DOCTYPE html>" in html, "DOCTYPE present"),
        ("<html lang=" in html, "html lang attribute"),
        ("video-stage stage-16x9" in html, "video-stage stage-16x9 class (CP60 16:9)"),
        ("cartoon-anchor-svg" in html, "cartoon-anchor-svg in output"),
        ("stage-shot-meta" in html, "stage-shot-meta present"),
        ("window.__getTotalDuration__" in html, "window.__getTotalDuration__ shim"),
        ("window.__setTime__" in html, "window.__setTime__ shim"),
        ("window.__ANIMATION_READY__" in html, "window.__ANIMATION_READY__ set"),
        ("window.__prepareSeekMode__" in html, "window.__prepareSeekMode__ shim"),
        ("data-export-seek" in html, "data-export-seek attribute in seek CSS"),
        ("mock-news-card" in html, "mock-news-card present"),
        ('data-section-type="news_segment"' in html, "data-section-type=news_segment"),
        ("tl-rail" in html, "tl-rail timeline rail"),
        ("tl-time" in html, "tl-time timecode markers"),
        ("stage-main-row" in html, "stage-main-row (CP60 16:9 flex layout)"),
        ("stage-anchor-col" in html, "stage-anchor-col (CP60 16:9 anchor column)"),
        ("stage-anchor-enter" in html, "stage-anchor-enter present"),
        ("stage-anchor-layer" in html, "stage-anchor-layer present"),
        ("stage-main-card" in html, "stage-main-card present"),
        ("stage-supporting" in html, "stage-supporting present"),
        ("stage-subtitle-bar" in html, "stage-subtitle-bar present"),
        ("stage-closing-chip" in html, "stage-closing-chip present"),
        ("stage-timeline" in html, "stage-timeline present"),
        ("stage-progress-wrap" in html, "stage-progress-wrap present"),
        ("data-progress-fill" in html, "data-progress-fill on progress bar"),
        ("stage-shot-label" in html, "stage-shot-label present"),
        ("stage-bg" in html, "stage-bg present"),
        ("stage-topbar" in html, "stage-topbar present"),
        ("stage-title-area" in html, "stage-title-area present"),
        ("🔴 BREAKING NEWS" in html, "BREAKING NEWS badge"),
        ("今日 AI 前沿速览" in html, "episode title rendered"),
        ("data-appear-at" in html, "data-appear-at attributes added"),
        ("is-visible" in html, "is-visible CSS class present"),
        # Seek-shim wiring checks
        ("stage-layer" in html, "stage-layer CSS class used on elements"),
        ("data-appear-at" in html, "data-appear-at on seekable elements"),
        ("data-export-seek" in html, "data-export-seek seek-mode CSS present"),
    ]
    for condition, msg in checks:
        check(condition, msg)

    # 6b. timeline_daily_v1 style (CP58) — second exportable style
    print("\n[timeline_daily_v1 render]")
    td = render_episode_stage_html(MOCK_CONTRACT, style_id="timeline_daily_v1")
    td_checks = [
        ("<!DOCTYPE html>" in td, "DOCTYPE present"),
        ("video-stage stage-9x16" in td, "video-stage stage-9x16 class"),
        ("window.__getTotalDuration__" in td, "__getTotalDuration__ shim"),
        ("window.__setTime__" in td, "__setTime__ shim"),
        ("window.__ANIMATION_READY__" in td, "__ANIMATION_READY__ set"),
        ("data-export-seek" in td, "seek-mode CSS present"),
        ("data-appear-at" in td, "data-appear-at on seekable layers"),
        ("stage-layer" in td, "stage-layer class used"),
        ("data-progress-fill" in td, "data-progress-fill on progress bar"),
        ("td-item-lead" in td, "lead timeline item present"),
        ("今日 AI 速览" in td, "daily-brief kicker present"),
        ("🔴 BREAKING NEWS" not in td, "no breaking-news badge (distinct style)"),
    ]
    for condition, msg in td_checks:
        check(condition, msg)

    # 6c. data_dashboard_v1 style (CP58) — third exportable style
    print("\n[data_dashboard_v1 render]")
    dd = render_episode_stage_html(MOCK_CONTRACT, style_id="data_dashboard_v1")
    dd_checks = [
        ("<!DOCTYPE html>" in dd, "DOCTYPE present"),
        ("video-stage stage-9x16" in dd, "video-stage stage-9x16 class"),
        ("window.__setTime__" in dd, "__setTime__ shim"),
        ("window.__getTotalDuration__" in dd, "__getTotalDuration__ shim"),
        ("data-export-seek" in dd, "seek-mode CSS present"),
        ("data-appear-at" in dd, "data-appear-at on seekable layers"),
        ("data-progress-fill" in dd, "data-progress-fill on progress bar"),
        ("dd-bar-fill" in dd, "bar chart fills present"),
        ("dd-bar-lead" in dd, "lead bar highlighted"),
        ("LIVE 数据简报" in dd, "dashboard LIVE kicker present"),
        ("各条目时长分布" in dd, "bar chart title present"),
    ]
    for condition, msg in dd_checks:
        check(condition, msg)

    # 6d. podcast_cards_v1 + research_briefing_v1 (CP58) — final two exportable styles
    for sid, marker, marker_desc in [
        ("podcast_cards_v1", "🎙 PODCAST", "podcast kicker"),
        ("research_briefing_v1", "RESEARCH BRIEFING", "research kicker"),
    ]:
        print(f"\n[{sid} render]")
        out = render_episode_stage_html(MOCK_CONTRACT, style_id=sid)
        for condition, msg in [
            ("<!DOCTYPE html>" in out, "DOCTYPE present"),
            ("video-stage stage-9x16" in out, "video-stage stage-9x16 class"),
            ("window.__setTime__" in out, "__setTime__ shim"),
            ("window.__getTotalDuration__" in out, "__getTotalDuration__ shim"),
            ("data-export-seek" in out, "seek-mode CSS present"),
            ("data-appear-at" in out, "data-appear-at on seekable layers"),
            ("data-progress-fill" in out, "data-progress-fill on progress bar"),
            (marker in out, marker_desc + " present"),
        ]:
            check(condition, msg)

    # 7. Write to temp file
    print("\n[File output]")
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
        tmp_path = Path(f.name)

    try:
        out = render_episode_stage_html_to_file(MOCK_CONTRACT, tmp_path, style_id="breaking_news_v1")
        check(out.exists(), f"file written to {out}")
        content = out.read_text(encoding="utf-8")
        check(len(content) > 1000, f"file size > 1KB (got {len(content)})")
        check("video-stage stage-16x9" in content, "file contains stage class")
    finally:
        tmp_path.unlink(missing_ok=True)

    # 8. Style guard — an id with no renderer must raise
    print("\n[Style guard]")
    try:
        render_episode_stage_html(MOCK_CONTRACT, style_id="nonexistent_style_v1")
        check(False, "should have raised ValueError for unsupported style")
    except ValueError as e:
        check("breaking_news_v1" in str(e), "ValueError lists supported styles")

    # 9. Security: no external URLs / scripts
    print("\n[Security checks]")
    check("http://" not in html.lower() or "127.0.0.1" in html, "no external http URLs")
    check("https://" not in html.lower(), "no external https URLs")
    check("api_key" not in html.lower(), "no api_key in output")
    check("voice_id" not in html.lower(), "no voice_id in output")
    check("<script" in html, "timing shim <script> present (expected for export HTML)")
    check("src=" not in html or "data:" in html, "no external script src attributes")

    print()
    if failures == 0:
        print("All checks passed.")
        return 0
    else:
        print(f"{failures} check(s) FAILED.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
