"""Export module: render animation.html to output.mp4 via Playwright + FFmpeg.

Strategy:
1. Serve animation.html via a local HTTP server on a random port.
2. Open the HTTP URL in headless Chromium at 1280x720.
3. Wait for window.__ANIMATION_READY__.
4. For each frame: call window.__setTime__(t), take a PNG screenshot.
5. Encode PNG sequence to MP4 with libx264 + yuv420p.
"""


import shutil
import socket
import subprocess
import tempfile
import threading
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler


def _probe_duration(media_path):
    """Return media duration in seconds via ffprobe, or 0.0 on failure."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(media_path),
            ],
            capture_output=True, text=True, errors="replace",
        )
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except Exception:
        pass
    return 0.0


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


def export_video(html_path, output_path, fps=30, width=1280, height=720, headless=True,
                 *, audio_path=None, scale_factor=2, crf=18, settle_ms=24):
    """Render animation.html to MP4.

    Args:
        html_path: path to animation.html
        output_path: path to output.mp4
        fps: frames per second
        width, height: viewport size
        headless: run Chromium headless
        audio_path: optional path to WAV/MP3 audio to mux into the video
        scale_factor: device pixel ratio for capture. >1 supersamples (renders at
            scale_factor*size then downscales to width:height) for crisper text/lines.
        crf: libx264 quality (lower = better, 18 ≈ visually lossless, 23 = old default).
        settle_ms: per-frame settle time so CSS animations finish before screenshot.

    Returns:
        Absolute path to the produced MP4.
    """
    check_ffmpeg()

    from playwright.sync_api import sync_playwright

    html_path = Path(html_path).resolve()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    html_dir = html_path.parent  # directory to serve from
    html_filename = html_path.name  # filename to serve at root

    # Use a local HTTP server instead of file:// URL for reliable Playwright loading
    class _QuietHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            # Serve from html_dir, not CWD
            super().__init__(*args, directory=str(html_dir), **kwargs)
        def log_message(self, format, *args):
            pass  # suppress request logging

    # Find a free port
    with socket.socket() as s:
        s.bind(("", 0))
        server_port = s.getsockname()[1]

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        frames_dir = tmp_dir / "frames"
        frames_dir.mkdir(parents=True, exist_ok=True)

        # Start HTTP server inside temp dir context
        server = HTTPServer(("127.0.0.1", server_port), _QuietHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        http_url = f"http://127.0.0.1:{server_port}/{html_filename}"

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=headless,
                    args=[
                        "--disable-web-security",
                        "--allow-running-insecure-content",
                        "--disable-dev-shm-usage",
                        "--no-sandbox",
                    ],
                )
                try:
                    context = browser.new_context(
                        viewport={"width": width, "height": height},
                        device_scale_factor=max(1, int(scale_factor)),
                    )
                    page = context.new_page()
                    page.on("pageerror", lambda exc: print(f"[pageerror] {exc}"))
                    page.on("console", lambda msg: print(f"[console.{msg.type}] {msg.text}")
                            if msg.type in ("error", "warning") else None)
                    page.goto(http_url, wait_until="domcontentloaded")
                    # Wait for page to settle and animation to initialize
                    page.wait_for_timeout(10000)
                    # Get total duration
                    total_duration = float(page.evaluate(
                        "window.__getTotalDuration__ ? window.__getTotalDuration__() : 60"
                    ))

                    total_frames = int(total_duration * fps) + 1
                    print(f"[export] duration={total_duration:.3f}s, frames={total_frames}")

                    frame_interval_ms = max(1, int(round(1000.0 / fps)))

                    for i in range(total_frames):
                        t = i / fps
                        page.evaluate(f"window.__setTime__({t})")
                        # Let the DOM/CSS animations settle before capturing
                        page.wait_for_timeout(settle_ms)
                        frame_path = frames_dir / f"frame_{i:05d}.png"
                        page.screenshot(path=str(frame_path), full_page=False)
                finally:
                    browser.close()
                    server.shutdown()
        except Exception as exc:
            if _is_playwright_not_installed(exc):
                raise RuntimeError(
                    "Playwright browser is not installed. "
                    "Please run: playwright install chromium"
                ) from exc
            raise

        # Encode PNG sequence to MP4
        frame_pattern = str(frames_dir / "frame_%05d.png")
        video_only_path = tmp_dir / "video_only.mp4"
        cmd = [
            "ffmpeg",
            "-y",
            "-framerate", str(fps),
            "-i", frame_pattern,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", str(crf),
            "-pix_fmt", "yuv420p",
            # Downscale supersampled frames to target size (lanczos = crisp text)
            "-vf", f"scale={width}:{height}:flags=lanczos",
            "-movflags", "+faststart",
            str(video_only_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
        if result.returncode != 0:
            print(result.stdout)
            print(result.stderr)
            raise RuntimeError(
                f"FFmpeg encoding failed (exit {result.returncode}). "
                "See stderr above for details."
            )

        # If audio is provided, mux it into the video
        if audio_path:
            audio_path = Path(audio_path)
            if not audio_path.exists():
                raise RuntimeError(f"Audio file not found: {audio_path}")
            print(f"[export] mux audio: {audio_path.name}")

            # If narration is longer than the animation, hold the last frame so the
            # full voiceover plays instead of being cut off by -shortest.
            video_dur = _probe_duration(video_only_path)
            audio_dur = _probe_duration(audio_path)
            pad = (audio_dur - video_dur) if (video_dur and audio_dur) else 0.0

            if pad > 0.1:
                print(f"[export] audio {audio_dur:.2f}s > video {video_dur:.2f}s, "
                      f"padding last frame by {pad:.2f}s")
                audio_mux_cmd = [
                    "ffmpeg",
                    "-y",
                    "-i", str(video_only_path),
                    "-i", str(audio_path),
                    "-vf", f"tpad=stop_mode=clone:stop_duration={pad:.3f}",
                    "-c:v", "libx264",
                    "-preset", "medium",
                    "-crf", str(crf),
                    "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart",
                    "-c:a", "aac",
                    "-shortest",
                    str(output_path),
                ]
            else:
                audio_mux_cmd = [
                    "ffmpeg",
                    "-y",
                    "-i", str(video_only_path),
                    "-i", str(audio_path),
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-shortest",
                    str(output_path),
                ]
            audio_result = subprocess.run(audio_mux_cmd, capture_output=True, text=True, errors="replace")
            if audio_result.returncode != 0:
                print(audio_result.stdout)
                print(audio_result.stderr)
                raise RuntimeError(
                    f"FFmpeg audio mux failed (exit {audio_result.returncode}). "
                    "See stderr above for details."
                )
            print(f"[export] muxed audio into video")

            # Check final MP4 duration
            try:
                probe_cmd = [
                    "ffprobe",
                    "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    str(output_path),
                ]
                probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, errors="replace")
                if probe_result.returncode == 0 and probe_result.stdout.strip():
                    duration = float(probe_result.stdout.strip())
                    print(f"[export] output duration={duration:.3f}s")
            except Exception:
                pass  # non-fatal
        else:
            # No audio, copy video_only to output_path (shutil.move handles cross-volume)
            import shutil
            shutil.copy2(str(video_only_path), str(output_path))

    return output_path.resolve()
