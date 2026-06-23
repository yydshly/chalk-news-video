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

## 文件清单（V0.7 新增 / 修改）

新增：
- `src/generate_ir.py`
- `src/llm/__init__.py` / `base.py` / `client.py` / `openai_compatible_provider.py` / `anthropic_messages_provider.py` / `json_utils.py`
- `prompts/news_to_semantic_ir.md`

修改：
- `config/llm.yaml`（profile 结构）
- `.env.example`（新增 6 个环境变量）
- `README.md` / `PROJECT_SPEC.md` / `BACKLOG.md`

未修改：
- `src/pipeline.py` / `layout.py` / `pace.py` / `render_html.py` / `export_video.py`
- `src/fetch_news.py` / `src/config_loader.py` / `src/utils.py`
- `schema/semantic_ir.schema.json`（prompt 引用其内容）
- `renderer/template.html`
- `examples/sample.semantic.json`
