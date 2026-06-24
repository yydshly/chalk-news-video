# CP22: Theme Sample Preview Library

**Branch:** `feat/cp22-theme-sample-preview-library`
**Commit:** `feat(cp22): add theme sample preview library`
**Date:** 2026-06-24

---

## 1. Problem Statement

CP20 introduced theme showcase cards with text descriptions, but users still couldn't intuitively see what each theme looks like visually.

CP22 adds "查看样例" (View Sample) buttons that load a static mock HTML preview directly in the right-side iframe — without creating any jobs, calling any APIs, or running any TTS.

---

## 2. Static Sample Files

Three simplified mock HTML files were created in `web/theme_samples/`:

| File | Theme | Content |
|------|-------|---------|
| `news_card_v1.html` | 新闻卡片风 | News card layout with fake headlines, sources, scores |
| `research_desk_v2.html` | AI 研究室风 | Research desk layout with model comparison table |
| `causal_map_v1.html` | 因果链地图 | Causal chain map with arrows showing cause-effect |

These are **static mock skeletons**, not real generated outputs. They contain:
- No API keys or secrets
- No real news content
- No voice IDs
- No debug prompts/responses

---

## 3. Backend: Whitelist Route

**New route in `src/server.py`:**

```
GET /examples/theme_samples/{filename}
```

**Security:**
- `filename` must be in a whitelist: `news_card_v1.html`, `research_desk_v2.html`, `causal_map_v1.html`
- Path traversal is blocked — only exact whitelisted filenames allowed
- Non-whitelisted requests return 404
- No arbitrary file serving

---

## 4. Frontend: THEME_SHOWCASES Extension

Each theme now has a `sample_url` field:

```javascript
const THEME_SHOWCASES = {
  news_card_v1: {
    id: "news_card_v1",
    name: "新闻卡片风",
    sample_url: "/examples/theme_samples/news_card_v1.html",
    // ...
  },
  // ...
};
```

---

## 5. UI: Theme Card "查看样例" Button

Each theme card in the showcase now has a "查看样例" button:

- Positioned at the bottom of the card
- Blue background on hover
- Does NOT change the selected theme

**Click behavior:**
1. Switches to "视频预览" tab
2. Clears previous preview
3. Loads sample HTML in the iframe
4. Shows "🎨 主题样例预览：{theme_name}" banner
5. Hides download links and audio player
6. Sets preview mode to HTML
7. Does NOT create any job
8. Does NOT call `/api/jobs`

---

## 6. No Job / No API Creation

Clicking "查看样例" only sets `previewHtml.src` — it:
- Does NOT call `loadHotNews()`
- Does NOT call `/api/jobs`
- Does NOT call any LLM or TTS
- Does NOT write to history
- Does NOT affect `lastResult`
- Does NOT change `selectedNews`

---

## 7. Payload Verification

Clicking "查看样例" produces **no payload**. It only changes the iframe `src`.

Generating a real video still uses the correct payload from CP19.1/CP21.

---

## 8. Lightweight Verification

- Page loads with theme cards showing "查看样例" button ✓
- Clicking news_card_v1 "查看样例" loads `news_card_v1.html` in iframe ✓
- Clicking research_desk_v2 "查看样例" loads `research_desk_v2.html` in iframe ✓
- Clicking causal_map_v1 "查看样例" loads `causal_map_v1.html` in iframe ✓
- Banner shows "🎨 主题样例预览：" + theme name ✓
- No download links shown during sample preview ✓
- Sample preview does NOT create any job ✓
- Backend route rejects non-whitelisted filenames with 404 ✓
- No real TTS calls ✓
- No MP4 export ✓

---

## 9. No Real TTS / No MP4 Export

All previews are static HTML files. No job is created.

---

## 10. Current Limitations

- Samples are static mock HTML, not real generated results
- No MP4 video samples
- No 9:16 (vertical) samples
- No real content — simplified visual skeletons only
- Samples don't update based on user's actual news selection

---

## 11. Forbidden in This Change

- No real TTS calls
- No MP4 export
- No job creation for samples
- No waiting for long tasks
- No outputs/jobs/job_* committed
- No outputs/latest committed
- No .env or API key or voice_id committed
- No arbitrary file reading on backend
- No debug prompt/response exposure
- No Remotion / digital human / cloud deployment / login / billing
