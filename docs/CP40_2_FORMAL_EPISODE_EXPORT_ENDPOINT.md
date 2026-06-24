# CP40.2: Formal Episode Export Endpoint

## 1. Baseline

- **Branch**: `feat/cp40.1-minimal-episode-stage-mp4-export` (commit `318fd3a`)
- CP40.1 validated the local prototype: `render_episode_stage_html_to_file()` + `export_video()` produces a valid 720×1280 MP4.
- CP40.2 extends this into a proper FastAPI endpoint.

## 2. Goal

Expose `POST /api/episode/export` that accepts an `episode_template_v1` contract and returns a downloadable MP4 with proper artifact URLs. No real LLM, no real TTS, no audio mux.

## 3. New Endpoint

```
POST /api/episode/export
GET  /outputs/episode_exports/{export_id}/{filename}
```

**Files changed:**
- `src/episode_export.py` — new service layer module
- `src/server.py` — added endpoints
- `.gitignore` — added `outputs/episode_exports/` protection
- `outputs/episode_exports/.gitkeep` — preserves directory in git
- `scripts/test_episode_export_endpoint.py` — endpoint test
- `docs/CP40_2_FORMAL_EPISODE_EXPORT_ENDPOINT.md` — this document

## 4. Request Contract

```json
{
  "contract": {
    "schema_version": "episode_template_v1",
    "template_id": "breaking_news_v1",
    "episode": { ... },
    "timeline": { ... },
    "sections": { ... }
  },
  "style_id": "breaking_news_v1",
  "width": 720,
  "height": 1280,
  "fps": 30
}
```

**Validation rules:**
- `contract` must be an object with `schema_version == "episode_template_v1"`
- `style_id` must be `"breaking_news_v1"` (only allowed value in CP40.2)
- `width` clamped to 360–1080 (default 720)
- `height` clamped to 640–1920 (default 1280)
- `fps` clamped to 1–30 (default 30)
- `audio_path` is always ignored (CP40.2 produces no audio)

## 5. Response Contract

```json
{
  "status": "completed",
  "export_id": "episode_export_aa8d004e81b6",
  "style_id": "breaking_news_v1",
  "width": 720,
  "height": 1280,
  "fps": 30,
  "mp4_path": "outputs/episode_exports/episode_export_aa8d004e81b6/output.mp4",
  "mp4_url": "/outputs/episode_exports/episode_export_aa8d004e81b6/output.mp4",
  "html_url": "/outputs/episode_exports/episode_export_aa8d004e81b6/animation.html",
  "meta_url": "/outputs/episode_exports/episode_export_aa8d004e81b6/export_meta.json",
  "contract_url": "/outputs/episode_exports/episode_export_aa8d004e81b6/contract.json",
  "mp4_size_bytes": 186061,
  "audio_path": null,
  "created_at": "2026-06-25T07:46:24.672541"
}
```

**Error responses:**
- `400` — invalid contract, unsupported style_id, dimension out of range
- `500` — export_video failure (redacted error message)

## 6. Export Artifact Layout

```
outputs/episode_exports/{export_id}/
  contract.json      — input contract (for traceability)
  animation.html     — rendered 9:16 stage HTML
  output.mp4        — final 720×1280 MP4
  export_meta.json   — export metadata (dimensions, URLs, sizes)
```

Example:
```
outputs/episode_exports/episode_export_aa8d004e81b6/
  output.mp4
  animation.html
  contract.json
  export_meta.json
```

## 7. Security Boundaries

- **export_id**: must match `^episode_export_[a-f0-9]{12}$` — no path traversal
- **filename whitelist**: only `output.mp4`, `animation.html`, `contract.json`, `export_meta.json` are served
- **Path traversal protection**: resolved paths are checked to be under `EPISODE_EXPORT_DIR`
- **No audio_path from client**: audio mux is disabled (always `None`)
- **No client-supplied HTML**: server generates HTML from contract only
- **No API key / voice_id in response**: error messages are redacted via `_redact_secret_text()`

## 8. Reused Components

| Module | Function | Role |
|--------|----------|------|
| `src/render_episode_html.py` | `render_episode_stage_html_to_file()` | Generate self-contained 9:16 HTML |
| `src/export_video.py` | `export_video()` | Playwright + ffmpeg MP4 export |
| `src/server.py` | `EpisodeExportRequest` pydantic model | Request validation |
| `src/server.py` | `_redact_secret_text()` | Error message redaction |

## 9. 9:16 Viewport

Default dimensions are **720×1280** (portrait 9:16). Both Playwright viewport and ffmpeg scale use the passed `width`/`height`. Clamped ranges:

- width: 360–1080
- height: 640–1920
- fps: 1–30

## 10. Test Result

```
POST /api/episode/export → 200 OK
  status: completed
  export_id: episode_export_aa8d004e81b6
  width: 720, height: 1280, fps: 30
  mp4_size_bytes: 186061
  mp4_url: /outputs/episode_exports/episode_export_aa8d004e81b6/output.mp4

GET /outputs/episode_exports/{id}/output.mp4 → 200 video/mp4
GET /outputs/episode_exports/{id}/animation.html → 200 text/html
GET /outputs/episode_exports/{id}/export_meta.json → 200 application/json
GET /outputs/episode_exports/{id}/contract.json → 200 application/json

All checks PASSED
```

Smoke test: `scripts/smoke_test_render_episode_html.py` — All checks passed.

## 11. What CP40.2 Does Not Do

- No web UI integration
- No history UI integration
- No `/api/jobs` integration
- No async status tracking
- No SSE
- No real LLM
- No real TTS
- No real audio mux
- No Remotion
- No uploaded user file support
- No path traversal / arbitrary file access
- No arbitrary audio_path from client

## 12. Known Limitations

- Export is **synchronous** — the request blocks until ffmpeg finishes encoding. For long videos this can be slow. CP40.3 will add async job status.
- `export_video()` currently re-encodes via ffmpeg `-vf scale=W:H` after capture. If Playwright viewport constraints differ, the final size may not match exactly.
- The `outputs/episode_exports/` directory grows indefinitely — no cleanup strategy yet.

## 13. Next Checkpoint

CP40.3: Add async job status for episode export (SSE or polling), so the endpoint returns immediately and clients can poll for completion.
