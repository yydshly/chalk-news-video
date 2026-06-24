"""Generate semantic_ir.json from latest_news.json via LLM.

Checkpoint 3 (V0.8) adds:
  --validate : validate after generation, print issues and exit 5 if invalid.
  --repair   : if invalid, call LLM to fix, up to --repair-attempts times.
  --no-save-invalid : refuse to write an invalid semantic_ir.json (default).
  --save-invalid    : allow writing an invalid result to .invalid.json.

CP15.2.3 adds:
  - Debug files written to args.output's parent directory (job-scoped).
  - Deterministic repairs for UNREVEALED_EDGE / UNREVEALED_NODE issues.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import validate_ir
from .llm import client as llm_client
from .llm.json_utils import extract_json_object
from .utils import PROJECT_ROOT, load_json, save_json


OUTPUT_DIR = PROJECT_ROOT / "outputs" / "latest"
DEFAULT_OUTPUT_PATH = OUTPUT_DIR / "semantic_ir.json"
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


# ---------- deterministic repair ----------

def _apply_deterministic_repairs(semantic_ir: dict, issues: list) -> tuple[dict, list[str]]:
    """Apply deterministic repairs for coverage issues (UNREVEALED_EDGE, UNREVEALED_NODE).

    Returns (modified_semantic_ir, applied_repairs_list).
    """
    applied = []

    # Collect all revealed ids
    revealed = set()
    for beat in semantic_ir.get("beats", []):
        rev = beat.get("reveal", "")
        if rev and isinstance(rev, str):
            revealed.add(rev)

    # Get all declared ids
    node_ids = {n["id"] for n in semantic_ir.get("nodes", [])}
    edge_ids = {e["id"] for e in semantic_ir.get("edges", [])}
    callout_ids = {c["id"] for c in semantic_ir.get("callouts", [])}

    # Existing beat ids
    existing_beat_ids = {b["id"] for b in semantic_ir.get("beats", [])}

    def make_unique_beat_id(base: str) -> str:
        """Generate a unique beat id matching ^b\\d+$ (e.g. b11, b12)."""
        # Extract existing numeric suffixes
        numeric_ids = []
        for bid in existing_beat_ids:
            m = re.match(r'^b(\d+)$', bid)
            if m:
                numeric_ids.append(int(m.group(1)))
        next_num = max(numeric_ids) + 1 if numeric_ids else 11
        while f"b{next_num}" in existing_beat_ids:
            next_num += 1
        result = f"b{next_num}"
        existing_beat_ids.add(result)
        return result

    # Handle UNREVEALED_EDGE
    unrevealed_edges = set()
    for issue in issues:
        if issue.code == "UNREVEALED_EDGE":
            # Parse edge ids from message like "Edge(s) never revealed: ['e1', 'e2']"
            msg = issue.message
            match = re.search(r"\['([^']+)'\]", msg)
            if match:
                for eid in match.group(1).split(","):
                    eid = eid.strip().strip("'\"")
                    if eid in edge_ids:
                        unrevealed_edges.add(eid)

    for eid in sorted(unrevealed_edges):
        if eid in revealed:
            continue
        beat_id = make_unique_beat_id(f"b_auto_edge_{eid}")
        new_beat = {
            "id": beat_id,
            "reveal": eid,
            "speaker": "expert",
            "narration": "这条关系解释了事件之间的关键连接。",
        }
        semantic_ir["beats"].append(new_beat)
        revealed.add(eid)
        applied.append(f"added beat {beat_id} revealing edge {eid}")

    # Handle UNREVEALED_NODE
    unrevealed_nodes = set()
    for issue in issues:
        if issue.code == "UNREVEALED_NODE":
            msg = issue.message
            match = re.search(r"\['([^']+)'\]", msg)
            if match:
                for nid in match.group(1).split(","):
                    nid = nid.strip().strip("'\"")
                    if nid in node_ids:
                        unrevealed_nodes.add(nid)

    for nid in sorted(unrevealed_nodes):
        if nid in revealed:
            continue
        beat_id = make_unique_beat_id(f"b_auto_node_{nid}")
        new_beat = {
            "id": beat_id,
            "reveal": nid,
            "speaker": "expert",
            "narration": "这个要点值得深入分析。",
        }
        semantic_ir["beats"].append(new_beat)
        revealed.add(nid)
        applied.append(f"added beat {beat_id} revealing node {nid}")

    # Handle UNREVEALED_CALLOUT (less common)
    unrevealed_callouts = set()
    for issue in issues:
        if issue.code == "UNREVEALED_CALLOUT":
            msg = issue.message
            match = re.search(r"\['([^']+)'\]", msg)
            if match:
                for cid in match.group(1).split(","):
                    cid = cid.strip().strip("'\"")
                    if cid in callout_ids:
                        unrevealed_callouts.add(cid)

    for cid in sorted(unrevealed_callouts):
        if cid in revealed:
            continue
        beat_id = make_unique_beat_id(f"b_auto_callout_{cid}")
        new_beat = {
            "id": beat_id,
            "reveal": cid,
            "speaker": "host",
            "narration": "这一点需要特别注意。",
        }
        semantic_ir["beats"].append(new_beat)
        revealed.add(cid)
        applied.append(f"added beat {beat_id} revealing callout {cid}")

    # CP15.5.2: Handle SCHEMA_VIOLATION — strip forbidden 'on' field from beats
    # The 'on' field is valid on callouts, not beats. LLM sometimes incorrectly adds it to beats.
    for beat in semantic_ir.get("beats", []):
        if "on" in beat:
            applied.append(f"stripped 'on' field from beat {beat.get('id', '?')}")
            del beat["on"]

    # CP15.5.2: Handle BROKEN_CAUSAL_CHAIN — remove orphan nodes not in the chain
    # Build adjacency for causal_chain: each node has at most one outgoing edge
    edges = semantic_ir.get("edges", [])
    adj = {}
    for e in edges:
        frm, to = e.get("from"), e.get("to")
        if frm and to:
            adj[frm] = to

    # Find all reachable nodes from chain starts
    if adj:
        has_incoming = set(adj.values())
        starts = [n for n in node_ids if n not in has_incoming]
        reachable = set()
        for start in starts:
            cur = start
            seen_path = []
            seen_set = {start}
            while cur in adj:
                seen_path.append(cur)
                reachable.add(cur)
                cur = adj[cur]
                if cur in seen_set:
                    break
                seen_set.add(cur)
            reachable.add(cur)  # last node

        # Nodes not reachable from any chain start are orphans
        orphan_nodes = node_ids - reachable
        if orphan_nodes:
            orphan_list = sorted(orphan_nodes)
            applied.append(f"removing orphan nodes (not in causal chain): {orphan_list}")
            # Remove orphan nodes
            semantic_ir["nodes"] = [n for n in semantic_ir.get("nodes", []) if n["id"] not in orphan_nodes]
            # Remove edges referencing orphan nodes
            semantic_ir["edges"] = [
                e for e in semantic_ir.get("edges", [])
                if e.get("from") not in orphan_nodes and e.get("to") not in orphan_nodes
            ]
            # Remove callouts referencing orphan nodes
            semantic_ir["callouts"] = [
                c for c in semantic_ir.get("callouts", []) if c.get("on") not in orphan_nodes
            ]
            # Remove beats revealing orphan nodes (keep title beat)
            semantic_ir["beats"] = [
                b for b in semantic_ir.get("beats", [])
                if b.get("reveal") in ("title",) or b.get("reveal", "") not in orphan_nodes
            ]

    return semantic_ir, applied


def _enforce_beat_budget(
    semantic_ir: dict,
    max_beats: int = 10,
    min_beats: int = 6,
) -> tuple[dict, list[dict]]:
    """Enforce that beats count is within [min_beats, max_beats] deterministically.

    CP15.5.2: LLM sometimes generates beats > 10 (e.g. 11). This guard trims
    to max_beats while preserving reveal order and not generating new content.

    Rules:
    1. If len(beats) <= max_beats: no change.
    2. If len(beats) > max_beats:
       - Keep first beat (title reveal).
       - Keep last beat.
       - Sample/compress middle beats to reach max_beats total.
       - Preserve reveal order; do NOT shuffle.
       - Do NOT generate new reveals that don't exist.
       - Do NOT remove the title reveal.
    3. If len(beats) < min_beats:
       - Do NOT fabricate facts.
       - Can supplement from existing title/node/callout reveals.
       - If uncertain, output repair warning only.
    4. Write repair record to debug_deterministic_repairs.json.

    Returns (modified_semantic_ir, repair_records).
    """
    beats = semantic_ir.get("beats", [])
    original_count = len(beats)
    records = []

    # Case 1: within budget — nothing to do
    if min_beats <= original_count <= max_beats:
        return semantic_ir, records

    # Case 2: over budget — trim middle beats
    if original_count > max_beats:
        records.append({
            "type": "BEAT_BUDGET_TRIM",
            "before_beats": original_count,
            "after_beats": max_beats,
            "reason": f"LLM generated {original_count} beats, exceeds schema limit {max_beats}. "
                      f"Preserving first (title) and last beats, compressing middle.",
        })

        # Strategy: keep first (title), keep last, compress middle
        # middle_slots = max_beats - 2
        # middle_original = original_count - 2
        # Take every (middle_original / middle_slots)-th beat from the middle
        kept_beats = []
        kept_beats.append(beats[0])  # always keep first (title)

        middle_count = original_count - 2
        target_middle = max_beats - 2

        if middle_count > 0 and target_middle > 0:
            # Sample middle beats at regular intervals
            step = middle_count / target_middle
            for i in range(target_middle):
                idx = int(round(1 + i * step))
                if idx < original_count - 1:  # don't include last (reserved)
                    kept_beats.append(beats[idx])

        kept_beats.append(beats[-1])  # always keep last

        semantic_ir["beats"] = kept_beats
        return semantic_ir, records

    # Case 3: under budget — do NOT fabricate, just warn
    # CP15.5.2: We do NOT add beats because that would require generating new content
    records.append({
        "type": "BEAT_BUDGET_UNDER",
        "before_beats": original_count,
        "after_beats": original_count,
        "reason": f"Only {original_count} beats, below minimum {min_beats}. "
                  f"Not fabricating new beats to avoid hallucination.",
    })
    return semantic_ir, records


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

    # Compute debug paths based on output directory (job-scoped, CP15.2.3)
    output_path = Path(args.output)
    debug_dir = output_path.parent

    debug_prompt_path = debug_dir / "debug_llm_prompt.txt"
    debug_response_path = debug_dir / "debug_llm_response.txt"
    debug_validation_path = debug_dir / "debug_validation_issues.json"
    debug_repair_prompt_path = debug_dir / "debug_repair_prompt.txt"
    debug_repair_response_path = debug_dir / "debug_repair_response.txt"
    debug_deterministic_path = debug_dir / "debug_deterministic_repairs.json"
    invalid_output_path = debug_dir / "semantic_ir.invalid.json"

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
    _save_text(debug_prompt_text, debug_prompt_path)

    if args.dry_run:
        print(f"[generate_ir] dry-run: wrote {debug_prompt_path}")
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
    _save_text(debug_resp_text, debug_response_path)

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

    # CP15.5.2: Enforce beat budget before validation
    # This deterministic guard runs regardless of --repair flag
    semantic_ir, beat_budget_repairs = _enforce_beat_budget(semantic_ir)
    if beat_budget_repairs:
        # Merge with any existing deterministic repairs log
        existing_repairs = []
        if debug_deterministic_path.exists():
            try:
                existing_repairs = load_json(debug_deterministic_path).get("repairs", [])
            except Exception:
                pass
        all_repairs = existing_repairs + beat_budget_repairs
        save_json({"repairs": all_repairs}, debug_deterministic_path)
        for r in beat_budget_repairs:
            print(f"[generate_ir] beat_budget: {r['type']} — before={r['before_beats']} after={r['after_beats']} "
                  f"({'; '.join(beat_budget_repairs[0].get('reason', '').split('.')[:2])}.)", file=sys.stderr)

    # --- full validation ---
    issues = validate_ir.validate_semantic_ir(semantic_ir, DEFAULT_SCHEMA_PATH)
    if issues:
        save_json({"issues": [i.to_dict() for i in issues]}, debug_validation_path)
        print(f"[generate_ir] validation issues ({len(issues)}) written to {debug_validation_path}")
        print(f"[generate_ir] validation FAILED:\n{_format_issues(issues)}", file=sys.stderr)

        # CP15.2.3: Try deterministic repairs first
        if issues:
            semantic_ir, det_repairs = _apply_deterministic_repairs(semantic_ir, issues)
            if det_repairs:
                save_json({"repairs": det_repairs}, debug_deterministic_path)
                print(f"[generate_ir] deterministic repairs applied: {det_repairs}", file=sys.stderr)
                # CP18.2.1: Deterministic repairs may push beats > 10 (adding unrevealed beats).
                # Enforce beat budget again BEFORE re-validation to catch this.
                semantic_ir, beat_trim_repairs = _enforce_beat_budget(semantic_ir)
                if beat_trim_repairs:
                    all_repairs = det_repairs + beat_trim_repairs
                    save_json({"repairs": all_repairs}, debug_deterministic_path)
                    for r in beat_trim_repairs:
                        print(f"[generate_ir] beat_budget trim: {r['type']} — "
                              f"before={r['before_beats']} after={r['after_beats']}", file=sys.stderr)
                # Re-validate after deterministic repair + budget enforcement
                issues = validate_ir.validate_semantic_ir(semantic_ir, DEFAULT_SCHEMA_PATH)
                save_json({"issues": [i.to_dict() for i in issues]}, debug_validation_path)
                if not issues:
                    print(f"[generate_ir] deterministic repair resolved all issues.")
                    save_json(semantic_ir, output_path)
                    print(
                        f"[generate_ir] wrote {output_path} "
                        f"(nodes={len(semantic_ir.get('nodes', []))}, "
                        f"beats={len(semantic_ir.get('beats', []))})"
                    )
                    return 0

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
                    debug_repair_prompt_path,
                )
                try:
                    repair_raw = llm.generate_text(repair_sys, repair_usr)
                except Exception as e:
                    print(f"[generate_ir] repair LLM call failed: {e}", file=sys.stderr)
                    break
                _save_text(
                    f"# Repair attempt {attempt} response:\n{repair_raw}\n",
                    debug_repair_response_path,
                )
                try:
                    semantic_ir = extract_json_object(repair_raw)
                    _minimum_checks(semantic_ir)
                except ValueError as e:
                    print(f"[generate_ir] repair attempt {attempt} JSON extract failed: {e}", file=sys.stderr)
                    issues = [{"error": str(e)}]
                    continue

                # CP18.2.1: Enforce beat budget after LLM repair extraction
                # before validation to ensure beats are within 6-10 before we try repairs
                semantic_ir, beat_trim_repairs = _enforce_beat_budget(semantic_ir)
                if beat_trim_repairs:
                    save_json({"repairs": beat_trim_repairs}, debug_deterministic_path)
                    for r in beat_trim_repairs:
                        print(f"[generate_ir] beat_budget trim after repair extract: "
                              f"{r['type']} — before={r['before_beats']} after={r['after_beats']}", file=sys.stderr)

                issues = validate_ir.validate_semantic_ir(semantic_ir, DEFAULT_SCHEMA_PATH)
                save_json({"issues": [i.to_dict() for i in issues]}, debug_validation_path)
                if not issues:
                    print(f"[generate_ir] repair attempt {attempt} succeeded.")
                    break

                # Try deterministic repair after LLM repair too
                semantic_ir, det_repairs = _apply_deterministic_repairs(semantic_ir, issues)
                if det_repairs:
                    save_json({"repairs": det_repairs}, debug_deterministic_path)
                    print(f"[generate_ir] deterministic repairs after LLM repair: {det_repairs}", file=sys.stderr)
                # CP18.2.1: Enforce beat budget again after deterministic repairs
                semantic_ir, beat_trim_repairs = _enforce_beat_budget(semantic_ir)
                if beat_trim_repairs:
                    all_repairs = (det_repairs if det_repairs else []) + beat_trim_repairs
                    save_json({"repairs": all_repairs}, debug_deterministic_path)
                    for r in beat_trim_repairs:
                        print(f"[generate_ir] beat_budget trim after deterministic repair: "
                              f"{r['type']} — before={r['before_beats']} after={r['after_beats']}", file=sys.stderr)
                issues = validate_ir.validate_semantic_ir(semantic_ir, DEFAULT_SCHEMA_PATH)
                save_json({"issues": [i.to_dict() for i in issues]}, debug_validation_path)
                if not issues:
                    print(f"[generate_ir] deterministic repair resolved all issues after LLM repair.")
                    break

                print(f"[generate_ir] repair attempt {attempt} still has issues:\n{_format_issues(issues)}", file=sys.stderr)
            else:
                print(f"[generate_ir] all {args.repair_attempts} repair attempts exhausted.", file=sys.stderr)
                if not args.save_invalid:
                    print("[generate_ir] NOT saving invalid semantic_ir (override with --save-invalid).", file=sys.stderr)
                    return 5
                save_json(semantic_ir, invalid_output_path)
                print(f"[generate_ir] wrote invalid result to {invalid_output_path} (--save-invalid)")
                return 5

        # Not repairing or repair not requested
        if not args.save_invalid:
            print("[generate_ir] NOT saving invalid semantic_ir.json (override with --save-invalid).", file=sys.stderr)
            return 5
        save_json(semantic_ir, invalid_output_path)
        print(f"[generate_ir] wrote invalid result to {invalid_output_path} (--save-invalid)")
        return 5

    # --- valid ---
    if args.validate:
        print("[generate_ir] validation PASSED.")

    save_json(semantic_ir, output_path)
    print(
        f"[generate_ir] wrote {output_path} "
        f"(nodes={len(semantic_ir.get('nodes', []))}, "
        f"beats={len(semantic_ir.get('beats', []))})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
