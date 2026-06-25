# CP51 MVP Readiness Audit

## 1. MVP 一句话定位

这是一个"可靠来源新闻 → 结构化栏目 → 9:16 视频预览 → MP4 导出 → 发布素材包"的新闻视频生产工作台 MVP。

## 2. 当前真实可用能力

### 核心链路

| 步骤 | 功能 | 说明 |
|------|------|------|
| 1 | Reliable Source Registry | 内置可信来源列表（OpenAI、arXiv 等），支持域名识别 |
| 2 | URL 输入 | 支持 `url_input` API 输入新闻 URL |
| 3 | URL 草稿篮 | 本地多 URL 暂存，最多 5 条，可手动编辑标题/摘要 |
| 4 | URL 静态抽取 | 调用 `/api/article/extract` 抓取静态 HTML，提取 title/description |
| 5 | Redirect 安全限制 | 不跟随重定向到私有 IP/本地地址 |
| 6 | 来源集合保存/恢复 | localStorage 保存/恢复来源集合（CP47） |
| 7 | Source Contract API | 生成 `episode_template_v1` 格式合同（CP43） |
| 8 | Inspector | 查看生成的合同内容 |
| 9 | Apply Planner | 将合同应用到 planner |
| 10 | 9:16 Preview | 多种 HTML 视觉样式预览 |
| 11 | Playwright + ffmpeg MP4 Export | 异步导出 9:16 竖屏 MP4（CP40） |
| 12 | Export Job Status/History | 查询导出状态、查看历史、删除 |
| 13 | Optional Audio Mux | 可混入本地 WAV 音频（静音或自定义） |
| 14 | Production Workflow Checklist | 实时显示生产流程各步骤完成状态（CP48） |
| 15 | Publish Package Copy Kit | 生成标题/简介/平台文案/标签/封面提示词（CP49） |
| 16 | Publish Package 本地导出 | 下载 `publish_package.json` / `publish_package.md`（CP50） |

## 3. 当前不是能力的东西

以下内容**当前版本不提供**，必须明确告知用户：

| 类别 | 说明 |
|------|------|
| 真实新闻 API | 没有接入真实新闻聚合服务（如 NewsAPI、Bing News） |
| 爬虫 | 没有后台爬虫；URL 抽取仅限静态 HTML，不支持 JS 动态渲染 |
| Real LLM | 没有调用真实 LLM 进行内容理解或改写；文案为规则生成 |
| Real TTS | 没有真实文字转语音；音频处理为静音混入或已有音频 mux |
| Remotion | 没有使用 Remotion 生成高级动画 |
| 真实平台发布（真实发布） | 没有接入抖音/B站/YouTube API；不自动上传文件 |
| 账号体系 | 没有用户登录、OAuth、云端同步 |
| 云端数据库 | 所有数据存在浏览器 localStorage，不适合多设备同步 |
| 大规模源采集 | 适合单次演示/小规模采集，不适合大规模新闻采集 |

## 4. 推荐演示路径（8 步）

1. **打开工作台** — 访问本地服务器，查看 capability dashboard
2. **查看 capability / workflow panel** — 了解当前已实现的能力
3. **添加 URL 到草稿篮** — 输入 2–3 个可信来源 URL
4. **抽取或手动填写标题摘要** — 点击抽取或直接在卡片里编辑
5. **保存来源集合** — 命名并保存，方便后续恢复
6. **从草稿篮生成栏目 contract** — 点击"生成栏目"触发 `/api/source-contract`
7. **Inspector 检查并 Apply Planner** — 查看合同后应用到 planner
8. **Preview + Export MP4** — 选择样式，预览后异步导出 MP4
9. **生成 Publish Package** — 点击"生成发布素材包"
10. **导出 JSON/Markdown** — 下载 `publish_package.json` 和 `publish_package.md`

## 5. 验收结果

当前版本已通过以下测试：

- ✅ CP42 — News Source to Episode Contract Pipeline（20/20）
- ✅ CP43 — Source Contract API（15/15）
- ✅ CP44 — Reliable Source Registry / URL Input（27/27）
- ✅ CP45 — Article Fetch / Extraction MVP（35/35）
- ✅ CP46 — URL Draft Basket（30/30）
- ✅ CP47 — Source Collection Saved Drafts（23/23）
- ✅ CP48 — Production Workflow Checklist（26/26）
- ✅ CP49 — Publish Package Copy Kit（31/31）
- ✅ CP50 — Export Publish Package Files（24/24）
- ✅ CP40.8 — Episode Export E2E（11/11）

## 6. MVP 风险清单

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| URL 抽取仅适合静态 HTML | 部分新闻网站无法抓取 | 手动编辑草稿卡片的标题/摘要 |
| 新闻理解是规则生成 | 摘要/标签质量有限 | 提供手动编辑能力 |
| 文案模板化 | 平台适配性差 | 用户可手动复制修改后发布 |
| 视觉效果是 HTML Renderer | 动画/特效有限 | CP49 提供了封面提示词供 AI 绘图 |
| 主播是 SVG/CSS | 非数字人/真人 | 路线图中可接入 real TTS + Remotion |
| localStorage 不跨设备 | 多设备用户无法同步 | 未来可做导出/导入 JSON |
| 大规模采集未做 | 不适合新闻聚合平台 | 当前定位为单用户本地工作台 |
| 导出依赖 Playwright + ffmpeg | 需本地安装依赖 | README 有环境说明 |

## 7. 冻结建议

### 推荐冻结版本

**MVP Candidate v0.1**

冻结范围：
- CP42–CP50 所有已实现功能
- 仅限本地开发/演示使用
- 单用户本地 workflow

不冻结范围：
- 真实生产爬虫/新闻 API 接入
- 多用户 SaaS
- 平台发布 API（抖音/B站/YouTube）
- Real LLM / TTS / Remotion
- 云端同步/数据库

### 后续路线图方向（不承诺）

1. **CP52** — 新闻源扩展（接入 NewsAPI 等）
2. **CP53** — Real LLM 接入（内容理解/改写）
3. **CP54** — Real TTS 接入（语音合成）
4. **CP55** — Remotion 接入（高级动画）
5. **CP56** — 平台发布 API（抖音/B站/YouTube）

## 8. 变更日志（CP42–CP51）

| CP | 功能 | 类型 |
|----|------|------|
| CP42 | News Source → Episode Contract Pipeline | 新功能 |
| CP43 | Source Contract API | 新功能 |
| CP44 | Reliable Source Registry / URL Input | 新功能 |
| CP45 | Article Fetch / Extraction MVP | 新功能 |
| CP46 | URL Draft Basket | 新功能 |
| CP47 | Source Collection Saved Drafts | 新功能 |
| CP48 | Production Workflow Checklist | 新功能 |
| CP49 | Publish Package Copy Kit | 新功能 |
| CP50 | Export Publish Package JSON/Markdown | 新功能 |
| CP51 | MVP Readiness Audit | 文档/冻结 |

## 9. 技术债务

| 项目 | 说明 |
|------|------|
| `episode_export.py` | 包含硬编码路径，生产环境需配置化 |
| `render_episode_html.py` | HTML renderer 偶有长标题溢出 |
| `localStorage` 数据结构 | 无版本号，未来字段变更需迁移逻辑 |
| CORS | 当前 API 期望同源部署 |
