# CP50: Export Publish Package JSON / Markdown

## 目标

在 CP49 发布素材包的基础上，新增"导出发布包文件"能力。用户生成发布素材包后，可以导出 `publish_package.json` 和 `publish_package.md`，用于归档、交付、复制到其他工具或人工发布。

**本轮只做前端本地文件导出，不做后端保存，不上传文件，不接抖音/B站/YouTube API，不接账号系统。**

## 功能范围

### 导出格式

#### JSON

Schema: `chalk_publish_package_v1`

包含字段：
- `schema` — 版本标识
- `generated_at` — ISO 时间戳
- `title` — 视频标题
- `description` — 短简介
- `platform_copy` — 平台文案
- `tags` — 标签数组
- `cover_prompt` — 封面提示词
- `asset_links` — MP4 链接
- `source_summary` — 来源摘要
- `metadata` — 元数据
  - `has_mp4` — 是否已导出 MP4
  - `mp4_url` — MP4 URL
  - `source_item_count` — 来源条数
  - `workflow_ready` — CP48 workflow 是否就绪

#### Markdown

包含章节：
- `# 标题`
- `## 短简介`
- `## 平台文案`
- `## 标签`
- `## 封面提示词`
- `## MP4 / 素材链接`
- `## 来源摘要`
- `## 边界说明` — 声明未做真实发布

### 文件名

格式：`YYYY-MM-DD_{安全标题}.{json|md}`

- 日期取自 `new Date().toISOString().slice(0, 10)`
- 标题裁剪到 60 字符以内
- 特殊字符替换为 `_`
- 空格替换为 `_`

### 自动生成

导出按钮被点击时：
1. 如果 `latestPublishPackage` 为空，自动调用 `buildPublishPackage()` 并渲染
2. 然后执行导出

## 技术实现

### 前端仅限

- `web/index.html` — 导出按钮
- `web/style.css` — 按钮组布局
- `web/app.js` — 导出函数（Blob + URL.createObjectURL）
- `docs/CP50_EXPORT_PUBLISH_PACKAGE_FILES.md` — 本文档

### 禁止事项

- ❌ 不做真实平台发布 API
- ❌ 不自动上传 MP4
- ❌ 不做后端保存
- ❌ 不做 OAuth / 账号体系
- ❌ 不做云同步
- ❌ 不改 MP4 导出主逻辑
- ❌ 不接 real LLM
- ❌ 不接 real TTS
- ❌ 不引入 Remotion
- ❌ 不提交 outputs

## 后续 CP51

可做 server-side artifact export（将 publish_package 保存到服务器），但当前不做。

## 文件变更

| 文件 | 变更 |
|------|------|
| web/index.html | 新增导出 JSON / Markdown 按钮 |
| web/style.css | 新增 `.publish-package-actions` 和响应式布局 |
| web/app.js | 新增导出函数和工具函数 |
| docs/CP50_EXPORT_PUBLISH_PACKAGE_FILES.md | 本文档 |
| scripts/test_cp50_export_publish_package_static.py | 静态检查测试 |
