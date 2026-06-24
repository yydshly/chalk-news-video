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

---

## CP33.1: Timeline Preview Safety Hardening

**Branch:** `fix/cp33.1-timeline-preview-safety`
**Commit:** `fix(cp33.1): harden episode timeline preview validation`
**Date:** 2026-06-25

### 1. Issues Fixed

#### 1.1 Footer Title Not Escaped

**Problem:** In `buildMockEpisodeHtml()`, the footer rendered `renderIr.episode_title` directly without `escapeHtml()`:

```js
// Before (vulnerable)
'<span>' + renderIr.episode_title + '</span>'

// After (safe)
'<span>' + escapeHtml(renderIr.episode_title || "") + '</span>'
```

**Impact:** If `episode_title` contained user-controlled content with characters like `<`, `>`, `&`, `"`, it could break HTML structure or enable XSS in certain contexts. Fixed by wrapping with `escapeHtml()` and providing a fallback `""` for null/undefined.

#### 1.2 Missing `data-section-type` Validation

**Problem:** `validateMockEpisodeHtml()` validated `mock-news-card` class presence but did not check for `data-section-type="news_segment"`, which is a required structural attribute on timeline preview cards per CP33 spec.

**Fix:** Added strict check:

```js
if (html.indexOf('data-section-type="news_segment"') === -1) {
  errors.push('HTML 必须包含 data-section-type="news_segment"');
}
```

#### 1.3 Missing Timeline Rail Validation

**Problem:** The timeline rail (`tl-rail` / `tl-track`) and pseudo timecode (`tl-time`) markers are core structural elements of the timeline preview, but were not validated.

**Fix:** Added checks:

```js
if (html.indexOf("tl-rail") === -1 && html.indexOf("tl-track") === -1) {
  errors.push("HTML 必须包含 timeline rail (tl-rail 或 tl-track)");
}
if (html.indexOf("tl-time") === -1) {
  errors.push("HTML 必须包含伪时间码 (tl-time)");
}
```

#### 1.4 Script Tag Rejection

**Problem:** While the CP31 spec documents "no `<script>` tags", the validator used a general external-link regex that could miss `<script>` tags in certain positions.

**Fix:** Added explicit rejection:

```js
if (/<script\b/i.test(html)) {
  errors.push("HTML 不允许包含 script 标签");
}
```

Also added explicit rejection of `<img>` tags with remote `src`:

```js
if (/<img[^>]*src=["']?https?:\/\//i.test(html)) {
  errors.push("HTML 不允许 img 标签包含外部链接");
}
```

### 2. Security Checks Added

| Check | Rule |
|-------|------|
| `data-section-type="news_segment"` | Required in HTML |
| Timeline rail | Required (`tl-rail` or `tl-track`) |
| Pseudo timecode | Required (`tl-time`) |
| `<script>` tags | Explicitly rejected |
| `<img>` with remote src | Explicitly rejected |
| All prior checks | Preserved (API key, voice_id, external http) |

### 3. Lightweight Verification Results

| Test | Result |
|------|--------|
| Footer title escaped with `escapeHtml()` | ✓ |
| `validateMockEpisodeHtml` rejects missing `data-section-type` | ✓ |
| `validateMockEpisodeHtml` rejects missing timeline rail | ✓ |
| `validateMockEpisodeHtml` rejects missing `tl-time` | ✓ |
| `validateMockEpisodeHtml` rejects `<script>` tag | ✓ |
| `validateMockEpisodeHtml` rejects `<img>` with remote src | ✓ |
| Preview iframe still works | ✓ |
| Save to history still works | ✓ |
| No external http/https in HTML | ✓ |
| No API key / voice_id in HTML | ✓ |
| No `/api/jobs` called | ✓ |
| No real LLM / TTS / MP4 | ✓ |
| `outputs/episode_previews/*.html` not committed | ✓ |

### 4. Compatibility

All CP33 capabilities preserved:
- `previewMockEpisodeHtml()` → works
- `saveMockEpisodeHtml()` → works
- `/api/episode/mock-html` → works
- `/api/episode/html-history` → works
- Timeline rail and pseudo timecodes → present in HTML
- `mock-news-card` and `data-section-type="news_segment"` → present on cards
