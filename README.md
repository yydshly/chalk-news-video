# chalk-news-video

把一条新闻自动生成黑板风格的讲解动画视频 (output.mp4)。

## 当前 Checkpoint

**Checkpoint 6 — TTS 单人口播 + 音画同步（当前）**

一条命令跑通 news → semantic_ir → TTS narration → video（含音频）：

```bash
# 无音频（CP4/CP5 模式，不变）
python -m src.pipeline --auto --mock

# 带音频（CP6 新增）
python -m src.pipeline --auto --mock --tts --tts-profile mock
```

TTS 使用 `config/tts.yaml` 配置，支持 mock（默认）和真实 MiniMax TTS。

不包含（后续 Checkpoint）：
- 双人对话（CP7）
- 多角色 TTS（CP8）
- Remotion / 数字人（CP9）

## 项目定位

V0.10: News → LLM → semantic_ir → TTS narration → video（含音频）。

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

> **不要提交真实 API key**。本仓库 `.env.example` 全部留空或使用官方示例值。

## 运行 generate_ir

```bash
# 1) Dry-run：只拼 prompt，不调用 LLM
python -m src.generate_ir --news examples/sample_news.json --dry-run

# 2) Mock：无 key 本地测试（推荐方式，绕过 llm.yaml 的 profile 选择）
python -m src.generate_ir --news examples/sample_news.json --mock

# 3) 真实 MiniMax M3 OpenAI-compatible（读 .env / 系统环境变量）
python -m src.generate_ir --news outputs/latest/latest_news.json \
    --profile minimax_m3_openai

# 4) 真实 MiniMax M2.7-highspeed OpenAI-compatible
python -m src.generate_ir --news outputs/latest/latest_news.json \
    --profile minimax_m27_highspeed_openai

# 5) 真实 MiMo 按量
python -m src.generate_ir --news outputs/latest/latest_news.json \
    --profile mimo_v25_pro_openai

# 6) 真实 MiMo Token Plan（需先设置 MIMO_BASE_URL 和 MIMO_API_KEY）
python -m src.generate_ir --news outputs/latest/latest_news.json \
    --profile mimo_token_plan_v25_pro_openai
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
- **causal_chain 连通性**：必须存在一条线性路径覆盖所有 node，断链报错 `BROKEN_CAUSAL_CHAIN`

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

**Checkpoint 4 — 完整 pipeline 编排（当前）**

详见 [PROJECT_SPEC.md](PROJECT_SPEC.md) 和 [BACKLOG.md](BACKLOG.md)。

## 自动 pipeline（Checkpoint 4）

一条命令跑通 news → semantic_ir → validate → video：

```bash
# Mock 模式（无需 API key）
python -m src.pipeline --auto --mock

# 指定已有 news 文件 + mock LLM
python -m src.pipeline --auto --news outputs/latest/latest_news.json --mock

# 跳过视频导出（快速调试 HTML 渲染）
python -m src.pipeline --auto --mock --no-export

# 真实新闻 + 真实 LLM（需配置 .env）
python -m src.pipeline --auto --source openai_news --profile minimax_m3_openai --repair

# 真实 LLM 但使用已有 news 文件
python -m src.pipeline --auto --news outputs/latest/latest_news.json --profile minimax_m3_openai
```

参数说明：

| 参数 | 作用 |
|---|---|
| `--auto` | 启用完整 auto pipeline |
| `--mock` | 使用 mock LLM，不调用真实 API |
| `--news <path>` | 指定 news JSON，跳过 fetch_news |
| `--source <id>` | 从 sources.yaml 选择新闻源 |
| `--profile <name>` | LLM profile（如 minimax_m3_openai） |
| `--repair` | 校验失败时自动 LLM 修复 |
| `--no-export` | 跳过 output.mp4 导出 |
| `--repair-attempts N` | 最大修复尝试次数（默认 2） |
| `--tts` | 启用 TTS narration 生成 |
| `--tts-profile <name>` | TTS profile（如 mock / minimax_speech） |

**auto pipeline 链路**：
1. `fetch_news`（除非 `--news` 或 `--mock`）
2. `generate_ir --validate`（subprocess）
3. `validate_ir` 再次校验
4. `narration` TTS（仅当 `--tts`，生成 narration.wav + narration_manifest.json）
5. `layout.build_render_ir`
6. `render_html.render_html`
7. `export_video.export_video`（除非 `--no-export`，音频 mux 在此阶段）

**常见失败**：
- `sources.yaml` 仍是占位 URL → `[auto:fetch_news]` 失败
- LLM fake key 401/403 → `[auto:generate_ir]` 失败
- `generate_ir` exit 5 = validation/repair failed → `[auto:generate_ir]` 失败；查看 `outputs/latest/debug_validation_issues.json` 和 `debug_repair_response.txt`
- `semantic_ir` validate failed → `[auto:validate_ir]` 失败
- TTS endpoint 未配置 / voice_id 缺失 → `[auto:tts]` 失败
- FFmpeg / Playwright 缺失 → `[auto:export]` 失败
- FFmpeg audio mux 失败 → `[auto:export]` 失败

**注意**：`semantic_ir.invalid.json` 是调试产物，不进入 pipeline 后续渲染阶段。

## TTS 单人口播（Checkpoint 6）

### Mock TTS 验收（无需真实 API key）

```bash
# 单独生成 narration
python -m src.narration --semantic-ir outputs/latest/semantic_ir.json --profile mock

# 带音频的完整 pipeline
python -m src.pipeline --auto --mock --tts --tts-profile mock
```

TTS 配置在 `config/tts.yaml`，默认 profile 为 `mock`。

### 真实 MiniMax TTS

1. 填入 `.env`：
   ```
   MINIMAX_API_KEY=<your key>
   MINIMAX_TTS_BASE_URL=<your TTS endpoint>
   MINIMAX_TTS_ENDPOINT_PATH=<e.g. v1/t2a_v2>
   MINIMAX_TTS_MODEL=speech-2.8-hd
   MINIMAX_TTS_VOICE_ID=<your voice id>
   ```

2. 运行：
   ```bash
   python -m src.pipeline --auto --mock --tts --tts-profile minimax_speech
   ```

> 注意：本仓库不硬猜 MiniMax TTS endpoint，需要用户提供已跑通的 Voice Lab 配置。

### TTS 产物

```
outputs/latest/audio/beat_001.wav   # 单句音频
outputs/latest/audio/narration.wav  # 拼接后完整音频
outputs/latest/narration_manifest.json  # 音画时间轴 manifest
```

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
