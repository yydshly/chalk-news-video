# CP36: Fixed Video Stage Preview

**Branch:** `feat/cp36-fixed-video-stage-preview`
**Commit:** `feat(cp36): add fixed video stage preview`
**Date:** 2026-06-25

---

## 1. Why CP35 Was Still "Web Page" Preview

CP35 (and CP35.1/CP35.2) implemented 5 distinct episode layout styles, but all of them were **web page information flows**:

- Vertical card scroll
- Hero section at top
- Cards stacked vertically
- Footer at bottom
- Horizontal timeline rail (scrollable)

These layouts looked like rendered web articles, not video frames. They used `body` scroll to present information — a newspaper or blog layout translated to browser. The iframe showed a full-page scroll view, not a fixed video canvas.

---

## 2. CP36 Goal: Fixed Video Canvas

CP36 transitions `breaking_news_v1` from a web layout to a **fixed 9:16 video stage**:

- The iframe now renders a **fixed-aspect-ratio video frame** (9:16, vertical)
- Content is **constrained inside the frame**, not flowing in a page scroll
- The preview feels like a **video player viewport** — not a news website
- The stage has video-like **layer hierarchy** (background → topbar → title → card → subtitle → timeline)

This establishes the baseline architecture for future video generation without yet implementing real render.

---

## 3. Why Only `breaking_news_v1` This Round

Only `breaking_news_v1` was upgraded this checkpoint:

1. **News urgency** — breaking news format is most naturally suited to short-video aesthetics
2. **Easy transition** — red/black color scheme and lead-card structure translate well to stage
3. **Anchor potential** — future: cartoon anchor / presenter overlay fits naturally here
4. **Isolation** — other 4 styles stay as web layouts for parallel comparison

Other styles (`timeline_daily_v1`, `data_dashboard_v1`, `research_briefing_v1`, `podcast_cards_v1`) remain unchanged.

---

## 4. 9:16 Stage Structure

```
.video-stage-shell          ← full-viewport centering shell
  └── .video-stage          ← fixed 9:16 frame, centered, rounded
        ├── .stage-bg      ← animated dark-red gradient background
        ├── .stage-topbar  ← BREAKING NEWS badge + meta (news count · duration)
        ├── .stage-recap   ← RECAP chip (top-right overlay)
        ├── .stage-opening-label  ← "📍 开场" label
        ├── .stage-title-area    ← episode title + subtitle
        ├── .stage-main-card     ← lead news card (with mock-news-card, data-section-type)
        ├── .stage-supporting   ← stacked compact supporting cards (right side)
        ├── .stage-subtitle-bar ← bottom subtitle bar (2-line clamp)
        ├── .stage-closing-chip ← "📍 结尾" chip
        └── .stage-timeline     ← bottom timeline rail (tl-rail / tl-track)
```

### CSS Key Specs

```css
.video-stage-shell {
  width: 100%;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #050505;
  padding: 24px;
}

.video-stage {
  position: relative;
  width: min(420px, 92vw);
  aspect-ratio: 9 / 16;
  overflow: hidden;
  border-radius: 24px;
  background: #0a0000;
  box-shadow: 0 24px 80px rgba(0,0,0,.55);
}
```

The stage uses `aspect-ratio: 9/16` — a vertical short-video canvas. Content is absolutely positioned inside the stage, constrained by `overflow: hidden`.

---

## 5. Stage Layer Breakdown

### Background Layer (`.stage-bg`)
Dark red-black gradient with a slow `stageBgPulse` animation (6s breathing effect).

### Topbar Layer (`.stage-topbar`)
Fixed at top. Contains:
- BREAKING NEWS animated badge (`.stage-breaking-badge` — CSS `breakingBlink` 2s)
- News count and total duration in monospace

### Title Layer (`.stage-title-area`)
Positioned below topbar. Contains:
- Episode title in bold white
- Subtitle in muted red

### Lead Card Layer (`.stage-main-card`)
Primary content card with:
- `class="mock-news-card mock-news-card-lead"`
- `data-section-type="news_segment"`
- Lead badge, headline (15px bold), time_range, duration, layout tag
- `cardEnter` animation (0.5s ease-out)

### Supporting Cards Layer (`.stage-supporting`)
Compact stacked cards positioned bottom-right:
- Max 3 cards shown
- Clamped 2-line headlines
- `cardEnter` animation with 0.25s delay
- Each has `mock-news-card` + `data-section-type="news_segment"`

### Subtitle Layer (`.stage-subtitle-bar`)
Bottom-fixed subtitle bar:
- Uses `opening.title` or lead headline as mock subtitle text
- 2-line clamp
- `subtitleSlideUp` animation (0.5s 0.4s delay)

### Closing Chip (`.stage-closing-chip`)
Positioned bottom-left above timeline:
- Red dot + "📍 结尾 — [closing title]"

### Timeline Layer (`.stage-timeline`)
Bottom-most visible layer:
- `tl-rail` / `tl-track` / `tl-time` all present
- All dots red (breaking news theme)
- Compact design as video progress rail

---

## 6. CSS Animations (No JavaScript)

All animations are pure CSS:

| Animation | Target | Duration | Effect |
|-----------|--------|----------|--------|
| `stageBgPulse` | `.stage-bg` | 6s infinite | Background opacity breathing |
| `breakingBlink` | `.stage-breaking-badge` | 2s infinite | Badge opacity pulse |
| `cardEnter` | `.stage-main-card` | 0.5s ease-out | Lead card fade-up |
| `cardEnter` (delayed) | `.stage-supporting` | 0.5s 0.25s ease-out | Support cards staggered entry |
| `subtitleSlideUp` | `.stage-subtitle-bar` | 0.5s 0.4s ease-out | Subtitle bar slide-up |
| `pulseLine` | `.tl-dot-closing` | 2s infinite | Closing dot pulse |

No JavaScript animation, no external libraries.

---

## 7. Why No Cartoon Character / Anchor Yet

Cartoon anchor / presenter overlay is intentionally deferred because:

1. **Layout first** — establish fixed canvas before layering character animation
2. **Asset complexity** — requires SVG/PNG sprite or Lottie, adds external-dependency risk
3. **Positioning** — anchor placement depends on stage layout; we need stage stability first
4. **Future work** — anchor will overlay on top of the existing stage layers as a separate `z-index` layer

---

## 8. Why Not Connect Remotion Yet

Remotion integration is intentionally deferred because:

1. **Validation layer needed first** — fixed canvas HTML validates before video render
2. **Composition model not finalized** — how narrator audio + news cards + anchor compose is TBD
3. **CDN/bundle complexity** — Remotion requires npm bundle and `@remotion/browser` which adds external deps
4. **Stage architecture sufficient** — the HTML stage structure maps directly to future Remotion composition; this is the thin wedge

Future CP will add:
- `@remotion/browser` composition
- Real subtitle track from narration timing
- Anchor layer as React component
- MP4 export via `npx remotion render`

---

## 9. Security Boundaries (Unchanged)

CP36 maintains all CP33.1 / CP35 security boundaries:

| Check | Required |
|-------|----------|
| `<!DOCTYPE html>` | ✅ |
| `mock-news-card` class | ✅ |
| `data-section-type="news_segment"` | ✅ |
| `tl-rail` or `tl-track` | ✅ |
| `tl-time` | ✅ |
| "开场" literal | ✅ |
| "结尾" literal | ✅ |
| No API key / voice_id | ✅ |
| No `https?://` external links | ✅ |
| No `<script>` tags | ✅ |
| No remote `<img>` links | ✅ |
| No external CDN | ✅ |
| No external fonts | ✅ |

---

## 10. What CP36 Is NOT

- **NOT real video** — still HTML mock
- **NOT connected to Remotion** — no video render pipeline
- **NOT MP4 export** — no encoding
- **NOT real audio** — no TTS or audio tracks
- **NOT real subtitles** — mock subtitle text only
- **NOT a complete video player** — no playback controls, no real timeline
- **NOT the 5th style** — only `breaking_news_v1` upgraded; others stay web layout
- **NOT a new template v2** — same `episode_template_v1` contract

---

## 11. Architecture

```
renderIr
  → buildEpisodeTemplateContract(renderIr)
       sets contract.template_id = currentEpisodePreviewStyle
       ↓
  → validateEpisodeTemplateContract(contract)
       accepts 5 valid template_ids
       ↓
  → renderEpisodeTemplateHtml(contract)
       if breaking_news_v1 → renderBreakingNewsStageEpisodeHtml()  ← NEW
       else if data_dashboard_v1 → renderDataDashboardEpisodeHtml()
       else if research_briefing_v1 → renderResearchBriefingEpisodeHtml()
       else if podcast_cards_v1 → renderPodcastCardsEpisodeHtml()
       else → renderTimelineDailyEpisodeHtml()
       ↓
    HTML (breaking_news_v1 = fixed 9:16 stage canvas; others = web layout)
```

---

## 12. New Function: `renderBreakingNewsStageEpisodeHtml`

**Location:** `web/app.js` — inserted after `renderBreakingNewsEpisodeHtml`

**Signature:** `function renderBreakingNewsStageEpisodeHtml(contract, st)`

**Responsibilities:**
1. Generates fixed 9:16 video stage HTML
2. Uses `aspect-ratio: 9/16` CSS for fixed canvas
3. Positions all content absolutely within the stage
4. Includes all required validation markers (`mock-news-card`, `data-section-type`, `tl-rail`, `tl-time`, "开场", "结尾")
5. Pure string concatenation, no external deps

**Dispatcher update:**
```js
if (templateId === "breaking_news_v1") return renderBreakingNewsStageEpisodeHtml(contract, st);
```

Old `renderBreakingNewsEpisodeHtml` (CP35.1 web layout) is retained in codebase but no longer called from dispatcher.

---

## 13. Lightweight Verification Results

| Test | Result |
|------|--------|
| `breaking_news_v1` preview shows 9:16 fixed canvas | ✅ |
| Content constrained within stage (no page scroll) | ✅ |
| Top BREAKING NEWS banner with animation | ✅ |
| Episode title and subtitle visible | ✅ |
| Lead news card (mock-news-card + data-section-type) | ✅ |
| Supporting stacked cards (right side, compact) | ✅ |
| Subtitle bar (bottom, 2-line clamp) | ✅ |
| Bottom timeline rail (tl-rail / tl-track / tl-time) | ✅ |
| Closing chip with "结尾" literal | ✅ |
| Opening label with "开场" literal | ✅ |
| CSS animations (bg pulse, badge blink, card enter) | ✅ |
| `validateMockEpisodeHtml` passes | ✅ |
| No `<script>` tags | ✅ |
| No external http/https links | ✅ |
| No API key / voice_id | ✅ |
| Other 4 styles unchanged (web layouts) | ✅ |
| `timeline_daily_v1` preview still works | ✅ |
| `data_dashboard_v1` preview still works | ✅ |
| `research_briefing_v1` preview still works | ✅ |
| `podcast_cards_v1` preview still works | ✅ |
| Preview mock episode saves HTML artifact | ✅ |
| History open works | ✅ |
| No real LLM / TTS / MP4 / Remotion / job | ✅ |

---

## 14. Current Limitations

- Still HTML mock — not a real video render
- No real playback time轴
- No real subtitles (mock text only)
- No cartoon anchor / presenter
- Only `breaking_news_v1` in stage mode; other 4 styles remain web layout
- No Remotion integration
- No MP4 export
- No real audio track
- No character animation
