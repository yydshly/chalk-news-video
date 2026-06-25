# CP42: News Source to Episode Contract Pipeline

## 1. Problem

The system already had `episode_template_v1` → HTML preview → 9:16 stage → MP4 export → audio mux → history management. But the upstream pipeline — from raw news input to a standardized episode contract — was ad-hoc and lived entirely in the browser JavaScript.

## 2. Goal

Establish a local, controllable, testable pipeline:

```
input sources → normalized news_items → selected episode items → episode_template_v1 contract
```

The output contract must be directly consumable by the existing `render_episode_html` and `episode_export` layers without any new API endpoints.

## 3. Source Types

Three input modes are supported, all local/mock:

| Source type | Description |
|---|---|
| `inline_text` | Raw text pasted by the user — parsed by rule-based heuristics |
| `manual_items` | Pre-structured dict list with known fields |
| `sample_pack` | Built-in 5-item mock AI news pack |

No real web crawler, no real news API.

## 4. News Item Schema

```python
{
    "id": "news_<sha12hex>",      # stable hash-based ID
    "title": "...",                # max 80 chars (truncated)
    "summary": "...",              # up to 180 chars, rule-derived or provided
    "source": "Sample",            # source name
    "url": "",                    # optional URL
    "published_at": None,
    "final_score": 8.5,          # 0–10, rule-based keyword scoring
    "points": 200,
    "comments": 15,
    "tags": ["openai", "model"], # auto-extracted, max 8
    "source_type": "inline_text | manual_items | sample_pack",
}
```

## 5. Scoring Rules

Rule-based (no LLM). Keywords add weighted points:

| Pattern | Weight |
|---|---|
| openai | +1.5 |
| anthropic | +1.5 |
| google/deepmind/gemini | +1.0 |
| model/llm/gpt/claude | +1.2 |
| benchmark/score | +0.5 |
| launch/release/announce | +1.0 |
| regulation/EU | +0.7 |
| security/outage | +0.8 |
| research/arxiv/paper | +0.6 |
| Longer summary (>100 chars) | +0.3 |
| Numeric data (%, $) | +0.4 each |

Base score: 5.0. Clamped to [0, 10].

## 6. Episode Item Selection

`build_episode_items_from_news(items, limit=4)`:
1. Filter out items with empty title
2. Sort by `final_score` desc, then `points` desc
3. Cap at `min(limit, 5)`
4. First item → `role: "lead"`, rest → `role: "supporting"`

## 7. Contract Output

`build_episode_contract_from_news_items()` produces `episode_template_v1`:

```python
{
    "schema_version": "episode_template_v1",
    "template_id": "breaking_news_v1",
    "episode": {
        "title": "今日 AI 前沿速览",
        "subtitle": "多条热门 AI 新闻合集",
        "theme_id": "breaking_news_v1",
        "theme_name": "快讯大屏风",
        "estimated_duration_sec": 128,
        "news_count": 3,
        "lead_count": 1,
    },
    "timeline": {
        "markers": [
            {"type": "opening", "timecode": "00:00", ...},
            {"type": "news_segment", "timecode": "00:12", ...},
            {"type": "transition", "timecode": "00:44", ...},
            {"type": "news_segment", "timecode": "00:48", ...},
            ...
            {"type": "closing", "timecode": "02:08", ...},
        ]
    },
    "sections": {
        "opening": {...},
        "news_cards": [...],   # one per selected news item
        "transitions": [...],
        "closing": {...},
    },
    "constraints": {
        "no_external_assets": True,
        "no_script": True,
        "no_real_render": True,
        "no_audio": True,
        "no_mp4": False,   # exportable
    }
}
```

Compatible with:
- `render_episode_html.render_episode_stage_html()` (breaking_news_v1)
- `episode_export.start_episode_export_background()`

## 8. API / Function Summary

```python
normalize_inline_text(text, *, source="Manual", url=None) -> dict
normalize_manual_items(items: list[dict]) -> list[dict]
load_sample_news_pack() -> list[dict]
score_news_item(item: dict) -> float  # 0–10
build_episode_items_from_news(news_items, *, limit=4) -> list[dict]
build_episode_contract_from_news_items(news_items, *, template_id=..., title=..., subtitle=...) -> dict
build_contract_from_inline_text(text, ...) -> dict  # single-call shortcut
build_contract_from_sample_pack(...) -> dict           # single-call shortcut
contract_has_secrets(contract: dict) -> bool
```

## 9. Test Coverage

Run: `python scripts/test_news_source_to_episode_contract.py`

20 test cases covering:
1. `normalize_inline_text` basic conversion
2. Title truncation at 80 chars
3. Empty text raises `ValueError`
4. `normalize_manual_items` basic conversion
5. Missing title raises error
6. `load_sample_news_pack` returns ≥3 items
7. `score_news_item` returns 0–10 range
8. Score is deterministic
9. Items sorted by score, first is lead
10. `limit` and hard cap (5) respected
11. Contract `schema_version` = `episode_template_v1`
12. Default `template_id` = `breaking_news_v1`
13. `news_cards` count matches input items
14. Timeline markers non-empty with correct types
15. `constraints` all present, `no_mp4` = `False`
16. No API key / voice_id leakage
17. Contract renders valid HTML via `render_episode_html`
18. `build_contract_from_inline_text` shortcut works
19. `build_contract_from_sample_pack` shortcut works
20. `estimated_duration_sec` matches formula sum

## 10. What CP42 Does Not Do

- No real news crawler
- No real news API
- No real LLM
- No real TTS
- No new backend API endpoints
- No changes to MP4 export logic
- No changes to `episode_export.py`
- No changes to `render_episode_html.py`
- No Remotion integration
- No files written to `outputs/`
