"""Theme System V1: configurable visual themes for chalk-news-video.

Checkpoint 10: Theme System V1.
Checkpoint 10.1: Theme validation and solid-background hardening.
Checkpoint 11: Theme Layout System V1.

Themes only affect visual expression (colors, fills, strokes) in the renderer.
They do NOT modify business contracts: semantic_ir, dialogue_script, dialogue_manifest.

Usage:
    from src.theme import load_themes, resolve_theme, apply_theme, apply_theme_layout
    render_ir = apply_theme(render_ir, theme_name="podcast")
    render_ir = apply_theme_layout(render_ir)

    # CLI:
    python -m src.theme --theme podcast
    python -m src.theme --theme not_exist
    python -m src.theme --theme broken --config examples/invalid.themes.yaml
"""

import argparse
import re
import sys
from pathlib import Path

from .config_loader import load_yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_THEMES_PATH = PROJECT_ROOT / "config" / "themes.yaml"

# Color pattern: #RGB, #RRGGBB, rgba(...), transparent
_COLOR_PATTERN = re.compile(
    r"^(#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})|rgba\(\d+,\s*\d+,\s*\d+,\s*[\d.]+\)|transparent)$"
)

# Valid layout variants (CP11)
_VALID_LAYOUT_VARIANTS = (
    "chalkboard_v1",
    "podcast_v1",
    "research_desk_v1",
    "research_desk_v2",
    "notebook_v1",
    "news_card_v1",
    "causal_map_v1",
)

# Valid panel positions (CP11)
_VALID_PANEL_POSITIONS = ("side", "bottom_corner", "desk_cards")


def _is_valid_color(color: str) -> bool:
    """Check if a color string is valid."""
    return bool(_COLOR_PATTERN.match(color))


def validate_theme(theme: dict, theme_id: str) -> list[str]:
    """Validate a theme config dict.

    Returns:
        List of error strings (empty if valid).
    """
    errors = []

    def err(msg):
        errors.append(f"{theme_id}: {msg}")

    # 1. Must have top-level sections
    for section in ("background", "text", "node", "edge", "callout", "dialogue"):
        if section not in theme:
            err(f"missing section: {section}")

    # 2. background must have type and color
    bg = theme.get("background", {})
    if "type" not in bg:
        err("background.type is required")
    elif bg["type"] not in ("grid", "solid"):
        err(f"background.type must be 'grid' or 'solid', got '{bg['type']}'")
    if "color" not in bg:
        err("background.color is required")
    elif not _is_valid_color(bg["color"]):
        err(f"background.color is not a valid color: '{bg['color']}'")

    # 3. text must have title, body, subtitle
    text = theme.get("text", {})
    for field in ("title", "body", "subtitle"):
        if field not in text:
            err(f"text.{field} is required")
        elif not _is_valid_color(text[field]):
            err(f"text.{field} is not a valid color: '{text[field]}'")

    # 4. node must have fill, stroke, text
    node = theme.get("node", {})
    for field in ("fill", "stroke", "text"):
        if field not in node:
            err(f"node.{field} is required")
        elif not _is_valid_color(node[field]):
            err(f"node.{field} is not a valid color: '{node[field]}'")
    # badge_fill / badge_text are optional
    for field in ("badge_fill", "badge_text"):
        if field in node and not _is_valid_color(node[field]):
            err(f"node.{field} is not a valid color: '{node[field]}'")

    # 5. edge must have stroke, label
    edge = theme.get("edge", {})
    for field in ("stroke", "label"):
        if field not in edge:
            err(f"edge.{field} is required")
        elif not _is_valid_color(edge[field]):
            err(f"edge.{field} is not a valid color: '{edge[field]}'")

    # 6. dialogue must have host_accent, expert_accent, panel_fill, subtitle_fill
    dialogue = theme.get("dialogue", {})
    for field in ("host_accent", "expert_accent", "panel_fill", "subtitle_fill"):
        if field not in dialogue:
            err(f"dialogue.{field} is required")
        elif not _is_valid_color(dialogue[field]):
            err(f"dialogue.{field} is not a valid color: '{dialogue[field]}'")

    # 7. layout is optional, but if present must be valid (CP11)
    layout = theme.get("layout")
    if layout is not None:
        _validate_layout(layout, theme_id, err, errors)

    return errors


def _validate_layout(layout: dict, theme_id: str, err, errors: list):
    """Validate layout section of a theme."""
    # layout.variant is required
    variant = layout.get("variant")
    if variant is None:
        err("layout.variant is required")
    elif variant not in _VALID_LAYOUT_VARIANTS:
        err(f"layout.variant must be one of {_VALID_LAYOUT_VARIANTS}, got '{variant}'")

    # dialogue section: panel_w, panel_h, panel_y, subtitle_h, subtitle_font_size
    dialogue_layout = layout.get("dialogue", {})
    for field in ("panel_w", "panel_h", "panel_y"):
        if field in dialogue_layout:
            val = dialogue_layout[field]
            if not isinstance(val, (int, float)) or val <= 0:
                err(f"layout.dialogue.{field} must be a positive number, got '{val}'")

    for field in ("subtitle_h", "subtitle_font_size"):
        if field in dialogue_layout:
            val = dialogue_layout[field]
            if not isinstance(val, (int, float)) or val <= 0:
                err(f"layout.dialogue.{field} must be a positive number, got '{val}'")

    panel_position = dialogue_layout.get("panel_position")
    if panel_position is not None and panel_position not in _VALID_PANEL_POSITIONS:
        err(f"layout.dialogue.panel_position must be one of {_VALID_PANEL_POSITIONS}, got '{panel_position}'")


def load_themes(config_path: Path | str | None = None) -> dict:
    """Load all themes from config/themes.yaml.

    Returns:
        dict with keys: default_theme, themes (dict of theme configs)
    """
    path = Path(config_path) if config_path else DEFAULT_THEMES_PATH
    data = load_yaml(path)
    default_theme = data.get("default_theme", "chalkboard")
    themes = data.get("themes", {})
    return {
        "default_theme": default_theme,
        "themes": themes,
    }


def resolve_theme(
    theme_name: str | None,
    config_path: Path | str | None = None,
) -> dict:
    """Resolve a single theme by name.

    Args:
        theme_name: name of theme to resolve, or None for default
        config_path: optional override for themes.yaml path

    Returns:
        theme config dict (without 'name' wrapper)

    Raises:
        ValueError: if theme_name not found or fails validation
    """
    themes_data = load_themes(config_path)
    default_name = themes_data["default_theme"]
    themes = themes_data["themes"]

    resolved_name = theme_name if theme_name else default_name

    if resolved_name not in themes:
        available = sorted(themes.keys())
        raise ValueError(
            f"Theme '{resolved_name}' not found. Available themes: {available}"
        )

    theme = themes[resolved_name]

    # CP10.1: validate theme tokens
    errors = validate_theme(theme, resolved_name)
    if errors:
        raise ValueError(
            f"Theme '{resolved_name}' validation failed:\n  " + "\n  ".join(errors)
        )

    return dict(theme)


def apply_theme(
    render_ir: dict,
    theme_name: str | None = None,
    config_path: Path | str | None = None,
) -> dict:
    """Apply a theme to render_ir, writing render_ir["theme"].

    Args:
        render_ir: render_ir dict to augment
        theme_name: name of theme to apply, or None for default
        config_path: optional override for themes.yaml path

    Returns:
        render_ir with render_ir["theme"] added

    Raises:
        ValueError: if theme_name not found or fails validation
    """
    theme = resolve_theme(theme_name, config_path)
    theme_id = theme_name if theme_name else load_themes(config_path)["default_theme"]

    render_ir = dict(render_ir)
    render_ir["theme"] = {
        "id": theme_id,
        **theme,
    }

    return render_ir


def apply_theme_layout(render_ir: dict) -> dict:
    """Apply theme layout tokens to render_ir dialogue panels and subtitle.

    CP11: Theme Layout System V1.

    Reads render_ir.theme.layout.dialogue to compute:
    - render_ir.dialogue.speakers.host.panel {x, y, w, h}
    - render_ir.dialogue.speakers.expert.panel {x, y, w, h}
    - render_ir.subtitles.bar {h, y}
    - render_ir.subtitles.text_y

    Panel positions:
    - side: host on left (safe_margin), expert on right (canvas_w - margin - panel_w)
    - bottom_corner: both panels near bottom
    - desk_cards: host slightly inset left, expert slightly inset right

    Args:
        render_ir: render_ir with render_ir.theme already set

    Returns:
        render_ir with updated dialogue panels and subtitle layout
    """
    render_ir = dict(render_ir)

    theme = render_ir.get("theme", {})
    layout = theme.get("layout")
    dialogue_cfg = render_ir.get("dialogue")

    # No layout token or no dialogue → nothing to do
    if layout is None or dialogue_cfg is None:
        return render_ir

    dialogue_layout = layout.get("dialogue", {})
    panel_position = dialogue_layout.get("panel_position", "side")
    safe_margin = layout.get("canvas", {}).get("safe_margin", 48)
    panel_w = dialogue_layout.get("panel_w", 180)
    panel_h = dialogue_layout.get("panel_h", 90)
    panel_y = dialogue_layout.get("panel_y", 160)
    subtitle_h = dialogue_layout.get("subtitle_h", 64)

    canvas_w = render_ir.get("canvas", {}).get("width", 1280)
    canvas_h = render_ir.get("canvas", {}).get("height", 720)

    # Compute panel positions based on panel_position
    if panel_position == "side":
        host_x = safe_margin
        expert_x = canvas_w - safe_margin - panel_w
        host_y = panel_y
        expert_y = panel_y
    elif panel_position == "bottom_corner":
        host_x = safe_margin
        expert_x = canvas_w - safe_margin - panel_w
        host_y = canvas_h - panel_h - 20
        expert_y = canvas_h - panel_h - 20
    elif panel_position == "desk_cards":
        host_x = safe_margin + 20
        expert_x = canvas_w - safe_margin - panel_w - 20
        host_y = panel_y
        expert_y = panel_y
    else:
        # Default to side
        host_x = safe_margin
        expert_x = canvas_w - safe_margin - panel_w
        host_y = panel_y
        expert_y = panel_y

    # Update dialogue speakers panels
    if "speakers" in dialogue_cfg:
        speakers = dict(dialogue_cfg["speakers"])
        if "host" in speakers:
            speakers["host"] = dict(speakers["host"])
            speakers["host"]["panel"] = dict(speakers["host"].get("panel", {}))
            speakers["host"]["panel"]["x"] = host_x
            speakers["host"]["panel"]["y"] = host_y
            speakers["host"]["panel"]["w"] = panel_w
            speakers["host"]["panel"]["h"] = panel_h
        if "expert" in speakers:
            speakers["expert"] = dict(speakers["expert"])
            speakers["expert"]["panel"] = dict(speakers["expert"].get("panel", {}))
            speakers["expert"]["panel"]["x"] = expert_x
            speakers["expert"]["panel"]["y"] = expert_y
            speakers["expert"]["panel"]["w"] = panel_w
            speakers["expert"]["panel"]["h"] = panel_h
        dialogue_cfg = dict(dialogue_cfg)
        dialogue_cfg["speakers"] = speakers

    # Update subtitle bar
    subtitles = dict(render_ir.get("subtitles", {}))
    bar = dict(subtitles.get("bar", {}))
    bar_h = subtitle_h
    bar_y = canvas_h - bar_h - 12
    bar["h"] = bar_h
    bar["y"] = bar_y
    subtitles["bar"] = bar
    subtitles["text_y"] = bar_y + bar_h // 2 + 6
    # subtitle_font_size from layout (optional, default 22)
    subtitle_font_size = dialogue_layout.get("subtitle_font_size", 22)
    subtitles["font_size"] = subtitle_font_size

    render_ir["dialogue"] = dialogue_cfg
    render_ir["subtitles"] = subtitles

    return render_ir


def _cli_main():
    """CLI entry point for src.theme module."""
    parser = argparse.ArgumentParser(
        description="Theme system CLI (CP10.1). Validate and inspect themes.",
    )
    parser.add_argument(
        "--theme", type=str, default=None,
        help="Theme name to resolve. Omit to use default theme.",
    )
    parser.add_argument(
        "--config", type=str, default=None,
        help="Path to themes.yaml. Default: config/themes.yaml",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output resolved theme as JSON.",
    )

    args = parser.parse_args()

    try:
        theme = resolve_theme(args.theme, args.config)
        theme_id = args.theme if args.theme else load_themes(args.config)["default_theme"]

        if args.json:
            import json
            print(json.dumps({"id": theme_id, **theme}, indent=2))
        else:
            print(f"Theme '{theme_id}' is valid.")
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    _cli_main()
