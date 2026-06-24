# CP21: Generation Plan Panel

**Branch:** `feat/cp21-generation-plan-panel`
**Commit:** `feat(cp21): add generation plan confirmation panel`
**Date:** 2026-06-24

---

## 1. Problem Statement

CP19 introduced the news candidate board.
CP20 introduced the theme showcase gallery.
CP18.5 introduced generation modes.

But users lacked a unified confirmation area before clicking "Generate". They couldn't tell at a glance:
1. Which news is currently selected
2. Which video style is active
3. What generation mode is chosen
4. What outputs will be produced
5. How long it will take
6. Whether they are ready to generate

CP21 adds a "Generation Plan Confirmation Panel" that aggregates all these signals.

---

## 2. UI Design

### 2.1 Panel Location

Added between "Provider Config" and "Generate Button" in the left input panel.

### 2.2 Panel Content

```
📋 生成方案
新闻        | 请选择一条热门 AI 新闻   ← red when missing
视频风格   | 新闻卡片风
生成模式   | 快速预览
预计产物   | animation.html
预计耗时   | 较快
状态       | ✓ 已就绪              ← green/yellow/red
```

### 2.3 Status Messages

| State | Color | Message |
|-------|-------|---------|
| Ready | Green | ✓ 已就绪 |
| Missing news | Yellow | ⚠ 请先选择新闻 |
| Missing text | Yellow | ⚠ 请输入新闻文本 |
| Generating | Blue | ⟳ 正在生成... |

### 2.4 Gen Mode Output Mapping

| Mode | Name | Outputs | Time |
|------|------|---------|------|
| `fast` | 快速预览 | animation.html | 较快 |
| `voice` | 语音预览 | animation.html + dialogue.wav | 中等 |
| `export` | 最终导出 MP4 | animation.html + dialogue.wav + output.mp4 | 较慢 |

---

## 3. Implementation

### 3.1 HTML

```html
<div id="generation-plan-panel" class="generation-plan-panel">
  <div class="gen-plan-header">📋 生成方案</div>
  <div class="gen-plan-row">
    <span class="gen-plan-label">新闻</span>
    <span id="gen-plan-news" class="gen-plan-value gen-plan-news-empty">请选择一条热门 AI 新闻</span>
  </div>
  <div class="gen-plan-row">
    <span class="gen-plan-label">视频风格</span>
    <span id="gen-plan-theme" class="gen-plan-value">—</span>
  </div>
  <div class="gen-plan-row">
    <span class="gen-plan-label">生成模式</span>
    <span id="gen-plan-mode" class="gen-plan-value">快速预览</span>
  </div>
  <div class="gen-plan-row">
    <span class="gen-plan-label">预计产物</span>
    <span id="gen-plan-outputs" class="gen-plan-value">animation.html</span>
  </div>
  <div class="gen-plan-row">
    <span class="gen-plan-label">预计耗时</span>
    <span id="gen-plan-time" class="gen-plan-value">较快</span>
  </div>
  <div id="gen-plan-status-row" class="gen-plan-row gen-plan-status-row">
    <span class="gen-plan-label">状态</span>
    <span id="gen-plan-status" class="gen-plan-value gen-plan-status-ready">✓ 已就绪</span>
  </div>
</div>
```

### 3.2 CSS

Panel uses dark background with subtle border. Status row has a top border. Empty news state uses red italic text. Ready state is green, warning is yellow, working is blue.

### 3.3 JavaScript: `updateGenerationPlan()`

Called on:
1. Page init (`init()`)
2. Hot news loaded (`renderHotNews()`)
3. News item selected (`selectHotNewsItem()`)
4. Theme card clicked (via `selectTheme` change event → `renderThemeShowcase()`)
5. Gen mode switched (`genModeRadios` change)
6. News mode switched (`modeRadios` change)
7. Text input changed (`inputNews` input event)
8. Generation completed (done event)
9. Generation failed (error event)

Reuses `THEME_SHOWCASES` from CP20 for theme name mapping.

---

## 4. Button State in hot_ai Mode

Building on CP19.1:
- `mode=hot_ai` + no `selectedNews` → button text "请先选择一条新闻"
- CP21 additionally shows "⚠ 请先选择新闻" in the plan panel status
- Text mode and sample mode are unaffected

---

## 5. Payload Verification

Payload is unchanged from CP19.1. Still includes:
```json
{
  "mode": "hot_ai",
  "theme": "news_card_v1",
  "dialogue": true,
  "mock": false,
  "no_export": true,
  "llm_provider": "...",
  "tts_provider": "mock_dialogue",
  "repair": true,
  "selected_news_id": "...",
  "selected_news_title": "...",
  "selected_news_url": "...",
  "selected_news_source": "...",
  "max_turns": 10,
  "target_duration_sec": 45
}
```

---

## 6. Lightweight Verification

- Page loads with generation plan panel visible ✓
- No news selected → "请选择一条热门 AI 新闻" in red ✓
- Status shows "⚠ 请先选择新闻" in yellow ✓
- Select a news item → title appears in news row ✓
- Status changes to "✓ 已就绪" in green ✓
- Switch theme card → theme name updates ✓
- Switch gen mode → outputs and time update ✓
- Button text remains "请先选择一条新闻" until news selected ✓
- No real TTS calls ✓
- No MP4 export ✓

---

## 7. No Real TTS / No MP4 Export

All verification done with `mock_dialogue` and `no_export: true`.

---

## 8. Current Limitations

- Time estimates are static labels ("较快/中等/较慢"), not real timing data
- No cost estimation
- No theme sample previews in the panel
- Status does not reflect API key availability (only readiness)

---

## 9. Forbidden in This Change

- No real TTS calls
- No MP4 export
- No waiting for long tasks
- No backend pipeline changes
- No multi-news stitching
- No Remotion / digital human / cloud deployment / login / billing
- No `.env`, `API key`, `voice_id`, `outputs/jobs/job_*`, `outputs/latest` committed
- No arbitrary URL backend reading
- No debug prompt/response exposure
