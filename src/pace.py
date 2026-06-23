"""Pace module: estimate animation timing from beats (not nodes).

V0.5 contract:
- The timeline is driven by semantic_ir.beats, not by node.narration.
- Each beat has reveal + narration.
- Timeline items carry {beat_id, reveal, at, duration, narration}.

Heuristics (unchanged from V0.1):
- Chinese characters: ~4 chars/sec
- English words: ~3 words/sec
- Minimum duration: 1.5 sec
- Padding after each beat: 0.5 sec
"""


# Tunable heuristics; see config/app.yaml in a later checkpoint.
CHINESE_CHARS_PER_SEC = 4.0
ENGLISH_WORDS_PER_SEC = 3.0
MIN_DURATION = 1.5
PADDING = 0.5


def _is_chinese(ch):
    return "一" <= ch <= "鿿"


def estimate_duration(text):
    """Estimate narration duration in seconds from text length."""
    if not text:
        return MIN_DURATION

    chinese = sum(1 for ch in text if _is_chinese(ch))
    english_words = 0
    in_word = False
    for ch in text:
        is_alpha = ch.isascii() and ch.isalpha()
        if is_alpha and not in_word:
            english_words += 1
            in_word = True
        elif not is_alpha:
            in_word = False
        # else: still inside an English word

    chinese_time = chinese / CHINESE_CHARS_PER_SEC if chinese else 0.0
    english_time = english_words / ENGLISH_WORDS_PER_SEC if english_words else 0.0

    duration = max(chinese_time, english_time)
    return max(duration, MIN_DURATION)


def compute_timeline_from_beats(beats):
    """Build a timeline from beats.

    Args:
        beats: list of {id, reveal, narration}

    Returns:
        (timeline, total_duration)
        timeline: list of {beat_id, reveal, at, duration, narration}
        total_duration: seconds (sum of beat durations)
    """
    timeline = []
    current = 0.0
    for beat in beats:
        base = estimate_duration(beat.get("narration", ""))
        duration = base + PADDING
        timeline.append({
            "beat_id": beat["id"],
            "reveal": beat["reveal"],
            "at": round(current, 3),
            "duration": round(duration, 3),
            "narration": beat.get("narration", ""),
        })
        current += duration
    return timeline, round(current, 3)


def compute_timeline(nodes):
    """DEPRECATED shim. Builds a synthetic beat list from nodes.

    Kept for backwards compatibility — pipeline.py and layout.py no longer
    call this. Will be removed in a later checkpoint.
    """
    import warnings
    warnings.warn(
        "pace.compute_timeline(nodes) is deprecated; "
        "use pace.compute_timeline_from_beats(beats) instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    beats = [
        {
            "id": f"legacy_b{i + 1}",
            "reveal": n.get("id", f"n{i + 1}"),
            "narration": n.get("narration", ""),
        }
        for i, n in enumerate(nodes)
    ]
    return compute_timeline_from_beats(beats)
