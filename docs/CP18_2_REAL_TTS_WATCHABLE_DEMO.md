# CP18.2: Real LLM + Real MiniMax Dialogue TTS Watchable Demo

**Branch:** `test/cp18.2-real-tts-watchable-demo`
**Commit:** `9713d7e` (base) → current HEAD
**Date:** 2026-06-24

---

## 1. Job Summary

| Field | Value |
|-------|-------|
| job_id | `job_cb2e6b537940` |
| status | **succeeded** |
| news_title | OpenAI DayBreak – GPT-5.5-Cyber |
| news_url | https://openai.com/index/daybreak-securing-the-world/ |
| source | Hacker News (211 points, 168 comments) |
| theme | `news_card_v1` |
| LLM provider | `minimax_m3_openai` |
| TTS provider | `minimax_dialogue` |
| duration | 62.056s (within 45–70s target) |
| dialogue turns | 12 (≤ 14 target) |
| audio files count | 12 turn_*.wav + 1 dialogue.wav = 13 |
| dual-speaker | Yes — host + expert, configured via MINIMAX_TTS_HOST_VOICE_ID / MINIMAX_TTS_EXPERT_VOICE_ID |

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
  "repair_attempts": 2,
  "no_export": true,
  "target_duration_sec": 45,
  "max_turns": 10
}
```

Note: Actual turns generated = 12 (LLM expanded beyond max_turns cap of 10). Duration came in at 62s due to real TTS audio lengths. This was the original CP18.2 baseline run. CP18.2.1 fixed this with a hard cap.

---

## 4. Outputs Verified

| Artifact | Present | Notes |
|----------|---------|-------|
| latest_news.json | ✓ | hn_48639063 |
| hot_ai_candidates.json | ✓ | 6 candidates fetched |
| semantic_ir.json | ✓ | causal_chain structure |
| dialogue_script.json | ✓ | 12 turns |
| dialogue_manifest.json | ✓ | total_duration=62.056s |
| render_ir.json | ✓ | total_duration=62.056s (matches manifest) |
| animation.html | ✓ | 59176 bytes |
| audio/dialogue.wav | ✓ | 2,978,752 bytes |
| audio/turn_*.wav | ✓ | 12 files (d1–d12) |

**render_ir.total_duration == dialogue_manifest.total_duration: 62.056 == 62.056 ✓**

---

## 5. Dual Speaker Voice Configuration

- **Host:** `MINIMAX_TTS_HOST_VOICE_ID` (male voice, configured in .env)
- **Expert:** `MINIMAX_TTS_EXPERT_VOICE_ID` (female voice, configured in .env)
- Both voices successfully generated real audio with no "voice invalid" errors
- No API key or voice_id values exposed in any output JSON or this document

---

## 6. First Job Failure (job_ab7636f446e1)

Before the successful run, an earlier attempt with `target_duration_sec=60, max_turns=14` failed at `semantic_ir` stage:

- **Error:** `INVALID_BEAT_COUNT` — LLM generated 11 beats, validation requires 6–10
- **Repair failed:** Deterministic repair added a beat (b11) instead of removing one, worsening the error
- **Resolution:** Retried with `target_duration_sec=45, max_turns=10` which succeeded

---

## 7. Viewing Experience Scores

| Dimension | Score (1–5) | Notes |
|-----------|-------------|-------|
| 标题清晰度 | 4 | 主标题醒目，卡片标签清晰 |
| 信息密度 | 4 | 因果链完整，要点覆盖到位 |
| 新闻感 | 4 | 深色背景+橙色accent，HN热度标记有新闻感 |
| 动画节奏 | 4 | 节点依次揭示，节奏适中 |
| 字幕可读性 | 4 | 底部字幕条对比度好，字号适中 |
| 音频自然度 | 4 | 两人音色自然，中文流畅 |
| 双人区分度 | 5 | 男女音色差异明显，主持人/专家角色清晰 |
| **Overall** | **4** | 整体可观看，真实TTS体验验证成功 |

---

## 8. Top 5 Issues

1. **b10 beat duration too long (13.258s)** — 最后一个beat(b10)独占13.258s，画面静止时间偏长，建议优化长beat上限
2. **Repair logic adds beats instead of removing** — INVALID_BEAT_COUNT repair策略方向错误，修复时添加而非删除，导致失败
3. **max_turns软上限被突破** — 请求10 turns，实际生成12 turns，LLM扩展超出预期
4. **无MP4导出** — 本次仅生成HTML+音频，未验证最终视频体验
5. **部分节点sub标签截断** — "网络安全专用大模型"callout文字可能溢出

---

## 9. Next Steps

1. **Fix beat-count repair logic** — 当beats > 10时应删除而非添加
2. **Enforce hard max_turns cap** — 确保LLM不超出turns上限
3. **Add beat duration validation** — 长beat(如>10s)应触发警告或拆分
4. **Run MP4 export** — 生成完整视频验证最终观看体验
5. **Try speech-2.8-turbo for cost reduction** — 当前使用speech-2.8-hd，成本较高

---

## 10. Security Verification

- [x] No API key values in any output JSON
- [x] No voice_id values in dialogue_manifest.json (only env var names: `MINIMAX_TTS_HOST_VOICE_ID`, `MINIMAX_TTS_EXPERT_VOICE_ID`)
- [x] No voice_id values in render_ir.json
- [x] No voice_id values in meta.json
- [x] No voice_id values in this document
- [x] `.env` not committed
- [x] `outputs/jobs/job_*` not committed

---

## 11. Git Status

```
Branch: test/cp18.2-real-tts-watchable-demo
Outputs NOT committed: outputs/jobs/job_cb2e6b537940/
Only doc committed: docs/CP18_2_REAL_TTS_WATCHABLE_DEMO.md
```

---

## CP18.2.1: Real TTS Demo Hardening

**Branch:** `fix/cp18.2.1-real-tts-demo-hardening`
**Base commit:** `0e9c421`
**Date:** 2026-06-24

### Changes Made

#### 1. Documentation Desensitization
- Removed specific `male-qn-jingying` / `female-yujie` voice_id values from Section 5
- Voice IDs now referenced only as env var names (`MINIMAX_TTS_HOST_VOICE_ID`, `MINIMAX_TTS_EXPERT_VOICE_ID`)
- Security verification updated to confirm no voice_id values in document

#### 2. Beat-Count Repair Fix (`generate_ir.py`)
- After `_apply_deterministic_repairs()` adds beats, `_enforce_beat_budget()` now runs BEFORE re-validation
- After LLM repair extract + `_minimum_checks()`, `_enforce_beat_budget()` runs before validation
- After deterministic repairs in LLM repair loop, `_enforce_beat_budget()` runs again before re-validation
- `debug_deterministic_repairs.json` now records `BEAT_BUDGET_TRIM` entries with before/after counts

#### 3. max_turns Hard Cap (`generate_dialogue.py`)
- `compress_dialogue_script()` now always enforces max_turns as a hard cap (previously soft)
- LLM generated 12 turns → compressed to 10 (hard cap enforced)
- `dialogue_budget.json` now includes: `requested_max_turns`, `compression_applied`, `reason`
- Hard truncation to `max_turns` even if middle compression can't reduce enough

#### 4. Long Beat Detection (`narration.py`)
- Added `duration_warnings.json` generation in both `generate_narration()` and `generate_dialogue_audio()`
- Threshold: 10 seconds per turn/beat
- Warning records: turn_id/beat_id, speaker, duration, threshold, message
- Cleans up stale `duration_warnings.json` on subsequent runs with no long beats

### E2E Validation Results (job_46332c130b18)

| Field | Value |
|-------|-------|
| job_id | `job_46332c130b18` |
| status | **succeeded** |
| news_title | OpenAI DayBreak – GPT-5.5-Cyber |
| theme | `news_card_v1` |
| LLM | `minimax_m3_openai` |
| TTS | `minimax_dialogue` (real) |
| duration | 57.111s (within 40-70s target) |
| dialogue turns | **10** (hard cap enforced: LLM generated 12 → compressed to 10) |
| audio files | 10 turn_*.wav + 1 dialogue.wav |
| max turn duration | 7.721s (d10, under 10s threshold) |
| long beat warning | None (no beats > 10s) |
| animation.html | ✓ (59078 bytes) |
| dialogue.wav | ✓ |
| render_ir.total_duration | 57.111s == dialogue_manifest.total_duration ✓ |

### dialogue_budget.json (hard cap verified)

```json
{
  "requested_max_turns": 10,
  "max_turns": 10,
  "before_turns": 12,
  "after_turns": 10,
  "compressed": true,
  "compression_applied": true,
  "reason": "LLM generated 12 turns, exceeds max_turns=10. Hard cap applied.",
  "warnings": ["turns 12 > max_turns 10, hard cap enforced"]
}
```

### Security Verification (CP18.2.1)

- [x] No voice_id values in any output JSON
- [x] No API key values in any output JSON
- [x] `dialogue_manifest.json` contains only env var names (`voice_env` fields), no actual voice IDs
- [x] `render_ir.json` has no voice_id values
- [x] This document contains no voice_id values
- [x] `.env` not committed
- [x] `outputs/jobs/job_*` not committed

### Remaining Issues (CP18.2.1)

1. **BROKEN_CAUSAL_CHAIN repair instability** — First E2E attempt (job_20623c6c6575) failed with `BROKEN_CAUSAL_CHAIN` + `UNREVEALED_EDGE` after 2 repair attempts. Succeeded on retry with 3 attempts. LLM repair for structural IR issues is non-deterministic.
2. **Speaker alternation slightly irregular after compression** — d5 and d6 are both expert turns (adjacent same-speaker). Compression doesn't preserve strict host/expert alternation.
3. **No MP4 export** — animation.html + dialogue.wav only; final video experience not verified
4. **Compression drops middle beats** — When compressing 12→10 turns, some reveal content may be lost (e.g., only 10 beats remain from original semantic_ir structure)

### Next Steps

1. **Stabilize IR repair** — Consider stronger IR prompt or multi-step repair for BROKEN_CAUSAL_CHAIN
2. **Preserve speaker alternation in compression** — When compressing, avoid placing same-speaker turns consecutively
3. **Add compression quality check** — Log which beats/turns were dropped during compression
4. **Run MP4 export** — Generate full video to verify end-to-end experience
5. **Beat-to-turn mapping audit** — After compression, verify all critical beats are still referenced
