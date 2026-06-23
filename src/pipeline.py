"""Main pipeline: orchestrate the rendering process.

Usage:
    # Checkpoint 4 (V0.9) — Auto pipeline
    python -m src.pipeline --auto --mock
    python -m src.pipeline --auto --news path/to/news.json --mock
    python -m src.pipeline --auto --source openai_news --profile minimax_m3_openai --repair
    python -m src.pipeline --auto --mock --no-export

    # Legacy modes
    python -m src.pipeline --use-sample
    python -m src.pipeline --semantic-ir path/to/semantic_ir.json
"""


import argparse
import subprocess
import sys
from pathlib import Path

from . import export_video, fetch_news, layout, render_html, validate_ir
from .utils import PROJECT_ROOT, load_json, save_json


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_SEMANTIC_PATH = PROJECT_ROOT / "examples" / "sample.semantic.json"
SAMPLE_NEWS_PATH = PROJECT_ROOT / "examples" / "sample_news.json"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "latest"
DEFAULT_SCHEMA_PATH = PROJECT_ROOT / "schema" / "semantic_ir.schema.json"


# ---------- auto pipeline helpers ----------


def _run_step(stage, fn, *args, **kwargs):
    """Run a stage function, wrapping RuntimeError with stage prefix."""
    try:
        return fn(*args, **kwargs)
    except RuntimeError as exc:
        print(f"[auto:{stage}] FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"[auto:{stage}] UNEXPECTED ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


def run_auto_pipeline(args):
    """Run the full auto pipeline: news → semantic_ir → validate → render → export."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---- Stage 1: determine news path ----
    if args.mock or args.news:
        # Use provided news file or default sample
        news_path = Path(args.news) if args.news else SAMPLE_NEWS_PATH
        if not news_path.exists():
            print(f"[auto:setup] news file not found: {news_path}", file=sys.stderr)
            sys.exit(1)
        print(f"[auto:news] using {news_path}")
    else:
        # Real mode: fetch news from RSS
        print(f"[auto:fetch_news] source={args.source}")
        news_dict = _run_step(
            "fetch_news",
            fetch_news.fetch_latest_news,
            source_id=args.source,
        )
        news_path = OUTPUT_DIR / "latest_news.json"
        save_json(news_dict, news_path)
        print(f"[auto:fetch_news] wrote {news_path}")

    # ---- Stage 2: generate_ir ----
    generate_cmd = [
        sys.executable, "-m", "src.generate_ir",
        "--news", str(news_path),
        "--output", str(OUTPUT_DIR / "semantic_ir.json"),
        "--validate",
    ]
    if args.mock:
        generate_cmd.append("--mock")
    if args.profile:
        generate_cmd += ["--profile", args.profile]
    if args.repair:
        generate_cmd.append("--repair")
        generate_cmd += ["--repair-attempts", str(args.repair_attempts)]
        generate_cmd.append("--save-invalid")

    print(f"[auto:generate_ir] running: {' '.join(generate_cmd)}")
    result = subprocess.run(generate_cmd, capture_output=False)

    semantic_ir_path = OUTPUT_DIR / "semantic_ir.json"
    if result.returncode == 0:
        pass  # normal case, use semantic_ir.json
    elif result.returncode == 5 and args.repair:
        # With --repair --save-invalid, generate_ir saves .invalid.json and returns 5
        # Check if we have a usable output
        if semantic_ir_path.exists():
            print(f"[auto:generate_ir] repair ended with warnings, using semantic_ir.json")
        else:
            invalid_path = OUTPUT_DIR / "semantic_ir.invalid.json"
            if invalid_path.exists():
                semantic_ir_path = invalid_path
                print(f"[auto:generate_ir] repair ended with warnings, using semantic_ir.invalid.json")
            else:
                print(f"[auto:generate_ir] exited with code 5 but no output found", file=sys.stderr)
                sys.exit(5)
    else:
        print(f"[auto:generate_ir] exited with code {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)
    if not semantic_ir_path.exists():
        print(f"[auto:generate_ir] output not found: {semantic_ir_path}", file=sys.stderr)
        sys.exit(1)

    # ---- Stage 3: validate_ir ----
    print(f"[auto:validate_ir] re-validating {semantic_ir_path}")
    semantic_ir = load_json(semantic_ir_path)
    issues = validate_ir.validate_semantic_ir(semantic_ir, DEFAULT_SCHEMA_PATH)
    if issues:
        errors = [i for i in issues if i.severity == "error"]
        print(f"[auto:validate_ir] FAILED with {len(errors)} error(s):", file=sys.stderr)
        for i in errors:
            print(f"  ERROR  [{i.code}] {i.path}: {i.message}", file=sys.stderr)
        sys.exit(1)
    print(f"[auto:validate_ir] PASSED")

    # ---- Stage 4: layout ----
    print(f"[auto:layout] building render_ir")
    render_ir = _run_step("layout", layout.build_render_ir, semantic_ir)
    render_ir_path = save_json(render_ir, OUTPUT_DIR / "render_ir.json")
    print(f"[auto:layout] wrote {render_ir_path}")

    # ---- Stage 5: render_html ----
    print(f"[auto:render_html] rendering animation.html")
    html_path = render_html.render_html(render_ir, OUTPUT_DIR / "animation.html")
    print(f"[auto:render_html] wrote {html_path}")

    # ---- Stage 6: export_video (optional) ----
    fps = render_ir.get("fps", 30)
    width = render_ir["canvas"]["width"]
    height = render_ir["canvas"]["height"]
    video_path = OUTPUT_DIR / "output.mp4"

    if args.no_export:
        print(f"[auto:export] SKIPPED (--no-export)")
    else:
        print(f"[auto:export] exporting video")
        video_path = _run_step(
            "export",
            export_video.export_video,
            html_path,
            video_path,
            fps=fps,
            width=width,
            height=height,
            headless=True,
        )
        print(f"[auto:export] wrote {video_path}")

    # ---- Summary ----
    total_duration = render_ir.get("total_duration", 0)
    print("\n=== Auto Pipeline Summary ===")
    print(f"  news_path:        {news_path}")
    print(f"  semantic_ir_path: {semantic_ir_path}")
    print(f"  render_ir_path:   {render_ir_path}")
    print(f"  animation_html:   {html_path}")
    if not args.no_export:
        print(f"  output_mp4:      {video_path}")
    print(f"  total_duration:  {total_duration}s")
    print(f"  fps:             {fps}")
    print(f"  canvas:          {width}x{height}")
    print("=" * 30)
    print("Done.")


# ---------- legacy pipeline ----------


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


# ---------- CLI ----------


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="chalk-news-video pipeline (V0.9 / Checkpoint 4)",
    )

    # Auto pipeline group
    auto_group = parser.add_argument_group("auto pipeline (Checkpoint 4)")
    auto_group.add_argument(
        "--auto", action="store_true",
        help="Enable full auto pipeline: news → semantic_ir → validate → render → export.",
    )
    auto_group.add_argument(
        "--mock", action="store_true",
        help="In auto mode, use mock LLM (no API key required). "
             "Uses examples/sample_news.json unless --news is provided.",
    )
    auto_group.add_argument(
        "--news", type=str, default=None,
        help="Path to a news JSON file. In auto mode, skips fetch_news.",
    )
    auto_group.add_argument(
        "--source", type=str, default=None,
        help="In auto real mode, pass source id to fetch_news (from sources.yaml).",
    )
    auto_group.add_argument(
        "--profile", type=str, default=None,
        help="In auto real mode, LLM profile name (from config/llm.yaml).",
    )
    auto_group.add_argument(
        "--repair", action="store_true",
        help="In auto real mode, enable LLM repair on validation failure.",
    )
    auto_group.add_argument(
        "--repair-attempts", type=int, default=2,
        help="Max repair attempts (default: 2).",
    )
    auto_group.add_argument(
        "--no-export", action="store_true",
        help="Skip video export (output.mp4). Useful for fast iteration.",
    )

    # Legacy modes
    legacy_group = parser.add_argument_group("legacy pipeline")
    legacy_group.add_argument(
        "--use-sample", action="store_true",
        help="Use the bundled examples/sample.semantic.json.",
    )
    legacy_group.add_argument(
        "--semantic-ir", type=str, default=None,
        help="Path to a custom semantic_ir.json file.",
    )
    legacy_group.add_argument(
        "--no-headless", action="store_true",
        help="Run Chromium with a visible window (debug only).",
    )

    args = parser.parse_args(argv)

    if args.auto:
        run_auto_pipeline(args)
        return

    # Legacy pipeline
    if args.use_sample:
        semantic_ir_path = SAMPLE_SEMANTIC_PATH
    elif args.semantic_ir:
        semantic_ir_path = Path(args.semantic_ir)
    else:
        parser.error("Please provide --auto, --use-sample, or --semantic-ir <path>.")

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
