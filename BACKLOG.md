# BACKLOG

按 Checkpoint 推进。每个 Checkpoint 完成后才能进入下一个。

## ✅ Checkpoint 0 — 项目骨架（当前）

让手写 `sample.semantic.json` 可以跑通：
```
semantic_ir → layout → render_ir → animation.html → output.mp4
```

任务：
- [x] 创建目录结构
- [x] `examples/sample.semantic.json` (causal_chain × 3 nodes)
- [x] `src/layout.py` 水平链布局
- [x] `src/pace.py` 中文 narration 节奏估算
- [x] `src/render_html.py` Jinja2 注入
- [x] `src/export_video.py` Playwright + FFmpeg
- [x] `src/pipeline.py --use-sample`
- [x] `renderer/template.html` 单文件 SVG 黑板动画
- [x] 画布 1280×720 / 30fps / 黑板底 / 底部字幕

## Checkpoint 1 — 真实新闻抓取

- `src/fetch_news.py`
- `config/sources.yaml` 列出 RSS / 站点
- 支持 mock 模式 / 真实 HTTP

## Checkpoint 2 — LLM 生成 semantic_ir

- `src/llm.py` 抽象 OpenAI / Anthropic / mock
- `prompt.py` 拼装 prompt
- LLM 强制只输出 semantic_ir，禁止坐标

## Checkpoint 3 — semantic_ir 校验

- `schema/semantic_ir.schema.json`
- `src/validate_ir.py` 使用 jsonschema

## Checkpoint 4 — TTS

- `src/tts.py`
- narration → wav → 与 animation 对齐

## Checkpoint 5 — 多布局

- timeline / comparison / list 等

## Checkpoint 6 — 多主题

- theme 系统：黑板 / 米黄 / 深蓝

## 不做（Out of Scope）

- Remotion
- 数字人
- 自动选题 / 多新闻合并
