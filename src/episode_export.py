"""Episode Export Service Layer (CP40.2-CP40.3).

CP40.2: export_episode_contract_to_mp4() — synchronous export.
CP40.3: async job status via status.json + background thread.

No real LLM, no real TTS, no audio mux.
"""

from __future__ import annotations

import json
import re
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Resolve project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parents[1]
EPISODE_EXPORT_DIR = PROJECT_ROOT / "outputs" / "episode_exports"

# Allowed export_id format: episode_export_<12 hex chars>
EXPORT_ID_PATTERN = re.compile(r"^episode_export_[a-f0-9]{12}$")

# Allowed filename whitelist for static serving
ALLOWED_EXPORT_FILENAMES = frozenset([
    "output.mp4",
    "animation.html",
    "contract.json",
    "export_meta.json",
    "status.json",
])

# Style IDs allowed in this checkpoint
ALLOWED_STYLE_IDS = frozenset(["breaking_news_v1"])

# Dimension constraints
MIN_WIDTH = 360
MAX_WIDTH = 1080
MIN_HEIGHT = 640
MAX_HEIGHT = 1920
MIN_FPS = 1
MAX_FPS = 30


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
    text = re.sub(r"sk-[a-zA-Z0-9_-]{20,}", "[REDACTED]", text)
    for pattern in [
        r"(MINIMAX_API_KEY)=[^\s,;]+",
        r"(MIMO_API_KEY)=[^\s,;]+",
        r"(MINIMAX_TTS_HOST_VOICE_ID)=[^\s,;]+",
        r"(MINIMAX_TTS_EXPERT_VOICE_ID)=[^\s,;]+",
        r"(MINIMAX_TTS_VOICE_ID)=[^\s,;]+",
    ]:
        text = re.sub(pattern, r"\1=[REDACTED]", text)
    return text


def make_episode_export_id() -> str:
    """Generate a new episode export ID."""
    return "episode_export_" + uuid.uuid4().hex[:12]


def clamp_export_options(
    width: int,
    height: int,
    fps: int,
) -> tuple[int, int, int]:
    """Clamp width, height, fps to allowed ranges."""
    w = max(MIN_WIDTH, min(MAX_WIDTH, width))
    h = max(MIN_HEIGHT, min(MAX_HEIGHT, height))
    f = max(MIN_FPS, min(MAX_FPS, fps))
    return w, h, f


def validate_export_id(export_id: str) -> bool:
    """Check that export_id matches the expected pattern."""
    return bool(EXPORT_ID_PATTERN.match(export_id))


def validate_filename(filename: str) -> bool:
    """Check that filename is in the whitelist."""
    return filename in ALLOWED_EXPORT_FILENAMES


def get_episode_export_dir(export_id: str) -> Path:
    """Return the export directory path for a given export_id."""
    return EPISODE_EXPORT_DIR / export_id


def get_episode_export_status_path(export_id: str) -> Path:
    """Return the status.json path for a given export_id."""
    return EPISODE_EXPORT_DIR / export_id / "status.json"


def _validate_contract(contract: dict) -> tuple[bool, Optional[str]]:
    """Validate the episode contract structure.

    Returns (is_valid, error_message).
    """
    if not isinstance(contract, dict):
        return False, "contract must be an object"

    schema = contract.get("schema_version")
    if schema != "episode_template_v1":
        return False, f"schema_version must be 'episode_template_v1', got {schema!r}"

    template_id = contract.get("template_id")
    if template_id and template_id != "breaking_news_v1":
        return False, f"template_id must be 'breaking_news_v1', got {template_id!r}"

    return True, None


# ---------------------------------------------------------------------------
# Status management
# ---------------------------------------------------------------------------

def write_episode_export_status(
    export_id: str,
    *,
    status: str,
    message: Optional[str] = None,
    progress: Optional[int] = None,
    result: Optional[dict] = None,
    error_type: Optional[str] = None,
    error_message: Optional[str] = None,
    style_id: Optional[str] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    fps: Optional[int] = None,
) -> dict:
    """Write a status.json file for the given export_id.

    Returns the written status dict.
    """
    now = datetime.now().isoformat()
    export_dir = EPISODE_EXPORT_DIR / export_id
    export_dir.mkdir(parents=True, exist_ok=True)

    # Load existing status if present
    status_path = export_dir / "status.json"
    existing = {}
    if status_path.exists():
        try:
            existing = json.loads(status_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    # Merge with new values
    data = {
        "export_id": export_id,
        "status": status,
        "message": message,
        "progress": progress,
        "style_id": existing.get("style_id"),
        "width": existing.get("width"),
        "height": existing.get("height"),
        "fps": existing.get("fps"),
        "created_at": existing.get("created_at", now),
        "updated_at": now,
        "result": result,
        "error_type": error_type,
        "error_message": error_message,
    }

    # Remove None values so they don't clutter the JSON
    data = {k: v for k, v in data.items() if v is not None}

    status_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def read_episode_export_status(export_id: str) -> Optional[dict]:
    """Read the status.json for a given export_id.

    Returns None if not found.
    """
    status_path = get_episode_export_status_path(export_id)
    if not status_path.exists():
        return None
    try:
        return json.loads(status_path.read_text(encoding="utf-8"))
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Background worker
# ---------------------------------------------------------------------------

def _run_episode_export_worker(
    export_id: str,
    contract: dict,
    style_id: str,
    width: int,
    height: int,
    fps: int,
) -> None:
    """Background worker: renders HTML and exports MP4.

    Updates status.json at each step.
    All errors are caught and redacted before writing to status.json.
    """
    try:
        # Import heavy deps inside worker (defer module load)
        from render_episode_html import render_episode_stage_html_to_file
        from export_video import export_video

        # Mark as running
        write_episode_export_status(
            export_id,
            status="running",
            progress=10,
            message="Rendering HTML",
        )

        export_dir = EPISODE_EXPORT_DIR / export_id

        # Write contract.json
        contract_path = export_dir / "contract.json"
        contract_path.write_text(
            json.dumps(contract, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # Render HTML
        html_path = export_dir / "animation.html"
        render_episode_stage_html_to_file(contract, html_path, style_id=style_id)

        write_episode_export_status(
            export_id,
            status="running",
            progress=50,
            message="Exporting MP4",
        )

        # Export MP4
        mp4_path = export_dir / "output.mp4"
        export_video(
            html_path=str(html_path),
            output_path=str(mp4_path),
            fps=fps,
            width=width,
            height=height,
            headless=True,
            audio_path=None,
        )

        write_episode_export_status(
            export_id,
            status="running",
            progress=90,
            message="Writing metadata",
        )

        # Write export_meta.json
        mp4_size = mp4_path.stat().st_size if mp4_path.exists() else 0
        meta = {
            "export_id": export_id,
            "status": "completed",
            "style_id": style_id,
            "width": width,
            "height": height,
            "fps": fps,
            "html_path": str(html_path),
            "mp4_path": str(mp4_path),
            "mp4_url": f"/outputs/episode_exports/{export_id}/output.mp4",
            "html_url": f"/outputs/episode_exports/{export_id}/animation.html",
            "meta_url": f"/outputs/episode_exports/{export_id}/export_meta.json",
            "contract_url": f"/outputs/episode_exports/{export_id}/contract.json",
            "mp4_size_bytes": mp4_size,
            "audio_path": None,
            "created_at": datetime.now().isoformat(),
        }
        meta_path = export_dir / "export_meta.json"
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

        # Mark completed
        write_episode_export_status(
            export_id,
            status="completed",
            progress=100,
            message="Export completed",
            result={
                "mp4_url": meta["mp4_url"],
                "html_url": meta["html_url"],
                "meta_url": meta["meta_url"],
                "contract_url": meta["contract_url"],
                "mp4_size_bytes": mp4_size,
            },
        )

    except Exception as exc:
        redacted = _redact_secret_text(str(exc))
        write_episode_export_status(
            export_id,
            status="failed",
            progress=100,
            message="Export failed",
            error_type="export_failed",
            error_message=redacted,
        )


def start_episode_export_background(
    contract: dict,
    *,
    style_id: str = "breaking_news_v1",
    width: int = 720,
    height: int = 1280,
    fps: int = 30,
) -> dict[str, Any]:
    """Start an async episode export in a background thread.

    Writes initial status.json and launches a daemon thread.
    Returns immediately with export_id and URLs.

    Returns:
        dict with export_id, status, status_url, mp4_url, etc.
    """
    # Validate contract
    valid, error = _validate_contract(contract)
    if not valid:
        raise ValueError(f"Invalid contract: {error}")

    # Validate style_id
    if style_id not in ALLOWED_STYLE_IDS:
        raise ValueError(
            f"Unsupported style_id {style_id!r}. "
            f"Allowed: {', '.join(sorted(ALLOWED_STYLE_IDS))}"
        )

    # Clamp dimensions
    width, height, fps = clamp_export_options(width, height, fps)

    # Generate export_id and create directory
    export_id = make_episode_export_id()
    export_dir = EPISODE_EXPORT_DIR / export_id
    export_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now().isoformat()

    # Write initial pending status
    write_episode_export_status(
        export_id,
        status="pending",
        progress=0,
        message="Export queued",
        style_id=style_id,
        width=width,
        height=height,
        fps=fps,
    )

    # Launch background thread
    thread = threading.Thread(
        target=_run_episode_export_worker,
        args=(export_id, contract, style_id, width, height, fps),
        daemon=True,
    )
    thread.start()

    return {
        "export_id": export_id,
        "status": "pending",
        "status_url": f"/api/episode/exports/{export_id}",
        "mp4_url": f"/outputs/episode_exports/{export_id}/output.mp4",
        "html_url": f"/outputs/episode_exports/{export_id}/animation.html",
        "meta_url": f"/outputs/episode_exports/{export_id}/export_meta.json",
        "contract_url": f"/outputs/episode_exports/{export_id}/contract.json",
        "width": width,
        "height": height,
        "fps": fps,
        "created_at": now,
    }


# ---------------------------------------------------------------------------
# Synchronous export (CP40.2 — kept for scripts and backward compatibility)
# ---------------------------------------------------------------------------

def export_episode_contract_to_mp4(
    contract: dict,
    *,
    style_id: str = "breaking_news_v1",
    width: int = 720,
    height: int = 1280,
    fps: int = 30,
    audio_path: Optional[str] = None,
    export_id: Optional[str] = None,
) -> dict[str, Any]:
    """Export an episode contract to MP4 (synchronous).

    Kept for backward compatibility with CP40.2 scripts.
    Prefer start_episode_export_background() for async use.
    """
    # Enforce audio_path=None for CP40.2/CP40.3
    audio_path = None

    # Validate contract
    valid, error = _validate_contract(contract)
    if not valid:
        raise ValueError(f"Invalid contract: {error}")

    # Validate style_id
    if style_id not in ALLOWED_STYLE_IDS:
        raise ValueError(
            f"Unsupported style_id {style_id!r}. "
            f"Allowed: {', '.join(sorted(ALLOWED_STYLE_IDS))}"
        )

    # Clamp dimensions
    width, height, fps = clamp_export_options(width, height, fps)

    # Generate or validate export_id
    if export_id is None:
        export_id = make_episode_export_id()
    else:
        if not validate_export_id(export_id):
            raise ValueError(
                f"Invalid export_id format: {export_id!r}. "
                "Must match ^episode_export_[a-f0-9]{12}$"
            )

    # Create output directory
    export_dir = EPISODE_EXPORT_DIR / export_id
    export_dir.mkdir(parents=True, exist_ok=True)

    # Write contract.json
    contract_path = export_dir / "contract.json"
    with open(contract_path, "w", encoding="utf-8") as f:
        json.dump(contract, f, ensure_ascii=False, indent=2)

    # Import render and export
    from render_episode_html import render_episode_stage_html_to_file
    from export_video import export_video

    # Render HTML
    html_path = export_dir / "animation.html"
    render_episode_stage_html_to_file(contract, html_path, style_id=style_id)

    # Export MP4
    mp4_path = export_dir / "output.mp4"
    export_video(
        html_path=str(html_path),
        output_path=str(mp4_path),
        fps=fps,
        width=width,
        height=height,
        headless=True,
        audio_path=None,
    )

    # Write export_meta.json
    mp4_size = mp4_path.stat().st_size if mp4_path.exists() else 0
    meta = {
        "export_id": export_id,
        "status": "completed",
        "style_id": style_id,
        "width": width,
        "height": height,
        "fps": fps,
        "html_path": str(html_path),
        "mp4_path": str(mp4_path),
        "mp4_url": f"/outputs/episode_exports/{export_id}/output.mp4",
        "html_url": f"/outputs/episode_exports/{export_id}/animation.html",
        "meta_url": f"/outputs/episode_exports/{export_id}/export_meta.json",
        "contract_url": f"/outputs/episode_exports/{export_id}/contract.json",
        "mp4_size_bytes": mp4_size,
        "audio_path": None,
        "created_at": datetime.now().isoformat(),
    }
    meta_path = export_dir / "export_meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # Write initial status.json (completed)
    write_episode_export_status(
        export_id,
        status="completed",
        progress=100,
        message="Export completed",
        result={
            "mp4_url": meta["mp4_url"],
            "html_url": meta["html_url"],
            "meta_url": meta["meta_url"],
            "contract_url": meta["contract_url"],
            "mp4_size_bytes": mp4_size,
        },
    )

    return meta
