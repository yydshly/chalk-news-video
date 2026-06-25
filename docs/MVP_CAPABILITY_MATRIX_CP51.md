# MVP Capability Matrix

> 截至 CP51 (MVP Candidate v0.1)
> 状态定义：ready = 已实现可用 / limited = 有条件可用 / mock = 模拟实现 / not_implemented = 未实现

| 模块 | 子功能 | 当前状态 | 真实可用 | 说明 |
|------|--------|----------|----------|------|
| **来源输入** | Reliable Source Registry | ready | ✅ | 内置域名列表，`/api/reliable-sources` |
| | URL 手动输入 | ready | ✅ | `/api/source-contract` url_input |
| | 批量 URL 输入 | limited | ✅ | 通过草稿篮多次添加 |
| **文章抽取** | 静态 HTML 抽取 | ready | ✅ | `/api/article/extract` |
| | JS 动态渲染抓取 | not_implemented | ❌ | 需 Playwright crawler 扩展 |
| | Redirect 安全限制 | ready | ✅ | 拒绝私有 IP/本地地址重定向 |
| | 标题/摘要提取 | ready | ✅ | og:title > title, og:description > meta description |
| **草稿管理** | URL 草稿篮 | ready | ✅ | 最多 5 条，localStorage |
| | 手动编辑标题/摘要 | ready | ✅ | 实时同步 workflow 状态 |
| | 草稿抽取 | ready | ✅ | 单条点击抽取 |
| | 草稿删除/清空 | ready | ✅ | |
| **来源集合** | 保存集合 | ready | ✅ | localStorage，命名保存 |
| | 恢复集合 | ready | ✅ | 重建草稿篮和合同 |
| | 删除集合 | ready | ✅ | |
| | 最多保存数量 | ready | ✅ | 20 个集合上限 |
| **合同生成** | Source Contract API | ready | ✅ | `/api/source-contract` |
| | episode_template_v1 schema | ready | ✅ | |
| | breaking_news_v1 模板 | ready | ✅ | |
| | hot_ai_news_v1 模板 | ready | ✅ | |
| | 合同 HTML 渲染 | ready | ✅ | `render_episode_html` |
| **合同检查** | Inspector 面板 | ready | ✅ | 查看合同内容 |
| | Contract 字段验证 | ready | ✅ | 必填字段校验 |
| **Planner** | Apply to Planner | ready | ✅ | 将合同应用到 planner 状态 |
| | Episode Items 管理 | ready | ✅ | latestSourceEpisodeItems |
| **预览** | 9:16 竖屏预览 | ready | ✅ | 多种样式 |
| | 16:9 横屏预览 | ready | ✅ | |
| | 样式切换 | ready | ✅ | |
| **MP4 导出** | Playwright 渲染 | ready | ✅ | 异步任务 |
| | ffmpeg 合成 | ready | ✅ | |
| | 导出状态轮询 | ready | ✅ | `/api/export/status` |
| | 导出历史 | ready | ✅ | 列表、打开、删除 |
| | 导出进度 | ready | ✅ | |
| **音频混流** | 混本地 WAV | ready | ✅ | 可选步骤 |
| | 无音频导出 | ready | ✅ | 默认 |
| | Real TTS | not_implemented | ❌ | 无 TTS 接入 |
| **生产流程** | Workflow Checklist | ready | ✅ | 实时显示各步骤状态 |
| | Ready Badge | ready | ✅ | 已完成 → 待补齐 |
| **发布素材（publish package）** | 生成发布素材包 | ready | ✅ | 规则生成标题/简介等 |
| | 复制字段 | ready | ✅ | clipboard API |
| | 导出 JSON | ready | ✅ | Blob download |
| | 导出 Markdown | ready | ✅ | Blob download |
| **底层依赖** | Real LLM | not_implemented | ❌ | 无 LLM 接入 |
| | Remotion | not_implemented | ❌ | 无动画生成 |
| | 真实爬虫 | not_implemented | ❌ | 仅静态 HTML |
| **发布对接** | 真实平台发布 | not_implemented | ❌ | 无抖音/B站/YouTube API |
| | 账号/OAuth | not_implemented | ❌ | 无账号体系 |
| **数据管理** | 云端数据库 | not_implemented | ❌ | localStorage 仅本地 |
| | 多设备同步 | not_implemented | ❌ | 需手动导出/导入 |
| **环境依赖** | Python + FastAPI | ready | ✅ | 后端服务 |
| | Playwright | ready | ✅ | 浏览器渲染 |
| | ffmpeg | ready | ✅ | 视频合成 |
| | Node.js | ready | ✅ | 前端服务 |

## 状态速查

| 状态 | 数量 |
|------|------|
| ready | 28 |
| limited | 1 |
| not_implemented | 11 |
| **Total** | **40** |

## 关键结论

- **已实现（ready + limited）**：29 项 — 覆盖了完整的内容生产闭环
- **未实现（not_implemented）**：11 项 — 主要是高级功能和平台对接
- **MVP 覆盖率**：约 72.5% 的规划功能已落地
