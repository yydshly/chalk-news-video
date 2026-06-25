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

---

## CP41.2: Result Panel Capability Navigation / Empty State Polish

### What was added

The right-side result panel was reorganized to make product tabs and debug tabs visually distinct, and every tab received a clear empty-state message that tells the user what action to take.

#### Tab group structure

**结果 (Main results)** — prominent styling:
- 视频预览
- 栏目计划
- 栏目脚本
- 音频计划
- 视觉计划
- 历史作品

**调试数据 (Debug data)** — subdued styling with permanent hint:
- render_ir
- semantic_ir
- dialogue_script

A `result-panel-guide` box at the top of the result panel explains what the area contains.

#### Empty states

Each product tab shows a guide box when empty:

| Tab | Empty state title | Guidance |
|---|---|---|
| 视频预览 | 还没有视频预览 | 点击左侧「生成快速预览」或在合集区点击「预览合集画面」 |
| 栏目计划 | 还没有栏目计划 | 在左侧「规划」中点击「查看栏目计划」 |
| 栏目脚本 | 还没有栏目脚本 | 在左侧「规划」中点击「生成栏目脚本草案」 |
| 音频计划 | 还没有音频计划 | 在左侧「规划」中点击「生成音频计划」 |
| 视觉计划 | 还没有视觉计划 | 在左侧「规划」中点击「生成视觉计划」 |
| 历史作品 | 暂无历史作品 | 生成或导出后会在这里出现 |

Debug tabs show a persistent hint: "这是工程调试数据，普通用户可以忽略。"

#### JS empty-state control

- `setTabEmptyState(tabId, isEmpty)` — hides/shows the empty-state div for a given tab
- `updateTabEmptyState(tabId)` — called on tab switch; checks whether the content `pre` element already has text and toggles the empty state accordingly
- `showPreview()`, `clearPreview()`, `showEpisodePlan()`, `showEpisodeScript()`, `showEpisodeAudioManifest()`, `showEpisodeRenderIr()` all call `setTabEmptyState` to hide the empty state when content is populated
- `loadHistory()` manages the history empty state based on API response

### Files changed

- `web/index.html` — restructured tabs into `result-tabs-main` and `result-tabs-debug` groups; added `result-panel-guide`, `debug-tabs-hint`, and empty-state `div` elements
- `web/style.css` — new `.result-panel-guide`, `.result-nav-section`, `.result-nav-label`, `.result-tabs-main`, `.result-tabs-debug`, `.debug-tabs-hint`, `.result-empty-state` styles
- `web/app.js` — new empty-state DOM refs, `setTabEmptyState()` and `updateTabEmptyState()` helpers, calls wired into all content-generating functions
- `docs/CP41_STUDIO_CAPABILITY_DASHBOARD.md` — this section

### Design principles

- All original `data-tab` values are preserved — the existing tab-switching JS (`tabBtns.forEach + click`) continues to work unchanged
- All original content `pre` IDs (`json-episode_plan`, `json-episode_script`, etc.) are preserved
- Debug tabs use subdued colors so they are visually de-emphasized without being hidden
- Empty states are dashed-border boxes that match the dark theme, not alarming error states
- Tab group labels ("结果", "调试数据") provide orientation without adding engineering jargon to button labels

### What was not changed

- No backend (`server.py`, `episode_export.py`, `render_episode_html.py`, `export_video.py`) was modified
- No renderer was modified
- No MP4 export logic was changed
- No real LLM or real TTS integration was added
- No Remotion was introduced
- No真实生成物 were committed
- `preview iframe`, `video`, `audio`, export panel, and export history panel all remain fully functional

---

## CP41.3: First-run Guidance / Demo Path

### What was added

A new `first-run-guide` section was added between the capability dashboard and the main layout, giving new users a clear 6-step "fastest path to see a result" without requiring any configuration.

### UI structure

The guide appears as a card below the CP41 dashboard and above the input/result panels. It contains:

**Header** — eyebrow label, title, one-line description, and a collapse/expand button.

**6-step grid** — step cards for each phase of the workflow:
1. 选新闻
2. 加入合集
3. 规划
4. 预览
5. 导出 MP4 (highlighted in green as the active/export step)
6. 查看历史

**Boundary note** — a yellow-highlighted note clarifying which capabilities are real vs mock.

### Optional collapse state

A lightweight localStorage-based collapse button lets users hide the guide after they have used the app once. State is purely client-side and does not affect any backend or API call.

### Files changed

- `web/index.html` — added `#first-run-guide` section with step cards and boundary note
- `web/style.css` — new `.first-run-guide`, `.first-run-guide-header`, `.first-run-steps`, `.first-run-step`, `.first-run-step.is-export`, `.first-run-step-num`, `.first-run-note`, `.first-run-collapse-btn`, `.first-run-guide.is-collapsed` styles
- `web/app.js` — new `initFirstRunGuide()` function and DOM refs; called at the end of `init()`
- `docs/CP41_STUDIO_CAPABILITY_DASHBOARD.md` — this section

### What was not changed

- No backend, renderer, export logic, LLM, TTS, or Remotion integration
- All existing CP41, CP41.1, CP41.2 UI elements remain in place
- The guide does not auto-scroll or navigate — it is purely informational

