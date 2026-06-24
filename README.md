# chalk-news-video

把一条新闻自动生成黑板风格的讲解动画视频 (output.mp4)。

## 当前 Checkpoint

**Checkpoint 9 — 对话式视觉表现 / 当前 speaker 高亮（当前）**

CP9 在 CP8.1 基础上：
- 新增 `render_ir.dialogue` 字段，驱动 speaker 卡片高亮和 turn 字幕
- 左侧 host 卡片 / 右侧 expert 卡片，底部字幕框
- 当前 turn 时间段内高亮对应 speaker，字幕显示 turn.text
- 不影响单人口播 / 无声模式

```bash
# CP9 双人对话模式（dialogue visual）
python -m src.pipeline --auto --mock --tts --dialogue --dialogue-profile mock_dialogue

# CP9 快速验收（不导出视频）
python -m src.pipeline --auto --mock --tts --dialogue --dialogue-profile mock_dialogue --no-export
```

**CP9 render_ir.dialogue 字段**：

```json
{
  "dialogue": {
    "enabled": true,
    "style": "podcast_overlay_v1",
    "speakers": {
      "host": { "name": "主持人", "role": "questioner", "side": "left" },
      "expert": { "name": "讲解员", "role": "explainer", "side": "right" }
    },
    "turns": [
      {
        "turn_id": "d1", "speaker": "host", "beat_id": "b1",
        "reveal": "title", "text": "...",
        "start": 0.0, "duration": 2.4, "end": 2.4
      }
    ]
  }
}
```

**CP9 限制（明确不做）**：
- 不是 Remotion（CP11）
- 不是数字人（CP11+）
- 不做 lip-sync
- 不破坏 CP8.1 voice mapping

**Checkpoint 9.1 — dialogue visual hardening**：

- `src/dialogue_visual._normalize_style_speakers()`：正确处理 `dialogue_script.style.speakers` list 格式
- `render_ir.dialogue.speakers.*.panel`：新增 panel 布局字段（x/y/w/h），外置到 render_ir
- `template.html`：JS 初始化时从 `DIALOGUE.speakers.host.panel` / `expert.panel` 读取位置，不再硬编码
- `examples/sample.dialogue.custom_speakers.json`：自定义 speaker name 测试 fixture（提问者/分析员）
- speaker name 优先从 `dialogue_script.style.speakers` 读取，支持自定义
- `dialogue.turns` 仍然不含 audio_path / voice_id

**Checkpoint 10 — Theme System V1**：

支持 4 种视觉主题：`chalkboard`（默认）、`podcast`、`research_desk`、`notebook`。

```bash
# 使用 podcast 主题
python -m src.pipeline --auto --mock --tts --dialogue --dialogue-profile mock_dialogue --theme podcast

# 使用 notebook 主题
python -m src.pipeline --auto --mock --tts --tts-profile mock --theme notebook
```

**config/themes.yaml** 定义所有主题的视觉 token：
- background（color, grid_color, type）
- text（title, body, subtitle）
- node（fill, stroke, text）
- edge（stroke, label）
- callout（info/alert/positive fill/stroke/text）
- dialogue（host_accent, expert_accent, panel_fill, subtitle_fill）

**render_ir.theme** 结构：
```json
{
  "id": "podcast",
  "name": "双人播客",
  "background": {"type": "solid", "color": "#0b1020", "grid_color": "#1f2a44"},
  "text": {"title": "#f8fafc", "body": "#cbd5e1", "subtitle": "#f8fafc"},
  "node": {"fill": "#111827", "stroke": "#38bdf8", "text": "#f8fafc", "badge_fill": "#0f172a", "badge_text": "#f8fafc"},
  ...
}
```

**CP10 限制（明确不做）**：
- 不是 Remotion（CP11）
- 不是数字人（CP11+）
- 不做 lip-sync
- 不改 semantic_ir / dialogue_script / dialogue_manifest schema

**Checkpoint 10.1 — Theme System 加固（当前）**：

- `template.html`：`board-bg` rect 使用 `id` 选择，不再用 `querySelector("rect[width]")` 猜测背景 rect
- `background.type = solid`：JS 正确设置 `board-bg fill = BG.color`，不引用 `url(#boardGrid)`
- `background.type = grid`：JS 设置 `board-bg fill = url(#boardGrid)` 并更新 pattern 填充色
- `node.badge_fill` / `node.badge_text`：所有 4 个主题均已配置，提升 index badge 对比度
- `src/theme.py`：`validate_theme()` 基础校验（必填字段、background.type 枚举、颜色格式）
- `src/theme.py`：新增 CLI（`python -m src.theme --theme podcast`）
- `examples/invalid.themes.yaml`：用于手动验收 invalid theme 失败路径
- `--theme not_exist` / `--theme broken` → exit 非 0，列出可用 themes 或 validation 错误
- legacy `--use-sample` 不支持 `--theme`（CP10.1 暂不修，需文档明确）

```bash
# 验证 podcast theme
python -m src.theme --theme podcast

# 验证 invalid theme
python -m src.theme --theme broken --config examples/invalid.themes.yaml

# pipeline 拒绝无效 theme
python -m src.pipeline --auto --mock --theme not_exist --no-export
```

**Checkpoint 11 — Theme Layout System V1（当前）**：

- `config/themes.yaml`：新增 `layout` 段（variant / canvas.safe_margin / title.y / nodes.style/radius/shadow/stroke_width / dialogue.panel_position/w/h/y/subtitle_h/font_size）
- `src/theme.py`：`layout` 校验（variant 枚举、panel 正数）；新增 `apply_theme_layout()` 计算 speaker panel 位置和 subtitle 布局
- `src/pipeline.py`：新增 `apply_theme_layout` 调用（apply_theme 之后）
- `renderer/template.html`：JS 读取 `NODE_LAYOUT` 控制 node 圆角/阴影/线宽；subtitle font-size 从 `render_ir.subtitles.font_size` 读取

**panel_position 布局规则**：

| panel_position | host | expert |
|---|---|---|
| `side` | x=safe_margin, y=panel_y | x=canvas_w-margin-panel_w, y=panel_y |
| `bottom_corner` | x=safe_margin, y=canvas_h-panel_h-20 | x=canvas_w-margin-panel_w, y=canvas_h-panel_h-20 |
| `desk_cards` | x=safe_margin+20, y=panel_y | x=canvas_w-margin-panel_w-20, y=panel_y |

```bash
# podcast 主题（side 布局，panel 更大）
python -m src.pipeline --auto --mock --tts --dialogue --dialogue-profile mock_dialogue --theme podcast

# research_desk（desk_cards 布局）
python -m src.pipeline --auto --mock --tts --dialogue --dialogue-profile mock_dialogue --theme research_desk

# notebook（bottom_corner 布局）
python -m src.pipeline --auto --mock --tts --dialogue --dialogue-profile mock_dialogue --theme notebook
```

**CP11 限制（明确不做）**：
- 不是 Remotion（CP12+）
- 不是数字人（CP12+）
- 不做 lip-sync
- 不改 semantic_ir / dialogue_script / dialogue_manifest schema

## 项目定位

V0.11: News → LLM → semantic_ir → dual-host dialogue → video（含双角色音频）。

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
4. `narration` TTS（仅当 `--tts`，生成 narration.wav + narration_manifest.json 或 dialogue_manifest.json）
5. `layout.build_render_ir`
6. `apply_narration_timing`（仅当 TTS）
7. `apply_dialogue_visual_cues`（仅当 `--dialogue`，CP9 新增）
8. `apply_theme`（CP10 新增，始终执行）
9. `render_html.render_html`
10. `export_video.export_video`（除非 `--no-export`，音频 mux 在此阶段）

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
outputs/latest/audio/narration.wav  # 拼接后完整音频（含 tail_silence）
outputs/latest/narration_manifest.json  # 音画时间轴 manifest
```

## 双人对话（Checkpoint 8）+ CP9 视觉表现

CP8 主路径：semantic_ir → dialogue_script → dialogue_manifest → video。

### Mock 对话验收

```bash
# 1. 生成 dialogue_script（CP7.1 新增）
python -m src.generate_dialogue --semantic-ir outputs/latest/semantic_ir.json --mock --validate

# 2. 生成 dialogue audio（CP8 新方式：--dialogue-profile）
python -m src.narration --dialogue-script outputs/latest/dialogue_script.json \
    --dialogue --dialogue-profile mock_dialogue

# 3. 完整 pipeline（CP8：--dialogue-profile）
python -m src.pipeline --auto --mock --tts --dialogue --dialogue-profile mock_dialogue

# 4. 旧方式（仍支持）
python -m src.pipeline --auto --mock --tts --dialogue \
    --host-profile mock_host --expert-profile mock_expert
```

### dialogue_script.json 字段

| 字段 | 含义 |
|------|------|
| `turns[].speaker` | 该 turn 的发言人（`"host"` 或 `"expert"`） |
| `turns[].beat_id` | 关联的 semantic_ir beat |
| `turns[].function` | hook/question/explain/clarify/transition/summary |
| `turns[].duration_hint` | 估算时长（非真实音频时间） |

### dialogue_manifest.json 字段（CP8 新增字段）

| 字段 | 含义 |
|------|------|
| `turns` | 音频 turn 列表（含 real start/duration/end） |
| `source_dialogue_script.schema_version` | 来源 dialogue_script 版本 |
| `combined_audio_path` | outputs/latest/audio/dialogue.wav |
| `dialogue_profile` | 使用的 dialogue profile 名称（CP8 新增） |
| `speaker_profiles` | host/expert → {profile, voice}（CP8 新增） |

> **CP9**：render_ir.dialogue.turns 不包含 audio_path 或真实 voice_id。
> dialogue_visual.py 从 dialogue_manifest.turns 清洗敏感字段后写入 render_ir.dialogue。

### 旧路径（CP7 compatibility）

```bash
# 使用 semantic_ir.beats[].speaker 的兼容路径
python -m src.pipeline --auto --mock --tts --dialogue-legacy \
    --host-profile mock_host --expert-profile mock_expert
```

### dialogue_script 校验错误码（CP7.2 新增）

| code | 含义 |
|------|------|
| `REVEAL_MISMATCH` | turn.reveal 与 semantic_ir beat 的 reveal 不一致 |
| `MISSING_HOST_TURN` | turns 中没有 speaker='host' 的 turn |
| `MISSING_EXPERT_TURN` | turns 中没有 speaker='expert' 的 turn |
| `UNKNOWN_STYLE_SPEAKER` | turn.speaker 不是 style.speakers 中定义的 id |
| `DUPLICATE_STYLE_SPEAKER` | style.speakers 中有重复的 speaker id |
| `MISSING_STYLE_SPEAKERS` | style.speakers 为空或缺失 |
| `INVALID_SPEAKER` | turn.speaker 不是 'host' 或 'expert' |
| `UNKNOWN_BEAT_ID` | turn.beat_id 在 semantic_ir 中不存在 |
| `BEAT_NOT_COVERED` | 有 semantic_ir beat 没有被任何 turn 覆盖 |
| `JSONSCHEMA_ERROR` | JSON Schema 校验失败 |

### narration_manifest.json 字段说明

| 字段 | 含义 |
|------|------|
| `speech_duration` | 最后一个 beat 的 end（不含尾静音） |
| `tail_silence` | 追加的尾静音秒数（默认 0.5s） |
| `total_duration` | speech_duration + tail_silence（最终音频时长） |
| `sample_rate` | 来自 TTS provider（非硬编码） |
| `beats[].start/duration/end` | 每个 beat 的真实音频时间 |

CP6.1 时间优先级：`narration_manifest` > `pace` 估算。

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
