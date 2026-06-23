"""Generate semantic_ir.json from latest_news.json via LLM.

Checkpoint 3 (V0.8) adds:
  --validate : validate after generation, print issues and exit 5 if invalid.
  --repair   : if invalid, call LLM to fix, up to --repair-attempts times.
  --no-save-invalid : refuse to write an invalid semantic_ir.json (default).
  --save-invalid    : allow writing an invalid result to .invalid.json.

NOT in this checkpoint:
- TTS / Remotion / video export (Checkpoint 4+)
- generate_ir is NOT wired into `src.pipeline` default flow.
"""


import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import validate_ir
from .llm import client as llm_client
from .llm.json_utils import extract_json_object
from .utils import PROJECT_ROOT, load_json, save_json


OUTPUT_DIR = PROJECT_ROOT / "outputs" / "latest"
DEFAULT_OUTPUT_PATH = OUTPUT_DIR / "semantic_ir.json"
INVALID_OUTPUT_PATH = OUTPUT_DIR / "semantic_ir.invalid.json"
DEFAULT_DEBUG_PROMPT_PATH = OUTPUT_DIR / "debug_llm_prompt.txt"
DEFAULT_DEBUG_RESPONSE_PATH = OUTPUT_DIR / "debug_llm_response.txt"
DEFAULT_DEBUG_VALIDATION_PATH = OUTPUT_DIR / "debug_validation_issues.json"
DEFAULT_DEBUG_REPAIR_PROMPT_PATH = OUTPUT_DIR / "debug_repair_prompt.txt"
DEFAULT_DEBUG_REPAIR_RESPONSE_PATH = OUTPUT_DIR / "debug_repair_response.txt"
DEFAULT_NEWS_PATH = OUTPUT_DIR / "latest_news.json"
DEFAULT_PROMPT_PATH = PROJECT_ROOT / "prompts" / "news_to_semantic_ir.md"
DEFAULT_REPAIR_PROMPT_PATH = PROJECT_ROOT / "prompts" / "repair_semantic_ir.md"
DEFAULT_SCHEMA_PATH = PROJECT_ROOT / "schema" / "semantic_ir.schema.json"
DEFAULT_LLM_CONFIG = PROJECT_ROOT / "config" / "llm.yaml"


# ---------- minimum checks (kept for the --mock path) ----------

def _minimum_checks(sem):
    """Cheap shape check used before full validate_ir for --mock."""
    if not isinstance(sem, dict):
        raise ValueError("semantic_ir must be a JSON object at the top level.")
    required = {
        "schema_version", "meta", "structure_type", "title",
        "nodes", "edges", "callouts", "beats",
    }
    missing = required - set(sem.keys())
    if missing:
        raise ValueError(f"semantic_ir missing required keys: {sorted(missing)}")
    validate_ir._check_no_coords_at(sem)  # raises on coords
    validate_ir._check_no_legacy_fields(sem)  # raises on legacy


# ---------- prompt composition ----------

def _build_llm_prompts(news, prompt_template, schema_text):
    system_prompt = (
        "You are a JSON-only generator for chalk-news-video.\n"
        "Output exactly ONE JSON object and nothing else: no prose, no markdown, "
        "no code fences outside the JSON, no greetings.\n\n"
        "# Schema reference (do not output):\n"
        "```json\n" + schema_text + "\n```\n"
    )
    news_str = json.dumps(news, ensure_ascii=False, indent=2)
    user_prompt = (
        "# Task brief\n\n"
        + prompt_template
        + "\n\n"
        + "# Input news (latest_news.json)\n\n"
        + "```json\n" + news_str + "\n```\n\n"
        + "# Now output the semantic_ir JSON object for this news.\n"
        + "Remember: NO coordinate fields (x, y, w, h, cx, cy). "
        + "Only the JSON object itself, nothing else."
    )
    return system_prompt, user_prompt


def _build_repair_prompts(original_ir, issues, schema_text, repair_template):
    system_prompt = (
        "You are a JSON repair tool. Output exactly ONE JSON object and nothing else."
    )
    original_str = json.dumps(original_ir, ensure_ascii=False, indent=2)
    issues_str = json.dumps([i.to_dict() for i in issues], ensure_ascii=False, indent=2)
    user_prompt = (
        "# Task brief\n\n"
        + Path(repair_template).read_text(encoding="utf-8")
        + "\n\n"
        + "# Original semantic_ir (invalid)\n\n"
        + "```json\n" + original_str + "\n```\n\n"
        + "# Validation issues\n\n"
        + "```json\n" + issues_str + "\n```\n\n"
        + "# Schema\n\n"
        + "```json\n" + schema_text + "\n```\n\n"
        + "# Now output the repaired semantic_ir JSON object.\n"
        + "Only the JSON object itself, nothing else."
    )
    return system_prompt, user_prompt


# ---------- mock generator ----------

def _generate_mock_semantic_ir(news):
    """Deterministic mock semantic_ir for offline testing without API keys."""
    title = (news.get("title") or "新闻示例").strip() or "新闻示例"
    summary_seed = (news.get("summary") or news.get("content") or "").strip()
    summary = summary_seed[:60] + ("..." if len(summary_seed) > 60 else "") if summary_seed else "本文件为 mock 示例。"
    source_name = (news.get("source_name") or "manual").strip() or "manual"
    source_url = (news.get("url") or "").strip()

    return {
        "schema_version": "0.1",
        "meta": {
            "source_title": news.get("title", ""),
            "source_url": source_url,
            "source_name": source_name,
            "published_at": news.get("published_at"),
            "lang": "zh",
        },
        "structure_type": "causal_chain",
        "title": title,
        "summary": summary,
        "nodes": [
            {"id": "n1", "label": "起因",   "sub": "事件背景",  "role": "source"},
            {"id": "n2", "label": "经过",   "sub": "关键过程",  "role": "neutral"},
            {"id": "n3", "label": "结果",   "sub": "影响与意义", "role": "target"},
        ],
        "edges": [
            {"id": "e1", "from": "n1", "to": "n2", "label": "导致"},
            {"id": "e2", "from": "n2", "to": "n3", "label": "引发"},
        ],
        "callouts": [
            {"id": "c1", "on": "n1", "text": "重点", "tone": "info"},
        ],
        "beats": [
            {"id": "b1", "reveal": "title", "speaker": "host", "narration": f"今天我们聊：{title[:20]}。"},
            {"id": "b2", "reveal": "n1",    "speaker": "expert", "narration": "首先，来看事件的起因与背景。"},
            {"id": "b3", "reveal": "c1",    "speaker": "host", "narration": "这部分尤其值得关注。"},
            {"id": "b4", "reveal": "e1",    "speaker": "expert", "narration": "这些因素推动了后续的演变。"},
            {"id": "b5", "reveal": "n2",    "speaker": "expert", "narration": "在过程中，关键转折点出现了。"},
            {"id": "b6", "reveal": "e2",    "speaker": "host", "narration": "由此引发了最终的结果。"},
            {"id": "b7", "reveal": "n3",    "speaker": "expert", "narration": "最终，我们看到了它的深远影响。"},
        ],
    }


# ---------- helpers ----------

def _save_text(text, path):
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
        description="Generate semantic_ir.json from latest_news.json via LLM.",
    )
    parser.add_argument("--news", type=str, default=str(DEFAULT_NEWS_PATH),
                        help=f"Path to latest_news.json (default: {DEFAULT_NEWS_PATH}).")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT_PATH),
                        help=f"Output path (default: {DEFAULT_OUTPUT_PATH}).")
    parser.add_argument("--prompt", type=str, default=str(DEFAULT_PROMPT_PATH),
                        help=f"Prompt template (default: {DEFAULT_PROMPT_PATH}).")
    parser.add_argument("--repair-prompt", type=str, default=str(DEFAULT_REPAIR_PROMPT_PATH),
                        help=f"Repair prompt template (default: {DEFAULT_REPAIR_PROMPT_PATH}).")
    parser.add_argument("--config", type=str, default=str(DEFAULT_LLM_CONFIG),
                        help=f"llm.yaml path (default: {DEFAULT_LLM_CONFIG}).")
    parser.add_argument("--profile", type=str, default=None,
                        help="LLM profile name. Defaults to default_profile in llm.yaml.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Compose and save the prompt, do NOT call any LLM.")
    parser.add_argument("--mock", action="store_true",
                        help="Use the in-process mock provider (no API key).")
    parser.add_argument("--validate", action="store_true",
                        help="After generation, run validate_ir. Exit 5 if invalid.")
    parser.add_argument("--repair", action="store_true",
                        help="If validation fails, attempt LLM repair up to --repair-attempts times.")
    parser.add_argument("--repair-attempts", type=int, default=2,
                        help="Max repair attempts (default: 2).")
    parser.add_argument("--save-invalid", action="store_true",
                        help="Allow saving an invalid semantic_ir.json (default: reject it).")
    parser.add_argument("--env", type=str, default=None,
                        help="Path to .env file. Defaults to <project root>/.env.")
    args = parser.parse_args(argv)

    news_path = Path(args.news)
    if not news_path.exists():
        print(f"Error: news file not found at {news_path}", file=sys.stderr)
        return 1

    try:
        news = load_json(news_path)
        prompt_template = Path(args.prompt).read_text(encoding="utf-8")
        schema_text = Path(DEFAULT_SCHEMA_PATH).read_text(encoding="utf-8")
    except (OSError, ValueError) as e:
        print(f"Error: failed to load inputs: {e}", file=sys.stderr)
        return 1

    system_prompt, user_prompt = _build_llm_prompts(news, prompt_template, schema_text)

    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    debug_prompt_text = (
        f"# Generated at {timestamp}\n"
        f"# News: {news_path.resolve()}\n"
        f"# Prompt: {args.prompt}\n"
        f"# Dry-run: {args.dry_run}  Mock: {args.mock}\n"
        f"# Profile: {args.profile or '(default_profile)'}\n"
        f"# Validate: {args.validate}  Repair: {args.repair}\n"
        "\n## SYSTEM PROMPT\n\n" + system_prompt +
        "\n\n## USER PROMPT\n\n" + user_prompt + "\n"
    )
    _save_text(debug_prompt_text, DEFAULT_DEBUG_PROMPT_PATH)

    if args.dry_run:
        print(f"[generate_ir] dry-run: wrote {DEFAULT_DEBUG_PROMPT_PATH}")
        return 0

    # --- acquire raw response ---
    if args.mock:
        raw_response = json.dumps(_generate_mock_semantic_ir(news), ensure_ascii=False, indent=2)
        debug_meta = "# mock provider (no HTTP call)\n"
    else:
        # --repair requires a real LLM
        if args.repair:
            try:
                llm = llm_client.create_llm_client(
                    profile_name=args.profile,
                    config_path=args.config,
                    env_path=args.env,
                )
            except (FileNotFoundError, ValueError, RuntimeError) as e:
                print(f"Error: failed to build LLM client: {e}", file=sys.stderr)
                return 2
        else:
            # Try to create the client even for non-repair; user might still want --validate
            try:
                llm = llm_client.create_llm_client(
                    profile_name=args.profile,
                    config_path=args.config,
                    env_path=args.env,
                )
            except (FileNotFoundError, ValueError, RuntimeError) as e:
                print(f"Error: failed to build LLM client: {e}", file=sys.stderr)
                return 2

        try:
            raw_response = llm.generate_text(system_prompt, user_prompt)
        except Exception as e:
            print(f"Error: LLM call failed: {e}", file=sys.stderr)
            return 3
        debug_meta = f"# Profile: {args.profile or '(default_profile)'}\n"

    debug_resp_text = f"# Generated at {timestamp}\n{debug_meta}\n{raw_response}"
    _save_text(debug_resp_text, DEFAULT_DEBUG_RESPONSE_PATH)

    # --- extract JSON ---
    try:
        semantic_ir = extract_json_object(raw_response)
    except ValueError as e:
        print(f"Error: failed to extract JSON from LLM response: {e}", file=sys.stderr)
        return 4

    # --- minimum shape checks ---
    try:
        _minimum_checks(semantic_ir)
    except ValueError as e:
        print(f"Error: minimum checks failed: {e}", file=sys.stderr)
        return 5

    # --- full validation ---
    issues = validate_ir.validate_semantic_ir(semantic_ir, DEFAULT_SCHEMA_PATH)
    if issues:
        save_json({"issues": [i.to_dict() for i in issues]}, DEFAULT_DEBUG_VALIDATION_PATH)
        print(f"[generate_ir] validation issues ({len(issues)}) written to {DEFAULT_DEBUG_VALIDATION_PATH}")
        print(f"[generate_ir] validation FAILED:\n{_format_issues(issues)}", file=sys.stderr)

        if args.repair and not args.mock:
            repair_template = Path(args.repair_prompt).read_text(encoding="utf-8")
            for attempt in range(1, args.repair_attempts + 1):
                print(f"[generate_ir] repair attempt {attempt}/{args.repair_attempts}...")
                repair_sys, repair_usr = _build_repair_prompts(
                    semantic_ir, issues, schema_text, args.repair_prompt,
                )
                _save_text(
                    f"# Repair attempt {attempt} at {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n"
                    f"# Issues: {len(issues)}\n\n## SYSTEM\n\n{repair_sys}\n\n## USER\n\n{repair_usr}\n",
                    DEFAULT_DEBUG_REPAIR_PROMPT_PATH,
                )
                try:
                    repair_raw = llm.generate_text(repair_sys, repair_usr)
                except Exception as e:
                    print(f"[generate_ir] repair LLM call failed: {e}", file=sys.stderr)
                    break
                _save_text(
                    f"# Repair attempt {attempt} response:\n{repair_raw}\n",
                    DEFAULT_DEBUG_REPAIR_RESPONSE_PATH,
                )
                try:
                    semantic_ir = extract_json_object(repair_raw)
                    _minimum_checks(semantic_ir)
                except ValueError as e:
                    print(f"[generate_ir] repair attempt {attempt} JSON extract failed: {e}", file=sys.stderr)
                    issues = [{"error": str(e)}]
                    continue

                issues = validate_ir.validate_semantic_ir(semantic_ir, DEFAULT_SCHEMA_PATH)
                if not issues:
                    print(f"[generate_ir] repair attempt {attempt} succeeded.")
                    break
                save_json({"issues": [i.to_dict() for i in issues]}, DEFAULT_DEBUG_VALIDATION_PATH)
                print(f"[generate_ir] repair attempt {attempt} still has issues:\n{_format_issues(issues)}", file=sys.stderr)
            else:
                print(f"[generate_ir] all {args.repair_attempts} repair attempts exhausted.", file=sys.stderr)
                if not args.save_invalid:
                    print("[generate_ir] NOT saving invalid semantic_ir (override with --save-invalid).", file=sys.stderr)
                    return 5
                out_path = Path(args.output).parent / "semantic_ir.invalid.json"
                save_json(semantic_ir, out_path)
                print(f"[generate_ir] wrote invalid result to {out_path} (--save-invalid)")
                return 5

        # Not repairing or repair not requested
        if not args.save_invalid:
            print("[generate_ir] NOT saving invalid semantic_ir.json (override with --save-invalid).", file=sys.stderr)
            return 5
        out_path = Path(args.output).parent / "semantic_ir.invalid.json"
        save_json(semantic_ir, out_path)
        print(f"[generate_ir] wrote invalid result to {out_path} (--save-invalid)")
        return 5

    # --- valid ---
    if args.validate:
        print("[generate_ir] validation PASSED.")

    save_json(semantic_ir, Path(args.output))
    print(
        f"[generate_ir] wrote {args.output} "
        f"(nodes={len(semantic_ir.get('nodes', []))}, "
        f"beats={len(semantic_ir.get('beats', []))})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
