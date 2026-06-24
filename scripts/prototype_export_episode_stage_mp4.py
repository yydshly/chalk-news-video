#!/usr/bin/env python3
"""CP40.1: Minimal Episode Stage MP4 Export Prototype.

This is a local prototype script only — NOT a formal API endpoint.
It validates the end-to-end export pipeline:
  1. Build mock episode_template_v1 contract
  2. Render HTML via render_episode_stage_html_to_file()
  3. Export to MP4 via export_video() with 720x1280 viewport

No real LLM, no real TTS, no audio, no /api/jobs.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from render_episode_html import render_episode_stage_html_to_file
from export_video import export_video


def build_mock_episode_contract() -> dict:
    """Return a minimal episode_template_v1 contract for prototype validation."""
    return {
        "schema_version": "episode_template_v1",
        "template_id": "breaking_news_v1",
        "episode": {
            "title": "今日 AI 前沿速览",
            "subtitle": "三条值得关注的 AI 新闻",
            "theme_name": "AI News",
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
                "title": "今天我们快速看几条值得关注的 AI 新闻"
            },
            "news_cards": [
                {
                    "section_id": "segment_001",
                    "order": 1,
                    "role": "lead",
                    "headline": "OpenAI 发布新的模型能力更新",
                    "layout": "breaking_news",
                    "emphasis": "hot",
                    "badges": ["AI", "模型"],
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
                    "headline": "Anthropic 更新企业级 AI 安全能力",
                    "layout": "news_card",
                    "emphasis": "",
                    "badges": ["AI"],
                    "audio_clip_count": 1,
                    "time_range": "00:09-00:12",
                    "duration_hint_sec": 3,
                    "is_lead": False,
                    "section_type": "news_segment",
                },
                {
                    "section_id": "segment_003",
                    "order": 3,
                    "role": "supporting",
                    "headline": "AI 基准测试刷新多项指标",
                    "layout": "news_card",
                    "emphasis": "",
                    "badges": ["Benchmark"],
                    "audio_clip_count": 1,
                    "time_range": "00:12-00:14",
                    "duration_hint_sec": 2,
                    "is_lead": False,
                    "section_type": "news_segment",
                },
            ],
            "closing": {
                "title": "今天最值得关注的是模型能力的持续迭代",
                "focus_news_id": "segment_001",
            },
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="CP40.1: Export episode stage HTML to MP4")
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / ".tmp" / "cp40_1_episode_stage.mp4",
        help="Output MP4 path (default: .tmp/cp40_1_episode_stage.mp4)",
    )
    args = parser.parse_args()

    out_path = args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # HTML intermediate goes alongside the MP4
    html_path = out_path.parent / (out_path.stem + ".html")

    contract = build_mock_episode_contract()

    print("[CP40.1] Step 1: Render HTML …")
    render_episode_stage_html_to_file(contract, html_path)
    print(f"[CP40.1] HTML written → {html_path}")

    print("[CP40.1] Step 2: Export MP4 (720×1280, 30fps, no audio) …")
    try:
        result = export_video(
            html_path=str(html_path),
            output_path=str(out_path),
            fps=30,
            width=720,
            height=1280,
            headless=True,
            audio_path=None,
        )
        print(f"[CP40.1] MP4 written → {result}")
        if result.exists():
            size = result.stat().st_size
            print(f"[CP40.1] MP4 exists: True")
            print(f"[CP40.1] MP4 size bytes: {size:,}")
        else:
            print("[CP40.1] MP4 exists: False — export returned path but file missing")
    except Exception as exc:
        print(f"[CP40.1] Export FAILED: {exc}")
        raise


if __name__ == "__main__":
    main()
