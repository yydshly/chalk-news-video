"""Dialogue visual cues: add speaker panels and turn subtitles to render_ir.

Checkpoint 9: dialogue_visual adds a dialogue overlay layer to render_ir.
CP9.1: Harden speaker metadata reading (style.speakers is a list, not a dict).

This layer is consumed by the renderer (template.html) to show:
1. Left/right speaker cards (host/expert)
2. Active speaker highlight
3. Current turn subtitle at the bottom

The dialogue layer is derived from dialogue_manifest.turns only.
It does NOT modify semantic_ir or dialogue_manifest.

Rules:
- dialogue.enabled = true only when args.dialogue=true AND manifest has turns
- dialogue.turns strips audio_path and real voice_id values
- Speakers are named from dialogue_script.style.speakers (if available) or defaults
- Non-dialogue single-voice narration should NOT have dialogue.enabled=true
- Silent mode should NOT have dialogue.enabled=true
"""

import warnings


# Default panel layout (1280x720 canvas)
_DEFAULT_PANEL = {"x": 60, "y": 160, "w": 180, "h": 90}
_DEFAULT_EXPERT_PANEL = {"x": 1040, "y": 160, "w": 180, "h": 90}

# Default speaker names when dialogue_script is not available
_DEFAULT_SPEAKERS = {
    "host": {
        "name": "主持人",
        "role": "questioner",
        "side": "left",
        "panel": _DEFAULT_PANEL,
    },
    "expert": {
        "name": "讲解员",
        "role": "explainer",
        "side": "right",
        "panel": _DEFAULT_EXPERT_PANEL,
    },
}


def _normalize_style_speakers(dialogue_script: dict | None) -> dict:
    """Normalize dialogue_script.style.speakers to a dict keyed by speaker id.

    dialogue_script.style.speakers can be:
    - A list of {id, name, role} objects (standard format)
    - A dict {host: {...}, expert: {...}} (legacy/compat format)

    Returns:
        Dict with host/expert keys, each containing name/role/side/panel.
    """
    if dialogue_script is None:
        return dict(_DEFAULT_SPEAKERS)

    style = dialogue_script.get("style", {})
    style_speakers = style.get("speakers")

    if style_speakers is None:
        return dict(_DEFAULT_SPEAKERS)

    # Normalize to list format for uniform handling
    if isinstance(style_speakers, list):
        # Standard format: list of {id, name, role} objects
        speakers_list = style_speakers
    elif isinstance(style_speakers, dict):
        # Legacy dict format: {host: {...}, expert: {...}}
        speakers_list = [
            {"id": "host", **style_speakers.get("host", {})},
            {"id": "expert", **style_speakers.get("expert", {})},
        ]
    else:
        warnings.warn(
            f"style.speakers is neither list nor dict (type={type(style_speakers).__name__}), "
            f"using defaults"
        )
        return dict(_DEFAULT_SPEAKERS)

    # Build result dict from list
    result = {}
    for item in speakers_list:
        if not isinstance(item, dict):
            continue
        sid = item.get("id", "")
        if sid not in ("host", "expert"):
            warnings.warn(f"Unknown speaker id '{sid}' in style.speakers, skipping")
            continue
        default = _DEFAULT_SPEAKERS[sid]
        result[sid] = {
            "name": item.get("name") or default["name"],
            "role": item.get("role") or default["role"],
            "side": item.get("side") or default["side"],
            "panel": {
                "x": item.get("panel", {}).get("x") or default["panel"]["x"],
                "y": item.get("panel", {}).get("y") or default["panel"]["y"],
                "w": item.get("panel", {}).get("w") or default["panel"]["w"],
                "h": item.get("panel", {}).get("h") or default["panel"]["h"],
            },
        }

    # Ensure both host and expert are present
    for key in ("host", "expert"):
        if key not in result:
            result[key] = dict(_DEFAULT_SPEAKERS[key])

    return result


def apply_dialogue_visual_cues(
    render_ir: dict,
    dialogue_manifest: dict,
    dialogue_script: dict | None = None,
) -> dict:
    """Add dialogue visual cues to render_ir.

    Args:
        render_ir: render_ir dict to augment
        dialogue_manifest: dialogue_manifest dict (must have turns)
        dialogue_script: optional dialogue_script dict for speaker names

    Returns:
        render_ir with render_ir["dialogue"] added

    Raises:
        ValueError: if dialogue_manifest has no turns
    """
    manifest_turns = dialogue_manifest.get("turns")
    if manifest_turns is None:
        raise ValueError(
            "dialogue_manifest has no turns — cannot apply dialogue visual cues"
        )

    if not isinstance(manifest_turns, list) or len(manifest_turns) == 0:
        raise ValueError(
            f"dialogue_manifest turns is empty or invalid — cannot apply dialogue visual cues"
        )

    # Resolve speaker names and panel layout from dialogue_script
    speakers = _normalize_style_speakers(dialogue_script)

    # Build clean turns list for render_ir (strip audio_path and voice fields)
    clean_turns = []
    for turn in manifest_turns:
        speaker = turn.get("speaker", "host")
        # Warn on unknown speaker, but allow through (fallback to host visual)
        if speaker not in ("host", "expert"):
            warnings.warn(
                f"Unknown turn speaker '{speaker}' at turn {turn.get('turn_id')}, "
                f"treating as host for visual purposes"
            )
            speaker = "host"

        clean_turn = {
            "turn_id": turn.get("turn_id", ""),
            "speaker": speaker,
            "beat_id": turn.get("beat_id", ""),
            "reveal": turn.get("reveal", ""),
            "text": turn.get("text", ""),
            "start": round(float(turn.get("start", 0.0)), 3),
            "duration": round(float(turn.get("duration", 0.0)), 3),
            "end": round(float(turn.get("end", 0.0)), 3),
        }
        # Explicitly do NOT include audio_path or voice/voice_id
        clean_turns.append(clean_turn)

    render_ir = dict(render_ir)
    render_ir["dialogue"] = {
        "enabled": True,
        "style": "podcast_overlay_v1",
        "speakers": speakers,
        "turns": clean_turns,
    }

    return render_ir
