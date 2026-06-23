# chalk-news-video

把一条新闻自动生成黑板风格的讲解动画视频 (output.mp4)。

## V0.5：IR 契约已校准

`semantic_ir` 现在是正式契约（`schema_version: "0.1"`），未来 LLM 会输出它，fetch_news 会产出它。
当前演示版 `examples/sample.semantic.json` 已经按新结构组织：3 节点 / 2 边 / 2 callout / 8 beats。

不再做的事：
- LLM 不允许输出坐标（任何 `x/y/w/h/cx/cy` 都会被 schema 拒绝）
- `layout` 字段已废弃，改用 `structure_type`
- `nodes[].narration` 已废弃，narration 全部来自 `beats`
- `callouts[].attach_to` 已废弃，改用 `callouts[].on`

## 项目定位

V0.5: IR 契约稳定，pipeline 仍能 `python -m src.pipeline --use-sample` 跑通到 `output.mp4`。

不包含（后续 Checkpoint）：
- 真实新闻抓取 (Checkpoint 1)
- LLM 调用 (Checkpoint 2)
- IR schema 运行时校验 (Checkpoint 3)
- TTS / 数字人 / 多新闻 / 多主题 / Remotion

## 架构

```
semantic_ir.json (无坐标, 含 beats)
        │
        ▼
   layout.py  +  pace.compute_timeline_from_beats
        │
        ▼
   render_ir.json (带坐标 + 时间)
        │
        ▼
   render_html.py  ── Jinja2 ──▶  animation.html  (renderer/template.html 渲染)
        │
        ▼
   export_video.py  ── Playwright + FFmpeg ──▶  output.mp4
```

唯一允许产出坐标的地方：`layout.py`。
唯一允许产生时间的地方：`pace.compute_timeline_from_beats`。

## 安装

```bash
cd chalk-news-video
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

还需要 FFmpeg 加入 PATH：
- Windows: `choco install ffmpeg`
- macOS:   `brew install ffmpeg`
- Linux:   `sudo apt install ffmpeg`

## 运行

```bash
python -m src.pipeline --use-sample
```

可选：
- `--semantic-ir path/to/file.json`
- `--no-headless`（调试用，可见 Chromium）

## 产物

```
outputs/latest/render_ir.json
outputs/latest/animation.html
outputs/latest/output.mp4
```

## 当前 Checkpoint

详见 [PROJECT_SPEC.md](PROJECT_SPEC.md) 和 [BACKLOG.md](BACKLOG.md)。
