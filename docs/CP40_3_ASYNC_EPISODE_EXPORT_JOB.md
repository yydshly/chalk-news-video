# CP40.3: Async Episode Export Job

## 1. Baseline

- **Branch**: `feat/cp40.2-formal-episode-export-endpoint` (commit `400701a`)
- CP40.2 added `POST /api/episode/export` — synchronous, blocks until MP4 is ready.
- CP40.3 converts it to async: immediate 202 return + background worker + status polling.

## 2. Goal

Non-blocking episode export via background thread with JSON status file. Client polls `GET /api/episode/exports/{export_id}` until `completed` or `failed`.

## 3. Endpoint Changes

| Method | Path | Change |
|--------|------|--------|
| `POST` | `/api/episode/export` | Now returns `202 Accepted` immediately, runs export in background thread |
| `GET` | `/api/episode/exports/{export_id}` | **New** — returns `status.json` contents |
| `GET` | `/outputs/episode_exports/{export_id}/status.json` | **New** — serves `status.json` as static file |

Existing static file endpoints unchanged:
- `GET /outputs/episode_exports/{export_id}/output.mp4`
- `GET /outputs/episode_exports/{export_id}/animation.html`
- `GET /outputs/episode_exports/{export_id}/contract.json`
- `GET /outputs/episode_exports/{export_id}/export_meta.json`

## 4. Status Model

Four states: `pending` → `running` → `completed` | `failed`

Progress milestones written to `status.json`:

| Progress | Stage |
|----------|-------|
| 0 | pending — Export queued |
| 10 | running — Rendering HTML |
| 50 | running — Exporting MP4 |
| 90 | running — Writing metadata |
| 100 | completed / failed |

## 5. Artifact Layout

```
outputs/episode_exports/{export_id}/
  contract.json      — input contract
  animation.html     — rendered 9:16 stage HTML
  output.mp4        — final 720×1280 MP4
  export_meta.json  — export metadata
  status.json       — job status (pending/running/completed/failed)
```

## 6. Background Worker

`src/episode_export.py` — new functions:

- `write_episode_export_status()` — atomic status.json write with merge from existing
- `read_episode_export_status()` — read status.json, returns None if absent
- `start_episode_export_background()` — creates export_id dir, writes pending status, launches daemon thread
- `_run_episode_export_worker()` — renders HTML → exports MP4 → writes meta → updates status; all errors caught and redacted
- `_redact_secret_text()` — local redaction helper (no cross-module dependency)

CP40.2 sync function `export_episode_contract_to_mp4()` is **preserved** for backward compatibility with scripts.

## 7. Polling Flow

```
Client                    Server
  |                          |
  |-- POST /api/episode/ ----→|
  |   export (body=contract)  |
  |                          | create export_id
  |                          | write status.json (pending)
  |                          | start background thread
  |<-- 202 {export_id, ----|
  |      status_url, mp4_url}
  |
  |-- GET /api/episode/ ----→|
  |   exports/{export_id}    |
  |                          | read status.json
  |<-- 200 {status: pending} |
  |      (poll every 1s)     |
  |                          | [background thread]
  |                          | write status.json (running, 10%)
  |                          | write status.json (running, 50%)
  |                          | write status.json (running, 90%)
  |                          | write export_meta.json
  |                          | write status.json (completed, 100%)
  |
  |-- GET /api/episode/ ----→|
  |   exports/{export_id}    |
  |<-- 200 {status: ----|
  |      completed,           |
  |      result: {mp4_url,   |
  |      html_url, ...}}     |
```

## 8. Error Handling and Redaction

If the worker raises an exception:
- Error message is redacted via `_redact_secret_text()` (removes `sk-` tokens, env var values, voice_ids)
- `status.json` written with `status: "failed"`, `error_type: "export_failed"`, `error_message: "[REDACTED]"`

API error responses from `POST /api/episode/export`:
- `400` — invalid contract / unsupported style_id / validation error
- `500` — unexpected error (message redacted)

## 9. Test Result

```
POST /api/episode/export → 202 Accepted
  export_id: episode_export_e2a738dc9e99
  status_url: /api/episode/exports/episode_export_e2a738dc9e99

Poll sequence:
  poll 1-45: status=running, progress=50, message=Exporting MP4
  poll 46: status=completed, progress=100

All file serving checks PASSED:
  GET output.mp4 → 200 video/mp4
  GET animation.html → 200 text/html
  GET export_meta.json → 200 application/json
  GET contract.json → 200 application/json
  GET status.json → 200 application/json

All checks PASSED — export episode_export_e2a738dc9e99 completed successfully
```

Smoke test: `scripts/smoke_test_render_episode_html.py` — All checks passed.

## 10. What CP40.3 Does Not Do

- No web UI integration
- No history UI integration
- No `/api/jobs` integration
- No SSE
- No real LLM
- No real TTS
- No real audio mux
- No Remotion
- No uploaded user file support

## 11. Known Limitations

- Progress reporting for the HTML rendering step (progress=10) is ephemeral — by the time a client polls, the background thread has usually already moved past it.
- No per-frame progress within ffmpeg encoding (stays at 50% during entire MP4 export).
- No cleanup strategy for old export directories under `outputs/episode_exports/`.
- Daemon threads are terminated abruptly when the server process exits.

## 12. Next Checkpoint

CP40.4: Add audio mux support to episode export — accept optional `audio_path` parameter, mux WAV/MP3 into MP4 using ffmpeg.
