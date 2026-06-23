"""Main pipeline: orchestrate the rendering process.

Usage:
    # Checkpoint 6 (V0.10) — Auto pipeline + TTS
    python -m src.pipeline --auto --mock
    python -m src.pipeline --auto --mock --tts --tts-profile mock
    python -m src.pipeline --auto --news path/to/news.json --mock
    python -m src.pipeline --auto --source openai_news --profile minimax_m3_openai --repair
    python -m src.pipeline --auto --mock --no-export

    # Checkpoint 7/8 (V0.11) — Dual-host dialogue
    python -m src.pipeline --auto --mock --tts --dialogue --host-profile mock_host --expert-profile mock_expert
    python -m src.pipeline --auto --mock --tts --dialogue --dialogue-profile mock_dialogue

    # Real LLM dialogue (CP8)
    python -m src.pipeline --auto --news outputs/latest/latest_news.json --profile minimax_m3_openai --tts --dialogue --dialogue-profile mock_dialogue

    # Legacy modes
    python -m src.pipeline --use-sample
    python -m src.pipeline --semantic-ir path/to/semantic_ir.json
"""


import argparse
import subprocess
import sys
from pathlib import Path

from . import export_video, fetch_news, layout, render_html, validate_ir
from .narration import generate_narration
from .narration_timing import apply_narration_timing
from .utils import PROJECT_ROOT, load_json, save_json


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_SEMANTIC_PATH = PROJECT_ROOT / "examples" / "sample.semantic.json"
SAMPLE_NEWS_PATH = PROJECT_ROOT / "examples" / "sample_news.json"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "latest"
AUDIO_DIR = OUTPUT_DIR / "audio"
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
    """Run the full auto pipeline: news → semantic_ir → validate → render → export.

    CP7.1 order with --tts --dialogue:
        generate_ir → validate_ir
        → (auto-generate dialogue_script.json if missing)
        → narration (dialogue_audio) → layout → apply_narration_timing
        → save render_ir → render_html → export_video(audio_path)

    Without TTS:
        generate_ir → validate_ir → layout → save render_ir → render_html → export_video
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Clean up artifacts from previous runs to avoid stale file reuse
    for artifact in [
        OUTPUT_DIR / "semantic_ir.json",
        OUTPUT_DIR / "semantic_ir.invalid.json",
        OUTPUT_DIR / "debug_validation_issues.json",
        OUTPUT_DIR / "debug_repair_prompt.txt",
        OUTPUT_DIR / "debug_repair_response.txt",
        OUTPUT_DIR / "narration_manifest.json",
        OUTPUT_DIR / "dialogue_manifest.json",
        OUTPUT_DIR / "dialogue_script.json",
        OUTPUT_DIR / "dialogue_script.invalid.json",
        OUTPUT_DIR / "debug_dialogue_prompt.txt",
        OUTPUT_DIR / "debug_dialogue_response.txt",
        OUTPUT_DIR / "debug_dialogue_validation_issues.json",
        OUTPUT_DIR / "debug_repair_prompt.txt",
        OUTPUT_DIR / "debug_repair_response.txt",
    ]:
        if artifact.exists():
            artifact.unlink()

    # Clean audio directory if TTS is enabled
    if args.tts and AUDIO_DIR.exists():
        import shutil
        shutil.rmtree(AUDIO_DIR)

    # ---- Stage 1: determine news path ----
    if args.mock or args.news:
        news_path = Path(args.news) if args.news else SAMPLE_NEWS_PATH
        if not news_path.exists():
            print(f"[auto:setup] news file not found: {news_path}", file=sys.stderr)
            sys.exit(1)
        print(f"[auto:news] using {news_path}")
    else:
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

    if result.returncode != 0:
        if result.returncode == 5:
            print(f"[auto:generate_ir] validation/repair failed", file=sys.stderr)
            print(f"[auto:generate_ir] see outputs/latest/debug_validation_issues.json", file=sys.stderr)
            print(f"[auto:generate_ir] invalid output is only for debugging, not used by pipeline", file=sys.stderr)
        else:
            print(f"[auto:generate_ir] exited with code {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)

    semantic_ir_path = OUTPUT_DIR / "semantic_ir.json"
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

    # ---- Stage 3a: narration TTS (optional, CP6/CP7) ----
    audio_path = None
    manifest = None
    if args.tts:
        if args.dialogue:
            # CP7.1 main path: dialogue_script → dialogue_manifest
            dialogue_script_path = OUTPUT_DIR / "dialogue_script.json"
            if not dialogue_script_path.exists():
                # Auto-generate dialogue_script
                print(f"[auto:dialogue] dialogue_script.json not found, generating...")
                gen_dialogue_cmd = [
                    sys.executable, "-m", "src.generate_dialogue",
                    "--semantic-ir", str(semantic_ir_path),
                    "--validate",
                ]
                if args.mock:
                    gen_dialogue_cmd.append("--mock")
                elif args.profile:
                    gen_dialogue_cmd += ["--profile", args.profile]
                    gen_dialogue_cmd.append("--repair")
                    gen_dialogue_cmd += ["--repair-attempts", str(args.repair_attempts)]

                dialogue_gen_result = subprocess.run(gen_dialogue_cmd, capture_output=False)
                if dialogue_gen_result.returncode != 0:
                    print(f"[auto:dialogue] generate_dialogue failed with code {dialogue_gen_result.returncode}", file=sys.stderr)
                    sys.exit(dialogue_gen_result.returncode)
                if not dialogue_script_path.exists():
                    print(f"[auto:dialogue] dialogue_script.json still not found after generation", file=sys.stderr)
                    sys.exit(1)
                print(f"[auto:dialogue] generated dialogue_script.json")
            else:
                print(f"[auto:dialogue] using existing dialogue_script.json")

            # Build narration command with dialogue_profile or host/expert profiles
            narration_cmd = [
                sys.executable, "-m", "src.narration",
                "--dialogue-script", str(dialogue_script_path),
                "--dialogue",
            ]
            if args.dialogue_profile:
                narration_cmd += ["--dialogue-profile", args.dialogue_profile]
                print(f"[auto:tts] generating dialogue audio: dialogue_profile={args.dialogue_profile}")
            else:
                narration_cmd += [
                    "--host-profile", args.host_profile,
                    "--expert-profile", args.expert_profile,
                ]
                print(f"[auto:tts] generating dialogue audio: host={args.host_profile}, expert={args.expert_profile}")
            manifest_path = OUTPUT_DIR / "dialogue_manifest.json"
        elif args.dialogue_legacy:
            # CP7 legacy path: semantic_ir.beats[].speaker → dialogue_manifest
            print(f"[auto:dialogue] using legacy semantic_ir speaker mode (compatibility preview)")
            print(f"[auto:tts] generating dialogue: host={args.host_profile}, expert={args.expert_profile}")
            narration_cmd = [
                sys.executable, "-m", "src.narration",
                "--semantic-ir", str(semantic_ir_path),
                "--dialogue-legacy",
                "--host-profile", args.host_profile,
                "--expert-profile", args.expert_profile,
            ]
            manifest_path = OUTPUT_DIR / "dialogue_manifest.json"
        else:
            # CP6 single-voice narration mode
            print(f"[auto:tts] generating narration with profile={args.tts_profile}")
            narration_cmd = [
                sys.executable, "-m", "src.narration",
                "--semantic-ir", str(semantic_ir_path),
                "--profile", args.tts_profile,
            ]
            manifest_path = OUTPUT_DIR / "narration_manifest.json"

        narration_result = subprocess.run(narration_cmd, capture_output=False)
        if narration_result.returncode != 0:
            print(f"[auto:tts] exited with code {narration_result.returncode}", file=sys.stderr)
            sys.exit(narration_result.returncode)

        if not manifest_path.exists():
            print(f"[auto:tts] manifest not found: {manifest_path.name}", file=sys.stderr)
            sys.exit(1)

        manifest = load_json(manifest_path)
        audio_path = manifest.get("combined_audio_path")
        if not audio_path:
            print(f"[auto:tts] combined_audio_path not in manifest", file=sys.stderr)
            sys.exit(1)
        audio_path = Path(audio_path)
        if not audio_path.exists():
            print(f"[auto:tts] audio file not found: {audio_path}", file=sys.stderr)
            sys.exit(1)
        print(f"[auto:tts] audio ready: {audio_path}")
    else:
        print(f"[auto:tts] SKIPPED (no --tts flag)")

    # ---- Stage 4: layout ----
    print(f"[auto:layout] building render_ir")
    render_ir = _run_step("layout", layout.build_render_ir, semantic_ir)

    # ---- Stage 4b: apply narration timing (CP6.1) ----
    if manifest is not None:
        print(f"[auto:layout] syncing render_ir.timeline to narration_manifest timing")
        render_ir = apply_narration_timing(render_ir, manifest)

    # Save render_ir BEFORE render_html so timing is committed
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
        export_kwargs = dict(
            fps=fps,
            width=width,
            height=height,
            headless=True,
        )
        if audio_path:
            export_kwargs["audio_path"] = audio_path
            print(f"[auto:export] muxing audio: {audio_path}")
        video_path = _run_step(
            "export",
            export_video.export_video,
            html_path,
            video_path,
            **export_kwargs,
        )
        print(f"[auto:export] wrote {video_path}")

    # ---- Summary ----
    total_duration = render_ir.get("total_duration", 0)
    print("\n=== Auto Pipeline Summary ===")
    print(f"  news_path:        {news_path}")
    print(f"  semantic_ir_path: {semantic_ir_path}")
    print(f"  render_ir_path:   {render_ir_path}")
    print(f"  animation_html:   {html_path}")
    if audio_path:
        print(f"  audio_path:       {audio_path}")
    if not args.no_export:
        print(f"  output_mp4:      {video_path}")
    print(f"  total_duration:  {total_duration}s")
    print(f"  fps:             {fps}")
    print(f"  canvas:          {width}x{height}")
    print(f"  tts_enabled:     {args.tts}")
    if args.dialogue:
        if args.dialogue_profile:
            print(f"  dialogue_mode:   True (dialogue_profile={args.dialogue_profile})")
        else:
            print(f"  dialogue_mode:   True (host={args.host_profile}, expert={args.expert_profile})")
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
        description="chalk-news-video pipeline (V0.11 / Checkpoint 7)",
    )

    # Auto pipeline group
    auto_group = parser.add_argument_group("auto pipeline (Checkpoint 4+)")
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

    # TTS group
    tts_group = parser.add_argument_group("TTS / narration (Checkpoint 6/7)")
    tts_group.add_argument(
        "--tts", action="store_true",
        help="Enable TTS narration generation.",
    )
    tts_group.add_argument(
        "--tts-profile", type=str, default="mock",
        help="TTS profile name (from config/tts.yaml) for single-voice mode. Default: mock.",
    )
    tts_group.add_argument(
        "--dialogue", action="store_true",
        help="Enable dual-host dialogue mode (CP7.1). Auto-generates dialogue_script.json if missing.",
    )
    tts_group.add_argument(
        "--dialogue-legacy", action="store_true",
        help="Use legacy semantic_ir.beats[].speaker path for dialogue (CP7 compatibility preview).",
    )
    tts_group.add_argument(
        "--dialogue-profile", type=str, default=None,
        help="Dialogue profile name from config/tts.yaml (e.g. mock_dialogue, minimax_dialogue). "
             "Takes priority over --host-profile/--expert-profile when set. (CP8)",
    )
    tts_group.add_argument(
        "--host-profile", type=str, default="mock_host",
        help="TTS profile for host speaker in dialogue mode. Default: mock_host.",
    )
    tts_group.add_argument(
        "--expert-profile", type=str, default="mock_expert",
        help="TTS profile for expert speaker in dialogue mode. Default: mock_expert.",
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
