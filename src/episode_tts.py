"""Experimental TTS narration helper (CP56).

.. deprecated:: This module is not part of the stable CP53.2 capability surface.
   Formal TTS integration is planned for a later checkpoint.

Builds a broadcast-style narration script from an episode_template_v1 contract
and synthesizes it into a single WAV using a real TTS provider (MiniMax by default).

The produced WAV lands under outputs/episode_audio/<audio_id>.wav and is exposed
at the server-relative URL /outputs/episode_audio/<audio_id>.wav, which is exactly
the shape that episode_export.resolve_safe_audio_url() accepts for muxing.

This is the first real-TTS step: no LLM rewriting yet — narration text is derived
directly from the contract's existing headlines/titles.
"""

from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EPISODE_AUDIO_DIR = PROJECT_ROOT / "outputs" / "episode_audio"

AUDIO_ID_PATTERN = re.compile(r"^episode_audio_[a-f0-9]{12}$")


def make_episode_audio_id() -> str:
    return "episode_audio_" + uuid.uuid4().hex[:12]


def validate_audio_id(audio_id: str) -> bool:
    return bool(AUDIO_ID_PATTERN.match(audio_id))


def _clean(text: Any) -> str:
    """Collapse whitespace and strip; return '' for falsy/non-str."""
    if not text:
        return ""
    s = str(text).strip()
    return re.sub(r"\s+", " ", s)


def build_narration_script(contract: dict) -> list[dict]:
    """Build an ordered list of narration segments from an episode contract.

    Each segment is {"section": <id>, "text": <str>}. The concatenated text is
    what gets synthesized. Segments are also returned so callers can show the
    script in the UI / build subtitles later.
    """
    episode = contract.get("episode") or {}
    sections = contract.get("sections") or {}

    segments: list[dict] = []

    # Opening — CP61: prefer an LLM-written narration script; else fall back to titles.
    opening = sections.get("opening") or {}
    opening_narration = _clean(opening.get("narration"))
    if opening_narration:
        segments.append({"section": "opening", "text": opening_narration})
    else:
        opening_text = _clean(opening.get("title")) or _clean(episode.get("title"))
        subtitle = _clean(episode.get("subtitle"))
        if opening_text:
            lead_in = opening_text
            if subtitle and subtitle not in opening_text:
                lead_in = f"{opening_text}。{subtitle}"
            segments.append({"section": "opening", "text": f"{lead_in}。"})

    # News cards — CP61: prefer per-card narration; else headline + broadcast connective.
    cards = sections.get("news_cards") or []
    ordered = sorted(
        [c for c in cards if isinstance(c, dict)],
        key=lambda c: c.get("order", 0),
    )
    connectives = ["首先", "接下来", "另外", "此外", "最后"]
    for idx, card in enumerate(ordered):
        narration = _clean(card.get("narration"))
        section_key = card.get("section_id") or f"card_{idx}"
        if narration:
            segments.append({"section": section_key, "text": narration})
            continue
        headline = _clean(card.get("headline"))
        if not headline:
            continue
        if card.get("role") == "lead":
            prefix = "先看今天的重点。"
        else:
            prefix = (connectives[idx] + "，") if idx < len(connectives) else ""
        segments.append({"section": section_key, "text": f"{prefix}{headline}。"})

    # Closing — CP61: prefer narration; else closing title.
    closing = sections.get("closing") or {}
    closing_narration = _clean(closing.get("narration"))
    if closing_narration:
        segments.append({"section": "closing", "text": closing_narration})
    else:
        closing_text = _clean(closing.get("title"))
        if closing_text:
            segments.append({"section": "closing", "text": f"{closing_text}。"})

    return segments


def synthesize_episode_narration(
    contract: dict,
    *,
    profile: str = "minimax_speech",
    speed: float = 1.0,
    audio_id: Optional[str] = None,
) -> dict[str, Any]:
    """Synthesize episode narration to a WAV under outputs/episode_audio/.

    Returns a dict with audio_url (server-relative /outputs/...), audio_path,
    duration, voice, the full script text, and the per-section segments.

    Raises ValueError on an empty/invalid script, RuntimeError on TTS failure
    (propagated from the provider).
    """
    if not isinstance(contract, dict):
        raise ValueError("contract must be an object")

    segments = build_narration_script(contract)
    full_text = " ".join(seg["text"] for seg in segments).strip()
    if not full_text:
        raise ValueError("No narratable text found in contract")

    if audio_id is None:
        audio_id = make_episode_audio_id()
    elif not validate_audio_id(audio_id):
        raise ValueError(f"Invalid audio_id format: {audio_id!r}")

    EPISODE_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    out_path = EPISODE_AUDIO_DIR / f"{audio_id}.wav"

    # Lazy import so module import stays cheap and TTS config errors surface here.
    from src.tts.client import create_tts_client

    client = create_tts_client(profile)
    result = client.synthesize(full_text, out_path, speed=speed)

    return {
        "audio_id": audio_id,
        "audio_url": f"/outputs/episode_audio/{audio_id}.wav",
        "audio_path": str(out_path),
        "duration": result.get("duration"),
        "voice": result.get("voice"),
        "provider": result.get("provider"),
        "profile": profile,
        "script": full_text,
        "segments": segments,
        "size_bytes": out_path.stat().st_size if out_path.exists() else 0,
    }
