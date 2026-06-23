# BACKLOG

按 Checkpoint 推进。每个 Checkpoint 完成后才能进入下一个。

## ✅ Checkpoint 0 — 项目骨架
## ✅ Checkpoint 0.5 — IR 契约校准
## ✅ Checkpoint 1 — News Ingestion
## ✅ Checkpoint 2 — LLM Provider + semantic_ir 生成
## ✅ Checkpoint 3 — Validation Layer + Repair Loop

- [x] `src/validate_ir.py`：`ValidationIssue` dataclass + `validate_semantic_ir()` + `assert_valid_semantic_ir()`
- [x] jsonschema A层：Draf7Validator，jsonschema 错误转换为 ValidationIssue
- [x] 自定义 B层规则全集：禁止坐标/旧字段、node/edge/callout id 唯一性、引用完整性、beats 覆盖率、narration 长度、causal_chain 连通性（含断链检测 `BROKEN_CAUSAL_CHAIN`）
- [x] `src/generate_ir.py` 新参数：`--validate` / `--repair` / `--repair-attempts` / `--save-invalid`
- [x] `prompts/repair_semantic_ir.md`
- [x] 4 个 invalid 样例：`bad_reveal` / `coord_field` / `duplicate_id` / `disconnected_chain`
- [x] `src/layout.py`：`continue` → `ValueError`（edge/callout 引用缺失）
- [x] `requirements.txt` +jsonschema
- [x] `README.md` / `PROJECT_SPEC.md` / `BACKLOG.md` 同步更新
- [x] `--mock --validate` 通过；4 个 invalid 样例全部 exit=1 并含对应错误 code
- [x] mock semantic_ir 继续生成 output.mp4 链路通
- [x] 未实现 TTS / Remotion / pipeline 自动编排
- [x] 未提交 .env / outputs/latest 生成物

不做（本轮显式排除）：
- 未把 validate_ir 接入 pipeline 默认流程（CP4）
- 未做 TTS（CP4）
- 未做 Remotion

## Checkpoint 3.1 — causal_chain 连通性校验修复

- [x] 修复 `BROKEN_CAUSAL_CHAIN` 漏报：原来多条不相连路径不会报错，现在会正确检测并报错
- [x] 新增 `examples/invalid.semantic.disconnected_chain.json`
- [x] README.md / PROJECT_SPEC.md / BACKLOG.md 更新

## Checkpoint 3.2 — 官方 LLM Provider 配置校准

- [x] config/llm.yaml：新增 5 个 official profiles（minimax_m3_openai / minimax_m27_highspeed_openai / minimax_m3_anthropic / mimo_v25_pro_openai / mimo_token_plan_v25_pro_openai）
- [x] openai_compatible_provider.py：支持 auth_type / api_key_header / max_tokens_param / extra_body 配置化
- [x] anthropic_messages_provider.py：支持 endpoint_path / api_key_header / extra_body；anthropic_version 非空才发送 header
- [x] .env.example：更新为官方 base_url / model 示例值
- [x] README.md / PROJECT_SPEC.md 更新：auth_type / max_tokens_param / extra_body / 官方 base_url 说明
- [x] 环境变量优先级：env > yaml 静态值
- [x] 未提交真实 API Key / .env / outputs/latest

## Checkpoint 4 — Auto Pipeline Orchestrator

- [x] `src/pipeline.py` 新增 `--auto / --mock / --news / --source / --profile / --repair / --no-export`
- [x] auto 链路：`fetch_news → generate_ir --validate → validate_ir → layout → render_html → export`
- [x] `generate_ir` 通过 subprocess 调用，避免循环 import
- [x] 阶段化错误标签：`[auto:fetch_news]` / `[auto:generate_ir]` / `[auto:validate_ir]` / `[auto:layout]` / `[auto:render_html]` / `[auto:export]`
- [x] `--mock` 使用 examples/sample_news.json + mock LLM，无需 API key
- [x] `--no-export` 跳过 video export
- [x] 原有 `--use-sample` / `--semantic-ir` 行为不变
- [x] README.md / PROJECT_SPEC.md / BACKLOG.md 更新
- [x] 未实现 TTS / Remotion / 前端 UI

不做（显式排除）：
- 未实现 TTS（CP6+）
- 未实现 Remotion / 数字人（CP6+）
- 未实现前端 UI（CP6+）
- 未实现多新闻选择 / 聚类

## Checkpoint 5 — 真实 RSS + 真实 MiniMax/MiMo 端到端验证

- 配置真实 RSS URL + 真实 MiniMax/MiMo key
- 完整链路跑通，检查输出视频质量

## Checkpoint 6+ — TTS / Dialogue / Remotion / UI

- TTS（Text-to-Speech）语音旁白
- Dialogue / 多角色对话
- Remotion 数字人
- 前端 UI（网页端配置和播放）
- `structure_type` 扩展：timeline / comparison / list
- theme 系统：黑板 / 米黄 / 深蓝

## 不做（Out of Scope）

- Remotion（CP6+）
- 数字人（CP6+）
- 自动选题 / 多新闻合并
