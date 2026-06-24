# CP40.1: Minimal Episode Stage MP4 Export Prototype

## 1. Baseline

- **Branch**: `fix/cp40.0.1-seek-shim-visibility-wiring` (commit `48cf6c0`)
- **CP40.0** added `src/render_episode_html.py` with `render_episode_stage_html()` and `render_episode_stage_html_to_file()`.
- **CP40.0.1** fixed seek shim visibility wiring: `window.__getTotalDuration__()`, `window.__setTime__(t)`, `data-appear-at`, `stage-layer`, `is-visible`, `data-export-seek`, `data-progress-fill`.
- **Existing export path**: `src/export_video.py` → Playwright headless Chromium → `page.screenshot()` per frame → ffmpeg encode MP4.

## 2. Goal

Validate end-to-end MP4 export of a 9:16 episode stage HTML using mock contract data, without touching real LLM, real TTS, audio, or the `/api/jobs` system.

## 3. Existing Export Path Reused

| Module | Function | Role |
|--------|----------|------|
| `src/render_episode_html.py` | `render_episode_stage_html_to_file()` | Generate self-contained HTML from contract |
| `src/export_video.py` | `export_video()` | Playwright capture + ffmpeg encode |

Signature used:
```python
export_video(
    html_path=str,   # path to animation.html
    output_path=str,  # path to output.mp4
    fps=30,
    width=720,       # 9:16 height
    height=1280,      # 9:16 height
    headless=True,
    audio_path=None,  # no real audio this checkpoint
)
```

## 4. New Prototype Script

```
scripts/prototype_export_episode_stage_mp4.py
```

Usage:
```bash
python scripts/prototype_export_episode_stage_mp4.py
python scripts/prototype_export_episode_stage_mp4.py --out .tmp/cp40_1_episode_stage.mp4
```

## 5. Mock Contract Used

`episode_template_v1` with:
- `template_id: "breaking_news_v1"`
- 1 lead news card + 2 supporting news cards
- Timeline markers: opening / lead / supporting / closing
- Estimated duration: 14 seconds

## 6. HTML Generation Step

`render_episode_stage_html_to_file(contract, html_path)` produces a self-contained HTML document with:
- Inline CSS (breaking news dark theme, 9:16 aspect ratio)
- Inline SVG cartoon anchor with expression/action animations
- `window.__ANIMATION_READY__`, `window.__getTotalDuration__()`, `window.__setTime__(t)` timing shim
- `data-export-seek` seek-mode overrides for deterministic Playwright frame capture

## 7. export_video Invocation

```python
export_video(
    html_path=html_path,   # temporary animation.html
    output_path=mp4_path,   # .tmp/cp40_1_episode_stage.mp4
    fps=30,
    width=720,
    height=1280,
    audio_path=None,
)
```

## 8. 9:16 Viewport

The prototype targets **720×1280** (portrait 9:16). The `export_video()` function passes `width`/`height` to both Playwright's `browser.new_context(viewport={...})` and ffmpeg's `-vf scale=720:1280`. The existing `export_video()` does NOT force 1280×720; it respects the passed dimensions.

## 9. Result

**Status**: `success` / `failed` (environment-dependent)

**Output**: `.tmp/cp40_1_episode_stage.mp4`
**HTML**: `.tmp/cp40_1_animation.html` (temporary intermediate)

If Playwright Chromium or ffmpeg is not installed, the script exits with a clear error message.

## 10. What CP40.1 Does Not Do

- No real LLM calls
- No real TTS / audio generation
- No `/api/jobs` endpoint
- No server changes
- No UI changes
- No new formal API endpoints
- No Remotion
- No history database integration
- No commit of `.tmp/` or `outputs/`

## 11. Known Limitations

- `export_video()` currently encodes with ffmpeg `-vf scale=width:height` AFTER capturing frames at the Playwright viewport size. If Playwright fails to capture at 720×1280 (e.g. viewport constraints), the output may not be true 9:16 — requires verification in CP40.2.
- No audio mux in this prototype (audio_path=None).
- Progress bar is CSS-driven; during seek mode (`data-export-seek="1"`) the CSS `mockProgressFill` animation is paused and width is driven by JS.

## 12. Next Checkpoint

CP40.2: Integrate export into formal `/api/episode/export` endpoint, add audio mux support, and validate 720×1280 scale end-to-end.
