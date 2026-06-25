# CP44: Reliable Source Registry / URL Input MVP

## Goal
Move from sample/text-only to a reliable source workflow. Establish a curated source registry and a URL input path that generates standard news_items and episode contracts without any network requests.

## Reliable Source Registry

**File:** `src/reliable_sources.py`

A hard-coded list of 7 trusted AI news sources:

| ID | Name | Domain | Trust Level |
|---|---|---|---|
| openai_blog | OpenAI Blog | openai.com | official |
| anthropic_news | Anthropic News | anthropic.com | official |
| google_ai_blog | Google AI Blog | blog.google | official |
| deepmind_blog | Google DeepMind Blog | deepmind.google | official |
| meta_ai_blog | Meta AI Blog | ai.meta.com | official |
| microsoft_ai_blog | Microsoft AI Blog | blogs.microsoft.com | official |
| arxiv | arXiv | arxiv.org | research |

Functions:
- `list_reliable_sources()` — returns all sources
- `get_reliable_source(id)` — returns a single source by id
- `infer_source_from_url(url)` — infers source from URL domain
- `validate_source_url(url)` — validates URL scheme (http/https only, no javascript:/file:)

## URL Input MVP

**No crawler. No network requests. No auto article extraction.**

User provides:
- Source (optional — select from registry or leave as "auto-detect")
- URL (provenance metadata only — not fetched)
- News title (required)
- Summary (optional — derived from title if empty)

System produces:
- A standard `news_item` with `source_type=url_input`
- Source metadata from registry: `matched_source_id`, `trust_level`, `default_tags`
- Tags merged from registry defaults + user input + rule-based extraction
- A `final_score` with a small bonus for official/research sources
- An `episode_template_v1` contract via the existing pipeline

## API

### GET /api/reliable-sources
Returns the source registry.

```json
{
  "ok": true,
  "items": [...],
  "count": 7
}
```

### POST /api/episode/source-contract

New `source_type: url_input`:

```json
{
  "source_type": "url_input",
  "url": "https://openai.com/blog/example",
  "news_title": "OpenAI 发布新功能",
  "news_summary": "这是官方公告摘要。",
  "source_id": "openai_blog",
  "tags": ["api", "developer"],
  "limit": 1,
  "template_id": "breaking_news_v1",
  "episode_title": "官方来源快讯",
  "episode_subtitle": "URL 输入生成"
}
```

**Payload field naming (CP44):**
- `news_title` / `news_summary` — news item fields (avoids conflict with `title`/`subtitle` which are episode fields)
- `episode_title` / `episode_subtitle` — episode fields (backward-compatible: `title`/`subtitle` still work)
- `source_id` — registry source id (optional; auto-inferred from URL if omitted)

Validation:
- `url` is required, must be http/https
- `news_title` is required
- `template_id` is clamped to `breaking_news_v1`
- `limit` is clamped to 1–5

## Frontend

Source contract panel now has a third section below sample/inline:

**From reliable URL generation:**
- Select dropdown — lists all registry sources (loaded from `GET /api/reliable-sources`)
- URL input — required
- News title input — required
- Summary textarea — optional
- "From URL generate episode" button

Inspector enhancements:
- Each news item shows **trust badge** (官方/研究/手动/未知) with color coding
- Each news item shows **source link** (opens in new tab)
- Lead item still highlighted in green

## Not Done
- No auto article/body extraction from URL
- No crawler
- No real news API
- No real LLM
- No real TTS
- No Remotion
- No changes to MP4 export main logic
- No outputs generated

## Tests
```bash
python scripts/test_cp44_url_source_pipeline.py
```

All 25 tests cover:
- Reliable source registry functions
- URL validation (empty, javascript:, file://, valid https)
- `normalize_url_item()` output schema, source inference, tag merging, error cases
- `GET /api/reliable-sources` response
- `POST /api/episode/source-contract` url_input success and error cases
- Contract format, security (no secrets), HTML renderability
