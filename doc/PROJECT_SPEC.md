# 新闻讲解动画生成器 — 项目架构与技术方案

> 代号:**Chalk**(暂定,可改)
> 本文档是交付给执行模型(Claude Code / 其他 LLM)的实现规格。执行者应严格按本文档的契约与里程碑推进,不得擅自扩大范围。
> 状态:M0 已完成(手写 IR → 渲染器跑通,见 `explainer_v1_demo.html`)。本文档定义 M1–M3,即 V1 闭环。

---

## 0. 一句话定位

输入一条新闻,自动产出一段"信息被一步步画出来"的风趣讲解动画(黑板/讲课风格,带旁白文案)。

## 1. 核心论断(整个项目的难点在哪)

这个项目的难度**高度集中在一个转换上**:

```
新闻原文  ──(LLM 理解)──►  结构化编排 IR
```

也就是:让模型读懂一条新闻的**逻辑骨架**(是因果链?对比?时间线?数据增长?),再把这个骨架翻译成"先画哪个方块、箭头从哪连到哪、重点划在哪、第几拍出现"。

**除此之外的一切——渲染、配音、抓截图、换皮肤——都是这个转换周围的管道工程,技术风险低。** 本项目的全部设计,都是为了把这个唯一的难点**隔离出来、单独验证、单独迭代**。任何让这个核心变模糊的需求,一律延后。

---

## 2. V1 范围(P0:不做完不算数)

V1 的唯一目标:**喂一条真新闻,无需手工摆元素,自动产出一段可在浏览器播放的讲解动画。**

P0 必须有:
- 采集:接收一条新闻(纯文本或 URL→正文)。
- 理解与编排:LLM 输出符合 schema 的**语义编排 IR**(只描述结构,不含坐标)。
- 校验与修正:对 IR 做 schema 校验,失败时自动反馈给 LLM 修正(最多 N 次)。
- 布局引擎:把语义 IR 按 `structure_type` 算成带坐标的渲染 IR。
- 渲染器:渲染 IR → 可播放的 HTML/SVG 动画(复用现有 demo 引擎)。
- 旁白:**以字幕形式**呈现风趣讲解文案(V1 不配音)。
- 支持结构类型:`causal_chain`(因果链)+ `comparison`(对比)两种。

**完成定义(DoD):一条命令 `news(文本/URL) → output.html`,打开即播,画面是自动生成的、逐步construct的讲解动画。**

## 3. V1 明确不做(Non-Goals,防膨胀)

以下全部延后,V1 一律不碰。每条都注明原因:

| 不做 | 原因 |
|---|---|
| TTS 真人配音 + 音频时间轴对齐 | 这是版本一(播客)的核心难点,会和"理解→编排"叠加成两个难题同时打。V1 用字幕隔离核心。→ V2 |
| 真实网页截图抓取与清洗 | 素材体力活,会脏。闭环跑通前加它没意义。→ V2 |
| 角落卡通人物 / 立绘 / 表情 | 纯装修,改样式即可,不构成风险也不构成价值。→ 闭环后 |
| 背景/配色/字体多主题 | 同上,改 CSS 变量的事。→ 闭环后 |
| 时间线 / 数据增长 / 拆解 等更多结构类型 | 先用因果链+对比验证编排链路是否成立,再扩。→ 闭环后 |
| 人物对口型 / 图生视频 B-roll | 烧算力、不可控。→ V3+ |
| MP4 导出 | 浏览器预览足够验证 V1。导出是换渲染器后端的事(见 §10)。→ V2/V3 |

> **铁律:在 §2 的闭环跑通一条真新闻之前,上表任何一项都不许动。** 好点子全部进 §14 停车场。

---

## 4. 系统架构

### 4.1 数据流(单向)

```
 [1 采集]            [2 理解与编排]         [3 校验/修正]        [4 布局]            [5 渲染]
新闻文本/URL  ──►  LLM  ──► 语义IR(无坐标) ──► schema校验 ──► 渲染IR(含坐标) ──► HTML/SVG动画
                    ▲            │  失败             │ structure_type
                    └──修正提示──┘                   └─► 布局模板
                                                                            [6 配速]
                                                              每拍 dwell 时长 (V1: 由文案长度估算)
```

### 4.2 三条不可违背的架构决策(承重墙)

1. **IR 是唯一契约。** LLM 只产出 IR,渲染器只消费 IR。两边永不直接耦合。
   - 好处:LLM 可随意更换(MiniMax / MiMo / 任意模型),只要能吐合法 IR 就行;渲染器可独立演进(加主题、加人物)而不动 LLM 层。
2. **语义层与布局层分离 —— LLM 永远不输出坐标。** LLM 只描述"有哪些节点、谁连谁、强调谁、第几拍出现";坐标由确定性的布局引擎按 `structure_type` 模板算出。
   - 原因:LLM 的空间排版能力很差,让它写 x/y 必然重叠错乱;但它擅长理解关系。让它干它擅长的。
3. **单向数据流。** 渲染器绝不回调 LLM;布局层绝不理解语义。每一层只依赖上游产物。
   - 好处:每一层都能独立测试。手写 IR 就能测渲染器(M0 已证明);不渲染就能校验 IR。

---

## 5. 编排 IR Schema v0.1(本项目的心脏)

**语义层 IR**(LLM 产出,严禁出现任何坐标/像素值):

```jsonc
{
  "schema_version": "0.1",
  "meta": { "source_title": "string", "source_url": "string|null", "lang": "zh" },
  "structure_type": "causal_chain",   // V1: causal_chain | comparison
  "title": "string",                  // 黑板标题
  "tone": "witty",                    // 旁白语气
  "nodes": [                          // 图元:概念方块,2–5 个
    { "id": "string", "label": "string", "sub": "string|null", "role": "source|target|neutral" }
  ],
  "edges": [                          // 关系:节点间连线(causal_chain/comparison 用)
    { "id": "string", "from": "nodeId", "to": "nodeId",
      "label": "string|null", "emphasis_span": "string|null" }  // emphasis_span 是 label 里要高亮的子串
  ],
  "callouts": [                       // 旁注气泡(挂在某节点旁)
    { "id": "string", "on": "nodeId", "text": "string", "sub": "string|null",
      "tone": "alert|info|positive" }
  ],
  "beats": [                          // 编排时序:每拍揭示一个元素 + 一句旁白
    { "reveal": "elementRef|null", "narration": "string" }
  ]
}
```

**约束(校验规则):**
- `nodes` 数量 2–5。超过则要求 LLM 合并或拆成多段。
- 每个 `edges.from/to` 必须指向存在的 `nodeId`;`callouts.on` 同理。
- `beats[].reveal` 取值:`null`(只配旁白不揭示新元素)、节点/边/旁注的 `id`、或子元素引用 `"<edgeId>.label"` / `"<edgeId>.emphasis"`(把一条边拆成"画线→出标签→划重点"多拍,这正是"逐步construct"的来源)。
- `beats` 必须覆盖所有 `nodes/edges/callouts`(否则有元素永不出现)。
- `narration` 每句建议 ≤ 40 字,风趣口语,可含一处 `<b>…</b>` 重点标记。

**配速层(非 LLM 产出,由配速 pass 计算):** 给每拍算 `at`(出现时刻 ms)。V1 规则:`dwell = clamp(每字 90ms × 文案字数, 1800ms, 5000ms)`,累加得 `at`。V2 改为由 TTS 每句音频实际时长回填(这就是之前讲过的"音频—时间轴耦合",到 V2 才处理)。

---

## 6. 目标实例(执行者照此对齐)

挪威 AI 招聘新规这条新闻,正确的语义 IR 应该长这样:

```json
{
  "schema_version": "0.1",
  "meta": { "source_title": "挪威立法限制 AI 招聘筛选", "source_url": null, "lang": "zh" },
  "structure_type": "causal_chain",
  "title": "挪威 · AI 招聘新规",
  "tone": "witty",
  "nodes": [
    { "id": "gov", "label": "挪威政府", "sub": "立法者·出手方", "role": "source" },
    { "id": "biz", "label": "企业 / HR", "sub": "被约束方", "role": "target" }
  ],
  "edges": [
    { "id": "e1", "from": "gov", "to": "biz", "label": "禁止用 AI 自动筛简历", "emphasis_span": "自动" }
  ],
  "callouts": [
    { "id": "c1", "on": "biz", "text": "合规成本 ↑↑", "sub": "HR 集体头大", "tone": "alert" }
  ],
  "beats": [
    { "reveal": "title",       "narration": "来,今天第一条——<b>挪威</b>搞了个大动作。" },
    { "reveal": "gov",         "narration": "主角登场:挪威政府,这回亲自下场立法。" },
    { "reveal": "e1",          "narration": "矛头直接指向……" },
    { "reveal": "biz",         "narration": "企业,尤其是 HR 部门。" },
    { "reveal": "e1.label",    "narration": "新规:不准用 AI <b>自动</b>筛简历。" },
    { "reveal": "e1.emphasis", "narration": "重点全在'<b>自动</b>'——人能看,机器不能替你拍板。" },
    { "reveal": "c1",          "narration": "于是 HR 集体头大:合规成本蹭蹭往上涨。" },
    { "reveal": null,          "narration": "想偷懒的 AI,这回先被一纸法律按住了。(笑)" }
  ]
}
```

这份 IR 喂进布局+渲染,应当还原出 `explainer_v1_demo.html` 的效果。**M0 已证明渲染器能吃这种结构,所以这是个已知可达的目标,不是赌博。**

---

## 7. 布局引擎(structure_type → 坐标)

输入语义 IR,输出每个元素的坐标/朝向。确定性,无随机,无 LLM。V1 实现两个模板:

- **`causal_chain`**:节点沿水平轴等距排布(画布宽度按节点数均分),相邻节点间画箭头;边标签居于箭头上方居中;callout 落在其挂靠节点正下方。支持 2–5 节点。
- **`comparison`**:画布左右两半,两个(组)节点对置;中间可放一条对比轴或 VS 标记;callout 在各自半区下方。

> 实现建议:V1 用手写模板足够且更可控。节点数多、关系复杂时再考虑引入图布局库(dagre / elkjs)。**但这是 P1,不在 V1。**

输出的渲染 IR = 语义 IR + 每个元素一个 `{x,y,w,h,rotate}` + 每拍的 `at`。

---

## 8. 渲染器契约(IR → HTML/SVG)

直接演进现有 `explainer_v1_demo.html`,把"硬编码的 SVG"改成"按渲染 IR 动态生成 SVG"。元素类型 → 动画 op 的映射(已在 demo 验证):

| IR 元素 | 渲染为 | 揭示动画 |
|---|---|---|
| node | 圆角方块 + label + sub | `pop`(弹入,带轻微旋转) |
| edge(线) | 粉笔笔触路径 + 箭头 | `draw`(stroke-dashoffset 自绘) |
| edge.label | 标签文字 + 荧光底 | `swipe`(荧光笔扫入) |
| edge.emphasis | emphasis_span 下的强调线 | `draw`(珊瑚色划线) |
| callout | 气泡框 | `pop` + 挂靠节点可 `shake` |
| title | 标题 + 下划线 | `pop` + 下划线 `draw` |

时序:渲染器读每拍 `at`,用一个时钟(`requestAnimationFrame`)累积揭示——`at ≤ 当前时间` 的元素全部点亮(讲课是**叠加**不是替换)。这套机制 demo 里已经跑通,照搬即可。

主题(背景/配色/字体)全部走 CSS 变量,换皮即换一组变量——但 V1 只保留黑板一种。

---

## 9. LLM 编排层(prompt + 修正环)

这是核心难点所在,执行者要把功夫下在这里。

**Prompt 骨架(给编排 LLM):**
1. 角色设定:你是一个把新闻转成讲解分镜的编导。
2. 任务:读下面这条新闻,判断它的逻辑骨架属于哪种 `structure_type`,然后输出严格符合 schema 的语义 IR。
3. **硬约束:只输出 JSON,不要坐标,不要任何解释文字;节点 2–5 个;beats 覆盖所有元素;旁白风趣口语 ≤40 字。**
4. 给 1–2 个完整 few-shot 范例(用 §6 这种)。
5. Schema 定义原文(§5)。

**修正环:**
```
llm_output → JSON 解析 → schema 校验
  ├─ 通过 → 进入布局
  └─ 失败 → 把具体错误(哪条规则违反)拼回 prompt,让 LLM 重出;最多重试 3 次;仍失败则报错并落盘原始输出供人工查看。
```

> 这一层的质量(LLM 能否从杂乱新闻里抽出像样的、非平凡的结构)是项目第一风险。**先用 5–10 条真实新闻人工评估它的 IR 质量,再往下做配音、装修。**

---

## 10. 技术栈与边界

| 层 | 选型 | 理由 |
|---|---|---|
| 采集 / 编排 / 校验 / 布局 / 配速 | **Python** | 你的主场;LLM 调用、JSON 处理、正文抽取(trafilatura/readability)都顺手。 |
| 渲染器 | **独立 HTML/SVG/JS 单文件**,无构建步骤 | demo 已成立,零依赖,双击即看,改起来快。 |
| 层间边界 | **IR JSON 文件** | Python 写出 `render_ir.json`,HTML 读它渲染。彻底解耦。 |
| (V2/V3)MP4 导出 | 届时把 HTML 渲染器换成 **Remotion**(React/TS)消费同一份 IR | 因为有 IR 契约,这是一次干净替换,不动编排层。 |

> 不引入 LiteLLM 这类重封装(你之前评估过太重)。一个薄薄的 `llm_client.py`,按你常用模型封一个 `chat(prompt) -> str` 即可。

---

## 11. 建议仓库结构

```
chalk/
  README.md
  PROJECT_SPEC.md            # 本文档,项目宪法
  BACKLOG.md                 # §14 停车场,V1 期间只进不出、不开工
  schema/
    ir_semantic.schema.json  # §5 语义层 JSON Schema
    ir_render.schema.json    # 布局后的渲染 IR
  src/
    fetch.py                 # 采集:URL→正文
    orchestrate.py           # 调 LLM,产出语义 IR
    validate.py              # schema 校验 + 修正环
    layout.py                # structure_type → 坐标(causal_chain / comparison)
    pace.py                  # 每拍 at 时长
    pipeline.py              # 串起来:news → render_ir.json
  renderer/
    index.html               # 渲染器(由 explainer_v1_demo.html 演进)
    render.js                # 读 render_ir.json → 生成 SVG + 时钟
    theme.css                # CSS 变量(V1 仅黑板)
  examples/
    norway.semantic.json     # §6 目标实例,回归测试基准
  fixtures/
    news_samples/            # 5–10 条真实新闻,用于评估编排质量
```

---

## 12. 里程碑(逐级闸门,前一个绿了才做下一个)

- **M0 ✅ 已完成**:手写 SVG 动画跑通(`explainer_v1_demo.html`)。证明渲染契约成立。
- **M1 冻结 schema + 渲染器吃 IR**:定稿 §5/§7 的 schema;把 demo 改成读 `render_ir.json` 动态渲染。手写 2–3 份渲染 IR,确认都能正确还原。**闸门:手写 IR → 正确动画。**
- **M2 布局引擎**:实现 `causal_chain` + `comparison`;输入**语义 IR(无坐标)**→ 输出渲染 IR → 渲染。**闸门:§6 的语义 IR 不含坐标也能渲染成 demo 效果。**
- **M3 编排 LLM + 闭环(= V1 完成)**:写 §9 的 prompt + 修正环;`pipeline.py` 串通 `news → 语义IR → 校验 → 布局 → 配速 → output.html`。拿**一条真新闻**端到端跑出无声讲解动画。**闸门 = §2 的 DoD。**

V1 之后(不在本规格,仅记录方向):M4 接 TTS + 音频时间轴对齐;M5+ 从 BACKLOG 取项(主题、人物、截图、更多结构类型)。

---

## 13. 验收标准(Given/When/Then)

V1 整体:
- Given 一条真实新闻文本或 URL
- When 运行 `python -m src.pipeline <输入>`
- Then 生成 `output.html`,打开点播放,能看到:标题自绘 → 概念方块按拍弹入 → 关系箭头自绘 → 重点被划/扫 →(若有)旁注弹出,旁白字幕逐拍切换,语气风趣;**全程无需人工调整任何元素位置。**

分项检查清单:
- [ ] 采集能把一个新闻 URL 抽成干净正文。
- [ ] LLM 对 5–10 条样本新闻,IR 校验通过率 ≥ 80%(失败的能被修正环救回)。
- [ ] 语义 IR 中**不含任何坐标字段**(架构红线,违反即不通过)。
- [ ] 布局引擎对 2、3、4、5 个节点都不重叠、不出画。
- [ ] 渲染器对 `examples/norway.semantic.json` 还原出与 demo 一致的效果(回归基准)。
- [ ] 修正环:故意喂一个缺字段的 IR,能在 ≤3 次内修好或干净报错。
- [ ] 负向:节点 >5 时 LLM 被要求合并而非硬塞。

---

## 14. 风险

1. **(最高)LLM 编排质量。** 杂乱新闻里抽不出像样结构,或抽出来很平庸/牵强。缓解:`structure_type` 模板约束输出空间;高质量 few-shot;校验+修正环;先人工评估 fixtures 再前进;实在不行保留"人工微调 IR"兜底。
2. **布局对任意节点数的鲁棒性。** 缓解:prompt 限制节点 2–5;模板按节点数分档设计;§13 明确测 2/3/4/5。
3. **(V2)音频—时间轴耦合。** 整段自然配音没时间戳 vs 逐句配音丢节奏的取舍——到 M4 再处理,V1 用字幕规避。
4. **(元风险,必须直说)范围蔓延 / 永远不发布。** 这是本项目最大的真实风险。缓解 = §3 Non-Goals + §15 铁律 + §12 闸门。**执行者每收到一个新需求,先问:它在 §2 P0 里吗?不在 → 进 BACKLOG,继续当前里程碑。**

---

## 15. 防膨胀铁律(钉在墙上)

1. V1 全程**静音 + 字幕**。M3 闸门没绿之前,不许碰 TTS。
2. **LLM 永远不输出坐标。** 这条违反即架构破坏。
3. 渲染器**永远不调 LLM**,布局层**永远不懂语义**。单向流。
4. `causal_chain` 没把一条真新闻端到端跑通之前,**不许加任何新 structure_type**。
5. 任何"还可以有……"的丰富度需求,**一律进 BACKLOG.md,且 V1 期间该文件不开工**。
6. V1 的完成定义只有一个:`news → output.html` 一条命令跑通。其余都不是 V1。

---

## 16. BACKLOG / 停车场(V1 只进不出)

按"便宜/中等/贵"已分级,闭环跑通后再按价值取用:

- 便宜:背景/配色/字体多主题化;黑板换材质;角落卡通人物 + 表情切换。
- 中等:真实网页截图抓取 + 去弹窗/裁剪/兜底;配图搜索;更多结构类型(timeline / data_trend / breakdown);场景内引入截图/图片图元。
- 贵:TTS 配音 + 时间轴对齐(其实是 V2 主线,不算装修);人物动作 / 对口型;图生视频 B-roll;MP4 导出 + 转场;批量日更流水线。
