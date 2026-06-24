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

---

## CP19.1: Candidate Board Product Entry Cleanup

**Branch:** `fix/cp19.1-candidate-board-product-entry`
**Commit:** `fix/cp19.1` (this change)
**Date:** 2026-06-24

### 1. Default Entry Changed to Hot AI News

`index.html` now defaults to `hot_ai` mode instead of `sample`:
```html
<input type="radio" name="mode" value="hot_ai" checked>
```

`tryAutoLoadHotNews()` is called on `init()`, so page load automatically fetches `/api/hot-ai-news`.

### 2. Candidate Pool Moved Before Generate Button

New DOM order in the input panel:
1. 新闻来源（默认热门 AI 新闻）
2. 热门 AI 新闻候选池 ← moved here
3. 主题
4. 生成模式
5. 高级设置（Provider）
6. 生成按钮

Users now see and select news **before** picking style/generation mode.

### 3. Old Export Checkbox Hidden

`label-check-export` has `checkbox-export-hidden` class by default in HTML:
```html
<label class="checkbox-label checkbox-export-hidden" id="label-check-export">
```

`updateGenModeUI()` no longer removes `checkbox-export-hidden` — it always adds it. `checkExport.checked` is still set internally:
- `fast` mode: `false`
- `voice` mode: `false`
- `export` mode: `true`

### 4. Empty State Messages

| State | Message |
|-------|---------|
| Loading | "正在加载今日热门 AI 新闻..." |
| Load error | "新闻加载失败，请重试" |
| Empty list | "暂无合适新闻，请点击刷新重试" |

### 5. Block Generation Without News Selection (hot_ai mode)

When `mode === "hot_ai"` and `selectedNews` is null, clicking generate shows:
```
"请先选择一条新闻，或点击刷新重新加载候选"
```
No fallback auto-selection occurs. Button text also changes to "请先选择一条新闻".

### 6. Generate Button Text Changes

| Mode | News selected | No news (hot_ai) |
|------|--------------|-----------------|
| 快速预览 | 生成所选新闻快速预览 | 请先选择一条新闻 |
| 语音预览 | 生成所选新闻语音预览 | 请先选择一条新闻 |
| 最终导出 | 导出所选新闻 MP4 成片 | 请先选择一条新闻 |

Button text also updates when switching between modes via `updateGenModeUI()`.

### 7. Payload Includes selected_news_* Fields

For `mode=hot_ai` with selected news, `POST /api/jobs` payload includes:
```json
{
  "selected_news_id": "hn_...",
  "selected_news_title": "...",
  "selected_news_url": "...",
  "selected_news_source": "..."
}
```

Quick preview (fast mode) payload also includes:
```json
{
  "tts_provider": "mock_dialogue",
  "no_export": true,
  "dialogue": true,
  "max_turns": 10,
  "target_duration_sec": 45
}
```

### 8. Lightweight Verification (No Real TTS / No MP4 Export)

- Page opens with `hot_ai` radio checked ✓
- `/api/hot-ai-news` is called on page load ✓
- Candidate news list is displayed ✓
- Clicking generate without selection shows error message ✓
- After selecting a news item, button text changes ✓
- `checkExport` checkbox is hidden (not visible) ✓
- No real TTS calls, no MP4 export ✓

### 9. Forbidden in This Change

- No real TTS calls
- No MP4 export
- No waiting for long tasks
- No real LLM calls
- No Remotion / digital human / cloud deployment / login / billing
- No `.env`, `API key`, `voice_id`, `outputs/jobs/job_*`, `outputs/latest` committed
