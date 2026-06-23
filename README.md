# chalk-news-video

把一条新闻自动生成黑板风格的讲解动画视频 (output.mp4)。

## 当前 Checkpoint

**Checkpoint 1 — 自动拉取一条新闻**

`config/sources.yaml` 列出新闻源；`python -m src.fetch_news` 拉取最新一条并写入 `outputs/latest/latest_news.json`。
LLM、`generate_ir`、`validate_ir`、TTS、视频导出**都还没有接入**——它们分别属于 Checkpoint 2 / 3 / 4 / 0.5。

`python -m src.pipeline --use-sample` 仍可用，跑的是 Checkpoint 0.5 的演示视频链路。

## 项目定位

V0.6: News Ingestion Layer 已就位，但只产出 `latest_news.json`；不直接生成视频。

不包含（后续 Checkpoint）：
- LLM 生成 semantic_ir (Checkpoint 2)
- semantic_ir schema 运行时校验 (Checkpoint 3)
- TTS / 数字人 / 多主题 / Remotion

## 架构

```
sources.yaml ──▶ fetch_news ──▶ latest_news.json (Checkpoint 1)
                                     │
                                     ▼
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
                  export_video.py ── Playwright + FFmpeg ──▶ output.mp4
```

唯一允许产出坐标的地方：`layout.py`。
唯一允许产生时间的地方：`pace.compute_timeline_from_beats`。

## 安装

```bash
cd chalk-news-video
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

还需要 FFmpeg 加入 PATH：
- Windows: `choco install ffmpeg`
- macOS:   `brew install ffmpeg`
- Linux:   `sudo apt install ffmpeg`

## 配置 sources.yaml

复制下面的内容到 `config/sources.yaml`，**把 `url` 改成真实可用的 RSS feed 链接**，再把 `enabled: true`：

```yaml
sources:
  - id: openai_news
    name: OpenAI News
    type: rss
    url: "https://example.com/openai.rss"     # 替换成真链接
    enabled: true
    language: en
    category: ai_official
    content_strategy: summary_then_extract

  - id: anthropic_news
    name: Anthropic News
    type: rss
    url: "https://example.com/anthropic.rss"  # 替换成真链接
    enabled: false                            # 暂时禁用
    language: en
    category: ai_official
    content_strategy: summary_then_extract
```

如果 `url` 留空或仍是 `待填 RSS URL` 之类占位符，`fetch_news` 会**清晰报错**而不是崩溃。

> 不要把任何真实 API key 或私密 RSS token 写进 sources.yaml 或本 README。

## 配置 llm.yaml（占位）

`config/llm.yaml` 只是 Checkpoint 2 的占位。**本轮不调用任何 LLM**。真实 key 通过环境变量读取：

```bash
cp .env.example .env
# 编辑 .env，填入 MINIMAX_API_KEY / MIMO_API_KEY
```

## 运行 fetch_news

```bash
python -m src.fetch_news
# 可选：python -m src.fetch_news --source openai_news
# 可选：python -m src.fetch_news --config path/to/sources.yaml
# 可选：python -m src.fetch_news --output path/to/out.json
```

未配置时输出：

```
Error: source 'openai_news' has an empty or placeholder URL.
Edit config/sources.yaml and set a real RSS URL before running fetch_news.
```

配置正确时输出：

```
[fetch_news] wrote D:\...\outputs\latest\latest_news.json
(id=openai_news-ec03c415d785, content_source=rss_summary, content_chars=482)
```

## latest_news.json 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | `source_id` + sha1(source_id\|url\|title\|published_at) 前 12 位；同一新闻重复拉取 id 一致 |
| `title` | string | 新闻标题 |
| `url` | string | 文章链接 |
| `source_id` | string | `sources.yaml` 中的 id |
| `source_name` | string | 来源名称 |
| `published_at` | string \| null | RSS 中的发布时间（raw 字符串） |
| `summary` | string | RSS summary |
| `content` | string | 选定的正文（见下） |
| `content_source` | string | `rss_summary` / `extracted_html` / `fallback_summary` |
| `fetched_at` | string | UTC ISO 8601 时间戳 |

正文选择策略：
1. `summary` 长度 ≥ 300 字符 → `content = summary`，`content_source = rss_summary`
2. 否则尝试 `extract_article_content(url)`（trafilatura → BeautifulSoup 兜底）
3. 抽到正文 ≥ 300 字符 → `content_source = extracted_html`
4. 仍不足 → `content = summary`，`content_source = fallback_summary`

## 运行 pipeline（演示版，仍可用）

```bash
python -m src.pipeline --use-sample
```

产物：

```
outputs/latest/render_ir.json
outputs/latest/animation.html
outputs/latest/output.mp4
```

注：本轮 fetch_news **不**写入 render_ir/animation.html/output.mp4。
要把 latest_news.json 接入到 pipeline，等 Checkpoint 2 的 LLM。

## 不要提交真实 key

- 真实 API key 放在 `.env`（不要提交）
- RSS feed token 同样放在 `.env` 或外部 secrets，不要写进 yaml 或 README
- `.env.example` 留空，作为模板

## 当前 Checkpoint

详见 [PROJECT_SPEC.md](PROJECT_SPEC.md) 和 [BACKLOG.md](BACKLOG.md)。
