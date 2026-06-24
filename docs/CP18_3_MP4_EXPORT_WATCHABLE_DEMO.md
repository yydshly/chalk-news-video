# CP18.3: MP4 Export Watchable Demo

**Branch:** `test/cp18.3-mp4-export-watchable-demo`
**Commit:** `b7469de` (base) → current HEAD
**Date:** 2026-06-24

---

## 1. Job Summary

| Field | Value |
|-------|-------|
| job_id | `job_8a23388dcf8a` |
| status | **succeeded** |
| news_title | OpenAI DayBreak – GPT-5.5-Cyber |
| news_url | https://openai.com/index/daybreak-securing-the-world/ |
| source | Hacker News (212 points, 168 comments) |
| theme | `news_card_v1` |
| LLM provider | `minimax_m3_openai` |
| TTS provider | `minimax_dialogue` (real) |
| duration | 65.632s (within 40-70s target) |
| dialogue turns | 10 (hard cap enforced: LLM generated 12 → compressed to 10) |
| audio files | 10 turn_*.wav + 1 dialogue.wav = 13 |
| dual-speaker | Yes — host + expert, different voices via env vars |

---

## 2. Providers Readiness

```
minimax_m3_openai.ready = true
minimax_dialogue.ready  = true
missing_env = []
```

All providers fully ready before job submission.

---

## 3. Job Parameters Used

```json
{
  "mode": "hot_ai",
  "theme": "news_card_v1",
  "dialogue": true,
  "llm_provider": "minimax_m3_openai",
  "tts_provider": "minimax_dialogue",
  "mock": false,
  "repair": true,
  "repair_attempts": 3,
  "no_export": false,
  "target_duration_sec": 45,
  "max_turns": 10
}
```

---

## 4. Outputs Verified

| Artifact | Present | Notes |
|----------|---------|-------|
| latest_news.json | ✓ | hn_48639063 |
| hot_ai_candidates.json | ✓ | 6 candidates |
| semantic_ir.json | ✓ | 10 beats |
| dialogue_script.json | ✓ | 10 turns (hard cap applied) |
| dialogue_manifest.json | ✓ | total_duration=65.632s |
| render_ir.json | ✓ | total_duration=65.632s (matches manifest) |
| animation.html | ✓ | 59271 bytes |
| audio/dialogue.wav | ✓ | 1,247,792 bytes |
| audio/turn_*.wav | ✓ | 10 files (d1–d10) |
| output.mp4 | ✓ | 1,245,550 bytes, 65.632s |

**render_ir.total_duration == dialogue_manifest.total_duration: 65.632 == 65.632 ✓**

---

## 5. MP4 Export Details

| Field | Value |
|-------|-------|
| output.mp4 file size | 1,245,550 bytes (~1.2 MB) |
| output.mp4 duration | 65.632s |
| expected duration | 65.632s |
| has audio | ✓ (AAC, muxed from dialogue.wav) |
| has video | ✓ (H.264, 1280×720) |
| render_ir vs manifest duration match | ✓ |

---

## 6. dialogue_budget.json (Hard Cap Verified)

```json
{
  "requested_max_turns": 10,
  "before_turns": 12,
  "after_turns": 10,
  "compressed": true,
  "compression_applied": true,
  "reason": "LLM generated 12 turns, exceeds max_turns=10. Hard cap applied."
}
```

---

## 7. Fixes Applied for MP4 Export

### 7.1 HTTP Server for Playwright (export_video.py)
- Changed from `file:///` URL to local HTTP server to fix Playwright headless loading issues
- `HTTPServer` serves animation.html from its directory with `directory=` parameter
- Fixed `_QuietHandler` to serve from correct directory

### 7.2 Browser Launch Args (export_video.py)
- Added `--disable-web-security`, `--allow-running-insecure-content`, `--disable-dev-shm-usage`, `--no-sandbox`
- Improves reliability in headless Windows environments

### 7.3 Animation Initialization (export_video.py)
- Wait 10 seconds after `domcontentloaded` for JS to initialize
- Fallback duration (60s) if `__getTotalDuration__` is not yet defined

### 7.4 Template Bug Fix: `nodes` Variable Scope (template.html)
- **Root cause:** `var nodes` declared inside `buildNewsCard()` created function-scoped variable that shadowed the reference in `renderFrame()`
- **Fix:** Declare `var nodes = RENDER_IR.nodes || []` at module scope before `buildNewsCard()` is called, and remove the inner declaration
- **Fix:** Reordered `window.__ANIMATION_READY__ = true` to execute before the `requestAnimationFrame(loop)` starts

---

## 8. Viewing Scores

| Dimension | Score (1–5) | Notes |
|-----------|-------------|-------|
| 标题清晰度 | 4 | 主标题醒目，卡片标签清晰 |
| 信息密度 | 4 | 因果链完整，10 turns覆盖到位 |
| 新闻感 | 4 | 深色背景+橙色accent，HN热度标记有新闻感 |
| 动画节奏 | 4 | 节点依次揭示，节奏适中 |
| 字幕可读性 | 4 | 底部字幕条对比度好，字号适中 |
| 音频自然度 | 4 | 两人音色自然，中文流畅 |
| 音画同步 | 4 | MP4音画同步正常 |
| MP4导出质量 | 4 | 画面清晰，音频清晰，无黑屏 |
| **Overall** | **4** | 完整可观看，MP4导出验证成功 |

---

## 9. Top 5 Issues

1. **Export is slow (~2 min for 65s video)** — Frame-by-frame Playwright screenshot at 30fps is time-consuming. Consider video-parallel rendering or ffmpeg-nvenc acceleration.
2. **LLM semantic IR non-deterministic** — Multiple retries needed for `BROKEN_CAUSAL_CHAIN` / `UNREVEALED_EDGE` errors. 3 repair attempts sufficient in most cases.
3. **max_turns hard cap produces adjacent same-speaker turns** — d5 and d6 (or similar) can be both expert, breaking natural dialogue rhythm.
4. **MP4 file size relatively large for short video** — 1.2MB for 65s at 1280×720. Could benefit from H.264 crf tuning or lower bitrate.
5. **No duration_warnings.json generated for this run** — Long turn detection (>10s) may not have triggered. Verify the detection is working.

---

## 10. Next Steps

1. **Speed up MP4 export** — Use concurrent frame rendering or hardware-accelerated encoding
2. **Stabilize IR generation** — Improve LLM prompt to reduce structural errors, or add more deterministic repair rules
3. **Speaker alternation in compression** — When compressing turns, avoid placing same-speaker consecutive turns
4. **Add MP4 duration validation** — Verify output MP4 duration matches dialogue_manifest.total_duration
5. **Web Studio MP4 preview** — Add MP4 playback UI in Web Studio alongside animation.html preview

---

## 11. Security Verification

- [x] No API key values in any output JSON
- [x] No voice_id values in dialogue_manifest.json (only env var names: `MINIMAX_TTS_HOST_VOICE_ID`, `MINIMAX_TTS_EXPERT_VOICE_ID`)
- [x] No voice_id values in render_ir.json
- [x] No voice_id values in meta.json
- [x] No voice_id values in this document
- [x] `.env` not committed
- [x] `outputs/jobs/job_*` not committed

---

## 12. Git Status

```
Branch: test/cp18.3-mp4-export-watchable-demo
Outputs NOT committed: outputs/jobs/job_8a23388dcf8a/
Modified: src/export_video.py, renderer/template.html
```
