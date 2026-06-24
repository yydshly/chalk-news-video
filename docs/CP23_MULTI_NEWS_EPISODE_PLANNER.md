# CP23: Multi-News Episode Planner

**Branch:** `feat/cp23-multi-news-episode-planner`
**Commit:** `feat(cp23): add multi-news episode planner`
**Date:** 2026-06-24

---

## 1. Problem Statement

Previously users could only select one news item to generate a single video. CP23 introduces the first step toward multi-news "episode" support: a playlist builder where users can add multiple hot AI news items to a "今日 AI 新闻合集", reorder them, and see the episode structure — all without creating any jobs or calling any APIs.

---

## 2. UI Design

### 2.1 Episode Planner Section

Located between the recommended hint and the theme showcase. Shows:
- Header: "📺 今日 AI 新闻合集" + count badge (e.g. "3 条")
- Episode items list (sortable)
- Empty state: "从左侧热门新闻中加入 2-4 条，组成今日 AI 新闻合集"
- Episode structure preview below the list

### 2.2 Episode Item Card

Each item shows:
- Rank number (#1, #2...)
- News title (truncated with ellipsis)
- Source + score
- ↑ ↓ reorder buttons (first item disables ↑, last disables ↓)
- 移除 button

### 2.3 Hot News Card "加入合集" Button

Each hot news candidate card now has two action buttons:
1. **选择这条** — selects for single-video generation (existing behavior)
2. **加入合集** — adds to episode playlist (new behavior)

When a news item is already in the episode:
- Button shows **"已加入"** in green
- Button is visually styled differently (green background, no pointer cursor)
- Clicking it does nothing (no duplicate)

### 2.4 Episode Structure Preview

Below the episode list, a structure preview shows:
```
📋 栏目结构
开场：今日 AI 前沿速览
1. [News Title A]
2. [News Title B]
3. [News Title C]
结尾：今天最值得关注的是：[Top-scored news title]
```

---

## 3. Data Structures

### 3.1 episodeItemList (Client State)

```javascript
let episodeItemList = []; // CP23

// Each item:
{
  id: "hn_123456",      // news id
  title: "OpenAI announces...",
  url: "https://...",
  source: "Hacker News",
  final_score: 84.2,
  points: 342,
  comments: 89,
}
```

### 3.2 Constants

```javascript
const MAX_EPISODE_ITEMS = 5; // Maximum items in episode
```

---

## 4. Functions

| Function | Behavior |
|----------|----------|
| `addNewsToEpisode(item)` | Adds item if not already present and under 5 items. Shows error if at limit. |
| `removeNewsFromEpisode(id)` | Removes item by id. Re-renders planner and hot news buttons. |
| `moveEpisodeItem(id, direction)` | Moves item up (-1) or down (+1) in the list. |
| `renderEpisodePlanner()` | Renders episode list, count badge, empty state, and structure preview. |
| `renderEpisodeStructure()` | Renders the "📋 栏目结构" text preview with ranking and closing recommendation. |

---

## 5. Limits

- Maximum 5 items per episode
- Recommended range: 2-4 items
- Duplicate items are silently ignored (no error shown for already-joined)
- Items sorted by user order, not by score (score shown in metadata)

---

## 6. No Job / No API Creation

This CP only manages client-side state. Clicking "加入合集", "移除", ↑, ↓ does **not**:
- Call any API
- Create any job
- Trigger any pipeline
- Call LLM or TTS
- Export MP4

---

## 7. Compatibility

- `selectedNews` for single-video generation is **unchanged**
- `selectHotNewsItem()` is **unchanged**
- Both features coexist independently

---

## 8. Lightweight Verification

- Page loads with episode planner section visible ✓
- Empty state message shown when no items ✓
- "加入合集" button appears on each hot news card ✓
- Clicking "加入合集" adds item to episode list ✓
- Button changes to "已加入" (green) after adding ✓
- Clicking same item again does nothing (no duplicate) ✓
- ↑ and ↓ buttons reorder items ✓
- First item ↑ is disabled, last item ↓ is disabled ✓
- "移除" removes item from episode ✓
- Episode structure preview updates with order changes ✓
- Adding 6th item shows error message ✓
- No API calls to /api/jobs ✓
- No real TTS ✓
- No MP4 export ✓

---

## 9. Current Limitations

- Cannot generate episode video yet (playlist builder only)
- No real opening/closing script generation
- No multi-segment video stitching
- No episode MP4 export
- No auto-select best 3 news items
- Episode state does not persist across page refresh

---

## 10. Forbidden in This Change

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
