"""Text-to-image generation via MiniMax T2I (CP62 — illustrated explainer).

Generates one illustration per episode scene (opening + each news card + closing)
using MiniMax's image_generation API, downloads them locally under
outputs/episode_images/<image_id>/, and embeds the local paths back into the
contract so the illustrated_v1 renderer can base64-embed them into a
self-contained HTML (works in both preview and Playwright export).

Endpoint/credentials come from .env (MINIMAX_API_KEY, MINIMAX_BASE_URL), the same
ones the LLM/TTS already use. No keys are hardcoded.
"""

from __future__ import annotations

import base64
import os
import uuid
from pathlib import Path
from typing import Any, Optional

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EPISODE_IMAGES_DIR = PROJECT_ROOT / "outputs" / "episode_images"

# A consistent visual style applied to every scene so the whole video looks coherent.
DEFAULT_STYLE_PREFIX = (
    "扁平极简矢量信息图插画，统一的蓝紫色调，简洁现代，柔和光感，"
    "新闻科普解说风格，画面中不要出现任何文字或字母，"
)

ALLOWED_ASPECT = {"16:9", "1:1", "9:16"}


def make_image_id() -> str:
    return "img_" + uuid.uuid4().hex[:12]


def _resolve_minimax() -> tuple[str, str]:
    """Return (api_key, image_generation_endpoint). Raises if unconfigured."""
    from src.config_loader import load_env_file
    load_env_file(PROJECT_ROOT / ".env")
    key = (os.environ.get("MINIMAX_API_KEY") or "").strip()
    base = (os.environ.get("MINIMAX_BASE_URL") or "https://api.minimaxi.com/v1").strip().rstrip("/")
    if not key:
        raise RuntimeError("MINIMAX_API_KEY not configured")
    return key, base + "/image_generation"


def generate_image_bytes(
    prompt: str,
    *,
    aspect_ratio: str = "16:9",
    model: str = "image-01",
    timeout: int = 60,
) -> bytes:
    """Generate a single image and return its bytes. Raises on failure."""
    if aspect_ratio not in ALLOWED_ASPECT:
        aspect_ratio = "16:9"
    key, endpoint = _resolve_minimax()
    payload = {
        "model": model,
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "response_format": "url",
        "n": 1,
        "prompt_optimizer": True,
    }
    resp = requests.post(
        endpoint,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json=payload,
        timeout=timeout,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"[t2i] HTTP {resp.status_code}")
    data = resp.json()
    base_resp = data.get("base_resp", {})
    if base_resp.get("status_code") not in (0, None):
        raise RuntimeError(f"[t2i] API error {base_resp.get('status_code')}: {base_resp.get('status_msg')}")
    urls = (data.get("data") or {}).get("image_urls") or []
    if not urls:
        raise RuntimeError("[t2i] response missing image_urls")
    img = requests.get(urls[0], timeout=timeout)
    if img.status_code != 200 or not img.content:
        raise RuntimeError("[t2i] failed to download generated image")
    return img.content


def _scene_prompt(card: dict) -> str:
    """Build an illustration prompt for a card: prefer LLM image_prompt, else content."""
    explicit = str(card.get("image_prompt") or "").strip()
    if explicit:
        body = explicit
    else:
        headline = str(card.get("headline") or "").strip()
        summary = str(card.get("description") or card.get("summary") or "").strip()
        body = (headline + "。" + summary).strip("。")
    return DEFAULT_STYLE_PREFIX + "画面内容：" + body


def generate_contract_images(
    contract: dict,
    *,
    aspect_ratio: str = "16:9",
    image_id: Optional[str] = None,
) -> dict[str, Any]:
    """Generate one illustration per news card and embed local paths into the contract.

    Mutates and returns {"image_id", "count", "contract"}. Each news_card gets
    `image_path` (local) and `image_url` (/outputs/...). Raises on first failure
    (caller decides fallback — e.g. render without illustrations).
    """
    if not isinstance(contract, dict):
        raise ValueError("contract must be an object")
    sections = contract.get("sections") or {}
    cards = sections.get("news_cards") or []
    if not cards:
        raise ValueError("contract has no news_cards to illustrate")

    image_id = image_id or make_image_id()
    out_dir = EPISODE_IMAGES_DIR / image_id
    out_dir.mkdir(parents=True, exist_ok=True)

    def _gen_one(idx: int, card: dict) -> tuple[int, Optional[str]]:
        """Generate + save one scene's image. Returns (idx, filename|None).

        T2I is flaky — retry a few times; a single scene failing must not abort
        the batch (that scene just gets a placeholder in the renderer).
        """
        prompt = _scene_prompt(card)
        for _ in range(3):
            try:
                img = generate_image_bytes(prompt, aspect_ratio=aspect_ratio)
                fname = f"card_{idx + 1:02d}.jpg"
                (out_dir / fname).write_bytes(img)
                return idx, fname
            except Exception:
                continue
        return idx, None

    # Generate all scenes concurrently — cuts N×~30s down to ~one image's time.
    import concurrent.futures
    results: dict[int, Optional[str]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, len(cards))) as ex:
        for idx, fname in ex.map(lambda p: _gen_one(*p), list(enumerate(cards))):
            results[idx] = fname

    count = 0
    failed = 0
    for i, card in enumerate(cards):
        fname = results.get(i)
        if fname:
            card["image_path"] = str(out_dir / fname)
            card["image_url"] = f"/outputs/episode_images/{image_id}/{fname}"
            count += 1
        else:
            failed += 1

    if count == 0:
        raise RuntimeError("all scene illustrations failed to generate")

    contract["image_id"] = image_id
    contract["has_illustrations"] = True
    return {"image_id": image_id, "count": count, "failed": failed, "contract": contract}


def image_path_to_data_uri(path: str | Path) -> str:
    """Read a local image file and return a base64 data URI (for self-contained HTML)."""
    p = Path(path)
    raw = p.read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64,{b64}"
