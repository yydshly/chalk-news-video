"""Pace module: estimate animation timing from narration length.

V0.1 strategy:
- Chinese characters: ~4 chars/sec
- English words: ~3 words/sec
- Minimum duration: 1.5 sec
- Padding after each node: 0.5 sec
"""


# Reading-speed heuristics. Tunable; see config/app.yaml later.
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
    # English word count: any run of ASCII letters counts as one word
    english_words = 0
    in_word = False
    for ch in text:
        is_alpha = ch.isascii() and ch.isalpha()
        if is_alpha and not in_word:
            english_words += 1
            in_word = True
        elif not is_alpha:
            in_word = False
        else:
            pass

    chinese_time = chinese / CHINESE_CHARS_PER_SEC if chinese else 0.0
    english_time = english_words / ENGLISH_WORDS_PER_SEC if english_words else 0.0

    duration = max(chinese_time, english_time)
    return max(duration, MIN_DURATION)


def compute_timeline(nodes):
    """Compute cumulative at/duration for each node.

    Returns:
        (timeline, total_duration)
        timeline: list of {node_id, at, duration, narration}
        total_duration: seconds
    """
    timeline = []
    current = 0.0
    for node in nodes:
        base = estimate_duration(node.get("narration", ""))
        duration = base + PADDING
        timeline.append({
            "node_id": node["id"],
            "at": round(current, 3),
            "duration": round(duration, 3),
            "narration": node.get("narration", ""),
        })
        current += duration
    return timeline, round(current, 3)
