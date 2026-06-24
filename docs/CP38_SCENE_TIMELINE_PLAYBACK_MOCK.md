# CP38: Scene Timeline / Shot Playback Mock

**Branch:** `feat/cp38-scene-timeline-playback-mock`
**Commit:** `feat(cp38): add scene timeline playback mock`
**Date:** 2026-06-25

---

## 1. Why CP37.1 Was Still Static

CP37.1 polished the cartoon anchor's visuals, but the stage still rendered all elements simultaneously — every layer appeared at once when the HTML loaded. The stage looked like a snapshot of a video, not a video in progress. CP38 adds a CSS-driven shot timeline that makes elements enter sequentially, creating the sensation of a short-video playback.

---

## 2. CP38 Goal: Shot-by-Shot Playback Mock

Transform the breaking_news_v1 stage from a **static snapshot** to a **sequential playback sequence** using only CSS `animation-delay`. No JavaScript, no video player, no Remotion.

---

## 3. Shot Timeline Structure

`buildBreakingNewsShotTimeline(contract)` returns:

| shot_id | label | start_sec | duration_sec | layer_targets |
|---------|-------|-----------|--------------|---------------|
| opening | 开场 | 0 | 3 | stage-topbar, stage-title-area |
| anchor_intro | 主持人导入 | 1 | 3 | stage-anchor-layer |
| lead_news | 主新闻 | 3 | 6 | stage-main-card, stage-subtitle-bar |
| supporting_news | 补充快讯 | 7 | 6 | stage-supporting |
| closing | 结尾 | 11 | 3 | stage-closing-chip, stage-timeline |

**Total mock duration: ~12s** (the `mockProgressFill` animation runs 12s linear).

---

## 4. CSS Animation Delay Strategy

Each stage layer enters via `animation-delay`:

| Layer | Animation | Delay |
|-------|-----------|-------|
| `.stage-topbar` | `shotFadeIn` 0.5s | 0.1s |
| `.stage-title-area` | `shotFadeIn` 0.6s | 0.2s |
| `.stage-opening-label` | `shotFadeIn` 0.4s | 0.15s |
| `.stage-recap` | `shotFadeIn` 0.4s | 0.3s |
| `.stage-shot-label` | `shotFadeIn` 0.4s | 0.1s |
| `.stage-anchor-layer` | `anchorEnter` 0.7s | 1.0s (then `anchorFloat` at 1.8s) |
| `.stage-main-card` | `shotCardIn` 0.6s | 2.5s |
| `.stage-subtitle-bar` | `shotFadeIn` 0.5s | 3.2s |
| `.stage-supporting` | `shotFadeIn` 0.5s | 5.0s |
| `.stage-support-card:nth(1)` | `shotCardIn` 0.5s | 5.2s |
| `.stage-support-card:nth(2)` | `shotCardIn` 0.5s | 5.55s |
| `.stage-support-card:nth(3)` | `shotCardIn` 0.5s | 5.9s |
| `.stage-closing-chip` | `shotFadeIn` 0.5s | 9.5s |

Entrance animations:

```css
@keyframes shotFadeIn {
  from { opacity: 0; transform: translateY(-6px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes anchorEnter {
  from { opacity: 0; transform: translateX(-14px) translateY(8px); }
  to { opacity: 1; transform: translateX(0) translateY(0); }
}

@keyframes shotCardIn {
  from { opacity: 0; transform: translateY(14px) scale(0.97); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
```

---

## 5. Mock Progress Bar

A visual red progress bar fills over 12 seconds at the bottom of the stage:

```html
<div class="stage-progress-wrap">
  <div class="stage-progress-track">
    <div class="stage-progress-fill"></div>
  </div>
</div>
```

```css
.stage-progress-fill {
  animation: mockProgressFill 12s linear forwards;
}

@keyframes mockProgressFill {
  0% { width: 0%; }
  100% { width: 100%; }
}
```

**Important:** The existing `tl-rail / tl-track / tl-time` structure is preserved — the progress bar is an enhancement layered on top, not a replacement. Validation still requires `tl-rail` and `tl-time`.

---

## 6. Shot Label

A small non-intrusive label at the top center shows the shot flow:

```
SHOT FLOW · 开场 → 主持人 → 主新闻 → 快讯 → 结尾
```

Styled as a tiny pill badge (`font-size: 8px`, dark semi-transparent background). Fades in at 0.1s with the opening shot.

---

## 7. Supporting Cards Stagger

Each supporting card enters with a 0.35s stagger:

```css
.stage-support-card:nth-child(1) { animation-delay: 5.2s; }
.stage-support-card:nth-child(2) { animation-delay: 5.55s; }
.stage-support-card:nth-child(3) { animation-delay: 5.9s; }
```

This creates the effect of news items "popping in" one after another.

---

## 8. Anchor Entrance

The anchor already had continuous action animations. CP38 wraps the anchor layer with an entrance animation that:
1. Starts invisible (`opacity: 0`)
2. Slides in from left at 1.0s
3. Then transitions to the normal float + action animation at 1.8s

---

## 9. Security Boundaries (Unchanged)

All CP33.1 / CP35 / CP36 / CP37 boundaries remain enforced:

| Check | Required |
|-------|----------|
| `<!DOCTYPE html>` | ✅ |
| `mock-news-card` class | ✅ |
| `data-section-type="news_segment"` | ✅ |
| `tl-rail` or `tl-track` | ✅ (preserved alongside progress bar) |
| `tl-time` | ✅ (preserved alongside progress bar) |
| "开场" literal | ✅ |
| "结尾" literal | ✅ |
| No API key / voice_id | ✅ |
| No `https?://` external links | ✅ |
| No `<script>` tags | ✅ |
| No remote `<img>` links | ✅ |
| No external CDN | ✅ |
| No external fonts | ✅ |

---

## 10. What CP38 Is NOT

- **NOT a real video player** — no JS play/pause/seek controls
- **NOT connected to Remotion** — no video render pipeline
- **NOT MP4 export** — no encoding
- **NOT real audio** — no TTS or audio tracks
- **NOT real subtitles** — mock text only
- **NOT shot switching** — elements appear sequentially but don't disappear/replace
- **NOT affecting other 4 styles** — they remain unchanged

---

## 11. Architecture

```
renderBreakingNewsStageEpisodeHtml(contract, st)
  ├── buildBreakingNewsShotTimeline(contract)  ← new, not used in output but documented
  ├── stageCss (enhanced with shot entrance animations)
  │    ├── shotFadeIn keyframe
  │    ├── shotCardIn keyframe
  │    ├── anchorEnter keyframe
  │    ├── mockProgressFill keyframe (~12s linear)
  │    └── per-layer animation-delay assignments
  ├── leadHtml / supportHtml / subtitleBarHtml / ... (unchanged)
  └── HTML assembly
       ├── stage-shot-label  ← new
       ├── stage-anchor-layer (opacity:0 + entrance animation)
       ├── stage-main-card (delayed entry)
       ├── stage-supporting + stage-support-card stagger
       ├── stage-subtitle-bar (delayed)
       ├── stage-closing-chip (delayed)
       ├── tl-rail / tl-track / tl-time (preserved)
       └── stage-progress-wrap + stage-progress-fill  ← new
```

---

## 12. Current Limitations

- Elements appear sequentially but never disappear — it's a reveal, not true shot cuts
- No JS means no pause/play/seek control
- Progress bar is purely visual, not tied to any playback state
- No audio synchronization
- Only `breaking_news_v1` has shot timeline; other 4 styles unchanged
- Supporting cards stagger is hardcoded (3 cards max)
