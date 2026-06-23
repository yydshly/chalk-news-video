"""semantic_ir validation with structured issue reporting.

Validates a semantic_ir dict (or JSON file) against:
  A) jsonschema (schema/semantic_ir.schema.json)
  B) custom business rules (IDs, references, beats, etc.)

Returns a list of ValidationIssue (never raises on validation failure —
only on JSON parse errors).

Also exposes assert_valid_semantic_ir() which raises ValueError on any issue.
"""

from __future__ import annotations

import dataclasses
import json
import re
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
    path: str       # JSON path to the offending element, e.g. "nodes[0].label"
    message: str    # human-readable description
    severity: str = "error"   # "error" | "warning"

    def to_dict(self):
        return dataclasses.asdict(self)


# ---------------------------------------------------------------------------
# Rule A: jsonschema
# ---------------------------------------------------------------------------

_FORBIDDEN_COORDS = {"x", "y", "w", "h", "cx", "cy"}
_LEGACY_TOP_FIELDS = {"layout"}
_DEPRECATED_NODE_FIELDS = {"narration"}
_DEPRECATED_CALLOUT_FIELDS = {"attach_to"}


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
                    message=f"Forbidden coordinate field '{k}' found at {path}.{k}. "
                             f"LLM must NOT output coordinates.",
                ))
            _check_no_coords_at(v, f"{path}.{k}", issues)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            _check_no_coords_at(item, f"{path}[{i}]", issues)
    return issues


def _check_no_legacy_fields(obj, path="root", issues=None):
    """Check for deprecated/legacy top-level and nested fields."""
    if issues is None:
        issues = []
    if isinstance(obj, dict):
        for k in obj.keys():
            if path == "root" and k in _LEGACY_TOP_FIELDS:
                issues.append(ValidationIssue(
                    code="LEGACY_FIELD",
                    path=f"root.{k}",
                    message=f"Legacy top-level field '{k}' found. "
                             f"Use structure_type instead of 'layout'.",
                ))
        # node-level deprecated fields
        if path.startswith("root.nodes"):
            for k in _DEPRECATED_NODE_FIELDS:
                if k in obj:
                    issues.append(ValidationIssue(
                        code="DEPRECATED_NODE_FIELD",
                        path=f"{path}.{k}",
                        message=f"Deprecated field '{k}' in node. "
                                 f"Narration must be in beats, not nodes.",
                    ))
        if path.startswith("root.callouts"):
            for k in _DEPRECATED_CALLOUT_FIELDS:
                if k in obj:
                    issues.append(ValidationIssue(
                        code="DEPRECATED_CALLOUT_FIELD",
                        path=f"{path}.{k}",
                        message=f"Deprecated field '{k}' in callout. Use 'on' instead.",
                    ))
        for k, v in obj.items():
            _check_no_legacy_fields(v, f"{path}.{k}", issues)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            _check_no_legacy_fields(item, f"{path}[{i}]", issues)
    return issues


def _jsonschema_issues(sem: dict, schema_path: Path | str | None) -> list[ValidationIssue]:
    """Run Draft7Validator and return a list of ValidationIssues."""
    if schema_path is None:
        schema_path = PROJECT_ROOT / "schema" / "semantic_ir.schema.json"
    schema_path = Path(schema_path)
    try:
        schema = load_json(schema_path)
    except Exception as e:
        return [ValidationIssue(
            code="SCHEMA_LOAD_ERROR",
            path="root",
            message=f"Failed to load schema at {schema_path}: {e}",
        )]

    issues = []
    validator = Draft7Validator(schema)
    for err in validator.iter_errors(sem):
        # Build a JSON path string
        json_path = ".".join(str(p) for p in err.path) or "root"
        msg = err.message
        issues.append(ValidationIssue(
            code="SCHEMA_VIOLATION",
            path=json_path,
            message=msg,
        ))
    return issues


# ---------------------------------------------------------------------------
# Rule B: custom business validation
# ---------------------------------------------------------------------------

_ID_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
_NODE_ID_RE = re.compile(r"^n\d+$")
_EDGE_ID_RE = re.compile(r"^e\d+$")
_CALLOUT_ID_RE = re.compile(r"^c\d+$")
_BEAT_ID_RE = re.compile(r"^b\d+$")


def _is_chinese_length_ok(text: str, max_chars: int = 80) -> bool:
    """Roughly: allow up to max_chars characters, counting Chinese as 1 each."""
    if not text:
        return False
    # Count Chinese chars (CJK range)
    chinese = sum(1 for ch in text if "一" <= ch <= "鿿")
    # Non-Chinese chars
    other = len(text) - chinese
    # Heuristic: 1 Chinese = 1 char budget, 1 other = 1 char budget
    return len(text) <= max_chars


def validate_semantic_ir(sem: dict, schema_path: str | Path | None = None) -> list[ValidationIssue]:
    """Full validation: jsonschema (A) + custom rules (B).

    Returns a list of ValidationIssue (empty = valid).
    """
    issues: list[ValidationIssue] = []

    if not isinstance(sem, dict):
        return [ValidationIssue(
            code="NOT_A_DICT",
            path="root",
            message="semantic_ir must be a JSON object at the top level.",
        )]

    # A) jsonschema
    issues.extend(_jsonschema_issues(sem, schema_path))

    # B) recursive forbidden fields
    issues.extend(_check_no_coords_at(sem))
    issues.extend(_check_no_legacy_fields(sem))

    # Quick-accessors
    nodes = sem.get("nodes") or []
    edges = sem.get("edges") or []
    callouts = sem.get("callouts") or []
    beats = sem.get("beats") or []
    meta = sem.get("meta") or {}
    structure_type = sem.get("structure_type")

    # ---- meta ----
    if meta:
        lang = meta.get("lang")
        if lang is not None and lang != "zh":
            issues.append(ValidationIssue(
                code="INVALID_LANG",
                path="meta.lang",
                message=f"meta.lang must be 'zh', got {lang!r}.",
            ))
        for field in ("source_title", "source_url", "source_name"):
            if field not in meta:
                issues.append(ValidationIssue(
                    code="MISSING_META_FIELD",
                    path=f"meta.{field}",
                    message=f"meta.{field} is required but missing.",
                ))
    else:
        issues.append(ValidationIssue(
            code="MISSING_META",
            path="meta",
            message="meta object is required but missing or empty.",
        ))

    # ---- structure_type ----
    if structure_type and structure_type != "causal_chain":
        issues.append(ValidationIssue(
            code="INVALID_STRUCTURE_TYPE",
            path="structure_type",
            message=f"Only 'causal_chain' is supported, got {structure_type!r}.",
        ))

    # ---- nodes ----
    node_ids = set()
    for i, node in enumerate(nodes):
        nid = node.get("id", "")
        path = f"nodes[{i}]"
        if not nid:
            issues.append(ValidationIssue(
                code="MISSING_NODE_ID", path=path,
                message="Node is missing 'id'.", severity="error",
            ))
        elif nid in node_ids:
            issues.append(ValidationIssue(
                code="DUPLICATE_NODE_ID", path=f"{path}.id",
                message=f"Duplicate node id '{nid}'.", severity="error",
            ))
        else:
            node_ids.add(nid)
            if not _NODE_ID_RE.match(nid):
                issues.append(ValidationIssue(
                    code="NONCONFORMING_NODE_ID", path=f"{path}.id",
                    message=f"Node id '{nid}' should match ^n\\d+$.", severity="warning",
                ))
        if "narration" in node:
            issues.append(ValidationIssue(
                code="DEPRECATED_NODE_NARRATION", path=f"{path}.narration",
                message="Node must not have 'narration'. Put narration in beats.", severity="error",
            ))

    # node count
    if not (2 <= len(nodes) <= 5):
        issues.append(ValidationIssue(
            code="INVALID_NODE_COUNT", path="nodes",
            message=f"nodes must have 2-5 items, got {len(nodes)}.", severity="error",
        ))

    # ---- edges ----
    edge_ids = set()
    for i, edge in enumerate(edges):
        eid = edge.get("id", "")
        path = f"edges[{i}]"
        if not eid:
            issues.append(ValidationIssue(
                code="MISSING_EDGE_ID", path=path,
                message="Edge is missing 'id'.", severity="error",
            ))
        elif eid in edge_ids:
            issues.append(ValidationIssue(
                code="DUPLICATE_EDGE_ID", path=f"{path}.id",
                message=f"Duplicate edge id '{eid}'.", severity="error",
            ))
        else:
            edge_ids.add(eid)
            if not _EDGE_ID_RE.match(eid):
                issues.append(ValidationIssue(
                    code="NONCONFORMING_EDGE_ID", path=f"{path}.id",
                    message=f"Edge id '{eid}' should match ^e\\d+$.", severity="warning",
                ))
        src = edge.get("from", "")
        dst = edge.get("to", "")
        if not src:
            issues.append(ValidationIssue(
                code="MISSING_EDGE_FROM", path=f"{path}.from",
                message="Edge is missing 'from'.", severity="error",
            ))
        elif src not in node_ids:
            issues.append(ValidationIssue(
                code="UNKNOWN_EDGE_FROM", path=f"{path}.from",
                message=f"edge.from '{src}' does not reference any existing node id.", severity="error",
            ))
        if not dst:
            issues.append(ValidationIssue(
                code="MISSING_EDGE_TO", path=f"{path}.to",
                message="Edge is missing 'to'.", severity="error",
            ))
        elif dst not in node_ids:
            issues.append(ValidationIssue(
                code="UNKNOWN_EDGE_TO", path=f"{path}.to",
                message=f"edge.to '{dst}' does not reference any existing node id.", severity="error",
            ))
        if src and dst and src == dst:
            issues.append(ValidationIssue(
                code="SELF_LOOP_EDGE", path=path,
                message=f"edge '{eid}' has from == to ('{src}').", severity="error",
            ))

    # edge count
    min_edges = max(0, len(nodes) - 1)
    if len(edges) < min_edges:
        issues.append(ValidationIssue(
            code="INSUFFICIENT_EDGES", path="edges",
            message=f"For {len(nodes)} nodes at least {min_edges} edge(s) needed, got {len(edges)}.", severity="error",
        ))

    # causal_chain connectivity: check n1→n2→n3 basic chain
    if structure_type == "causal_chain" and nodes:
        # Build a quick adjacency
        adj = {e.get("from"): e.get("to") for e in edges if e.get("from") and e.get("to")}
        # Find nodes with no incoming (potential chain starts)
        has_incoming = set(adj.values())
        starts = [n for n in node_ids if n not in has_incoming]
        if starts:
            found_complete = False
            # Walk from each potential start
            for start in starts:
                path_so_far = [start]
                cur = start
                seen = {start}
                while cur in adj:
                    nxt = adj[cur]
                    if nxt in seen:
                        break  # loop, but we don't error on this in CP3
                    path_so_far.append(nxt)
                    seen.add(nxt)
                    cur = nxt
                # If we can reach all nodes, the chain is complete
                if set(path_so_far) == node_ids:
                    found_complete = True
                    break
            if not found_complete:
                issues.append(ValidationIssue(
                    code="BROKEN_CAUSAL_CHAIN", path="edges",
                    message="Could not find a linear path covering all nodes. "
                            "causal_chain requires a single continuous chain.", severity="error",
                ))
        else:
            issues.append(ValidationIssue(
                code="NO_CHAIN_START", path="edges",
                message="Could not find a chain start (node with no incoming edge). "
                        "causal_chain requires a linear path covering all nodes.", severity="error",
            ))

    # ---- callouts ----
    callout_ids = set()
    for i, callout in enumerate(callouts):
        cid = callout.get("id", "")
        path = f"callouts[{i}]"
        if not cid:
            issues.append(ValidationIssue(
                code="MISSING_CALLOUT_ID", path=path,
                message="Callout is missing 'id'.", severity="error",
            ))
        elif cid in callout_ids:
            issues.append(ValidationIssue(
                code="DUPLICATE_CALLOUT_ID", path=f"{path}.id",
                message=f"Duplicate callout id '{cid}'.", severity="error",
            ))
        else:
            callout_ids.add(cid)
            if not _CALLOUT_ID_RE.match(cid):
                issues.append(ValidationIssue(
                    code="NONCONFORMING_CALLOUT_ID", path=f"{path}.id",
                    message=f"Callout id '{cid}' should match ^c\\d+$.", severity="warning",
                ))
        on = callout.get("on", "")
        if not on:
            issues.append(ValidationIssue(
                code="MISSING_CALLOUT_ON", path=f"{path}.on",
                message="Callout is missing 'on'.", severity="error",
            ))
        elif on not in node_ids:
            issues.append(ValidationIssue(
                code="UNKNOWN_CALLOUT_ON", path=f"{path}.on",
                message=f"callout.on '{on}' does not reference any existing node id.", severity="error",
            ))
        if "attach_to" in callout:
            issues.append(ValidationIssue(
                code="DEPRECATED_CALLOUT_ATTACH_TO", path=f"{path}.attach_to",
                message="callout must use 'on', not 'attach_to'.", severity="error",
            ))

    # callout count
    if len(callouts) > 3:
        issues.append(ValidationIssue(
            code="TOO_MANY_CALLOUTS", path="callouts",
            message=f"callouts must have 0-3 items, got {len(callouts)}.", severity="error",
        ))

    # ---- beats ----
    beat_ids = set()
    if not (6 <= len(beats) <= 10):
        issues.append(ValidationIssue(
            code="INVALID_BEAT_COUNT", path="beats",
            message=f"beats must have 6-10 items, got {len(beats)}.", severity="error",
        ))

    revealed_ids = set()   # all ids revealed across all beats
    for i, beat in enumerate(beats):
        bid = beat.get("id", "")
        path = f"beats[{i}]"
        if not bid:
            issues.append(ValidationIssue(
                code="MISSING_BEAT_ID", path=path,
                message="Beat is missing 'id'.", severity="error",
            ))
        elif bid in beat_ids:
            issues.append(ValidationIssue(
                code="DUPLICATE_BEAT_ID", path=f"{path}.id",
                message=f"Duplicate beat id '{bid}'.", severity="error",
            ))
        else:
            beat_ids.add(bid)
            if not _BEAT_ID_RE.match(bid):
                issues.append(ValidationIssue(
                    code="NONCONFORMING_BEAT_ID", path=f"{path}.id",
                    message=f"Beat id '{bid}' should match ^b\\d+$.", severity="warning",
                ))
        reveal = beat.get("reveal", "")
        if not reveal:
            issues.append(ValidationIssue(
                code="MISSING_BEAT_REVEAL", path=f"{path}.reveal",
                message="Beat is missing 'reveal'.", severity="error",
            ))
        else:
            valid_reveals = {"title"} | node_ids | edge_ids | callout_ids
            if reveal not in valid_reveals:
                issues.append(ValidationIssue(
                    code="UNKNOWN_REVEAL", path=f"{path}.reveal",
                    message=f"beat.reveal '{reveal}' is not one of the known ids "
                            f"or 'title'. Known: {sorted(valid_reveals)}.", severity="error",
                ))
        narration = beat.get("narration", "")
        if not narration:
            issues.append(ValidationIssue(
                code="EMPTY_NARRATION", path=f"{path}.narration",
                message="beat.narration must be a non-empty string.", severity="error",
            ))
        elif len(narration) > 120:
            issues.append(ValidationIssue(
                code="NARRATION_TOO_LONG", path=f"{path}.narration",
                message=f"beat.narration is {len(narration)} chars (max 120).", severity="error",
            ))
        # Track what this beat reveals (for coverage checks)
        if reveal in {"title"} | node_ids | edge_ids | callout_ids:
            revealed_ids.add(reveal)

    # First beat must reveal title
    if beats and beats[0].get("reveal") != "title":
        issues.append(ValidationIssue(
            code="FIRST_BEAT_NOT_TITLE", path="beats[0].reveal",
            message=f"First beat must have reveal='title', got {beats[0].get('reveal')!r}.", severity="error",
        ))

    # Coverage: every node must be revealed at least once
    unrevealed_nodes = node_ids - revealed_ids
    if unrevealed_nodes:
        issues.append(ValidationIssue(
            code="UNREVEALED_NODE", path="beats",
            message=f"Node(s) never revealed in any beat: {sorted(unrevealed_nodes)}.", severity="error",
        ))

    # Coverage: every edge must be revealed at least once
    unrevealed_edges = edge_ids - revealed_ids
    if unrevealed_edges:
        issues.append(ValidationIssue(
            code="UNREVEALED_EDGE", path="beats",
            message=f"Edge(s) never revealed in any beat: {sorted(unrevealed_edges)}.", severity="error",
        ))

    # Coverage: if callouts exist, each must be revealed at least once
    for cid in callout_ids:
        if cid not in revealed_ids:
            issues.append(ValidationIssue(
                code="UNREVEALED_CALLOUT", path="beats",
                message=f"Callout '{cid}' never revealed in any beat.", severity="error",
            ))

    return issues


# ---------------------------------------------------------------------------
# Assertion helper
# ---------------------------------------------------------------------------

def assert_valid_semantic_ir(sem: dict, schema_path: str | Path | None = None):
    """Raise ValueError listing all issues if sem is invalid."""
    issues = validate_semantic_ir(sem, schema_path)
    if issues:
        lines = [f"[{i.code}] {i.path}: {i.message}" for i in issues]
        raise ValueError(
            f"semantic_ir validation failed with {len(issues)} issue(s):\n"
            + "\n".join(lines)
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(
        description="Validate a semantic_ir JSON file.",
    )
    parser.add_argument("file", type=str, nargs="?", default=None,
                        help="Path to semantic_ir.json. Omit to read from stdin.")
    parser.add_argument("--schema", type=str, default=None,
                        help="Path to schema (default: schema/semantic_ir.schema.json).")
    parser.add_argument("--json", action="store_true",
                        help="Output issues as JSON.")
    parser.add_argument("--strict", action="store_true",
                        help="Treat warnings as errors.")
    args = parser.parse_args(argv)

    # Load semantic_ir
    if args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"Error: file not found: {path}", file=sys.stderr)
            return 2
        try:
            sem = load_json(path)
        except Exception as e:
            print(f"Error: failed to parse JSON: {e}", file=sys.stderr)
            return 2
    else:
        try:
            sem = json.load(sys.stdin)
        except Exception as e:
            print(f"Error: failed to read JSON from stdin: {e}", file=sys.stderr)
            return 2

    issues = validate_semantic_ir(sem, args.schema)
    if args.strict:
        issues = [i for i in issues if i.severity in ("error", "warning")]

    if args.json:
        print(json.dumps([i.to_dict() for i in issues], ensure_ascii=False, indent=2))
    else:
        if not issues:
            print("OK: semantic_ir is valid.")
        else:
            errors = [i for i in issues if i.severity == "error"]
            warns = [i for i in issues if i.severity == "warning"]
            for i in errors:
                print(f"ERROR  [{i.code}] {i.path}: {i.message}", file=sys.stderr)
            for i in warns:
                print(f"WARN   [{i.code}] {i.path}: {i.message}", file=sys.stderr)
    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
