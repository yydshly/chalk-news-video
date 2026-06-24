# CP30: News-Aware Style Recommendation

**Branch:** `feat/cp30-news-aware-style-recommendation`
**Commit:** `feat(cp30): add news-aware style recommendation`
**Date:** 2026-06-24

---

## 1. Why News-Aware Recommendation?

CP29 expanded the video style gallery to 12 themes. Users face selection cost when choosing among 12 styles. CP30 adds rule-based style recommendations driven by news content — reducing friction without requiring real LLM inference.

---

## 2. `recommendStylesForNews(newsItem)` Rules

Input: a hot news item object (`title`, `summary`, `source`, `final_score`, `points`, `comments`, `rank_reason`, `url`).

Output: array of up to 3 `{ theme_id, reason }` objects, deduplicated and ordered by rule priority.

### Rule Table

| Condition | Keywords / Trigger | Recommended Themes |
|-----------|-------------------|-------------------|
| Product launch | `launch`, `release`, `announces`, `unveils`, `introduces`, `product`, `app`, `feature`, `api`, `model` | `product_launch_v1`, `news_card_v1` |
| Paper / research | `paper`, `arxiv`, `research`, `study`, `benchmark`, `eval`, `dataset`, `method`, `reasoning` | `paper_digest_v1`, `research_desk_v2` |
| Developer / open source | `github`, `open source`, `repo`, `library`, `framework`, `sdk`, `cli`, `terminal`, `developer` | `dev_terminal_v1`, `research_desk_v2` |
| Data / funding / leaderboard | `funding`, `raises`, `valuation`, `revenue`, `users`, `benchmark`, `score`, `ranking`, `leaderboard`, `downloads` | `data_dashboard_v1`, `news_card_v1` |
| Breaking / regulation | `breaking`, `ban`, `regulation`, `lawsuit`, `outage`, `security`, `policy`, `government`, `antitrust` | `breaking_news_v1`, `causal_map_v1` |
| Causal / opinion | `why`, `because`, `impact`, `effect`, `risk`, `concern`, `debate`, `controversy`, `backlash` | `causal_map_v1`, `opinion_column_v1` |
| Multi-news episode | `episodeItemList.length >= 2` | `timeline_brief_v1`, `magazine_cover_v1` |
| High score (>= 8.0 or pts >= 200) | — | `news_card_v1` |
| Very high score (>= 8.5) | — | `breaking_news_v1` |

### Deduplication & Limit

Rules are evaluated independently; results are deduplicated by `theme_id` (first-occurrence wins), then sliced to top 3.

### Fallback

If no rules match, returns an empty array. The recommendation UI row hides itself when the array is empty.

---

## 3. `updateStyleRecommendations()`

Updates the **gen plan panel recommendation row** (`#gen-plan-recommend-row` / `#gen-plan-recommend`). Called when:

- `renderHotNews()` completes (hot news loaded or refreshed)
- `selectHotNewsItem()` (user selects a news item)
- `addNewsToEpisode()` / `removeNewsFromEpisode()` via `renderHotNews()`
- User clicks a recommendation tag (after applying theme)

---

## 4. UI — Hot News Card Recommendation Tags

Each hot news card shows a `.style-recommend-tags` row below metadata. Tags are `.style-recommend-tag` buttons. Clicking a tag:

1. Calls `ensureThemeOption(THEME_SHOWCASES[theme_id])`
2. Re-renders theme showcase (highlight update)
3. Calls `updateStyleRecommendations()` (active tag highlight updates)
4. Calls `updateGenerationPlan()`

Does NOT change `selectedNews`. Does NOT create a job.

Active tag is gold (`#f59e0b`) with `.active` class.

---

## 5. UI — Gen Plan Panel Recommendation Row

HTML added after "视频风格" row in generation plan panel:

```html
<div class="gen-plan-row" id="gen-plan-recommend-row" style="display:none">
  <span class="gen-plan-label">推荐风格</span>
  <span id="gen-plan-recommend" class="gen-plan-value"></span>
</div>
```

Tags are `.gen-plan-recommend-tag` buttons, same click behavior as card tags.

---

## 6. CSS Classes Added

| Class | Location | Purpose |
|-------|----------|---------|
| `.style-recommend-tags` | Hot news cards | Container for tag buttons |
| `.style-recommend-tag` | Hot news cards | Tag button (blue border) |
| `.style-recommend-tag.active` | Hot news cards | Currently selected theme (gold) |
| `.gen-plan-recommend-tag` | Gen plan panel | Tag button |
| `.gen-plan-recommend-tag.active` | Gen plan panel | Currently selected theme (gold) |

---

## 7. Compatibility

- Does not modify `THEME_SHOWCASES` (12-style gallery unchanged)
- Does not modify `ensureThemeOption()`, `syncThemeSelectWithShowcases()`, `renderThemeShowcase()`
- Does not modify `buildEpisodePlan()`, `buildEpisodeRenderIrFromContracts()`, or any contract function
- `selectTheme` value changes only on explicit tag click
- No job creation, no LLM, no TTS, no MP4

---

## 8. Lightweight Verification Results

| Test | Result |
|------|--------|
| News card shows 2–3 recommendation tags | ✓ |
| `product_launch_v1` recommended for "announces new model" title | ✓ |
| `paper_digest_v1` recommended for "arxiv paper" title | ✓ |
| `dev_terminal_v1` recommended for "GitHub open source" title | ✓ |
| `timeline_brief_v1` recommended when `episodeItemList.length >= 2` | ✓ |
| Clicking tag sets `selectTheme.value` correctly | ✓ |
| Active tag turns gold | ✓ |
| Gen plan panel shows recommendation row when news selected | ✓ |
| Recommendations update when episode list changes | ✓ |
| No `/api/jobs` called | ✓ |
| No real LLM / TTS / MP4 | ✓ |
| No API key / voice_id leakage | ✓ |

---

## 9. Current Limitations

- Rule-based keyword matching, not semantic LLM understanding
- Only inspects `title`, `summary`, `source`, `final_score`, `points`
- No user preference memory
- No A/B testing
- No cross-news style consistency for episode mode
