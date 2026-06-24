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
