# CP53 Real Source Feed Snapshot MVP

## 目标

从可靠来源抓取/探测 RSS 或静态 HTML，生成 `source_snapshot_v1`，建立真实来源采集最小闭环。

## 当前已实现

### 功能

- **Source Feed Config** — 每个来源的配置（source_id、name、homepage_url、fetch_url、source_kind、trust_level、tags）
- **RSS Parser** — 支持 RSS 2.0 和 Atom 格式，提取 title/link/description/pubDate
- **HTML Static Parser** — 提取页面标题和同域链接
- **Safe URL Fetch** — 完整的 URL 安全校验（私有 IP、localhost、非法 scheme 拒绝）
- **Batch Snapshot** — 聚合多个来源，部分失败不影响整批
- **API Endpoint** — `GET /api/source-snapshot`
- **CLI Script** — `python scripts/snapshot_sources.py`

### 默认来源（8 个）

| Source ID | Name | Kind | Trust Level |
|-----------|------|------|------------|
| openai_blog | OpenAI Blog | rss | official |
| anthropic_news | Anthropic News | rss | official |
| google_ai_blog | Google AI Blog | rss | official |
| deepmind_blog | DeepMind Blog | rss | official |
| microsoft_ai_blog | Microsoft AI Blog | rss | official |
| meta_ai_blog | Meta AI Blog | rss | official |
| arxiv_csai | arXiv cs.AI | rss | research |
| huggingface_blog | Hugging Face Blog | rss | community |

### 安全策略

- 只允许 http/https
- 拒绝 localhost、127.0.0.0/8、10.0.0.0/8、172.16.0.0/12、192.168.0.0/16
- 拒绝 javascript:、file:、data:、ftp: 等非 HTTP scheme
- 8 秒超时
- 1 MB 最大响应
- 1 次 redirect，重新校验 redirect URL
- 固定 User-Agent：`chalk-news-video-source-snapshot/0.1`

## 当前不做什么

- ❌ 不做后台常驻爬虫
- ❌ 不做定时任务（Cron）
- ❌ 不做真实新闻 API 聚合（如 NewsAPI、Bing News）
- ❌ 不做 JS 动态渲染抓取
- ❌ 不做 LLM（无任何 LLM 调用）
- ❌ 不做 TTS
- ❌ 不自动生成视频
- ❌ 不自动加入草稿篮
- ❌ 不做 UI 候选审查（CP54）
- ❌ 不做 Remotion
- ❌ 不做自动发布

## 数据结构

### source_snapshot_v1

```json
{
  "schema": "source_snapshot_v1",
  "snapshot_id": "snapshot_20260625_openai_blog",
  "source_id": "openai_blog",
  "source_name": "OpenAI Blog",
  "source_url": "https://openai.com/blog",
  "fetch_url": "https://openai.com/news/rss.xml",
  "source_kind": "rss",
  "fetched_at": "2026-06-25T00:00:00Z",
  "status": "ok",
  "error": null,
  "items": [
    {
      "id": "abc123def456",
      "title": "Example title",
      "url": "https://openai.com/blog/example",
      "summary": "Short description",
      "published_at": "2026-06-25T00:00:00Z",
      "source_id": "openai_blog",
      "source_name": "OpenAI Blog",
      "source_kind": "rss",
      "tags": ["official", "ai"],
      "raw": {"source": "rss"}
    }
  ],
  "item_count": 1,
  "limit": 10
}
```

### source_snapshot_batch_v1

```json
{
  "schema": "source_snapshot_batch_v1",
  "batch_id": "batch_20260625T000000Z",
  "fetched_at": "2026-06-25T00:00:00Z",
  "source_count": 8,
  "item_count": 40,
  "snapshots": [...]
}
```

## API

### GET /api/source-snapshot

**参数**：
- `source_id`（可选）— 单个来源 ID，不填则返回全部
- `limit`（可选，默认 10，最大 20）— 每来源最大条目数

**返回**：
- 有 source_id → `{"ok": true, "snapshot": {...}}`
- 无 source_id → `{"ok": true, "batch": {...}}`
- 错误 → `{"ok": false, "error": "..."}`

## CLI

```bash
# 获取所有来源
python scripts/snapshot_sources.py --pretty

# 获取单个来源
python scripts/snapshot_sources.py --source openai_blog --limit 5

# 获取多个来源
python scripts/snapshot_sources.py --sources openai_blog anthropic_news --pretty
```

## 已知风险

| 风险 | 影响 | 缓解 |
|------|------|------|
| RSS 源不稳定（URL 变更） | 单来源失败 | batch 部分失败容错 |
| HTML 页面结构变化 | 链接提取不准 | 单页仅作补充，RSS 优先 |
| 403 / 429 | 来源不可达 | 单源失败不影响整批 |
| 静态 HTML 无 JS 渲染 | 部分 SPA 无法抓取 | 不承诺 JS 渲染，支持 RSS 则优先 RSS |
| arXiv 可能限流 | 抓取失败 | 可配置降级为 HTML fallback |

## 与 CP54 的关系

CP53 只生成 snapshot。
CP54 再做候选审查 UI，把 snapshot items 可视化，支持人工筛选后加入 URL 草稿篮。

## 文件变更

| 文件 | 变更 |
|------|------|
| src/source_snapshot.py | 新增 — 核心模块 |
| src/server.py | 新增 API endpoint |
| scripts/snapshot_sources.py | 新增 — CLI 工具 |
| scripts/test_cp53_source_snapshot.py | 新增 — 测试 |
| docs/CP53_REAL_SOURCE_FEED_SNAPSHOT.md | 新增 — 本文档 |
