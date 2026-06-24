"""Layout module: convert semantic_ir (no coords) to render_ir (with coords).

V0.5 changes:
- Dispatches on semantic_ir["structure_type"] (was "layout" in V0.1).
- Timeline comes from semantic_ir.beats via pace.compute_timeline_from_beats.
- meta is passed through to render_ir.
- Edges carry id and label.
- Callouts use semantic_ir.callouts[].on (was "attach_to" in V0.1).
"""


from . import pace


# Canvas / timing constants
CANVAS_W = 1280
CANVAS_H = 720
FPS = 30

# Layout constants for causal_chain
MARGIN_X = 80
NODE_W = 240
NODE_H = 140
NODE_GAP = 60
NODE_Y = 340
TITLE_Y = 60
SUMMARY_Y = 100
CALLOUT_OFFSET_Y = -110  # place callout above the node
CALLOUT_W = 160
CALLOUT_H = 56
SUBTITLE_BAR_Y = 624
SUBTITLE_TEXT_Y = 664


def _empty_render_ir(semantic_ir):
    meta = semantic_ir.get("meta", {})
    return {
        "canvas": {"width": CANVAS_W, "height": CANVAS_H},
        "fps": FPS,
        "meta": semantic_ir.get("meta", {}),
        "title": {
            "text": semantic_ir.get("title", ""),
            "x": CANVAS_W // 2,
            "y": TITLE_Y,
        },
        "summary": {
            "text": semantic_ir.get("summary", ""),
            "x": CANVAS_W // 2,
            "y": SUMMARY_Y,
        },
        # CP18.4: Propagate news metadata so server.py meta writer can read it
        "news": {
            "title": semantic_ir.get("title") or meta.get("source_title", ""),
            "summary": semantic_ir.get("summary", ""),
            "url": meta.get("source_url", ""),
            "source": meta.get("source_name", ""),
        },
        "nodes": [],
        "edges": [],
        "callouts": [],
        "timeline": [],
        "subtitles": {
            "bar": {"x": 80, "y": SUBTITLE_BAR_Y, "w": CANVAS_W - 160, "h": 60},
            "text_x": CANVAS_W // 2,
            "text_y": SUBTITLE_TEXT_Y,
        },
        "total_duration": 0.0,
    }


def _layout_nodes_horizontal(nodes):
    """Lay nodes out left-to-right and centered on the canvas.

    Returns (positioned_nodes, node_by_id, node_index_map).
    """
    n = len(nodes)
    total_w = n * NODE_W + (n - 1) * NODE_GAP
    usable_w = CANVAS_W - 2 * MARGIN_X
    if total_w > usable_w:
        gap = max(0, (usable_w - n * NODE_W) // max(1, n - 1))
    else:
        gap = NODE_GAP
    total_w = n * NODE_W + (n - 1) * gap
    start_x = (CANVAS_W - total_w) // 2

    positioned = []
    by_id = {}
    for i, node in enumerate(nodes):
        x = start_x + i * (NODE_W + gap)
        out = dict(node)  # preserve id, label, sub, role, ...
        out["x"] = x
        out["y"] = NODE_Y
        out["w"] = NODE_W
        out["h"] = NODE_H
        out["cx"] = x + NODE_W // 2
        out["cy"] = NODE_Y + NODE_H // 2
        positioned.append(out)
        by_id[node["id"]] = out
    return positioned, by_id


def layout_causal_chain(semantic_ir):
    """Lay out a causal chain horizontally and return a render_ir dict."""
    nodes = semantic_ir.get("nodes", []) or []
    edges = semantic_ir.get("edges", []) or []
    callouts = semantic_ir.get("callouts", []) or []
    beats = semantic_ir.get("beats", []) or []

    if not nodes:
        return _empty_render_ir(semantic_ir)

    positioned_nodes, node_by_id = _layout_nodes_horizontal(nodes)

    # Edges (horizontal arrows; raise on dangling references)
    positioned_edges = []
    for edge in edges:
        src = node_by_id.get(edge["from"])
        dst = node_by_id.get(edge["to"])
        if not src:
            raise ValueError(
                f"edge '{edge.get('id')}' references from='{edge.get('from')}' "
                f"which is not a known node id. "
                f"Known node ids: {sorted(node_by_id.keys())}"
            )
        if not dst:
            raise ValueError(
                f"edge '{edge.get('id')}' references to='{edge.get('to')}' "
                f"which is not a known node id. "
                f"Known node ids: {sorted(node_by_id.keys())}"
            )
        positioned_edges.append({
            "id": edge["id"],
            "from": edge["from"],
            "to": edge["to"],
            "label": edge.get("label"),
            "x1": src["x"] + src["w"],
            "y1": src["cy"],
            "x2": dst["x"],
            "y2": dst["cy"],
        })

    # Callouts above their attached node (callout.on -> node id)
    positioned_callouts = []
    for callout in callouts:
        target = node_by_id.get(callout.get("on"))
        if not target:
            raise ValueError(
                f"callout '{callout.get('id')}' references on='{callout.get('on')}' "
                f"which is not a known node id. "
                f"Known node ids: {sorted(node_by_id.keys())}"
            )
        cx = target["cx"] - CALLOUT_W // 2
        cy = target["y"] + CALLOUT_OFFSET_Y
        positioned_callouts.append({
            "id": callout["id"],
            "text": callout.get("text", ""),
            "tone": callout.get("tone", "info"),
            "on": callout["on"],
            "x": cx,
            "y": cy,
            "w": CALLOUT_W,
            "h": CALLOUT_H,
        })

    # Timeline is driven by beats, NOT by nodes
    timeline, total_duration = pace.compute_timeline_from_beats(beats)

    return {
        "canvas": {"width": CANVAS_W, "height": CANVAS_H},
        "fps": FPS,
        "meta": semantic_ir.get("meta", {}),
        "title": {
            "text": semantic_ir.get("title", ""),
            "x": CANVAS_W // 2,
            "y": TITLE_Y,
        },
        "summary": {
            "text": semantic_ir.get("summary", ""),
            "x": CANVAS_W // 2,
            "y": SUMMARY_Y,
        },
        # CP18.4: Propagate news metadata so server.py meta writer can read it
        "news": {
            "title": semantic_ir.get("title") or semantic_ir.get("meta", {}).get("source_title", ""),
            "summary": semantic_ir.get("summary", ""),
            "url": semantic_ir.get("meta", {}).get("source_url", ""),
            "source": semantic_ir.get("meta", {}).get("source_name", ""),
        },
        "nodes": positioned_nodes,
        "edges": positioned_edges,
        "callouts": positioned_callouts,
        "timeline": timeline,
        "subtitles": {
            "bar": {"x": 80, "y": SUBTITLE_BAR_Y, "w": CANVAS_W - 160, "h": 60},
            "text_x": CANVAS_W // 2,
            "text_y": SUBTITLE_TEXT_Y,
        },
        "total_duration": total_duration,
    }


def build_render_ir(semantic_ir):
    """Dispatch on semantic_ir.structure_type and return a render_ir dict."""
    structure_type = semantic_ir.get("structure_type")
    if structure_type == "causal_chain":
        return layout_causal_chain(semantic_ir)
    raise ValueError(f"Unknown structure_type: {structure_type!r}")
