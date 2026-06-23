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
- anthropic_messages：`POST {base_url}/messages`。若 base_url 已以 `/messages` 结尾则不重复追加。
- 两者缺 `base_url` 或缺 API key 时**清晰报错**，不静默回退。

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
| edges | id 唯一；推荐 `^e\d+$`；from/to 必须引用存在的 node id；from ≠ to；数量 ≥ nodes-1；causal_chain 要求存在从 n1 出发的线性链 |
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

## 文件清单（V0.8 新增 / 修改）

新增：
- `src/validate_ir.py`
- `prompts/repair_semantic_ir.md`
- `examples/invalid.semantic.bad_reveal.json`
- `examples/invalid.semantic.coord_field.json`
- `examples/invalid.semantic.duplicate_id.json`

修改：
- `src/generate_ir.py`（加 `--validate` / `--repair` / `--repair-attempts` / `--save-invalid`）
- `src/layout.py`（`continue` → `ValueError`）
- `requirements.txt`（+jsonschema）
- `README.md` / `PROJECT_SPEC.md` / `BACKLOG.md`

未修改：
- `src/pipeline.py` / `pace.py` / `render_html.py` / `export_video.py`
- `src/fetch_news.py` / `src/config_loader.py` / `src/utils.py`
- `schema/semantic_ir.schema.json`
- `renderer/template.html`
- `examples/sample.semantic.json`
