# CP29: Episode HTML Artifact Export

**Branch:** `feat/cp29-episode-html-artifact-export`
**Commit:** `feat(cp29): export mock episode html artifact`
**Date:** 2026-06-24

---

## 1. Problem Statement

CP28 generated a mock episode HTML preview as a Blob URL in browser memory. This is transient — lost on refresh, not accessible from history, and not reusable as a downstream artifact.

CP29 persists the mock HTML as a named file in `outputs/episode_previews/` via a secure backend endpoint.

---

## 2. Backend API

### `POST /api/episode/mock-html`

**Request body:**
```json
{
  "html": "<!DOCTYPE html>...",
  "episode_title": "今日 AI 前沿速览"
}
```

**Response (success):**
```json
{
  "ok": true,
  "path": "/outputs/episode_previews/episode_20260624_143052_今日_AI_前沿速览.html",
  "file_path": "outputs/episode_previews/episode_20260624_143052_今日_AI_前沿速览.html"
}
```

**Security checks:**
- HTML must contain `<!DOCTYPE html>` or `<html>` — 400 error otherwise
- No `api_key` or `voice_id` (case-insensitive) — 400 error
- No external `http://` or `https://` links (except localhost) — 400 error
- Filename generated server-side from timestamp + sanitized title
- No path traversal possible (filename is server-controlled)
- No `/api/jobs` created
- No `outputs/jobs/` or `outputs/latest/` written

### `GET /outputs/episode_previews/{filename}`

Serves saved HTML files. Filename is validated against traversal characters (`..`, `/`, `\`).

---

## 3. Frontend: "保存合集 HTML" Button

Located below "预览合集画面" in the episode planner section.

Click flow:
1. `episodeItemList.length === 0` → error "请先加入新闻，再保存合集 HTML"
2. Full pipeline: plan → script → manifest → render_ir (each validated)
3. `validateMockEpisodeHtml(html)` → block on error
4. `POST /api/episode/mock-html` with `{ html, episode_title }`
5. On success: `previewHtml.src = resp.path` → loads saved file in iframe
6. Banner: "已保存的合集 HTML 预览"
7. `latestEpisodeHtmlArtifact` state updated

---

## 4. State

- `latestEpisodeHtmlArtifact` — `{ path, file_path, created_at }`

---

## 5. Enhanced Mock HTML Markers

Each section now has stable CSS classes and `data-*` attributes for validation:

| Element | Class / Attribute |
|---------|------------------|
| News card | `class="mock-news-card"` `data-section-type="news_segment"` `data-role="lead\|supporting"` |
| Opening card | `class="mock-opening-card"` `data-section-type="opening"` |
| Closing card | `class="mock-closing-card"` `data-section-type="closing"` |

---

## 6. Enhanced Validation: `validateMockEpisodeHtml()`

| Condition | Level | Message |
|-----------|-------|---------|
| HTML empty | error | HTML 为空 |
| No `<!DOCTYPE html>` or `<html>` | error | HTML 必须包含 <!DOCTYPE html> 或 <html> |
| No `mock-news-card` | error | HTML 必须包含 mock-news-card |
| No `mock-opening-card` | error | HTML 必须包含开场区块 |
| No `mock-closing-card` | error | HTML 必须包含结尾区块 |
| API key / voice_id found | error | HTML 中不允许出现 API key 或 voice_id |
| External http/https links found | error | HTML 中不允许出现外部 http 链接 |

---

## 7. Output Directory

- `outputs/episode_previews/` — gitignored
- Files named `episode_{timestamp}_{safe_title}.html`
- No `outputs/jobs/` written
- No `outputs/latest/` written

---

## 8. Lightweight Verification Results

| Test | Result |
|------|--------|
| 0 items → "请先加入新闻" error | ✓ |
| 2 items → backend returns ok + path | ✓ |
| Saved path loads in iframe | ✓ |
| HTML contains `mock-news-card` | ✓ |
| HTML contains `mock-opening-card` / `mock-closing-card` | ✓ |
| No API key / voice_id in saved HTML | ✓ |
| No external http links in saved HTML | ✓ |
| `outputs/episode_previews/*.html` gitignored | ✓ |
| No /api/jobs called | ✓ |
| No TTS / MP4 / animation.html | ✓ |

---

## 9. Current Limitations

- Saved file is mock HTML — not final `animation.html`
- No audio playback
- No subtitle overlay
- No MP4 export
- No history integration
- File lost on server restart (no database)

---

## 10. Future Path

The saved HTML artifact will be replaced by:
1. Real `animation.html` generation from `episode_render_ir`
2. Multi-segment canvas rendering
3. Audio synchronization
4. History integration

---

## 11. Forbidden in This Change

- No /api/jobs call
- No real LLM / TTS calls
- No MP4 export
- No `outputs/jobs/` or `outputs/latest/` written
- No external CDN / remote images
