# CP52 Next Phase Plan（CP53–CP60）

> 基于 CP52 路线决策，下一阶段详细实施草案。

## Phase 2 总体目标

在 MVP v0.1 基础上，建立"真实来源 + 内容质量"最小闭环。

**核心原则**：
- Route A（来源采集）和 Route B（LLM/TTS）并行小步推进
- 保持人工审查节点，不过度自动化
- 不做 Remotion 全面重构、不做多用户 SaaS

---

## CP53：Real Source Feed Snapshot MVP

**目标**：抓取/探测官方来源快照，生成结构化候选列表

### 做的事

1. 选择 5–8 个高质量官方来源（RSS feed 或静态 HTML 页面）
2. 实现 `source_snapshot_v1` schema：
   ```json
   {
     "schema": "source_snapshot_v1",
     "source_id": "openai-news",
     "fetched_at": "2026-06-25T00:00:00Z",
     "items": [
       {
         "url": "https://...",
         "title": "...",
         "published_at": "...",
         "summary": "..."
       }
     ]
   }
   ```
3. `/api/source-snapshot` endpoint（新增后端）
4. 定时探测逻辑（不自动生成视频）

### 不做的事

- 不生成视频
- 不调用 LLM
- 不调用 TTS
- 不接入未验证的新闻 API
- 不做自动发布

**验收**：能抓取 5+ 来源，返回结构化 snapshot JSON

---

## CP54：Source Candidate Review UI

**目标**：让用户在 UI 上审查、筛选采集到的候选新闻，然后加入草稿篮

### 做的事

1. 新增 `Source Candidates` 面板（类似 URL 草稿篮）
2. 展示 snapshot 中的候选列表
3. 支持：
   - 查看详情（URL、标题、摘要、时间）
   - 标记"采用" / "排除"
   - 批量操作
   - 一键将选中项加入 URL 草稿篮
4. 状态：`pending_review` → `approved` / `rejected`
5. `source_candidates_v1` schema：
   ```json
   {
     "schema": "source_candidates_v1",
     "snapshot_id": "...",
     "items": [
       {
         "item_id": "...",
         "url": "...",
         "title": "...",
         "status": "pending_review|approved|rejected",
         "approved_at": null
       }
     ]
   }
   ```

### 不做的事

- 不自动筛选（全部人工审查）
- 不自动生成视频
- 不做 RSS 订阅推送

**验收**：候选列表可展示，approved 项可进入 URL 草稿篮

---

## CP55：LLM Script Draft Spike

**目标**：基于 approved candidates 生成 episode_script_draft_v1，对比规则生成 vs LLM 生成

### 做的事

1. `episode_script_draft_v1` schema：
   ```json
   {
     "schema": "episode_script_draft_v1",
     "source_candidates": ["item_id_1", "item_id_2"],
     "script_sections": [
       {
         "type": "opening|segment|closing",
         "speaker": "anchor",
         "content": "...",
         "llm_generated": true,
         "facts_guard": ["fact_check_note"]
       }
     ],
     "generated_by": "llm|gpt-4o",
     "generated_at": "..."
   }
   ```
2. `/api/script-draft` endpoint（后端，新增）
3. Facts guard 注释（LLM 输出中标记"需人工核实"段落）
4. 对比视图：规则生成 vs LLM 生成（UI 展示两组结果）
5. 人工确认后可进入 planner

### 不做的事

- 不做全自动事实补全（facts guard 只是提示，不自动查证）
- 不自动发布
- 不接入 TTS

**验收**：能生成 script draft，facts guard 标记可疑段落

---

## CP56：TTS Audio Draft Spike

**目标**：基于 approved script draft 生成音频草稿和 audio manifest

### 做的事

1. `audio_manifest_v1` schema：
   ```json
   {
     "schema": "audio_manifest_v1",
     "script_draft_id": "...",
     "segments": [
       {
         "section_type": "opening",
         "text": "...",
         "duration_estimate_s": 15,
         "tts_audio_url": null,
         "tts_status": "pending|completed|failed"
       }
     ],
     "total_duration_estimate_s": 120
   }
   ```
2. `/api/tts-audio-draft` endpoint（后端，新增）
3. 接入一个 TTS 服务（如 OpenAI TTS / Azure TTS / 火山引擎）
4. audio_manifest 管理（查询状态、重新生成失败段落）
5. 可 mux 到已有 MP4

### 不做的事

- 不做批量大规模合成
- 不做多音色并行
- 不做自动视频生成

**验收**：script draft 可提交 TTS 音频生成，manifest 状态可查询

---

## CP57：Subtitle / Caption Track

**目标**：从 script draft + audio manifest 生成字幕轨

### 做的事

1. `subtitle_track_v1` schema（SRT / VTT 格式）
2. 时间轴对齐（TTS duration 估算 + 人工微调）
3. `/api/subtitle-track` endpoint
4. 可导出 SRT / VTT 文件

### 不做的事

- 不做 ASR（自动语音识别）
- 不做复杂音视频对齐算法

**验收**：生成的 SRT 格式正确，时间轴与音频片段对应

---

## CP58：Visual Polish / Remotion Spike

**目标**：选择一个模板尝试 Remotion render，对比效果

### 做的事

1. 选定 1 个 9:16 竖屏新闻简报模板
2. Playwright screenshot path vs Remotion render path 对比
3. 输出 MP4 对比测试
4. 不替换现有 Python renderer，只做 research spike

### 不做的事

- 不全量替换 Python renderer
- 不做动画模板库（只做 1 个）
- 不做复杂 3D/粒子特效

**验收**：Remotion spike 可输出 MP4，与 Python renderer 输出对比

---

## CP59：Publishing Package v2

**目标**：基于真实 LLM 内容生成更完整平台文案

### 做的事

1. 平台差异化文案：
   - 抖音版（短、爆点、标签）
   - B站版（中长、深度、专栏风格）
   - YouTube 版（标题党 SEO + 描述）
2. `publish_package_v2` schema（含多平台版本）
3. 支持导出各平台差异化文案

### 不做的事

- 不做自动发布 API
- 不接入平台 OAuth

**验收**：可生成三个平台差异化的发布文案

---

## CP60：MVP v0.2 Freeze

**目标**：冻结第二阶段闭环，验证完整链路

### 做的事

1. 完整测试（CP53–CP59 各 CP 测试 + E2E）
2. 演示验证（Source → Candidates → Script → TTS → MP4 → Publish Package v2）
3. 更新 MVP_CAPABILITY_MATRIX
4. 冻结决策文档更新
5. 确定是否进入 Phase 3（Remotion 全面接入 / 多用户探索）

### 验收条件

- [ ] CP53 snapshot 可抓取 5+ 来源
- [ ] CP54 候选可审查并加入草稿篮
- [ ] CP55 LLM script draft 可生成
- [ ] CP56 TTS audio manifest 可生成
- [ ] CP57 字幕轨可导出
- [ ] CP58 Remotion spike 有输出
- [ ] CP59 多平台文案可生成
- [ ] 完整 E2E 链路跑通
- [ ] 所有 Phase 2 测试通过

---

## 阶段依赖图

```
CP53 Source Snapshot
       │
       ▼
CP54 Candidate Review UI ◄──┐
       │                    │
       ▼ (approved)         │
CP55 LLM Script Draft      │
       │                    │
       ▼ (approved)         │
CP56 TTS Audio Draft       │
       │                    │
       ▼                    │
CP57 Subtitle Track ───────┘
       │
       ▼
CP58 Remotion Spike
       │
       ▼
CP59 Publish Package v2
       │
       ▼
CP60 MVP v0.2 Freeze
```

## 快速检查：每 CP 的"不做"边界

| CP | 明确不做 |
|----|----------|
| CP53 | 不生成视频、不调 LLM/TTS |
| CP54 | 不自动筛选、不自动生成视频 |
| CP55 | 不自动事实补全、不发布 |
| CP56 | 不批量合成、不自动视频生成 |
| CP57 | 不做 ASR、不做复杂对齐 |
| CP58 | 不全量替换 renderer |
| CP59 | 不做自动发布 API |
| CP60 | 不承诺 Phase 3 路线 |
