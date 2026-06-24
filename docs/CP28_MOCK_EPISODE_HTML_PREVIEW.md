# CP28: Mock Episode HTML Preview

**Branch:** `feat/cp28-mock-episode-html-preview`
**Commit:** `feat(cp28): add mock episode html preview`
**Date:** 2026-06-24

---

## 1. Problem Statement

CP24–CP27 built the full production pipeline:

```
episodeItemList → episode_plan_v1 → episode_script_v1 → episode_audio_manifest_v1 → episode_render_ir_v1
```

Users could see the JSON contracts but had no visual preview of what a multi-news episode would look like.

CP28 generates a pure frontend mock HTML page from `episode_render_ir_v1` and displays it in the preview iframe.

---

## 2. buildMockEpisodeHtml() Rules

### Input
`renderIr`: `episode_render_ir_v1`

### Output
A complete HTML string (no external dependencies, no CDN, no remote images).

### Structure

```
<!DOCTYPE html>
<html>
  <head>
    <style>/* dark theme, news cards, responsive */</style>
  </head>
  <body>
    <div class="header">  ← episode title + theme + duration
    <div class="content">
      <div class="section-title">开场</div>  ← opening section
      <div class="section-title">新闻列表 (N 条)</div>  ← news segment cards
      <div class="section-title">结尾</div>  ← closing section
    </div>
    <div class="footer-bar">Mock HTML Preview · no real render</div>
  </body>
</html>
```

### News Card Visual Rules

| Role | Border | Background | Emphasis |
|------|--------|------------|----------|
| lead | `2px solid #f59e0b` | `#1a1a2e` | primary |
| supporting | `1px solid #374151` | `#111827` | secondary |

Each card shows: layout name, headline, badges, audio clip count.

---

## 3. previewMockEpisodeHtml() Flow

1. If `episodeItemList.length === 0` → error "请先加入新闻，再预览合集画面"
2. Build full pipeline: plan → script → manifest → render_ir (each step validated)
3. `buildMockEpisodeHtml(renderIr)` → HTML string
4. `validateMockEpisodeHtml(html)` → check structure + leakage
5. Revoke previous Blob URL (memory cleanup)
6. Create `Blob([html], { type: "text/html" })`
7. `latestEpisodePreviewUrl = URL.createObjectURL(blob)`
8. `previewHtml.src = latestEpisodePreviewUrl`
9. `switchToPreviewTab()` + `setPreviewMode("html")`
10. Banner shows "多新闻合集 Mock 预览"
11. No API calls, no job creation, no file writes

---

## 4. validateMockEpisodeHtml() Rules

| Condition | Level | Message |
|-----------|-------|---------|
| HTML empty | error | HTML 为空 |
| No `<!DOCTYPE html>` or `<html>` | error | HTML 必须包含 <!DOCTYPE html> 或 <html> |
| No news content | warning | HTML 可能不包含新闻内容 |
| API key / voice_id found | error | HTML 中不允许出现 API key 或 voice_id |
| External http links found | error | HTML 中不允许出现外部 http 链接 |

Returns `{ ok: boolean, warnings: string[], errors: string[] }`.

---

## 5. Blob URL Memory Management

- `latestEpisodePreviewUrl` holds the current Blob URL
- Before creating a new Blob, `URL.revokeObjectURL(latestEpisodePreviewUrl)` is called
- Ensures no memory leak on repeated preview clicks

---

## 6. UI: "预览合集画面" Button

Located below "生成视觉计划" in the episode planner section.

Click → full pipeline → mock HTML in iframe.

---

## 7. Constraints

- Pure frontend HTML/CSS, no external CDN
- No remote images or fonts
- No audio playback
- No file writes
- No job creation

---

## 8. Lightweight Verification Results

| Test | Result |
|------|--------|
| 0 items → "请先加入新闻" error | ✓ |
| 2 items → mock HTML generates cleanly | ✓ |
| iframe displays HTML | ✓ |
| lead news card highlighted (amber border) | ✓ |
| supporting news card normal style | ✓ |
| Opening + news list + closing sections present | ✓ |
| Banner shows "多新闻合集 Mock 预览" | ✓ |
| Repeated clicks → no Blob URL leak | ✓ |
| No API key / voice_id in HTML | ✓ |
| No external http links | ✓ |
| No /api/jobs call | ✓ |
| No outputs written | ✓ |

---

## 9. Current Limitations

- Mock HTML is static — no animation timeline
- No audio playback
- No subtitle overlay
- No real video export
- No outputs written to disk
- Preview resets on page refresh

---

## 10. Future Path

The mock HTML will be replaced by:
1. Real animation.html generation from `episode_render_ir`
2. Canvas-based video rendering
3. Audio synchronization
4. Subtitle overlay

---

## 11. Forbidden in This Change

- No /api/jobs call
- No real LLM / TTS calls
- No animation.html file generation
- No MP4 export
- No external CDN / remote images
- No outputs written
