"""Theme System V1: configurable visual themes for chalk-news-video.

Checkpoint 10: Theme System V1.

Themes only affect visual expression (colors, fills, strokes) in the renderer.
They do NOT modify business contracts: semantic_ir, dialogue_script, dialogue_manifest.

Usage:
    from src.theme import load_themes, resolve_theme, apply_theme
    render_ir = apply_theme(render_ir, theme_name="podcast")
"""

from pathlib import Path

from .config_loader import load_yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_THEMES_PATH = PROJECT_ROOT / "config" / "themes.yaml"


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
        ValueError: if theme_name not found in themes
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
        ValueError: if theme_name not found
    """
    theme = resolve_theme(theme_name, config_path)
    theme_id = theme_name if theme_name else load_themes(config_path)["default_theme"]

    render_ir = dict(render_ir)
    render_ir["theme"] = {
        "id": theme_id,
        **theme,
    }

    return render_ir
