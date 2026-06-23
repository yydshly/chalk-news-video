"""Generate dialogue_script.json from semantic_ir via LLM.

CP7.1: Dialogue script contract — separates dialogue expression from semantic structure.
CP8: Add repair flow, --save-invalid, --repair, --dry-run options.

Usage:
    python -m src.generate_dialogue --semantic-ir outputs/latest/semantic_ir.json --mock --validate
    python -m src.generate_dialogue --semantic-ir outputs/latest/semantic_ir.json --profile minimax_m3_openai --validate --repair
    python -m src.generate_dialogue --semantic-ir outputs/latest/semantic_ir.json --mock --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import validate_dialogue
from .llm import create_llm_client
from .utils import PROJECT_ROOT, load_json, save_json


DEFAULT_SEMANTIC_PATH = PROJECT_ROOT / "outputs" / "latest" / "semantic_ir.json"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "outputs" / "latest" / "dialogue_script.json"
DEFAULT_INVALID_OUTPUT_PATH = PROJECT_ROOT / "outputs" / "latest" / "dialogue_script.invalid.json"
DEFAULT_PROMPT_PATH = PROJECT_ROOT / "prompts" / "semantic_ir_to_dialogue.md"
DEFAULT_REPAIR_PROMPT_PATH = PROJECT_ROOT / "prompts" / "repair_dialogue_script.md"
DEFAULT_LLM_CONFIG = PROJECT_ROOT / "config" / "llm.yaml"


# ---------- mock generator ----------

_HOST_TURNS = {
    "hook": "这条新闻到底在说什么？让我们一探究竟。",
    "question": "那具体是怎么回事呢？",
    "transition": "接下来我们具体看看。",
    "summary": "总结一下，今天的核心信息就是这些。",
}

_EXPERT_TURNS = {
    "explain": "简单说，它讲的是……",
    "clarify": "关键在于这一点。",
    "transition": "这就是整个事情的全貌。",
    "summary": "所以归根结底，这是一个值得关注的现象。",
}


def _duration_hint(text: str) -> float:
    """Estimate duration hint from text length."""
    return max(1.2, min(6.0, len(text) / 6.0))


def _generate_mock_dialogue_script(semantic_ir: dict) -> dict:
    """Deterministic mock dialogue_script for offline testing without API keys.

    Generates 2 turns per semantic_ir beat:
      - host: question/hook/transition
      - expert: explain/clarify/summary
    """
    beats = semantic_ir.get("beats", [])
    turns = []
    turn_id = 1

    beat_functions = {
        0: ("hook", "question"),       # first beat: hook + question
        "default": ("explain", "clarify"),  # middle beats: explain + clarify
    }

    for i, beat in enumerate(beats):
        beat_id = beat.get("id", f"b{i+1}")
        reveal = beat.get("reveal", "")
        narration = beat.get("narration", "").strip()

        # host turn
        if i == 0:
            host_text = _HOST_TURNS.get("hook", "这条新闻在讲什么？").replace("这条新闻", narration[:10] if narration else "这个问题")
        elif i == len(beats) - 1:
            host_text = _HOST_TURNS.get("transition", "继续看下一部分。")
        else:
            host_text = _HOST_TURNS.get("question", "具体是怎么回事？")

        host_text = host_text[:40]  # ensure short
        turns.append({
            "id": f"d{turn_id}",
            "speaker": "host",
            "beat_id": beat_id,
            "reveal": reveal,
            "text": host_text,
            "function": "hook" if i == 0 else ("question" if i == 1 else "transition"),
            "duration_hint": round(_duration_hint(host_text), 1),
        })
        turn_id += 1

        # expert turn (always)
        if narration:
            expert_text = narration[:60]
        elif i == 0:
            expert_text = f"简单说，{semantic_ir.get('title', '这件事')[:30]}。"
        elif i == len(beats) - 1:
            expert_text = "这就是这件事的完整分析。"
        else:
            expert_text = _EXPERT_TURNS.get("explain", "关键在于这一点。")[:40]

        turns.append({
            "id": f"d{turn_id}",
            "speaker": "expert",
            "beat_id": beat_id,
            "reveal": reveal,
            "text": expert_text,
            "function": "explain",
            "duration_hint": round(_duration_hint(expert_text), 1),
        })
        turn_id += 1

    return {
        "schema_version": "0.1",
        "source_semantic_ir": {
            "title": semantic_ir.get("title", ""),
            "schema_version": semantic_ir.get("schema_version", "0.1"),
        },
        "style": {
            "format": "two_speaker_explainer",
            "tone": "clear_curious",
            "language": "zh",
            "speakers": [
                {"id": "host", "name": "主持人", "role": "questioner"},
                {"id": "expert", "name": "讲解员", "role": "explainer"},
            ],
        },
        "turns": turns,
    }


# ---------- helpers ----------

def _save_text(text: str, path: Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def _format_issues(issues):
    return "\n".join(
        f"  [{i.code}] {i.path}: {i.message}"
        for i in issues
    )


# ---------- repair flow ----------

def _call_llm_for_repair(
    semantic_ir: dict,
    invalid_dialogue: dict,
    issues: list,
    llm_client,
    repair_prompt_template: str,
    attempt: int,
) -> dict | None:
    """Call LLM to repair an invalid dialogue_script."""
    # Substitute placeholders in repair prompt
    repair_prompt = repair_prompt_template
    repair_prompt = repair_prompt.replace("<SEMANTIC_IR_JSON>", json.dumps(semantic_ir, ensure_ascii=False, indent=2))
    repair_prompt = repair_prompt.replace("<INVALID_DIALOGUE_SCRIPT>", json.dumps(invalid_dialogue, ensure_ascii=False, indent=2))
    repair_prompt = repair_prompt.replace("<VALIDATION_ISSUES_JSON>", json.dumps([i.to_dict() for i in issues], ensure_ascii=False, indent=2))

    # Save repair prompt
    debug_repair_prompt_path = DEFAULT_OUTPUT_PATH.parent / "debug_repair_prompt.txt"
    _save_text(repair_prompt, debug_repair_prompt_path)

    # Call LLM
    try:
        raw_response = llm_client.generate_text(repair_prompt, "")
    except Exception as exc:
        print(f"[generate_dialogue] repair attempt {attempt} LLM call failed: {exc}", file=sys.stderr)
        return None

    debug_repair_response_path = DEFAULT_OUTPUT_PATH.parent / "debug_repair_response.txt"
    _save_text(raw_response, debug_repair_response_path)

    # Parse response
    try:
        repaired = json.loads(raw_response)
    except json.JSONDecodeError:
        text = raw_response.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            start = next((i for i, l in enumerate(lines) if "{" in l), 0)
            end = next((len(lines) - 1 - i for i, l in enumerate(reversed(lines)) if "}" in l), len(lines) - 1)
            text = "\n".join(lines[start:end+1])
        try:
            repaired = json.loads(text)
        except json.JSONDecodeError:
            print(f"[generate_dialogue] repair attempt {attempt} response is not valid JSON", file=sys.stderr)
            return None

    return repaired


def _validate_and_handle(
    dialogue_script: dict,
    semantic_ir: dict,
    output_path: Path,
    invalid_output_path: Path,
    save_invalid: bool,
) -> int:
    """Validate dialogue_script, handle errors. Returns exit code."""
    issues = validate_dialogue.validate_dialogue_script(dialogue_script, semantic_ir=semantic_ir)
    errors = [i for i in issues if i.severity == "error"]

    if not errors:
        save_json(dialogue_script, output_path)
        print(f"[generate_dialogue] wrote {output_path}")
        print(f"[generate_dialogue] validation PASSED")
        # Save validation issues (empty = valid)
        save_json([i.to_dict() for i in issues], DEFAULT_OUTPUT_PATH.parent / "debug_dialogue_validation_issues.json")
        return 0

    # Validation failed
    print(f"[generate_dialogue] validation failed with {len(errors)} error(s):", file=sys.stderr)
    for i in errors:
        print(f"  ERROR  [{i.code}] {i.path}: {i.message}", file=sys.stderr)

    # Save validation issues
    save_json([i.to_dict() for i in issues], DEFAULT_OUTPUT_PATH.parent / "debug_dialogue_validation_issues.json")

    if save_invalid:
        save_json(dialogue_script, invalid_output_path)
        print(f"[generate_dialogue] wrote invalid version to {invalid_output_path}", file=sys.stderr)

    return 5


# ---------- CLI ----------

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate dialogue_script.json from semantic_ir via LLM.",
    )
    parser.add_argument(
        "--semantic-ir",
        type=str,
        default=str(DEFAULT_SEMANTIC_PATH),
        help=f"Path to semantic_ir.json (default: {DEFAULT_SEMANTIC_PATH})",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_OUTPUT_PATH),
        help=f"Output path (default: {DEFAULT_OUTPUT_PATH})",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default=str(DEFAULT_PROMPT_PATH),
        help=f"Prompt template (default: {DEFAULT_PROMPT_PATH})",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=str(DEFAULT_LLM_CONFIG),
        help=f"LLM config (default: {DEFAULT_LLM_CONFIG})",
    )
    parser.add_argument(
        "--profile",
        type=str,
        default=None,
        help="LLM profile name.",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use in-process mock provider (no API key).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate and save prompt only, don't call LLM.",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate output with validate_dialogue.",
    )
    parser.add_argument(
        "--env",
        type=str,
        default=None,
        help="Path to .env file to load before calling LLM.",
    )
    parser.add_argument(
        "--save-invalid",
        action="store_true",
        default=True,
        help="Save invalid dialogue_script to .invalid.json on validation failure (default: True).",
    )
    parser.add_argument(
        "--no-save-invalid",
        action="store_true",
        help="Do not save invalid dialogue_script.",
    )
    parser.add_argument(
        "--repair",
        action="store_true",
        help="Enable LLM repair on validation failure (non-mock only).",
    )
    parser.add_argument(
        "--repair-attempts",
        type=int,
        default=2,
        help="Max repair attempts (default: 2).",
    )

    args = parser.parse_args(argv)

    save_invalid = not args.no_save_invalid
    invalid_output_path = Path(str(DEFAULT_OUTPUT_PATH).replace(".json", ".invalid.json"))

    semantic_ir_path = Path(args.semantic_ir)
    if not semantic_ir_path.exists():
        print(f"Error: semantic_ir not found: {semantic_ir_path}", file=sys.stderr)
        return 2

    try:
        semantic_ir = load_json(semantic_ir_path)
    except Exception as exc:
        print(f"Error: failed to load semantic_ir: {exc}", file=sys.stderr)
        return 2

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    prompt_path = Path(args.prompt)
    if not prompt_path.exists():
        print(f"Error: prompt not found: {prompt_path}", file=sys.stderr)
        return 2

    prompt_template = prompt_path.read_text(encoding="utf-8")

    # Build user prompt from semantic_ir
    user_prompt = json.dumps(semantic_ir, ensure_ascii=False, indent=2)

    # Substitute variables in prompt (title, etc.)
    system_prompt = prompt_template

    raw_response = ""

    if args.mock:
        print(f"[generate_dialogue] using mock provider (no LLM call)")
        raw_response = json.dumps(_generate_mock_dialogue_script(semantic_ir), ensure_ascii=False, indent=2)
    elif args.dry_run:
        full_prompt = f"# System:\n{system_prompt}\n\n# User:\n{user_prompt}"
        _save_text(full_prompt, output_path.parent / "debug_dialogue_prompt.txt")
        print(f"[generate_dialogue] dry-run: saved prompt to debug_dialogue_prompt.txt")
        return 0
    else:
        # Real LLM call
        llm_client = create_llm_client(
            profile_name=args.profile,
            config_path=args.config,
            env_path=args.env,
        )
        full_prompt = f"# System:\n{system_prompt}\n\n# User:\n{user_prompt}"
        _save_text(full_prompt, output_path.parent / "debug_dialogue_prompt.txt")
        try:
            raw_response = llm_client.generate_text(system_prompt, user_prompt)
        except Exception as exc:
            print(f"Error: LLM call failed: {exc}", file=sys.stderr)
            return 1
        _save_text(raw_response, output_path.parent / "debug_dialogue_response.txt")

    # Parse LLM response as JSON
    try:
        dialogue_script = json.loads(raw_response)
    except json.JSONDecodeError:
        text = raw_response.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            start = next((i for i, l in enumerate(lines) if "{" in l), 0)
            end = next((len(lines) - 1 - i for i, l in enumerate(reversed(lines)) if "}" in l), len(lines) - 1)
            text = "\n".join(lines[start:end+1])
        try:
            dialogue_script = json.loads(text)
        except json.JSONDecodeError as exc:
            print(f"Error: LLM response is not valid JSON: {exc}", file=sys.stderr)
            print(f"Raw response:\n{raw_response[:500]}", file=sys.stderr)
            return 1

    # Validate if requested
    if args.validate:
        print(f"[generate_dialogue] validating...")
        issues = validate_dialogue.validate_dialogue_script(dialogue_script, semantic_ir=semantic_ir)
        errors = [i for i in issues if i.severity == "error"]

        if not errors:
            save_json(dialogue_script, output_path)
            print(f"[generate_dialogue] wrote {output_path}")
            print(f"[generate_dialogue] validation PASSED")
            save_json([i.to_dict() for i in issues], output_path.parent / "debug_dialogue_validation_issues.json")
            return 0

        # Validation failed
        print(f"[generate_dialogue] validation failed with {len(errors)} error(s):", file=sys.stderr)
        for i in errors:
            print(f"  ERROR  [{i.code}] {i.path}: {i.message}", file=sys.stderr)
        save_json([i.to_dict() for i in issues], output_path.parent / "debug_dialogue_validation_issues.json")

        # Repair flow (non-mock only)
        if args.repair and not args.mock:
            print(f"[generate_dialogue] attempting repair...")
            repair_prompt_path = Path(args.prompt.replace("semantic_ir_to_dialogue", "repair_dialogue_script"))
            if not repair_prompt_path.exists():
                repair_prompt_path = Path(DEFAULT_REPAIR_PROMPT_PATH)
            if not repair_prompt_path.exists():
                print(f"[generate_dialogue] repair prompt not found, skipping repair", file=sys.stderr)
                if save_invalid:
                    save_json(dialogue_script, invalid_output_path)
                    print(f"[generate_dialogue] wrote invalid version to {invalid_output_path}", file=sys.stderr)
                return 5

            repair_prompt_template = repair_prompt_path.read_text(encoding="utf-8")

            llm_client = create_llm_client(
                profile_name=args.profile,
                config_path=args.config,
                env_path=args.env,
            )

            for attempt in range(1, args.repair_attempts + 1):
                print(f"[generate_dialogue] repair attempt {attempt}/{args.repair_attempts}...")
                repaired = _call_llm_for_repair(
                    semantic_ir, dialogue_script, issues, llm_client,
                    repair_prompt_template, attempt,
                )
                if repaired is None:
                    continue

                # Validate repaired version
                repaired_issues = validate_dialogue.validate_dialogue_script(repaired, semantic_ir=semantic_ir)
                repaired_errors = [i for i in repaired_issues if i.severity == "error"]
                if not repaired_errors:
                    print(f"[generate_dialogue] repair attempt {attempt} succeeded")
                    dialogue_script = repaired
                    save_json([i.to_dict() for i in repaired_issues], output_path.parent / "debug_dialogue_validation_issues.json")
                    save_json(dialogue_script, output_path)
                    print(f"[generate_dialogue] wrote {output_path}")
                    print(f"[generate_dialogue] validation PASSED after repair")
                    return 0

                print(f"[generate_dialogue] repair attempt {attempt} still has {len(repaired_errors)} error(s)")
                for i in repaired_errors:
                    print(f"  ERROR  [{i.code}] {i.path}: {i.message}", file=sys.stderr)
                dialogue_script = repaired
                issues = repaired_errors

            # All repair attempts failed
            print(f"[generate_dialogue] all {args.repair_attempts} repair attempts failed", file=sys.stderr)
            if save_invalid:
                save_json(dialogue_script, invalid_output_path)
                print(f"[generate_dialogue] wrote invalid version to {invalid_output_path}", file=sys.stderr)
            return 5

        # No repair requested or mock mode
        if save_invalid:
            save_json(dialogue_script, invalid_output_path)
            print(f"[generate_dialogue] wrote invalid version to {invalid_output_path}", file=sys.stderr)
        return 5

    # No validation requested - just save
    save_json(dialogue_script, output_path)
    print(f"[generate_dialogue] wrote {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
