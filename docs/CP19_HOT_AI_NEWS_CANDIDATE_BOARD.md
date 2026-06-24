# CP19: Hot AI News Candidate Board

**Branch:** `feat/cp19-hot-ai-news-candidate-board`
**Commit:** `6c92f48` (base)
**Date:** 2026-06-24

---

## 1. Problem Statement

Previously, the `hot_ai` mode automatically selected the top-ranked AI news item in the background. Users had no visibility into what news was available or agency to choose.

This CP upgrades the UX to:
1. Show a ranked list of hot AI news candidates
2. Let users select a specific item before generating
3. Use the selected news throughout the pipeline

---

## 2. Backend Changes

### 2.1 New Endpoint: `GET /api/hot-ai-news`

**Request:** `GET /api/hot-ai-news`

**Response:**
```json
{
  "ok": true,
  "count": 10,
  "items": [
    {
      "id": "hn_123456",
      "title": "OpenAI announces GPT-5...",
      "url": "https://openai.com/blog/...",
      "source": "Hacker News",
      "points": 342,
      "comments": 89,
      "final_score": 84.2,
      "rank_reason": "score=425 hotness_norm=85.0 story=83 ...",
      "summary": "[HN] OpenAI announces GPT-5..."
    }
  ]
}
```

**Behavior:**
- Fetches up to 10 candidates (dry-run — does not save files)
- Uses existing `fetch_hot_ai_news()` with `dry_run=False` and a temp output path
- Returns simplified fields (no raw HN metadata bloat)
- On error: returns `{ok: false, error: "..."}` with 500 status
- Does NOT expose API keys or full article text

### 2.2 `POST /api/jobs` — Selected News Support

New optional fields in `GenerateRequest`:
```json
{
  "selected_news_id": "hn_123456",
  "selected_news_title": "OpenAI announces GPT-5...",
  "selected_news_url": "https://openai.com/blog/...",
  "selected_news_source": "Hacker News"
}
```

**Pipeline behavior:**
- If `selected_news_id` is provided → write it directly to `latest_news.json` and skip auto-selection
- If not provided (hot_ai mode) → fallback to current auto-select logic (with print log)
- The `latest_news.json` uses the selected news title/url, so `render_ir.news.title` will be correct (fixing CP18.4)

---

## 3. Frontend Changes

### 3.1 Hot News Board (HTML)

Added `#hot-news-section` above the generation mode fieldset:
- Header with "🔥 今日热门 AI 新闻" title + refresh button
- Loading state: "加载中..."
- Error state: "新闻加载失败，请重试"
- Empty state: "暂无合适新闻"
- List of `hot-news-item` cards

### 3.2 News Item Card (CSS)

Each card shows:
- Rank badge (#1, #2, ...)
- News title (bold, 2-line clamp)
- Source + final_score + points + comments
- "选择这条" button

Selected state: green border + green background + green button.

### 3.3 JavaScript Logic

- `loadHotNews()` — fetches `/api/hot-ai-news` on page init if mode=hot_ai
- `renderHotNews(items)` — renders the list
- `selectHotNewsItem(index)` — sets `selectedNews`, highlights card, updates button text
- Mode radio change → reloads news list
- Refresh button → reloads news list
- Generate button text includes selected news title when available

### 3.4 Generate Button Text (CP19)

| Mode | No news selected | News selected |
|------|-----------------|---------------|
| 快速预览 | 生成快速预览 | 生成所选新闻快速预览 |
| 语音预览 | 生成语音预览 | 生成所选新闻语音预览 |
| 最终导出 | 导出 MP4 成片 | 导出所选新闻 MP4 成片 |

---

## 4. No Auto-Generate on Page Load

The page does NOT auto-generate on load. Users must:
1. See the hot news list
2. Click a news item (or skip/refresh)
3. Click a generate button

---

## 5. CP18.5 Checkbox Cleanup

The old `checkExport` checkbox is still in the DOM but its label is hidden by the generation mode radios. It is never directly checked/unchecked by the user in the new UX. The `no_export` flag is entirely controlled by the generation mode.

---

## 6. Security Notes

Same as V0.1 baseline:
- No API keys in any response
- No full article text fetched (HN metadata only)
- No arbitrary URL access from backend
- No user auth required

---

## 7. No Real TTS / No MP4 Export

This CP was verified using:
- Quick preview mode only (`mock_dialogue`, `no_export=true`)
- No real TTS calls
- No MP4 export

---

## 8. Current Limitations

- Source is still only Hacker News (no multi-source)
- Does not fetch full article text
- No news favorites / ignore list
- No multi-news stitching
- News list does not persist across page refreshes (re-fetched each time)
