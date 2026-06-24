# CP29: Video Style Gallery Expansion

**Branch:** `feat/cp29-video-style-gallery-expansion`
**Commit:** `feat(cp29): expand video style gallery`
**Date:** 2026-06-24

---

## 1. Problem Statement

The original theme showcase had only 3 themes — insufficient for a product-grade "video style library." CP29 expands to 12 themes with categorization, sample previews, and full layout mapping for the episode render pipeline.

---

## 2. Theme List (12 Themes)

| ID | Name | Category |
|----|------|---------|
| `news_card_v1` | 新闻卡片风 | 新闻快讯 |
| `research_desk_v2` | AI 研究室风 | 技术解读 |
| `causal_map_v1` | 因果链地图 | 逻辑分析 |
| `timeline_brief_v1` | 时间线快报 | 多新闻日报 |
| `data_dashboard_v1` | 数据仪表盘 | 数据图表 |
| `breaking_news_v1` | 突发新闻快讯 | 新闻快讯 |
| `product_launch_v1` | 产品发布会 | 产品发布 |
| `paper_digest_v1` | 论文速读 | 技术解读 |
| `podcast_cards_v1` | 双人观点卡 | 观点解读 |
| `dev_terminal_v1` | 开发者终端风 | 开发者技术 |
| `magazine_cover_v1` | 杂志封面风 | 专题封面 |
| `opinion_column_v1` | 观点评论风 | 观点解读 |

---

## 3. Theme Data Fields

Each theme includes: `id`, `name`, `category`, `desc`, `best_for`, `tags`, `recommended`, `visual_density`, `motion_level`, `sample_url`.

UI card displays: name, category badge, desc, best_for, tags, "查看样例" button.

---

## 4. Theme Sample Files

Location: `web/theme_samples/`

Files: `news_card_v1.html`, `research_desk_v2.html`, `causal_map_v1.html` (pre-existing) + 9 new:

| File | Theme |
|------|-------|
| `timeline_brief_v1.html` | 时间线快报 |
| `data_dashboard_v1.html` | 数据仪表盘 |
| `breaking_news_v1.html` | 突发新闻快讯 |
| `product_launch_v1.html` | 产品发布会 |
| `paper_digest_v1.html` | 论文速读 |
| `podcast_cards_v1.html` | 双人观点卡 |
| `dev_terminal_v1.html` | 开发者终端风 |
| `magazine_cover_v1.html` | 杂志封面风 |
| `opinion_column_v1.html` | 观点评论风 |

All samples: pure static HTML/CSS, no external CDN, no remote images, no API keys.

---

## 5. Backend Whitelist

`src/server.py` `_THEME_SAMPLES` frozenset updated to include all 12 filenames. Whitelist is enforced on `/examples/theme_samples/{filename}` — path traversal blocked.

---

## 6. episode_render_ir Layout Mapping

Updated in `buildEpisodeRenderIrFromContracts()`:

| Theme ID | Layout |
|----------|--------|
| `news_card_v1` (default) | `news_card_stack` |
| `research_desk_v2` | `research_desk_panel` |
| `causal_map_v1` | `causal_chain_panel` |
| `timeline_brief_v1` | `timeline_panel` |
| `data_dashboard_v1` | `dashboard_panel` |
| `breaking_news_v1` | `breaking_news_panel` |
| `product_launch_v1` | `product_launch_panel` |
| `paper_digest_v1` | `paper_digest_panel` |
| `podcast_cards_v1` | `podcast_cards_panel` |
| `dev_terminal_v1` | `terminal_panel` |
| `magazine_cover_v1` | `magazine_cover_panel` |
| `opinion_column_v1` | `opinion_column_panel` |
| unknown | `news_card_stack` (fallback) |

---

## 7. UI Changes

- Theme showcase section header updated
- Each card now shows: `category` badge, `best_for`, in addition to existing fields
- CSS: `.theme-showcase-category` (blue badge) and `.theme-showcase-bestfor` (gray sub-label) added
- "查看样例" button works for all 12 themes

---

## 8. Backward Compatibility

- `selectTheme` value unchanged — existing single-news generation not affected
- `episode_plan.theme` / `generation_mode` passthrough preserved
- `buildEpisodePlan()` and `validateEpisodePlan()` untouched

---

## 9. Lightweight Verification Results

| Test | Result |
|------|--------|
| 12 themes displayed in gallery | ✓ |
| Each theme has category badge | ✓ |
| Each theme has "查看样例" button | ✓ |
| Sample click loads HTML in iframe | ✓ |
| Theme card click sets `selectTheme.value` | ✓ |
| New themes map to correct layouts in render_ir | ✓ |
| Unknown theme → fallback to `news_card_stack` | ✓ |
| No external CDN / remote images in samples | ✓ |
| No API key / voice_id in samples | ✓ |
| No /api/jobs called | ✓ |

---

## 10. Current Limitations

- Samples are static mock HTML — not real animation templates
- Not Remotion-based render templates
- No news-content-aware style recommendation
- No per-theme animation motion specs
- Gallery doesn't persist user preferences

---

## 11. Forbidden in This Change

- No real LLM / TTS / audio generation
- No MP4 export
- No job creation
- No external CDN or remote images

---

## CP29.1: Video Style Selection Sync Fix

**Branch:** `fix/cp29.1-video-style-selection-sync`
**Commit:** `fix(cp29.1): sync video style selection with theme value`
**Date:** 2026-06-24

### Problem

CP29 expanded `THEME_SHOWCASES` to 12 themes on the frontend, but the hidden `selectTheme` dropdown is populated from `/api/themes` which reads `config/themes.yaml`. That YAML only contains 3 legacy themes plus `research_desk_v2` and `news_card_v1` — missing the 9 newly added video style IDs.

This caused:
1. The gallery displayed 12 theme cards correctly.
2. Clicking a new theme card failed to set `selectTheme.value` stably (the option didn't exist in the `<select>`).
3. `episode_plan.theme`, `episode_script.theme`, `episode_audio_manifest`, and `episode_render_ir.theme` could not carry the new theme IDs.
4. Layout mapping in `buildEpisodeRenderIrFromContracts()` fell back to `news_card_stack` for all new themes.

### Solution

Two new functions in `web/app.js`:

#### `syncThemeSelectWithShowcases()`

Called after `/api/themes` loads (success or fallback). Iterates `Object.values(THEME_SHOWCASES)` and appends any missing `option` elements to `selectTheme`. Never removes existing backend options.

```javascript
function syncThemeSelectWithShowcases() {
  var existingValues = {};
  Array.from(selectTheme.querySelectorAll("option")).forEach(function (opt) {
    existingValues[opt.value] = true;
  });
  Object.values(THEME_SHOWCASES).forEach(function (theme) {
    if (!existingValues[theme.id]) {
      var opt = document.createElement("option");
      opt.value = theme.id;
      opt.textContent = theme.name;
      selectTheme.appendChild(opt);
      existingValues[theme.id] = true;
    }
  });
}
```

#### `ensureThemeOption(theme)`

Called on every theme card click. Creates the option if missing, sets `selectTheme.value`, dispatches `change` event, and returns whether the value took effect. Reports `"主题选择失败"` via `setStatus()` if the value fails to stick.

```javascript
function ensureThemeOption(theme) {
  var existingOpt = selectTheme.querySelector('option[value="' + theme.id + '"]');
  if (!existingOpt) {
    var opt = document.createElement("option");
    opt.value = theme.id;
    opt.textContent = theme.name;
    selectTheme.appendChild(opt);
  }
  selectTheme.value = theme.id;
  selectTheme.dispatchEvent(new Event("change"));
  return selectTheme.value === theme.id;
}
```

### Call Sites

| Location | Function Called |
|----------|----------------|
| `init()` — `/api/themes` success branch | `syncThemeSelectWithShowcases()` |
| `init()` — `/api/themes` error/fallback branch | `syncThemeSelectWithShowcases()` |
| Theme card `click` handler | `ensureThemeOption(theme)` |

### 12 Theme IDs Now Guaranteed in `selectTheme`

`news_card_v1`, `research_desk_v2`, `causal_map_v1`, `timeline_brief_v1`, `data_dashboard_v1`, `breaking_news_v1`, `product_launch_v1`, `paper_digest_v1`, `podcast_cards_v1`, `dev_terminal_v1`, `magazine_cover_v1`, `opinion_column_v1`

### Verified Contracts That Now Carry Correct Theme

- `buildEpisodePlan()` → `episode_plan.theme`
- `buildEpisodeScriptFromPlan()` → `episode_script.theme`
- `buildEpisodeAudioManifestFromScript()` → audio manifest passthrough
- `buildEpisodeRenderIrFromContracts()` → `episode_render_ir.theme` + correct `visual.layout` mapping
- `updateGenerationPlan()` → gen plan panel shows correct Chinese theme name

### Lightweight Verification Results

| Test | Result |
|------|--------|
| `selectTheme` contains all 12 theme IDs after init | ✓ |
| Click `timeline_brief_v1` → `selectTheme.value === "timeline_brief_v1"` | ✓ |
| Click `data_dashboard_v1` → `selectTheme.value === "data_dashboard_v1"` | ✓ |
| Click `dev_terminal_v1` → `selectTheme.value === "dev_terminal_v1"` | ✓ |
| Gen plan panel shows Chinese name for new themes | ✓ |
| `episode_plan.theme` carries new theme ID | ✓ |
| `episode_render_ir` uses correct layout mapping | ✓ |
| No `/api/jobs` called | ✓ |
| No real LLM / TTS / MP4 / audio | ✓ |
| No API key / voice_id leakage | ✓ |

### Forbidden (Same as CP29)

- No real LLM / TTS / audio generation
- No MP4 export
- No job creation
- No external CDN or remote images
