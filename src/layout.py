"""Layout module: convert semantic_ir (no coords) to render_ir (with coords).

V0.1 supports:
- causal_chain: nodes laid out left-to-right, edges drawn as arrows.
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
    return {
        "canvas": {"width": CANVAS_W, "height": CANVAS_H},
        "fps": FPS,
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


def layout_causal_chain(semantic_ir):
    """Lay out a causal chain horizontally and return a render_ir dict."""
    nodes = semantic_ir.get("nodes", []) or []
    edges = semantic_ir.get("edges", []) or []
    callouts = semantic_ir.get("callouts", []) or []

    n = len(nodes)
    if n == 0:
        return _empty_render_ir(semantic_ir)

    # Center the chain horizontally
    total_w = n * NODE_W + (n - 1) * NODE_GAP
    usable_w = CANVAS_W - 2 * MARGIN_X
    if total_w > usable_w:
        # Shrink gaps if chain is too wide
        gap = max(0, (usable_w - n * NODE_W) // max(1, n - 1))
    else:
        gap = NODE_GAP
    total_w = n * NODE_W + (n - 1) * gap
    start_x = (CANVAS_W - total_w) // 2

    positioned_nodes = []
    node_by_id = {}
    for i, node in enumerate(nodes):
        x = start_x + i * (NODE_W + gap)
        positioned = dict(node)  # copy original fields (id, label, narration)
        positioned["x"] = x
        positioned["y"] = NODE_Y
        positioned["w"] = NODE_W
        positioned["h"] = NODE_H
        positioned["cx"] = x + NODE_W // 2
        positioned["cy"] = NODE_Y + NODE_H // 2
        positioned_nodes.append(positioned)
        node_by_id[node["id"]] = positioned

    # Layout edges as straight horizontal arrows
    positioned_edges = []
    for edge in edges:
        src = node_by_id.get(edge["from"])
        dst = node_by_id.get(edge["to"])
        if not src or not dst:
            continue
        positioned_edges.append({
            "from": edge["from"],
            "to": edge["to"],
            "x1": src["x"] + src["w"],
            "y1": src["cy"],
            "x2": dst["x"],
            "y2": dst["cy"],
        })

    # Layout callouts above their attached nodes
    positioned_callouts = []
    for callout in callouts:
        target = node_by_id.get(callout.get("attach_to"))
        if not target:
            continue
        cx = target["cx"] - CALLOUT_W // 2
        cy = target["y"] + CALLOUT_OFFSET_Y
        positioned_callouts.append({
            "id": callout["id"],
            "text": callout.get("text", ""),
            "x": cx,
            "y": cy,
            "w": CALLOUT_W,
            "h": CALLOUT_H,
            "attach_to": callout["attach_to"],
        })

    # Build timeline from narration
    timeline, total_duration = pace.compute_timeline(positioned_nodes)

    return {
        "canvas": {"width": CANVAS_W, "height": CANVAS_H},
        "fps": FPS,
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
    """Dispatch on layout type and return a render_ir dict."""
    layout_type = semantic_ir.get("layout", "causal_chain")
    if layout_type == "causal_chain":
        return layout_causal_chain(semantic_ir)
    raise ValueError(f"Unknown layout type: {layout_type}")
