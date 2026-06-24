# CP32: Episode HTML Artifact History

**Branch:** `feat/cp32-episode-html-artifact-history`
**Commit:** `feat(cp32): add episode html artifact history`
**Date:** 2026-06-25

---

## 1. Why Artifact History?

CP31 introduced saving mock episode HTML as server-side artifacts, but there was no way to revisit saved files after a page refresh. CP32 adds a history panel that persists across page loads.

---

## 2. Backend: GET /api/episode/html-history

**Response:**
```json
{
  "ok": true,
  "items": [
    {
      "filename": "episode_20260625_101010_abcd1234.html",
      "path": "/outputs/episode_previews/episode_20260625_101010_abcd1234.html",
      "file_path": "outputs/episode_previews/episode_20260625_101010_abcd1234.html",
      "created_at": "2026-06-25T10:10:10",
      "size": 12345
    }
  ]
}
```

### Scanning Rules & Security

| Rule | Detail |
|------|--------|
| Directory | Only `outputs/episode_previews/` |
| File type | Only `.html` files |
| Depth | No recursion into subdirectories |
| Path traversal | Blocked — filename must not contain `..`, `/`, `\` |
| Absolute path | Never returned |
| Content | Never read |
| Other directories | `outputs/jobs/`, `outputs/latest/` not scanned |
| Sort | By `st_mtime` descending (newest first) |
| Limit | Max 50 items |
| Missing dir | Returns `{ok: true, items: []}` |

---

## 3. Frontend: History Panel

Added below episode controls in `index.html`:

```html
<div id="episode-html-history-section">
  <div class="episode-html-history-header">📁 已保存合集 HTML</div>
  <div id="episode-html-history-list">
    <div class="episode-html-history-empty">暂无已保存合集 HTML</div>
  </div>
</div>
```

Each item shows: filename, created time, size, "打开" and "下载" buttons.

---

## 4. Frontend Functions

| Function | Purpose |
|---------|---------|
| `loadEpisodeHtmlHistory()` | Fetch `/api/episode/html-history`, update `episodeHtmlHistoryList`, call `renderEpisodeHtmlHistory()` |
| `renderEpisodeHtmlHistory(items)` | Render list or empty state |
| `openEpisodeHtmlArtifact(item, action)` | `action="open"` → iframe preview; `action="download"` → trigger browser download |

### Call Sites

| Location | Action |
|----------|--------|
| `init()` | `loadEpisodeHtmlHistory()` on startup |
| `saveMockEpisodeHtml()` success | `loadEpisodeHtmlHistory()` to refresh list |

---

## 5. Lightweight Verification Results

| Test | Result |
|------|--------|
| No `episode_previews` dir → `items: []` | ✓ |
| 2 HTML files → 2 items returned | ✓ |
| `file_path` is relative, not absolute | ✓ |
| History panel renders list on load | ✓ |
| Click "打开" → iframe loads `item.path` | ✓ |
| Click "下载" → browser download triggered | ✓ |
| New save → history list refreshes automatically | ✓ |
| No `/api/jobs` called | ✓ |
| No real LLM / TTS / MP4 | ✓ |
| Files not committed by git | ✓ |

---

## 6. Current Limitations

- Lists only mock episode HTML artifacts — not integrated with job history
- No delete functionality
- No rename functionality
- No HTML content inspection (only filename/metadata)
- No pagination beyond 50 items
- No merge with regular job history

---

## CP32.1: History Filename Safety Filter

**Branch:** `fix/cp32.1-history-filename-safety`
**Commit:** `fix(cp32.1): harden episode html history filename filtering`
**Date:** 2026-06-25

### Problem

CP32's history endpoint only checked `f.is_file() and f.suffix == ".html"`. There was no explicit filtering of suspicious filenames. While `iterdir()` doesn't recurse into subdirectories, the static route `/outputs/episode_previews/{filename}` already guards against `..`, `/`, and `\`, so the history endpoint should match that same safety boundary.

### Fix

Explicit filename filter before appending to results:
```python
filename = f.name
if ".." in filename or "/" in filename or "\\" in filename:
    continue
if not filename.endswith(".html"):
    continue
```

This is consistent with the `serve_episode_preview()` static route which blocks path traversal in the same way.

### Lightweight Verification Results

| Test | Result |
|------|--------|
| Normal `episode_xxx.html` returned | ✓ |
| Non-`.html` files not returned | ✓ |
| Subdirectory files not returned | ✓ |
| Filename with `..` not returned | ✓ |
| `file_path` still relative | ✓ |
| No HTML content read | ✓ |
| No `/api/jobs` called | ✓ |
| No real LLM / TTS / MP4 | ✓ |

