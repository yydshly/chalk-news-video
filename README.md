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

  mock:                         # 仅供本地 / CI 测试，不代表真实 LLM 效果
    provider: mock
    protocol: mock
    model: "mock"
    temperature: 0.0
    max_tokens: 4000
    timeout_seconds: 1
```

支持协议：
- `openai_compatible` → POST `{base_url}/chat/completions`
- `anthropic_messages` → POST `{base_url}/messages`
- `mock` → 本地确定性生成

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

# 2) Mock：无 key 本地测试
python -m src.generate_ir --news examples/sample_news.json --mock

# 3) 真实 MiniMax
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

## 产物

```
outputs/latest/debug_llm_prompt.txt      完整 prompt（system + user）
outputs/latest/debug_llm_response.txt    LLM 原始响应 / mock 输出
outputs/latest/semantic_ir.json          解析后的 semantic_ir
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

## 当前 Checkpoint

详见 [PROJECT_SPEC.md](PROJECT_SPEC.md) 和 [BACKLOG.md](BACKLOG.md)。
