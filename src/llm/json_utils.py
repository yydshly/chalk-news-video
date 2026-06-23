"""JSON extraction helpers for LLM responses."""


import json
import re


_FENCE_RE = re.compile(r"```(?:json|JSON)?\s*(\{.*?\})\s*```", re.DOTALL)


def extract_json_object(text):
    """Extract a single JSON object from a string.

    Tries in order:
      1) parse the whole string as JSON
      2) the first ```json ... ``` (or ``` ... ```) fenced block
      3) the greedy outermost { ... } span

    Args:
        text: LLM response string. May contain prose, fences, etc.

    Returns:
        dict

    Raises:
        ValueError: if no JSON object can be parsed.
    """
    if text is None:
        raise ValueError("Cannot extract JSON from None")
    raw = str(text)
    if not raw.strip():
        raise ValueError("Cannot extract JSON from empty string")

    # 1) direct parse
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            return obj
    except (json.JSONDecodeError, TypeError):
        pass

    # 2) fenced ```json ... ```
    m = _FENCE_RE.search(raw)
    if m:
        candidate = m.group(1)
        try:
            obj = json.loads(candidate)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Found JSON fence but failed to parse: {e}. "
                f"Candidate starts with: {candidate[:200]!r}"
            )

    # 3) greedy outermost {...}
    if "{" in raw and "}" in raw:
        first = raw.index("{")
        last = raw.rindex("}")
        candidate = raw[first:last + 1]
        try:
            obj = json.loads(candidate)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass

    raise ValueError(
        f"Could not extract a JSON object from response. "
        f"First 500 chars: {raw[:500]!r}"
    )
