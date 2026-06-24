"""Episode Export Service Layer (CP40.2).

Provides export_episode_contract_to_mp4() which:
1. Creates an isolated output directory under outputs/episode_exports/{export_id}/
2. Writes the contract.json
3. Renders animation.html via render_episode_stage_html_to_file()
4. Exports MP4 via export_video.export_video()
5. Writes export_meta.json
6. Returns result dict

No real LLM, no real TTS, no audio mux.
"""

from __future__ import annotations

import json
import re
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


def _validate_contract(contract: dict) -> tuple[bool, Optional[str]]:
    """Validate the episode contract structure.

    Returns (is_valid, error_message).
    """
    if not isinstance(contract, dict):
        return False, "contract must be an object"

    # Must have episode_template_v1 schema
    schema = contract.get("schema_version")
    if schema != "episode_template_v1":
        return False, f"schema_version must be 'episode_template_v1', got {schema!r}"

    template_id = contract.get("template_id")
    if template_id and template_id != "breaking_news_v1":
        return False, f"template_id must be 'breaking_news_v1', got {template_id!r}"

    return True, None


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
    """Export an episode contract to MP4.

    Args:
        contract: episode_template_v1 contract dict.
        style_id: Style identifier (only 'breaking_news_v1' in CP40.2).
        width: Video width in pixels (360-1080).
        height: Video height in pixels (640-1920).
        fps: Frames per second (1-30).
        audio_path: Not used in CP40.2 (must be None).
        export_id: Optional pre-specified export ID. If None, one is generated.

    Returns:
        Result dict with export_id, status, paths, and URLs.
    """
    # Enforce audio_path=None for CP40.2
    if audio_path is not None:
        audio_path = None  # explicitly ignore — no real audio in CP40.2

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
                "Must match ^episode_export_[a-f0-9]{{12}}$"
            )

    # Create output directory
    export_dir = EPISODE_EXPORT_DIR / export_id
    export_dir.mkdir(parents=True, exist_ok=True)

    # Write contract.json
    contract_path = export_dir / "contract.json"
    with open(contract_path, "w", encoding="utf-8") as f:
        json.dump(contract, f, ensure_ascii=False, indent=2)

    # Import render and export (defer to avoid circular imports / heavy deps at module load)
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

    return meta
