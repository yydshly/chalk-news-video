# CP37: Contextual Cartoon Anchor Layer

**Branch:** `feat/cp37-contextual-cartoon-anchor-layer`
**Commit:** `feat(cp37): add contextual cartoon anchor layer`
**Date:** 2026-06-25

---

## 1. Why Add the Anchor Layer After CP36

CP36 established the **fixed 9:16 video stage** — a constrained canvas that feels like a video frame instead of a web page. However, the stage still looked like "news cards floating on a dark background" — it lacked a presenter. CP37 adds a **cartoon anchor layer** to create the sensation of "a presenter talking about the news," without requiring real video generation.

The anchor is deliberately SVG/CSS-based (not a real digital human, AI-generated image, or Lottie) because:
1. **Zero external dependencies** — no CDN, no asset download
2. **Fully可控** — expression/action/position driven by CSS classes, no player needed
3. **Fast to render** — pure string concatenation, no animation engine
4. **Stage architecture first** — establish the layer hierarchy before investing in richer character assets

---

## 2. Why SVG/CSS Rather Than Digital Human / Video Generation

| Approach | External Deps | Complexity | Fits Current Stage | Verdict |
|----------|--------------|------------|-------------------|---------|
| SVG + CSS (this CP) | None | Low | Yes | ✅ Implemented |
| Lottie | CDN / npm bundle | Medium | Needs player | Deferred |
| Rive | CDN / npm bundle | Medium | Needs runtime | Deferred |
| AI-generated avatar | API call | High | Needs video pipeline | Deferred |
| Real video anchor | Camera + studio | Very High | Not applicable | Not planned |

SVG was chosen because it is self-contained, requires no runtime, and can be embedded directly in the HTML string.

---

## 3. Anchor Layer Stage Hierarchy

```
.video-stage (9:16, overflow:hidden)
  ├── .stage-bg          (z-index: 0, animated dark-red gradient)
  ├── .stage-topbar     (z-index: 20, BREAKING NEWS badge)
  ├── .stage-recap      (z-index: 18, RECAP chip)
  ├── .stage-opening-label (z-index: 18, "📍 开场")
  ├── .stage-title-area (z-index: 15, title + subtitle)
  ├── .stage-main-card  (z-index: 12, lead news — shifted right to leave room for anchor)
  ├── .stage-supporting (z-index: 12, compact support cards — right side)
  ├── .stage-anchor-layer (z-index: 16, cartoon SVG — bottom-left)
  ├── .stage-subtitle-bar (z-index: 14, subtitle text)
  ├── .stage-closing-chip (z-index: 15, "📍 结尾" chip)
  └── .stage-timeline  (z-index: 20, bottom timeline rail)
```

Anchor is at z-index 16 — above title area and supporting cards, below topbar (20) and timeline (20). It does not overlap the lead card or subtitle bar.

---

## 4. New Functions Added

| Function | Location | Purpose |
|----------|----------|---------|
| `inferNewsContextFromContract(contract)` | `web/app.js` | Keyword-based context inference (no LLM) |
| `inferEpisodeAnchorCue(contract)` | `web/app.js` | Maps context → expression/action/position/tone |
| `renderCartoonAnchorSvg(anchorCue)` | `web/app.js` | Generates inline SVG with expression-aware face |
| `getAnchorActionClass(action)` | `web/app.js` | Maps action name → CSS class string |
| `getAnchorExpressionClass(expression)` | `web/app.js` | Maps expression name → CSS class string |
| `renderCartoonAnchorLayer(anchorCue)` | `web/app.js` | Full anchor HTML (wrapper div + SVG) |

---

## 5. Context Inference Rules (Keyword-Based, No LLM)

Input sources: `episode.title`, `episode.subtitle`, `news_cards[].headline`, `news_cards[].badges`, `news_cards[].emphasis`, `news_cards[].layout`

### Keywords → `context_type`

| context_type | Trigger Keywords |
|--------------|------------------|
| `alert` | breaking, outage, security, risk, lawsuit, ban, regulation, alert, emergency, crisis, scandal |
| `launch` | launch, release, announce, unveil, model, product, feature, debut, coming soon |
| `data` | benchmark, score, ranking, leaderboard, funding, valuation, revenue, profit, market, percent, % |
| `research` | research, paper, arxiv, study, reasoning, method, dataset, experiment, result, finding |
| `general` | fallback — none of the above |

### `severity` derived from context_type

| context_type | severity |
|--------------|----------|
| `alert` | `high` |
| `launch` | `normal` |
| `data` | `normal` |
| `research` | `low` |
| `general` | `normal` |

---

## 6. Anchor Cue Mapping

```
context_type + severity → { role, position, expression, action, tone }
```

| context_type | expression | action | position | tone |
|--------------|------------|--------|----------|------|
| `alert` | serious / focused | `alert_point` | left | breaking |
| `launch` | excited | `introduce` | left | energetic |
| `data` | focused | `point_right` | left | analytical |
| `research` | thinking | `explain` | left | calm |
| `general` | neutral | `talk` | left | normal |

---

## 7. Supported Expressions

| Expression | Eye Shape | Mouth Shape | Eyebrow | Notes |
|------------|-----------|-------------|---------|-------|
| `neutral` | Normal ellipses | Gentle smile curve | Neutral | Default |
| `serious` | Slightly squashed | Flat line | Lowered | Alert situations |
| `excited` | Larger circles | Open ellipse | Raised | Cheek blush added |
| `focused` | Normal | Smile curve | Slightly lowered | Analytical tone |
| `thinking` | Slightly squashed | Small curve | Asymmetric | One brow raised |

---

## 8. Supported Actions

| Action | Body Animation | Arm Animation | Used For |
|--------|---------------|----------------|---------|
| `talk` | `anchorFloat` 2.5s infinite | `armWave` 2s infinite | general |
| `point_right` | `anchorFloat` 2.5s infinite | `armPoint` 1.5s infinite | data |
| `alert_point` | `anchorAlert` 1.2s infinite | `armPoint` 0.8s infinite | alert |
| `introduce` | `anchorFloat` 2.5s infinite | `armIntroduce` 2s infinite | launch |
| `explain` | `anchorFloat` 3s infinite | `armWave` 2.5s infinite | research |

---

## 9. SVG Character Design

The anchor is drawn with inline SVG primitives:

- **ViewBox:** `0 0 120 180` (half-body portrait, suitable for bottom-left placement)
- **Elements:** head, hair, ears, eyes (white + pupil + shine), eyebrows, nose, mouth, neck, suit jacket, tie, left arm, right arm, hand circles
- **Skin color:** `#f5c9a0` (warm peach)
- **Suit:** `#1a1a2e` (dark navy)
- **Tie:** `#dc2626` (breaking-news red)
- **Hair:** `#2d1b0e` (dark brown)
- **Cheek blush:** conditional on `excited` expression

All colors use CSS variables derived from `st` theme object where appropriate. The SVG has `aria-hidden="true"` to avoid screen reader interference.

---

## 10. CSS Animation Architecture

All animations are **pure CSS keyframes** — no JavaScript:

```css
@keyframes anchorFloat { ... }   /* body vertical oscillation */
@keyframes anchorAlert { ... }   /* body rotation for alert */
@keyframes armWave { ... }       /* arm swing */
@keyframes armPoint { ... }      /* arm pointing */
@keyframes armIntroduce { ... }   /* arm scale + rotate */
@keyframes mouthOpen { ... }      /* mouth vertical scale */
@keyframes pupilLook { ... }     /* pupil horizontal drift */
```

Action classes are composed onto `.stage-anchor-layer` div:
```css
.anchor-action-talk { animation: anchorFloat 2.5s ease-in-out infinite; transform-origin: center bottom; }
.anchor-action-talk .anchor-arm-right { animation: armWave 2s ease-in-out infinite; transform-origin: 90px 108px; }
```

Expression classes provide visual overrides:
```css
.anchor-expression-excited .cartoon-anchor-svg { filter: brightness(1.05); }
```

---

## 11. Layout Adjustment: Main Card Shifted Right

To prevent the anchor (bottom-left, width 90px) from overlapping the lead news card, the main card was shifted right:

```css
/* Before CP37 */
.stage-main-card { left: 14px; right: 14px; }

/* After CP37 */
.stage-main-card { left: 108px; right: 14px; }
```

The anchor occupies the bottom-left corner (10px from left, 110px from bottom). The main card now starts at x=108, giving the anchor unobstructed space. All other elements (supporting cards, subtitle bar, timeline) remain at their original positions.

---

## 12. Security Boundaries (Unchanged)

All CP33.1 / CP35 / CP36 boundaries remain enforced:

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

No character cue data is written to any backend contract or database.

---

## 13. What CP37 Is NOT

- **NOT a real digital human** — SVG illustration only
- **NOT AI-generated** — no DALL-E, Stable Diffusion, etc.
- **NOT Lottie / Rive** — pure inline SVG + CSS
- **NOT Remotion-connected** — no video render pipeline
- **NOT lip-sync** — mouth animation is decorative oscillation, not audio-driven
- **NOT context-aware via LLM** — keyword rules only
- **NOT affecting other 4 styles** — they remain web layouts unchanged
- **NOT saved to contract** — anchor cue is inferred at render time, not stored

---

## 14. Current Limitations

- SVG character is simple geometric shapes — not a detailed illustration
- No lip-sync to real audio (mouth animation is decorative oscillation)
- Context inference is keyword-based only — no semantic LLM understanding
- Anchor position is fixed (bottom-left) — not dynamically repositioned based on card layout
- Only `breaking_news_v1` has the anchor layer — other 4 styles unchanged
- No interaction with timeline (anchor doesn't react to playback position)
- No audio feedback — purely visual
