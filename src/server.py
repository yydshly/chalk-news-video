"""Local Web Studio V1 (CP12/CF13).

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

from src.config_loader import load_yaml


class GenerateRequest(BaseModel):
    mode: str = "sample"
    theme: str = "chalkboard"
    dialogue: bool = True
    mock: bool = True
    no_export: bool = False
    title: str = ""
    news_text: str = ""


app = FastAPI(title="Chalk News Video Studio")

# Paths
WEB_DIR = PROJECT_ROOT / "web"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "latest"
EXAMPLES_DIR = PROJECT_ROOT / "examples"

# Whitelist of allowed artifact names
ALLOWED_ARTIFACTS = {
    "semantic_ir",
    "dialogue_script",
    "dialogue_manifest",
    "render_ir",
}

# Whitelist of allowed output files for preview
ALLOWED_PREVIEW_FILES = {
    "animation.html",
    "output.mp4",
}

# ---------- job store (in-memory, single-user) ----------

JOBS: dict[str, dict] = {}
# Serialize pipeline execution to avoid shared output dir conflicts
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


def _prepare_news_input(body: GenerateRequest) -> tuple[Optional[str], Optional[str]]:
    """Prepare news input file path.

    Returns:
        (news_path, error_message). One of them is None.
    """
    mode = body.mode
    news_text = body.news_text
    title = body.title

    if mode == "sample":
        return str(EXAMPLES_DIR / "sample_news.json"), None
    elif mode == "text":
        if not news_text.strip():
            return None, "news_text is required when mode=text."
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
        try:
            with open(news_path, "w", encoding="utf-8") as f:
                json.dump(news_payload, f, ensure_ascii=False, indent=2)
            return news_path, None
        except Exception as e:
            return None, f"Failed to write news file: {e}"
    else:
        return None, f"Invalid mode: {mode}. Use 'sample' or 'text'."


def _build_pipeline_cmd(body: GenerateRequest, news_path: str) -> list[str]:
    """Build pipeline command from request."""
    cmd = [
        sys.executable, "-m", "src.pipeline",
        "--auto",
        "--mock",
        "--news", news_path,
        "--theme", body.theme,
    ]
    if body.dialogue:
        cmd += ["--tts", "--dialogue", "--dialogue-profile", "mock_dialogue"]
    else:
        cmd += ["--tts", "--tts-profile", "mock"]
    if body.no_export:
        cmd.append("--no-export")
    return cmd


def _parse_pipeline_progress(line: str) -> Optional[tuple[str, str, int]]:
    """Parse pipeline stdout/stderr line for stage progress.

    Returns:
        (stage, message, progress) if matched, else None.
    """
    for pattern, stage, message, progress in STAGE_PATTERNS:
        if pattern.search(line):
            return stage, message, progress
    return None


def _run_pipeline(body: GenerateRequest, job_id: str) -> tuple[int, str, str]:
    """Run the pipeline and emit events to job.

    Returns:
        (returncode, stdout, stderr)
    """
    news_path, error = _prepare_news_input(body)
    if error:
        return 1, "", error

    cmd = _build_pipeline_cmd(body, news_path)

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

    # Read stdout in real-time
    while True:
        line = proc.stdout.readline()
        if not line and proc.poll() is not None:
            break
        if line:
            stdout_lines.append(line)
            # Check for stage progress
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


def _build_generate_result(no_export: bool) -> dict:
    """Build GenerateResponse from current output state."""
    animation_path = OUTPUT_DIR / "animation.html"
    if not animation_path.exists():
        return {
            "ok": False,
            "error": "animation.html was not generated. Pipeline may have failed.",
        }

    if no_export:
        return {
            "ok": True,
            "exported": False,
            "output_mp4": None,
            "animation_html": "/outputs/latest/animation.html",
            "render_ir": "/api/artifacts/render_ir",
            "semantic_ir": "/api/artifacts/semantic_ir",
            "dialogue_script": "/api/artifacts/dialogue_script",
        }
    else:
        output_mp4_path = OUTPUT_DIR / "output.mp4"
        if not output_mp4_path.exists():
            return {
                "ok": False,
                "error": "output.mp4 was not generated. Check pipeline output.",
            }
        return {
            "ok": True,
            "exported": True,
            "output_mp4": "/outputs/latest/output.mp4",
            "animation_html": "/outputs/latest/animation.html",
            "render_ir": "/api/artifacts/render_ir",
            "semantic_ir": "/api/artifacts/semantic_ir",
            "dialogue_script": "/api/artifacts/dialogue_script",
        }


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


def _run_job(job_id: str, body: GenerateRequest) -> None:
    """Background job executor (runs in separate thread)."""
    job = JOBS.get(job_id)
    if not job:
        return

    try:
        # Update to running
        _emit_job_event(job_id, "progress", {
            "status": "running",
            "stage": "queued",
            "message": "任务已创建，正在启动",
            "progress": 0,
        })

        # Serialize pipeline execution to avoid shared output dir conflicts
        with JOB_LOCK:
            returncode, stdout, stderr = _run_pipeline(body, job_id)

        if returncode != 0:
            # Extract error message
            error_msg = stderr[-1000:] if stderr else stdout[-1000:]
            if not error_msg:
                error_msg = f"Pipeline failed with exit code {returncode}."

            # Try to find theme error
            theme_match = re.search(r"THEME ERROR.*", error_msg)
            if theme_match:
                error_msg = theme_match.group(0)
            elif "[auto:" in error_msg:
                # Extract stage error
                stage_error = re.search(r"\[auto:[^\]]+\].*", error_msg)
                if stage_error:
                    error_msg = stage_error.group(0)

            _emit_job_event(job_id, "error", {
                "status": "failed",
                "error": error_msg,
                "stage": job["stage"],
                "progress": job["progress"],
            })
            job["status"] = "failed"
            job["error"] = error_msg
            job["updated_at"] = datetime.now().isoformat()
            return

        # Check result
        result = _build_generate_result(body.no_export)

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
            return

        # Success
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

    except Exception as e:
        _emit_job_event(job_id, "error", {
            "status": "failed",
            "error": str(e),
        })
        job["status"] = "failed"
        job["error"] = str(e)
        job["updated_at"] = datetime.now().isoformat()


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
    themes = list(data.get("themes", {}).keys())
    return JSONResponse({
        "default_theme": default_theme,
        "themes": sorted(themes),
    })


# ---------- generate (sync, backward compatible) ----------


@app.post("/api/generate")
def api_generate(body: GenerateRequest):
    """Synchronous generate (CP12.1 compatibility)."""
    if not body.mock:
        return JSONResponse({
            "ok": False,
            "error": "Only mock=true is supported.",
        }, status_code=400)

    news_path, error = _prepare_news_input(body)
    if error:
        return JSONResponse({"ok": False, "error": error}, status_code=400)

    cmd = _build_pipeline_cmd(body, news_path)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
    except Exception as e:
        return JSONResponse({
            "ok": False,
            "error": f"Failed to run pipeline: {e}",
        }, status_code=500)

    if result.returncode != 0:
        return JSONResponse({
            "ok": False,
            "error": f"Pipeline failed with exit code {result.returncode}.\n{result.stderr[-1000:]}",
        }, status_code=500)

    gen_result = _build_generate_result(body.no_export)
    if not gen_result.get("ok"):
        return JSONResponse(gen_result, status_code=500)

    return JSONResponse(gen_result)


# ---------- jobs ----------


@app.post("/api/jobs")
def api_create_job(body: GenerateRequest):
    """Create an async generation job."""
    if not body.mock:
        return JSONResponse({
            "ok": False,
            "error": "Only mock=true is supported.",
        }, status_code=400)

    job_id = f"job_{uuid.uuid4().hex[:12]}"

    job = {
        "job_id": job_id,
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

    # Start background thread
    thread = threading.Thread(target=_run_job, args=(job_id, body), daemon=True)
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


# ---------- artifacts ----------


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


# ---------- preview (outputs/latest/) ----------


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

    parser = argparse.ArgumentParser(description="Chalk News Video Studio (CP13)")
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
