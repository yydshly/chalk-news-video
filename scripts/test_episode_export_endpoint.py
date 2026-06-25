#!/usr/bin/env python3
"""CP40.3: Endpoint test for async POST /api/episode/export + status polling.

This is a prototype test — it creates real MP4 artifacts.
Run manually to validate the async job flow.
"""

from __future__ import annotations

import sys
import time
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


def test_async_episode_export() -> None:
    print("[test] POST /api/episode/export (async)")

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

    # Must return 202 Accepted
    assert resp.status_code == 202, f"Expected 202, got {resp.status_code}"

    export_id = data.get("export_id")
    assert export_id, "export_id missing"
    assert export_id.startswith("episode_export_"), f"Bad export_id format: {export_id}"

    # Verify metadata in POST response (CP40.3.1)
    assert data.get("width") == 720, f"POST response width should be 720, got {data.get('width')}"
    assert data.get("height") == 1280, f"POST response height should be 1280, got {data.get('height')}"
    assert data.get("fps") == 30, f"POST response fps should be 30, got {data.get('fps')}"

    status_url = data.get("status_url")
    assert status_url, "status_url missing"
    assert f"/api/episode/exports/{export_id}" == status_url, \
        f"status_url mismatch: expected /api/episode/exports/{export_id}, got {status_url}"

    mp4_url = data.get("mp4_url")
    assert mp4_url, "mp4_url missing"

    # Poll status until completed or failed
    print(f"[test] Polling status for {export_id} …")
    max_polls = 120
    final_status = None
    final_data = None
    for i in range(max_polls):
        time.sleep(1)
        r = client.get(f"/api/episode/exports/{export_id}")
        assert r.status_code == 200, f"Status GET failed: {r.status_code}"
        status_data = r.json()
        current_status = status_data.get("status")
        progress = status_data.get("progress", 0)
        message = status_data.get("message", "")
        print(f"  poll {i+1:3d}: status={current_status}, progress={progress}, message={message}")

        # CP40.3.1: verify metadata persists in every status response
        assert status_data.get("style_id") == "breaking_news_v1", \
            f"[poll {i+1}] style_id missing or wrong: {status_data.get('style_id')}"
        assert status_data.get("width") == 720, \
            f"[poll {i+1}] width should be 720, got {status_data.get('width')}"
        assert status_data.get("height") == 1280, \
            f"[poll {i+1}] height should be 1280, got {status_data.get('height')}"
        assert status_data.get("fps") == 30, \
            f"[poll {i+1}] fps should be 30, got {status_data.get('fps')}"

        if current_status in ("completed", "failed"):
            final_status = current_status
            final_data = status_data
            break
    else:
        raise AssertionError(f"Export did not complete after {max_polls} polls")

    assert final_status == "completed", \
        f"Expected completed, got {final_status}: {final_data}"

    # CP40.3.1: final completed status also preserves metadata
    assert final_data.get("style_id") == "breaking_news_v1"
    assert final_data.get("width") == 720
    assert final_data.get("height") == 1280
    assert final_data.get("fps") == 30

    result = final_data.get("result")
    assert result is not None, "result missing in completed status"

    # Verify result URLs
    assert result.get("mp4_url"), "mp4_url missing in result"
    assert result.get("html_url"), "html_url missing in result"
    assert result.get("meta_url"), "meta_url missing in result"
    assert result.get("contract_url"), "contract_url missing in result"

    # Verify file serving
    mp4_resp = client.get(mp4_url)
    assert mp4_resp.status_code == 200, f"MP4 serve failed: {mp4_resp.status_code}"
    assert mp4_resp.headers.get("content-type") == "video/mp4"

    html_url = data.get("html_url")
    html_resp = client.get(html_url)
    assert html_resp.status_code == 200, f"HTML serve failed: {html_resp.status_code}"

    meta_url = data.get("meta_url")
    meta_resp = client.get(meta_url)
    assert meta_resp.status_code == 200, f"Meta serve failed: {meta_resp.status_code}"

    contract_url = data.get("contract_url")
    contract_resp = client.get(contract_url)
    assert contract_resp.status_code == 200, f"Contract serve failed: {contract_resp.status_code}"

    # Verify status.json is served
    status_url_full = f"/outputs/episode_exports/{export_id}/status.json"
    status_file_resp = client.get(status_url_full)
    assert status_file_resp.status_code == 200, f"status.json serve failed: {status_file_resp.status_code}"
    assert status_file_resp.headers.get("content-type") == "application/json"

    # Verify export_meta.json matches status result
    meta_json = meta_resp.json()
    assert meta_json.get("status") == "completed"
    assert meta_json.get("width") == 720
    assert meta_json.get("height") == 1280
    assert meta_json.get("fps") == 30

    print(f"[test] All checks PASSED — export {export_id} completed successfully")


if __name__ == "__main__":
    test_async_episode_export()
