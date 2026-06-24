# CP18.5: Generation Speed UX

**Branch:** `feat/cp18.5-generation-speed-ux`
**Commit:** `0b52c58` (base)
**Date:** 2026-06-24

---

## 1. Problem Statement

The full generation pipeline is too slow for iterative UX:

- **Real LLM** (minimax_m3_openai) + repair can take 30–60s
- **Real MiniMax Dialogue TTS** — sequential per-turn requests, each ~3–5s
- **MP4 export** — Playwright frame-by-frame screenshots + FFmpeg, ~2 min for 60s video
- **No mode separation** — users could accidentally trigger the slowest path every time

---

## 2. Three Generation Modes

### 2.1 Quick Preview（快速预览）

| Field | Value |
|-------|-------|
| Purpose | Fastest — see news structure and visual layout |
| TTS | `mock_dialogue` |
| MP4 Export | No (`no_export=true`) |
| Dialogue | Yes |
| Expected time | ~5–10s |

**Payload:**
```json
{
  "tts_provider": "mock_dialogue",
  "no_export": true,
  "dialogue": true,
  "target_duration_sec": 45,
  "max_turns": 10
}
```

### 2.2 Voice Preview（语音预览）

| Field | Value |
|-------|-------|
| Purpose | Hear real dual-speaker dialogue, no MP4 export |
| TTS | User-selected (e.g. `minimax_dialogue`) |
| MP4 Export | No (`no_export=true`) |
| Dialogue | Yes |
| Expected time | ~30–90s (TTS time) |

**Payload:**
```json
{
  "tts_provider": "minimax_dialogue",
  "no_export": true,
  "dialogue": true,
  "target_duration_sec": 45,
  "max_turns": 10
}
```

### 2.3 Final Export（最终导出）

| Field | Value |
|-------|-------|
| Purpose | Full production-ready MP4 |
| TTS | User-selected (e.g. `minimax_dialogue`) |
| MP4 Export | Yes (`no_export=false`) |
| Dialogue | Yes |
| Expected time | ~2–5 min |

**Payload:**
```json
{
  "tts_provider": "minimax_dialogue",
  "no_export": false,
  "dialogue": true,
  "target_duration_sec": 45,
  "max_turns": 10
}
```

---

## 3. UI Changes

### 3.1 New Fieldset: "生成模式"

Three radio buttons added to the input panel, replacing the standalone `check-export` checkbox:

```
○ 快速预览  (default, checked)
○ 语音预览
○ 最终导出 MP4
```

Below the radios, a `#gen-mode-hint` paragraph shows contextual help text.

### 3.2 Button Text Changes with Mode

| Mode | Button Text |
|------|-------------|
| 快速预览 | 生成快速预览 |
| 语音预览 | 生成语音预览 |
| 最终导出 MP4 | 导出 MP4 成片 |

### 3.3 Hint Text per Mode

- **快速预览:** "最快，只生成动画预览，不调用真实 TTS，不导出 MP4。"
- **语音预览:** "生成真实双人语音，但不导出 MP4。"
- **最终导出 MP4:** "生成完整 MP4，耗时较长，请耐心等待。"

### 3.4 check-export Checkbox

Hidden from the user in the new UI (the generation mode radios control export behavior). Kept in DOM for potential future programmatic use.

---

## 4. Implementation Details

### 4.1 Files Changed

- `web/index.html` — Added generation mode fieldset and hint paragraph; updated button text and footer
- `web/app.js` — Added `updateGenModeUI()`, generation mode radio listeners, modified `btnGenerate` payload logic
- `web/style.css` — Added `.gen-mode-hint` and `.checkbox-export-hidden` styles

### 4.2 Payload Override Logic

In `btnGenerate.click`:

```javascript
const genMode = document.querySelector('input[name="gen_mode"]:checked').value;
const effectiveTts = (genMode === "fast") ? "mock_dialogue" : selectTtsProvider.value;
const effectiveNoExport = (genMode !== "export");
```

LLM provider is passed through as user-selected (can be `mock` or `minimax_m3_openai`).

---

## 5. No Heavy E2E Run

- ✓ No real LLM called
- ✓ No real TTS called
- ✓ No MP4 exported
- ✓ No long background jobs waited on

Verification was done by:
- Code review of the payload construction logic
- Checking that default state (`fast` mode) sets `no_export=true` and `tts_provider=mock_dialogue`

---

## 6. Performance Optimization Roadmap (Future)

| Direction | Description |
|-----------|-------------|
| TTS concurrency | Parallelize per-turn TTS requests |
| MP4 lower FPS | Preview at 15fps instead of 30fps |
| MP4 lower resolution | Render at 720p for preview, not full 1080p |
| NVENC / QSV | GPU-accelerated H.264 encoding |
| Remotion renderer | Server-side video rendering, no Playwright |
| Frame render parallelism | Concurrent browser tab rendering |
| Cached TTS | Reuse previously generated audio for same text |

---

## 7. Security Notes

Same as V0.1 baseline — no new security concerns introduced.
