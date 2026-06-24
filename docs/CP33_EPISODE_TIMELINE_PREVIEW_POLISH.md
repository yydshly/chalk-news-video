# CP33: Episode Timeline Preview Polish

**Branch:** `feat/cp33-episode-timeline-preview-polish`
**Commit:** `feat(cp33): polish episode timeline html preview`
**Date:** 2026-06-25

---

## 1. Why Polish the Mock Episode HTML?

CP28/31 generated functional but visually flat mock episode HTML. It looked like a static document rather than a video preview. CP33 upgrades the HTML to feel like a real 60-second news video timeline preview.

---

## 2. Visual Structure

### Hero Header
- Gradient dark background with subtle grid overlay
- Episode title, subtitle, theme name, total duration
- Stats row: news count, total time, lead news count
- Eyebrow badges: "🔥 合集", theme name, duration

### Timeline Rail
- Horizontal scrollable track below header
- Each marker shows: dot (color-coded), pseudo timecode (MM:SS), segment name
- Color coding: blue=opening, amber=lead, gray=supporting, green=closing
- Dots for lead segments have a subtle glow
- Opening/closing dots pulse gently

### News Cards
Each card retains required attributes: `class="mock-news-card"` and `data-section-type="news_segment"`.

Enhanced content:
- Card header row: rank number, pseudo time range, duration, lead badge
- Headline text (large, bold)
- Meta row: layout tag (blue), emphasis tag (amber), badges
- Footer: audio clip count, role label

Lead cards: amber left border, slightly different background.

### Transition Rows
Lightweight dividers between cards showing transition text ("接着看下一条" or from `transition.visual.text`).

### Closing Section
Gradient card with "重点回看" badge, closing title, focus news ID.

---

## 3. CSS Animations

| Animation | Element | Effect |
|-----------|---------|--------|
| `fadeUp` | News cards | Slides up on load |
| `pulseLine` | Opening/closing dots | Gentle opacity pulse |
| `shimmer` | Defined but not used | Background shimmer (available) |

All pure CSS keyframes, no JavaScript, no external dependencies.

---

## 4. Security

Same as CP31 — all original security checks preserved:
- `<!DOCTYPE html>` required
- No API key / voice_id
- No external `https?://` links (localhost allowed)
- No `<script>` tags
- No remote images

Additionally enforced:
- `mock-news-card` class required
- "开场" and "结尾" required
- `data-section-type="news_segment"` on cards

---

## 5. Compatibility

- `previewMockEpisodeHtml()` → unchanged behavior, improved visuals
- `saveMockEpisodeHtml()` → unchanged behavior, improved visuals
- `validateMockEpisodeHtml()` → unchanged
- Backend `/api/episode/mock-html` → unchanged
- All downstream: history, open, download → unchanged
- 12-style gallery → unchanged
- Style recommendations → unchanged

---

## 6. Lightweight Verification Results

| Test | Result |
|------|--------|
| Preview iframe loads with timeline rail | ✓ |
| Pseudo timecodes shown (MM:SS format) | ✓ |
| Hero header with stats | ✓ |
| Lead cards have amber border/glow | ✓ |
| Each card has `class="mock-news-card"` | ✓ |
| Each card has `data-section-type="news_segment"` | ✓ |
| HTML contains "开场" and "结尾" | ✓ |
| No external http/https links | ✓ |
| No API key / voice_id | ✓ |
| Save and history work | ✓ |
| No `/api/jobs` called | ✓ |
| No real LLM / TTS / MP4 | ✓ |

---

## 7. Current Limitations

- Pure CSS animations, not actual video playback
- Pseudo timecodes are estimates from `duration_hint_sec`
- No real audio, no subtitles, no MP4
- Not a Remotion render template
- Not integrated with actual video pipeline
