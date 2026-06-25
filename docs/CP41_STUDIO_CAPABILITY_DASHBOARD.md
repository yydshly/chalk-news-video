# CP41: Studio UI Capability Dashboard

## 1. Baseline

- **Branch**: `fix/cp40.8.1-pending-delete-assertion` (commit `eb240b4`)
- CP40.8 added the E2E regression suite covering all episode export capabilities.
- CP41 reorganizes the UI to make existing capabilities visible and understandable at a glance.

## 2. Problem

The system had accumulated many capabilities (HTML preview, audio mux, MP4 export, history, etc.) but they were scattered across the interface with no unified overview. Users could not quickly tell:

- What was actually working vs. mock
- What the 5-step workflow was
- What the export limitations were
- What each section was for

## 3. Goal

Add a visible capability dashboard at the top of the page that:

1. Shows the 5-step workflow from news input to MP4 export
2. Clearly labels which features are real vs. mock vs. limited
3. Summarizes the current export capabilities (style, audio, format)
4. Does not add any new backend capability

## 4. New UI Sections

### Studio Capability Dashboard (`#studio-capability-dashboard`)

Placed at the top of the main content area, visible immediately on page load. Contains:

**Header** — Title, subtitle, and current stage indicator.

**Flow Guide** — A horizontal 5-step guide:
1. 选择新闻
2. 加入合集
3. 生成计划
4. 预览画面
5. 导出 MP4

Step 5 is highlighted in green to indicate the export phase.

**Capability Grid** — 8 cards categorized as:

- `is-real` (green border): MP4 export, audio mux, export history, HTML preview/save
- `is-mock` (gray border): Mock LLM news understanding, Mock TTS voice
- `is-limited` (gray border): Export style limitation, Remotion/not-connected

**Export Capability Summary** — Dynamically updated from `GET /api/episode/export/capabilities`:
- Supported export style name
- Video aspect ratio (9:16 720×1280)
- Frame rate (30 fps)
- Audio mux support status

### JavaScript: `updateCapabilityDashboard()`

Called from `loadEpisodeExportCapabilities()` after the API response is received. Populates the summary grid with real capability data.

## 5. Real Capabilities (labeled `is-real`)

- **MP4 Export** — Async background export of `output.mp4` at 9:16, 720×1280, 30fps
- **Audio Mux** — Mixes an existing `/outputs/` audio file into the MP4; ffprobe verifies the audio stream
- **Export History** — View, open, delete, and cleanup old exports
- **HTML Preview & Save** — Real-time preview in multiple visual styles; save HTML to local

## 6. Mock / Not Yet Implemented (labeled `is-mock`)

- **Mock LLM News Reasoning** — Generates episode script drafts using mock logic; no real LLM
- **Mock TTS Voice** — Mock dialogue provider used for previews; no real MiniMax TTS in export pipeline

## 7. Limited / Warning (labeled `is-limited`)

- **Export Style** — 5 preview styles exist (timeline, breaking news, data dashboard, research briefing, podcast cards), but MP4 export only supports `breaking_news_v1`
- **Remotion / Cloud Storage** — Not connected; all processing is local

## 8. What CP41 Does Not Do

- Does **not** add any new backend capability
- Does **not** connect real LLM
- Does **not** connect real TTS to the export pipeline
- Does **not** add Remotion renderer
- Does **not** change `episode_export.py` or `server.py`
- Does **not** change `render_episode_html.py` visual logic
- Does **not** add `/api/jobs` integration
- Does **not** submit any files to outputs

## 9. Manual Test

1. Open `http://127.0.0.1:8777`
2. Verify the capability dashboard appears at the top of the page
3. Verify the 5-step flow guide is visible with step 5 highlighted in green
4. Verify 4 green (real), 2 gray (mock), 2 gray (limited) cards are shown
5. Wait for capabilities to load — verify "快讯大屏风" appears in the export style summary
6. Verify audio mux shows "支持（仅 /outputs/ 下音频）"
7. Verify the original episode planner buttons and export functionality are still present
8. Change the preview style — verify the export style hint still updates correctly
9. Verify export history and audio checkbox are unaffected
10. Resize to mobile width — verify cards reflow correctly

## 10. Next Checkpoint

---

## CP41.1: Episode Planner Action Grouping

### What was added

The episode planner's action buttons were reorganized into four clearly-labeled groups:

| Group | Title | Contents |
|---|---|---|
| 1 | 规划 | 查看栏目计划, 生成栏目脚本草案, 生成音频计划, 生成视觉计划 |
| 2 | 预览 | 合集视觉样式 selector, 预览合集画面, 保存合集 HTML |
| 3 | 导出 MP4 | 导出样式 selector, 导出提示, 导出 MP4 按钮, 音频混流 checkbox |
| 4 | 管理 | 提示用户去导出历史查看记录 |

### Design principles

- All original button IDs are preserved — no JS event bindings were changed
- The export group (`is-export`) has a green border to reinforce it as the active capability
- The management group has a blue border and points users to the export history panel
- Buttons remain full-width in their natural column layout
- Preview style selector was moved into the Preview group alongside its related buttons

### Files changed

- `web/index.html` — restructured button DOM into `.episode-action-groups`
- `web/style.css` — new action group styles

### What was not changed

- No JS logic was modified
- No backend logic was modified
- No renderer was modified
- Export style selector, MP4 export button, audio checkbox, export status panel, and export history panel remain fully functional

CP42: Episode Export Concurrent Job Limit — limit the number of concurrent running exports per session.
