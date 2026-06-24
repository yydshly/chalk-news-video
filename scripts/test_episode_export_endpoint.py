#!/usr/bin/env python3
"""CP40.2: Endpoint test for POST /api/episode/export.

This is a prototype test — it creates real MP4 artifacts.
Run manually to validate the endpoint.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fastapi.testclient import TestClient

from server import app

client = TestClient(app)


def build_mock_episode_contract() -> dict:
    """Return a minimal episode_template_v1 contract for testing."""
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


def test_episode_export() -> None:
    print("[test] POST /api/episode/export")

    resp = client.post("/api/episode/export", json={
        "contract": build_mock_episode_contract(),
        "style_id": "breaking_news_v1",
        "width": 720,
        "height": 1280,
        "fps": 30,
    })

    print(f"[test] status_code={resp.status_code}")
    data = resp.json()
    print(f"[test] response={data}")

    # Assertions
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert data.get("status") == "completed", f"Expected status=completed, got {data}"

    export_id = data.get("export_id")
    assert export_id, "export_id missing"

    mp4_url = data.get("mp4_url")
    assert mp4_url, "mp4_url missing"
    assert mp4_url.endswith("/output.mp4"), f"mp4_url should end with /output.mp4: {mp4_url}"

    mp4_path_str = data.get("mp4_path")
    assert mp4_path_str, "mp4_path missing"
    mp4_path = Path(mp4_path_str)
    assert mp4_path.exists(), f"MP4 file does not exist: {mp4_path}"
    assert mp4_path.stat().st_size > 0, "MP4 file is empty"

    assert data.get("width") == 720, f"Expected width=720, got {data.get('width')}"
    assert data.get("height") == 1280, f"Expected height=1280, got {data.get('height')}"
    assert data.get("fps") == 30, f"Expected fps=30, got {data.get('fps')}"

    # Test static file serving
    static_resp = client.get(mp4_url)
    assert static_resp.status_code == 200, f"Static file serve failed: {static_resp.status_code}"
    assert static_resp.headers.get("content-type") == "video/mp4", f"Wrong content-type: {static_resp.headers.get('content-type')}"

    html_url = data.get("html_url")
    html_resp = client.get(html_url)
    assert html_resp.status_code == 200, f"HTML serve failed: {html_resp.status_code}"

    meta_url = data.get("meta_url")
    meta_resp = client.get(meta_url)
    assert meta_resp.status_code == 200, f"Meta serve failed: {meta_resp.status_code}"
    meta_data = meta_resp.json()
    assert meta_data.get("status") == "completed", "meta status should be completed"

    print("[test] All checks PASSED")


if __name__ == "__main__":
    test_episode_export()
