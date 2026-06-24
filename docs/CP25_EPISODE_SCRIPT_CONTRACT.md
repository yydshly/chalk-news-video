# CP25: Episode Script Contract

**Branch:** `feat/cp25-episode-script-contract`
**Commit:** `feat(cp25): add episode script contract`
**Date:** 2026-06-24

---

## 1. Problem Statement

CP24 built the `episode_plan_v1` contract from a list of selected news items. The next step is to convert that plan into a structured multi-segment narration script that can drive TTS and video rendering.

CP25 defines `episode_script_v1` — a deterministic mock script generated from `episode_plan_v1` using rule-based templates (no real LLM).

---

## 2. Episode Script JSON Schema

```json
{
  "version": "episode_script_v1",
  "episode_title": "今日 AI 前沿速览",
  "theme": "news_card_v1",
  "generation_mode": "fast",
  "estimated_duration_sec": 180,
  "opening": {
    "type": "opening",
    "text": "今天我们快速看几条值得关注的 AI 新闻。",
    "duration_hint_sec": 12
  },
  "segments": [
    {
      "order": 1,
      "type": "news_segment",
      "news_id": "hn_123456",
      "headline": "OpenAI announces GPT-5...",
      "role": "lead",
      "beats": [
        { "type": "headline", "text": "第 1 条，OpenAI announces GPT-5..." },
        { "type": "context",   "text": "这条是今天的主线新闻，热度和讨论度都比较高。" },
        { "type": "takeaway", "text": "后续值得关注它是否会带来产品、模型或市场层面的变化。" }
      ],
      "duration_hint_sec": 35
    }
  ],
  "transitions": [
    { "after_order": 1, "text": "接着看下一条。" }
  ],
  "closing": {
    "type": "closing",
    "focus_news_id": "hn_123456",
    "text": "今天最值得关注的是：OpenAI announces GPT-5..."
  },
  "constraints": {
    "min_segments": 2,
    "max_segments": 5,
    "target_duration_sec": 180,
    "tone": "清晰、克制、新闻解说"
  }
}
```

---

## 3. buildEpisodeScriptFromPlan() Mock Rules

### Opening
Fixed text: `"今天我们快速看几条值得关注的 AI 新闻。"`

### Per-Segment Beats

| Beat type | Lead segment | Supporting segment |
|-----------|-------------|-------------------|
| headline | `第 N 条，{title}。` | `第 N 条，{title}。` |
| context | `这条是今天的主线新闻，热度和讨论度都比较高。` | `这条可以作为补充观察，帮助我们理解今天的 AI 动向。` |
| takeaway | `后续值得关注它是否会带来产品、模型或市场层面的变化。` | `后续值得关注它是否会带来产品、模型或市场层面的变化。` |

### Transition (between segments)
`"接着看下一条。"`

### Closing
`今天最值得关注的是：{lead title}。`

`closing.focus_news_id` equals lead segment's `news_id`.

---

## 4. Role Inheritance

`episode_script.segments[].role` is copied directly from `episode_plan.items[].role`.

Only one segment has `role: "lead"`.

`closing.focus_news_id === lead segment.news_id`.

---

## 5. validateEpisodeScript() Rules

| Condition | Level | Message |
|-----------|-------|---------|
| `script` is null | error | 脚本为空 |
| `version !== "episode_script_v1"` | error | version 必须为 episode_script_v1 |
| `opening.text` empty | error | opening.text 不能为空 |
| `segments.length < 1` | error | 至少需要 1 个 segment |
| `segments.length > 5` | error | 最多支持 5 个 segment |
| segment missing `news_id` | error | 第 N 个 segment 缺少 news_id |
| segment missing `headline` | error | 第 N 个 segment 缺少 headline |
| segment has `< 3` beats | error | 第 N 个 segment 至少需要 3 个 beats |
| `leadCount !== 1` | error | 必须有且只有 1 个 lead segment |
| `closing.focus_news_id !== leadSegment.news_id` | error | closing.focus_news_id 必须等于 lead segment 的 news_id |
| API key / voice_id found in script | error | 脚本中不允许出现 API key 或 voice_id |

Returns `{ ok: boolean, warnings: string[], errors: string[] }`.

---

## 6. UI: "生成栏目脚本草案" Button

Located below "查看栏目计划" in the episode planner section.

Click behavior:
1. If `episodeItemList.length === 0` → error "请先加入新闻，再生成栏目脚本"
2. `buildEpisodePlan()` → `validateEpisodePlan()`
3. If plan has errors → block, show error "栏目计划有误，无法生成脚本"
4. `buildEpisodeScriptFromPlan(plan)` → `validateEpisodeScript(script)`
5. Switch to "栏目脚本" tab
6. Display `{ script, validation }` JSON
7. No API calls, no job creation

---

## 7. UI: "栏目脚本" Tab

New tab showing:
- Formatted JSON of the full `episode_script` object
- Validation results (warnings and errors)

Does NOT:
- Call any LLM or TTS API
- Create any job
- Export MP4

---

## 8. State Variables

- `latestEpisodePlan` — set when "查看栏目计划" is clicked (CP24)
- `latestEpisodeScript` — set when "生成栏目脚本草案" is clicked (CP25)

---

## 9. Lightweight Verification Results

| Test | Result |
|------|--------|
| 0 items → "请先加入新闻" error | ✓ |
| 1 item → script generates, plan warning | ✓ |
| 2 items → script generates cleanly | ✓ |
| Highest score item → segment.role = "lead" | ✓ |
| Only 1 lead segment | ✓ |
| `closing.focus_news_id` === lead segment `news_id` | ✓ |
| Each segment has headline/context/takeaway beats | ✓ |
| "栏目脚本" tab displays JSON | ✓ |
| Plan error blocks script generation | ✓ |
| No API key / voice_id leakage | ✓ |
| No real LLM / TTS / MP4 / job creation | ✓ |

---

## 10. Current Limitations

- Script is mock/deterministic — not a real LLM output
- No multi-voice dialogue
- No audio timeline
- No multi-news `render_ir`
- No episode MP4 export
- No episode audio manifest
- Script does not persist across page refresh

---

## 11. Future Path

`episode_script_v1` will be the input for:
1. TTS text splitting (per-segment beats → audio clips)
2. Episode audio manifest creation
3. Multi-segment animation rendering (render_ir)
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
