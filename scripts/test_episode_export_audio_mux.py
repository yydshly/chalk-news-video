#!/usr/bin/env python3
"""CP40.6.2: ffprobe Audio Track Verification Test.

This test verifies that episode export with audio_url:
1. Generates a real MP4 with an audio stream (verified via ffprobe)
2. Writes correct has_audio metadata in export_meta.json and status.json
3. Rejects invalid audio_url inputs
4. Maintains backward compatibility for no-audio exports

No real TTS, no real LLM, no /api/jobs, no Remotion.
"""

from __future__ import annotations

import json
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
# Test fixtures
# ---------------------------------------------------------------------------

TEST_AUDIO_DIR = ROOT / "outputs" / "test_audio"
TEST_AUDIO_WAV = TEST_AUDIO_DIR / "cp40_6_silence.wav"
TEST_AUDIO_URL = "/outputs/test_audio/cp40_6_silence.wav"


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

    Returns True if ffprobe is installed and finds an audio stream.
    Returns False if ffprobe is not installed (caller should SKIP stream check).
    Raises AssertionError if ffprobe is installed but no audio stream found.
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


# ---------------------------------------------------------------------------
# Contract fixture
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_security_validation_invalid_audio_urls() -> None:
    """Verify resolve_safe_audio_url() rejects all invalid inputs."""
    from episode_export import resolve_safe_audio_url

    invalid_urls = [
        "https://evil.com/a.wav",
        "http://localhost/a.wav",
        "file:///tmp/a.wav",
        "C:\\tmp\\a.wav",
        "/etc/passwd",
        "/outputs/../../../secret.wav",
        "/outputs/test_audio/a.txt",           # wrong extension
        "/outputs/test_audio/a.flac",           # unsupported extension
        "/outputs/test_audio/",                  # directory (not a file)
    ]

    for u in invalid_urls:
        try:
            result = resolve_safe_audio_url(u)
            raise AssertionError(
                f"Expected ValueError for {u!r}, but got {result}"
            )
        except ValueError:
            pass  # Expected

    # None and empty string should return None (no audio mux)
    assert resolve_safe_audio_url(None) is None
    assert resolve_safe_audio_url("") is None

    print("[PASS] Security validation: all invalid URLs rejected correctly")


def test_security_validation_valid_audio_url() -> None:
    """Verify resolve_safe_audio_url() accepts a valid /outputs/ URL."""
    from episode_export import resolve_safe_audio_url

    # Write the test audio first
    write_silence_wav(TEST_AUDIO_WAV)
    assert TEST_AUDIO_WAV.exists(), "Test WAV was not created"

    result = resolve_safe_audio_url(TEST_AUDIO_URL)
    assert result is not None
    assert result == TEST_AUDIO_WAV
    assert result.exists()

    print("[PASS] Security validation: valid /outputs/ URL accepted")


def test_episode_export_with_audio() -> None:
    """Test async episode export with audio_url via POST /api/episode/export."""
    # 1. Start async export with audio_url
    resp = client.post("/api/episode/export", json={
        "contract": build_mock_episode_contract(),
        "style_id": "breaking_news_v1",
        "width": 720,
        "height": 1280,
        "fps": 30,
        "audio_url": TEST_AUDIO_URL,
    })

    assert resp.status_code == 202, f"Expected 202, got {resp.status_code}: {resp.text}"
    data = resp.json()

    export_id = data["export_id"]
    assert export_id.startswith("episode_export_")

    # Verify POST response includes audio metadata
    assert data.get("has_audio") is True
    assert data.get("audio_url") == TEST_AUDIO_URL

    # 2. Poll until completed
    max_polls = 120
    final_status = None
    final_data = None
    for i in range(max_polls):
        time.sleep(1)
        r = client.get(f"/api/episode/exports/{export_id}")
        assert r.status_code == 200
        status_data = r.json()
        current = status_data.get("status")
        progress = status_data.get("progress", 0)
        print(f"  poll {i+1:3d}: status={current}, progress={progress}")

        if current in ("completed", "failed"):
            final_status = current
            final_data = status_data
            break
    else:
        raise AssertionError(f"Export did not complete after {max_polls} polls")

    assert final_status == "completed", \
        f"Expected completed, got {final_status}: {final_data}"

    # 3. Verify status result has_audio
    result = final_data.get("result")
    assert result is not None, "result missing in completed status"
    assert result.get("has_audio") is True, \
        f"status.json result.has_audio should be True, got {result.get('has_audio')}"

    # 4. Verify export_meta.json
    meta_url = f"/outputs/episode_exports/{export_id}/export_meta.json"
    meta_resp = client.get(meta_url)
    assert meta_resp.status_code == 200, f"Meta fetch failed: {meta_resp.status_code}"
    meta = meta_resp.json()

    assert meta.get("has_audio") is True, \
        f"export_meta.json.has_audio should be True, got {meta.get('has_audio')}"
    assert meta.get("audio_url") == TEST_AUDIO_URL, \
        f"export_meta.json.audio_url should be {TEST_AUDIO_URL}, got {meta.get('audio_url')}"
    assert meta.get("audio_ext") == ".wav", \
        f"export_meta.json.audio_ext should be .wav, got {meta.get('audio_ext')}"
    assert meta.get("audio_size_bytes") and meta["audio_size_bytes"] > 0, \
        f"audio_size_bytes should be positive, got {meta.get('audio_size_bytes')}"

    # 5. Verify output.mp4 exists
    mp4_url = f"/outputs/episode_exports/{export_id}/output.mp4"
    mp4_resp = client.get(mp4_url)
    assert mp4_resp.status_code == 200, f"MP4 serve failed: {mp4_resp.status_code}"
    assert mp4_resp.headers.get("content-type") == "video/mp4"

    # 6. Verify MP4 has audio stream via ffprobe
    export_dir = ROOT / "outputs" / "episode_exports" / export_id
    mp4_path = export_dir / "output.mp4"
    assert mp4_path.exists(), f"output.mp4 not found at {mp4_path}"

    ffprobe_path = shutil.which("ffprobe")
    if ffprobe_path:
        print(f"  ffprobe found at {ffprobe_path}, checking audio stream...")
        has_audio_stream(mp4_path)  # raises AssertionError on failure
        print("[PASS] ffprobe: audio stream confirmed in output.mp4")
    else:
        print("[SKIP] ffprobe not installed — stream-level verification skipped")
        print("       Metadata verified: has_audio=true in export_meta.json and status.json")

    print(f"[PASS] Episode export with audio completed: export_id={export_id}")


def test_episode_export_without_audio() -> None:
    """Test that no-audio export still works (backward compatibility)."""
    # 1. Start export without audio_url
    resp = client.post("/api/episode/export", json={
        "contract": build_mock_episode_contract(),
        "style_id": "breaking_news_v1",
        "width": 720,
        "height": 1280,
        "fps": 30,
        # audio_url omitted
    })

    assert resp.status_code == 202
    data = resp.json()
    export_id = data["export_id"]

    # Verify POST response has_audio=False
    assert data.get("has_audio") is False
    assert data.get("audio_url") is None

    # 2. Poll until completed
    max_polls = 120
    final_status = None
    for i in range(max_polls):
        time.sleep(1)
        r = client.get(f"/api/episode/exports/{export_id}")
        assert r.status_code == 200
        status_data = r.json()
        current = status_data.get("status")
        print(f"  poll {i+1:3d}: status={current}")

        if current in ("completed", "failed"):
            final_status = current
            break
    else:
        raise AssertionError(f"Export did not complete after {max_polls} polls")

    assert final_status == "completed"

    # 3. Verify metadata
    result = status_data.get("result")
    assert result is not None
    assert result.get("has_audio") is False

    meta_url = f"/outputs/episode_exports/{export_id}/export_meta.json"
    meta_resp = client.get(meta_url)
    assert meta_resp.status_code == 200
    meta = meta_resp.json()
    assert meta.get("has_audio") is False
    assert meta.get("audio_url") is None

    # 4. Verify MP4 exists
    mp4_url = f"/outputs/episode_exports/{export_id}/output.mp4"
    mp4_resp = client.get(mp4_url)
    assert mp4_resp.status_code == 200

    print(f"[PASS] Episode export without audio completed: export_id={export_id}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("CP40.6.2: ffprobe Audio Track Verification Test")
    print("=" * 60)
    print()

    # Setup: generate test audio
    print("[SETUP] Generating controlled silence WAV...")
    cleanup_test_audio()
    write_silence_wav(TEST_AUDIO_WAV)
    print(f"[SETUP] Test WAV: {TEST_AUDIO_WAV}")
    print()

    try:
        # Phase 1: Security validation
        print("-" * 40)
        print("Phase 1: Security validation (invalid URLs)")
        print("-" * 40)
        test_security_validation_invalid_audio_urls()
        print()

        # Phase 2: Security validation (valid URL)
        print("-" * 40)
        print("Phase 2: Security validation (valid URL)")
        print("-" * 40)
        test_security_validation_valid_audio_url()
        print()

        # Phase 3: Async export with audio
        print("-" * 40)
        print("Phase 3: Episode export with audio_url (async API)")
        print("-" * 40)
        test_episode_export_with_audio()
        print()

        # Phase 4: Async export without audio (backward compat)
        print("-" * 40)
        print("Phase 4: Episode export without audio (backward compat)")
        print("-" * 40)
        test_episode_export_without_audio()
        print()

        print("=" * 60)
        print("ALL TESTS PASSED")
        print("=" * 60)

    finally:
        # Cleanup test audio
        print()
        print("[CLEANUP] Removing test audio directory...")
        cleanup_test_audio()
        print("[CLEANUP] Done")


if __name__ == "__main__":
    main()
