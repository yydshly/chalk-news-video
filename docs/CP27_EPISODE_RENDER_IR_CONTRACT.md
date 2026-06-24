# CP27: Episode Render IR Contract

**Branch:** `feat/cp27-episode-render-ir-contract`
**Commit:** `feat(cp27): add episode render ir contract`
**Date:** 2026-06-24

---

## 1. Problem Statement

CP24–CP26 built a complete production pipeline:

```
episodeItemList → episode_plan_v1 → episode_script_v1 → episode_audio_manifest_v1
```

The final missing contract is `episode_render_ir_v1` — a visual production plan that maps each audio segment to a visual layout, timeline section, and rendering hint. This contract will drive multi-segment HTML animation rendering and eventual video stitching.

---

## 2. Episode Render IR JSON Schema

```json
{
  "version": "episode_render_ir_v1",
  "episode_title": "今日 AI 前沿速览",
  "theme": "news_card_v1",
  "canvas": {
    "width": 1280,
    "height": 720,
    "fps": 30,
    "background": "dark_newsroom"
  },
  "timeline": {
    "estimated_duration_sec": 180,
    "sections": [
      {
        "section_id": "opening",
        "type": "opening",
        "start_order": 1,
        "duration_hint_sec": 12,
        "audio_clip_ids": ["opening_001"],
        "visual": {
          "layout": "title_card",
          "title": "今日 AI 前沿速览",
          "subtitle": "多条热门 AI 新闻合集"
        }
      },
      {
        "section_id": "segment_001",
        "type": "news_segment",
        "news_id": "hn_123456",
        "order": 1,
        "role": "lead",
        "duration_hint_sec": 32,
        "audio_clip_ids": ["seg_001_headline", "seg_001_context", "seg_001_takeaway"],
        "visual": {
          "layout": "news_card_stack",
          "headline": "OpenAI announces GPT-5...",
          "source": "hn_123456",
          "badges": ["Lead", "Hot AI"],
          "emphasis": "primary"
        }
      },
      {
        "section_id": "transition_after_001",
        "type": "transition",
        "duration_hint_sec": 4,
        "audio_clip_ids": ["transition_after_001"],
        "visual": {
          "layout": "simple_transition",
          "text": "接着看下一条。"
        }
      },
      {
        "section_id": "closing",
        "type": "closing",
        "duration_hint_sec": 12,
        "audio_clip_ids": ["closing_001"],
        "visual": {
          "layout": "summary_card",
          "focus_news_id": "hn_123456",
          "title": "今天最值得关注的是..."
        }
      }
    ]
  },
  "style": {
    "theme_id": "news_card_v1",
    "motion": "subtle",
    "density": "medium"
  },
  "constraints": {
    "no_real_render": true,
    "no_export": true,
    "render_paths_are_placeholders": true
  }
}
```

---

## 3. buildEpisodeRenderIrFromContracts() Rules

### Input
- `plan`: `episode_plan_v1`
- `script`: `episode_script_v1`
- `audioManifest`: `episode_audio_manifest_v1`

### Section Generation Order

| Section Type | Source | Layout |
|-------------|--------|--------|
| opening | `audioManifest` opening clip | `title_card` |
| `news_segment_001` | first script segment | theme-based |
| `transition_after_001` | first transition | `simple_transition` |
| `news_segment_002` | second script segment | theme-based |
| `transition_after_002` | second transition | `simple_transition` |
| ... | ... | ... |
| closing | closing clip | `summary_card` |

### Layout by Theme

| Theme ID | Layout |
|----------|--------|
| `news_card_v1` / default | `news_card_stack` |
| `research_desk` / `research_desk_v2` | `research_desk_panel` |
| `causal_map` / `causal_map_v1` | `causal_chain_panel` |

### Role-Based Visual Emphasis

| Role | Visual Emphasis | Badges |
|------|----------------|--------|
| lead | `primary` | `["Lead", "Hot AI"]` |
| supporting | `secondary` | `["AI News"]` |

### Duration Calculation

`duration_hint_sec` per section = sum of `duration_hint_sec` of all audio clips in that section.

`estimated_duration_sec` = sum of all section `duration_hint_sec` values.

---

## 4. validateEpisodeRenderIr() Rules

| Condition | Level | Message |
|-----------|-------|---------|
| `renderIr` is null | error | renderIr 为空 |
| `version !== "episode_render_ir_v1"` | error | version 必须为 episode_render_ir_v1 |
| canvas.width/height/fps missing | error | canvas.width/height/fps 必须合法 |
| `sections.length < 1` | error | 至少需要 1 个 section |
| `section_id` missing or duplicate | error | section_id 必须唯一 |
| section missing `type` | error | 第 N 个 section 缺少 type |
| `duration_hint_sec <= 0` | error | 第 N 个 section 的 duration_hint_sec 必须大于 0 |
| `audio_clip_ids` empty | error | 第 N 个 section 的 audio_clip_ids 不能为空 |
| section missing `visual` | error | 第 N 个 section 缺少 visual |
| no opening section | error | 必须包含 opening section |
| no closing section | error | 必须包含 closing section |
| no news_segment section | error | 必须至少包含 1 个 news_segment section |
| `constraints.no_real_render !== true` | error | constraints.no_real_render 必须为 true |
| `constraints.no_export !== true` | error | constraints.no_export 必须为 true |
| API key / voice_id found | error | renderIr 中不允许出现 API key 或 voice_id |

Returns `{ ok: boolean, warnings: string[], errors: string[] }`.

---

## 5. UI: "生成视觉计划" Button

Located below "生成音频计划" in the episode planner section.

Click behavior:
1. If `episodeItemList.length === 0` → error "请先加入新闻，再生成视觉计划"
2. Full pipeline: plan → script → audio manifest → render_ir
3. Each step validated before proceeding
4. Switch to "视觉计划" tab
5. Display `{ render_ir, validation }` JSON
6. No API calls, no TTS, no render, no job creation

---

## 6. UI: "视觉计划" Tab

New tab showing:
- Formatted JSON of the full `episode_render_ir` object
- Validation results

Does NOT:
- Call any TTS or render API
- Generate any HTML or animation
- Export MP4

---

## 7. State Variable

- `latestEpisodeRenderIr` — set when "生成视觉计划" is clicked (CP27)

---

## 8. Lightweight Verification Results

| Test | Result |
|------|--------|
| 0 items → "请先加入新闻" error | ✓ |
| 2 items → full pipeline generates cleanly | ✓ |
| `sections` includes opening, news_segment, closing | ✓ |
| Each news segment maps to correct `audio_clip_ids` | ✓ |
| lead segment → `emphasis: primary` | ✓ |
| supporting segment → `emphasis: secondary` | ✓ |
| `news_card_v1` theme → `layout: news_card_stack` | ✓ |
| "视觉计划" tab displays JSON | ✓ |
| `constraints.no_real_render === true` | ✓ |
| `constraints.no_export === true` | ✓ |
| No API key / voice_id leakage | ✓ |
| No real LLM / TTS / render / MP4 export | ✓ |

---

## 9. Current Limitations

- Render IR is a visual plan only — no real HTML rendering
- No actual animation generation
- No subtitle overlay rendering
- No video export (MP4)
- No multi-news animation templates
- `render_paths_are_placeholders: true` — no actual render output paths

---

## 10. Future Path

`episode_render_ir_v1` will be the input for:
1. Multi-segment HTML animation generation
2. Canvas-based video rendering (Remotion or similar)
3. Audio-visual synchronization timeline
4. Final episode video stitching

---

## 11. Forbidden in This Change

- No real LLM calls
- No real TTS calls
- No real audio generation
- No HTML / animation rendering
- No MP4 export
- No job creation via /api/jobs
- No Remotion / digital human / cloud deployment
