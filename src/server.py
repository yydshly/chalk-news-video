"""Local Web Studio V1 (CP12-CP15).

Minimal web interface for chalk-news-video generation with async jobs.

Usage:
    python -m src.server --host 127.0.0.1 --port 8777
    # or
    uvicorn src.server:app --host 127.0.0.1 --port 8777 --reload
"""

import json
import os
import re
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load .env file for provider config (CP15.2.1)
# override=False: system env vars take precedence; .env only fills missing vars
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env", override=False)
except Exception:
    pass

from src.config_loader import load_yaml, load_llm_config


# ---------- provider status helpers (CP15) ----------


def _dedupe_keep_order(items: list[str]) -> list[str]:
    """Remove duplicates while preserving order."""
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _redact_secret_text(text: str) -> str:
    """Remove API keys and secrets from error text for safe display.

    Redacts:
    - sk- tokens (API keys)
    - MINIMAX_API_KEY=<value>
    - MIMO_API_KEY=<value>
    - Any voice_id values
    """
    if not text:
        return text
    # Redact sk- tokens (length 20+ alphanumeric strings)
    text = re.sub(r"sk-[a-zA-Z0-9_-]{20,}", "[REDACTED]", text)
    # Redact env var assignments with values
    for pattern in [
        r"(MINIMAX_API_KEY)=[^\s,;]+",
        r"(MIMO_API_KEY)=[^\s,;]+",
        r"(MINIMAX_TTS_HOST_VOICE_ID)=[^\s,;]+",
        r"(MINIMAX_TTS_EXPERT_VOICE_ID)=[^\s,;]+",
        r"(MINIMAX_TTS_VOICE_ID)=[^\s,;]+",
    ]:
        text = re.sub(pattern, r"\1=[REDACTED]", text)
    return text


def _check_env_vars(required_env: list[str]) -> list[str]:
    """Return list of missing env var names (not values)."""
    missing = []
    for var in required_env:
        if var and not os.environ.get(var):
            missing.append(var)
    return missing


def _collect_required_env_from_profile(profile: dict) -> list[str]:
    """Collect required env var names from a profile.

    Rules:
    - api_key_env is always required if present
    - base_url_env is only required if profile has no base_url or base_url is empty
    - model_env is only required if profile has no model or model is empty
    - endpoint_path_env is only required if profile has no endpoint_path
    - voice_id_env is only required if profile has no voice_id
    """
    required = []
    api_key = profile.get("api_key_env")
    if api_key:
        required.append(api_key)

    base_url = profile.get("base_url", "")
    base_url_env = profile.get("base_url_env")
    if base_url_env and not base_url:
        required.append(base_url_env)

    model = profile.get("model", "")
    model_env = profile.get("model_env")
    if model_env and not model:
        required.append(model_env)

    endpoint_path = profile.get("endpoint_path", "")
    endpoint_path_env = profile.get("endpoint_path_env")
    if endpoint_path_env and not endpoint_path:
        required.append(endpoint_path_env)

    voice_id = profile.get("voice_id", "")
    voice_id_env = profile.get("voice_id_env")
    if voice_id_env and not voice_id:
        required.append(voice_id_env)

    return _dedupe_keep_order(required)


def _get_llm_provider_status() -> list[dict]:
    """Return LLM provider status list with readiness and missing env vars."""
    try:
        llm_config = load_llm_config()
    except Exception:
        llm_config = {}

    profiles = llm_config.get("profiles", {})

    # Known provider display names and types
    provider_info = {
        "mock": {"name": "Mock", "type": "mock"},
        "minimax_m3_openai": {"name": "MiniMax M3 OpenAI", "type": "openai_compatible"},
        "minimax_m27_highspeed_openai": {"name": "MiniMax M2.7-highspeed", "type": "openai_compatible"},
        "minimax_m3_anthropic": {"name": "MiniMax M3 Anthropic", "type": "anthropic_messages"},
        "mimo_v25_pro_openai": {"name": "MiMo v2.5 Pro", "type": "openai_compatible"},
        "mimo_token_plan_v25_pro_openai": {"name": "MiMo Token Plan", "type": "openai_compatible"},
    }

    # Always include mock first
    result = [
        {
            "id": "mock",
            "name": "Mock",
            "ready": True,
            "type": "mock",
            "missing_env": [],
        }
    ]

    for pid, info in provider_info.items():
        if pid == "mock":
            continue
        profile = profiles.get(pid, {})
        required_env = _collect_required_env_from_profile(profile)
        missing = _check_env_vars(required_env)
        result.append({
            "id": pid,
            "name": info["name"],
            "ready": len(missing) == 0,
            "type": info["type"],
            "missing_env": missing,
        })

    return result


def _get_tts_provider_status() -> list[dict]:
    """Return TTS provider status list with readiness and missing env vars."""
    try:
        tts_config = load_yaml(PROJECT_ROOT / "config" / "tts.yaml")
    except Exception:
        tts_config = {}

    profiles = tts_config.get("profiles", {})
    dialogue_profiles = tts_config.get("dialogue_profiles", {})

    provider_info = {
        "mock": {"name": "Mock TTS", "type": "mock"},
        "mock_dialogue": {"name": "Mock Dialogue", "type": "mock"},
        "minimax_dialogue": {"name": "MiniMax Dialogue", "type": "minimax"},
    }

    result = []

    # mock
    result.append({
        "id": "mock",
        "name": "Mock TTS",
        "ready": True,
        "type": "mock",
        "missing_env": [],
    })

    # mock_dialogue
    result.append({
        "id": "mock_dialogue",
        "name": "Mock Dialogue",
        "ready": True,
        "type": "mock",
        "missing_env": [],
    })

    # minimax_dialogue
    min_diag_profile = dialogue_profiles.get("minimax_dialogue", {})
    required_env = []
    seen_envs = set()

    for speaker in ("host", "expert"):
        sp_info = min_diag_profile.get(speaker, {})
        voice_env = sp_info.get("voice_env")
        if voice_env and voice_env not in seen_envs:
            required_env.append(voice_env)
            seen_envs.add(voice_env)

        # Check the minimax_speech profile for required envs
        sp_profile_name = sp_info.get("profile")
        if sp_profile_name:
            sp_profile = profiles.get(sp_profile_name, {})
            profile_required = _collect_required_env_from_profile(sp_profile)
            for env in profile_required:
                if env not in seen_envs:
                    required_env.append(env)
                    seen_envs.add(env)

    missing = _check_env_vars(required_env)
    result.append({
        "id": "minimax_dialogue",
        "name": "MiniMax Dialogue",
        "ready": len(missing) == 0,
        "type": "minimax",
        "missing_env": missing,
    })

    return result


class GenerateRequest(BaseModel):
    mode: str = "sample"
    theme: str = "chalkboard"
    dialogue: bool = True
    mock: bool = True
    no_export: bool = False
    title: str = ""
    news_text: str = ""
    llm_provider: Optional[str] = None  # "mock" | "minimax_m3_openai" | etc.
    tts_provider: Optional[str] = None  # "mock" | "mock_dialogue" | "minimax_dialogue"
    repair: bool = False
    repair_attempts: int = 2
    # CP15.4: dialogue duration control
    target_duration_sec: Optional[int] = 60
    max_turns: Optional[int] = 14
    # CP19: user-selected hot AI news
    selected_news_id: Optional[str] = None
    selected_news_title: Optional[str] = None
    selected_news_url: Optional[str] = None
    selected_news_source: Optional[str] = None


def _get_provider_status_by_id(kind: str, provider_id: str) -> Optional[dict]:
    """Get provider status dict by kind ('llm' or 'tts') and provider_id."""
    if kind == "llm":
        providers = _get_llm_provider_status()
    elif kind == "tts":
        providers = _get_tts_provider_status()
    else:
        return None
    for p in providers:
        if p["id"] == provider_id:
            return p
    return None


def _validate_provider_selection(body: GenerateRequest) -> tuple[bool, Optional[str]]:
    """Validate provider selection.

    Returns (is_valid, error_message).
    error_message contains only env var names, never values.
    """
    # Determine effective llm_provider
    if body.llm_provider:
        llm_provider = body.llm_provider
    elif body.mock:
        llm_provider = "mock"
    else:
        llm_provider = "minimax_m3_openai"

    # Determine effective tts_provider
    if body.tts_provider:
        tts_provider = body.tts_provider
    elif body.dialogue:
        tts_provider = "mock_dialogue"
    else:
        tts_provider = "mock"

    # Check LLM provider readiness
    if llm_provider != "mock":
        llm_status = _get_provider_status_by_id("llm", llm_provider)
        if llm_status is None:
            return False, f"Unknown LLM provider: {llm_provider}"
        if not llm_status["ready"]:
            missing = ", ".join(llm_status["missing_env"])
            return False, f"Provider '{llm_provider}' is not ready. Missing env: {missing}"

    # Check TTS provider readiness (only for real TTS providers)
    if tts_provider not in ("mock", "mock_dialogue"):
        tts_status = _get_provider_status_by_id("tts", tts_provider)
        if tts_status is None:
            return False, f"Unknown TTS provider: {tts_provider}"
        if not tts_status["ready"]:
            missing = ", ".join(tts_status["missing_env"])
            return False, f"Provider '{tts_provider}' is not ready. Missing env: {missing}"

    return True, None


app = FastAPI(title="Chalk News Video Studio")


@app.get("/api/providers")
def api_providers():
    """Return LLM and TTS provider status with readiness and missing env vars.

    Does NOT expose API key values or voice_id values.
    """
    return JSONResponse({
        "ok": True,
        "llm": _get_llm_provider_status(),
        "tts": _get_tts_provider_status(),
    })


@app.get("/api/hot-ai-news")
def api_hot_ai_news():
    """CP19: Return hot AI news candidates for user selection.

    Returns up to 10 candidates without saving files.
    Does NOT expose API keys or fetch full article text.
    """
    import tempfile
    import uuid

    try:
        from .fetch_hot_ai_news import fetch_hot_ai_news

        # Use dry_run=True to get candidates without saving files
        candidates_output_path = Path(tempfile.gettempdir()) / f"hot_ai_candidates_{uuid.uuid4().hex[:8]}.json"

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_output = Path(tmpdir) / "latest_news.json"
            fetch_hot_ai_news(
                source="hn",
                hours=72,
                limit=10,
                output_path=tmp_output,
                candidates_output_path=candidates_output_path,
                dry_run=False,
            )

        # Read candidates
        if not candidates_output_path.exists():
            return JSONResponse({
                "ok": False,
                "error": "Failed to fetch hot AI news candidates.",
            }, status_code=500)

        with open(candidates_output_path, "r", encoding="utf-8") as f:
            candidates_data = json.load(f)

        items = candidates_data.get("items", [])

        # Return simplified structure for UI
        return JSONResponse({
            "ok": True,
            "count": len(items),
            "items": [
                {
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "source": item.get("source_name", "Hacker News"),
                    "points": item.get("points", 0),
                    "comments": item.get("comments", 0),
                    "final_score": item.get("final_score", 0),
                    "rank_reason": item.get("rank_reason", ""),
                    "summary": item.get("summary", ""),
                }
                for item in items
            ],
        })

    except Exception as e:
        redacted = _redact_secret_text(str(e))
        return JSONResponse({
            "ok": False,
            "error": f"Failed to fetch hot AI news: {redacted}",
        }, status_code=500)


# Paths
WEB_DIR = PROJECT_ROOT / "web"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "latest"
JOBS_DIR = PROJECT_ROOT / "outputs" / "jobs"
EPISODE_PREVIEWS_DIR = PROJECT_ROOT / "outputs" / "episode_previews"
EPISODE_EXPORTS_DIR = PROJECT_ROOT / "outputs" / "episode_exports"
EXAMPLES_DIR = PROJECT_ROOT / "examples"

# Whitelist of allowed artifact names
ALLOWED_ARTIFACTS = {
    "semantic_ir",
    "dialogue_script",
    "dialogue_manifest",
    "render_ir",
    "meta",
    "hot_ai_candidates",
    "latest_news",
}

# Whitelist of allowed output files for preview
ALLOWED_PREVIEW_FILES = {
    "animation.html",
    "output.mp4",
    "audio/dialogue.wav",
    "audio/dialogue.mp3",
}

# ---------- job store (in-memory, single-user) ----------

JOBS: dict[str, dict] = {}
JOB_LOCK = threading.Lock()

# Stage definitions for progress mapping
STAGE_PATTERNS = [
    (re.compile(r"\[auto:fetch_news\]"), "preparing_input", "准备输入", 5),
    (re.compile(r"\[auto:generate_ir\]"), "semantic_ir", "正在生成 semantic_ir", 25),
    (re.compile(r"\[auto:validate_ir\]"), "validate_ir", "正在校验 semantic_ir", 35),
    (re.compile(r"\[auto:dialogue\]"), "dialogue_script", "正在生成 dialogue_script", 40),
    (re.compile(r"\[auto:tts\]"), "tts", "正在生成 TTS 音频", 55),
    (re.compile(r"\[auto:layout\]"), "layout", "正在计算布局", 62),
    (re.compile(r"\[auto:render_html\]"), "render_html", "正在渲染 HTML", 82),
    (re.compile(r"\[auto:export\]"), "export_video", "正在导出 MP4", 92),
]


# ---------- helpers ----------


def _build_pipeline_cmd(body: GenerateRequest, news_path: str, output_dir: Path) -> list[str]:
    """Build pipeline command from request.

    Handles both mock and real LLM/TTS providers.
    API keys are NOT passed as command-line arguments — they are read from
    environment variables via the config files.
    """
    # Determine effective provider (must match _validate_provider_selection logic)
    if body.llm_provider:
        llm_provider = body.llm_provider
    elif body.mock:
        llm_provider = "mock"
    else:
        llm_provider = "minimax_m3_openai"

    # TTS provider
    if body.tts_provider:
        tts_provider = body.tts_provider
    elif body.dialogue:
        tts_provider = "mock_dialogue"
    else:
        tts_provider = "mock"

    cmd = [
        sys.executable, "-m", "src.pipeline",
        "--auto",
        "--news", news_path,
        "--theme", body.theme,
        "--output-dir", str(output_dir),
    ]

    if llm_provider == "mock":
        cmd.append("--mock")
    else:
        cmd += ["--profile", llm_provider]
        if body.repair:
            cmd.append("--repair")
            cmd += ["--repair-attempts", str(body.repair_attempts)]

    # TTS
    if body.dialogue:
        cmd += ["--tts", "--dialogue", "--dialogue-profile", tts_provider]
    elif tts_provider != "mock":
        cmd += ["--tts", "--tts-profile", tts_provider]
    else:
        cmd += ["--tts", "--tts-profile", "mock"]

    if body.no_export:
        cmd.append("--no-export")

    # CP15.4: dialogue duration control
    if body.target_duration_sec is not None:
        cmd += ["--target-duration-sec", str(body.target_duration_sec)]
    if body.max_turns is not None:
        cmd += ["--max-turns", str(body.max_turns)]

    return cmd


def _parse_pipeline_progress(line: str) -> Optional[tuple[str, str, int]]:
    """Parse pipeline stdout/stderr line for stage progress."""
    for pattern, stage, message, progress in STAGE_PATTERNS:
        if pattern.search(line):
            return stage, message, progress
    return None


def _emit_job_event(job_id: str, event_type: str, data: dict) -> None:
    """Append an event to a job's event list (thread-safe)."""
    job = JOBS.get(job_id)
    if not job:
        return
    event = {"type": event_type, "data": data}
    job["events"].append(event)
    job["status"] = data.get("status", job["status"])
    job["stage"] = data.get("stage", job["stage"])
    job["message"] = data.get("message", job["message"])
    job["progress"] = data.get("progress", job["progress"])
    job["updated_at"] = datetime.now().isoformat()


def _resolve_job_output_dir(job_id: str) -> Path:
    """Resolve output directory for a job_id.

    Security rules:
    - job_id must match ^job_[a-f0-9]+$
    - Returns JOBS[job_id].output_dir if in memory, otherwise JOBS_DIR / job_id
    - Resolved path must be under JOBS_DIR (no path traversal)
    """
    if not re.match(r"^job_[a-f0-9]+$", job_id):
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    if job_id in JOBS:
        output_dir = Path(JOBS[job_id]["output_dir"])
    else:
        output_dir = JOBS_DIR / job_id

    # Path traversal check
    try:
        output_dir = output_dir.resolve()
        jobs_dir_resolved = JOBS_DIR.resolve()
        # Ensure output_dir is under JOBS_DIR
        if not str(output_dir).startswith(str(jobs_dir_resolved)):
            raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    except Exception:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    return output_dir


def _load_history_from_disk() -> list[dict]:
    """Scan outputs/jobs/job_*/meta.json and return history items."""
    items = []
    if not JOBS_DIR.exists():
        return items

    for job_dir in JOBS_DIR.iterdir():
        if not job_dir.is_dir():
            continue
        job_id = job_dir.name
        if not re.match(r"^job_[a-f0-9]+$", job_id):
            continue

        meta_path = job_dir / "meta.json"
        if not meta_path.exists():
            continue

        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)

            item = {
                "job_id": meta.get("job_id", job_id),
                "status": meta.get("status", "unknown"),
                "stage": meta.get("status", "unknown"),
                "message": "完成" if meta.get("status") == "succeeded" else ("失败" if meta.get("status") == "failed" else "未知"),
                "progress": 100 if meta.get("status") == "succeeded" else (0 if meta.get("status") == "failed" else 50),
                "created_at": meta.get("created_at", ""),
                "updated_at": meta.get("updated_at", ""),
                "theme": meta.get("theme", ""),
                "mode": meta.get("mode", "sample"),
                "dialogue": meta.get("dialogue", False),
                "llm_provider": meta.get("llm_provider"),
                "tts_provider": meta.get("tts_provider"),
                "exported": meta.get("exported", False),
                "title": meta.get("title"),
                "summary": meta.get("summary"),
                "duration": meta.get("duration"),
                "error": meta.get("error"),
            }

            # Use artifacts from meta if present
            artifacts = meta.get("artifacts", {})
            if artifacts:
                item["animation_html"] = artifacts.get("animation_html")
                item["output_mp4"] = artifacts.get("output_mp4")
            else:
                # Fallback: derive from job_id
                item["animation_html"] = f"/outputs/jobs/{job_id}/animation.html"
                if meta.get("exported"):
                    item["output_mp4"] = f"/outputs/jobs/{job_id}/output.mp4"

            # CP15.6: Include dialogue_audio if available
            dialogue_audio_path = job_dir / "audio" / "dialogue.wav"
            if dialogue_audio_path.exists():
                item["dialogue_audio"] = f"/outputs/jobs/{job_id}/audio/dialogue.wav"
            else:
                # Try mp3 fallback
                dialogue_mp3_path = job_dir / "audio" / "dialogue.mp3"
                if dialogue_mp3_path.exists():
                    item["dialogue_audio"] = f"/outputs/jobs/{job_id}/audio/dialogue.mp3"

            # CP15.6: Fill in title from meta if not present
            if not item.get("title"):
                item["title"] = meta.get("title")

            items.append(item)
        except Exception:
            continue

    return items


def _build_generate_result(no_export: bool, output_dir: Path) -> dict:
    """Build GenerateResponse from job's isolated output directory."""
    animation_path = output_dir / "animation.html"
    if not animation_path.exists():
        return {
            "ok": False,
            "error": "animation.html was not generated. Pipeline may have failed.",
        }

    # CP15.6: Check for dialogue audio
    dialogue_audio = None
    audio_dir = output_dir / "audio"
    if audio_dir.exists():
        dialogue_wav = audio_dir / "dialogue.wav"
        if dialogue_wav.exists():
            dialogue_audio = f"/outputs/jobs/{output_dir.name}/audio/dialogue.wav"
        else:
            dialogue_mp3 = audio_dir / "dialogue.mp3"
            if dialogue_mp3.exists():
                dialogue_audio = f"/outputs/jobs/{output_dir.name}/audio/dialogue.mp3"

    if no_export:
        return {
            "ok": True,
            "exported": False,
            "output_mp4": None,
            "animation_html": f"/outputs/jobs/{output_dir.name}/animation.html",
            "render_ir": f"/api/jobs/{output_dir.name}/artifacts/render_ir",
            "semantic_ir": f"/api/jobs/{output_dir.name}/artifacts/semantic_ir",
            "dialogue_script": f"/api/jobs/{output_dir.name}/artifacts/dialogue_script",
            "dialogue_audio": dialogue_audio,
        }
    else:
        output_mp4_path = output_dir / "output.mp4"
        if not output_mp4_path.exists():
            return {
                "ok": False,
                "error": "output.mp4 was not generated. Check pipeline output.",
            }
        return {
            "ok": True,
            "exported": True,
            "output_mp4": f"/outputs/jobs/{output_dir.name}/output.mp4",
            "animation_html": f"/outputs/jobs/{output_dir.name}/animation.html",
            "render_ir": f"/api/jobs/{output_dir.name}/artifacts/render_ir",
            "semantic_ir": f"/api/jobs/{output_dir.name}/artifacts/semantic_ir",
            "dialogue_script": f"/api/jobs/{output_dir.name}/artifacts/dialogue_script",
            "dialogue_audio": dialogue_audio,
        }


def _write_meta(job: dict, output_dir: Path) -> None:
    """Write meta.json into job output directory."""
    job_id = job["job_id"]
    exported = job.get("result", {}).get("exported", False) if job.get("result") else False

    # Read duration/title/summary from render_ir if available
    duration = None
    title = None
    summary = None
    render_ir_path = output_dir / "render_ir.json"
    if render_ir_path.exists():
        try:
            with open(render_ir_path, "r", encoding="utf-8") as f:
                render_ir = json.load(f)
            duration = render_ir.get("total_duration")
            if render_ir.get("news"):
                title = render_ir["news"].get("title")
                summary = render_ir["news"].get("summary")
        except Exception:
            pass

    artifacts = {
        "animation_html": f"/outputs/jobs/{job_id}/animation.html",
        "render_ir": f"/api/jobs/{job_id}/artifacts/render_ir",
        "semantic_ir": f"/api/jobs/{job_id}/artifacts/semantic_ir",
        "dialogue_script": f"/api/jobs/{job_id}/artifacts/dialogue_script",
        "dialogue_manifest": f"/api/jobs/{job_id}/artifacts/dialogue_manifest",
        "meta": f"/api/jobs/{job_id}/artifacts/meta",
    }
    if exported:
        artifacts["output_mp4"] = f"/outputs/jobs/{job_id}/output.mp4"

    # CP15.6: Include dialogue_audio if available
    audio_dir = output_dir / "audio"
    if audio_dir.exists():
        if (audio_dir / "dialogue.wav").exists():
            artifacts["dialogue_audio"] = f"/outputs/jobs/{job_id}/audio/dialogue.wav"
        elif (audio_dir / "dialogue.mp3").exists():
            artifacts["dialogue_audio"] = f"/outputs/jobs/{job_id}/audio/dialogue.mp3"

    # Determine provider ids for meta (safe to record, no secrets)
    request = job.get("request", {})
    llm_provider = request.get("llm_provider") or ("mock" if request.get("mock", True) else "minimax_m3_openai")
    tts_provider = request.get("tts_provider")
    if not tts_provider:
        tts_provider = "mock_dialogue" if request.get("dialogue", False) else "mock"

    meta = {
        "job_id": job_id,
        "created_at": job["created_at"],
        "updated_at": job["updated_at"],
        "status": job["status"],
        "mode": request.get("mode", "sample"),
        "theme": request.get("theme", ""),
        "dialogue": request.get("dialogue", False),
        "mock": request.get("mock", True),
        "llm_provider": llm_provider,
        "tts_provider": tts_provider,
        "exported": exported,
        "title": title,
        "summary": summary,
        "duration": duration,
        "error": job["error"],
        "artifacts": artifacts,
    }
    try:
        with open(output_dir / "meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _run_job(job_id: str, body: GenerateRequest, output_dir: Path) -> None:
    """Background job executor (runs in separate thread)."""
    job = JOBS.get(job_id)
    if not job:
        return

    try:
        _emit_job_event(job_id, "progress", {
            "status": "running",
            "stage": "queued",
            "message": "任务已创建，正在启动",
            "progress": 0,
        })

        # Serialize pipeline execution
        with JOB_LOCK:
            returncode, stdout, stderr = _run_pipeline(body, job_id, output_dir)

        if returncode != 0:
            # Take up to 3000 chars of stderr/stdout, redact secrets
            raw_error = stderr[-3000:] if stderr else stdout[-3000:]
            if not raw_error:
                raw_error = f"Pipeline failed with exit code {returncode}."

            # Theme errors get priority
            theme_match = re.search(r"THEME ERROR.*", raw_error)
            if theme_match:
                error_msg = theme_match.group(0)
            elif "[auto:" in raw_error:
                # Collect all [auto:...] lines for better diagnostics
                auto_lines = re.findall(r"\[auto:[^\]]+\][^\n]*", raw_error)
                if auto_lines:
                    # Join all auto: lines, redact, and truncate
                    error_msg = " | ".join(auto_lines[:5])
                else:
                    error_msg = raw_error.strip().split("\n")[-1] if raw_error else f"exit code {returncode}"
            else:
                error_msg = raw_error.strip().split("\n")[-1] if raw_error else f"exit code {returncode}"

            error_msg = _redact_secret_text(error_msg)

            _emit_job_event(job_id, "error", {
                "status": "failed",
                "error": error_msg,
                "stage": job["stage"],
                "progress": job["progress"],
            })
            job["status"] = "failed"
            job["error"] = error_msg
            job["updated_at"] = datetime.now().isoformat()
            _write_meta(job, output_dir)
            return

        result = _build_generate_result(body.no_export, output_dir)

        if not result.get("ok"):
            _emit_job_event(job_id, "error", {
                "status": "failed",
                "error": result.get("error", "Unknown error"),
                "stage": job["stage"],
                "progress": job["progress"],
            })
            job["status"] = "failed"
            job["error"] = result.get("error")
            job["updated_at"] = datetime.now().isoformat()
            _write_meta(job, output_dir)
            return

        _emit_job_event(job_id, "done", {
            "status": "succeeded",
            "result": result,
        })
        job["status"] = "succeeded"
        job["stage"] = "succeeded"
        job["message"] = "完成"
        job["progress"] = 100
        job["result"] = result
        job["updated_at"] = datetime.now().isoformat()
        _write_meta(job, output_dir)

    except Exception as e:
        _emit_job_event(job_id, "error", {
            "status": "failed",
            "error": str(e),
        })
        job["status"] = "failed"
        job["error"] = str(e)
        job["updated_at"] = datetime.now().isoformat()
        _write_meta(job, output_dir)


def _run_pipeline(body: GenerateRequest, job_id: str, output_dir: Path) -> tuple[int, str, str]:
    """Run the pipeline and emit events to job."""
    mode = body.mode
    news_text = body.news_text
    title = body.title

    if mode == "sample":
        news_path = str(EXAMPLES_DIR / "sample_news.json")
    elif mode == "real_fixture":
        news_path = str(EXAMPLES_DIR / "real_news_fixture.json")
    elif mode == "hot_ai":
        # CP15.2.5: Fetch hot AI news from Hacker News into job output_dir
        # CP19: If user selected a news item, use it directly instead of auto-selecting
        latest_news_path = output_dir / "latest_news.json"
        candidates_path = output_dir / "hot_ai_candidates.json"

        if body.selected_news_id:
            # CP19: Use user-selected news — write directly to latest_news.json
            selected_news_payload = {
                "id": body.selected_news_id or f"selected_{uuid.uuid4().hex[:8]}",
                "title": body.selected_news_title or "Selected News",
                "url": body.selected_news_url or "",
                "source_id": "user_selected",
                "source_name": body.selected_news_source or "User Selected",
                "published_at": datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000"),
                "summary": "",
                "content": f"User selected news: {body.selected_news_title}",
                "content_source": "user_selected",
                "fetched_at": datetime.now().isoformat() + "+00:00",
            }
            try:
                with open(latest_news_path, "w", encoding="utf-8") as f:
                    json.dump(selected_news_payload, f, ensure_ascii=False, indent=2)
                print(f"[api/jobs] CP19: using user-selected news: {body.selected_news_title}")
            except Exception as e:
                return 1, "", f"Failed to write selected news: {e}"
        else:
            # Fallback: auto-select top candidate (log it)
            try:
                from .fetch_hot_ai_news import fetch_hot_ai_news
                _emit_job_event(job_id, "progress", {
                    "status": "running",
                    "stage": "preparing_input",
                    "message": "正在抓取热门 AI 新闻",
                    "progress": 5,
                })
                fetch_hot_ai_news(
                    source="hn",
                    hours=72,
                    limit=20,
                    output_path=latest_news_path,
                    candidates_output_path=candidates_path,
                )
            except Exception as e:
                redacted = _redact_secret_text(str(e))
                return 1, "", f"fetch_hot_ai_news failed: {redacted}"
        news_path = str(latest_news_path)
    elif mode == "text":
        if not news_text.strip():
            return 1, "", "news_text is required when mode=text."
        news_payload = {
            "id": f"manual_{uuid.uuid4().hex[:8]}",
            "title": title.strip() if title.strip() else "手动输入新闻",
            "url": "",
            "source_id": "manual",
            "source_name": "手动输入",
            "published_at": datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "summary": "",
            "content": news_text.strip(),
            "content_source": "manual",
            "fetched_at": datetime.now().isoformat() + "+00:00",
        }
        news_path = str(output_dir / "input_news.json")
        try:
            with open(news_path, "w", encoding="utf-8") as f:
                json.dump(news_payload, f, ensure_ascii=False, indent=2)
        except Exception as e:
            return 1, "", f"Failed to write news file: {e}"
    else:
        return 1, "", f"Invalid mode: {mode}. Use 'sample', 'real_fixture', 'text', or 'hot_ai'."

    cmd = _build_pipeline_cmd(body, news_path, output_dir)

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
    except Exception as e:
        return 1, "", str(e)

    stdout_lines = []
    stderr_lines = []

    while True:
        line = proc.stdout.readline()
        if not line and proc.poll() is not None:
            break
        if line:
            stdout_lines.append(line)
            parsed = _parse_pipeline_progress(line)
            if parsed:
                stage, message, progress = parsed
                _emit_job_event(job_id, "progress", {
                    "status": "running",
                    "stage": stage,
                    "message": message,
                    "progress": progress,
                })

    stdout = "".join(stdout_lines)
    stderr = proc.stderr.read()
    returncode = proc.returncode

    return returncode, stdout, stderr


# ---------- static files ----------


@app.get("/")
def serve_index():
    return FileResponse(str(WEB_DIR / "index.html"))


@app.get("/app.js")
def serve_app_js():
    return FileResponse(str(WEB_DIR / "app.js"))


@app.get("/style.css")
def serve_style_css():
    return FileResponse(str(WEB_DIR / "style.css"))


# ---------- theme sample whitelist (CP22/CP29) ----------
_THEME_SAMPLES = frozenset([
    "news_card_v1.html",
    "research_desk_v2.html",
    "causal_map_v1.html",
    "timeline_brief_v1.html",
    "data_dashboard_v1.html",
    "breaking_news_v1.html",
    "product_launch_v1.html",
    "paper_digest_v1.html",
    "podcast_cards_v1.html",
    "dev_terminal_v1.html",
    "magazine_cover_v1.html",
    "opinion_column_v1.html",
])


@app.get("/examples/theme_samples/{filename}")
def serve_theme_sample(filename: str):
    """Serve a whitelisted static theme sample HTML. No path traversal allowed."""
    if filename not in _THEME_SAMPLES:
        raise HTTPException(status_code=404, detail="Sample not found")
    sample_path = WEB_DIR / "theme_samples" / filename
    if not sample_path.exists():
        raise HTTPException(status_code=404, detail="Sample not found")
    return FileResponse(str(sample_path))


# ---------- episode preview static (CP31) ----------


@app.get("/outputs/episode_previews/{filename}")
def serve_episode_preview(filename: str):
    """Serve a saved episode preview HTML. Whitelist only .html in episode_previews."""
    if not filename.endswith(".html"):
        raise HTTPException(status_code=404, detail="Not found")
    # Block path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=404, detail="Not found")
    preview_path = EPISODE_PREVIEWS_DIR / filename
    if not preview_path.exists():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(str(preview_path))


# ---------- episode preview API (CP31) ----------


class EpisodeMockHtmlRequest(BaseModel):
    html: str
    episode_title: str


@app.post("/api/episode/mock-html")
def api_save_episode_mock_html(body: EpisodeMockHtmlRequest):
    """Save a mock episode HTML artifact. No job, no LLM, no TTS."""
    html: str = body.html
    episode_title: str = body.episode_title

    # Security: must contain DOCTYPE or html tag
    if "<!DOCTYPE html>" not in html and "<html" not in html:
        return JSONResponse({"ok": False, "error": "Invalid HTML: missing DOCTYPE or <html>"}, status_code=400)

    # Security: no API key / voice_id leakage
    if re.search(r"api[_-]?key", html, re.IGNORECASE):
        return JSONResponse({"ok": False, "error": "API key not allowed in HTML"}, status_code=400)
    if re.search(r"voice[_-]?id", html, re.IGNORECASE):
        return JSONResponse({"ok": False, "error": "voice_id not allowed in HTML"}, status_code=400)

    # Security: no external http/https links (allow localhost for dev)
    external_links = re.findall(r"https?://(?!localhost)[^\s\"']+", html)
    if external_links:
        return JSONResponse({"ok": False, "error": "External links not allowed: " + external_links[0]}, status_code=400)

    # Ensure output directory exists
    EPISODE_PREVIEWS_DIR.mkdir(parents=True, exist_ok=True)

    # Generate safe filename
    safe_title = re.sub(r"[^a-zA-Z0-9_一-鿿-]", "_", episode_title or "episode")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_id = uuid.uuid4().hex[:8]
    filename = f"episode_{timestamp}_{short_id}.html"
    file_path = EPISODE_PREVIEWS_DIR / filename

    # Write file
    try:
        file_path.write_text(html, encoding="utf-8")
    except Exception as e:
        return JSONResponse({"ok": False, "error": "Failed to write file: " + str(e)}, status_code=500)

    return JSONResponse({
        "ok": True,
        "path": f"/outputs/episode_previews/{filename}",
        "file_path": f"outputs/episode_previews/{filename}",
        "created_at": datetime.now().isoformat(),
    })


# ---------- episode HTML artifact history (CP32) ----------


@app.get("/api/episode/html-history")
def api_episode_html_history():
    """List saved episode HTML artifacts. Max 50, sorted by mtime descending."""
    if not EPISODE_PREVIEWS_DIR.exists():
        return JSONResponse({"ok": True, "items": []})

    try:
        files = []
        for f in EPISODE_PREVIEWS_DIR.iterdir():
            if not f.is_file():
                continue

            filename = f.name

            # CP32.1: Explicit safety filter — must match static route rules
            if ".." in filename or "/" in filename or "\\" in filename:
                continue

            if not filename.endswith(".html"):
                continue

            stat = f.stat()
            files.append({
                "filename": filename,
                "path": f"/outputs/episode_previews/{filename}",
                "file_path": f"outputs/episode_previews/{filename}",
                "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "size": stat.st_size,
            })
        # Sort by mtime descending
        files.sort(key=lambda x: x["created_at"], reverse=True)
        return JSONResponse({"ok": True, "items": files[:50]})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


# ---------- episode export (CP40.2) ----------


class EpisodeExportRequest(BaseModel):
    contract: dict
    style_id: str = "breaking_news_v1"
    width: int = 720
    height: int = 1280
    fps: int = 30
    audio_url: Optional[str] = None  # CP40.6: server-relative /outputs/ audio URL


# ---------- episode export history (CP40.5) ----------


@app.get("/api/episode/exports")
def api_list_episode_exports(limit: int = 50):
    """List recent episode export summaries, sorted by updated_at descending."""
    from src.episode_export import list_episode_exports

    try:
        items = list_episode_exports(limit=limit)
        return JSONResponse({
            "ok": True,
            "items": items,
            "count": len(items),
            "limit": limit,
        })
    except Exception as e:
        redacted = _redact_secret_text(str(e))
        return JSONResponse({"ok": False, "error": redacted}, status_code=500)


@app.post("/api/episode/exports/cleanup")
def api_cleanup_episode_exports(body: Optional[dict] = None):
    """Clean up old episode exports, keeping the most recent `keep_latest`.

    Body: { "keep_latest": 30, "dry_run": false }
    """
    from src.episode_export import cleanup_episode_exports

    keep_latest = 30
    dry_run = False

    if body:
        if "keep_latest" in body:
            keep_latest = int(body["keep_latest"])
        if "dry_run" in body:
            dry_run = bool(body["dry_run"])

    try:
        result = cleanup_episode_exports(keep_latest=keep_latest, dry_run=dry_run)
        return JSONResponse(result)
    except Exception as e:
        redacted = _redact_secret_text(str(e))
        return JSONResponse({"ok": False, "error": redacted}, status_code=500)


@app.delete("/api/episode/exports/{export_id}")
def api_delete_episode_export(export_id: str):
    """Delete a single episode export by ID.

    Only allows deleting completed/failed/unknown exports.
    """
    from src.episode_export import delete_episode_export

    try:
        result = delete_episode_export(export_id)
        if not result.get("ok"):
            return JSONResponse(result, status_code=400)
        return JSONResponse(result)
    except Exception as e:
        redacted = _redact_secret_text(str(e))
        return JSONResponse({"ok": False, "error": redacted}, status_code=500)


# ---------- episode export (CP40.2) ----------


@app.get("/api/episode/export/capabilities")
def api_episode_export_capabilities():
    """Return the episode export capabilities document (CP40.7).

    Declares which styles can produce an MP4 and which cannot.
    Used by the frontend export style picker.
    No real LLM, no real TTS.
    """
    from src.episode_export import get_episode_export_capabilities
    return JSONResponse(get_episode_export_capabilities())


@app.post("/api/episode/export")
def api_episode_export(body: EpisodeExportRequest):
    """Start an async episode export job.

    Returns immediately with 202 Accepted. Poll GET /api/episode/exports/{export_id} for status.
    No real LLM, no real TTS.
    CP40.6: supports optional audio_url for muxing an existing local audio file.
    CP40.7: style_id is validated against ALLOWED_STYLE_IDS (only breaking_news_v1).
    """
    from src.episode_export import (
        start_episode_export_background,
        ALLOWED_STYLE_IDS,
        resolve_safe_audio_url,
    )

    # Validate style_id
    if body.style_id not in ALLOWED_STYLE_IDS:
        return JSONResponse({
            "status": "failed",
            "error_type": "invalid_style_id",
            "message": f"Unsupported style_id {body.style_id!r}. Allowed: {', '.join(sorted(ALLOWED_STYLE_IDS))}",
        }, status_code=400)

    # Validate contract presence
    if not isinstance(body.contract, dict):
        return JSONResponse({
            "status": "failed",
            "error_type": "invalid_contract",
            "message": "contract must be an object",
        }, status_code=400)

    # Validate audio_url if provided (raises ValueError on invalid)
    try:
        resolve_safe_audio_url(body.audio_url)
    except ValueError as ve:
        return JSONResponse({
            "status": "failed",
            "error_type": "invalid_audio_url",
            "message": str(ve),
        }, status_code=400)

    try:
        result = start_episode_export_background(
            contract=body.contract,
            style_id=body.style_id,
            width=body.width,
            height=body.height,
            fps=body.fps,
            audio_url=body.audio_url,
        )
        return JSONResponse(result, status_code=202)
    except ValueError as ve:
        return JSONResponse({
            "status": "failed",
            "error_type": "validation_error",
            "message": str(ve),
        }, status_code=400)
    except Exception as exc:
        redacted = _redact_secret_text(str(exc))
        return JSONResponse({
            "status": "failed",
            "error_type": "export_failed",
            "message": redacted,
        }, status_code=500)


@app.get("/api/episode/exports/{export_id}")
def api_get_episode_export_status(export_id: str):
    """Get the status of an episode export job.

    Returns status.json contents: pending / running / completed / failed.
    """
    from src.episode_export import (
        validate_export_id,
        read_episode_export_status,
    )

    if not validate_export_id(export_id):
        raise HTTPException(status_code=404, detail="Export not found")

    status = read_episode_export_status(export_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Export not found")

    return JSONResponse(status)


@app.get("/outputs/episode_exports/{export_id}/{filename}")
def serve_episode_export_file(export_id: str, filename: str):
    """Serve a whitelisted file from an episode export directory.

    Only allows files in the whitelist and export_ids matching the pattern.
    """
    from src.episode_export import (
        validate_export_id,
        validate_filename,
        EPISODE_EXPORT_DIR,
    )

    # Validate export_id format
    if not validate_export_id(export_id):
        raise HTTPException(status_code=404, detail="Export not found")

    # Validate filename whitelist
    if not validate_filename(filename):
        raise HTTPException(status_code=404, detail="File not allowed")

    export_dir = EPISODE_EXPORT_DIR / export_id
    # Security: ensure resolved path is under EPISODE_EXPORT_DIR
    try:
        file_path = (export_dir / filename).resolve()
        if not str(file_path).startswith(str(EPISODE_EXPORT_DIR.resolve())):
            raise HTTPException(status_code=404, detail="Export not found")
    except Exception:
        raise HTTPException(status_code=404, detail="Export not found")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    if filename == "animation.html":
        return FileResponse(str(file_path), media_type="text/html")
    elif filename == "output.mp4":
        return FileResponse(str(file_path), media_type="video/mp4")
    elif filename == "contract.json":
        return FileResponse(str(file_path), media_type="application/json")
    elif filename == "export_meta.json":
        return FileResponse(str(file_path), media_type="application/json")
    elif filename == "status.json":
        return FileResponse(str(file_path), media_type="application/json")

    raise HTTPException(status_code=404, detail="Unsupported file type")


# ---------- health ----------


@app.get("/api/health")
def api_health():
    return JSONResponse({"ok": True, "project": "chalk-news-video"})


# ---------- themes ----------


@app.get("/api/themes")
def api_themes():
    themes_path = PROJECT_ROOT / "config" / "themes.yaml"
    data = load_yaml(themes_path)
    default_theme = data.get("default_theme", "chalkboard")
    themes_data = data.get("themes", {})
    # Return list of {id, name} objects for better UI display
    theme_list = []
    for theme_id, theme_cfg in themes_data.items():
        name = theme_cfg.get("name", theme_id) if isinstance(theme_cfg, dict) else theme_id
        theme_list.append({"id": theme_id, "name": name})
    theme_list.sort(key=lambda x: x["id"])
    return JSONResponse({
        "default_theme": default_theme,
        "themes": theme_list,
    })


# ---------- generate (sync, backward compatible) ----------


@app.post("/api/generate")
def api_generate(body: GenerateRequest):
    """Synchronous generate using shared OUTPUT_DIR (CP12.1 compatibility)."""
    if not body.mock:
        return JSONResponse({
            "ok": False,
            "error": "Only mock=true is supported.",
        }, status_code=400)

    mode = body.mode
    news_text = body.news_text
    title = body.title

    if mode == "sample":
        news_path = str(EXAMPLES_DIR / "sample_news.json")
    elif mode == "real_fixture":
        news_path = str(EXAMPLES_DIR / "real_news_fixture.json")
    elif mode == "text":
        if not news_text.strip():
            return JSONResponse({"ok": False, "error": "news_text is required when mode=text."}, status_code=400)
        news_payload = {
            "id": f"manual_{uuid.uuid4().hex[:8]}",
            "title": title.strip() if title.strip() else "手动输入新闻",
            "url": "",
            "source_id": "manual",
            "source_name": "手动输入",
            "published_at": datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "summary": "",
            "content": news_text.strip(),
            "content_source": "manual",
            "fetched_at": datetime.now().isoformat() + "+00:00",
        }
        news_path = str(OUTPUT_DIR / "input_news.json")
        with open(news_path, "w", encoding="utf-8") as f:
            json.dump(news_payload, f, ensure_ascii=False, indent=2)
    else:
        return JSONResponse({"ok": False, "error": f"Invalid mode: {mode}. Use 'sample', 'real_fixture', or 'text'."}, status_code=400)

    cmd = [
        sys.executable, "-m", "src.pipeline",
        "--auto", "--mock",
        "--news", news_path,
        "--theme", body.theme,
    ]
    if body.dialogue:
        cmd += ["--tts", "--dialogue", "--dialogue-profile", "mock_dialogue"]
    else:
        cmd += ["--tts", "--tts-profile", "mock"]
    if body.no_export:
        cmd.append("--no-export")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
    except Exception as e:
        return JSONResponse({"ok": False, "error": f"Failed to run pipeline: {e}"}, status_code=500)

    if result.returncode != 0:
        return JSONResponse({
            "ok": False,
            "error": f"Pipeline failed with exit code {result.returncode}.\n{result.stderr[-1000:]}",
        }, status_code=500)

    gen_result = _build_generate_result(body.no_export, OUTPUT_DIR)
    if not gen_result.get("ok"):
        return JSONResponse(gen_result, status_code=500)

    return JSONResponse(gen_result)


# ---------- jobs ----------


def _create_failed_job(body: GenerateRequest, error_message: str) -> tuple[str, Path]:
    """Create a failed job with the given error message. Returns (job_id, output_dir)."""
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    output_dir = JOBS_DIR / job_id
    output_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now().isoformat()
    job = {
        "job_id": job_id,
        "output_dir": str(output_dir),
        "status": "failed",
        "stage": "provider_validation",
        "message": "Provider not ready",
        "progress": 0,
        "created_at": now,
        "updated_at": now,
        "result": None,
        "error": error_message,
        "events": [{
            "type": "error",
            "data": {
                "status": "failed",
                "error": error_message,
                "stage": "provider_validation",
                "progress": 0,
            }
        }],
        "request": body.model_dump(),
    }

    JOBS[job_id] = job
    _write_meta(job, output_dir)

    return job_id, output_dir


@app.post("/api/jobs")
def api_create_job(body: GenerateRequest):
    """Create an async generation job with isolated output directory.

    Supports both mock and real LLM/TTS providers.
    If provider is not ready (missing required env vars), creates a failed job.
    """
    # Validate provider selection
    is_valid, error_msg = _validate_provider_selection(body)
    if not is_valid:
        job_id, output_dir = _create_failed_job(body, error_msg)
        return JSONResponse({
            "ok": False,
            "job_id": job_id,
            "status": "failed",
            "error": error_msg,
            "status_url": f"/api/jobs/{job_id}",
            "events_url": f"/api/jobs/{job_id}/events",
        }, status_code=400)

    job_id = f"job_{uuid.uuid4().hex[:12]}"
    output_dir = JOBS_DIR / job_id
    output_dir.mkdir(parents=True, exist_ok=True)

    job = {
        "job_id": job_id,
        "output_dir": str(output_dir),
        "status": "queued",
        "stage": "queued",
        "message": "任务已创建",
        "progress": 0,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "result": None,
        "error": None,
        "events": [],
        "request": body.model_dump(),
    }

    JOBS[job_id] = job

    thread = threading.Thread(target=_run_job, args=(job_id, body, output_dir), daemon=True)
    thread.start()

    return JSONResponse({
        "ok": True,
        "job_id": job_id,
        "status_url": f"/api/jobs/{job_id}",
        "events_url": f"/api/jobs/{job_id}/events",
    })


@app.get("/api/jobs/{job_id}")
def api_get_job(job_id: str):
    """Get job status and result."""
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    job = JOBS[job_id]
    return JSONResponse({
        "ok": True,
        "job": {
            "job_id": job["job_id"],
            "status": job["status"],
            "stage": job["stage"],
            "message": job["message"],
            "progress": job["progress"],
            "created_at": job["created_at"],
            "updated_at": job["updated_at"],
            "result": job["result"],
            "error": job["error"],
        },
    })


@app.get("/api/jobs/{job_id}/events")
def api_job_events(job_id: str):
    """SSE stream for job events."""
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    def event_stream():
        last_index = 0
        job = JOBS[job_id]

        while True:
            events = job["events"]
            while last_index < len(events):
                e = events[last_index]
                last_index += 1
                yield f"event: {e['type']}\ndata: {json.dumps(e['data'], ensure_ascii=False)}\n\n"

            if job["status"] in ("succeeded", "failed"):
                break

            time.sleep(0.3)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ---------- history ----------


@app.get("/api/history")
def api_history():
    """Return list of all jobs ordered by updated_at descending.

    Merges in-memory JOBS with disk-scanned meta.json files.
    For duplicate job_ids, in-memory state takes priority.
    """
    # Build a map of job_id -> item from disk
    disk_items: dict[str, dict] = {}
    for disk_item in _load_history_from_disk():
        disk_items[disk_item["job_id"]] = disk_item

    # Merge in-memory jobs (priority over disk)
    for job in JOBS.values():
        job_id = job["job_id"]
        item = {
            "job_id": job_id,
            "status": job["status"],
            "stage": job["stage"],
            "message": job["message"],
            "progress": job["progress"],
            "created_at": job["created_at"],
            "updated_at": job["updated_at"],
            "theme": job.get("request", {}).get("theme", ""),
            "mode": job.get("request", {}).get("mode", "sample"),
            "dialogue": job.get("request", {}).get("dialogue", False),
            "llm_provider": job.get("request", {}).get("llm_provider"),
            "tts_provider": job.get("request", {}).get("tts_provider"),
            "exported": job.get("result", {}).get("exported", False) if job.get("result") else False,
            "error": job["error"],
        }
        if job["result"]:
            item["animation_html"] = job["result"].get("animation_html")
            item["output_mp4"] = job["result"].get("output_mp4")
            # CP15.6: dialogue_audio from result
            item["dialogue_audio"] = job["result"].get("dialogue_audio")

        # Supplement from disk meta if available
        if job_id in disk_items:
            disk = disk_items.pop(job_id)
            # Fill in missing fields from disk
            for key in ("title", "summary", "duration", "mode", "dialogue_audio"):
                if key not in item or item[key] is None:
                    item[key] = disk.get(key)

        disk_items[job_id] = item

    # Add remaining disk-only items
    items = list(disk_items.values())

    items.sort(key=lambda x: x.get("updated_at") or x.get("created_at") or "", reverse=True)
    return JSONResponse({"ok": True, "items": items})


# ---------- job artifacts ----------


@app.get("/api/jobs/{job_id}/artifacts/{name}")
def api_job_artifact(job_id: str, name: str):
    """Get artifact JSON from a job's output directory.

    Supports both in-memory jobs and disk-only jobs (after restart).
    """
    if name not in ALLOWED_ARTIFACTS:
        raise HTTPException(status_code=404, detail=f"Unknown artifact: {name}")

    output_dir = _resolve_job_output_dir(job_id)

    if name == "meta":
        filename = "meta.json"
    else:
        filename = f"{name}.json"

    filepath = output_dir / filename

    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"{filename} not found.")

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return JSONResponse(data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"Invalid JSON in {filename}")


# ---------- job debug info (CP15.2.2 / CP15.2.3) ----------


@app.get("/api/jobs/{job_id}/debug")
def api_job_debug(job_id: str):
    """Return debug summary for a job.

    Returns validation issues and debug file presence without exposing secrets.
    This endpoint is for local debugging only.
    Debug files are read from job output_dir (job-scoped, CP15.2.3).
    """
    output_dir = _resolve_job_output_dir(job_id)

    debug_files = {}
    validation_issues = []
    deterministic_repairs = []

    # Read debug files from job output_dir (CP15.2.3: job-scoped)
    debug_issues_path = output_dir / "debug_validation_issues.json"
    if debug_issues_path.exists():
        debug_files["debug_validation_issues"] = True
        try:
            data = json.loads(debug_issues_path.read_text(encoding="utf-8"))
            # Return first 10 issues only (summary, not full details)
            issues = data.get("issues", [])
            for issue in issues[:10]:
                validation_issues.append({
                    "severity": issue.get("severity", "error"),
                    "code": issue.get("code", "?"),
                    "path": issue.get("path", "?"),
                    "message": _redact_secret_text(issue.get("message", "?")),
                })
        except Exception:
            pass
    else:
        debug_files["debug_validation_issues"] = False

    # Check for deterministic repairs (CP15.2.3)
    det_repairs_path = output_dir / "debug_deterministic_repairs.json"
    if det_repairs_path.exists():
        debug_files["debug_deterministic_repairs"] = True
        try:
            data = json.loads(det_repairs_path.read_text(encoding="utf-8"))
            deterministic_repairs = data.get("repairs", [])
        except Exception:
            pass
    else:
        debug_files["debug_deterministic_repairs"] = False

    # Check for invalid semantic_ir in job output_dir
    invalid_path = output_dir / "semantic_ir.invalid.json"
    debug_files["semantic_ir_invalid"] = invalid_path.exists()

    # Check for LLM prompt/response (CP15.2.3: job-scoped)
    llm_prompt_path = output_dir / "debug_llm_prompt.txt"
    debug_files["debug_llm_prompt"] = llm_prompt_path.exists()

    llm_response_path = output_dir / "debug_llm_response.txt"
    debug_files["debug_llm_response"] = llm_response_path.exists()

    # Check for repair response (CP15.2.3: job-scoped)
    repair_prompt_path = output_dir / "debug_repair_prompt.txt"
    debug_files["debug_repair_prompt"] = repair_prompt_path.exists()

    repair_resp_path = output_dir / "debug_repair_response.txt"
    debug_files["debug_repair_response"] = repair_resp_path.exists()

    return JSONResponse({
        "ok": True,
        "job_id": job_id,
        "debug_files": debug_files,
        "validation_issues": validation_issues,
        "deterministic_repairs": deterministic_repairs,
    })


# ---------- job output files ----------


@app.get("/outputs/jobs/{job_id}/{filename:path}")
def api_job_preview(job_id: str, filename: str):
    """Preview animation.html, output.mp4, or audio from a job's output directory.

    Supports both in-memory jobs and disk-only jobs (after restart).
    The :path suffix allows filename to contain slashes (e.g. audio/dialogue.wav).
    """
    if filename not in ALLOWED_PREVIEW_FILES:
        raise HTTPException(status_code=404, detail=f"Preview not allowed: {filename}")

    output_dir = _resolve_job_output_dir(job_id)
    filepath = output_dir / filename

    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"{filename} not found.")

    if filename == "animation.html":
        return FileResponse(str(filepath), media_type="text/html")
    elif filename == "output.mp4":
        return FileResponse(str(filepath), media_type="video/mp4")
    elif filename.startswith("audio/"):
        if filename.endswith(".wav"):
            return FileResponse(str(filepath), media_type="audio/wav")
        elif filename.endswith(".mp3"):
            return FileResponse(str(filepath), media_type="audio/mpeg")
        raise HTTPException(status_code=404, detail="Unsupported audio format")

    raise HTTPException(status_code=404, detail="Unknown file type")


# ---------- legacy artifacts / preview (CP12.1 compatibility) ----------


@app.get("/api/artifacts/{name}")
def api_artifact(name: str):
    if name not in ALLOWED_ARTIFACTS:
        raise HTTPException(status_code=404, detail=f"Unknown artifact: {name}")

    filename = f"{name}.json"
    filepath = OUTPUT_DIR / filename

    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"{filename} not found. Run generate first.")

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return JSONResponse(data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"Invalid JSON in {filename}")


@app.get("/outputs/latest/{filename}")
def api_preview(filename: str):
    if filename not in ALLOWED_PREVIEW_FILES:
        raise HTTPException(status_code=404, detail=f"Preview not allowed: {filename}")

    filepath = OUTPUT_DIR / filename

    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"{filename} not found. Run generate first.")

    if filename == "animation.html":
        return FileResponse(str(filepath), media_type="text/html")
    elif filename == "output.mp4":
        return FileResponse(str(filepath), media_type="video/mp4")

    raise HTTPException(status_code=404, detail="Unknown file type")


# ---------- CLI entry point ----------


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Chalk News Video Studio (CP14)")
    parser.add_argument(
        "--host", type=str, default="127.0.0.1",
        help="Host to bind (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port", type=int, default=8777,
        help="Port to bind (default: 8777)",
    )
    args = parser.parse_args()

    print(f"Starting Chalk News Video Studio at http://{args.host}:{args.port}")
    print(f"Open http://{args.host}:{args.port} in your browser")
    uvicorn.run(app, host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
