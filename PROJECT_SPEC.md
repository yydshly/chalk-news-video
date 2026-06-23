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

## Checkpoint 7 — 双人对话脚本

- 多角色对话分析
- 两个 TTS voice_id

## Checkpoint 8+ — Remotion / UI

- Remotion 数字人
- 前端 UI（网页端配置和播放）

## 文件清单（V0.11 新增 / 修改）

新增：
- `src/tts/`（TTS provider 基础设施）
- `src/narration.py`
- `config/tts.yaml`
- `docs/CP5_REAL_E2E_VALIDATION.md`

修改：
- `src/pipeline.py`（新增 `--tts` / `--tts-profile`）
- `src/export_video.py`（音频 mux 支持）
- `README.md` / `PROJECT_SPEC.md` / `BACKLOG.md`

新增：
- `src/validate_ir.py`
- `prompts/repair_semantic_ir.md`
- `examples/invalid.semantic.bad_reveal.json`
- `examples/invalid.semantic.coord_field.json`
- `examples/invalid.semantic.duplicate_id.json`
- `examples/invalid.semantic.disconnected_chain.json`

修改：
- `src/generate_ir.py`（加 `--validate` / `--repair` / `--repair-attempts` / `--save-invalid`）
- `src/layout.py`（`continue` → `ValueError`）
- `src/llm/openai_compatible_provider.py`（支持 auth_type / api_key_header / max_tokens_param / extra_body）
- `src/llm/anthropic_messages_provider.py`（支持 endpoint_path / api_key_header / extra_body）
- `src/pipeline.py`（新增 `--auto` / `--mock` / `--news` / `--source` / `--profile` / `--repair` / `--no-export`）
- `config/llm.yaml`（5 个 official profiles）
- `.env.example`（官方 base_url / model 示例）
- `requirements.txt`（+jsonschema）
- `README.md` / `PROJECT_SPEC.md` / `BACKLOG.md`

未修改：
- `src/pace.py` / `src/render_html.py` / `src/export_video.py`
- `src/fetch_news.py` / `src/config_loader.py` / `src/utils.py`
- `schema/semantic_ir.schema.json`
- `renderer/template.html`
- `examples/sample.semantic.json`
