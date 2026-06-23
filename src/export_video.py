"""Export module: render animation.html to output.mp4 via Playwright + FFmpeg.

Strategy:
1. Open animation.html in headless Chromium at 1280x720.
2. Wait for window.__ANIMATION_READY__.
3. For each frame: call window.__setTime__(t), take a PNG screenshot.
4. Encode PNG sequence to MP4 with libx264 + yuv420p.
"""


import shutil
import subprocess
import tempfile
from pathlib import Path


def check_ffmpeg():
    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "FFmpeg not found in PATH. "
            "Install FFmpeg (e.g. `choco install ffmpeg` on Windows, "
            "`brew install ffmpeg` on macOS, `sudo apt install ffmpeg` on Linux) "
            "and make sure `ffmpeg` is callable from the command line."
        )


def _is_playwright_not_installed(exc):
    msg = str(exc).lower()
    return (
        "executable doesn't exist" in msg
        or "playwright install" in msg
        or "browser was not found" in msg
    )


def export_video(html_path, output_path, fps=30, width=1280, height=720, headless=True):
    """Render animation.html to MP4.

    Args:
        html_path: path to animation.html
        output_path: path to output.mp4
        fps: frames per second
        width, height: viewport size
        headless: run Chromium headless

    Returns:
        Absolute path to the produced MP4.
    """
    check_ffmpeg()

    from playwright.sync_api import sync_playwright

    html_path = Path(html_path).resolve()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    file_url = "file:///" + str(html_path).replace("\\", "/")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        frames_dir = tmp_dir / "frames"
        frames_dir.mkdir(parents=True, exist_ok=True)

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=headless)
                try:
                    context = browser.new_context(
                        viewport={"width": width, "height": height},
                        device_scale_factor=1,
                    )
                    page = context.new_page()
                    page.on("pageerror", lambda exc: print(f"[pageerror] {exc}"))
                    page.on("console", lambda msg: print(f"[console.{msg.type}] {msg.text}")
                            if msg.type in ("error", "warning") else None)
                    page.goto(file_url)
                    page.wait_for_function(
                        "window.__ANIMATION_READY__ === true",
                        timeout=15000,
                    )

                    total_duration = float(page.evaluate("window.__getTotalDuration__()"))
                    total_frames = int(total_duration * fps) + 1
                    print(f"[export] duration={total_duration:.3f}s, frames={total_frames}")

                    frame_interval_ms = max(1, int(round(1000.0 / fps)))

                    for i in range(total_frames):
                        t = i / fps
                        page.evaluate(f"window.__setTime__({t})")
                        # Let the DOM settle
                        page.wait_for_timeout(15)
                        frame_path = frames_dir / f"frame_{i:05d}.png"
                        page.screenshot(path=str(frame_path), full_page=False)
                finally:
                    browser.close()
        except Exception as exc:
            if _is_playwright_not_installed(exc):
                raise RuntimeError(
                    "Playwright browser is not installed. "
                    "Please run: playwright install chromium"
                ) from exc
            raise

        # Encode PNG sequence to MP4
        frame_pattern = str(frames_dir / "frame_%05d.png")
        cmd = [
            "ffmpeg",
            "-y",
            "-framerate", str(fps),
            "-i", frame_pattern,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-vf", f"scale={width}:{height}",
            "-movflags", "+faststart",
            str(output_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(result.stdout)
            print(result.stderr)
            raise RuntimeError(
                f"FFmpeg encoding failed (exit {result.returncode}). "
                "See stderr above for details."
            )

    return output_path.resolve()
