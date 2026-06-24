# CP20: Theme Showcase Gallery

**Branch:** `feat/cp20-theme-showcase-gallery`
**Commit:** `feat(cp20): add theme showcase gallery`
**Date:** 2026-06-24

---

## 1. Problem Statement

The theme selector was previously a plain `<select>` dropdown:
```
news_card_v1
research_desk_v2
causal_map_v1
...
```

Users had no idea:
- Which theme suits which type of news
- What the visual difference between themes is
- Which theme is the current default / recommended
- Why `news_card_v1` is the recommended choice

CP20 upgrades theme selection from an "engineering config" to a "effect showcase".

---

## 2. Theme Showcase Data (CP20)

Three themes are defined in `web/app.js`:

```javascript
const THEME_SHOWCASES = {
  news_card_v1: {
    id: "news_card_v1",
    name: "新闻卡片风",
    desc: "适合快讯、产品发布、公司动态、热点新闻",
    tags: ["推荐", "新闻感强", "当前主推"],
    recommended: true,
  },
  research_desk_v2: {
    id: "research_desk_v2",
    name: "AI 研究室风",
    desc: "适合技术解读、研究报告、模型能力分析",
    tags: ["深度解读", "技术感"],
    recommended: false,
  },
  causal_map_v1: {
    id: "causal_map_v1",
    name: "因果链地图",
    desc: "适合解释事件原因、影响链条、监管变化",
    tags: ["逻辑分析", "结构化"],
    recommended: false,
  },
};
```

### 2.1 Theme Details

| Theme ID | Display Name | Suitable For | Tags |
|----------|-------------|--------------|------|
| `news_card_v1` | 新闻卡片风 | 快讯、产品发布、公司动态、热点新闻 | 推荐, 新闻感强, 当前主推 |
| `research_desk_v2` | AI 研究室风 | 技术解读、研究报告、模型能力分析 | 深度解读, 技术感 |
| `causal_map_v1` | 因果链地图 | 事件原因、影响链条、监管变化 | 逻辑分析, 结构化 |

---

## 3. UI Changes

### 3.1 Theme Showcase Section

Added a new section `#theme-showcase-section` between the hot news section and the generation mode fieldset:

```html
<div id="theme-showcase-section" class="theme-showcase-section">
  <div class="theme-showcase-header-row">
    <span class="theme-showcase-section-title">🎨 视频风格</span>
  </div>
  <div id="theme-showcase-list" class="theme-showcase-list"></div>
</div>
```

Each theme card shows:
- Theme name
- Description
- Tags (with "推荐" highlighted in gold)
- Selected state (green border + green background)

### 3.2 Hidden Theme Select (Compatibility)

The original `<select id="select-theme">` is kept in the DOM but hidden with CSS class `hidden`. It is still used for:
- Building the POST payload (`payload.theme = selectTheme.value`)
- Backend API communication

### 3.3 CSS for Theme Cards

Theme cards have:
- Default: dark background with subtle border
- Hover: blue border + slightly lighter background
- Selected: green border + green background + green name text
- "★ 推荐" badge in gold on recommended theme
- "推荐" tag highlighted in green

---

## 4. Interactions

### 4.1 Click Theme Card

1. Sets `selectTheme.value = theme.id`
2. Dispatches `change` event on `selectTheme`
3. Re-renders all theme showcase cards (highlighting the selected one)
4. Updates the recommended hint text

### 4.2 Default Theme

On page init, after loading theme list from `/api/themes`:
```javascript
if (themeOptions.includes("news_card_v1")) {
  selectTheme.value = "news_card_v1";
}
```

`news_card_v1` is always the default if available, regardless of what the backend returns as `default_theme`.

### 4.3 Recommended Hint Updates

The "💡 推荐体验配置" text now dynamically uses the selected theme's display name:
```
热门 AI 新闻 + 新闻卡片风 + minimax_m3_openai + mock_dialogue + 不导出 MP4
```

---

## 5. Payload Verification

Clicking "生成快速预览" with `news_card_v1` selected produces:
```json
{
  "theme": "news_card_v1",
  ...
}
```

Clicking "生成快速预览" with `causal_map_v1` selected produces:
```json
{
  "theme": "causal_map_v1",
  ...
}
```

The `selectTheme.value` (hidden) is always used for `payload.theme`.

---

## 6. Lightweight Verification

- Page opens with theme showcase visible (🎨 视频风格) ✓
- `news_card_v1` card is highlighted by default (green border) ✓
- Clicking `research_desk_v2` card switches highlight ✓
- `selectTheme.value` updates to `research_desk_v2` ✓
- Recommended hint text updates to "AI 研究室风" ✓
- Payload contains correct `theme` field ✓
- No real TTS calls ✓
- No MP4 export ✓

---

## 7. No Real TTS / No MP4 Export

Verified with:
- `mock_dialogue` TTS provider
- `no_export: true`
- Quick preview generation only

---

## 8. Current Limitations

- No real theme sample video thumbnails
- No theme scoring/ranking system
- No auto-recommended theme based on news content
- No 9:16 (vertical) theme support
- Theme data is hardcoded in `app.js` (not from backend config)
- Only 3 themes defined (backend may have more)

---

## 9. Forbidden in This Change

- No real TTS calls
- No MP4 export
- No generation of real sample videos per theme
- No waiting for long tasks
- No Remotion / digital human / cloud deployment / login / billing
- No `.env`, `API key`, `voice_id`, `outputs/jobs/job_*`, `outputs/latest` committed
- No arbitrary URL backend reading
- No debug prompt/response exposure
