"""Generate semantic_ir.json from latest_news.json via LLM.

Pipeline:
  1. Load latest_news.json.
  2. Load prompt template (prompts/news_to_semantic_ir.md).
  3. Load schema/semantic_ir.schema.json (embedded in system_prompt as ref).
  4. Compose system_prompt + user_prompt.
  5. Save full prompt to outputs/latest/debug_llm_prompt.txt.
  6. If --dry-run: stop here.
  7. If --mock: generate a deterministic semantic_ir without any HTTP call.
  8. Otherwise: create_llm_client(profile_name) -> generate_text().
  9. Save raw response to outputs/latest/debug_llm_response.txt.
 10. Extract JSON from response.
 11. Minimum checks: must be dict, required keys present, no coord keys.
 12. Save outputs/latest/semantic_ir.json.

NOT in this checkpoint:
- validate_ir / auto-repair (Checkpoint 3)
- TTS / Remotion / video export (Checkpoint 4+)
- generate_ir is NOT wired into `src.pipeline` default flow.
"""


import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from .llm import client as llm_client
from .llm.json_utils import extract_json_object
from .utils import PROJECT_ROOT, load_json, save_json


OUTPUT_DIR = PROJECT_ROOT / "outputs" / "latest"
DEFAULT_OUTPUT_PATH = OUTPUT_DIR / "semantic_ir.json"
DEFAULT_DEBUG_PROMPT_PATH = OUTPUT_DIR / "debug_llm_prompt.txt"
DEFAULT_DEBUG_RESPONSE_PATH = OUTPUT_DIR / "debug_llm_response.txt"
DEFAULT_NEWS_PATH = OUTPUT_DIR / "latest_news.json"
DEFAULT_PROMPT_PATH = PROJECT_ROOT / "prompts" / "news_to_semantic_ir.md"
DEFAULT_SCHEMA_PATH = PROJECT_ROOT / "schema" / "semantic_ir.schema.json"
DEFAULT_LLM_CONFIG = PROJECT_ROOT / "config" / "llm.yaml"

FORBIDDEN_COORD_KEYS = {"x", "y", "w", "h", "cx", "cy"}
REQUIRED_TOP_KEYS = {
    "schema_version", "meta", "structure_type", "title",
    "nodes", "edges", "callouts", "beats",
}


# ---------- minimum checks (no full validation, that's Checkpoint 3) ----------


def _check_minimum_shape(obj):
    """Cheap shape check; full jsonschema validation is Checkpoint 3."""
    if not isinstance(obj, dict):
        raise ValueError("semantic_ir must be a JSON object at the top level.")
    missing = REQUIRED_TOP_KEYS - set(obj.keys())
    if missing:
        raise ValueError(
            f"semantic_ir is missing required top-level keys: {sorted(missing)}. "
            f"Have: {sorted(obj.keys())}"
        )


def _check_no_coord_keys(obj, path="root"):
    """Recursively ensure no coord-like keys appear anywhere in semantic_ir."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in FORBIDDEN_COORD_KEYS:
                raise ValueError(
                    f"semantic_ir contains forbidden coord field '{k}' at "
                    f"{path}.{k}. LLM must NOT output coordinates."
                )
            _check_no_coord_keys(v, path + "." + str(k))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            _check_no_coord_keys(item, path + f"[{i}]")


# ---------- prompt composition ----------


def _build_prompts(news, prompt_template, schema_text):
    """Compose system_prompt and user_prompt for the LLM call."""
    news_str = json.dumps(news, ensure_ascii=False, indent=2)
    system_prompt = (
        "You are a JSON-only generator for chalk-news-video.\n"
        "Output exactly ONE JSON object and nothing else: no prose, no markdown, "
        "no code fences outside the JSON, no greetings.\n\n"
        "# Schema reference (do not output):\n"
        "```json\n" + schema_text + "\n```\n"
    )
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


# ---------- mock generator ----------


def _generate_mock_semantic_ir(news):
    """Deterministic mock semantic_ir. Used for tests without API keys.

    Produces a 3-node causal_chain driven by news.title + news.source_name.
    This does NOT represent real LLM output — README warns about that.
    """
    title = (news.get("title") or "新闻示例").strip() or "新闻示例"
    summary_seed = (news.get("summary") or news.get("content") or "").strip()
    if summary_seed:
        summary = summary_seed[:60] + ("..." if len(summary_seed) > 60 else "")
    else:
        summary = "本文件为 mock 生成的 semantic_ir 示例，不代表真实 LLM 输出。"

    source_name = (news.get("source_name") or "manual").strip() or "manual"
    source_url = (news.get("url") or "").strip()

    semantic_ir = {
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
            {"id": "n1", "label": "起因",   "sub": "事件背景",     "role": "source"},
            {"id": "n2", "label": "经过",   "sub": "关键过程",     "role": "neutral"},
            {"id": "n3", "label": "结果",   "sub": "影响与意义",   "role": "target"},
        ],
        "edges": [
            {"id": "e1", "from": "n1", "to": "n2", "label": "导致"},
            {"id": "e2", "from": "n2", "to": "n3", "label": "引发"},
        ],
        "callouts": [
            {"id": "c1", "on": "n1", "text": "重点", "tone": "info"},
        ],
        "beats": [
            {"id": "b1", "reveal": "title", "narration": f"今天我们聊：{title[:30]}。"},
            {"id": "b2", "reveal": "n1",    "narration": "首先，来看事件发生的起因与背景。"},
            {"id": "b3", "reveal": "c1",    "narration": "这个部分尤其值得关注。"},
            {"id": "b4", "reveal": "e1",    "narration": "这些因素进一步推动了事情的演变。"},
            {"id": "b5", "reveal": "n2",    "narration": "在过程中，关键的转折点开始出现。"},
            {"id": "b6", "reveal": "e2",    "narration": "由此引发了最终的结果。"},
            {"id": "b7", "reveal": "n3",    "narration": "最终，我们看到它对未来产生的影响。"},
        ],
    }
    return semantic_ir


# ---------- helpers ----------


def _save_text(text, path):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


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
    parser.add_argument("--config", type=str, default=str(DEFAULT_LLM_CONFIG),
                        help=f"llm.yaml path (default: {DEFAULT_LLM_CONFIG}).")
    parser.add_argument("--profile", type=str, default=None,
                        help="LLM profile name. Defaults to default_profile in llm.yaml.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Compose and save the prompt, do NOT call any LLM.")
    parser.add_argument("--mock", action="store_true",
                        help="Use the in-process mock provider (no API key).")
    parser.add_argument("--env", type=str, default=None,
                        help="Path to .env file. Defaults to <project root>/.env. "
                             "Missing file is fine; os.environ keeps current values.")
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

    system_prompt, user_prompt = _build_prompts(news, prompt_template, schema_text)

    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    debug_prompt_text = (
        f"# Generated at {timestamp}\n"
        f"# News: {news_path.resolve()}\n"
        f"# Prompt template: {args.prompt}\n"
        f"# Dry-run: {args.dry_run}\n"
        f"# Mock: {args.mock}\n"
        f"# Profile: {args.profile or '(default_profile)'}\n"
        "\n"
        "## SYSTEM PROMPT\n\n" + system_prompt +
        "\n\n## USER PROMPT\n\n" + user_prompt + "\n"
    )
    debug_prompt_path = Path(args.output).parent / "debug_llm_prompt.txt"
    _save_text(debug_prompt_text, debug_prompt_path)

    if args.dry_run:
        print(f"[generate_ir] dry-run: wrote {debug_prompt_path}")
        return 0

    # Acquire response
    if args.mock:
        semantic_ir = _generate_mock_semantic_ir(news)
        raw_response = json.dumps(semantic_ir, ensure_ascii=False, indent=2)
        debug_meta = "# mock provider (no HTTP call)\n"
    else:
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
        debug_meta = (
            f"# Profile: {args.profile or '(default_profile)'}\n"
            f"# Config: {args.config}\n"
        )

    debug_resp_text = (
        f"# Generated at {timestamp}\n" + debug_meta + "\n" + raw_response
    )
    debug_resp_path = Path(args.output).parent / "debug_llm_response.txt"
    _save_text(debug_resp_text, debug_resp_path)
    print(f"[generate_ir] wrote {debug_resp_path}")

    # Extract JSON
    try:
        semantic_ir = extract_json_object(raw_response)
    except ValueError as e:
        print(
            f"Error: failed to extract JSON from LLM response: {e}",
            file=sys.stderr,
        )
        return 4

    # Minimum checks
    try:
        _check_minimum_shape(semantic_ir)
        _check_no_coord_keys(semantic_ir)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 5

    save_json(semantic_ir, Path(args.output))
    print(
        f"[generate_ir] wrote {args.output} "
        f"(nodes={len(semantic_ir.get('nodes', []))}, "
        f"beats={len(semantic_ir.get('beats', []))})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
