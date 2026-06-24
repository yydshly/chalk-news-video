# CP24: Episode Plan Contract

**Branch:** `feat/cp24-episode-plan-contract`
**Commit:** `feat(cp24): add episode plan contract`
**Date:** 2026-06-24

---

## 1. Problem Statement

CP23 introduced `episodeItemList` as a client-side playlist of selected news items. However, it had no stable data contract for downstream generation.

CP24 formalizes the `episode_plan` data structure — a versioned JSON contract that represents the complete plan for a multi-news episode. This contract is the input for future episode script generation, audio manifest creation, and multi-segment video rendering.

---

## 2. Episode Plan JSON Schema

```json
{
  "version": "episode_plan_v1",
  "title": "今日 AI 前沿速览",
  "subtitle": "多条热门 AI 新闻合集",
  "theme": "news_card_v1",
  "generation_mode": "fast",
  "items": [
    {
      "order": 1,
      "id": "hn_123456",
      "title": "OpenAI announces GPT-5...",
      "url": "https://...",
      "source": "Hacker News",
      "final_score": 84.2,
      "points": 342,
      "comments": 89,
      "role": "lead"
    },
    {
      "order": 2,
      "id": "hn_789012",
      "title": "Claude 4 released...",
      "url": "https://...",
      "source": "Hacker News",
      "final_score": 75.2,
      "points": 218,
      "comments": 56,
      "role": "supporting"
    }
  ],
  "structure": {
    "opening": "今日 AI 前沿速览",
    "segments": [
      { "order": 1, "type": "news_segment", "news_id": "hn_123456", "headline": "OpenAI announces GPT-5..." },
      { "order": 2, "type": "news_segment", "news_id": "hn_789012", "headline": "Claude 4 released..." }
    ],
    "closing": {
      "type": "summary",
      "focus_news_id": "hn_123456",
      "focus_title": "OpenAI announces GPT-5..."
    }
  },
  "constraints": {
    "min_items": 2,
    "max_items": 5,
    "recommended_items": "2-4",
    "target_duration_sec": 180
  }
}
```

---

## 3. buildEpisodePlan() Rules

1. `version` is always `"episode_plan_v1"`
2. `theme` comes from `selectTheme.value`
3. `generation_mode` comes from the checked `gen_mode` radio
4. `items` maps each `episodeItemList` entry with:
   - `order`: 1-based index
   - `id`, `title`, `url`, `source`, `final_score`, `points`, `comments`: copied from source
   - `role`: `"lead"` for the item with highest `final_score` (or first if tied), `"supporting"` for all others
5. `structure.segments` is a list of `{order, type, news_id, headline}` objects
6. `structure.closing.focus_news_id` is set to the highest-scored news's id
7. `constraints` provides metadata about the episode

---

## 4. validateEpisodePlan() Rules

| Condition | Level | Message |
|-----------|-------|---------|
| `items.length === 0` | error | 至少需要 1 条新闻才能生成栏目计划 |
| `items.length < 2` | warning | 建议至少加入 2 条新闻形成栏目 |
| `items.length > 5` | error | 最多支持 5 条新闻 |
| `item` missing `id` | error | 第 N 条新闻缺少 id |
| `item` missing `title` | error | 第 N 条新闻缺少 title |
| `item.order` not sequential | error | 第 N 条新闻 order 序号不连续 |
| `closing.focus_news_id` not in items | error | 结尾推荐的新闻 ID 不在列表中 |

Returns `{ ok: boolean, warnings: string[], errors: string[] }`.

---

## 5. UI: "查看栏目计划" Button

Located below the episode structure in the episode planner section.

Click behavior:
1. If `episodeItemList.length === 0` → show error "请先加入新闻，再查看栏目计划"
2. Calls `buildEpisodePlan()` → generates plan JSON
3. Calls `validateEpisodePlan()` → validates plan
4. Switches to the "栏目计划" tab
5. Displays formatted JSON including plan + validation results
6. Shows status message: success / warning / error based on validation

---

## 6. UI: "栏目计划" Tab

New tab in the result panel showing:
- Formatted JSON of the full `episode_plan` object
- Validation results (warnings and errors)

Does NOT:
- Call any API
- Create any job
- Trigger LLM or TTS
- Export MP4

---

## 7. Role Assignment Logic

The item with the highest `final_score` gets `role: "lead"`. All other items get `role: "supporting"`.

If there is a tie for highest score, the first item in the list wins.

---

## 8. No Job / No API Creation

This CP only builds and displays the plan JSON. Clicking "查看栏目计划" does NOT:
- Call `/api/jobs`
- Call any LLM or TTS
- Create any job
- Write to history

---

## 9. Lightweight Verification

- 0 items → "请先加入新闻" error ✓
- 1 item → plan generates, warning "建议至少加入 2 条新闻" ✓
- 2+ items → plan generates without errors ✓
- Reordering updates `items[].order` ✓
- Removing item rebuilds plan ✓
- JSON contains no API keys, voice IDs, or debug prompts ✓
- No `/api/jobs` called ✓
- No real LLM / TTS / MP4 ✓

---

## 10. Current Limitations

- No `episode_script` generation yet
- No real opening/closing script copy
- No multi-news video generation
- No episode MP4 export
- `episode_plan` does not persist across page refresh
- No backend persistence

---

## 11. Future Path

The `episode_plan` contract will be the input for:
1. Episode script generation (LLM)
2. Audio manifest creation
3. Multi-segment animation rendering
4. Final episode video stitching

---

## 12. Forbidden in This Change

- No real LLM calls
- No real TTS calls
- No MP4 export
- No job creation via /api/jobs
- No waiting for long tasks
- No outputs/jobs/job_* committed
- No outputs/latest committed
- No .env / API key / voice_id committed
- No arbitrary file reading
- No debug prompt/response exposure
- No Remotion / digital human / cloud deployment / login / billing
