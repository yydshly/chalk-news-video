# CP46: URL Draft Basket / Multi-URL Collection MVP

## Status

**Stage:** CP46 — Implementation Complete
**Date:** 2026-06-25
**Branch:** `feat/cp46-url-draft-basket-multi-url-mvp`

## Goal

在 CP45 单条 URL 抽取能力基础上，新增"URL 草稿篮"：用户可以添加多条 URL 草稿，逐条抽取标题/摘要，人工确认后生成 `manual_items` / `episode_template_v1` contract，并继续进入 inspector → apply planner → preview/export 链路。

## What This Is

**人工 URL 草稿篮** — 用户手动逐条添加 URL 到草稿篮，每个草稿可以：
1. 人工填写标题和摘要
2. 或者点击"抽取"按钮调用 `POST /api/article/extract` 自动提取标题/摘要
3. 人工确认标题/摘要无误后，一键生成栏目 contract

## What This Is NOT

- ❌ 没有后台批量爬虫（batch crawler）
- ❌ 没有定时自动抓取
- ❌ 没有 JS 渲染（无 Puppeteer/Playwright）
- ❌ 没有接真实新闻 API（如 NewsAPI）
- ❌ 没有接真实 LLM（用于标题生成）
- ❌ 没有接真实 TTS
- ❌ 没有引入 Remotion
- ❌ 没有修改 MP4 导出主逻辑（`src/episode_export.py` 未改动）
- ❌ 没有修改 `src/export_video.py`、`src/render_episode_html.py`

## User Flow

```
用户输入 URL → 加入草稿篮（最多 5 条）
       ↓
  逐条点击"抽取" → /api/article/extract 返回标题/摘要
       ↓
  人工编辑标题/摘要（可选）
       ↓
  点击"从草稿篮生成栏目" → POST /api/episode/source-contract
       ↓（返回 episode_template_v1 contract）
  inspector 查看生成结果
       ↓
  点击"应用到当前合集" → 填充 episode planner
       ↓
  预览 → 导出 MP4
```

## Key Implementation Details

### 前端状态

```javascript
let urlDraftItems = [];
const MAX_URL_DRAFT_ITEMS = 5;

每个 draft item 结构：
{
  id: "url_draft_xxx",
  url: "",
  title: "",
  summary: "",
  source_id: "",
  source: "",
  final_score: 0,
  tags: [],
  status: "draft" | "extracting" | "ready" | "failed",
  error: ""
}
```

### 字段说明

| 字段 | 说明 |
|------|------|
| `id` | 草稿唯一 ID，格式 `url_draft_<timestamp>_<random>` |
| `url` | 用户输入的原始 URL |
| `title` | 抽取或手动填写的新闻标题 |
| `summary` | 抽取或手动填写的新闻摘要 |
| `source_id` | 关联的可靠来源 ID（可选） |
| `status` | `draft`=待填充, `extracting`=抽取中, `ready`=已就绪, `failed`=抽取失败 |
| `error` | 抽取失败时的错误信息 |

### API 调用

**抽取单条草稿**（复用 CP45）：
```
POST /api/article/extract
Body: { url: "https://..." }
```

**生成栏目 contract**（复用 CP43 `manual_items`）：
```
POST /api/episode/source-contract
Body: {
  source_type: "manual_items",
  items: [{ id, title, summary, source, url, final_score, points, comments, tags }, ...],
  limit: 5,
  template_id: "breaking_news_v1",
  episode_title: "URL 草稿快讯",
  episode_subtitle: "多来源 URL 汇总生成"
}
```

### 复用说明

- 抽取复用 `POST /api/article/extract`（CP45）
- 生成 contract 复用 `source_type: "manual_items"`（CP43）
- inspector 和 apply-to-planner 复用已有 UI（CP43.1）
- preview/export 复用已有链路

## UI Components

### HTML 新增元素

- `#url-draft-basket` — 草稿篮容器
- `#url-draft-new-url` — 新 URL 输入框
- `#btn-add-url-draft` — "加入草稿篮"按钮
- `#btn-clear-url-drafts` — "清空草稿"按钮
- `#url-draft-list` — 草稿列表容器
- `#btn-build-contract-from-url-drafts` — "从草稿篮生成栏目"按钮

### CSS 新增类

- `.url-draft-basket` — 草稿篮容器样式
- `.url-draft-basket-head` — 头部布局
- `.url-draft-add-row` — URL 输入行
- `.url-draft-list` — 草稿列表
- `.url-draft-card` — 单条草稿卡片
- `.url-draft-card-head` — 卡片头部（URL + 状态）
- `.url-draft-url` — URL 显示
- `.url-draft-status` — 状态标签
- `.url-draft-status-ready` — 已就绪状态样式
- `.url-draft-status-failed` — 失败状态样式
- `.url-draft-status-extracting` — 抽取中状态样式
- `.url-draft-error` — 错误信息样式
- `.url-draft-actions` — 操作按钮行
- `.url-draft-empty` — 空状态提示

### JS 新增函数

| 函数 | 说明 |
|------|------|
| `createUrlDraftId()` | 生成唯一草稿 ID |
| `addUrlDraft(url)` | 添加 URL 到草稿篮（含去重和上限检查） |
| `removeUrlDraft(id)` | 移除指定草稿 |
| `clearUrlDrafts()` | 清空所有草稿 |
| `renderUrlDraftBasket()` | 渲染草稿篮列表 UI |
| `extractUrlDraft(id)` | 调用后端抽取单条草稿的标题/摘要 |
| `buildContractFromUrlDrafts()` | 从所有就绪草稿生成栏目 contract |

## 文件修改

| 文件 | 修改类型 | 说明 |
|------|----------|------|
| `web/index.html` | 修改 | 新增 URL 草稿篮 UI |
| `web/app.js` | 修改 | 新增草稿篮状态和函数 |
| `web/style.css` | 修改 | 新增草稿篮样式 |
| `scripts/test_cp46_url_draft_basket_static.py` | 新增 | 静态测试 |
| `docs/CP46_URL_DRAFT_BASKET_MULTI_URL_MVP.md` | 新增 | 本文档 |

**未修改的文件（保持不变）：**
- `src/episode_export.py`
- `src/export_video.py`
- `src/render_episode_html.py`
- 其他后端文件

## 验收标准

- [x] 页面有 URL 草稿篮
- [x] 可添加最多 5 条 URL
- [x] 重复 URL 有提示
- [x] 可逐条抽取
- [x] 可手动编辑标题/摘要
- [x] 可移除单条
- [x] 可清空全部
- [x] 可从草稿篮生成 contract（复用 `manual_items`）
- [x] contract 进入 inspector
- [x] 可应用到 Episode Planner
- [x] 可继续预览和导出
- [x] 没有后台批量爬虫
- [x] 不改 MP4 导出主逻辑
- [x] 测试通过
- [x] git status clean

## Next Steps (CP47)

- 考虑 batch URL server-side contract（后端批量处理多条 URL）
- 考虑 URL 去重（跨 session 持久化草稿篮）
- 考虑批量抽取（一次触发多条 URL 抽取）
