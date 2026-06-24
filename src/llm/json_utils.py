"""JSON extraction helpers for LLM responses."""

import json
import re


_FENCE_RE = re.compile(r"```(?:json|JSON)?\s*([^\n].*?)```", re.DOTALL)


def _find_json_in_text(text: str) -> str:
    """Find and extract the first JSON object from text using brace counting.

    Uses brace counting to find the outermost {...} block.
    Returns the JSON string (not parsed).
    Raises ValueError if no valid JSON found.
    """
    start = -1
    brace_count = 0
    in_string = False
    escape_next = False

    for i, ch in enumerate(text):
        if escape_next:
            escape_next = False
            continue
        if ch == '\\':
            escape_next = True
            continue
        if ch == '"' and not escape_next:
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == '{':
            if start == -1:
                start = i
            brace_count += 1
        elif ch == '}':
            brace_count -= 1
            if brace_count == 0 and start != -1:
                return text[start:i + 1]

    raise ValueError(f"No valid JSON object found in text (first 200 chars): {text[:200]!r}")


def extract_json_object(text):
    """Extract a single JSON object from a string.

    Tries in order:
      1) parse the whole string as JSON
      2) the first ```json ... ``` (or ``` ... ```) fenced block using brace counting
      3) the outermost { ... } span using brace counting

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

    # 2) fenced block - use brace counting to extract the full JSON
    fence_patterns = [
        r"```json\s*\n?(.*?)```",
        r"```JSON\s*\n?(.*?)```",
        r"```\s*\n?(.*?)```",
    ]
    for pattern in fence_patterns:
        m = re.search(pattern, raw, re.DOTALL)
        if m:
            candidate = m.group(1).strip()
            # Try to parse the fenced content directly
            try:
                obj = json.loads(candidate)
                if isinstance(obj, dict):
                    return obj
            except json.JSONDecodeError:
                pass
            # Try brace counting within the fenced block
            if '{' in candidate:
                try:
                    json_str = _find_json_in_text(candidate)
                    obj = json.loads(json_str)
                    if isinstance(obj, dict):
                        return obj
                except ValueError:
                    pass

    # 3) outermost {...} using brace counting
    try:
        json_str = _find_json_in_text(raw)
        obj = json.loads(json_str)
        if isinstance(obj, dict):
            return obj
    except ValueError:
        pass

    raise ValueError(
        f"Could not extract a JSON object from response. "
        f"First 500 chars: {raw[:500]!r}"
    )
