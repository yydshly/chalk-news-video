# CP31: Episode HTML Artifact Export

**Branch:** `feat/cp31-episode-html-artifact-export`
**Commit:** `feat(cp31): export mock episode html artifact`
**Date:** 2026-06-24

---

## 1. Why HTML Artifact?

CP28 introduced a Blob URL mock preview of episode HTML. Blob URLs are browser-only and disappear on refresh. CP31 persists the mock HTML as a server-side artifact so it can be opened later, shared, and used as a stable preview reference.

---

## 2. Backend: POST /api/episode/mock-html

**Request:**
```json
{
  "html": "<!DOCTYPE html><html lang=\"zh-CN\">...",
  "episode_title": "今日 AI 前沿速览"
}
```

**Response (success):**
```json
{
  "ok": true,
  "path": "/outputs/episode_previews/episode_20240624_143052_a1b2c3d4.html",
  "file_path": "outputs/episode_previews/episode_20240624_143052_a1b2c3d4.html",
  "created_at": "2024-06-24T14:30:52.123456"
}
```

### Security Validations

| Check | Action on Failure |
|-------|------------------|
| HTML contains `<!DOCTYPE html>` or `<html>` | 400 error |
| No `api_key` / `api-key` (case-insensitive) | 400 error |
| No `voice_id` / `voice-id` (case-insensitive) | 400 error |
| No external `https?://` links (localhost allowed) | 400 error |

### Output Rules

- Output dir: `outputs/episode_previews/` (created automatically)
- Filename: `episode_{timestamp}_{uuid8}.html` — generated server-side
- No path traversal: `..`, `/`, `\` in filename rejected
- No user-supplied path accepted

---

## 3. Backend: GET /outputs/episode_previews/{filename}

Serves saved episode preview HTML files. Whitelist: only `.html` files inside `episode_previews/` directory.

---

## 4. Frontend: saveMockEpisodeHtml()

Flow:
1. Check `episodeItemList.length > 0`
2. Build episode contracts (same as preview flow)
3. Validate HTML with `validateMockEpisodeHtml()`
4. POST to `/api/episode/mock-html`
5. On success: set `latestEpisodeHtmlArtifact`, load returned path in preview iframe
6. Show banner: "已保存的合集 HTML 预览"

---

## 5. validateMockEpisodeHtml() Enhancements (CP31)

Added checks:
- Must contain `mock-news-card` CSS class on each news card
- Must contain opening section (warn if missing)
- Must contain closing section (warn if missing)
- No external `https?://` links (localhost allowed)
- No API key / voice_id

---

## 6. buildMockEpisodeHtml() Enhancement

Each news segment card now includes:
- `class="mock-news-card"`
- `data-section-type="news_segment"`

---

## 7. New UI Button

"保存合集 HTML" button below "预览合集画面" in the episode controls section.

---

## 8. .gitignore Update

```
outputs/episode_previews/*.html
!outputs/episode_previews/.gitkeep
```

---

## 9. Lightweight Verification Results

| Test | Result |
|------|--------|
| 0 news → error "请先加入新闻" | ✓ |
| 2 news → POST succeeds, returns ok + path | ✓ |
| Saved file accessible via `/outputs/episode_previews/{file}` | ✓ |
| HTML contains `mock-news-card` | ✓ |
| HTML contains no API key / voice_id | ✓ |
| HTML contains no external http links | ✓ |
| File not committed by git | ✓ |
| No `/api/jobs` called | ✓ |
| No real LLM / TTS / MP4 | ✓ |

---

## 10. Current Limitations

- Saved HTML is mock — not a real `animation.html` from the render pipeline
- No audio, no subtitles, no MP4
- Not integrated with job history
- No delete / cleanup of old artifacts
