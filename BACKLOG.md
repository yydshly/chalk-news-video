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

## Checkpoint 5.1 — Auto Pipeline 语义收紧

- [x] 清理上一轮遗留的 semantic_ir.json / .invalid.json / debug_*.txt
- [x] generate_ir 返回非 0 时直接退出，不使用 .invalid.json 继续
- [x] semantic_ir.invalid.json 明确为调试产物，pipeline 不使用
- [x] README / PROJECT_SPEC / BACKLOG / docs/CP5_REAL_E2E_VALIDATION.md 更新

## Checkpoint 6 — Narration Layer（TTS 单人口播）

- [x] `src/tts/`（base.py / mock_tts_provider.py / minimax_tts_provider.py / client.py / __init__.py）
- [x] `src/narration.py`（generate_narration / beat WAV 拼接 / narration_manifest.json）
- [x] `config/tts.yaml`（mock / minimax_speech profiles）
- [x] `src/export_video.py`（新增 audio_path 参数，ffmpeg mux 音频）
- [x] `src/pipeline.py`（新增 `--tts` / `--tts-profile` / `--audio-only`）
- [x] `.gitignore` 更新（忽略 audio/ / narration_manifest.json）
- [x] `.env.example` 更新（MINIMAX_TTS_* env vars）
- [x] README / PROJECT_SPEC / BACKLOG 更新
- [x] mock TTS 验收通过：`--tts --tts-profile mock` 生成带音频 output.mp4
- [x] 无 TTS 模式（`--auto --mock`）仍生成无声视频，不破坏旧流程

不做（显式排除）：
- 多角色 TTS（CP8+）
- Remotion / 数字人（CP9+）

## Checkpoint 6.1 — 音画同步

- [x] `src/narration_timing.py`（apply_narration_timing 函数）
- [x] `narration_manifest` 新增字段：speech_duration / tail_silence / total_duration / sample_rate
- [x] `narration.py` 追加 tail_silence 到 narration.wav
- [x] `narration.py` --output 参数实际生效
- [x] `mock_tts_provider` 返回 sample_rate
- [x] `pipeline.py` TTS 模式下校验 manifest 和音频文件存在，不存在则 fail
- [x] `pipeline.py` apply_narration_timing 在 render_html 之前执行
- [x] `pipeline.py` render_ir.json 在 render_html 之前保存
- [x] `export_video.py` 添加音频 mux 日志
- [x] README / PROJECT_SPEC / BACKLOG 更新
- [x] 验收通过：音频总时长 ≈ render_ir.total_duration ≈ output.mp4 时长

## Checkpoint 7 — 双人对话脚本

- [x] `prompts/news_to_semantic_ir.md` 新增 `speaker` 字段（host/expert）
- [x] `config/tts.yaml` 新增 `mock_host` 和 `mock_expert` profiles
- [x] `mock_tts_provider` 支持动态 voice 参数，不同 voice 用不同频率（host 440Hz，expert 330Hz）
- [x] `narration.py` 新增 `generate_dialogue()` 函数，生成 `dialogue_manifest.json`
- [x] `dialogue_manifest.json` 含 `host_profile`、`expert_profile`、`speakers`、`beats[].speaker`
- [x] `pipeline.py` 新增 `--dialogue`、`--host-profile`、`--expert-profile` 参数
- [x] `pipeline.py` 对话模式使用 `generate_dialogue` 而非 `generate_narration`
- [x] README / PROJECT_SPEC / BACKLOG 更新
- [ ] 验收通过：`--dialogue` 模式生成 dialogue.wav + dialogue_manifest.json
- [ ] 验收通过：render_ir.timeline 与 dialogue_manifest 时间一致
- [ ] 验收通过：最终 MP4 音频时长 ≈ dialogue_manifest.total_duration

## Checkpoint 8+ — Remotion / UI / 主题扩展

- Remotion 数字人
- 前端 UI（网页端配置和播放）
- `structure_type` 扩展：timeline / comparison / list
- theme 系统：黑板 / 米黄 / 深蓝

## 不做（Out of Scope）

- Remotion（CP9+）
- 数字人（CP9+）
- 自动选题 / 多新闻合并
