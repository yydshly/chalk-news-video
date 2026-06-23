# BACKLOG

按 Checkpoint 推进。每个 Checkpoint 完成后才能进入下一个。

## ✅ Checkpoint 0 — 项目骨架
## ✅ Checkpoint 0.5 — IR 契约校准
## ✅ Checkpoint 1 — News Ingestion
## ✅ Checkpoint 2 — LLM Provider + semantic_ir 生成（当前）

- [x] `config/llm.yaml` 改为 profile 结构（default + 2 真实 + mock）
- [x] `.env.example` 增加 6 个环境变量
- [x] `src/llm/{base,client,openai_compatible_provider,anthropic_messages_provider,json_utils}.py`
- [x] `prompts/news_to_semantic_ir.md` 写入完整契约 + 禁止项
- [x] `src/generate_ir.py` CLI：`--news --output --prompt --config --profile --dry-run --mock`
- [x] 最低限度校验：dict + 必填 key + 无坐标字段
- [x] 调试产物：`debug_llm_prompt.txt` / `debug_llm_response.txt`
- [x] mock → semantic_ir → pipeline → output.mp4 链路验证通过
- [x] 未修改 `pipeline.py / layout.py / pace.py / render_html.py / export_video.py / fetch_news.py / utils.py`
- [x] 未把 generate_ir 接入 pipeline 默认流程
- [x] 未提交任何真实 API key 或真实 base_url

不做（本轮显式排除）：
- 未做 jsonschema 完整校验（Checkpoint 3）
- 未做 repair loop / 自动重试（Checkpoint 3）
- 未做 TTS（Checkpoint 4）
- 未做 Remotion

注：MiniMax provider 已在 `src/llm/anthropic_messages_provider.py` 实现客户端模式（Anthropic Messages 风格）；真实 base_url 由用户本地 `.env` 注入。

## Checkpoint 3 — validate_ir + repair loop

- `src/validate_ir.py`：jsonschema + 自定义校验（`from`/`to`/`on` 必须指向存在的 id；`reveal` 必须在 node/edge/callout id 集合或 "title"）
- `repair loop`：校验失败时把错误塞回 LLM 重生成，限定 N 次
- pipeline 入口前置校验

## Checkpoint 4 — 完整 pipeline 编排

- 把 `fetch_news → generate_ir → validate_ir → layout → render → export` 串成一条 `python -m src.pipeline --auto`
- TTS（如已就位）
- 错误处理：fetch 失败 / LLM 失败 / 校验失败 / 视频编码失败的明确提示

## Checkpoint 5+ — 多布局 / 多主题 / 多新闻

- `structure_type` 扩展：timeline / comparison / list
- theme 系统：黑板 / 米黄 / 深蓝

## 不做（Out of Scope）

- Remotion
- 数字人
- 自动选题 / 多新闻合并
