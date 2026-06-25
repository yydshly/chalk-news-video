#!/usr/bin/env python3
"""CP40.8: Episode Export E2E Regression Suite.

Covers all CP40.2–CP40.7.1 episode export functionality:
- GET /api/episode/export/capabilities
- invalid style_id guard
- invalid audio_url security validation
- async export without audio
- async export with audio (silence WAV)
- ffprobe audio stream verification (when available)
- status completed
- export_meta.json metadata
- status.json/result
- output.mp4 file serving
- history list
- delete export
- cleanup endpoint (dry_run)
- pending status delete protection
- invalid export_id handling

No real LLM, no real TTS, no /api/jobs, no Remotion.
"""

from __future__ import annotations

import shutil
import struct
import subprocess
import sys
import time
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fastapi.testclient import TestClient

from server import app

client = TestClient(app)

# ---------------------------------------------------------------------------
# Test constants
# ---------------------------------------------------------------------------

TEST_AUDIO_DIR = ROOT / "outputs" / "test_audio"
TEST_AUDIO_WAV = TEST_AUDIO_DIR / "cp40_8_silence.wav"
TEST_AUDIO_URL = "/outputs/test_audio/cp40_8_silence.wav"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_silence_wav(path: Path, duration_sec: float = 1.0, sample_rate: int = 16000) -> None:
    """Generate a controlled silence WAV for testing."""
    path.parent.mkdir(parents=True, exist_ok=True)
    n_frames = int(duration_sec * sample_rate)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        silence_frame = struct.pack("<h", 0)
        wf.writeframes(silence_frame * n_frames)


def cleanup_test_audio() -> None:
    """Remove test audio directory if it exists."""
    if TEST_AUDIO_DIR.exists():
        shutil.rmtree(TEST_AUDIO_DIR)


def has_audio_stream(mp4_path: Path) -> bool:
    """Check if MP4 contains an audio stream using ffprobe.

    Returns True if audio stream found.
    Raises AssertionError if ffprobe is installed but no audio stream found.
    Returns False if ffprobe is not installed (caller should SKIP stream check).
    """
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return False

    result = subprocess.run(
        [
            ffprobe,
            "-v", "error",
            "-select_streams", "a",
            "-show_entries", "stream=codec_type",
            "-of", "csv=p=0",
            str(mp4_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if "audio" in result.stdout.lower():
        return True
    raise AssertionError(
        f"Expected audio stream in {mp4_path}, but ffprobe found none.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


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


def start_export(contract: dict, audio_url: str | None = None, style_id: str = "breaking_news_v1") -> str:
    """Start an async episode export and return the export_id."""
    body = {
        "contract": contract,
        "style_id": style_id,
        "width": 720,
        "height": 1280,
        "fps": 30,
    }
    if audio_url is not None:
        body["audio_url"] = audio_url

    resp = client.post("/api/episode/export", json=body)
    assert resp.status_code == 202, f"Expected 202, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["export_id"].startswith("episode_export_"), f"Bad export_id: {data.get('export_id')}"
    return data["export_id"]


def wait_completed(export_id: str, max_polls: int = 120) -> dict:
    """Poll until export is completed or failed. Returns final status data."""
    for i in range(max_polls):
        time.sleep(1)
        resp = client.get(f"/api/episode/exports/{export_id}")
        assert resp.status_code == 200, f"Status GET failed: {resp.status_code}"
        data = resp.json()
        status = data.get("status")
        progress = data.get("progress", 0)
        print(f"  poll {i + 1:03d}: {export_id} status={status} progress={progress}")
        if status == "completed":
            return data
        if status == "failed":
            raise AssertionError(f"Export failed: {data.get('error_message', data)}")
    raise AssertionError(f"Export did not complete after {max_polls} polls: {export_id}")


# ---------------------------------------------------------------------------
# Test phases
# ---------------------------------------------------------------------------

def test_capabilities() -> None:
    """Test GET /api/episode/export/capabilities returns correct structure."""
    resp = client.get("/api/episode/export/capabilities")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()

    assert data["ok"] is True
    assert data["default_style_id"] == "breaking_news_v1"

    supported_ids = [s["id"] for s in data["supported_styles"]]
    assert supported_ids == ["breaking_news_v1"], \
        f"Expected only breaking_news_v1 supported, got {supported_ids}"

    unsupported_ids = [s["id"] for s in data["unsupported_styles"]]
    assert "timeline_daily_v1" in unsupported_ids
    assert "data_dashboard_v1" in unsupported_ids
    assert "research_briefing_v1" in unsupported_ids
    assert "podcast_cards_v1" in unsupported_ids

    assert data["audio"]["supports_audio_mux"] is True
    assert data["limits"]["width"]["default"] == 720
    assert data["limits"]["height"]["default"] == 1280
    assert data["limits"]["fps"]["default"] == 30

    print("[PASS] test_capabilities")


def test_invalid_style_rejected() -> None:
    """Test that non-supported style_id is rejected by the backend."""
    resp = client.post("/api/episode/export", json={
        "contract": build_mock_episode_contract(),
        "style_id": "research_briefing_v1",
        "width": 720,
        "height": 1280,
        "fps": 30,
    })
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
    data = resp.json()
    assert data["status"] == "failed"
    assert data["error_type"] == "invalid_style_id"

    print("[PASS] test_invalid_style_rejected")


def test_security_validation_invalid_audio_urls() -> None:
    """Test that resolve_safe_audio_url() rejects all invalid inputs."""
    from episode_export import resolve_safe_audio_url

    invalid_urls = [
        "https://evil.com/a.wav",
        "http://localhost/a.wav",
        "file:///tmp/a.wav",
        "C:\\tmp\\a.wav",
        "/etc/passwd",
        "/outputs/../../../secret.wav",
        "/outputs/test_audio/a.txt",
        "/outputs/test_audio/a.flac",
    ]

    for u in invalid_urls:
        try:
            result = resolve_safe_audio_url(u)
            raise AssertionError(f"Expected ValueError for {u!r}, but got {result}")
        except ValueError:
            pass  # Expected

    # None and empty string should return None (no audio mux)
    assert resolve_safe_audio_url(None) is None
    assert resolve_safe_audio_url("") is None

    print("[PASS] test_security_validation_invalid_audio_urls")


def test_pending_delete_protected(created_export_ids: list[str]) -> None:
    """Test that pending status exports cannot be deleted."""
    from episode_export import make_episode_export_id, write_episode_export_status

    export_id = make_episode_export_id()
    created_export_ids.append(export_id)

    # Create a pending status entry directly
    write_episode_export_status(
        export_id,
        status="pending",
        progress=0,
        message="test pending",
        style_id="breaking_news_v1",
        width=720,
        height=1280,
        fps=30,
    )

    resp = client.delete(f"/api/episode/exports/{export_id}")
    assert resp.status_code == 200, f"Expected 200 from delete, got {resp.status_code}"
    data = resp.json()
    assert data["ok"] is False, \
        f"Expected deletion of pending export to be rejected, but got ok={data.get('ok')}"
    assert "pending" in data.get("error", "").lower() or "running" in data.get("error", "").lower()

    print("[PASS] test_pending_delete_protected")


def test_no_audio_export(created_export_ids: list[str]) -> str:
    """Test async export without audio — completed, metadata, file serving."""
    export_id = start_export(build_mock_episode_contract())
    created_export_ids.append(export_id)

    status = wait_completed(export_id)
    assert status["result"]["has_audio"] is False

    meta_resp = client.get(f"/outputs/episode_exports/{export_id}/export_meta.json")
    assert meta_resp.status_code == 200, f"Meta fetch failed: {meta_resp.status_code}"
    meta = meta_resp.json()
    assert meta["has_audio"] is False
    assert meta.get("audio_url") is None

    mp4_resp = client.get(f"/outputs/episode_exports/{export_id}/output.mp4")
    assert mp4_resp.status_code == 200, f"MP4 serve failed: {mp4_resp.status_code}"
    assert mp4_resp.headers.get("content-type") == "video/mp4"

    html_resp = client.get(f"/outputs/episode_exports/{export_id}/animation.html")
    assert html_resp.status_code == 200, f"HTML serve failed: {html_resp.status_code}"

    print(f"[PASS] test_no_audio_export: export_id={export_id}")
    return export_id


def test_audio_export(created_export_ids: list[str]) -> str:
    """Test async export with audio — completed, metadata, ffprobe verification."""
    write_silence_wav(TEST_AUDIO_WAV)
    assert TEST_AUDIO_WAV.exists(), f"Test WAV not created: {TEST_AUDIO_WAV}"

    export_id = start_export(build_mock_episode_contract(), audio_url=TEST_AUDIO_URL)
    created_export_ids.append(export_id)

    status = wait_completed(export_id)
    assert status["result"]["has_audio"] is True

    meta_resp = client.get(f"/outputs/episode_exports/{export_id}/export_meta.json")
    assert meta_resp.status_code == 200
    meta = meta_resp.json()
    assert meta["has_audio"] is True
    assert meta["audio_url"] == TEST_AUDIO_URL
    assert meta["audio_ext"] == ".wav"
    assert meta["audio_size_bytes"] > 0

    mp4_path = ROOT / "outputs" / "episode_exports" / export_id / "output.mp4"
    assert mp4_path.exists(), f"output.mp4 not found: {mp4_path}"

    ffprobe_path = shutil.which("ffprobe")
    if ffprobe_path:
        print(f"  ffprobe found at {ffprobe_path}, checking audio stream...")
        has_audio_stream(mp4_path)  # raises on failure
        print("[PASS] ffprobe confirmed audio stream in output.mp4")
    else:
        print("[SKIP] ffprobe not found — stream-level assertion skipped")

    print(f"[PASS] test_audio_export: export_id={export_id}")
    return export_id


def test_history_contains(export_id: str) -> None:
    """Test that history list includes the given export_id."""
    resp = client.get("/api/episode/exports?limit=50")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    ids = [item["export_id"] for item in data["items"]]
    assert export_id in ids, f"export_id {export_id} not found in history"
    print(f"[PASS] test_history_contains: {export_id} found in history")


def test_delete_export(export_id: str, created_export_ids: list[str]) -> None:
    """Test that completed export can be deleted."""
    resp = client.delete(f"/api/episode/exports/{export_id}")
    assert resp.status_code == 200, f"Delete failed: {resp.status_code}"
    data = resp.json()
    assert data["ok"] is True
    assert data["deleted"] is True

    if export_id in created_export_ids:
        created_export_ids.remove(export_id)

    # Confirm it's gone
    status_resp = client.get(f"/api/episode/exports/{export_id}")
    assert status_resp.status_code == 404, \
        f"Expected 404 after delete, got {status_resp.status_code}"

    print(f"[PASS] test_delete_export: {export_id}")


def test_cleanup_dry_run() -> None:
    """Test cleanup endpoint in dry_run mode."""
    resp = client.post("/api/episode/exports/cleanup", json={
        "keep_latest": 30,
        "dry_run": True,
    })
    assert resp.status_code == 200, f"Cleanup failed: {resp.status_code}"
    data = resp.json()
    assert data["ok"] is True
    assert data["dry_run"] is True
    assert "deleted_count" in data
    assert "skipped" in data
    print("[PASS] test_cleanup_dry_run")


def test_invalid_export_id_rejected() -> None:
    """Test that malformed export_id values are handled."""
    for export_id in [
        "bad",
        "episode_export_123",      # too short
        "episode_export_gggggggggggg",  # invalid chars
    ]:
        resp = client.delete(f"/api/episode/exports/{export_id}")
        assert resp.status_code in (400, 404), \
            f"Expected 400/404 for {export_id}, got {resp.status_code}"

    print("[PASS] test_invalid_export_id_rejected")


# ---------------------------------------------------------------------------
# Cleanup helpers
# ---------------------------------------------------------------------------

def cleanup_created_exports(created_export_ids: list[str]) -> None:
    """Delete export directories for export IDs that still exist."""
    from episode_export import delete_episode_export

    for export_id in list(created_export_ids):
        result = delete_episode_export(export_id)
        if result.get("ok"):
            print(f"[CLEANUP] Deleted export: {export_id}")
        else:
            # Try direct directory cleanup if API fails
            export_dir = ROOT / "outputs" / "episode_exports" / export_id
            if export_dir.exists():
                shutil.rmtree(export_dir)
                print(f"[CLEANUP] Force-removed directory: {export_id}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    import time as time_module
    start = time_module.time()

    print("=" * 60)
    print("CP40.8: Episode Export E2E Regression Suite")
    print("=" * 60)
    print()

    created_export_ids: list[str] = []

    # Setup
    print("[SETUP] Cleaning up any stale test audio...")
    cleanup_test_audio()
    print()

    try:
        # Phase 1: Capabilities
        print("-" * 40)
        print("Phase 1: Capabilities API")
        print("-" * 40)
        test_capabilities()
        print()

        # Phase 2: Security guards
        print("-" * 40)
        print("Phase 2: Security guards (style + audio_url)")
        print("-" * 40)
        test_invalid_style_rejected()
        test_security_validation_invalid_audio_urls()
        print()

        # Phase 3: Pending delete protection
        print("-" * 40)
        print("Phase 3: Pending delete protection")
        print("-" * 40)
        test_pending_delete_protected(created_export_ids)
        print()

        # Phase 4: No-audio async export
        print("-" * 40)
        print("Phase 4: Async export without audio")
        print("-" * 40)
        no_audio_id = test_no_audio_export(created_export_ids)
        test_history_contains(no_audio_id)
        print()

        # Phase 5: Audio async export
        print("-" * 40)
        print("Phase 5: Async export with audio")
        print("-" * 40)
        audio_id = test_audio_export(created_export_ids)
        test_history_contains(audio_id)
        print()

        # Phase 6: Delete export
        print("-" * 40)
        print("Phase 6: Delete export")
        print("-" * 40)
        test_delete_export(no_audio_id, created_export_ids)
        print()

        # Phase 7: Cleanup (dry_run)
        print("-" * 40)
        print("Phase 7: Cleanup endpoint (dry_run)")
        print("-" * 40)
        test_cleanup_dry_run()
        print()

        # Phase 8: Invalid export_id
        print("-" * 40)
        print("Phase 8: Invalid export_id handling")
        print("-" * 40)
        test_invalid_export_id_rejected()
        print()

        elapsed = time_module.time() - start
        print("=" * 60)
        print(f"ALL CP40.8 E2E TESTS PASSED  (elapsed: {elapsed:.1f}s)")
        print("=" * 60)

    finally:
        print()
        print("[CLEANUP] Cleaning up test audio...")
        cleanup_test_audio()
        print("[CLEANUP] Cleaning up created export directories...")
        cleanup_created_exports(created_export_ids)
        print("[CLEANUP] Done")


if __name__ == "__main__":
    main()
