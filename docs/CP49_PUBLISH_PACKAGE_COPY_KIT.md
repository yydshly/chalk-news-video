# CP49: Publish Package / Platform Copy Kit

## 目标

在 CP48 生产流程检查清单的基础上，新增"发布素材包"面板。用户完成 MP4 导出后，可以生成一套发布准备材料：视频标题、短简介、平台文案、标签、封面提示词、来源摘要、MP4 链接。

**本轮不做真实发布，不接抖音/B站/YouTube API，不上传文件，只生成可复制的文本和链接。**

## 功能范围

### 生成内容

| 字段 | 说明 |
|------|------|
| 视频标题 | 从 contract episode title 或首条新闻标题截取，最多 40 字符 |
| 短简介 | 从首条新闻 summary/description 截取，最多 120 字符 |
| 平台文案 | 标题 + 简介 + 本期看点列表 + 标签，格式适合粘贴到平台 |
| 标签 | 从已有 tags 合并去重，最多 10 个，含默认 AI/科技/前沿/新闻 |
| 封面提示词 | 生成适合 AI 绘图工具的 9:16 封面描述词 |
| MP4 链接 | currentEpisodeExportMp4Url 或"尚未导出"提示 |
| 来源摘要 | 列出前 6 条新闻的标题和来源 |

### 用户操作

1. 点击"生成发布素材包"按钮
2. 素材包字段自动填充
3. 每个字段旁有"复制"按钮，一键复制到剪贴板
4. 用户手动将内容粘贴到目标平台

### 与 CP48 的关系

CP49 **不改变** CP48 的"可发布"条件。CP48 的可发布仍是：
- planner items + preview + export

CP49 只是生成发布材料，不影响 workflow readiness 判定。

## 技术实现

### 前端仅限

- `web/index.html` — 发布素材包面板
- `web/style.css` — 样式
- `web/app.js` — 逻辑（纯规则生成，无 LLM）
- `docs/CP49_PUBLISH_PACKAGE_COPY_KIT.md` — 本文档

### 禁止事项

- ❌ 不做真实发布 API
- ❌ 不自动上传 MP4
- ❌ 不接抖音/B站/YouTube API
- ❌ 不做 OAuth / 账号体系
- ❌ 不改后端数据库
- ❌ 不改 MP4 导出主逻辑
- ❌ 不接 real LLM
- ❌ 不接 real TTS
- ❌ 不引入 Remotion
- ❌ 不提交 outputs

### 文案生成方式

文案是**规则生成**（字符串截取、模板拼接），不是 LLM 生成。封面提示词是固定模板填入，非 AI 生成。

## 后续 CP50

可做"导出 publish_package.json / .md"功能，将素材包保存为本地文件。

## 文件变更

| 文件 | 变更 |
|------|------|
| web/index.html | 新增 publish-package-panel 区块 |
| web/style.css | 新增 .publish-package-* 样式 |
| web/app.js | 新增 publish package 函数和状态 |
| docs/CP49_PUBLISH_PACKAGE_COPY_KIT.md | 本文档 |
| scripts/test_cp49_publish_package_static.py | 静态检查测试 |
