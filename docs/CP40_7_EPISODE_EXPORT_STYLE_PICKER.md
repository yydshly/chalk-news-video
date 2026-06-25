# CP40.7: Episode Export Style Picker / Capability Guard

## 1. Baseline

- **Branch**: `test/cp40.6.2-ffprobe-audio-track-verification` (commit `64a8b76`)
- CP40.6 completed audio mux support with server-relative `audio_url`.
- CP40.6.2 added ffprobe-based audio stream verification.
- This CP (40.7) adds an explicit export style picker so users understand which style will be used for MP4 export.

## 2. Problem

The frontend preview supports 5 visual styles:

- `timeline_daily_v1` — 时间线日报风
- `breaking_news_v1` — 快讯大屏风
- `data_dashboard_v1` — 数据仪表盘风
- `research_briefing_v1` — 研究室简报风
- `podcast_cards_v1` — 播客卡片风

However, the Python MP4 renderer only supports `breaking_news_v1`. Previously, the export code silently ignored the selected preview style and always exported with `breaking_news_v1`, which was safe but misleading.

## 3. Goal

Make the export style explicit, declared by the backend, and surfaced in the UI with clear feedback when the preview style differs from the export style.

## 4. Backend Capabilities API

`GET /api/episode/export/capabilities` returns a structured document:

```json
{
  "ok": true,
  "default_style_id": "breaking_news_v1",
  "supported_styles": [
    {
      "id": "breaking_news_v1",
      "name": "快讯大屏风",
      "status": "supported",
      "reason": null
    }
  ],
  "unsupported_styles": [
    {
      "id": "timeline_daily_v1",
      "name": "时间线日报风",
      "status": "unsupported",
      "reason": "Python MP4 renderer not implemented yet"
    },
    ...
  ],
  "limits": {
    "width":  {"default": 720, "min": 360,  "max": 1080},
    "height": {"default": 1280, "min": 640,  "max": 1920},
    "fps":    {"default": 30,  "min": 1,    "max": 30}
  },
  "audio": {
    "supports_audio_mux": true,
    "allowed_extensions": [".aac", ".m4a", ".mp3", ".wav"],
    "requires_server_relative_outputs_url": true
  }
}
```

`supported_styles` contains only the styles that actually have a Python MP4 renderer. Currently that is `breaking_news_v1` only.

`unsupported_styles` lists all other known preview styles with a reason string.

`get_episode_export_capabilities()` in `src/episode_export.py` is the single source of truth.

## 5. Supported Styles

Currently **only** `breaking_news_v1` supports MP4 export.

All other styles (`timeline_daily_v1`, `data_dashboard_v1`, `research_briefing_v1`, `podcast_cards_v1`) do not have Python MP4 renderers and cannot be exported as MP4.

`ALLOWED_STYLE_IDS` in `src/episode_export.py` remains `frozenset(["breaking_news_v1"])`.

## 6. Frontend Export Style Selector

### HTML

Added in `web/index.html` above the "导出 MP4" button, inside the episode planner:

```html
<div class="episode-export-style-row">
  <label class="episode-export-style-label" for="select-episode-export-style">导出样式</label>
  <select id="select-episode-export-style" class="episode-export-style-select"></select>
</div>
<div id="episode-export-style-hint" class="episode-export-style-hint"></div>
```

Placed between the save button and the export button, alongside the existing audio mux option.

### JavaScript

- `loadEpisodeExportCapabilities()` fetches `GET /api/episode/export/capabilities` and stores result in `episodeExportCapabilities`.
- `renderEpisodeExportStyleOptions(capabilities)` populates the `<select>`:
  - `supported_styles` as enabled options with "（支持导出）" suffix
  - `unsupported_styles` as disabled options with "（暂不支持 MP4 导出）" suffix
  - Default selection is `capabilities.default_style_id`
- `updateEpisodeExportStyleHint()` shows a warning when preview style ≠ export style:
  - Preview is `timeline_daily_v1` but export is `breaking_news_v1` → warning displayed
- `getCurrentEpisodeExportStyleId()` returns the value from the export style selector (not the preview style selector).
- `startEpisodeMp4Export()` reads `style_id` from the export style selector and validates it against `supported_styles` before POSTing.
- The preview style selector's `change` event listener also calls `updateEpisodeExportStyleHint()`.

### CSS

New minimal styles for the picker row, select, and hint (including `.is-warning` variant).

## 7. Preview Style vs Export Style

When a user selects a non-`breaking_news_v1` preview style, the hint shows:

> "注意：当前预览为 timeline_daily_v1，MP4 导出将使用 breaking_news_v1。"

This makes it clear the MP4 output will differ visually from the preview.

## 8. Request Body

`POST /api/episode/export` body now uses the export style selector's value:

```json
{
  "contract": { ... },
  "style_id": "breaking_news_v1",
  "width": 720,
  "height": 1280,
  "fps": 30,
  "audio_url": null
}
```

`style_id` comes from `getCurrentEpisodeExportStyleId()` (the export style selector), not `selectEpisodePreviewStyle`.

## 9. Backend Validation

`ALLOWED_STYLE_IDS` continues to only contain `breaking_news_v1`. The backend rejects any other `style_id` with a 400 error:

```json
{"status": "failed", "error_type": "invalid_style_id", "message": "Unsupported style_id 'timeline_daily_v1'."}
```

The frontend guard in `startEpisodeMp4Export()` also checks `supported_styles` from the capabilities response before POSTing, showing an error message rather than letting the backend reject it.

## 10. What CP40.7 Does Not Do

- Does **not** implement Python renderer for `timeline_daily_v1`
- Does **not** implement Python renderer for `data_dashboard_v1`
- Does **not** implement Python renderer for `research_briefing_v1`
- Does **not** implement Python renderer for `podcast_cards_v1`
- Does **not** change `/api/jobs`
- Does **not** call real LLM
- Does **not** call real TTS
- Does **not** introduce Remotion
- Does **not** modify `render_episode_html.py` main visual logic
- Does **not** add new style options to `ALLOWED_STYLE_IDS`

## 11. Manual Test

1. Start server: `python -m src.server`
2. Open `http://127.0.0.1:8777`
3. Verify "导出样式" select is visible above the export button
4. Verify it defaults to "快讯大屏风（支持导出）"
5. Verify other styles appear as disabled "（暂不支持 MP4 导出）"
6. Open browser console — `loadEpisodeExportCapabilities()` should succeed with 200
7. Change preview style to something other than `breaking_news_v1`
8. Verify the hint shows the mismatch warning
9. Click export — verify request body has `style_id` matching the export selector (not the preview selector)
10. Verify export completes successfully
11. `GET /api/episode/export/capabilities` returns 200 with correct structure

## 12. Next Checkpoint

CP40.8: Episode export concurrent job limit — limit the number of concurrent running exports per session.
