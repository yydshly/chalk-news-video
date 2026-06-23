# BACKLOG

按 Checkpoint 推进。每个 Checkpoint 完成后才能进入下一个。

## ✅ Checkpoint 0 — 项目骨架

- [x] 创建目录结构
- [x] `examples/sample.semantic.json`（causal_chain × 3 nodes，演示版）
- [x] `src/layout.py` 水平链布局
- [x] `src/pace.py` narration 节奏估算
- [x] `src/render_html.py` Jinja2 注入
- [x] `src/export_video.py` Playwright + FFmpeg
- [x] `src/pipeline.py --use-sample`
- [x] `renderer/template.html` 单文件 SVG 黑板动画

## ✅ Checkpoint 0.5 — IR 契约校准（当前）

把演示版 `semantic_ir` 升级为后续 fetch_news 和 LLM 可以稳定使用的正式契约。

- [x] `schema/semantic_ir.schema.json`：新增 `schema_version` / `meta` / `structure_type` / `beats`
- [x] `examples/sample.semantic.json`：改用 0.1 契约（3 nodes / 2 edges / 2 callouts / 8 beats）
- [x] `src/pace.py`：`compute_timeline_from_beats` 取代 `compute_timeline(nodes)` 作为唯一时间源
- [x] `src/layout.py`：按 `structure_type` 分发；edge 携带 `id`+`label`；callout 用 `on`；timeline 来自 beats
- [x] `renderer/template.html`：按 `timeline.reveal` 控显隐；已显示元素保持弱可见；title 从首个 title beat 起常显
- [x] `PROJECT_SPEC.md` / `README.md` 同步更新

不做：
- 仍未实现 fetch_news / LLM / validate_ir / TTS

## Checkpoint 1 — 真实新闻抓取

- `src/fetch_news.py`
- `config/sources.yaml` 列出 RSS / 站点
- 支持 mock 模式 / 真实 HTTP
- 产出原始新闻 JSON（不含 semantic_ir）

## Checkpoint 2 — LLM 生成 semantic_ir

- `src/llm.py` 抽象 OpenAI / Anthropic / mock
- `prompt.py` 拼装 prompt
- LLM 强制只输出 semantic_ir，禁止坐标
- 解析失败时降级到 mock

## Checkpoint 3 — semantic_ir 运行时校验

- `src/validate_ir.py` 使用 jsonschema
- pipeline 入口前置校验
- 校验失败给出可读错误（指出哪一个字段、哪一个 beat）

## Checkpoint 4 — TTS

- `src/tts.py`
- narration → wav → 与 animation 对齐
- 解决"拍子"和"人声"对齐问题

## Checkpoint 5 — 多布局

- timeline / comparison / list 等
- `structure_type` 扩展 enum

## Checkpoint 6 — 多主题

- theme 系统：黑板 / 米黄 / 深蓝

## 不做（Out of Scope）

- Remotion
- 数字人
- 自动选题 / 多新闻合并
