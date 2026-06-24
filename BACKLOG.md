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
- [x] `narration.py` 新增 `generate_dialogue()` 函数（legacy 路径）
- [x] `dialogue_manifest.json` 含 `host_profile`、`expert_profile`、`speakers`、`beats[].speaker`
- [x] `pipeline.py` 新增 `--dialogue`/`--host-profile`/`--expert-profile` 参数
- [x] README / PROJECT_SPEC / BACKLOG 更新

## Checkpoint 7.1 — Dialogue Script 契约层

- [x] `schema/dialogue_script.schema.json`（新增）
- [x] `prompts/semantic_ir_to_dialogue.md`（新增）
- [x] `src/validate_dialogue.py` + `validate_dialogue_script()`（新增）
- [x] `src/generate_dialogue.py`（新增）
- [x] `examples/sample.dialogue.json`（新增）
- [x] `examples/invalid.dialogue.bad_speaker.json`（新增）
- [x] `examples/invalid.dialogue.unknown_beat.json`（新增）
- [x] `narration.py` 新增 `generate_dialogue_audio()`，基于 dialogue_script.turns 生成音频
- [x] `narration.py` CLI 新增 `--dialogue-script` 参数
- [x] `narration_timing.py` 支持 turns 聚合（按 beat_id 分组）
- [x] `pipeline.py` dialogue 模式自动生成 dialogue_script.json
- [x] `pipeline.py` 新增 `--dialogue-legacy` 保留 CP7 兼容路径
- [x] README / PROJECT_SPEC / BACKLOG 更新
- [x] 验收通过：generate_dialogue --mock --validate 生成 dialogue_script.json
- [x] 验收通过：validate_dialogue 对无效输入报错
- [x] 验收通过：dialogue_manifest.turns 生成并同步 render_ir.timeline

## Checkpoint 7.2 — Dialogue Script 校验加固

- [x] `schema/dialogue_script.schema.json` 加固：`source_semantic_ir` 必含 title/schema_version，`style` 必含 format/tone/language/speakers，`speakers` uniqueItems: true
- [x] `src/validate_dialogue.py` 新增校验规则：
  - REVEAL_MISMATCH：turn.reveal 与 semantic_ir beat reveal 对齐
  - MISSING_HOST_TURN：至少一个 host turn
  - MISSING_EXPERT_TURN：至少一个 expert turn
  - UNKNOWN_STYLE_SPEAKER：turn.speaker 在 style.speakers 中定义
  - DUPLICATE_STYLE_SPEAKER：style.speakers id 不重复
  - MISSING_STYLE_SPEAKERS：style.speakers 不为空
- [x] `examples/invalid.dialogue.reveal_mismatch.json`（新增）
- [x] `examples/invalid.dialogue.missing_expert.json`（新增）
- [x] `examples/invalid.dialogue.missing_style_speakers.json`（新增）
- [x] README / PROJECT_SPEC / BACKLOG 更新
- [x] 验收通过：validate_dialogue 对 REVEAL_MISMATCH / MISSING_EXPERT_TURN 等报错
- [x] auto dialogue pipeline 回归测试通过
- [x] 单人口播回归测试通过
- [x] 无声回归测试通过

## Checkpoint 8 — 真实 LLM dialogue 验证 + 多角色 TTS mapping

- [x] `src/generate_dialogue.py` 新增 `--save-invalid` / `--no-save-invalid` / `--repair` / `--repair-attempts` / `--dry-run`
- [x] `src/generate_dialogue.py` 新增 debug 输出：`debug_dialogue_prompt.txt` / `debug_dialogue_response.txt` / `debug_dialogue_validation_issues.json`
- [x] `prompts/repair_dialogue_script.md`（新增）
- [x] `config/tts.yaml` 新增 `dialogue_profiles` 段：mock_dialogue / minimax_dialogue
- [x] `src/narration.py` 新增 `--dialogue-profile` 参数和 `speaker_profiles` 字段
- [x] `src/narration.py` `generate_dialogue_audio()` 支持 `dialogue_profile` + `speaker_profiles` 参数
- [x] `src/pipeline.py` dialogue 模式支持 `--dialogue-profile`
- [x] `src/pipeline.py` 非 mock 模式默认启用 `--repair`
- [x] `dialogue_manifest.json` 新增 `dialogue_profile` 和 `speaker_profiles` 字段
- [x] `docs/CP8_REAL_DIALOGUE_VALIDATION.md`（新增）
- [x] README / PROJECT_SPEC / BACKLOG 更新
- [x] mock dialogue 回归测试通过
- [x] auto mock + dialogue --dialogue-profile 回归测试通过
- [x] 单人口播回归测试通过
- [x] 无声回归测试通过

## Checkpoint 8.1 — dialogue_profile voice mapping 修复

- [x] `src/narration.py` 新增 `_resolve_speaker_voice()` helper，正确解析 voice/voice_env
- [x] `generate_dialogue_audio()` 每个 turn 调用 `provider.synthesize(voice=resolved_voice)`
- [x] manifest.turns 记录 `voice` 字段（mock：host/expert；env-based：只记录 voice_env 不记真实值）
- [x] manifest.speaker_profiles 对 env-based voice 不记录真实 voice_id
- [x] minimax_dialogue 缺配置时清晰报错（exit 非 0）
- [x] mock_dialogue voice mapping 验收通过（host→440Hz, expert→330Hz）
- [x] 真实 LLM dialogue 生成成功（MiniMax-M3, 14 turns, host/expert 各半）
- [x] docs/CP8_REAL_DIALOGUE_VALIDATION.md 更新

## Checkpoint 9 — Dialogue Visual Layer

- [x] `src/dialogue_visual.py`（新增 `apply_dialogue_visual_cues` 函数）
- [x] `src/pipeline.py`（CP9：dialogue visual cues 调用）
- [x] `renderer/template.html`（CP9：speaker panels + dialogue overlay + turn subtitle）
- [x] `render_ir.dialogue` 字段：enabled/style/speakers/turns
- [x] `render_ir.dialogue.turns` 不含 audio_path、voice、voice_id
- [x] speakers 名称从 dialogue_script.style.speakers 读取，无则用默认值
- [x] 单人口播回归：无 dialogue.enabled=true
- [x] 无声模式回归：无 dialogue.enabled=true
- [x] auto mock + dialogue --dialogue-profile 完整导出通过
- [x] README.md / PROJECT_SPEC.md / BACKLOG.md 更新

## Checkpoint 9.1 — Dialogue Visual Hardening

- [x] `src/dialogue_visual._normalize_style_speakers()`：正确处理 list 格式 `style.speakers`
- [x] `render_ir.dialogue.speakers.*.panel`：新增 panel 布局字段（x/y/w/h），外置到 render_ir
- [x] `renderer/template.html`：JS 初始化时从 `DIALOGUE.speakers.*.panel` 读取位置，不再硬编码
- [x] `examples/sample.dialogue.custom_speakers.json`：自定义 speaker 测试 fixture（提问者/分析员）
- [x] 未知 speaker 在 turn 中.warn 但 fallback 为 host 视觉
- [x] speaker metadata 读取测试通过（custom/standard/default）
- [x] README.md / PROJECT_SPEC.md / BACKLOG.md 更新

## Checkpoint 10 — Theme System V1

- [x] `config/themes.yaml`（新增：chalkboard / podcast / research_desk / notebook）
- [x] `src/theme.py`（新增 `load_themes` / `resolve_theme` / `apply_theme`）
- [x] `src/pipeline.py`（新增 `--theme` 参数，默认 chalkboard）
- [x] `renderer/template.html`（JS 读取 `RENDER_IR.theme` 覆盖所有颜色/填充/边框）
- [x] `render_ir.theme` 包含完整视觉 token（background/text/node/edge/callout/dialogue）
- [x] 4 个主题均可通过 `--theme` 切换
- [x] invalid theme → ValueError，pipeline exit 非 0
- [x] 单人口播/无声模式均可使用 `--theme`
- [x] 非 dialogue 模式 speaker panels 不出现
- [x] README.md / PROJECT_SPEC.md / BACKLOG.md 更新

## Checkpoint 10.1 — Theme System 加固

- [x] `template.html`：`board-bg` rect 使用 `id` 选择，明确区分 solid/grid
- [x] `background.type = solid`：JS 正确设置 solid fill，不引用 boardGrid pattern
- [x] `background.type = grid`：JS 设置 `url(#boardGrid)` 并更新 pattern 颜色
- [x] `node.badge_fill` / `node.badge_text`：所有 4 个主题均已配置
- [x] `src/theme.py`：`validate_theme()` 基础校验（必填字段、background.type 枚举、颜色格式）
- [x] `src/theme.py`：新增 CLI（`--theme` / `--config` / `--json`）
- [x] `examples/invalid.themes.yaml`：invalid theme 测试 fixture
- [x] pipeline 拒绝无效 theme name 和 invalid theme token
- [x] README.md / BACKLOG.md 更新

## Checkpoint 11 — Theme Layout System V1

- [x] `config/themes.yaml`：新增 `layout` 段（variant / canvas / title / nodes / dialogue）
- [x] `src/theme.py`：新增 layout 校验（variant 枚举、panel 正数）；新增 `apply_theme_layout()`
- [x] `src/pipeline.py`：新增 `apply_theme_layout` 调用
- [x] `renderer/template.html`：JS 读取 `NODE_LAYOUT` 控制 node 圆角/阴影/线宽；subtitle font-size 动态
- [x] 4 个主题 panel_position 布局（side / bottom_corner / desk_cards）
- [x] subtitle bar 高/位置/字号随 layout 变化
- [x] `examples/invalid.themes.yaml`：新增 `broken_layout` invalid layout 测试
- [x] README.md / BACKLOG.md 更新

## Checkpoint 12 — Local Web Studio V1

- [x] `src/server.py`（FastAPI 后端：health / themes / generate / artifacts / preview）
- [x] `web/index.html`（Studio 主页：输入配置 / 预览 / artifacts）
- [x] `web/app.js`（前端交互：generate / tab 切换 / JSON 展示）
- [x] `web/style.css`（深色双栏布局）
- [x] `requirements.txt`（新增 fastapi / uvicorn）
- [x] 支持 mode=sample / mode=text
- [x] 支持 theme 切换 / dialogue 开关 / export 开关
- [x] artifact JSON 预览（render_ir / semantic_ir / dialogue_script）
- [x] animation.html / output.mp4 预览和下载
- [x] README.md / BACKLOG.md 更新

## Checkpoint 12.1 — Web Studio no_export 状态修复

- [x] `src/server.py`：`/api/generate` 返回 `exported` 字段和 `output_mp4: null`（当 no_export=true）
- [x] `src/server.py`：no_export=false 但 output.mp4 不存在时返回 `ok=false`
- [x] `src/server.py`：animation.html 不存在时返回 `ok=false`
- [x] `web/app.js`：`showPreview()` 用 `exported` 判断，不使用 `output_mp4.includes("no_export")`
- [x] `web/index.html`：新增 `export-hint` 提示区域
- [x] `web/style.css`：新增 `.hint` 样式
- [x] README.md / PROJECT_SPEC.md / BACKLOG.md 更新

## Checkpoint 13 — 异步任务 / Progress Stream

- [x] `src/server.py`：新增 `/api/jobs` POST 创建异步任务
- [x] `src/server.py`：新增 `/api/jobs/{job_id}` GET 查询状态
- [x] `src/server.py`：新增 `/api/jobs/{job_id}/events` SSE 流
- [x] `src/server.py`：内存 job store（JOBS dict）
- [x] `src/server.py`：后台线程执行 `_run_job`
- [x] `src/server.py`：stdout 解析进度（STAGE_PATTERNS）
- [x] `src/server.py`：同步兼容 `/api/generate`（CP12.1 契约不变）
- [x] `web/app.js`：EventSource 接收 SSE 进度
- [x] `web/app.js`：进度条 + 日志展示
- [x] `web/index.html`：progress-bar / progress-text / job-log 元素
- [x] `web/style.css`：.progress-wrap / .progress-bar / .progress-text / .job-log 样式
- [x] README.md / PROJECT_SPEC.md / BACKLOG.md 更新

## Checkpoint 14 — Job History / Output Isolation

- [x] `src/pipeline.py`：新增 `--output-dir` 参数，默认 `outputs/latest`
- [x] `src/server.py`：每个 job 使用独立输出目录 `outputs/jobs/{job_id}`
- [x] `src/server.py`：新增 `/api/history` 返回历史任务列表
- [x] `src/server.py`：新增 `/api/jobs/{job_id}/artifacts/{name}` 读取 job 专属 artifact
- [x] `src/server.py`：新增 `/outputs/jobs/{job_id}/{filename}` 预览 job 专属文件
- [x] `src/server.py`：生成完成后写入 `meta.json`
- [x] `web/app.js`：新增历史 Gallery 展示
- [x] `web/app.js`：job done/error 后刷新 history
- [x] `web/index.html`：新增「历史作品」tab
- [x] `web/style.css`：新增 history panel 样式
- [x] README.md / PROJECT_SPEC.md / BACKLOG.md 更新

## Checkpoint 14.1 — Job History 加固

- [x] `.gitignore` 简化：`outputs/jobs/*` 整体忽略，只追踪 `.gitkeep`
- [x] `outputs/jobs/.gitkeep` 被 Git 追踪
- [x] `meta` 加入 `ALLOWED_ARTIFACTS`，`/api/jobs/{job_id}/artifacts/meta` 可用
- [x] `/api/history` 支持磁盘扫描（`_load_history_from_disk`）
- [x] 服务重启后 `/api/history` 从 meta.json 恢复
- [x] `_resolve_job_output_dir` helper：job_id 格式校验 + 路径穿越防护
- [x] artifact/preview API 重启后可访问磁盘上的 job
- [x] `meta.json` 增强：artifacts 映射、duration、title、summary
- [x] README.md / PROJECT_SPEC.md / BACKLOG.md 更新

## Checkpoint 15 — Real Provider Configuration

- [x] `/api/providers` GET 端点：返回 llm/tts provider status（ready + missing_env）
- [x] `_get_llm_provider_status()` / `_get_tts_provider_status()` helpers
- [x] `_check_env_vars()`：返回缺失 env var 名称列表（不返回值）
- [x] GenerateRequest 新增：`llm_provider` / `tts_provider` / `repair` / `repair_attempts`
- [x] `_build_pipeline_cmd()` 支持真实 provider command 构建
- [x] 前端 Provider 配置区：LLM/TTS select + ready/missing_env 提示
- [x] 前端 payload 增加 llm_provider / tts_provider / repair
- [x] history item 显示 llm_provider / tts_provider
- [x] README.md / PROJECT_SPEC.md / BACKLOG.md 更新

## Checkpoint 15.1 — Real Provider Entry

- [x] `/api/jobs` 支持 `mock=false`，不再直接拒绝
- [x] `_validate_provider_selection()`：创建 job 前验证 provider readiness
- [x] `_collect_required_env_from_profile()`：只有 profile 缺少默认值时才要求 env var
- [x] `_dedupe_keep_order()`：missing_env 去重
- [x] `_create_failed_job()`：provider 不 ready 时创建 failed job
- [x] `/api/generate` 保持同步兼容，仅支持 mock
- [x] README.md / PROJECT_SPEC.md / BACKLOG.md 更新

## Checkpoint 15.2 — Real LLM/TTS E2E 验证

- [x] `_validate_provider_selection()`：unknown provider 时立即返回错误
- [x] 真实 LLM + mock TTS E2E 验证
- [x] unknown provider failed job 验收
- [x] API key / voice_id 不泄露验收
- [ ] 真实 TTS E2E（CP15.3）

## Checkpoint 15.2.1 — Web Studio .env 自动加载

- [x] server 启动时 `load_dotenv(PROJECT_ROOT / ".env", override=False)`
- [x] `python-dotenv` 加入 requirements.txt
- [x] `/api/providers` 能读取 .env 中配置的 MINIMAX_API_KEY
- [x] README.md / PROJECT_SPEC.md / BACKLOG.md 更新

## Checkpoint 15.2.2 — 真实 LLM 失败诊断增强

- [x] pipeline.py：generate_ir 失败时打印 validation issues 摘要和 debug 文件路径
- [x] server.py：`_redact_secret_text()` helper，自动脱敏 API key / voice_id
- [x] server.py：改进 `_run_job` 错误提取，保留所有 `[auto:]` 行
- [x] server.py：`GET /api/jobs/{job_id}/debug` 端点，返回 validation issues 摘要
- [x] README.md / PROJECT_SPEC.md / BACKLOG.md 更新

## Checkpoint 15.2.3 — 真实 LLM E2E 成功收敛

- [x] generate_ir debug 文件写入 job output_dir（不再是 outputs/latest）
- [x] pipeline.py 从 output_dir 读取 debug 文件
- [x] server.py /api/jobs/{id}/debug 从 job output_dir 读取
- [x] `_apply_deterministic_repairs()`：自动修复 UNREVEALED_EDGE / UNREVEALED_NODE
- [x] prompts 更新：明确 reveal 覆盖规则
- [x] README.md / PROJECT_SPEC.md / BACKLOG.md 更新
- [ ] 真实 LLM + mock TTS E2E 完整成功（留待验收）

## Checkpoint 15.2.4 — 真实新闻样例 + real LLM E2E 通过

- [x] `examples/real_news_fixture.json`：真实新闻风格 fixture
- [x] server.py：支持 `mode=real_fixture`
- [x] `src/llm/json_utils.py`：`extract_json_object` 增强容错（brace counting）
- [x] README.md / PROJECT_SPEC.md / BACKLOG.md 更新
- [x] real LLM + mock TTS E2E 完整成功

## Checkpoint 15.2.5 — 热门 AI 新闻发现层 + hot_ai E2E（当前）

- [x] `src/fetch_hot_ai_news.py`：从 HN Firebase API 获取 AI 相关热门新闻
- [x] 关键词过滤：至少匹配一个 AI 相关关键词（OpenAI/LLM/Claude/Gemini 等）
- [x] 热度评分：`points * 1.0 + comments * 2.0 + recency_bonus + keyword_bonus`
- [x] 输出 `hot_ai_candidates.json`（20 条候选）
- [x] 输出 `latest_news.json`（top 1，选中新闻）
- [x] server.py：`mode=hot_ai` 支持，调用 `fetch_hot_ai_news`
- [x] ALLOWED_ARTIFACTS 新增 `hot_ai_candidates`、`latest_news`
- [x] 不抓取全文（无 paywall bypass、无版权内容）
- [x] mode=hot_ai + minimax_m3_openai + mock_dialogue E2E 验收通过
- [x] README.md / PROJECT_SPEC.md / BACKLOG.md 更新
- [ ] 多源聚合与去重（CP15.2.6）

## Checkpoint 15.3 — 真实 MiniMax TTS E2E

## Checkpoint 14.2 — Job 删除 / 清理

- DELETE `/api/jobs/{job_id}` 删除 job 输出目录
- 清理历史记录接口

## Checkpoint 16 — 主题预览图库

- 前端主题预览缩略图
- Theme gallery

## Checkpoint 17 — Remotion / 视觉升级

- Remotion 数字人
- 前端 UI（网页端配置和播放）

## Checkpoint 18 — 角色头像 / 半数字人

- 角色头像
- 半数字人

- Remotion 数字人
- 前端 UI（网页端配置和播放）
- `structure_type` 扩展：timeline / comparison / list

## 不做（Out of Scope）

- Remotion（CP16+）
- 数字人（CP16+）
- lip-sync（CP9+）
- 自动选题 / 多新闻合并
- 数据库 / Redis / Celery
- 数据库 / Redis / Celery
