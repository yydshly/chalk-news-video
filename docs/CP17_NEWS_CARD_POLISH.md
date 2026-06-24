# CP17: News Card Visual Polish

## Overview

CP17 polishes the `news_card_v1` template from a "distinguishable theme" to a "news video main visual template" that users can understand at a glance.

## What Changed vs CP16 Baseline

| Aspect | CP16 (news_card_v1) | CP17 (news_card_v1) |
|--------|---------------------|---------------------|
| Header | None | NEWS badge + Source info |
| Main event card | Generic node card | Dedicated "发生了什么" card |
| Key point cards | Not present | 3 cards: 为什么重要/谁受影响/接下来怎么看 |
| Progress bar | None | Timeline progress bar at bottom |
| Animation | Basic fade | Staggered slide-up for cards |
| Color scheme | #1a1a2e background | #12121f darker background |

## Current Layout

```
+--------------------------------------------------+
| [NEWS]                                    Source  |
|                                                  |
|  +--------------------------------------------+  |
|  | 发生了什么                                   |  |
|  | [Main event title - up to 2 lines]         |  |
|  | [Description - 1 line]                     |  |
|  +--------------------------------------------+  |
|                                                  |
|  +------------+ +------------+ +------------+   |
|  | 为什么重要  | | 谁受影响    | | 接下来怎么看 |   |
|  | [Content]  | | [Content]  | | [Content]  |   |
|  +------------+ +------------+ +------------+   |
|                                                  |
|  [=========== Progress Bar ===============]     |
|  [Speaker] [Subtitle bar]                       |
+--------------------------------------------------+
```

## Suitable News Types

- Breaking news
- Company announcements
- Regulatory news
- Hot AI news
- Market events

## Visual Defects Still Present

1. **Source metadata not fully populated** - hotness_score/story_score not in render_ir.meta
2. **No strong transition animations** - just basic opacity
3. **9:16 portrait mode not supported**
4. **MP4 export quality not optimized for news card layout**
5. **Subtitle timing not precisely synced to speech**

## CP17.1 TODO

1. **Inject news metadata into render_ir**
   - Pass hotness_score, story_score, final_score from hot_ai_news
   - Add to render_ir.meta without breaking schema

2. **Stronger transition animations**
   - Card flip/slide transitions between beats
   - Progress indicator animation

3. **9:16 vertical format support**
   - Different layout for mobile/vertical video
   - Adapt card sizes for vertical canvas

4. **MP4 export quality**
   - Higher bitrate for news card template
   - Optimize for social media sharing

5. **Subtitle-speech synchronization**
   - Use Whisper timestamps for precise subtitle display
   - Karaoke-style highlighting

## Files Changed

- `config/themes.yaml` - Enhanced news_card_v1 with layout tokens
- `renderer/template.html` - News card specific SVG elements and animations

## Testing

```bash
python -m src.server --host 127.0.0.1 --port 8777
```

Request:
```bash
curl -X POST http://127.0.0.1:8777/api/jobs \
-H "Content-Type: application/json" \
-d '{
  "mode": "hot_ai",
  "theme": "news_card_v1",
  "dialogue": true,
  "llm_provider": "minimax_m3_openai",
  "tts_provider": "mock_dialogue",
  "mock": false,
  "repair": true,
  "repair_attempts": 2,
  "no_export": true,
  "target_duration_sec": 60,
  "max_turns": 14
}'
```

## Acceptance Criteria

- [x] Job succeeded
- [x] animation.html exists
- [x] Web Studio auto-preview works
- [x] News title visible and not overflowed
- [x] At least 3 key point cards visible
- [x] Subtitle doesn't block main content
- [x] Progress bar shows timeline
- [x] dialogue_script turns <= 14
- [x] total_duration <= 65s
- [x] No API key / voice_id leakage
