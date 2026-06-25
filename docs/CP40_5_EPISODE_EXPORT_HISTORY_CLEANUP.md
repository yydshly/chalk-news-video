# CP40.5: Episode Export History / Cleanup

## 1. Baseline

- **Branch**: `fix/cp40.4.1-export-button-lifecycle` (commit `5fb34ec`)
- CP40.4 completed async episode export with status polling and a download link on completion.
- CP40.4.1 fixed the export button lifecycle — button re-enables and shows "重新导出 MP4" after completed/failed.
- CP40.5 adds export history list, per-item open/delete, and bulk cleanup.

## 2. Goal

Allow users to view past episode exports, open MP4/HTML files, delete individual exports, and bulk-cleanup old exports — all scoped to `outputs/episode_exports/`, without touching the main `/api/jobs` pipeline.

## 3. Backend APIs

### GET /api/episode/exports

List recent episode export summaries.

**Query params**: `limit` (int, default 50, max 200)

**Response**:
```json
{
  "ok": true,
  "items": [...],
  "count": 5,
  "limit": 50
}
```

### DELETE /api/episode/exports/{export_id}

Delete a single episode export by ID.

**Response (success)**:
```json
{
  "ok": true,
  "deleted": true,
  "export_id": "episode_export_a2b3c4d5e6f7",
  "summary": { ... }
}
```

**Response (failure — running/pending)**:
```json
{
  "ok": false,
  "error": "Cannot delete export with status 'running'",
  "export_id": "episode_export_a2b3c4d5e6f7"
}
```

### POST /api/episode/exports/cleanup

Bulk-cleanup old exports, keeping the most recent N.

**Body**:
```json
{
  "keep_latest": 30,
  "dry_run": false
}
```

**Response**:
```json
{
  "ok": true,
  "keep_latest": 30,
  "dry_run": false,
  "deleted_count": 3,
  "deleted": [
    { "export_id": "...", "status": "completed", "mp4_size_bytes": 123456 }
  ],
  "errors": [],
  "skipped": [
    { "export_id": "...", "reason": "running" }
  ],
  "total_kept": 30
}
```

## 4. Export Summary Contract

Each item in the list response:
```json
{
  "export_id": "episode_export_a2b3c4d5e6f7",
  "status": "completed",
  "progress": 100,
  "message": "Export completed",
  "error_message": null,
  "style_id": "breaking_news_v1",
  "width": 720,
  "height": 1280,
  "fps": 30,
  "created_at": "2026-06-25T10:00:00",
  "updated_at": "2026-06-25T10:01:30",
  "mp4_url": "/outputs/episode_exports/episode_export_a2b3c4d5e6f7/output.mp4",
  "html_url": "/outputs/episode_exports/episode_export_a2b3c4d5e6f7/animation.html",
  "status_url": "/api/episode/exports/episode_export_a2b3c4d5e6f7",
  "meta_url": "/outputs/episode_exports/episode_export_a2b3c4d5e6f7/export_meta.json",
  "contract_url": "/outputs/episode_exports/episode_export_a2b3c4d5e6f7/contract.json",
  "mp4_size_bytes": 186061,
  "has_mp4": true,
  "has_html": true,
  "has_meta": true,
  "has_contract": true,
  "has_status": true
}
```

## 5. Delete Rules

1. Must pass `validate_export_id(export_id)` — pattern `^episode_export_[a-f0-9]{12}$`
2. Directory must exist under `outputs/episode_exports/`
3. Resolved path must stay within `EPISODE_EXPORT_DIR.resolve()` (no path traversal)
4. **Cannot delete running or pending exports** — returns 400
5. Only completed, failed, or unknown exports can be deleted
6. Uses `shutil.rmtree()` to remove the directory
7. Never deletes `EPISODE_EXPORT_DIR` itself or `.gitkeep`

## 6. Cleanup Rules

1. Lists all exports via `list_episode_exports()`
2. Sorts by `updated_at` descending
3. Skips running/pending exports (they go into `skipped`)
4. Keeps the most recent `keep_latest` completed/failed/unknown exports
5. Deletes the rest using `delete_episode_export()`
6. Default `keep_latest=30`, range 1–200
7. `dry_run=True` skips actual deletion

## 7. Frontend UI

### Location

Below the `episode-export-panel` in the preview tab (inside `tab-preview`).

### Elements

- `episode-export-history-panel` — container, shown when history loads
- `btn-refresh-episode-exports` — reloads the list
- `btn-cleanup-episode-exports` — triggers bulk cleanup with confirm dialog
- `episode-export-history-list` — scrollable list of history items

### Per-Item Display

- Short export ID (last 8 chars)
- Status badge (completed=failed=running=pending=unknown) with color coding
- MP4 size (formatted as B/KB/MB)
- Timestamp (updated_at or created_at)
- Actions: Open MP4, Open HTML, Delete (only if not running/pending)

### State Transitions

- Export completes → `loadEpisodeExportHistory()` called → history panel updates
- Page loads → `loadEpisodeExportHistory()` called in `init()`
- Refresh button → reloads list
- Delete → `confirm()` then DELETE API → refresh list
- Cleanup → `confirm()` with explanation → POST cleanup → refresh list

## 8. Manual Test Result

1. Start server: `python -m src.server`
2. Open `http://127.0.0.1:8777`
3. Add 2-4 hot AI news items to the episode planner
4. Click "预览合集画面" → mock HTML preview appears
5. Click "导出 MP4"
6. Wait for completion → "导出完成" + download link
7. History panel shows the new export
8. Click "打开 MP4" → MP4 opens
9. Click "删除" → item disappears from list
10. Create another export, click "清理旧导出" → older exports removed
11. Running export cannot be deleted (button absent)
12. Path traversal DELETE rejected with 400

## 9. What CP40.5 Does Not Do

- No database persistence
- No real LLM
- No real TTS
- No audio mux
- No `/api/jobs` integration
- No Remotion
- No cloud storage
- No automatic scheduled cleanup
- No per-export rename or tagging
- No export of non-breaking_news_v1 styles

## 10. Known Limitations

- Only lists exports that have a directory under `outputs/episode_exports/`
- Export directories created by other processes (outside the server) may not appear until next poll
- Cleanup confirm dialog is browser-native `confirm()` — not a custom modal
- No pagination (limit caps at 200 but frontend always requests 50)

## 11. Next Checkpoint

CP40.6: Audio mux support — accept an optional `audio_path` in the export request and mux WAV/MP3 into the MP4 using ffmpeg.
