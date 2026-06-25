# CP52 Post-MVP Roadmap Gate

> 基于 CP51 MVP Candidate v0.1 冻结版本，下一阶段路线决策文档。

## 1. 当前状态

**已冻结版本**：chalk-news-video MVP Candidate v0.1（CP51）

**当前能力**：本地单用户新闻视频生产工作台

**当前闭环**：
```
可靠来源 → URL 抽取 → 多 URL 草稿篮 → 来源集合保存/恢复
→ contract 生成 → inspector → planner → 9:16 preview
→ MP4 export → workflow readiness → publish package
→ publish_package.json / publish_package.md
```

**当前最大价值**：完整跑通来源 → 视频 → 发布包的端到端闭环

**当前最大短板**：
- 内容质量依赖规则生成，非真实 AI 理解
- 信息源依赖手动输入，非自动采集
- 视觉动效有限，非 Remotion 级别
- 仅本地单用户，产品化未开始

---

## 2. 四条路线定义

### Route A：真实新闻采集

**目标**：
- RSS / HTML source watcher
- 官方来源更新检测
- 来源去重
- 每日候选池
- 新闻聚类

**核心价值**：解决"每天信息从哪里来"的问题，让产品真正具备持续信息源价值

**收益**：
- 从"手动填 URL"升级到"自动探测来源更新"
- 可支撑每日新闻简报类场景

**风险**：
- 抓取稳定性（403、反爬、IP 封禁）
- JS 动态渲染页面无法静态抓取
- 来源质量治理（误抓、重复、噪音）
- 去重/聚类算法复杂度

---

### Route B：Real LLM / TTS 内容生产

**目标**：
- Real LLM 摘要 / 改写 / 脚本生成
- Real TTS 口播合成
- 旁白时间线对齐
- 音频驱动视频节奏

**核心价值**：解决"视频内容是否足够好看、足够可信"的问题，让视频从"规则样片"升级为"可观看内容"

**收益**：
- 脚本质量大幅提升
- 自动生成口播旁白
- 内容一致性和准确性提升

**风险**：
- LLM API 成本控制
- Prompt 稳定性与事实准确性（hallucination）
- 多模型 token 消耗与延迟
- TTS 授权与音色质量选择
- 生成内容的合规性

---

### Route C：Remotion 视觉动画

**目标**：
- Remotion renderer path 替代当前 Python HTML renderer
- 更强动画模板、镜头级动画
- 卡片、时间线、主播、字幕全面升级
- 9:16 竖屏动画模板库

**核心价值**：解决"视频视觉效果是否足够吸引人"的问题，强化产品展示力和 Demo 效果

**收益**：
- 视觉效果接近专业级短视频
- 动画过渡更流畅自然
- 可做更复杂的信息图动画

**风险**：
- 工程复杂度高（React + TypeScript + Remotion）
- Render cost 大幅增加
- 动画调试周期长
- 与现有 Python renderer 并存需要维护两套 path
- Playwright screenshot 方案 vs Remotion 方案的取舍

---

### Route D：多用户产品化

**目标**：
- 用户登录 / 账号体系
- 项目/任务云端存储
- 云端文件管理（MP4、音频、素材包）
- 异步任务队列与状态同步
- 权限管理 / 计量计费

**核心价值**：支持多用户协作、商业化交付

**风险**：
- 过早产品化 — 核心价值（内容质量）还未验证充分
- 运维和安全成本高
- 需要数据库、对象存储、CICD
- 用户增长前先背运营成本

---

## 3. 路线对比总结

| 路线 | 核心解决 | 成本 | 推荐优先级 |
|------|----------|------|-----------|
| A 真实新闻采集 | 信息源自动化 | 中 | **第一优先** |
| B Real LLM/TTS | 内容质量 | 高 | **第二优先** |
| C Remotion 视觉 | 视觉效果 | 高 | 暂缓 |
| D 多用户产品化 | 商业化 | 极高 | 暂缓 |

---

## 4. 优先级建议

### 推荐结论

**第一优先级：Route A + Route B 的最小可行组合**

### 理由

1. **新闻视频产品的根本价值 = 信息质量 + 内容表达**
   - 信息质量靠 Route A（真实来源）
   - 内容表达靠 Route B（LLM/TTS）
   - 两者缺一不可，但 Route A 更基础

2. **视觉动画（Route C）可以后置**
   - 当前已有可导出 MP4（Python renderer）
   - 视觉再好，内容不好也没意义
   - Route C 应在内容链路稳定后再做

3. **多用户产品化（Route D）必须后置**
   - 单用户价值还没完全验证（内容质量还没解决）
   - 过早 SaaS 会背负运营成本却无核心壁垒
   - 等 Route A+B 验证后再做不迟

### 暂不优先 Remotion 的原因

- 当前 renderer 已能验证端到端
- Remotion 适合在内容链路稳定、内容质量达标后再引入
- 引入 Remotion 会增加工程复杂度（React/TS 技术栈）
- 视觉提升的边际价值 < 内容质量提升的边际价值

### 暂不优先多用户产品化的原因

- 当前产品定位是"本地单用户工作台"
- 核心壁垒还没建立（内容质量 + 信息源）
- 过早产品化分散研发注意力
- MVP 阶段应聚焦核心价值验证

---

## 5. 推荐下一阶段目标（CP53–CP60 草案）

### CP53：Real Source Feed Snapshot MVP
- 选择 5–8 个官方来源（RSS 或静态 HTML）
- 每日候选 snapshot 生成
- source_candidates_v1 schema
- **不做**：视频生成、LLM、TTS、发布

### CP54：Source Candidate Review UI
- 候选新闻列表展示
- 人工筛选 / 标记
- 一键加入 URL 草稿篮
- **不做**：自动筛选、自动生成视频

### CP55：LLM Script Draft Spike
- 基于 selected candidates 生成 episode_script_draft_v1
- 加 facts guard（事实核查提示）
- 对比规则生成 vs LLM 生成效果
- **不做**：自动可信事实补全、不做发布

### CP56：TTS Audio Draft Spike
- 基于 script draft 生成音频草稿和 audio_manifest
- 接入音频 mux 到已有 MP4
- **不做**：大规模批量合成

### CP57：Subtitle / Caption Track
- 从 script/audio manifest 生成字幕轨（SRT/VTT）
- **不做**：复杂 ASR 对齐

### CP58：Visual Polish / Remotion Spike
- 选择 1 个模板尝试 Remotion render
- 对比 Python renderer vs Remotion
- **不做**：全量替换 renderer

### CP59：Publishing Package v2
- 基于真实 LLM 内容生成更完整平台文案
- 平台差异化适配（抖音 vs B站 vs YouTube）
- **不做**：自动发布 API

### CP60：MVP v0.2 Freeze
- 冻结第二阶段闭环
- 完整测试 + 演示验证

---

## 6. CP52 决策结论

**下一阶段优先做：真实来源采集 + 人工筛选 + real LLM/TTS 小步接入**

- 不直接做多用户 SaaS
- 不直接重构 Remotion
- 不接入未经验证的新闻 API
- 保持本地 MVP 定位，聚焦内容链路质量
