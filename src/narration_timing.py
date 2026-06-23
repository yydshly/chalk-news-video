"""Narration timing: sync render_ir.timeline to narration/dialogue manifest timing.

Checkpoint 6.1: Audio timing is the source of truth for the render timeline.
Checkpoint 7.1: dialogue_manifest uses turns (not beats) as the primary structure.

In TTS mode, the manifest provides real audio timing (start/duration/end).
We use this to overwrite render_ir.timeline entries so the animation plays in sync
with the actual audio.

Two manifest structures are supported:
1. narration_manifest: has "beats" list with beat-level timing
2. dialogue_manifest: has "turns" list aggregated by beat_id

Contract:
- semantic_ir: semantic/structural contract (beat_id, reveal, narration text)
- manifest: audio timing contract (beats or turns with start/duration/end)
- render_ir.timeline: final render timing (beat_id, at, duration — MUST match manifest)
"""

import warnings
from collections import defaultdict


def _sync_from_beats(render_ir: dict, manifest_beats: list[dict]) -> dict:
    """Sync timeline using a beats-list manifest (old narration_manifest path)."""
    beat_map = {b["beat_id"]: b for b in manifest_beats}
    timeline = render_ir.get("timeline", [])
    synced_timeline = []
    missing_beat_ids = []

    for item in timeline:
        beat_id = item.get("beat_id")
        if beat_id not in beat_map:
            missing_beat_ids.append(beat_id)
            synced_timeline.append(item)
            continue

        manifest_beat = beat_map[beat_id]
        synced_item = dict(item)
        synced_item["at"] = round(manifest_beat["start"], 3)
        synced_item["duration"] = round(manifest_beat["duration"], 3)
        synced_timeline.append(synced_item)

    if missing_beat_ids:
        raise ValueError(
            f"timeline beat_id(s) not found in manifest: {missing_beat_ids}"
        )

    return synced_timeline


def _sync_from_turns(render_ir: dict, manifest_turns: list[dict]) -> dict:
    """Sync timeline using a turns-list manifest (dialogue_manifest path).

    Aggregation rules:
    - Group turns by beat_id
    - timeline_item.at = first turn's start for that beat_id
    - timeline_item.duration = last turn's end - first turn's start (total span)
    - Uncovered beat_ids → ValueError
    - Turns covering beats not in timeline → warning
    """
    # Group turns by beat_id, preserving order within each beat
    turns_by_beat = defaultdict(list)
    for turn in manifest_turns:
        bid = turn.get("beat_id", "")
        if bid:
            turns_by_beat[bid].append(turn)

    timeline = render_ir.get("timeline", [])
    synced_timeline = []
    missing_beat_ids = []

    for item in timeline:
        beat_id = item.get("beat_id")
        if beat_id not in turns_by_beat:
            missing_beat_ids.append(beat_id)
            synced_timeline.append(item)
            continue

        turns_for_beat = turns_by_beat[beat_id]
        first_start = turns_for_beat[0]["start"]
        last_end = max(t["end"] for t in turns_for_beat)

        synced_item = dict(item)
        synced_item["at"] = round(first_start, 3)
        synced_item["duration"] = round(last_end - first_start, 3)
        synced_timeline.append(synced_item)

    if missing_beat_ids:
        raise ValueError(
            f"timeline beat_id(s) not found in dialogue_manifest turns: {missing_beat_ids}"
        )

    # Warn about turns covering beats not in timeline (allowed per spec)
    timeline_beat_ids = {item["beat_id"] for item in timeline}
    turns_beat_ids = set(turns_by_beat.keys())
    extra_beat_ids = turns_beat_ids - timeline_beat_ids
    if extra_beat_ids:
        warnings.warn(
            f"dialogue_manifest turns cover beats not in timeline: {sorted(extra_beat_ids)}"
        )

    return synced_timeline


def apply_narration_timing(render_ir: dict, manifest: dict) -> dict:
    """Sync render_ir.timeline to use audio manifest timing.

    Supports two manifest structures:
    - "beats" key: narration_manifest (old path)
    - "turns" key: dialogue_manifest (CP7.1 path)

    Args:
        render_ir: render_ir dict with timeline list
        manifest: manifest dict (narration_manifest or dialogue_manifest)

    Returns:
        render_ir with synced timeline and total_duration

    Raises:
        ValueError: if a timeline beat_id is not found in manifest
    """
    beats = manifest.get("beats")
    turns = manifest.get("turns")

    if turns is not None and beats is None:
        # dialogue_manifest: use turns aggregation
        synced_timeline = _sync_from_turns(render_ir, turns)
    elif beats is not None:
        # narration_manifest: use beats direct lookup
        synced_timeline = _sync_from_beats(render_ir, beats)
    else:
        raise ValueError(
            "manifest must have either 'beats' (narration_manifest) or 'turns' (dialogue_manifest)"
        )

    render_ir = dict(render_ir)
    render_ir["timeline"] = synced_timeline
    render_ir["total_duration"] = round(manifest.get("total_duration", 0.0), 3)

    return render_ir
