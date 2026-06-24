# CP26: Episode Audio Manifest Contract

**Branch:** `feat/cp26-episode-audio-manifest-contract`
**Commit:** `feat(cp26): add episode audio manifest contract`
**Date:** 2026-06-24

---

## 1. Problem Statement

CP25 built `episode_script_v1` from `episode_plan_v1`. The script contains structured narration text organized by segment and beat type, but it is not yet tied to a specific audio production plan.

CP26 defines `episode_audio_manifest_v1` — a time-ordered list of audio clips with speaker assignments, duration hints, and silence padding. This contract is the bridge between script text and TTS generation.

---

## 2. Episode Audio Manifest JSON Schema

```json
{
  "version": "episode_audio_manifest_v1",
  "episode_title": "今日 AI 前沿速览",
  "source_script_version": "episode_script_v1",
  "voice_mode": "dual_speaker",
  "estimated_duration_sec": 180,
  "clips": [
    {
      "clip_id": "opening_001",
      "order": 1,
      "section": "opening",
      "speaker": "host_a",
      "text": "今天我们快速看几条值得关注的 AI 新闻。",
      "duration_hint_sec": 12,
      "audio_path": null
    },
    {
      "clip_id": "seg_001_headline",
      "order": 2,
      "section": "segment",
      "segment_order": 1,
      "news_id": "hn_123456",
      "beat_type": "headline",
      "speaker": "host_a",
      "text": "第 1 条，OpenAI announces GPT-5...",
      "duration_hint_sec": 8,
      "audio_path": null
    },
    {
      "clip_id": "seg_001_context",
      "order": 3,
      "section": "segment",
      "segment_order": 1,
      "news_id": "hn_123456",
      "beat_type": "context",
      "speaker": "host_b",
      "text": "这条是今天的主线新闻，热度和讨论度都比较高。",
      "duration_hint_sec": 14,
      "audio_path": null
    },
    {
      "clip_id": "seg_001_takeaway",
      "order": 4,
      "section": "segment",
      "segment_order": 1,
      "news_id": "hn_123456",
      "beat_type": "takeaway",
      "speaker": "host_a",
      "text": "后续值得关注它是否会带来产品、模型或市场层面的变化。",
      "duration_hint_sec": 10,
      "audio_path": null
    },
    {
      "clip_id": "transition_after_001",
      "order": 5,
      "section": "transition",
      "speaker": "host_b",
      "text": "接着看下一条。",
      "duration_hint_sec": 4,
      "audio_path": null
    },
    {
      "clip_id": "closing_001",
      "order": 6,
      "section": "closing",
      "speaker": "host_a",
      "text": "今天最值得关注的是：OpenAI announces GPT-5...",
      "duration_hint_sec": 12,
      "audio_path": null
    }
  ],
  "mixing": {
    "format": "wav",
    "sample_rate": 32000,
    "channels": 1,
    "silence_between_clips_sec": 0.25
  },
  "constraints": {
    "no_real_tts": true,
    "audio_paths_are_placeholders": true
  }
}
```

---

## 3. buildEpisodeAudioManifestFromScript() Rules

### clip_id Format

| Section | clip_id Pattern |
|---------|---------------|
| opening | `opening_001` |
| segment beat | `seg_NNN_{beat_type}` |
| transition | `transition_after_NNN` |
| closing | `closing_001` |

### Speaker Assignment

| Section / Beat Type | Speaker |
|---------------------|---------|
| opening | `host_a` |
| headline | `host_a` |
| context | `host_b` |
| takeaway | `host_a` |
| transition | `host_b` |
| closing | `host_a` |

### Duration Hints (static estimates)

| Beat Type / Section | duration_hint_sec |
|---------------------|------------------|
| opening | 12 |
| headline | 8 |
| context | 14 |
| takeaway | 10 |
| transition | 4 |
| closing | 12 |

`estimated_duration_sec` = sum of all `duration_hint_sec` across clips.

### audio_path

Always `null` in this CP — placeholders only.

---

## 4. validateEpisodeAudioManifest() Rules

| Condition | Level | Message |
|-----------|-------|---------|
| `manifest` is null | error | manifest 为空 |
| `version !== "episode_audio_manifest_v1"` | error | version 必须为 episode_audio_manifest_v1 |
| `clips.length < 1` | error | 至少需要 1 个 clip |
| `clips[].order` not sequential | error | 第 N 个 clip 的 order 不连续 |
| `clip_id` missing or duplicate | error | clip_id 必须唯一 |
| `speaker` not `host_a` or `host_b` | error | speaker 必须是 host_a 或 host_b |
| `text` empty | error | text 不能为空 |
| `audio_path !== null` | error | audio_path 必须为 null |
| `estimated_duration_sec <= 0` | error | estimated_duration_sec 必须大于 0 |
| API key / voice_id found | error | manifest 中不允许出现 API key 或 voice_id |

Returns `{ ok: boolean, warnings: string[], errors: string[] }`.

---

## 5. UI: "生成音频计划" Button

Located below "生成栏目脚本草案" in the episode planner section.

Click behavior:
1. If `episodeItemList.length === 0` → error "请先加入新闻，再生成音频计划"
2. `buildEpisodePlan()` → `validateEpisodePlan()`
3. If plan has errors → block
4. `buildEpisodeScriptFromPlan(plan)` → `validateEpisodeScript()`
5. If script has errors → block
6. `buildEpisodeAudioManifestFromScript(script)` → `validateEpisodeAudioManifest()`
7. Switch to "音频计划" tab
8. Display `{ manifest, validation }` JSON
9. No API calls, no TTS, no job creation

---

## 6. UI: "音频计划" Tab

New tab showing:
- Formatted JSON of the full `episode_audio_manifest` object
- Validation results

Does NOT:
- Call any TTS API
- Create any audio file
- Export MP4

---

## 7. State Variable

- `latestEpisodeAudioManifest` — set when "生成音频计划" is clicked (CP26)

---

## 8. Lightweight Verification Results

| Test | Result |
|------|--------|
| 0 items → "请先加入新闻" error | ✓ |
| 2 items → manifest generates cleanly | ✓ |
| `clips[].order` sequential from 1 | ✓ |
| `clip_id` unique per clip | ✓ |
| `speaker` only host_a / host_b | ✓ |
| `audio_path` all null | ✓ |
| `estimated_duration_sec` equals sum of duration_hints | ✓ |
| "音频计划" tab displays JSON | ✓ |
| No API key / voice_id leakage | ✓ |
| No real TTS / MP4 / job creation | ✓ |

---

## 9. Current Limitations

- Audio manifest is a plan only — no real TTS generation
- No real audio files (wav/mp3)
- No subtitle timeline (SRT/VTT)
- No audio concatenation
- `audio_path` is always null (placeholder)
- No actual voice assignment (only host_a / host_b labels)
- Manifest does not persist across page refresh

---

## 10. Future Path

`episode_audio_manifest_v1` will be the input for:
1. TTS text splitting per clip → audio clips
2. Audio clip concatenation / mixing
3. Subtitle generation (SRT from clip timing)
4. `render_ir` timeline synchronization

---

## 11. Forbidden in This Change

- No real TTS calls
- No real audio file generation
- No MP4 export
- No job creation via /api/jobs
- No subtitle generation
- No Remotion / render_ir
- No digital human / cloud deployment
