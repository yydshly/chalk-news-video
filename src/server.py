"""Local Web Studio V1 (CP12).

Minimal web interface for chalk-news-video generation.

Usage:
    python -m src.server --host 127.0.0.1 --port 8777
    # or
    uvicorn src.server:app --host 127.0.0.1 --port 8777 --reload
"""

import json
import os
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
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


# ---------- generate ----------


@app.post("/api/generate")
def api_generate(body: GenerateRequest):
    mode = body.mode
    theme = body.theme
    dialogue = body.dialogue
    mock = body.mock
    no_export = body.no_export
    title = body.title
    news_text = body.news_text

    # CP12: only mock mode supported
    if not mock:
        return JSONResponse({
            "ok": False,
            "error": "Only mock=true is supported in CP12.",
        }, status_code=400)

    # Build pipeline command
    news_path = None

    if mode == "sample":
        news_path = str(EXAMPLES_DIR / "sample_news.json")
    elif mode == "text":
        # Write text input to temporary news JSON
        if not news_text.strip():
            return JSONResponse({
                "ok": False,
                "error": "news_text is required when mode=text.",
            }, status_code=400)

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
        return JSONResponse({
            "ok": False,
            "error": f"Invalid mode: {mode}. Use 'sample' or 'text'.",
        }, status_code=400)

    # Build command
    cmd = [
        sys.executable, "-m", "src.pipeline",
        "--auto",
        "--mock",
        "--news", news_path,
        "--theme", theme,
    ]

    if dialogue:
        cmd += ["--tts", "--dialogue", "--dialogue-profile", "mock_dialogue"]
    else:
        cmd += ["--tts", "--tts-profile", "mock"]

    if no_export:
        cmd.append("--no-export")

    # Run pipeline synchronously
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

    # Check animation.html exists (required)
    animation_path = OUTPUT_DIR / "animation.html"
    if not animation_path.exists():
        return JSONResponse({
            "ok": False,
            "error": "animation.html was not generated. Pipeline may have failed.",
        }, status_code=500)

    # Build response based on no_export and output.mp4 existence
    if no_export:
        # no_export=true: preview only, no MP4
        response = {
            "ok": True,
            "exported": False,
            "output_mp4": None,
            "animation_html": "/outputs/latest/animation.html",
            "render_ir": "/api/artifacts/render_ir",
            "semantic_ir": "/api/artifacts/semantic_ir",
            "dialogue_script": "/api/artifacts/dialogue_script",
        }
    else:
        # no_export=false: MP4 should exist
        output_mp4_path = OUTPUT_DIR / "output.mp4"
        if not output_mp4_path.exists():
            return JSONResponse({
                "ok": False,
                "error": "output.mp4 was not generated. Check pipeline output.",
            }, status_code=500)

        response = {
            "ok": True,
            "exported": True,
            "output_mp4": "/outputs/latest/output.mp4",
            "animation_html": "/outputs/latest/animation.html",
            "render_ir": "/api/artifacts/render_ir",
            "semantic_ir": "/api/artifacts/semantic_ir",
            "dialogue_script": "/api/artifacts/dialogue_script",
        }

    return JSONResponse(response)


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
    # Security: whitelist check
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

    parser = argparse.ArgumentParser(description="Chalk News Video Studio (CP12)")
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
