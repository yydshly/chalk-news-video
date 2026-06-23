"""Dialogue script validation with structured issue reporting.

Validates a dialogue_script dict (or JSON file) against:
  A) jsonschema (schema/dialogue_script.schema.json)
  B) custom business rules (beat coverage, speaker references, forbidden fields)

Returns a list of ValidationIssue (never raises on validation failure —
only on JSON parse errors).

Also exposes assert_valid_dialogue_script() which raises ValueError on any issue.
"""

from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path
from typing import Sequence

import jsonschema
from jsonschema import Draft7Validator

from .utils import PROJECT_ROOT, load_json


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class ValidationIssue:
    """One problem found during validation."""
    code: str       # machine-readable short code
    path: str       # JSON path to the offending element
    message: str    # human-readable description
    severity: str = "error"   # "error" | "warning"

    def to_dict(self):
        return dataclasses.asdict(self)


# ---------------------------------------------------------------------------
# Rule A: jsonschema
# ---------------------------------------------------------------------------

_SCHEMA_PATH = PROJECT_ROOT / "schema" / "dialogue_script.schema.json"
_FORBIDDEN_COORDS = {"x", "y", "w", "h", "cx", "cy"}
# Fields that belong to audio/TTS output, not dialogue script
_FORBIDDEN_AUDIO_FIELDS = {"audio_path", "start", "end", "duration"}


def _check_no_coords_at(obj, path="root", issues=None):
    """Recursively reject any forbidden coordinate keys."""
    if issues is None:
        issues = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in _FORBIDDEN_COORDS:
                issues.append(ValidationIssue(
                    code="FORBIDDEN_COORD",
                    path=f"{path}.{k}",
                    message=f"Forbidden coordinate field '{k}' found at {path}.{k}.",
                ))
            _check_no_coords_at(v, f"{path}.{k}", issues)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            _check_no_coords_at(item, f"{path}[{i}]", issues)
    return issues


def _check_no_audio_fields_at(obj, path="root", issues=None):
    """Recursively reject audio/TTS output fields in dialogue script."""
    if issues is None:
        issues = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in _FORBIDDEN_AUDIO_FIELDS:
                issues.append(ValidationIssue(
                    code="FORBIDDEN_AUDIO_FIELD",
                    path=f"{path}.{k}",
                    message=f"Forbidden audio/TTS field '{k}' found at {path}.{k}. "
                             f"audio_path/start/end/duration belong in dialogue_manifest, not dialogue_script.",
                ))
            _check_no_audio_fields_at(v, f"{path}.{k}", issues)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            _check_no_audio_fields_at(item, f"{path}[{i}]", issues)
    return issues


def validate_dialogue_script(
    dialogue: dict,
    semantic_ir: dict | None = None,
    schema_path: Path | None = None,
) -> list[ValidationIssue]:
    """Validate a dialogue_script dict.

    Args:
        dialogue: parsed dialogue_script dict
        semantic_ir: optional semantic_ir dict to check beat coverage
        schema_path: optional override for dialogue_script.schema.json

    Returns:
        list of ValidationIssue (empty = valid)
    """
    issues: list[ValidationIssue] = []

    # A. jsonschema
    schema_file = schema_path or _SCHEMA_PATH
    try:
        schema = load_json(schema_file)
    except Exception as exc:
        return [ValidationIssue(
            code="SCHEMA_LOAD_ERROR",
            path="root",
            message=f"Failed to load schema: {exc}",
        )]

    jsonschema_validator = Draft7Validator(schema)
    for error in jsonschema_validator.iter_errors(dialogue):
        path = ".".join(str(p) for p in error.path) if error.path else "root"
        issues.append(ValidationIssue(
            code="JSONSCHEMA_ERROR",
            path=path,
            message=error.message,
        ))

    # B1. Forbidden coordinate fields
    _check_no_coords_at(dialogue, issues=issues)

    # B2. Forbidden audio/TTS fields
    _check_no_audio_fields_at(dialogue, issues=issues)

    # B3. Not a dict at root
    if not isinstance(dialogue, dict):
        issues.append(ValidationIssue(
            code="NOT_A_DICT",
            path="root",
            message=f"dialogue_script must be a dict, got {type(dialogue).__name__}",
        ))
        return issues  # no point continuing

    # B4. turns must be non-empty
    turns = dialogue.get("turns", [])
    if isinstance(turns, list) and len(turns) == 0:
        issues.append(ValidationIssue(
            code="EMPTY_TURNS",
            path="turns",
            message="turns array cannot be empty",
        ))

    # B5. turns count range (8-18 recommended)
    if isinstance(turns, list):
        if len(turns) < 8:
            issues.append(ValidationIssue(
                code="TURNS_TOO_FEW",
                path="turns",
                message=f"turns has only {len(turns)} items, recommended minimum is 8",
                severity="warning",
            ))
        if len(turns) > 18:
            issues.append(ValidationIssue(
                code="TURNS_TOO_MANY",
                path="turns",
                message=f"turns has {len(turns)} items, recommended maximum is 18",
                severity="warning",
            ))

    # B6. turn.id uniqueness
    if isinstance(turns, list):
        seen_ids = set()
        for i, turn in enumerate(turns):
            if not isinstance(turn, dict):
                continue
            tid = turn.get("id", "")
            if tid in seen_ids:
                issues.append(ValidationIssue(
                    code="DUPLICATE_TURN_ID",
                    path=f"turns[{i}].id",
                    message=f"Duplicate turn id '{tid}'",
                ))
            seen_ids.add(tid)

    # B7. speaker must be host or expert
    if isinstance(turns, list):
        for i, turn in enumerate(turns):
            if not isinstance(turn, dict):
                continue
            speaker = turn.get("speaker")
            if speaker not in ("host", "expert"):
                issues.append(ValidationIssue(
                    code="INVALID_SPEAKER",
                    path=f"turns[{i}].speaker",
                    message=f"speaker must be 'host' or 'expert', got '{speaker}'",
                ))

    # B8. text non-empty
    if isinstance(turns, list):
        for i, turn in enumerate(turns):
            if not isinstance(turn, dict):
                continue
            text = turn.get("text", "")
            if not text or not text.strip():
                issues.append(ValidationIssue(
                    code="EMPTY_TEXT",
                    path=f"turns[{i}].text",
                    message="turn text cannot be empty",
                ))
            elif len(text) > 80:
                issues.append(ValidationIssue(
                    code="TEXT_TOO_LONG",
                    path=f"turns[{i}].text",
                    message=f"turn text is {len(text)} chars, recommended maximum is 80",
                    severity="warning",
                ))

    # B9. duration_hint must be positive if present
    if isinstance(turns, list):
        for i, turn in enumerate(turns):
            if not isinstance(turn, dict):
                continue
            dh = turn.get("duration_hint")
            if dh is not None:
                if not isinstance(dh, (int, float)):
                    issues.append(ValidationIssue(
                        code="DURATION_HINT_NOT_NUMBER",
                        path=f"turns[{i}].duration_hint",
                        message=f"duration_hint must be a number, got {type(dh).__name__}",
                    ))
                elif dh <= 0:
                    issues.append(ValidationIssue(
                        code="DURATION_HINT_NOT_POSITIVE",
                        path=f"turns[{i}].duration_hint",
                        message=f"duration_hint must be > 0, got {dh}",
                    ))

    # B10. beat_id must reference a valid semantic_ir beat (if semantic_ir provided)
    if isinstance(semantic_ir, dict) and isinstance(turns, list):
        valid_beat_ids = {b.get("id") for b in semantic_ir.get("beats", []) if isinstance(b, dict)}
        for i, turn in enumerate(turns):
            if not isinstance(turn, dict):
                continue
            bid = turn.get("beat_id", "")
            if bid and bid not in valid_beat_ids:
                issues.append(ValidationIssue(
                    code="UNKNOWN_BEAT_ID",
                    path=f"turns[{i}].beat_id",
                    message=f"beat_id '{bid}' not found in semantic_ir.beats",
                ))

    # B11. each semantic_ir beat must be covered by at least one turn
    if isinstance(semantic_ir, dict) and isinstance(turns, list):
        valid_beat_ids = {b.get("id") for b in semantic_ir.get("beats", []) if isinstance(b, dict)}
        covered_beat_ids = {turn.get("beat_id") for turn in turns if isinstance(turn, dict)}
        uncovered = valid_beat_ids - covered_beat_ids
        if uncovered:
            issues.append(ValidationIssue(
                code="BEAT_NOT_COVERED",
                path="turns",
                message=f"semantic_ir beats not covered by any dialogue turn: {sorted(uncovered)}",
            ))

    # B12. function must be valid enum if present
    VALID_FUNCTIONS = {"hook", "question", "explain", "clarify", "transition", "summary"}
    if isinstance(turns, list):
        for i, turn in enumerate(turns):
            if not isinstance(turn, dict):
                continue
            fn = turn.get("function")
            if fn is not None and fn not in VALID_FUNCTIONS:
                issues.append(ValidationIssue(
                    code="INVALID_FUNCTION",
                    path=f"turns[{i}].function",
                    message=f"function must be one of {sorted(VALID_FUNCTIONS)}, got '{fn}'",
                ))

    return issues


def assert_valid_dialogue_script(dialogue: dict, semantic_ir: dict | None = None):
    """Raise ValueError if dialogue_script has any error-level issues."""
    issues = validate_dialogue_script(dialogue, semantic_ir=semantic_ir)
    errors = [i for i in issues if i.severity == "error"]
    if errors:
        lines = "\n".join(f"  [{i.code}] {i.path}: {i.message}" for i in errors)
        raise ValueError(f"dialogue_script validation failed:\n{lines}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate a dialogue_script.json file.",
    )
    parser.add_argument(
        "dialogue_script",
        type=str,
        help="Path to dialogue_script.json",
    )
    parser.add_argument(
        "--semantic-ir",
        type=str,
        default=None,
        help="Path to semantic_ir.json (for beat coverage check)",
    )
    parser.add_argument(
        "--schema",
        type=str,
        default=None,
        help="Path to dialogue_script.schema.json",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output issues as JSON",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors",
    )
    args = parser.parse_args(argv)

    # Load dialogue_script
    dialogue_path = Path(args.dialogue_script)
    if not dialogue_path.exists():
        print(f"Error: file not found: {dialogue_path}", file=sys.stderr)
        return 2

    try:
        dialogue = load_json(dialogue_path)
    except Exception as exc:
        print(f"Error: failed to parse JSON: {exc}", file=sys.stderr)
        return 2

    # Load semantic_ir if provided
    semantic_ir = None
    if args.semantic_ir:
        sem_path = Path(args.semantic_ir)
        if sem_path.exists():
            try:
                semantic_ir = load_json(sem_path)
            except Exception:
                pass  # non-fatal

    # Validate
    schema_path = Path(args.schema) if args.schema else None
    issues = validate_dialogue_script(dialogue, semantic_ir=semantic_ir, schema_path=schema_path)

    if args.json:
        print(json.dumps([i.to_dict() for i in issues], ensure_ascii=False, indent=2))
        return 0 if not issues else 1

    if not issues:
        print("OK")
        return 0

    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]

    for i in issues:
        prefix = "ERROR" if i.severity == "error" else "WARN "
        print(f"[{prefix}] [{i.code}] {i.path}: {i.message}")

    if errors:
        return 1
    if args.strict and warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
