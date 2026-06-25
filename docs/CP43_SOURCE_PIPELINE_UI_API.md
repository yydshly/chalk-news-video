# CP43: Source Pipeline UI/API

## Goal
Expose CP42 pipeline to the product through a new API endpoint and a small frontend panel.

## API
`POST /api/episode/source-contract`

### Input
```json
{
  "source_type": "sample_pack | inline_text | manual_items",
  "limit": 4,
  "template_id": "breaking_news_v1",
  "title": "...",
  "subtitle": "..."
}
```

### Output
```json
{
  "ok": true,
  "source_type": "sample_pack",
  "news_items": [...],
  "episode_items": [...],
  "contract": { "schema_version": "episode_template_v1", ... },
  "contract_schema_version": "episode_template_v1",
  "template_id": "breaking_news_v1"
}
```

## Supported Source Types
- `sample_pack` — built-in mock news pack (5 items)
- `inline_text` — user-pasted raw news text (max 20,000 chars)
- `manual_items` — structured news item list (max 10 items)

## Security Restrictions
- `template_id` is clamped to `breaking_news_v1`
- `limit` is clamped to 1–5
- `inline_text` is limited to 20,000 characters
- `manual_items` is limited to 10 items
- API keys / voice IDs in contract are rejected
- No outputs written, no MP4 export triggered
- No real LLM, no real TTS, no web crawler

## Frontend
Source contract panel above the episode planner in the input panel:
- "使用样例新闻包生成一期栏目" button → `sample_pack`
- Textarea + "从粘贴文本生成栏目" button → `inline_text`

On success, the contract is rendered in the preview iframe and stored as `latestEpisodeTemplateContract`, making it available for MP4 export.

## Export Behavior
`latestEpisodeTemplateContract` is shared between the episode planner and the source contract panel. Export MP4 uses it if present. Priority: episode planner contract > latest source contract.

## Not Done
- No crawler, no real LLM, no real TTS, no Remotion
- No changes to MP4 export main logic
- No outputs generated

## Tests
```bash
python scripts/test_episode_source_contract_api.py
```
