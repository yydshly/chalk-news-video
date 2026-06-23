"""Dialogue visual cues: add speaker panels and turn subtitles to render_ir.

Checkpoint 9: dialogue_visual adds a dialogue overlay layer to render_ir.

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

from .utils import load_json


# Default speaker names when dialogue_script is not available
DEFAULT_SPEAKERS = {
    "host": {
        "name": "主持人",
        "role": "questioner",
        "side": "left",
    },
    "expert": {
        "name": "讲解员",
        "role": "explainer",
        "side": "right",
    },
}


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

    # Resolve speaker names from dialogue_script.style.speakers
    speakers = {}
    if dialogue_script:
        style_speakers = dialogue_script.get("style", {}).get("speakers", {})
        for key, default in DEFAULT_SPEAKERS.items():
            if key in style_speakers:
                sp = style_speakers[key]
                speakers[key] = {
                    "name": sp.get("name", default["name"]),
                    "role": sp.get("role", default["role"]),
                    "side": sp.get("side", default["side"]),
                }
            else:
                speakers[key] = default
    else:
        speakers = dict(DEFAULT_SPEAKERS)

    # Build clean turns list for render_ir (strip audio_path and voice fields)
    clean_turns = []
    for turn in manifest_turns:
        clean_turn = {
            "turn_id": turn.get("turn_id", ""),
            "speaker": turn.get("speaker", "host"),
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
