"""Generate dialogue_script.json from semantic_ir via LLM.

CP7.1: Dialogue script contract — separates dialogue expression from semantic structure.

Usage:
    python -m src.generate_dialogue --semantic-ir outputs/latest/semantic_ir.json --mock --validate
    python -m src.generate_dialogue --semantic-ir outputs/latest/semantic_ir.json --profile minimax_m3_openai --validate
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
DEFAULT_PROMPT_PATH = PROJECT_ROOT / "prompts" / "semantic_ir_to_dialogue.md"
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

    args = parser.parse_args(argv)

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

    debug_meta = ""
    raw_response = ""

    if args.mock:
        print(f"[generate_dialogue] using mock provider (no LLM call)")
        raw_response = json.dumps(_generate_mock_dialogue_script(semantic_ir), ensure_ascii=False, indent=2)
        debug_meta = "# mock provider (no HTTP call)\n"
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
        debug_meta = "# LLM call\n"
        try:
            raw_response = llm_client.generate_text(system_prompt, user_prompt)
        except Exception as exc:
            print(f"Error: LLM call failed: {exc}", file=sys.stderr)
            return 1
        _save_text(raw_response, output_path.parent / "debug_dialogue_response.txt")

    # Parse LLM response as JSON
    try:
        # Try direct parse first
        dialogue_script = json.loads(raw_response)
    except json.JSONDecodeError:
        # Try to extract JSON object from response
        text = raw_response.strip()
        # Remove markdown code fences if present
        if text.startswith("```"):
            lines = text.split("\n")
            # Find first { and last }
            start = next((i for i, l in enumerate(lines) if "{" in l), 0)
            end = next((len(lines) - 1 - i for i, l in enumerate(reversed(lines)) if "}" in l), len(lines) - 1)
            text = "\n".join(lines[start:end+1])
        try:
            dialogue_script = json.loads(text)
        except json.JSONDecodeError as exc:
            print(f"Error: LLM response is not valid JSON: {exc}", file=sys.stderr)
            print(f"Raw response:\n{raw_response[:500]}", file=sys.stderr)
            return 1

    # Save output
    save_json(dialogue_script, output_path)
    print(f"[generate_dialogue] wrote {output_path}")

    # Validate if requested
    if args.validate:
        print(f"[generate_dialogue] validating...")
        issues = validate_dialogue.validate_dialogue_script(dialogue_script, semantic_ir=semantic_ir)
        errors = [i for i in issues if i.severity == "error"]
        if errors:
            print(f"[generate_dialogue] validation failed with {len(errors)} error(s):", file=sys.stderr)
            for i in errors:
                print(f"  ERROR  [{i.code}] {i.path}: {i.message}", file=sys.stderr)
            return 5
        print(f"[generate_dialogue] validation PASSED")

    return 0


if __name__ == "__main__":
    sys.exit(main())
