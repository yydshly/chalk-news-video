"""Main pipeline: orchestrate the rendering process.

Usage:
    python -m src.pipeline --use-sample
    python -m src.pipeline --semantic-ir path/to/semantic_ir.json
"""


import argparse
import sys
from pathlib import Path

from . import export_video, layout, render_html
from .utils import load_json, save_json


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_SEMANTIC_PATH = PROJECT_ROOT / "examples" / "sample.semantic.json"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "latest"


def run_pipeline(semantic_ir_path, headless=True):
    """Run layout → render_html → export_video end-to-end."""
    semantic_ir = load_json(semantic_ir_path)

    # 1) layout: semantic_ir -> render_ir
    render_ir = layout.build_render_ir(semantic_ir)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    render_ir_path = save_json(render_ir, OUTPUT_DIR / "render_ir.json")
    print(f"[pipeline] wrote {render_ir_path}")

    # 2) render_html: render_ir -> animation.html
    html_path = render_html.render_html(render_ir, OUTPUT_DIR / "animation.html")
    print(f"[pipeline] wrote {html_path}")

    # 3) export_video: animation.html -> output.mp4
    video_path = export_video.export_video(
        html_path,
        OUTPUT_DIR / "output.mp4",
        fps=render_ir.get("fps", 30),
        width=render_ir["canvas"]["width"],
        height=render_ir["canvas"]["height"],
        headless=headless,
    )
    print(f"[pipeline] wrote {video_path}")

    return {
        "render_ir": render_ir_path,
        "animation_html": html_path,
        "output_video": video_path,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="chalk-news-video pipeline (V0.1 / Checkpoint 0)",
    )
    parser.add_argument(
        "--use-sample",
        action="store_true",
        help="Use the bundled examples/sample.semantic.json.",
    )
    parser.add_argument(
        "--semantic-ir",
        type=str,
        default=None,
        help="Path to a custom semantic_ir.json file.",
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run Chromium with a visible window (debug only).",
    )
    args = parser.parse_args(argv)

    if args.use_sample:
        semantic_ir_path = SAMPLE_SEMANTIC_PATH
    elif args.semantic_ir:
        semantic_ir_path = Path(args.semantic_ir)
    else:
        parser.error("Please provide --use-sample or --semantic-ir <path>.")

    if not semantic_ir_path.exists():
        print(f"Error: semantic_ir not found at {semantic_ir_path}", file=sys.stderr)
        sys.exit(1)

    try:
        result = run_pipeline(semantic_ir_path, headless=not args.no_headless)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)

    print("\nDone. Generated files:")
    for name, path in result.items():
        print(f"  {name}: {path}")


if __name__ == "__main__":
    main()
