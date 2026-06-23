# PROJECT_SPEC

## 目标

把一条新闻 → 自动生成一段黑板风格的讲解动画视频 (`output.mp4`)，无需手动剪辑。

## 核心架构原则

1. **LLM 不输出坐标**：LLM 只产出结构化的 `semantic_ir`。
2. **semantic_ir 不含 x/y/w/h**：只描述新闻结构。
3. **layout.py 是坐标唯一来源**。
4. **renderer/template.html 只播 render_ir**：HTML 内不调用 LLM。
5. **export_video.py 只负责导出**。
6. **timeline 由 beats 驱动**：`pace.compute_timeline_from_beats` 唯一时间源。
7. **fetch_news 只产出 latest_news.json**：不解析为 semantic_ir，不接 pipeline。

## 数据流（完整）

```
sources.yaml ──▶ fetch_news ──▶ latest_news.json ──┐
                                                  │
                                     [Checkpoint 2: LLM]
                                                  │
                                                  ▼
                                           semantic_ir.json
                                                  │
                                                  ▼
                            layout.py + pace.compute_timeline_from_beats
                                                  │
                                                  ▼
                                            render_ir.json
                                                  │
                                                  ▼
                            render_html.py ── Jinja2 ──▶ animation.html
                                                              │
                                                              ▼
                            export_video.py (Playwright + FFmpeg)
                                                              │
                                                              ▼
                                                         output.mp4
```

## Checkpoint 1 — News Ingestion Layer

职责边界：
- **做**：读取 `config/sources.yaml`、解析 RSS、抓取 RSS summary、按需抽取文章正文、生成 `outputs/latest/latest_news.json`、稳定 id、不随机
- **不做**：调用 LLM、生成 semantic_ir、校验 semantic_ir、TTS、视频导出、修改 export_video.py

模块：
- `src/config_loader.py` — 读取 YAML 与 `.env`
- `src/fetch_news.py` — CLI 与 `fetch_latest_news(source_id=None, config_path=None)`
- `src/extract_content.py` — `extract_article_content(url, timeout=15)`，trafilatura → BeautifulSoup 兜底

错误处理（都需清晰报错，不吞）：
- `sources.yaml` 不存在
- 无 enabled source
- source url 为空 / 占位
- RSS 解析失败 / 无 item
- 网络失败
- 正文中空

## latest_news.json 数据契约

```json
{
  "id": "openai_news-ec03c415d785",
  "title": "...",
  "url": "...",
  "source_id": "openai_news",
  "source_name": "OpenAI News",
  "published_at": "Wed, 22 Jun 2026 10:00:00 +0000",
  "summary": "...",
  "content": "...",
  "content_source": "rss_summary",
  "fetched_at": "2026-06-23T12:34:56+00:00"
}
```

字段约束：
- `content` 必须非空
- `content_source ∈ {rss_summary, extracted_html, fallback_summary}`
- `id` 由 `sha1(source_id | url | title | published_at)` 前 12 位构成；相同输入 → 相同 id
- `fetched_at` 为 UTC ISO 8601（秒精度）
- 文件用 `ensure_ascii=False, indent=2` 写入

正文选择策略：
1. `len(summary) ≥ 300` → `rss_summary`
2. 否则 `extract_article_content(url)`，成功且 ≥ 300 → `extracted_html`
3. 否则 `fallback_summary`

## semantic_ir 契约（schema_version 0.1，未改动）

参考 Checkpoint 0.5；本轮不修改。

## V0.6 范围

包含：
- News Ingestion Layer
- `sources.yaml` / `llm.yaml` / `.env.example`
- `latest_news.json` 写入

不包含：
- LLM 生成 semantic_ir (Checkpoint 2)
- 运行时 schema 校验 (Checkpoint 3)
- TTS / 数字人 / 多主题 / Remotion

## 文件清单（V0.6 新增 / 修改）

| 文件 | 状态 | 职责 |
|------|------|------|
| `config/sources.yaml` | 新增 | RSS 源列表 |
| `config/llm.yaml` | 新增（占位） | LLM provider 配置（不调用） |
| `.env.example` | 新增 | 环境变量模板 |
| `src/config_loader.py` | 新增 | YAML / .env 加载 |
| `src/fetch_news.py` | 新增 | RSS → latest_news.json |
| `src/extract_content.py` | 新增 | 文章正文抽取 |
| `requirements.txt` | 更新 | + feedparser/requests/bs4/trafilatura |
| `examples/sample_news.json` | 更新 | 对齐 latest_news.json schema |
| `README.md` / `PROJECT_SPEC.md` / `BACKLOG.md` | 更新 | 文档同步 |

未修改：
- `src/pipeline.py` / `layout.py` / `pace.py` / `render_html.py` / `export_video.py`
- `schema/semantic_ir.schema.json`
- `renderer/template.html`
- `examples/sample.semantic.json`
