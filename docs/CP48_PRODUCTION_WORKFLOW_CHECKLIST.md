# CP48: Production Workflow Checklist / Publish Readiness Panel

## Status

**Stage:** CP48 — Implementation Complete
**Date:** 2026-06-25
**Branch:** `feat/cp48-production-workflow-checklist`

## Goal

在现有工作台上新增"生产流程检查清单 / 发布就绪面板"，把来源收集、URL 抽取、草稿篮、来源集合、生成 contract、inspector、应用到 planner、预览、导出 MP8、历史记录这些能力串起来，让用户明确知道当前视频生产进度和发布状态。

## What This Is

**生产流程检查清单（Production Workflow Checklist）** — 展示 7 个核心生产步骤的状态：

| # | 步骤 | 触发条件 |
|---|------|----------|
| 1 | 来源准备 | urlDraftItems 非空，或 sourceCollections 非空，或 latestSourceEpisodeItems 非空 |
| 2 | 草稿确认 | 至少 1 条 urlDraftItem 有 title |
| 3 | 栏目合约 | latestSourceContract 非空 |
| 4 | 结果检查 | latestSourceEpisodeItems 非空 |
| 5 | 应用到合集 | episodeItemList 非空 |
| 6 | 预览 | latestEpisodePreviewUrl 或 latestEpisodeTemplateContract 非空 |
| 7 | MP4 导出 | currentEpisodeExportMp4Url 或 latestSucceededJob 非空 |

**发布就绪条件：** `hasPlannerItems && hasPreview && hasExport`

badge 显示：
- `is-ready`（绿色）：可发布
- `is-blocked`（灰色）：待补齐

## What This Is NOT

- ❌ 不是真实发布平台（不接抖音/B站/YouTube API）
- ❌ 没有后端数据库
- ❌ 没有账号体系
- ❌ 没有接真实 LLM/TTS
- ❌ 没有引入 Remotion
- ❌ 没有修改 MP4 导出主逻辑

## UI Layout

```
┌─────────────────────────────────────────────────────────┐
│ [Production Workflow]                                   │
│ 新闻视频生产检查清单                     [可发布/待补齐]   │
│                                                         │
│ ✓ 来源准备     已有 URL 草稿或来源集合                   │
│ ✓ 草稿确认     至少 1 条 URL 草稿已有标题                │
│ ✓ 栏目合约     已生成 episode_template_v1 contract        │
│ ✓ 结果检查     inspector 中已有入选新闻                   │
│ ✓ 应用到合集   Episode Planner 已有新闻项                 │
│ ✓ 预览        已有可预览的 9:16 视频舞台               │
│ ✓ MP4 导出    已有导出结果或成功任务                    │
│                                                         │
│ 当前进度：7/7。建议下一步：检查导出结果并准备发布。       │
└─────────────────────────────────────────────────────────┘
```

## Key Implementation Details

### State Calculation

`getProductionWorkflowState()` — 根据所有相关状态计算 7 个步骤的完成情况，返回：

```javascript
{
  steps: [...],        // 7 个步骤对象
  doneCount: 7,
  total: 7,
  ready: true,        // hasPlannerItems && hasPreview && hasExport
  hasSourceContract,
  hasPlannerItems,
  hasPreview,
  hasExport
}
```

### Render

`renderProductionWorkflowPanel()` — 渲染 7 个步骤行 + badge + 摘要提示

### Trigger Points

在以下位置调用 `renderProductionWorkflowPanel()`：

| 触发位置 | 说明 |
|----------|------|
| `init()` | 页面初始化 |
| `buildSourceContract()` 成功 | 生成 contract 后 |
| `applySourceContractToPlanner()` | 应用到 planner 后 |
| `addUrlDraft()` | 添加草稿后 |
| `removeUrlDraft()` | 移除草稿后 |
| `clearUrlDrafts()` | 清空草稿后 |
| `extractUrlDraft()` 成功/失败 | 抽取完成后 |
| `saveCurrentSourceCollection()` | 保存集合后 |
| `restoreSourceCollection()` | 恢复集合后 |
| `deleteSourceCollection()` | 删除集合后 |
| `clearSourceCollections()` | 清空集合后 |

## File Changes

| 文件 | 修改类型 | 说明 |
|------|----------|------|
| `web/index.html` | 修改 | 新增 workflow panel HTML |
| `web/app.js` | 修改 | 新增 3 个函数 + 多个调用点 |
| `web/style.css` | 修改 | 新增 workflow panel 样式 |
| `scripts/test_cp48_production_workflow_static.py` | 新增 | 静态测试 |
| `docs/CP48_PRODUCTION_WORKFLOW_CHECKLIST.md` | 新增 | 本文档 |

**未修改的文件（保持不变）：**
- `src/episode_export.py`
- `src/export_video.py`
- `src/render_episode_html.py`
- `src/article_extractor.py`
- `src/server.py`
- 其他后端文件

## Next Steps (CP49)

- 发布就绪包（caption / metadata / thumbnail 建议）
- 草稿篮批量导入
- 跨 session 恢复上一次生产状态
