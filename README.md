# chalk-news-video

把一条新闻自动生成黑板风格的讲解动画视频 (output.mp4)。

## 项目定位

V0.1: 用一条手写 `sample.semantic.json`，跑通 layout → render_html → export_video 的完整链路。

不包含（后续 Checkpoint）：
- 真实新闻抓取 (fetch_news)
- LLM 调用
- TTS / 数字人 / 多新闻 / 多主题
- Remotion

## 架构原则

```
semantic_ir.json (新闻结构, 无坐标)
        │
        ▼
   layout.py + pace.py
        │
        ▼
   render_ir.json (带坐标 + 时间)
        │
        ▼
   render_html.py  ── Jinja2 ──▶  animation.html (renderer/template.html 渲染)
        │
        ▼
   export_video.py ── Playwright + FFmpeg ──▶  output.mp4
```

LLM 永远不输出坐标；layout.py 唯一负责坐标。

## 安装

```bash
cd chalk-news-video
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

还需要安装 FFmpeg，并加入 PATH：
- Windows: `choco install ffmpeg` 或从 https://ffmpeg.org/download.html 下载
- macOS: `brew install ffmpeg`
- Linux: `sudo apt install ffmpeg`

## 运行

```bash
python -m src.pipeline --use-sample
```

产物：

```
outputs/latest/render_ir.json
outputs/latest/animation.html
outputs/latest/output.mp4
```

## 当前 Checkpoint

详见 [PROJECT_SPEC.md](PROJECT_SPEC.md) 和 [BACKLOG.md](BACKLOG.md)。
