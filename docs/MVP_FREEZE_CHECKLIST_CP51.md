# MVP Freeze Checklist — CP51

> MVP Candidate v0.1 冻结前必须通过的检查项

## 一、所有测试必须通过

### 静态检查

- [x] `node --check web/app.js` — 无语法错误
- [x] CP42 — News Source to Episode Contract Pipeline（20/20）
- [x] CP43 — Source Contract API（15/15）
- [x] CP44 — Reliable Source Registry / URL Input（27/27）
- [x] CP45 — Article Fetch / Extraction MVP（35/35）
- [x] CP46 — URL Draft Basket（30/30）
- [x] CP47 — Source Collection Saved Drafts（23/23）
- [x] CP48 — Production Workflow Checklist（26/26）
- [x] CP49 — Publish Package Copy Kit（31/31）
- [x] CP50 — Export Publish Package Files（24/24）
- [x] CP40.8 — Episode Export E2E（11/11）

### 手动功能验收

- [ ] URL 可加入草稿篮
- [ ] URL 可抽取或手动填写
- [ ] 草稿篮标题/摘要变更后 workflow 立即刷新
- [ ] 草稿篮可保存来源集合
- [ ] 来源集合可恢复
- [ ] 可生成 Source Contract（`/api/source-contract`）
- [ ] Inspector 可查看合同内容
- [ ] 可 Apply Planner
- [ ] 可选择 9:16 样式预览
- [ ] 可导出 MP4（异步，等待完成）
- [ ] 可混本地 WAV 音频
- [ ] 可生成 Publish Package
- [ ] 每个 Publish Package 字段可复制
- [ ] 可导出 `publish_package.json`
- [ ] 可导出 `publish_package.md`
- [ ] Production Workflow Checklist 实时更新

---

## 二、功能链路完整性

- [ ] **来源 → 合同** 链路通：URL 输入 → 草稿篮 → 抽取/编辑 → 生成合同
- [ ] **合同 → 预览** 链路通：合同 → Inspector → Apply Planner → Preview
- [ ] **预览 → 导出** 链路通：Preview → Export MP4 → History
- [ ] **导出 → 发布** 链路通：MP4 完成 → Publish Package → JSON/MD 导出

---

## 三、边界声明验证

以下声明在文档/UI 中已明确说明：

- [ ] 未声称有**真实新闻 API**（如 NewsAPI、Bing News）
- [ ] 未声称有**后台爬虫**
- [ ] 未声称有 **JS 动态渲染抓取**（只支持静态 HTML）
- [ ] 未声称有 **Real LLM**（内容理解为规则生成）
- [ ] 未声称有 **Real TTS**（无语音合成）
- [ ] 未声称有 **Remotion**（无高级动画）
- [ ] 未声称可**真实发布到抖音/B站/YouTube**
- [ ] 未声称有**账号体系/云端同步**
- [ ] 未声称有**云端数据库**

---

## 四、环境依赖声明

以下依赖已在 README 中说明：

- [ ] Python 3.10+
- [ ] Node.js
- [ ] Playwright（`playwright install chromium`）
- [ ] ffmpeg（在 PATH 中或通过配置指定路径）

---

## 五、禁止事项确认

确认本次冻结**未包含**以下内容：

- [x] 未新增真实新闻 API 接入
- [x] 未新增后台爬虫
- [x] 未新增 JS 动态渲染抓取
- [x] 未新增 Real LLM 接入
- [x] 未新增 Real TTS 接入
- [x] 未新增 Remotion 引入
- [x] 未新增平台发布 API（抖音/B站/YouTube）
- [x] 未新增账号/OAuth 体系
- [x] 未新增云端数据库
- [x] 未新增云端同步
- [x] 未修改 MP4 导出主逻辑
- [x] 未修改 episode_export.py 核心路径
- [x] 未提交 outputs 目录

---

## 六、文档完整性

- [ ] `docs/MVP_READINESS_AUDIT_CP51.md` — MVP 审计文档
- [ ] `docs/MVP_DEMO_SCRIPT_CP51.md` — 演示脚本
- [ ] `docs/MVP_CAPABILITY_MATRIX_CP51.md` — 能力矩阵
- [ ] `docs/MVP_FREEZE_CHECKLIST_CP51.md` — 本文档
- [ ] `docs/CP50_EXPORT_PUBLISH_PACKAGE_FILES.md` — CP50 功能文档
- [ ] `docs/CP49_PUBLISH_PACKAGE_COPY_KIT.md` — CP49 功能文档
- [ ] `docs/CP48_PRODUCTION_WORKFLOW_CHECKLIST.md` — CP48 功能文档
- [ ] `docs/CP47_SOURCE_COLLECTION_SAVED_DRAFTS.md` — CP47 功能文档
- [ ] `docs/CP46_URL_DRAFT_BASKET.md` — CP46 功能文档
- [ ] `docs/CP45_ARTICLE_FETCH_EXTRACTION.md` — CP45 功能文档
- [ ] `docs/CP44_RELIABLE_SOURCE_REGISTRY.md` — CP44 功能文档

---

## 七、冻结签署

| 角色 | 确认 |
|------|------|
| 技术负责人 |  |
| 产品负责人 |  |
| 日期 |  |

---

## 八、版本信息

- **冻结版本**：MVP Candidate v0.1
- **冻结日期**：2026-06-25
- **包含 CP**：CP42、CP43、CP44、CP45、CP46、CP47、CP48、CP49、CP50、CP51
- **后续路线图**：CP52+（真实新闻 API）、CP53+（Real LLM）、CP54+（Real TTS）、CP55+（Remotion）、CP56+（平台发布）
