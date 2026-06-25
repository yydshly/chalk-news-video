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
`latestEpisodeTemplateContract` is shared between the episode planner and the source contract panel. Both paths write to this same variable. The most recently generated preview/contract is the export source — clicking "预览合集画面" in the Episode Planner overwrites the source contract, and vice versa.

## CP43.1: Source Contract Result Inspector
After a successful source contract generation, an inspector panel appears below the status line showing:
- **入选栏目新闻** — the `episode_items` selected for the episode, with role badge (主线/补充), final_score, source, points, comments, and tags; lead item is highlighted in green
- **原始新闻项** — all `news_items` from the source pipeline, with score, source, and tags
- **Summary line** — source_type, news_items count, episode_items count, schema version, episode title

The inspector provides an **"应用到当前合集"** button that:
1. Maps `latestSourceEpisodeItems` into `episodeItemList` (the Episode Planner's internal list)
2. Resets derived planner outputs (`latestEpisodePlan`, `latestEpisodeScript`, `latestEpisodeAudioManifest`, `latestEpisodeRenderIr`)
3. Calls `renderEpisodePlanner()` to refresh the Episode Planner UI
4. Displays a success message telling the user to continue with the left-side "规划 / 预览 / 导出" buttons

This bridges the source pipeline output to the existing Episode Planner flow without disrupting the planner's own generation path.

## Not Done
- No crawler, no real LLM, no real TTS, no Remotion
- No changes to MP4 export main logic
- No outputs generated

## Tests
```bash
python scripts/test_episode_source_contract_api.py
```
