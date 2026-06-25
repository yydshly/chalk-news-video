"""Episode Export Service Layer (CP40.2-CP40.6).

CP40.2: export_episode_contract_to_mp4() — synchronous export.
CP40.3: async job status via status.json + background thread.
CP40.6: optional audio mux from safe local /outputs/ artifact URLs.

No real LLM, no real TTS.
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

# Allowed audio file extensions for episode export muxing
ALLOWED_AUDIO_EXTENSIONS = frozenset([".wav", ".mp3", ".m4a", ".aac"])

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


def resolve_safe_audio_url(audio_url: Optional[str]) -> Optional[Path]:
    """Resolve a server-relative audio URL to a safe local Path.

    Security rules:
    - None or empty string → None
    - Must start with /outputs/
    - No http://, https://, file://
    - No backslash paths (Windows absolute paths)
    - No path traversal (..)
    - No query string or hash fragment
    - Extension must be in ALLOWED_AUDIO_EXTENSIONS
    - Resolved path must stay within PROJECT_ROOT/outputs/
    - Must be an existing file (not directory)

    Returns None if audio_url is None/empty.
    Raises ValueError on any security violation.
    """
    if not audio_url:
        return None

    # Reject external/protocol URLs
    if "://" in audio_url:
        raise ValueError("External audio URLs are not allowed")

    # Reject Windows absolute paths
    if "\\" in audio_url:
        raise ValueError("Backslash paths are not allowed")

    # Strip query string and hash fragment
    clean = audio_url.split("?", 1)[0].split("#", 1)[0]

    if not clean.startswith("/outputs/"):
        raise ValueError("audio_url must start with /outputs/")

    # Reject path traversal
    parts = Path(clean).parts
    if ".." in parts:
        raise ValueError("Path traversal is not allowed")

    # Check extension
    ext = Path(clean).suffix.lower()
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise ValueError(f"Unsupported audio format: {ext}. Allowed: {', '.join(sorted(ALLOWED_AUDIO_EXTENSIONS))}")

    # Resolve to local path
    rel = clean.lstrip("/")
    local_path = (PROJECT_ROOT / rel).resolve()
    outputs_root = (PROJECT_ROOT / "outputs").resolve()

    # Ensure path is under outputs/
    if not str(local_path).startswith(str(outputs_root) + str(local_path.anchor)):
        # More precise: check relative to outputs root using separator
        sep = local_path.anchor
        local_str = str(local_path)
        outputs_str = str(outputs_root)
        if not (local_str == outputs_str or local_str.startswith(outputs_str + sep)):
            raise ValueError("audio_url is outside outputs directory")

    # Alternative simpler check: ensure the resolved path starts with outputs root
    try:
        local_path_str = str(local_path)
        outputs_str = str(outputs_root)
        if not (local_path_str == outputs_str or local_path_str.startswith(outputs_str + "/") or local_path_str.startswith(outputs_str + "\\")):
            # Check if it's exactly equal to outputs root (a directory, not allowed)
            if local_path == outputs_root:
                raise ValueError("audio_url must be a file, not a directory")
            if not local_path_str.startswith(outputs_str):
                raise ValueError("audio_url is outside outputs directory")
    except ValueError:
        raise
    except Exception:
        raise ValueError("audio_url is outside outputs directory")

    if not local_path.is_file():
        raise ValueError("audio file not found")

    return local_path


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
    has_audio: Optional[bool] = None,
    audio_url: Optional[str] = None,
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

    # Merge with new values — passed value wins over existing
    data = {
        "export_id": export_id,
        "status": status,
        "message": message,
        "progress": progress,
        "style_id": style_id if style_id is not None else existing.get("style_id"),
        "width": width if width is not None else existing.get("width"),
        "height": height if height is not None else existing.get("height"),
        "fps": fps if fps is not None else existing.get("fps"),
        "created_at": existing.get("created_at", now),
        "updated_at": now,
        "result": result,
        "error_type": error_type,
        "error_message": error_message,
        "has_audio": has_audio if has_audio is not None else existing.get("has_audio"),
        "audio_url": audio_url if audio_url is not None else existing.get("audio_url"),
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
    safe_audio_path: Optional[Path] = None,
) -> None:
    """Background worker: renders HTML and exports MP4.

    Updates status.json at each step.
    All errors are caught and redacted before writing to status.json.

    Args:
        safe_audio_path: resolved local Path to audio file, or None for no audio mux.
    """
    has_audio = safe_audio_path is not None
    audio_size = 0
    if safe_audio_path and safe_audio_path.exists():
        try:
            audio_size = safe_audio_path.stat().st_size
        except Exception:
            pass

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
            style_id=style_id,
            width=width,
            height=height,
            fps=fps,
            has_audio=has_audio,
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
            style_id=style_id,
            width=width,
            height=height,
            fps=fps,
            has_audio=has_audio,
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
            audio_path=str(safe_audio_path) if safe_audio_path else None,
        )

        write_episode_export_status(
            export_id,
            status="running",
            progress=90,
            message="Writing metadata",
            style_id=style_id,
            width=width,
            height=height,
            fps=fps,
            has_audio=has_audio,
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
            "has_audio": has_audio,
            "audio_url": str(safe_audio_path) if safe_audio_path else None,
            "audio_size_bytes": audio_size if has_audio else None,
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
                "has_audio": has_audio,
            },
            style_id=style_id,
            width=width,
            height=height,
            fps=fps,
            has_audio=has_audio,
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
            style_id=style_id,
            width=width,
            height=height,
            fps=fps,
            has_audio=has_audio,
        )


def start_episode_export_background(
    contract: dict,
    *,
    style_id: str = "breaking_news_v1",
    width: int = 720,
    height: int = 1280,
    fps: int = 30,
    audio_url: Optional[str] = None,
) -> dict[str, Any]:
    """Start an async episode export in a background thread.

    Writes initial status.json and launches a daemon thread.
    Returns immediately with export_id and URLs.

    Args:
        audio_url: optional server-relative URL to a local audio file (e.g. /outputs/jobs/.../dialogue.wav).
                   Must pass resolve_safe_audio_url() validation. None means no audio mux.
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

    # Resolve audio_url to safe local path (raises ValueError on invalid)
    safe_audio_path = resolve_safe_audio_url(audio_url)

    # Clamp dimensions
    width, height, fps = clamp_export_options(width, height, fps)

    # Generate export_id and create directory
    export_id = make_episode_export_id()
    export_dir = EPISODE_EXPORT_DIR / export_id
    export_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now().isoformat()

    # Determine audio info for status/meta
    has_audio = safe_audio_path is not None
    audio_size = 0
    if safe_audio_path and safe_audio_path.exists():
        try:
            audio_size = safe_audio_path.stat().st_size
        except Exception:
            pass

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
        has_audio=has_audio,
        audio_url=audio_url,
    )

    # Launch background thread
    thread = threading.Thread(
        target=_run_episode_export_worker,
        args=(export_id, contract, style_id, width, height, fps, safe_audio_path),
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
        "has_audio": has_audio,
        "audio_url": audio_url,
        "created_at": now,
    }


# ---------------------------------------------------------------------------
# Episode export history / summary (CP40.5)
# ---------------------------------------------------------------------------

def get_episode_export_summary(export_id: str) -> Optional[dict]:
    """Return a summary dict for an episode export, or None if not found.

    Reads status.json and export_meta.json from the export directory.
    """
    if not validate_export_id(export_id):
        return None

    export_dir = EPISODE_EXPORT_DIR / export_id
    if not export_dir.is_dir():
        return None

    status_path = export_dir / "status.json"
    meta_path = export_dir / "export_meta.json"

    status_data = None
    if status_path.exists():
        try:
            status_data = json.loads(status_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    meta_data = None
    if meta_path.exists():
        try:
            meta_data = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    if status_data is None and meta_data is None:
        return None

    # Determine effective status
    status = status_data.get("status", "unknown") if status_data else "unknown"

    # MP4 and HTML presence
    mp4_path = export_dir / "output.mp4"
    html_path = export_dir / "animation.html"

    mp4_size = 0
    if mp4_path.exists():
        try:
            mp4_size = mp4_path.stat().st_size
        except Exception:
            pass

    result = {
        "export_id": export_id,
        "status": status,
        "progress": status_data.get("progress") if status_data else None,
        "message": status_data.get("message") if status_data else None,
        "error_message": status_data.get("error_message") if status_data else None,
        "style_id": status_data.get("style_id") if status_data else (meta_data.get("style_id") if meta_data else None),
        "width": status_data.get("width") if status_data else (meta_data.get("width") if meta_data else None),
        "height": status_data.get("height") if status_data else (meta_data.get("height") if meta_data else None),
        "fps": status_data.get("fps") if status_data else (meta_data.get("fps") if meta_data else None),
        "created_at": status_data.get("created_at") if status_data else (meta_data.get("created_at") if meta_data else None),
        "updated_at": status_data.get("updated_at") if status_data else None,
        "mp4_url": f"/outputs/episode_exports/{export_id}/output.mp4",
        "html_url": f"/outputs/episode_exports/{export_id}/animation.html",
        "status_url": f"/api/episode/exports/{export_id}",
        "meta_url": f"/outputs/episode_exports/{export_id}/export_meta.json",
        "contract_url": f"/outputs/episode_exports/{export_id}/contract.json",
        "mp4_size_bytes": mp4_size,
        "has_mp4": mp4_path.exists(),
        "has_html": html_path.exists(),
        "has_meta": meta_path.exists(),
        "has_contract": (export_dir / "contract.json").exists(),
        "has_status": status_path.exists(),
    }

    # Fill mp4_size from meta if available and mp4 doesn't exist yet
    if mp4_size == 0 and meta_data and meta_data.get("mp4_size_bytes"):
        result["mp4_size_bytes"] = meta_data["mp4_size_bytes"]

    return result


def list_episode_exports(limit: int = 50) -> list[dict]:
    """List recent episode export summaries, sorted by updated_at descending.

    Only returns exports whose directory name matches validate_export_id().
    Skips directories that can't be read without raising errors.
    """
    if not EPISODE_EXPORT_DIR.is_dir():
        return []

    limit = max(1, min(limit, 200))

    items = []
    for export_dir in EPISODE_EXPORT_DIR.iterdir():
        if not export_dir.is_dir():
            continue

        export_id = export_dir.name
        if not validate_export_id(export_id):
            continue

        try:
            summary = get_episode_export_summary(export_id)
            if summary is None:
                continue
            items.append(summary)
        except Exception:
            continue

    # Sort by updated_at descending, then by export_id for stability
    def sort_key(item):
        updated = item.get("updated_at") or item.get("created_at") or ""
        return (updated, item["export_id"])

    items.sort(key=sort_key, reverse=True)

    return items[:limit]


def delete_episode_export(export_id: str) -> dict:
    """Delete an episode export directory.

    Only allows deleting completed/failed/unknown exports.
    Rejects running/pending exports.

    Returns {"ok": True, "deleted": True, "export_id": ..., "summary": ...} on success.
    Returns {"ok": False, "error": ..., "export_id": ...} on failure.
    """
    if not validate_export_id(export_id):
        return {"ok": False, "error": "Invalid export_id format", "export_id": export_id}

    export_dir = EPISODE_EXPORT_DIR / export_id
    if not export_dir.is_dir():
        return {"ok": False, "error": "Export directory not found", "export_id": export_id}

    # Security: resolve path and ensure it's under EPISODE_EXPORT_DIR
    try:
        resolved = export_dir.resolve()
        base_resolved = EPISODE_EXPORT_DIR.resolve()
        if not str(resolved).startswith(str(base_resolved)):
            return {"ok": False, "error": "Path traversal rejected", "export_id": export_id}
    except Exception:
        return {"ok": False, "error": "Invalid path", "export_id": export_id}

    # Check current status — reject running/pending
    summary = get_episode_export_summary(export_id)
    if summary and summary["status"] in ("running", "pending"):
        return {
            "ok": False,
            "error": f"Cannot delete export with status '{summary['status']}'",
            "export_id": export_id,
        }

    # Get summary before deletion for the return value
    deleted_summary = summary

    # Perform deletion
    import shutil
    try:
        shutil.rmtree(export_dir)
    except Exception as e:
        return {"ok": False, "error": f"Failed to delete directory: {e}", "export_id": export_id}

    return {
        "ok": True,
        "deleted": True,
        "export_id": export_id,
        "summary": deleted_summary,
    }


def cleanup_episode_exports(keep_latest: int = 30, dry_run: bool = False) -> dict:
    """Clean up old episode exports, keeping the most recent `keep_latest` completed/failed/unknown exports.

    Running and pending exports are never deleted.
    """
    keep_latest = max(1, min(keep_latest, 200))

    all_exports = list_episode_exports(limit=1000)

    # Separate into to_delete and to_skip
    to_delete = []
    to_skip = []

    for export in all_exports:
        if export["status"] in ("running", "pending"):
            to_skip.append({"export_id": export["export_id"], "reason": export["status"]})
        else:
            to_delete.append(export)

    # Keep the most recent `keep_latest`
    keep_list = to_delete[:keep_latest]
    delete_list = to_delete[keep_latest:]

    deleted = []
    errors = []

    if not dry_run:
        for export in delete_list:
            result = delete_episode_export(export["export_id"])
            if result.get("ok"):
                deleted.append({
                    "export_id": export["export_id"],
                    "status": export["status"],
                    "mp4_size_bytes": export.get("mp4_size_bytes"),
                })
            else:
                errors.append({"export_id": export["export_id"], "error": result.get("error")})

    return {
        "ok": True,
        "keep_latest": keep_latest,
        "dry_run": dry_run,
        "deleted_count": len(deleted),
        "deleted": deleted,
        "errors": errors,
        "skipped": to_skip,
        "total_kept": len(keep_list),
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
    audio_url: Optional[str] = None,
    export_id: Optional[str] = None,
) -> dict[str, Any]:
    """Export an episode contract to MP4 (synchronous).

    Kept for backward compatibility with CP40.2 scripts.
    Prefer start_episode_export_background() for async use.

    Args:
        audio_url: optional server-relative URL to a local audio file.
                    Must pass resolve_safe_audio_url() validation. None means no audio mux.
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

    # Resolve audio_url to safe local path (raises ValueError on invalid)
    safe_audio_path = resolve_safe_audio_url(audio_url)
    has_audio = safe_audio_path is not None

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
        audio_path=str(safe_audio_path) if safe_audio_path else None,
    )

    # Write export_meta.json
    mp4_size = mp4_path.stat().st_size if mp4_path.exists() else 0
    audio_size = 0
    if safe_audio_path and safe_audio_path.exists():
        try:
            audio_size = safe_audio_path.stat().st_size
        except Exception:
            pass

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
        "has_audio": has_audio,
        "audio_url": audio_url,
        "audio_size_bytes": audio_size if has_audio else None,
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
            "has_audio": has_audio,
        },
        style_id=style_id,
        width=width,
        height=height,
        fps=fps,
        has_audio=has_audio,
        audio_url=audio_url,
    )

    return meta
