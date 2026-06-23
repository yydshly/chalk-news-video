# BACKLOG

按 Checkpoint 推进。每个 Checkpoint 完成后才能进入下一个。

## ✅ Checkpoint 0 — 项目骨架
## ✅ Checkpoint 0.5 — IR 契约校准
## ✅ Checkpoint 1 — News Ingestion（当前）

- [x] 新增 `config/sources.yaml`（带占位 URL，enabled 可控）
- [x] 新增 `config/llm.yaml`（**占位**，本轮不调用任何 LLM）
- [x] 新增 `.env.example`（只放空 key，不写 token）
- [x] 新增 `src/config_loader.py`（YAML + .env 加载）
- [x] 新增 `src/fetch_news.py`（`load_enabled_sources` + `fetch_latest_news` + CLI）
- [x] 新增 `src/extract_content.py`（trafilatura → BeautifulSoup 兜底）
- [x] `requirements.txt` 加 `feedparser requests beautifulsoup4 trafilatura`
- [x] `examples/sample_news.json` 对齐 latest_news.json schema
- [x] `README.md` / `PROJECT_SPEC.md` 同步更新
- [x] 错误路径：sources.yaml 缺失 / 无 enabled / URL 占位 / RSS 失败 / 内容空 → 清晰报错
- [x] id 用 sha1(source_id | url | title | published_at) 前 12 位；稳定
- [x] 未修改 `pipeline.py / layout.py / pace.py / render_html.py / export_video.py`
- [x] `python -m src.pipeline --use-sample` 仍可跑（演示视频链路）

不做（本轮显式排除）：
- 未实现 LLM 调用（属于 Checkpoint 2）
- 未实现 `generate_ir`（属于 Checkpoint 2）
- 未实现 `validate_ir`（属于 Checkpoint 3）
- 未实现 TTS / Remotion / 视频导出改动

注：MiniMax / Mimo provider 在 `config/llm.yaml` 仅占位；Checkpoint 2 才真正实现客户端与调用。

## Checkpoint 2 — LLM 生成 semantic_ir

- `src/llm.py` 抽象 provider（minimax / openai_compatible / mock）
- `src/prompt.py` 拼装 prompt
- `src/generate_ir.py` 编排 `latest_news.json` → LLM → `semantic_ir.json`
- 强制 LLM 只输出 semantic_ir；解析失败降级 mock
- API key 走 `.env` / `api_key_env`，不写进 yaml 或 README

## Checkpoint 3 — semantic_ir 运行时校验

- `src/validate_ir.py`（jsonschema + 自定义边/callout 指向校验）
- pipeline 入口前置校验
- 失败时给出可读错误

## Checkpoint 4 — TTS

- `src/tts.py`
- narration → wav → 与 animation 对齐
- 解决"拍子"和"人声"对齐问题

## Checkpoint 5 — 多布局

- timeline / comparison / list 等
- `structure_type` enum 扩展

## Checkpoint 6 — 多主题

- theme 系统：黑板 / 米黄 / 深蓝

## 不做（Out of Scope）

- Remotion
- 数字人
- 自动选题 / 多新闻合并
