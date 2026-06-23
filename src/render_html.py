"""Render module: inject render_ir into renderer/template.html and write animation.html."""

import json
from pathlib import Path

from jinja2 import Template

from .utils import read_text


PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = PROJECT_ROOT / "renderer" / "template.html"


def render_html(render_ir, output_path):
    """Render animation.html by injecting render_ir into the Jinja template.

    Returns the absolute path to animation.html.
    """
    template_src = read_text(TEMPLATE_PATH)
    template = Template(template_src)

    # Pass render_ir as both an object (for Jinja attribute access) and a JSON
    # string (for the browser to consume).
    render_ir_json = json.dumps(render_ir, ensure_ascii=False)

    html = template.render(
        render_ir=render_ir,
        render_ir_json=render_ir_json,
    )

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    return out.resolve()
