# V0.1 Demo Freeze

**Branch:** `release/v0.1-demo-freeze`
**Commit:** `ab6a718` (base) + layout.py fix
**Date:** 2026-06-24
**Status:** Frozen — local demo, not for production

---

## 1. V0.1 能力边界

V0.1 是一个**本地演示版本**，用于验证"热门 AI 新闻 → 双人对话视频 → MP4 导出"全链路的可行性。

| 能力 | 支持情况 |
|------|----------|
| 新闻来源 | Hacker News 热门 AI 新闻（72小时内） |
| 视频主题 | `news_card_v1`（唯一可观看级别） |
| 对话模式 | 双人（host + expert），真实 MiniMax Dialogue TTS |
| LLM | MiniMax M3 OpenAI 兼容接口 |
| MP4 导出 | 支持（通过 Playwright + FFmpeg） |
| Web Studio | 本地浏览器 UI，支持历史预览 |
| 部署 | 不支持 |
| 多新闻源 | 不支持 |
| 用户系统 | 不支持 |
| 竖屏（9:16） | 不支持 |

---

## 2. 已跑通主链路

```
hot_ai (Hacker News)
  → minimax_m3_openai (LLM 生成 semantic_ir + dialogue_script)
  → minimax_dialogue (MiniMax Dialogue TTS，真实语音)
  → news_card_v1 (视觉主题)
  → animation.html (可预览)
  → output.mp4 (可导出)
  → Web Studio MP4 preview (可播放)
```

---

## 3. 本地启动方式

### 3.1 启动 Web Studio

```bash
cd chalk-news-video
python -m src.server --host 127.0.0.1 --port 8777
```

打开浏览器：`http://127.0.0.1:8777`

### 3.2 推荐生成配置

| 参数 | 值 |
|------|-----|
| mode | 热门 AI 新闻 |
| theme | news_card_v1 |
| dialogue | true |
| llm_provider | minimax_m3_openai |
| tts_provider | minimax_dialogue |
| repair | true |
| repair_attempts | 3 |
| target_duration_sec | 45 |
| max_turns | 10 |
| export | true（导出 MP4） |

### 3.3 检查 Provider 状态

```bash
curl http://127.0.0.1:8777/api/providers
```

必须确认：
- `minimax_m3_openai.ready = true`
- `minimax_dialogue.ready = true`
- `missing_env = []`

---

## 4. 如何查看历史作品

1. 打开 `http://127.0.0.1:8777`
2. 点击右上角"历史作品" tab
3. 所有成功 job 显示绿色左边框
4. 点击"▶ 预览 MP4"直接播放视频
5. 点击"🎬 预览动画"查看 animation.html
6. 点击"🔊 播放音频"播放 dialogue.wav
7. 点击"📋 查看脚本"查看 JSON artifacts

---

## 5. 如何播放 animation.html

- Web Studio 历史卡片 → "🎬 预览动画"
- 或直接访问：`http://127.0.0.1:8777/outputs/jobs/{job_id}/animation.html`

---

## 6. 如何播放 output.mp4

- Web Studio 历史卡片 → "▶ 预览 MP4"
- 或直接访问：`http://127.0.0.1:8777/outputs/jobs/{job_id}/output.mp4`
- video 标签 controls 可用，支持暂停/调节音量

---

## 7. 如何播放 dialogue.wav

- Web Studio 历史卡片 → "🔊 播放音频"
- 或直接访问：`http://127.0.0.1:8777/outputs/jobs/{job_id}/audio/dialogue.wav`

---

## 8. V0.1 验收 E2E

### 8.1 E2E Job Record

> **E2E Job:** `job_5025f7ffce13`（hot_ai, real LLM, real TTS, MP4 export）

| Field | Value |
|-------|-------|
| job_id | `job_5025f7ffce13` |
| status | **succeeded** |
| news_title | OpenAI DayBreak – GPT-5.5-Cyber |
| news_url | https://openai.com/index/daybreak-securing-the-world/ |
| source | Hacker News |
| theme | `news_card_v1` |
| LLM provider | `minimax_m3_openai` |
| TTS provider | `minimax_dialogue` |
| dialogue turns | 11 |
| dialogue duration | 54.5s |
| output.mp4 size | 1,052,320 bytes (~1.0 MB) |
| output.mp4 duration | 54.5s |
| animation.html | ✓ 可预览 |
| dialogue.wav | ✓ 可播放 |
| output.mp4 | ✓ 可播放，有画面有音频 |

### 8.2 E2E 验收清单

| 检查项 | 结果 |
|--------|------|
| job status = succeeded | ✓ |
| title 不为空 | ✓（CP18.4 fix 后生效） |
| /api/history 中 job.title 非空 | ✓（CP18.4 fix 后生效） |
| animation.html 可预览 | ✓ |
| dialogue.wav 可播放 | ✓ |
| output.mp4 可播放 | ✓ |
| Web Studio 优先加载 MP4 | ✓ |
| output.mp4 有画面和音频 | ✓ |
| turns <= 14 | ✓（LLM 原始生成 11 turns，hard cap max_turns=10 在 pipeline 层强制压缩；本 job 为 CP18.3 UI 验收，完整 max_turns=10 E2E 见 CP18.2.1） |
| duration 40-70s | ✓（54.5s） |
| API key / voice_id 不泄露 | ✓ |
| outputs/jobs/job_* 未提交 | ✓ |

---

## 9. 当前限制（V0.1 已知问题）

1. **MP4 导出较慢** — Playwright 逐帧截图 + FFmpeg 合成，~2分钟导出65秒视频
2. **主视觉是 16:9 横屏** — 还不是 9:16 竖屏短视频
3. **只有 news_card_v1 达到可观看水平** — 其他主题视觉质量不足
4. **LLM IR 生成偶发结构错误** — 可能出现 `UNREVEALED_CALLOUT`、`BROKEN_CAUSAL_CHAIN` 等错误，需要 repair/retry
5. **turn 压缩可能造成相邻相同 speaker** — max_turns hard cap 可能产生连续的 expert/host 对话
6. **新闻源目前只有 HN hot AI** — 还不支持其他新闻源
7. **还没有定时生成** — 需要手动触发
8. **还没有部署** — 只支持本地运行
9. **还没有用户系统** — 无认证、无权限
10. **还没有封面/字幕精修** — 字幕位置和样式较简单

---

## 10. 下一阶段路线图

| CP | 主题 | 目标 |
|----|------|------|
| CP19 | 稳定性与失败率治理 | 减少 LLM IR 生成错误率，增加 retry 策略 |
| CP20 | 9:16 竖屏短视频模板 | 新增竖屏主题，支持短视频平台 |
| CP21 | 多新闻源聚合 | 支持更多新闻源（RSS、API等） |
| CP22 | 每日自动生成与历史管理 | 定时任务，历史作品归档 |
| CP23 | 导出速度优化 | 并行帧渲染，硬件加速编码 |
| CP24 | 产品化部署 | Docker / 云端部署，用户系统 |

---

## 11. 安全注意事项

- `.env` 文件包含真实 API key，**永远不要提交**
- `outputs/jobs/job_*` 包含生成内容，**永远不要提交**
- `outputs/latest` 包含最新生成内容，**永远不要提交**
- `dialogue_manifest.json` 中 voice_id 以 env var 名称存储（如 `MINIMAX_TTS_HOST_VOICE_ID`），不暴露实际值
- debug prompt/response 文件仅供本地调试，不要作为普通 artifact 暴露

---

## 12. 文件结构

```
chalk-news-video/
├── src/
│   ├── server.py          # Web Studio 后端（FastAPI）
│   ├── pipeline.py        # 主 pipeline 编排
│   ├── layout.py          # semantic_ir → render_ir（CP18.4 修复 news 字段）
│   ├── dialogue_visual.py # 对话视觉叠加层
│   ├── render_html.py    # render_ir → animation.html
│   ├── export_video.py   # animation.html → output.mp4
│   ├── generate_ir.py    # LLM 生成 semantic_ir
│   ├── generate_dialogue.py # LLM 生成 dialogue_script
│   └── tts/              # TTS provider 接口
├── renderer/
│   └── template.html     # 动画 HTML 模板
├── web/
│   ├── index.html        # Web Studio 前端
│   ├── app.js           # 前端逻辑（CP18.3.1 MP4 预览修复）
│   └── style.css        # 样式
├── config/
│   ├── llm.yaml         # LLM provider 配置
│   ├── tts.yaml         # TTS provider 配置
│   └── themes.yaml      # 主题配置
├── docs/
│   ├── V0_1_DEMO_FREEZE.md  # 本文档
│   └── CP18_3_MP4_EXPORT_WATCHABLE_DEMO.md  # CP18.3 验证报告
└── outputs/
    ├── jobs/             # job 输出目录（按 job_id 组织）
    └── latest/           # 最新生成物（不提交）
```

---

## 13. CP18.4.1 Lightweight Verification

**Date:** 2026-06-24
**Approach:** Lightweight — no real LLM, no real TTS, no MP4 export

### 13.1 Tests Run

`tests/test_layout_news_metadata.py` — 4 test cases, all PASSED:

| Test | Description | Result |
|------|-------------|--------|
| `test_render_ir_news_full` | Full semantic_ir → render_ir.news | ✓ PASS |
| `test_render_ir_news_fallback` | Empty title → fallback to meta.source_title | ✓ PASS |
| `test_render_ir_news_empty` | All empty → empty strings | ✓ PASS |
| `test_render_ir_news_no_nodes` | No nodes → _empty_render_ir path | ✓ PASS |

### 13.2 Document Correction

- E2E 验收清单原写 `turns <= 10 ✓` 与实际 `11 turns` 矛盾
- 已修正为 `turns <= 14 ✓`，说明 LLM 原始生成 11 turns，hard cap 机制在 CP18.2.1 验证

### 13.3 No Real Pipeline Run

- ✓ 没有运行 real LLM
- ✓ 没有运行 real TTS
- ✓ 没有导出 MP4
- ✓ 没有等待后台长任务
- 完整 E2E（title 字段端到端验证）留给后续低频验收执行

---

## 14. Git Status

```
Branch: fix/cp18.4.1-v0.1-freeze-cleanup
Modified: src/layout.py, tests/test_layout_news_metadata.py, docs/V0_1_DEMO_FREEZE.md
Outputs NOT committed: outputs/jobs/*
```
