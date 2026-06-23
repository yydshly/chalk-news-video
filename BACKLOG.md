# BACKLOG

按 Checkpoint 推进。每个 Checkpoint 完成后才能进入下一个。

## ✅ Checkpoint 0 — 项目骨架
## ✅ Checkpoint 0.5 — IR 契约校准
## ✅ Checkpoint 1 — News Ingestion
## ✅ Checkpoint 2 — LLM Provider + semantic_ir 生成
## ✅ Checkpoint 3 — Validation Layer + Repair Loop（当前）

- [x] `src/validate_ir.py`：`ValidationIssue` dataclass + `validate_semantic_ir()` + `assert_valid_semantic_ir()`
- [x] jsonschema A层：Draf7Validator，jsonschema 错误转换为 ValidationIssue
- [x] 自定义 B层规则全集：禁止坐标/旧字段、node/edge/callout id 唯一性、引用完整性、beats 覆盖率、narration 长度、causal_chain 连通性
- [x] `src/generate_ir.py` 新参数：`--validate` / `--repair` / `--repair-attempts` / `--save-invalid`
- [x] `prompts/repair_semantic_ir.md`
- [x] 3 个 invalid 样例：`bad_reveal` / `coord_field` / `duplicate_id`
- [x] `src/layout.py`：`continue` → `ValueError`（edge/callout 引用缺失）
- [x] `requirements.txt` +jsonschema
- [x] `README.md` / `PROJECT_SPEC.md` / `BACKLOG.md` 同步更新
- [x] `--mock --validate` 通过；3 个 invalid 样例全部 exit=1 并含对应错误 code
- [x] mock semantic_ir 继续生成 output.mp4 链路通
- [x] 未实现 TTS / Remotion / pipeline 自动编排
- [x] 未提交 .env / outputs/latest 生成物

不做（本轮显式排除）：
- 未把 validate_ir 接入 pipeline 默认流程（CP4）
- 未做 TTS（CP4）
- 未做 Remotion

## Checkpoint 4 — 完整 pipeline 编排

- `python -m src.pipeline --auto` 串：`fetch_news → generate_ir --validate --repair → layout → render → export`
- TTS（如已就位）
- 错误处理：fetch 失败 / LLM 失败 / 校验失败 / 视频编码失败的明确提示

## Checkpoint 5 — 真实 RSS + 真实 LLM 端到端验证

- 配置真实 RSS URL
- 配置 MiniMax / Mimo 真实 key
- 完整链路跑通，检查输出视频质量

## Checkpoint 6+ — 多布局 / 多主题 / 多新闻

- `structure_type` 扩展：timeline / comparison / list
- theme 系统：黑板 / 米黄 / 深蓝

## 不做（Out of Scope）

- Remotion
- 数字人
- 自动选题 / 多新闻合并

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
