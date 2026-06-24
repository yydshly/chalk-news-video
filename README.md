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

**Checkpoint 12 — Local Web Studio V1（当前）**：

本地 Web 界面，通过浏览器访问 http://127.0.0.1:8777 。

```bash
# 安装依赖后启动
pip install fastapi uvicorn
python -m src.server --host 127.0.0.1 --port 8777
```

**API 路由**：

| 方法 | 路由 | 说明 |
|---|---|---|
| GET | `/` | Web Studio 主页 |
| GET | `/app.js` | 前端 JS |
| GET | `/style.css` | 样式 |
| GET | `/api/health` | 健康检查 |
| GET | `/api/themes` | 可用主题列表 |
| POST | `/api/generate` | 触发视频生成 |
| GET | `/api/artifacts/{name}` | 获取 JSON artifact |
| GET | `/outputs/latest/{filename}` | 预览 animation.html / output.mp4 |

**POST /api/generate 请求体**：

```json
{
  "mode": "sample",
  "theme": "podcast",
  "dialogue": true,
  "mock": true,
  "no_export": false
}
```

mode 也支持 `"text"`，此时需提供 `title` 和 `news_text`。

**POST /api/generate 返回**：

```json
{
  "ok": true,
  "exported": true,
  "output_mp4": "/outputs/latest/output.mp4",
  "animation_html": "/outputs/latest/animation.html",
  "render_ir": "/api/artifacts/render_ir",
  "semantic_ir": "/api/artifacts/semantic_ir",
  "dialogue_script": "/api/artifacts/dialogue_script"
}
```

当 `no_export=true` 时：

```json
{
  "ok": true,
  "exported": false,
  "output_mp4": null,
  "animation_html": "/outputs/latest/animation.html",
  ...
}
```

| 字段 | 说明 |
|------|------|
| `exported` | true = MP4 已导出；false = 仅预览 animation.html |
| `output_mp4` | exported=true 时为 `/outputs/latest/output.mp4`；exported=false 时为 `null` |

**CP12 限制（明确不做）**：
- 不做登录 / 计费 / 云部署
- 不做异步任务队列（CP13）
- 不是 Remotion（CP12+）
- 不暴露 .env 或真实 API key

**Checkpoint 13 — Async Jobs / Progress Stream（当前）**：

异步任务 + SSE 进度推送，前端不再阻塞等待。

```bash
python -m src.server --host 127.0.0.1 --port 8777
```

**新增 API 路由**：

| 方法 | 路由 | 说明 |
|---|---|---|
| POST | `/api/jobs` | 创建异步生成任务 |
| GET | `/api/jobs/{job_id}` | 查询任务状态和结果 |
| GET | `/api/jobs/{job_id}/events` | SSE 进度流 |

**POST /api/jobs 请求体**：同 `/api/generate`

```json
{
  "mode": "sample",
  "theme": "podcast",
  "dialogue": true,
  "mock": true,
  "no_export": false
}
```

**POST /api/jobs 返回**：

```json
{
  "ok": true,
  "job_id": "job_abc123",
  "status_url": "/api/jobs/job_abc123",
  "events_url": "/api/jobs/job_abc123/events"
}
```

**GET /api/jobs/{job_id} 返回**：

```json
{
  "ok": true,
  "job": {
    "job_id": "job_abc123",
    "status": "succeeded",
    "stage": "succeeded",
    "message": "完成",
    "progress": 100,
    "created_at": "...",
    "updated_at": "...",
    "result": { "ok": true, "exported": true, ... },
    "error": null
  }
}
```

**SSE 事件类型**：

| 事件 | 说明 |
|------|------|
| `progress` | 进度更新，含 stage/message/progress |
| `done` | 任务成功，含 result |
| `error` | 任务失败，含 error |

**阶段进度映射**：

| stage | progress | 说明 |
|-------|----------|------|
| `queued` | 0 | 任务已创建 |
| `preparing_input` | 5 | 准备输入 |
| `semantic_ir` | 25 | 生成 semantic_ir |
| `validate_ir` | 35 | 校验 |
| `dialogue_script` | 40 | 生成对话脚本 |
| `tts` | 55 | 生成 TTS |
| `layout` | 62 | 计算布局 |
| `render_html` | 82 | 渲染 HTML |
| `export_video` | 92 | 导出 MP4 |
| `succeeded` | 100 | 完成 |

**Job Store**：
- 内存存储，单用户本地工具
- 服务重启后任务记录丢失
- 不做数据库 / Redis / Celery

**同步兼容路由**：
- `POST /api/generate` 仍保留，同步阻塞返回（CP12.1 兼容）

**CP13 限制（明确不做）**：
- 不做多用户 / 任务隔离
- 不做数据库 / Redis / Celery
- 不做云部署
- 不做 Remotion（CP17）

**Checkpoint 14 — Job History / Output Isolation**：

每个任务拥有独立输出目录，不再相互覆盖。

```bash
python -m src.server --host 127.0.0.1 --port 8777
```

**新增 API 路由**：

| 方法 | 路由 | 说明 |
|---|---|---|
| GET | `/api/history` | 返回历史任务列表 |
| GET | `/api/jobs/{job_id}/artifacts/{name}` | 获取 job 专属 artifact JSON |
| GET | `/outputs/jobs/{job_id}/{filename}` | 预览 job 专属文件 |

**GET /api/history 返回**：

```json
{
  "ok": true,
  "items": [
    {
      "job_id": "job_abc123",
      "status": "succeeded",
      "stage": "succeeded",
      "theme": "podcast",
      "dialogue": true,
      "exported": true,
      "created_at": "...",
      "animation_html": "/outputs/jobs/job_abc123/animation.html",
      "output_mp4": "/outputs/jobs/job_abc123/output.mp4"
    }
  ]
}
```

**Job 输出目录结构**：

```
outputs/jobs/job_xxx/
├── meta.json
├── input_news.json
├── semantic_ir.json
├── dialogue_script.json
├── dialogue_manifest.json
├── render_ir.json
├── animation.html
└── output.mp4
```

**meta.json 示例**：

```json
{
  "job_id": "job_xxx",
  "status": "succeeded",
  "theme": "podcast",
  "mode": "sample",
  "dialogue": true,
  "mock": true,
  "exported": true,
  "title": "...",
  "summary": "...",
  "duration": 31.167,
  "error": null,
  "artifacts": {
    "animation_html": "/outputs/jobs/{job_id}/animation.html",
    "output_mp4": "/outputs/jobs/{job_id}/output.mp4",
    "render_ir": "/api/jobs/{job_id}/artifacts/render_ir",
    "semantic_ir": "/api/jobs/{job_id}/artifacts/semantic_ir",
    "dialogue_script": "/api/jobs/{job_id}/artifacts/dialogue_script",
    "dialogue_manifest": "/api/jobs/{job_id}/artifacts/dialogue_manifest",
    "meta": "/api/jobs/{job_id}/artifacts/meta"
  }
}
```

**pipeline --output-dir**：

```bash
python -m src.pipeline --auto --mock --output-dir outputs/jobs/job_xxx
```

所有产物写入指定目录，不影响 `outputs/latest`（保留 CP12.1 兼容）。

**历史 Gallery**：
- 前端新增「历史作品」tab
- 展示所有任务的 job_id / theme / status / exported
- 支持预览 animation / MP4 / artifacts
- 服务重启后内存中的历史记录从 meta.json 恢复

**CP14 限制（明确不做）**：
- 不做数据库持久化（CP14+）
- 不做 job 删除接口
- 不做多用户隔离

**Checkpoint 14.1 — Job History 加固（当前）**：

- `.gitignore` 简化：`outputs/jobs/*` 整体忽略，只追踪 `.gitkeep`
- `outputs/jobs/.gitkeep` 被 Git 追踪，job_* 生成物不追踪
- `meta` 加入 `ALLOWED_ARTIFACTS`，`/api/jobs/{job_id}/artifacts/meta` 可用
- `/api/history` 支持磁盘扫描，服务重启后可从 meta.json 恢复历史
- `/api/jobs/{job_id}/artifacts/{name}` 和 `/outputs/jobs/{job_id}/{filename}` 重启后仍可访问
- 新增 `_resolve_job_output_dir` 安全 helper：job_id 格式校验 + 路径穿越防护
- meta.json 增强：包含 artifacts 映射、duration、title、summary

**CP14.1 验收**：
- `git status` 干净（outputs/jobs/ 下无 untracked）
- `git ls-files outputs/jobs/` 只显示 `.gitkeep`
- 服务重启后 `/api/history` 包含重启前的 job
- `/api/jobs/{job_id}/artifacts/meta` 返回完整 meta.json
- invalid theme job 的 meta.json 正确记录 failed 状态

**Checkpoint 15 — Real Provider 配置（当前）**：

前端新增 Provider 配置区，支持选择 LLM 和 TTS provider。

```bash
python -m src.server --host 127.0.0.1 --port 8777
```

**新增 API 路由**：

| 方法 | 路由 | 说明 |
|---|---|---|
| GET | `/api/providers` | 返回 LLM/TTS provider 状态（ready + missing_env） |

**GET /api/providers 返回**：

```json
{
  "ok": true,
  "llm": [
    {
      "id": "mock",
      "name": "Mock",
      "ready": true,
      "type": "mock",
      "missing_env": []
    },
    {
      "id": "minimax_m3_openai",
      "name": "MiniMax M3 OpenAI",
      "ready": false,
      "type": "openai_compatible",
      "missing_env": ["MINIMAX_API_KEY"]
    }
  ],
  "tts": [
    {
      "id": "mock_dialogue",
      "name": "Mock Dialogue",
      "ready": true,
      "type": "mock",
      "missing_env": []
    },
    {
      "id": "minimax_dialogue",
      "name": "MiniMax Dialogue",
      "ready": false,
      "type": "minimax",
      "missing_env": ["MINIMAX_TTS_HOST_VOICE_ID", "MINIMAX_TTS_EXPERT_VOICE_ID"]
    }
  ]
}
```

**GenerateRequest 扩展**：

```json
{
  "llm_provider": "mock" | "minimax_m3_openai" | "mimo_v25_pro_openai",
  "tts_provider": "mock" | "mock_dialogue" | "minimax_dialogue",
  "repair": true,
  "repair_attempts": 2
}
```

**兼容规则**：
- `llm_provider` 未传时：mock=true 用 mock，否则默认 minimax_m3_openai
- `tts_provider` 未传时：dialogue=true 用 mock_dialogue，否则用 mock
- `mock` 字段可保留，新前端优先使用 `llm_provider`

**安全保证**：
- API key 值和 voice_id 值永不返回给前端
- 只显示缺失的环境变量名
- job request 记录 provider id，不记录 secret

**CP15 验收**：
- `/api/providers` 只显示 env var name，不显示 value
- mock job 成功
- real provider 缺配置时 failed job error 清晰但不泄露 secret
- 前端 Provider 区显示 ready/missing_env 状态

**Checkpoint 15.1 — Real Provider Entry（当前）**：

- `/api/jobs` 支持 `mock=false`，不再直接拒绝
- provider readiness 检查：`_validate_provider_selection()` 在 job 创建前验证
- 缺必需 env 时创建 failed job：`meta.json` + history 可见 + SSE error 事件
- `_collect_required_env_from_profile()`：只有 profile 缺少默认值时才要求 env var
- `_dedupe_keep_order()`：missing_env 去重
- `/api/generate` 保持同步兼容，仅支持 mock

**CP15.1 验收**：
- `minimax_m3_openai` 只缺 `MINIMAX_API_KEY` 时 `missing_env` 只包含 `MINIMAX_API_KEY`
- `minimax_dialogue` missing_env 去重后无重复
- 未配置真实 key 时 `curl -X POST /api/jobs -d '{"mock":false,"llm_provider":"minimax_m3_openai"}'` 创建 failed job
- failed job 在 `/api/history` 可见，`/api/jobs/{id}/artifacts/meta` 可读
- failed job meta 不包含任何 secret value

**Checkpoint 15.2 — Real LLM/TTS E2E 验证（当前）**：

- `_validate_provider_selection()`：unknown provider 时立即返回错误，不走后续流程
- 真实 LLM provider（minimax_m3_openai）+ mock TTS（mock_dialogue）E2E 验证
- 验证命令包含 `--profile minimax_m3_openai --repair --repair-attempts 2 --dialogue-profile mock_dialogue`
- 验证命令不包含 API key / voice_id / sk-
- 缺 env 时 failed job error 只包含 env var name，不包含 value
- unknown provider 时创建 failed job，error 包含 "Unknown LLM/TTS provider"

**CP15.2 验收**：
- unknown provider `curl -X POST /api/jobs -d '{"llm_provider":"not_exist","tts_provider":"mock_dialogue","mock":false}'` → failed job + error 包含 "Unknown LLM provider"
- real LLM + mock TTS：job succeeded，`semantic_ir.json` / `dialogue_script.json` 由真实 LLM 生成
- real LLM 缺 env：failed job error 只包含 `MINIMAX_API_KEY`（无 value）
- `/api/providers` 显示 provider ready 状态正确，missing_env 去重
- API key / voice_id 不泄露到任何 API 响应或 artifact

**Checkpoint 15.2.1 — Web Studio .env 自动加载（当前）**：

- `python -m src.server` 启动时自动加载项目根目录 `.env`
- 使用 `python-dotenv`，`override=False`（系统环境变量优先）
- `.env` 不存在时不报错
- 加载后 `/api/providers` 能读取 `.env` 中配置的 `MINIMAX_API_KEY` 等变量
- API 不返回 key value，只显示 missing_env 变量名
- `.env` 不提交 Git（已加入 .gitignore）

**CP15.2.1 验收**：
- 启动 server 后 `curl http://127.0.0.1:8777/api/providers` 显示 `minimax_m3_openai.ready=true`（如果 .env 已配置）
- `minimax_m3_openai` 的 `missing_env=[]`（不报缺 MINIMAX_API_KEY）
- API 响应中不出现真实 key / sk-

**Checkpoint 15.2.2 — 真实 LLM 失败诊断增强（当前）**：

- pipeline.py：generate_ir 失败时打印 validation issues 摘要（前 5 条）到 stderr
- pipeline.py：打印 debug_validation_issues.json / semantic_ir.invalid.json / debug_repair_response.txt 路径
- server.py：`_redact_secret_text()` helper — 自动脱敏 API key / voice_id
- server.py：改进错误提取 — 保留所有 `[auto:]` 行（最多 5 条）
- server.py：新增 `GET /api/jobs/{job_id}/debug` — 返回 validation issues 摘要
- debug prompt/response 不走普通 artifact 白名单

**CP15.2.2 验收**：
- 真实 LLM 失败时 job error 包含 validation issues 摘要（前 5 条）
- `GET /api/jobs/{job_id}/debug` 返回 validation_issues 列表（最多 10 条）
- error 文本中 API key 已脱敏（`sk-` → `[REDACTED]`，`MINIMAX_API_KEY=...` → `MINIMAX_API_KEY=[REDACTED]`）
- debug 文件不通过普通 artifact API 暴露

**Checkpoint 15.2.3 — 真实 LLM semantic_ir 收敛与 job-scoped debug（当前）**：

- generate_ir debug 文件写入 job output_dir（不再是 `outputs/latest`）
- pipeline.py 从 job output_dir 读取 debug_validation_issues.json
- server.py `GET /api/jobs/{job_id}/debug` 从 job output_dir 读取
- `_apply_deterministic_repairs()`：自动为 UNREVEALED_EDGE / UNREVEALED_NODE 补齐 beats
- prompts 更新：明确所有 edge/node/callout id 必须在 beats[].reveal 中出现
- prompts 强调 `beats[].reveal` 是字符串不是数组

**CP15.2.3 验收**：
- debug 文件出现在 `outputs/jobs/{job_id}/`（不是 outputs/latest）
- `GET /api/jobs/{job_id}/debug` 返回 debug_files 和 validation_issues 摘要
- UNREVEALED_EDGE 自动修复： deterministic repair 后 validation 通过
- 真实 LLM + mock TTS E2E job succeeded

**Checkpoint 15.2.4 — 真实新闻样例 + real LLM E2E 通过（当前）**：

- `examples/real_news_fixture.json`：真实新闻风格 fixture（AI 安全评测报告）
- server.py：支持 `mode=real_fixture`，使用 `examples/real_news_fixture.json`
- `src/llm/json_utils.py`：`extract_json_object` 增强容错，使用 brace counting 提取 JSON

**CP15.2.4 验收**：
- `mode=real_fixture` + minimax_m3_openai + mock_dialogue → job succeeded
- semantic_ir / dialogue_script / dialogue_manifest / render_ir / animation.html 全部生成
- `examples/sample_news.json` 仅作为字段结构示例，不用于真实 LLM 测试

**Checkpoint 15.2.5 — 热门 AI 新闻发现层 + hot_ai E2E（当前）**：

- `src/fetch_hot_ai_news.py`：从 HN Firebase API 获取 AI 相关热门新闻
  - 关键词过滤：至少匹配一个 AI 相关关键词（OpenAI/LLM/Claude/Gemini 等）
  - 热度评分：`points * 1.0 + comments * 2.0 + recency_bonus + keyword_bonus`
  - 输出 `hot_ai_candidates.json`（20 条候选）
  - 输出 `latest_news.json`（top 1，选中新闻）
  - 不抓取全文（无 paywall bypass、无版权内容）
- server.py：`mode=hot_ai` 支持，调用 `fetch_hot_ai_news` 生成最新新闻
- ALLOWED_ARTIFACTS 新增 `hot_ai_candidates`、`latest_news`

**CP15.2.5 验收**：

- `python -m src.fetch_hot_ai_news --source hn --hours 72 --limit 20 --output outputs/latest/latest_news.json --candidates-output outputs/latest/hot_ai_candidates.json` → 候选数量 > 0
- `mode=hot_ai` + minimax_m3_openai + mock_dialogue → job succeeded
- hot_ai_candidates.json / latest_news.json / semantic_ir / dialogue_script / render_ir / animation.html 全部生成
- latest_news.title 是真实热门 AI 新闻标题（关键词过滤生效）
- 不抓取付费墙全文、不绕过反爬、不提交版权新闻全文

**Checkpoint 15.2.6 — Hot AI News 关键词质量优化（当前）**：

- 边界感知关键词匹配：避免 "AI" 误匹配 Trains/rain/main 等非 AI 单词
- STRONG/WEAK 关键词分层：
  - STRONG（高精度）：OpenAI/Anthropic/Claude/Gemini/GPT/LLM/GPU 等，需 ≥1 个即可入选
  - WEAK（低精度）：AI/model/agent 等，需 ≥2 个才能入选
- 词边界正则：`(?<![A-Za-z0-9])AI(?![A-Za-z0-9])`
- 短语匹配：AI safety / machine learning / neural network 等多词短语
- 关键词加分：strong=+15 each (max 45)，weak=+5 each (max 15)
- rank_reason 增强：显示 strong_matched/weak_matched/kw_bonus
- 回归测试：`python tests/test_fetch_hot_ai_news.py`

**CP15.2.6 验收**：

- `python tests/test_fetch_hot_ai_news.py` → 9 passed, 0 failed
- Trains/rain/main/available 等不再因 AI 子串误入选
- 候选列表中无明显非 AI 新闻（如 "Trains halted across Germany"）
- `mode=hot_ai` + minimax_m3_openai + mock_dialogue → job succeeded

**Checkpoint 15.3 — 真实 MiniMax TTS E2E（进行中）**：

- `src/tts/minimax_tts_provider.py`：MiniMax TTS provider 实现
- `config/tts.yaml`：`minimax_dialogue` dialogue profile（host/expert voice 分离）
- `src/tts/client.py`：支持 dialogue_profiles 解析
- `src/narration.py`：支持 `--dialogue-profile minimax_dialogue`
- env vars 缺失：MINIMAX_TTS_BASE_URL / ENDPOINT_PATH / VOICE_ID / HOST_VOICE_ID / EXPERT_VOICE_ID
- `.env.example` 已更新（CP15.3）

**CP15.3 验收（待 env 配置）**：

- `/api/providers` 中 `minimax_dialogue.ready=true`
- `mode=hot_ai` + minimax_m3_openai + minimax_dialogue → job succeeded
- audio 文件在 `outputs/jobs/{job_id}/audio/` 生成
- dialogue_manifest.json 含 timing（turn_id/speaker/start/duration/end）
- render_ir.dialogue.enabled == true
- animation.html 含真实双人音频
- API key / voice_id 不泄露

## CP15.4 — 口播时长控制与 turns 控制（CP15.4）

**目标**：hot_ai 新闻生成的视频默认控制在 45-60 秒内，避免 dialogue_script 过长、TTS 成本过高、视频节奏拖慢。

**新增配置**：
- `--target-duration-sec`（CLI/API）：目标口播总时长，默认 60 秒
- `--max-turns`（CLI/API）：最大 dialogue turns 数，默认 14

**新增参数（GenerateRequest）**：
```python
target_duration_sec: int | None = 60  # 目标时长
max_turns: int | None = 14           # 最大 turns
```

**新增输出**：
- `dialogue_budget.json`：口播预算信息
  - `target_duration_sec`、`max_turns`、`max_chars_per_turn`
  - `before_turns` / `after_turns`、`before_chars` / `after_chars`
  - `compressed`：是否被压缩

**压缩策略**：
1. 保留前 2 个 turns（hook + first explain）
2. 保留最后 1-2 个 conclusion turns
3. 中间 turns 合并或截断
4. 单个 turn 超过 max_chars_per_turn（42）时截断
5. 保证至少 6 turns

**TTS 成本保护**：
- 真实 TTS（minimax_dialogue）前检查 dialogue_script 规模
- 如果 turns > 18 或 chars > 800：fail fast，提示降低目标或改用 mock
- 不直接发起大量 TTS 请求

**Prompt 层控制**：
- semantic_ir_to_dialogue.md 新增 Duration Budget 章节
- 要求 LLM 生成 10-14 turns，每 turn 20-42 个中文字符
- 只讲一个主线，不展开过多背景

**CP15.4 验收**：
- `mode=hot_ai` + minimax_m3_openai + mock_dialogue → job succeeded
- dialogue_script turns <= 14
- dialogue_manifest.total_duration <= 65 秒（mock 下允许近似）
- render_ir.total_duration == dialogue_manifest.total_duration
- animation.html 存在
- dialogue_budget.json 存在
- 如果压缩发生，compressed=true
- validation 无 error

## CP15.5 — 选题可讲性评分（Story Worthiness Scoring）

**目标**：HN 热门不等于适合做视频。需要按"是否适合生成 45-60 秒讲解视频"排序。

**背景问题**：
- 过于技术碎片、普通观众难懂
- 缺少因果链
- 标题太短，信息不足
- 只有工具发布，没有影响解释
- 过于冷门，不适合作为"今日 AI 新闻视频"

**新增评分维度** `story_score`（0-100）：

| 维度 | 分值 | 说明 |
|------|------|------|
| 大公司/公众认知 | +25 | OpenAI / Anthropic / Google / Meta / Nvidia / Apple / xAI / Hugging Face 等 |
| 模型/产品发布 | +20 | GPT / Claude / Gemini / Llama / Sora / Copilot / agent / benchmark 等 |
| 明确问题/冲突 | +20 | crisis / controversy / outage / safety / risk / lawsuit / ban / cost 等 |
| 影响面 | +15 | users / developers / enterprises / market / industry / regulation 等 |
| 可视化潜力 | +10 | chart / benchmark / report / ranking / comparison / architecture 等 |
| 标题长度 20-120 字符 | +10 | 信息密度充足 |
| 标题过短 <=8 字符 | -15 | 信息不足 |
| Show HN 无大公司 | -10 | 过度小众 |
| 纯论文/模型名无影响 | -10 | 缺 impact/conflict |

**最终排序**：`final_score = hotness_score + story_score`

**新增输出字段**：
- `hot_ai_candidates.json`：每条 candidate 含 `hotness_score` / `story_score` / `final_score` / `story_reasons[]` / `story_flags{}`
- `latest_news.json`：含 `hotness_score` / `story_score` / `final_score` / `story_reasons[]` / `story_flags{}`
- `content` 中新增 Story Worthiness 小节

**low_story_score 警告**：如果最高分新闻的 `story_score < 30`，输出 warning 但不失败。

**CP15.5 验收**：
- hot_ai_candidates.json 每条含 story_score / hotness_score / final_score
- latest_news.json 含 story_score / final_score
- selected news 是明显适合视频讲解的 AI 新闻
- semantic_ir validation PASS
- dialogue_script turns <= 14
- dialogue_manifest.total_duration <= 65
- animation.html 存在
- 不泄露 API key / voice_id

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
