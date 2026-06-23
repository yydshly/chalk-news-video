# chalk-news-video

把一条新闻自动生成黑板风格的讲解动画视频 (output.mp4)。

## 当前 Checkpoint

**Checkpoint 2 — 可配置 LLM → semantic_ir**

`python -m src.generate_ir --news outputs/latest/latest_news.json` 把一条新闻通过 LLM 转换为 `outputs/latest/semantic_ir.json`，并保留 `debug_llm_prompt.txt` / `debug_llm_response.txt` 用于调试。

支持三种运行模式：
1. **`--dry-run`**：拼装 prompt 并保存，不调用任何 LLM。
2. **`--mock`**：使用内置 mock provider，无 key 也能生成合法 semantic_ir（不代表真实 LLM 效果）。
3. **真实 provider**：使用 `config/llm.yaml` 中的 profile（`minimax_m27_highspeed_anthropic` / `mimo_openai_compatible`）。

不包含（后续 Checkpoint）：
- validate_ir / 自动修复（Checkpoint 3）
- TTS / 完整 pipeline 编排（Checkpoint 4）
- Remotion / 数字人

`generate_ir` **未接入** `python -m src.pipeline` 默认流程。pipeline 仍可用 `--use-sample` 或 `--semantic-ir` 显式指定。

## 项目定位

V0.7: News → LLM → semantic_ir；视频仍由 `src.pipeline` 显式触发。

## 架构

```
sources.yaml ──▶ fetch_news ──▶ latest_news.json ──┐
                                                  │
                            ┌─────────────────────┘
                            ▼
                      generate_ir (LLM)
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
             export_video.py ── Playwright + FFmpeg ──▶ output.mp4
```

唯一允许产出坐标的地方：`layout.py`。
唯一允许产生时间的地方：`pace.compute_timeline_from_beats`。
唯一允许调用 LLM 的入口：`src/generate_ir.py`。

## 安装

```bash
cd chalk-news-video
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

还需要 FFmpeg 加入 PATH。

## 配置 LLM（llm.yaml）

`config/llm.yaml` 用 profile 结构。每个 profile 描述一个 provider：

```yaml
default_profile: minimax_m27_highspeed_anthropic

profiles:
  minimax_m27_highspeed_anthropic:
    provider: minimax
    protocol: anthropic_messages
    api_key_env: MINIMAX_API_KEY
    base_url: ""                # ← 留空，由 .env 提供 MINIMAX_BASE_URL
    base_url_env: MINIMAX_BASE_URL
    model: "MiniMax-M2.7-highspeed"
    model_env: MINIMAX_MODEL
    anthropic_version: "2023-06-01"
    temperature: 0.2
    max_tokens: 4000
    timeout_seconds: 60

  mimo_openai_compatible:
    provider: mimo
    protocol: openai_compatible
    api_key_env: MIMO_API_KEY
    base_url: ""                # ← 留空，由 .env 提供 MIMO_BASE_URL
    base_url_env: MIMO_BASE_URL
    model: ""                   # ← 留空，由 .env 提供 MIMO_MODEL
    model_env: MIMO_MODEL
    temperature: 0.2
    max_tokens: 4000
    timeout_seconds: 60
```

支持协议：
- `openai_compatible` → POST `{base_url}/chat/completions`
- `anthropic_messages` → POST `{base_url}/messages`

> 本仓库**不再提供 `mock` profile**。Mock 入口唯一在 CLI：`python -m src.generate_ir --mock`。
> 这避免了在 llm.yaml 里写 `mock` 然后意外把它当 default_profile，导致 LLM 调用静默返回空。

## .env：默认自动加载

`create_llm_client()` 默认会从项目根目录读取 `.env`，把缺失的 key 填进 `os.environ`（用 `setdefault`，**不会覆盖你已经设好的系统环境变量**）。

```bash
cp .env.example .env
# 编辑 .env，填入：
#   MINIMAX_API_KEY=<your key>
#   MINIMAX_BASE_URL=<your endpoint>
#   MINIMAX_MODEL=MiniMax-M2.7-highspeed
#   MIMO_API_KEY=<your key>
#   MIMO_BASE_URL=<your endpoint>
#   MIMO_MODEL=<your model>
```

如果 `.env` 不存在，**不报错**，继续从系统环境变量读取（CI / shell export 都 OK）。

如要换路径：`python -m src.generate_ir --env /path/to/.env`。
如要显式跳过：把 `--env` 指向一个不存在的文件即可。

**优先级**：真实系统环境变量 > `.env` > `llm.yaml` 中的静态值。

## .env 示例

```bash
cp .env.example .env
# 编辑 .env，填入真实 key 与 base_url
```

```env
MINIMAX_API_KEY=<your MiniMax key>
MINIMAX_BASE_URL=<your MiniMax endpoint>
MINIMAX_MODEL=MiniMax-M2.7-highspeed

MIMO_API_KEY=<your Mimo key>
MIMO_BASE_URL=<your Mimo endpoint>
MIMO_MODEL=<your Mimo model>
```

> **不要提交真实 API key 或真实 base_url**。本仓库 `.env.example` 全部留空。
> **不要猜** MiniMax / Mimo 的真实 base_url——除非来自已验证的官方文档或你本地跑通过的项目代码。

## 运行 generate_ir

```bash
# 1) Dry-run：只拼 prompt，不调用 LLM
python -m src.generate_ir --news examples/sample_news.json --dry-run

# 2) Mock：无 key 本地测试（推荐方式，绕过 llm.yaml 的 profile 选择）
python -m src.generate_ir --news examples/sample_news.json --mock

# 3) 真实 MiniMax（读 .env / 系统环境变量）
python -m src.generate_ir --news outputs/latest/latest_news.json \
    --profile minimax_m27_highspeed_anthropic

# 4) 真实 Mimo
python -m src.generate_ir --news outputs/latest/latest_news.json \
    --profile mimo_openai_compatible
```

可选参数：
- `--config config/llm.yaml`
- `--prompt prompts/news_to_semantic_ir.md`
- `--output outputs/latest/semantic_ir.json`
- `--env /path/to/.env`（默认：`<project root>/.env`，缺失不报错）

## 产物

```
outputs/latest/debug_llm_prompt.txt      完整 prompt（system + user）
outputs/latest/debug_llm_response.txt    LLM 原始响应 / mock 输出
outputs/latest/semantic_ir.json          解析后的 semantic_ir
```

## 校验 semantic_ir

```bash
# 校验一个文件
python -m src.validate_ir outputs/latest/semantic_ir.json

# 输出 JSON 格式
python -m src.validate_ir outputs/latest/semantic_ir.json --json

# 把警告当错误
python -m src.validate_ir outputs/latest/semantic_ir.json --strict
```

退出码：`0` = 合法，`1` = 不合法，`2` = 文件不存在 / JSON 解析失败。

校验规则包括：
- **jsonschema**：required / type / enum / additionalProperties / minItems / maxItems
- **禁止坐标字段**：`x` `y` `w` `h` `cx` `cy` 任何层级出现都报错
- **ID 唯一性**：nodes / edges / callouts / beats 的 id 不可重复
- **引用完整性**：edge.from / edge.to / callout.on 必须指向存在的 node id
- **beats 覆盖率**：每个 node / edge / callout 至少被一个 beat reveal 一次
- **第一个 beat 必须是 title**
- **narration 长度**：≤ 120 字符
- **callout 数量**：0~3

## 生成 + 校验（一步）

```bash
# 生成后自动校验；不合法则打印 issue 并退出 5
python -m src.generate_ir --news examples/sample_news.json --mock --validate

# 生成后自动校验 + 自动修复（需要真实 LLM 配置）
python -m src.generate_ir --news outputs/latest/latest_news.json \
    --profile minimax_m27_highspeed_anthropic --validate --repair

# --repair 最多 2 次（可改）
python -m src.generate_ir --news outputs/latest/latest_news.json \
    --profile minimax_m27_highspeed_anthropic --validate --repair --repair-attempts 3
```

`--repair` 需要真实 LLM（不能 `--mock`）。修复尝试失败会写入：
- `outputs/latest/debug_validation_issues.json`
- `outputs/latest/debug_repair_prompt.txt`
- `outputs/latest/debug_repair_response.txt`

默认 `--no-save-invalid`：不合法的 semantic_ir **不会**被写入 `semantic_ir.json`。用 `--save-invalid` 强制保存到 `semantic_ir.invalid.json`。

## 常见校验错误

| code | 含义 |
|------|------|
| `FORBIDDEN_COORD` | LLM 输出了坐标字段（x/y/w/h/cx/cy） |
| `UNKNOWN_REVEAL` | beat.reveal 引用了不存在的 id |
| `DUPLICATE_NODE_ID` | node id 重复 |
| `UNREVEALED_NODE` | 某个 node 从未被 beats reveal |
| `FIRST_BEAT_NOT_TITLE` | 第一个 beat 的 reveal 不是 "title" |
| `MISSING_EDGE_FROM` | edge.from 指向不存在的 node |
| `BROKEN_CAUSAL_CHAIN` | causal_chain 存在多条不相连的路径，无法覆盖所有 node |

## gitignore 说明

以下文件类型都会被 `.gitignore` 屏蔽，**不会**被提交：
```
outputs/latest/*.json   # 含 semantic_ir.json / render_ir.json / debug_*.json
outputs/latest/*.html   # animation.html
outputs/latest/*.mp4   # output.mp4
outputs/latest/*.txt    # debug_*.txt
.env                   # 真实 key
```

## 当前 Checkpoint

详见 [PROJECT_SPEC.md](PROJECT_SPEC.md) 和 [BACKLOG.md](BACKLOG.md)。


## 把生成的 semantic_ir 接到 pipeline

```bash
python -m src.pipeline --semantic-ir outputs/latest/semantic_ir.json
# 产出：
#   outputs/latest/render_ir.json
#   outputs/latest/animation.html
#   outputs/latest/output.mp4
```

或继续用演示版：

```bash
python -m src.pipeline --use-sample
```

## 当前 Checkpoint

详见 [PROJECT_SPEC.md](PROJECT_SPEC.md) 和 [BACKLOG.md](BACKLOG.md)。
