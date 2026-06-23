"""Narration timing: sync render_ir.timeline to narration_manifest timing.

Checkpoint 6.1: Audio timing is the source of truth for the render timeline.

In TTS mode, narration_manifest.beats provides the real audio timing (start/duration/end).
We use this to overwrite render_ir.timeline entries so the animation plays in sync
with the actual audio.

Contract:
- semantic_ir: semantic/structural contract (beat_id, reveal, narration text)
- narration_manifest: audio timing contract (beat_id, start, duration, end from real TTS)
- render_ir.timeline: final render timing (beat_id, at, duration — MUST match manifest)
"""

import warnings


def apply_narration_timing(render_ir: dict, narration_manifest: dict) -> dict:
    """Sync render_ir.timeline to use narration_manifest timing.

    For each beat in render_ir.timeline, look up the matching beat in
    narration_manifest.beats by beat_id and use its start/duration.

    Args:
        render_ir: render_ir dict with timeline list
        narration_manifest: narration_manifest dict with beats list

    Returns:
        render_ir with synced timeline and total_duration

    Raises:
        ValueError: if a timeline beat_id is not found in narration_manifest
    """
    manifest_beats = {b["beat_id"]: b for b in narration_manifest.get("beats", [])}

    timeline = render_ir.get("timeline", [])
    synced_timeline = []
    missing_beat_ids = []

    for item in timeline:
        beat_id = item.get("beat_id")
        if beat_id not in manifest_beats:
            missing_beat_ids.append(beat_id)
            synced_timeline.append(item)
            continue

        manifest_beat = manifest_beats[beat_id]
        synced_item = dict(item)
        synced_item["at"] = round(manifest_beat["start"], 3)
        synced_item["duration"] = round(manifest_beat["duration"], 3)
        synced_timeline.append(synced_item)

    if missing_beat_ids:
        raise ValueError(
            f"timeline beat_id(s) not found in narration_manifest: {missing_beat_ids}"
        )

    # Warn about manifest beats not in timeline (allowed per spec)
    manifest_only_beat_ids = set(manifest_beats.keys()) - {item["beat_id"] for item in timeline}
    if manifest_only_beat_ids:
        warnings.warn(
            f"manifest beats not in timeline (silence/intro beats?): {sorted(manifest_only_beat_ids)}"
        )

    render_ir = dict(render_ir)
    render_ir["timeline"] = synced_timeline
    render_ir["total_duration"] = round(narration_manifest.get("total_duration", 0.0), 3)

    return render_ir
