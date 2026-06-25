# CP40.4: UI Export Button + Polling

## 1. Baseline

- **Branch**: `fix/cp40.3.1-status-metadata-persistence` (commit `1d8e41e`)
- CP40.3.1 completed async episode export with status polling.
- CP40.4 wires the async export into the web UI: "导出 MP4" button, status display, download link.

## 2. Goal

Allow users to export the current episode contract to MP4 from the web UI, with live status polling and a download link on completion.

## 3. UI Entry Point

- **Button**: `btn-export-episode-mp4` in the episode planner section (`index.html`)
- **Panel**: `episode-export-panel` inside the preview tab (`index.html`)
- **States shown**: `episode-export-status` — text + color class per status

## 4. Frontend State

New state variables in `web/app.js`:

```js
let currentEpisodeExportId = null;       // active export_id
let currentEpisodeExportPollTimer = null; // setInterval handle
let currentEpisodeExportMp4Url = null;   // from POST response
```

Existing state reused:
- `latestEpisodeTemplateContract` — already saved by `previewEpisode()` and `saveMockEpisodeHtml()`
- `selectEpisodePreviewStyle` — read to determine export style

## 5. API Calls

**POST /api/episode/export**

```js
fetch("/api/episode/export", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    contract: latestEpisodeTemplateContract,  // episode_template_v1 dict
    style_id: "breaking_news_v1",
    width: 720,
    height: 1280,
    fps: 30,
  }),
})
```

- **No HTML strings submitted** — only the contract dict
- **No audio_path** — not supported in CP40.4
- Expects `202 Accepted` response with `export_id`, `status_url`, `mp4_url`

## 6. Polling Flow

```
User clicks "导出 MP4"
  → startEpisodeMp4Export()
    → fetch POST /api/episode/export
    → 202 received
    → startEpisodeExportPolling(statusUrl)
      → pollEpisodeExportStatus() every 1000ms
        → GET /api/episode/exports/{export_id}
        → renderEpisodeExportStatus() → update DOM
        → if completed: show download link, stop polling
        → if failed: stop polling
```

## 7. Status Rendering

`renderEpisodeExportStatus(statusData)` sets CSS class and text:

| status | class | text |
|--------|-------|------|
| pending | `is-pending` (amber) | "已加入导出队列..." |
| running | `is-running` (blue) | "正在导出 · {progress}% · {message}" |
| completed | `is-completed` (green) | "导出完成" |
| failed | `is-failed` (red) | "导出失败 · {error_message}" |

## 8. Download Link

On `completed`:
```js
episodeExportDownload.href = statusData.result.mp4_url || currentEpisodeExportMp4Url;
episodeExportDownload.style.display = "inline-block";
```

Points to `/outputs/episode_exports/{export_id}/output.mp4`.

## 9. Error Handling

- **No contract**: shows error status, does not call API
- **POST non-202**: throws with `data.message`
- **Network error**: renders failed status with "网络错误"
- **Duplicate clicks**: button disabled during export; `stopEpisodeExportPolling()` called before starting new export

## 10. Manual Test Result

Manual verification steps:
1. Start server: `python -m src.server`
2. Open `http://127.0.0.1:8777`
3. Add 2-4 hot AI news items to the episode planner
4. Click "预览合集画面" → mock HTML preview appears
5. Click "导出 MP4" button
6. Status shows "已加入导出队列..." then "正在导出 · 50% · 正在导出 MP4"
7. After completion: "导出完成" + red "下载 MP4" link
8. Click download link → MP4 file served

## 11. What CP40.4 Does Not Do

- No real LLM
- No real TTS
- No audio mux
- No `/api/jobs` integration
- No SSE
- No Remotion
- No history library integration
- No automatic cleanup
- No progress bar within ffmpeg encoding
- No export of non-breaking_news_v1 styles

## 12. Known Limitations

- Only `breaking_news_v1` style is accepted by the backend export endpoint; other styles fall back silently
- No per-frame ffmpeg progress — progress stays at 50% during MP4 encoding
- No export cancellation
- Download link href is set from the POST response `mp4_url` field, which is correct but the link only appears after `completed`; if the browser auto-plays the MP4 on click, the user may see a blank page briefly

## 13. Next Checkpoint

CP40.5: Add audio mux support — accept an optional `audio_path` in the export request and mux WAV/MP3 into the MP4 using ffmpeg.
