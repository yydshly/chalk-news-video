# PROJECT_SPEC

## 目标

把一条新闻 → 自动生成一段黑板风格的讲解动画视频 (`output.mp4`)，无需手动剪辑。

## 核心架构原则

1. **LLM 不输出坐标**：LLM 只产出结构化的 `semantic_ir` (节点、边、callout、narration)。
2. **semantic_ir 不含 x/y/w/h**：只描述"这条新闻有几个因果节点，分别讲什么"。
3. **layout.py 是坐标唯一来源**：把 `semantic_ir` 转成 `render_ir` (带坐标)。
4. **renderer/template.html 只播 render_ir**：HTML 内不调用 LLM，只消费 JSON。
5. **export_video.py 只负责导出**：HTML → MP4 的物理过程，不参与语义。

## 数据流

```
[抓取/LLM] → semantic_ir.json ──▶ layout.py ──▶ render_ir.json
                                                       │
                                                       ▼
                              render_html.py ◀── Jinja2 注入
                                                       │
                                                       ▼
                                              animation.html
                                                       │
                                                       ▼
                                  export_video.py (Playwright + FFmpeg)
                                                       │
                                                       ▼
                                                 output.mp4
```

## V0.1 范围（Checkpoint 0）

只做最小骨架，让手写 `sample.semantic.json` 跑通到 `output.mp4`。

包含：
- causal_chain 布局
- 单文件 HTML 渲染
- 30fps Playwright 截屏 + FFmpeg 编码
- 中文 narration 节奏估算

不包含（后续 Checkpoint）：
- 真实抓取 (Checkpoint 1)
- LLM 生成 semantic_ir (Checkpoint 2)
- semantic_ir schema 校验 (Checkpoint 3)
- TTS / 数字人 / 多主题 / Remotion

## 画布与时间

- 画布：1280 × 720
- fps：30
- 字幕：底部
- 背景：黑板风格 (深绿 + 白粉笔)

## 文件清单

| 文件 | 职责 |
|------|------|
| `examples/sample.semantic.json` | 手写的语义输入 |
| `src/layout.py` | 坐标生成 |
| `src/pace.py` | 时间节奏生成 |
| `src/render_html.py` | 渲染 animation.html |
| `src/export_video.py` | 导出 mp4 |
| `src/pipeline.py` | 串联 + CLI |
| `renderer/template.html` | 播放器 (单文件自包含) |
