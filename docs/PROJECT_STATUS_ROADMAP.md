# 项目状态与路线图（Status & Roadmap）

> 快照日期：2026-06-26
> 定位：本地单人「新闻 → 16:9 短视频」生产工作台。
> 本文档是**活文档**，记录当前架构、已交付能力、完成度评估与剩余待实现项。

---

## 1. 当前架构

```
新闻文本
  → 内容生成： LLM 拆解（默认, src/llm_episode.py） │ 规则兜底（src/news_source_pipeline.py）
  → episode_template_v1 contract（含每段口播文稿 narration）
  → 渲染：render_episode_html.py（5 种风格，EPISODE_STYLE_RENDERERS 注册表，统一 seek 契约）
  → 分发：
       · 预览（preview-html → iframe，所见即所得）
       · 真人口播（episode_tts.py → MiniMax TTS → wav）
       · 导出 MP4 16:9（export_video.py：Playwright 逐帧 → ffmpeg，+音频混流+定格补足）
```

### 关键端点（FastAPI, src/server.py）
| 端点 | 作用 |
|---|---|
| `POST /api/episode/llm-contract` | 新闻 → LLM → contract（失败自动回退规则版） |
| `POST /api/episode/source-contract` | 新闻 → 规则 → contract |
| `POST /api/episode/preview-html` | contract+style → 服务端渲染 HTML（与导出同一渲染器；`persist` 区分临时/保存） |
| `POST /api/episode/tts-audio` | contract → 真人口播 wav（优先读 LLM 文稿） |
| `POST /api/episode/export` / `GET …/exports/{id}` | 异步导出 MP4 + 轮询 |
| `GET /api/episode/export/capabilities` | 可出片风格 + 尺寸/帧率上限（默认 1280×720） |
| `GET /api/hot-ai-news` | 候选新闻（外网不通时返回示例兜底） |

### 前端入口（同源）
- `/` 极简页（默认）：粘贴新闻 → 选风格 → 选比例 → 预览/生成（`web/simple.*`）
- `/showcase` 能力一览：5 风格实时样例 + 能力矩阵
- `/advanced` 高级工作台：老 chalk 管线（5000 行 `web/app.js`，平行系统）

### 5 种可出片风格（`render_episode_html.py`，均 16:9 铺满式）
`breaking_news_v1`（快讯大屏，卡通主播，已重做 16:9）· `data_dashboard_v1`（数据仪表盘）· `timeline_daily_v1`（时间线日报）· `podcast_cards_v1`（播客卡片）· `research_briefing_v1`（研究室简报）

### 配置 / 基础设施
`config/llm.yaml`（MiniMax-M3 默认 / MiMo）· `config/tts.yaml`（MiniMax / mock）· `config/themes.yaml` · `.env`（密钥）· `prompts/news_to_episode.md`（新，LLM 拆解）

### ⚠ 平行 / 遗留系统（仅 advanced 页用，待收敛）
旧单条 pipeline：`src/pipeline.py` + `generate_ir`（`prompts/news_to_semantic_ir.md`）+ `render_html` → semantic_ir/render_ir → chalk 16:9 动画；`web/theme_samples/*.html`（10+ 静态 16:9 样板，未接导出）。

---

## 2. 本会话已交付（未补正式 CP 文档，编号为约定俗成）

- **CP56 真人口播**：`episode_tts.py` + `/api/episode/tts-audio`，接 MiniMax，导出可混流；音频比画面长时**定格补足**。（模块现标注「实验」，待转正）
- **CP58 风格库**：5 种风格全部可出片（注册表 + 共享 seek 契约）。
- **CP59 预览==导出**：`/api/episode/preview-html` 用同一 Python 渲染器；删掉前端 ~1253 行重复 JS 渲染器。
- **CP60 16:9 主格式**：默认翻为 1280×720；4 风格改铺满式弹性布局；`breaking_news_v1` 重做成 16:9（主播左 / 头条+快讯右）。
- **CP61 真实 LLM 内容**：`src/llm_episode.py` + `/api/episode/llm-contract`，新闻 → 真正拆解 + 每段口播文稿；`build_narration_script` 优先读 LLM 文稿；极简页「用 AI 理解新闻」开关默认开；失败回退规则版。

测试：`scripts/smoke_test_render_episode_html.py`、`scripts/test_episode_export_e2e.py`、`scripts/test_llm_episode.py` 均通过。

---

## 3. 完成度评估

| 标准 | 完成度 | 说明 |
|---|---|---|
| 本地单人「新闻→短视频」MVP 闭环 | **~75–80%** | 核心通了：粘贴→AI 拆解→真人口播→16:9 成片 |
| Kurzgesagt 式插画解说愿景 | **~35–40%** | 内容/口播/风格有了，但非「插画分镜叙事」 |

---

## 4. 剩余待实现（优先级 + 粗估工作量）

> 🔴 高价值/高难 · 🟡 中 · ⚪ 低/卫生

### A. 内容 / 视觉上限（决定"好看好懂"）
- ⚪→🟡 **字幕轨（烧录字幕）** —— 未做，静音观看场景缺。**低成本高回报，建议优先。**【中】
- 🟡 **9:16 竖屏版面打磨** —— fill 风格中部偏空、快讯卡偏窄（窄屏改竖向堆叠 + 垂直居中）。【小】
- ⚪ **背景音乐 / 音效** —— 未做。【小-中】
- 🔴 **插画 / 分镜动画（Kurzgesagt 方向）** —— 未做，**卡在没有可用文生图服务**；需「素材组件库 + 大模型编排」，非纯模型生成。【大】

### B. 信息源
- 🟡 **自动新闻采集（RSS / 来源 watcher）** —— 未做；本环境外网受限，需先验证可连通性。【中】
- 🟡 **事实核查** —— 现在 facts guard 只提示「请人工核实」，不自动查证。【中】

### C. 工程 / 性能 / 卫生
- 🟡 **导出提速** —— 16:9 + 2× 超采样逐帧截 2560×1440 × 421 帧，单条偏慢、并发更慢。可降超采样/控并发。【小】
- 🟡 **两套渲染系统收敛** —— 老 semantic_ir/chalk + theme_samples 仅 advanced 用，长期应合一。【中】
- ⚪ **死代码清理** —— breaking_news 重做后 `subtitle_bar_html/timeline_html/closing_html/opening_label_html` 等未用变量；`/api/episode/mock-html` 端点已无人调用。【小】
- ⚪ **极简页支持多条新闻** —— 目前单条（inline_text→1 card 起）；多条合集仅 advanced。【小-中】
- ⚪ **补 CP 文档 + 测试、TTS 从「实验」转正、清理 `outputs/` 测试产物**。【小】

### D. 产品化（MVP 定位明确不做）
- ⚪ 多用户 / 账号 / 云存储 / 计量 —— 暂缓。【极大】

---

## 5. 建议下一步顺序

1. **字幕轨**（A，低成本高回报）—— 复用 contract 里的 narration + TTS 分段时长生成 SRT/烧录。
2. **导出提速**（C）—— 把 16:9 超采样从 2× 降到 1.5×/可配，或限制并发。
3. **9:16 版面打磨**（A）。
4. 之后再评估 **插画方向**（先确认文生图能力）与 **自动采集**（先验证外网）。
5. 穿插做 **卫生项**（死代码、CP 文档、测试产物清理、TTS 转正）。
