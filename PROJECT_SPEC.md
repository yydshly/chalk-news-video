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
7. **fetch_news 只产出 latest_news.json**。
8. **LLM 只在 generate_ir 调用一次**，HTML/SVG 渲染层不调用 LLM。
9. **generate_ir 不自动接入 pipeline**——它产出 semantic_ir；video 仍由 `src.pipeline --semantic-ir` 显式触发。

## 数据流（完整）

```
sources.yaml ──▶ fetch_news ──▶ latest_news.json ──┐
                                                  │
                            ┌─────────────────────┘
                            ▼
              src.generate_ir (LLM provider from llm.yaml)
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

## Checkpoint 2 — LLM Provider Layer

职责边界：
- **做**：从 `llm.yaml` 选择 profile，按 protocol 创建 provider，调用 LLM，解析 JSON，**最低限度**校验（dict + 必填顶层 key + 无坐标字段），写入 semantic_ir.json
- **不做**：完整 jsonschema 校验（Checkpoint 3）、自动 repair loop（Checkpoint 3）、TTS、Remotion、video 导出、把 generate_ir 接入 pipeline 默认流程

### 模块

| 文件 | 职责 |
|------|------|
| `src/llm/base.py` | `LLMProvider.generate_text(system, user) -> str` |
| `src/llm/openai_compatible_provider.py` | POST `{base_url}/chat/completions` |
| `src/llm/anthropic_messages_provider.py` | POST `{base_url}/messages`，headers 含 `x-api-key` / `anthropic-version` |
| `src/llm/client.py` | `create_llm_client(profile_name=None)` 工厂 + `MockProvider` |
| `src/llm/json_utils.py` | `extract_json_object(text)` 兼容裸 JSON / ```json fence / 前缀散文 |
| `prompts/news_to_semantic_ir.md` | LLM prompt：硬规则 + 输出契约 + 禁止项 |

### llm.yaml profile 结构

```yaml
profiles:
  <name>:
    protocol: openai_compatible | anthropic_messages | mock
    api_key_env: <ENV var name>          # 从 os.environ 读
    base_url: "<or empty>"
    base_url_env: <ENV var name>         # 若 base_url 为空，尝试读此环境变量
    model: "<or empty>"
    model_env: <ENV var name>            # 同上
    temperature: 0.2
    max_tokens: 4000
    timeout_seconds: 60
```

### 端点规则

- openai_compatible：`POST {base_url}/chat/completions`。若 base_url 已以 `/chat/completions` 结尾则不重复追加。
- anthropic_messages：`POST {base_url}{endpoint_path}`（默认 `/v1/messages`）。若 base_url 已以 `endpoint_path` 结尾则不重复追加。
- 两者缺 `base_url` 或缺 API key 时**清晰报错**，不静默回退。

### LLM Provider Official Config（CP3.2 校准）

**auth_type 支持**：
- `bearer` → `Authorization: Bearer {key}`（MiniMax OpenAI-compatible）
- `api-key` → `{api_key_header}: {key}`（MiMo，默认 header 为 `api-key`）

**max_tokens_param**：不同 provider 支持不同字段名。
- MiniMax M3 推荐 `max_completion_tokens`
- MiniMax M2.7-highspeed 可用 `max_tokens`
- MiMo 使用 `max_completion_tokens`

**extra_body**：profile.extra_body 合并进请求 payload，标准字段优先。

**环境变量优先级**：`env > yaml 静态值`。用户可通过 env 覆盖默认官方 base_url / model。

**官方 base_url**（已验证）：
- MiniMax OpenAI-compatible：`https://api.minimaxi.com/v1`
- MiniMax Anthropic-compatible：`https://api.minimaxi.com/anthropic`
- MiMo 按量：`https://api.xiaomimimo.com/v1`

**注意**：MiMo 不可直接等同普通 OpenAI-compatible；它使用 `api-key` header 和 `max_completion_tokens`。

## generate_ir 输入输出契约

**输入**
- `--news path/to/latest_news.json`（默认 `outputs/latest/latest_news.json`）
- `--config path/to/llm.yaml`（默认 `config/llm.yaml`）
- `--prompt path/to/prompt.md`（默认 `prompts/news_to_semantic_ir.md`）
- `--profile name`（覆盖 `default_profile`）
- `--dry-run` / `--mock` / `--output`

**输出**
- `outputs/latest/debug_llm_prompt.txt`（含 system + user prompt + 时间戳 + 来源标记）
- `outputs/latest/debug_llm_response.txt`（含 LLM 原始响应或 mock 输出）
- `outputs/latest/semantic_ir.json`（解析后，UTF-8，indent=2，ensure_ascii=False）

**最低限度校验（在本轮内）**
- 必须是 dict
- 必含 schema_version / meta / structure_type / title / nodes / edges / callouts / beats
- 任何层级禁止 `x` / `y` / `w` / `h` / `cx` / `cy`

完整 jsonschema 校验、自定义引用校验、repair loop **留到 Checkpoint 3**。

## semantic_ir 生成规则（与 prompt 对齐）

- schema_version = `"0.1"`
- structure_type = `"causal_chain"`
- meta.lang = `"zh"`
- nodes 2~5，edges ≥ nodes-1，callouts 0~3，beats 6~10
- 第一个 beat reveal 必须是 `"title"`
- 每个 narration ≤ 60 中文字符
- 不允许任何坐标字段
- 不允许 `nodes[].narration` / `callouts[].attach_to`

## 为什么 CP2 不做 validate_ir 自动修复

- 本轮目标只是把 LLM 接入并产出语义 IR；prompt 与 schema 已经约束得很死，但仍可能有小概率格式漂移。
- 自动 repair 需要：调用 LLM 二次、改 prompt、用 jsonschema 强校验。这些组合起来调试成本高，且需要 careful prompt engineering。
- 最低限度 dict + 必填 key + 无坐标字段已经覆盖 90% 的"硬错"；剩下的"软错"留到 CP3 配 jsonschema + repair loop 一起做。

## Checkpoint 3 — Validation Layer + Repair Loop

职责边界：
- **做**：强 jsonschema 校验 + 自定义业务规则校验；结构化 `ValidationIssue` 返回；可选 LLM repair loop（上限 N 次）
- **不做**：layout 强校验（layout.py 仍只做坐标生成，只在引用缺失时显式报错）；TTS / Remotion / pipeline 自动编排

### ValidationIssue 数据结构

```python
@dataclass
class ValidationIssue:
    code: str      # e.g. "FORBIDDEN_COORD", "UNKNOWN_REVEAL"
    path: str      # JSON path, e.g. "nodes[0].x"
    message: str   # 人类可读描述
    severity: str = "error"  # "error" | "warning"
```

### 校验规则（A + B 两层）

**A. jsonschema（Draft7）**
- `required` / `type` / `enum` / `additionalProperties` / `minItems` / `maxItems`

**B. 自定义业务规则**
| 类别 | 规则 |
|---|---|
| 禁止字段 | 任意层级禁止 `x` `y` `w` `h` `cx` `cy`；顶层禁止 `layout`；node 禁止 `narration`；callout 禁止 `attach_to` |
| nodes | 数量 2~5；id 唯一；推荐 `^n\d+$` |
| edges | id 唯一；推荐 `^e\d+$`；from/to 必须引用存在的 node id；from ≠ to；数量 ≥ nodes-1；causal_chain 要求存在一条线性路径覆盖所有 node，断链时报 `BROKEN_CAUSAL_CHAIN` |
| callouts | id 唯一；推荐 `^c\d+$`；on 必须引用存在的 node id；数量 0~3 |
| beats | 数量 6~10；id 唯一；推荐 `^b\d+$`；第一个 beat.reveal = "title"；reveal 必须是已知 id 或 "title"；narration 非空且 ≤ 120 字符；每个 node/edge/callout 至少被 reveal 一次 |
| meta | lang = "zh"；source_title / source_url / source_name 必须存在 |

### Repair Loop

触发条件：`--repair` 且 `validate_ir` 返回非空 issue。
流程：
1. 用 `prompts/repair_semantic_ir.md` 构造 repair prompt（附原始 IR + issues + schema）
2. 调用 LLM 获取修复版本
3. 再次 `validate_ir`
4. 最多 N 次（`--repair-attempts`，默认 2）
5. 仍不合法时写入 `debug_validation_issues.json` / `debug_repair_prompt.txt` / `debug_repair_response.txt`，退出 5

### generate_ir 新增参数

| 参数 | 作用 |
|---|---|
| `--validate` | 生成后调用 `validate_ir`，不合法则 exit 5 |
| `--repair` | 不合法时自动调用 LLM 修复（最多 `--repair-attempts` 次） |
| `--repair-attempts N` | 最大修复尝试次数（默认 2） |
| `--save-invalid` | 允许保存非法 IR 到 `.invalid.json`（默认拒绝） |

### layout.py 引用校验

- `edge.from` / `edge.to` 找不到节点 → `ValueError`（不再 `continue`）
- `callout.on` 找不到节点 → `ValueError`（不再 `continue`）
- 错误信息包含具体的 edge/callout id 和缺失的引用值

## Checkpoint 4 — Auto Pipeline Orchestrator

职责边界：
- **做**：完整链路编排 `news → generate_ir → validate_ir → layout → render_html → export_video`；阶段化错误报告；subprocess 隔离 generate_ir
- **不做**：TTS / Remotion / 数字人 / 前端 UI / 多新闻选择

### Auto Pipeline 阶段

| 阶段 | 输入 | 输出 | 失败标签 |
|---|---|---|---|
| fetch_news | sources.yaml | latest_news.json | `[auto:fetch_news]` |
| generate_ir | latest_news.json | semantic_ir.json | `[auto:generate_ir]` |
| validate_ir | semantic_ir.json | issues list | `[auto:validate_ir]` |
| layout | semantic_ir.json | render_ir.json | `[auto:layout]` |
| render_html | render_ir.json | animation.html | `[auto:render_html]` |
| export_video | animation.html | output.mp4 | `[auto:export]` |

### 错误处理规范

- 每一步失败打印 `[auto:<stage>] FAILED: <message>` 并 exit 1
- subprocess 错误透传 returncode，不吞错误
- 不继续使用旧文件生成视频
- `semantic_ir.invalid.json` 是调试产物，auto pipeline 不使用它进入 layout/render/export 阶段；generate_ir 返回非 0 时 pipeline 直接退出

### 为什么 CP4 仍不做 TTS/Remotion

TTS 和数字人需要额外的外部服务集成，且视频质量依赖模型选择。CP4 专注于端到端链路通顺，TTS/Remotion 留到 CP6+。

## Checkpoint 5 — 真实 RSS + 真实 LLM 端到端验证

配置真实 RSS URL + 真实 MiniMax/MiMo key，完整链路跑通验证。

## Checkpoint 6 — Narration Layer（TTS 单人口播）

### Narration Layer

职责边界：
- **做**：TTS narration 生成、音频拼接、narration_manifest.json 契约
- **不做**：多角色对话、双人 TTS、Remotion

### 阶段

| 阶段 | 输入 | 输出 |
|---|---|---|
| narration | semantic_ir.json | audio/beat_*.wav + audio/narration.wav + narration_manifest.json |

### narration_manifest.json 契约

```json
{
  "schema_version": "0.1",
  "provider": "mock",
  "audio_format": "wav",
  "sample_rate": 24000,
  "total_duration": 25.3,
  "beats": [
    {
      "beat_id": "b1",
      "reveal": "title",
      "text": "今天我们聊...",
      "audio_path": "outputs/latest/audio/beat_001.wav",
      "start": 0.0,
      "duration": 3.2,
      "end": 3.2
    }
  ],
  "combined_audio_path": "outputs/latest/audio/narration.wav"
}
```

### TTS Provider 抽象

| Provider | 配置 | 备注 |
|---|---|---|
| mock | local_wav | 默认，用于 CP6 验收 |
| minimax | http_tts | 需要用户提供 endpoint/key/voice_id |

### 为什么 CP6 先做单人口播

双人对话需要脚本分析和角色分配，复杂度更高。单人口播验证 TTS 链路后，CP7 再扩展对话。

## Checkpoint 6.1 — 音画同步

### 契约优先级

CP6.1 确立三层时间契约：

1. **semantic_ir**：语义契约（beat_id、reveal、narration 文本）
2. **narration_manifest**：音频时间契约（beat_id、start、duration、end，来自真实 TTS）
3. **render_ir.timeline**：最终渲染时间契约（beat_id、at、duration，**必须与 manifest 一致**）

TTS 模式下时间源优先级：
```
narration_manifest.start/duration  >  pace 估算
```

### apply_narration_timing

`src/narration_timing.apply_narration_timing(render_ir, narration_manifest)`：
- 用 `manifest.beats[].beat_id` 匹配 `render_ir.timeline[].beat_id`
- 对每个匹配 beat：`timeline_item.at = manifest_beat.start`，`timeline_item.duration = manifest_beat.duration`
- `render_ir.total_duration = narration_manifest.total_duration`
- timeline 有但 manifest 没有的 beat → `ValueError`
- manifest 有但 timeline 没有的 beat → `warnings.warn`（不失败）

### narration_manifest 新增字段（CP6.1）

| 字段 | 类型 | 说明 |
|------|------|------|
| `speech_duration` | float | 最后一个 beat 的 end（不含尾静音） |
| `tail_silence` | float | 追加的尾静音秒数（默认 0.5s） |
| `total_duration` | float | speech_duration + tail_silence |
| `sample_rate` | int | 来自 TTS provider（非硬编码 24000） |

### Pipeline 顺序（CP6.1 with TTS）

```
generate_ir → validate_ir → tts → layout → apply_narration_timing
→ save render_ir.json → render_html → export_video(audio_path)
```

### 错误处理（CP6.1）

- `--tts` 开启但 `narration_manifest.json` 不存在 → 直接失败，exit 1
- `--tts` 开启但 `combined_audio_path` 文件不存在 → 直接失败，exit 1
- TTS 失败后不允许无声继续导出

## Checkpoint 7 — 双人对话脚本

### 职责边界

- **做**：双角色对话、host/expert 多 voice TTS、dialogue_manifest.json
- **不做**：多角色 TTS（CP8）、Remotion / 数字人（CP9）

### CP7.1 契约层级（新增）

CP7.1 确立三层对话契约（CP7.2 继续加固）：

1. **semantic_ir**：结构语义契约（beat_id、reveal、narration）
2. **dialogue_script**：对话表达契约（turns with host/expert alternating）
3. **dialogue_manifest**：对话音频时间契约（turns with real start/duration/end）

### dialogue_script.json 契约

```json
{
  "schema_version": "0.1",
  "source_semantic_ir": { "title": "...", "schema_version": "0.1" },
  "style": {
    "format": "two_speaker_explainer",
    "tone": "clear_curious",
    "language": "zh",
    "speakers": [
      {"id": "host", "name": "主持人", "role": "questioner"},
      {"id": "expert", "name": "讲解员", "role": "explainer"}
    ]
  },
  "turns": [
    {
      "id": "d1",
      "speaker": "host",
      "beat_id": "b1",
      "reveal": "title",
      "text": "这条新闻在讲什么？",
      "function": "hook",
      "duration_hint": 2.5
    }
  ]
}
```

### dialogue_script 校验规则（CP7.2 新增）

**A. jsonschema（Draft7）**
- `source_semantic_ir`：必含 `title` 和 `schema_version`
- `style`：必含 `format`、`tone`、`language`、`speakers`
- `style.speakers`：必含 2 项，id 不可重复（uniqueItems: true）
- `turns`：`additionalProperties: false`，不允许 audio_path/start/end/duration

**B. 自定义业务规则**
| 类别 | 规则 |
|---|---|
| turns | 非空；数量推荐 8–18；turn id 唯一 |
| speaker | 必须是 'host' 或 'expert'；必须在 style.speakers 中定义 |
| beat 覆盖 | 每个 semantic_ir beat 至少被一个 turn 覆盖 |
| reveal 对齐 | turn.reveal 必须与 semantic_ir.beats[beat_id].reveal 一致 |
| 角色存在 | 至少有一个 host turn 和一个 expert turn |
| style.speakers | 不可为空；id 不可重复 |

### dialogue_manifest.json 契约（CP7.1 新结构）

```json
{
  "schema_version": "0.1",
  "provider": "mock_host+mock_expert",
  "dialogue_profile": "mock_dialogue",
  "speaker_profiles": {
    "host": { "profile": "mock_host", "voice": "host" },
    "expert": { "profile": "mock_expert", "voice": "expert" }
  },
  "source_dialogue_script": { "schema_version": "0.1" },
  "total_duration": 21.0,
  "turns": [
    {
      "turn_id": "d1",
      "speaker": "host",
      "beat_id": "b1",
      "reveal": "title",
      "text": "...",
      "audio_path": "outputs/latest/audio/turn_d1.wav",
      "start": 0.0,
      "duration": 2.4,
      "end": 2.4
    }
  ],
  "combined_audio_path": "outputs/latest/audio/dialogue.wav"
}
```

**CP8 新增字段**：
- `dialogue_profile`：使用的 dialogue profile 名称（如 `"mock_dialogue"`）
- `speaker_profiles`：speaker → {profile, voice/voice_env}（不记录真实 API key）

### narration_timing 聚合规则（CP7.1 新增）

`dialogue_manifest.turns` → `render_ir.timeline`：
- 同一 beat_id 的多个 turn 聚合为一个 timeline item
- `timeline_item.at` = 该 beat 第一条 turn 的 start
- `timeline_item.duration` = 最后一条 turn 的 end - 第一条 turn 的 start

### TTS voice 配置（CP7）

| Speaker | Mock Profile | 说明 |
|---------|-------------|------|
| host | mock_host | 440Hz A4 note |
| expert | mock_expert | 330Hz E4 note |

### Dialogue Profile Mapping（CP8 新增）

`config/tts.yaml` 中 `dialogue_profiles` 段定义 speaker → TTS profile 映射：

```yaml
dialogue_profiles:
  mock_dialogue:
    host:
      profile: mock_host
      voice: host
    expert:
      profile: mock_expert
      voice: expert
  minimax_dialogue:
    host:
      profile: minimax_speech
      voice_env: MINIMAX_TTS_HOST_VOICE_ID
    expert:
      profile: minimax_speech
      voice_env: MINIMAX_TTS_EXPERT_VOICE_ID
```

**优先级**：
1. `--host-profile` + `--expert-profile`（兼容旧方式）
2. `--dialogue-profile`（CP8 新方式，按 dialogue_profiles 映射）

**voice 执行语义（CP8.1）**：
- `voice` / `voice_env` 从 dialogue_profiles 解析后真正传入 `provider.synthesize(voice=...)`
- `_resolve_speaker_voice()` 解析顺序：voice > voice_id > voice_env（从 os.environ 读取）
- mock_dialogue 的 voice 值安全，可记录到 manifest
- minimax_dialogue 的真实 voice_id 不写入 manifest，只记录 voice_env 名
- env-based voice 缺失时 RuntimeError 清晰报错，不静默使用默认值

### generate_dialogue repair 流程（CP8 新增）

**触发条件**：`--repair` 且 validation 失败。

流程：
1. 用 `prompts/repair_dialogue_script.md` 构造 repair prompt（附 semantic_ir + invalid dialogue_script + issues）
2. 调用 LLM 获取修复版本
3. 再次 `validate_dialogue`
4. 最多 `--repair-attempts` 次（默认 2）
5. 成功 → 写 `dialogue_script.json`
6. 失败 → 写 `dialogue_script.invalid.json`，退出 5

**Debug 产物**：
- `debug_dialogue_prompt.txt`
- `debug_dialogue_response.txt`
- `debug_dialogue_validation_issues.json`
- `debug_repair_prompt.txt`
- `debug_repair_response.txt`

### Pipeline 顺序（CP8 dialogue mode）

```
generate_ir → validate_ir
→ (auto-generate dialogue_script.json if missing)
→ narration (dialogue_audio) → layout → apply_narration_timing
→ save render_ir.json → render_html → export_video(audio_path=dialogue.wav)
```

### 错误处理（CP8）

- `dialogue_script.json` 不存在 → 自动生成（mock 或 real LLM）
- `dialogue_script.json` validate 失败 → 非 mock 模式调用 repair；仍失败则 exit 5
- `dialogue_manifest.json` 不存在 → 直接失败
- `dialogue.wav` 不存在 → 直接失败
- timeline beat_id 在 manifest turns 中找不到 → ValueError

## Checkpoint 8+ — Remotion / UI

CP8：真实 LLM dialogue 生成验证 + 多角色 TTS profile mapping
CP9：对话式视觉表现 / 当前 speaker 高亮
CP10：Theme System（黑板 / 米黄 / 深蓝）
CP11：Remotion / 视觉升级

- Remotion 数字人
- 前端 UI（网页端配置和播放）

## 文件清单（V0.11 新增 / 修改）

新增：
- `src/tts/`（TTS provider 基础设施）
- `src/narration.py`（新增 `generate_dialogue` 函数）
- `src/narration_timing.py`（CP6.1 新增）
- `config/tts.yaml`（新增 mock_host / mock_expert profiles + dialogue_profiles）
- `docs/CP5_REAL_E2E_VALIDATION.md`
- `prompts/repair_dialogue_script.md`（CP8 新增）
- `docs/CP8_REAL_DIALOGUE_VALIDATION.md`（CP8 新增）

修改：
- `src/generate_dialogue.py`（CP8：repair 流程 + debug 输出）
- `src/narration.py`（CP8：--dialogue-profile + speaker_profiles）
- `src/pipeline.py`（CP8：dialogue-profile + repair 流程）
- `config/tts.yaml`（CP8：新增 dialogue_profiles 段）
- `README.md` / `PROJECT_SPEC.md` / `BACKLOG.md`

修改：
- `src/pipeline.py`（新增 `--dialogue` / `--host-profile` / `--expert-profile`）
- `src/export_video.py`（添加 mux 日志和 ffprobe 时长检查）
- `src/tts/mock_tts_provider.py`（返回 sample_rate，不同 voice 不同频率）
- `prompts/news_to_semantic_ir.md`（新增 speaker 字段说明）
- `README.md` / `PROJECT_SPEC.md` / `BACKLOG.md`

未修改：
- `src/pace.py` / `src/render_html.py`
- `src/fetch_news.py` / `src/config_loader.py` / `src/utils.py`
- `schema/semantic_ir.schema.json`
- `renderer/template.html`
- `examples/sample.semantic.json`
