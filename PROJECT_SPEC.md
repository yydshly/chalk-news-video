# PROJECT_SPEC

## 目标

把一条新闻 → 自动生成一段黑板风格的讲解动画视频 (`output.mp4`)，无需手动剪辑。

## 核心架构原则

1. **LLM 不输出坐标**：LLM 只产出结构化的 `semantic_ir`。
2. **semantic_ir 不含 x/y/w/h**：只描述新闻结构（节点、边、callout、beats）。
3. **layout.py 是坐标唯一来源**：把 `semantic_ir` 转成 `render_ir` (带坐标)。
4. **renderer/template.html 只播 render_ir**：HTML 内不调用 LLM，只消费 JSON。
5. **export_video.py 只负责导出**：HTML → MP4 的物理过程，不参与语义。
6. **timeline 由 beats 驱动**：layout/pace 不再用 nodes 推时间，全部从 `semantic_ir.beats` 算。

## 数据流

```
[抓取 / LLM]  →  semantic_ir.json
                    │
                    ▼
              layout.py  ← 唯一负责坐标
                    │
                    ▼
              render_ir.json
                    │
              pace.py (compute_timeline_from_beats)  ← 只读 beats
                    │
                    ▼
              render_html.py  ──  Jinja2 注入  ──▶  animation.html
                                                          │
                                                          ▼
                                    export_video.py (Playwright + FFmpeg)
                                                          │
                                                          ▼
                                                    output.mp4
```

## semantic_ir 契约（schema_version 0.1）

```json
{
  "schema_version": "0.1",
  "meta": {
    "source_title": "...",
    "source_url": "...",
    "source_name": "...",
    "published_at": "...",
    "lang": "zh"
  },
  "structure_type": "causal_chain",
  "title": "...",
  "summary": "...",
  "nodes":  [{"id": "n1", "label": "...", "sub": "...", "role": "source|target|neutral"}],
  "edges":  [{"id": "e1", "from": "n1", "to": "n2", "label": "..."}],
  "callouts": [{"id": "c1", "on": "n1", "text": "...", "tone": "info|alert|positive"}],
  "beats":  [{"id": "b1", "reveal": "title|n1|e1|c1|...", "narration": "..."}]
}
```

约束：
- `structure_type` 当前只支持 `causal_chain`
- `nodes` 数量 2~5
- `edges` / `callouts` 可为空数组，但字段必须存在
- `beats` 至少 1 个
- 任何层级都不允许出现 `x`、`y`、`w`、`h`、`cx`、`cy`
- `additionalProperties: false`（除 meta 列出的字段外不允许额外键）

## V0.5 范围（IR 契约校准）

包含：
- 新 semantic_ir 契约（`schema_version` / `meta` / `structure_type` / `beats`）
- `pace.compute_timeline_from_beats` 为唯一时间源
- `layout.build_render_ir` 按 `structure_type` 分发
- 边的 `id` / `label` 进入 render_ir
- callout 的 `on` 取代旧的 `attach_to`
- template.html 基于 `timeline.reveal` 决定元素出现
- 已显示元素保持弱可见，不消失

不包含（仍是后续 Checkpoint）：
- 真实新闻抓取 (Checkpoint 1)
- LLM 生成 semantic_ir (Checkpoint 2)
- semantic_ir schema 运行时校验 (Checkpoint 3)
- TTS / 数字人 / 多主题 / Remotion

## 画布与时间

- 画布：1280 × 720
- fps：30
- 字幕：底部 60px
- 背景：黑板风格 (#143b2e + 网格)
- 标题：粉笔白 (#f8f8f2)
- 节点：米色卡片 (#fff8dc) + 阴影
- callout 配色：`tone=info` 黄 / `tone=alert` 橙 / `tone=positive` 绿

## 文件清单

| 文件 | 职责 |
|------|------|
| `examples/sample.semantic.json` | 符合新契约的演示输入 |
| `src/layout.py` | 唯一负责坐标，分发 structure_type |
| `src/pace.py` | `compute_timeline_from_beats` 唯一时间源 |
| `src/render_html.py` | Jinja2 注入 render_ir |
| `src/export_video.py` | Playwright + FFmpeg |
| `src/pipeline.py` | 串联 + CLI |
| `renderer/template.html` | 播放器，按 reveal 控显隐 |
| `schema/semantic_ir.schema.json` | 0.1 契约定义 |
