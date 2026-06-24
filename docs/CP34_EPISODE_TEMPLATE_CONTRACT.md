# CP34: Episode Template Contract Extraction

**Branch:** `feat/cp34-episode-template-contract`
**Commit:** `feat(cp34): extract episode template contract`
**Date:** 2026-06-25

---

## 1. Why Extract a Template Contract?

CP33 produced a polished mock episode HTML but `buildMockEpisodeHtml(renderIr)` accumulated too many responsibilities:

1. Extracting sections from `renderIr`
2. Computing pseudo timecodes
3. Building timeline markers
4. Building news cards
5. Building transition rows
6. Assembling CSS
7. Assembling the full HTML string
8. Encoding structural constraints

This made the function:
- Hard to reuse if a future Remotion or other renderer needs the same data
- Difficult to test in isolation
- Impossible to switch between multiple episode template styles
- Unable to surface the contract for debugging/visualization

CP34 restructures this into two clean layers:

```
renderIr  →  buildEpisodeTemplateContract()  →  template contract (JS object)
                                                 ↓
                                        renderEpisodeTemplateHtml()
                                                 ↓
                                              HTML string
```

---

## 2. episode_template_v1 Schema

```json
{
  "schema_version": "episode_template_v1",
  "template_id": "timeline_preview_v1",
  "episode": {
    "title": "...",
    "subtitle": "...",
    "theme_id": "...",
    "theme_name": "...",
    "estimated_duration_sec": 120,
    "news_count": 5,
    "lead_count": 2
  },
  "timeline": {
    "markers": [
      {
        "type": "opening" | "news_segment" | "transition" | "closing",
        "label": "开场",
        "timecode": "00:00",
        "role": "lead" | null,
        "section_id": "..."
      }
    ]
  },
  "sections": {
    "opening": {
      "title": "...",
      "subtitle": "...",
      "duration_hint_sec": 12
    },
    "news_cards": [
      {
        "section_id": "...",
        "order": 1,
        "role": "lead",
        "headline": "...",
        "layout": "...",
        "emphasis": "...",
        "badges": ["..."],
        "audio_clip_count": 3,
        "duration_hint_sec": 32,
        "time_range": "00:12 – 00:44",
        "is_lead": true,
        "section_type": "news_segment"
      }
    ],
    "transitions": [
      {
        "after_order": 1,
        "text": "接着看下一条"
      }
    ],
    "closing": {
      "title": "今天最值得关注的是...",
      "focus_news_id": "..."
    }
  },
  "constraints": {
    "no_external_assets": true,
    "no_script": true,
    "no_real_render": true,
    "no_audio": true,
    "no_mp4": true
  }
}
```

---

## 3. renderIr → TemplateContract → HTML Relationship

| Layer | Function | Responsibility |
|-------|----------|----------------|
| Data extraction | `buildEpisodeTemplateContract(renderIr)` | Transform renderIr into a structured contract object |
| Validation | `validateEpisodeTemplateContract(contract)` | Validate contract schema, required fields, security |
| Rendering | `renderEpisodeTemplateHtml(contract)` | Consume contract, produce HTML string |
| Thin wrapper | `buildMockEpisodeHtml(renderIr)` | Orchestrate: build → validate (optional) → render |

The contract is a pure data object with no side effects. All HTML generation is isolated in `renderEpisodeTemplateHtml`.

---

## 4. Helper Functions

| Function | Role |
|----------|------|
| `formatTimecode(sec)` | Convert seconds → `MM:SS` string |
| `buildEpisodeTemplateContract(renderIr)` | Extract and structure data from renderIr into episode_template_v1 |
| `validateEpisodeTemplateContract(contract)` | Validate schema version, required fields, security constraints |
| `renderEpisodeTemplateHtml(contract)` | Render full HTML from contract (pure function) |
| `buildMockEpisodeHtml(renderIr)` | Thin wrapper: build → render |

---

## 5. validateEpisodeTemplateContract Rules

| Check | Condition |
|-------|-----------|
| Schema version | `schema_version === "episode_template_v1"` |
| Template ID | `template_id === "timeline_preview_v1"` |
| Episode title | `episode.title` must exist |
| Timeline markers | `timeline.markers` must be a non-empty array |
| News cards | `sections.news_cards` must be a non-empty array |
| Card fields | Each card must have `section_id`, `headline`, `time_range` |
| No API key | `JSON.stringify(contract)` must not contain `api_key` or `api-key` |
| No voice ID | Must not contain `voice_id` or `voice-id` |
| Constraints | `no_external_assets`, `no_script`, `no_audio`, `no_mp4` must all be `true` |

---

## 6. State

- `latestEpisodeTemplateContract` stores the most recently generated contract
- Set in `previewMockEpisodeHtml()` and `saveMockEpisodeHtml()` after contract validation
- Available for debugging / UI display (e.g., in `json-visual_plan` output)

---

## 7. Compatibility

All CP33 capabilities preserved:
- `previewMockEpisodeHtml()` → unchanged external behavior, now internally uses contract pipeline
- `saveMockEpisodeHtml()` → unchanged external behavior, now internally uses contract pipeline
- `validateMockEpisodeHtml()` → unchanged
- `buildMockEpisodeHtml()` → thin wrapper, external behavior unchanged
- All downstream: history, open, download → unchanged

---

## 8. Future Paths

The contract layer enables future work without refactoring the HTML renderer:

- **Remotion integration**: Pass `episode_template_v1` contract to a Remotion `Timeline` component
- **Multiple template styles**: Add `template_id: "compact_v1"` or `"vertical_v1"` with different renderers
- **Server-side rendering**: Share the contract between frontend mock and backend renderer
- **Visual diff testing**: Compare contract outputs across versions
- **Multi-episode series**: Compose multiple contracts into a series manifest

---

## 9. Current Limitations

- Still a frontend mock contract, not a final renderer contract
- Not yet extracted to a standalone module/file
- No actual multi-template selection UI
- No real animation renderer (pure CSS only)
- `renderEpisodeTemplateHtml` is still inline in app.js

---

## 10. Lightweight Verification Results

| Test | Result |
|------|--------|
| Preview iframe loads with timeline rail | ✓ |
| Pseudo timecodes shown (MM:SS format) | ✓ |
| Hero header with stats | ✓ |
| Lead cards have amber border | ✓ |
| Each card has `mock-news-card` | ✓ |
| Each card has `data-section-type="news_segment"` | ✓ |
| HTML contains "开场" and "结尾" | ✓ |
| No external http/https links | ✓ |
| No API key / voice_id | ✓ |
| Save to history works | ✓ |
| No `/api/jobs` called | ✓ |
| No real LLM / TTS / MP4 | ✓ |
| `buildMockEpisodeHtml` is thin wrapper | ✓ |
| Contract has `schema_version: "episode_template_v1"` | ✓ |
| Contract constraints all `true` | ✓ |
| `outputs/episode_previews/*.html` not committed | ✓ |

---

## CP34.1: Template Time Range Consistency

**Branch:** `fix/cp34.1-template-time-range-consistency`
**Commit:** `fix(cp34.1): align template news card time ranges`
**Date:** 2026-06-25

### 1. Issue

CP34 introduced `episode_template_v1` with two independent time calculations:

1. **Timeline markers** — computed from `transitions[i].duration_hint_sec` (correct)
2. **News card `time_range`** — hardcoded `cardCursor += 4` (incorrect when `duration_hint_sec !== 4`)

This caused the timeline rail timecodes and per-card time ranges to diverge when a transition had a non-default duration.

### 2. Fix

Added a shared helper inside `buildEpisodeTemplateContract`:

```js
function getTransitionDurationAfterIndex(index) {
  var trans = transitions[index];
  return trans && trans.duration_hint_sec ? trans.duration_hint_sec : 4;
}
```

Both timeline marker computation and news card `time_range` computation now call this helper, ensuring they always use the same transition duration value.

### 3. Verification

| Test | Result |
|------|--------|
| Transition duration != 4: markers and time_range now consistent | ✓ |
| Default (no `duration_hint_sec`): falls back to 4 seconds | ✓ |
| Preview iframe still works | ✓ |
| Save to history still works | ✓ |
| No `/api/jobs` called | ✓ |
| No real LLM / TTS / MP4 | ✓ |
