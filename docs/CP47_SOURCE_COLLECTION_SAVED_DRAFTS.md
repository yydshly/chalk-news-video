# CP47: Source Collection Snapshot / Saved Drafts

## Status

**Stage:** CP47 — Implementation Complete
**Date:** 2026-06-25
**Branch:** `feat/cp47-source-collection-saved-drafts`

## Goal

在 CP46 URL 草稿篮基础上，新增"来源集合保存"能力：用户可以把当前 URL 草稿篮保存为一个 collection snapshot，之后可恢复继续编辑、抽取、生成栏目。

## What This Is

**来源集合（Source Collection）** — URL 草稿篮的快照，保存到浏览器 `localStorage`，支持：
1. 将当前草稿篮保存为命名集合
2. 查看已保存的集合列表
3. 将集合恢复到草稿篮（继续编辑/抽取）
4. 删除单个集合
5. 清空所有已保存集合

## What This Is NOT

- ❌ 没有后端数据库（纯 localStorage）
- ❌ 没有账号体系
- ❌ 没有云同步
- ❌ 没有后台批量爬虫
- ❌ 没有接真实新闻 API
- ❌ 没有接真实 LLM/TTS
- ❌ 没有引入 Remotion
- ❌ 没有修改 MP4 导出主逻辑

## User Flow

```
URL 草稿篮（CP46）
  ↓（编辑/抽取后）
点击"保存集合" → 输入名称 → localStorage 持久化
  ↓
来源集合列表（CP47 新增）
  ↓（以后继续工作）
点击"恢复到草稿篮"
  ↓
继续编辑 / 抽取 / 生成栏目（复用 CP46 链路）
```

## Data Structure

```javascript
// localStorage key
const SOURCE_COLLECTION_STORAGE_KEY = "chalk_source_collections_v1";
const MAX_SOURCE_COLLECTIONS = 20;

collection = {
  id: "source_collection_xxx",
  name: "今日 AI 官方来源",
  created_at: "2026-06-25T12:00:00.000Z",
  updated_at: "2026-06-25T12:00:00.000Z",
  item_count: 3,
  items: [/* clone of urlDraftItems */]
}
```

## API / Storage

**无后端 API** — 所有操作在前端 `localStorage` 完成：

- `loadSourceCollections()` — 从 localStorage 读取
- `persistSourceCollections()` — 写入 localStorage
- `saveCurrentSourceCollection()` — 保存当前草稿篮
- `restoreSourceCollection(id)` — 恢复集合到草稿篮
- `deleteSourceCollection(id)` — 删除单个集合
- `clearSourceCollections()` — 清空所有集合

## Key Implementation Details

### `cloneUrlDraftItem`

将 URL 草稿项深度克隆，确保恢复时数据独立：

```javascript
function cloneUrlDraftItem(item) {
  return {
    id: item.id || createUrlDraftId(),
    url: item.url || "",
    title: item.title || "",
    summary: item.summary || "",
    source_id: item.source_id || "",
    source: item.source || "",
    final_score: Number(item.final_score || 0),
    tags: Array.isArray(item.tags) ? item.tags.slice(0, 10) : [],
    status: item.status || "draft",
    error: item.error || ""
  };
}
```

### 恢复后

恢复后草稿篮包含原始的 `id`、`url`、`status`，用户可以：
- 继续逐条抽取（调用 `/api/article/extract`）
- 手动修改标题/摘要
- 点击"从草稿篮生成栏目"（复用 `manual_items`）

### 上限保护

- 最多保存 20 个集合（`MAX_SOURCE_COLLECTIONS = 20`）
- 超出时丢弃最旧的
- 每个集合最多 5 个草稿项（`MAX_URL_DRAFT_ITEMS`，CP46 已有限制）

## UI Components

### HTML 新增元素

- `.source-collection-panel` — 整个面板容器
- `#source-collection-name` — 集合名称输入框
- `#btn-save-source-collection` — "保存集合"按钮
- `#btn-clear-source-collections` — "清空已保存集合"按钮
- `#source-collection-list` — 集合列表容器

### CSS 新增类

- `.source-collection-panel` — 面板容器
- `.source-collection-head` — 头部
- `.source-collection-save-row` — 名称输入 + 保存按钮行
- `.source-collection-actions` — 操作按钮行
- `.source-collection-list` — 集合列表
- `.source-collection-card` — 单个集合卡片
- `.source-collection-card-head` — 卡片头部
- `.source-collection-name` — 集合名称
- `.source-collection-meta` — 集合元信息（条数 + 时间）
- `.source-collection-first-url` — 第一个 URL 预览
- `.source-collection-card-actions` — 卡片操作按钮行
- `.source-collection-empty` — 空状态

### JS 新增函数

| 函数 | 说明 |
|------|------|
| `createSourceCollectionId()` | 生成唯一集合 ID |
| `cloneUrlDraftItem(item)` | 深度克隆草稿项 |
| `loadSourceCollections()` | 从 localStorage 加载集合 |
| `persistSourceCollections()` | 持久化集合到 localStorage |
| `saveCurrentSourceCollection()` | 保存当前草稿篮为集合 |
| `restoreSourceCollection(id)` | 恢复集合到草稿篮 |
| `deleteSourceCollection(id)` | 删除单个集合 |
| `clearSourceCollections()` | 清空所有集合 |
| `renderSourceCollections()` | 渲染集合列表 UI |

## 文件修改

| 文件 | 修改类型 | 说明 |
|------|----------|------|
| `web/index.html` | 修改 | 新增来源集合面板 HTML |
| `web/app.js` | 修改 | 新增集合状态和函数 |
| `web/style.css` | 修改 | 新增来源集合面板样式 |
| `scripts/test_cp47_source_collection_static.py` | 新增 | 静态测试 |
| `docs/CP47_SOURCE_COLLECTION_SAVED_DRAFTS.md` | 新增 | 本文档 |

**未修改的文件（保持不变）：**
- `src/episode_export.py`
- `src/export_video.py`
- `src/render_episode_html.py`
- 其他后端文件

## 验收标准

- [x] 当前草稿篮可以保存为集合
- [x] 已保存集合可以展示
- [x] 已保存集合可以恢复到草稿篮
- [x] 已保存集合可以删除
- [x] 已保存集合可以清空
- [x] 使用 localStorage
- [x] 不新增后端数据库
- [x] 不新增账号体系
- [x] 不影响 CP46 草稿篮生成 contract
- [x] 不影响 inspector / planner / preview / export
- [x] 所有测试通过
- [x] git status clean

## Next Steps (CP48)

- 考虑跨 session 持久化草稿篮状态
- 考虑集合重命名
- 考虑导出/导入集合 JSON
- 考虑批量导入 URL 到草稿篮
