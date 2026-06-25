# CP40.8: Episode Export E2E Regression Suite

## 1. Baseline

- **Branch**: `fix/cp40.7.1-load-export-capabilities-on-init` (commit `725c9bb`)
- CP40.7 added export style picker, capabilities API, and preview/export style mismatch hint.
- CP40.7.1 fixed the `init()` call so capabilities load on page startup.
- This CP (40.8) adds a single end-to-end regression test that covers all episode export functionality from CP40.2 through CP40.7.1.

## 2. Why This Exists

Before CP40.8, episode export had multiple scattered test scripts:

- `scripts/smoke_test_render_episode_html.py` — smoke test only
- `scripts/test_episode_export_endpoint.py` — covers CP40.3 async flow
- `scripts/test_episode_export_audio_mux.py` — covers CP40.6 audio mux

There was no single test that could answer: *"Does episode export as a whole still work?"*

CP40.8 introduces `scripts/test_episode_export_e2e.py` as the canonical regression suite for all episode export functionality.

## 3. Covered Checkpoints

| Checkpoint | Feature | Tested by |
|---|---|---|
| CP40.2 | Formal async export endpoint | E2E |
| CP40.3 | Async status via status.json | E2E |
| CP40.3.1 | Status metadata persistence | E2E |
| CP40.4 | Frontend export polling | Not browser-tested |
| CP40.5 | History / delete / cleanup | E2E |
| CP40.6 | Audio mux via audio_url | E2E |
| CP40.6.1 | Metadata path safety | E2E (implicit) |
| CP40.6.2 | ffprobe audio stream verification | E2E |
| CP40.7 | Capabilities API / style guard | E2E |
| CP40.7.1 | Capabilities loaded on init | Not browser-tested |

## 4. Test Script

```
scripts/test_episode_export_e2e.py
```

Run with:
```bash
python scripts/test_episode_export_e2e.py
```

The script uses `fastapi.testclient.TestClient` against the real `server.app` — no mocks for the HTTP layer.

## 5. Test Phases

### Phase 1: Capabilities API
- `GET /api/episode/export/capabilities` returns 200
- `ok == True`
- `default_style_id == "breaking_news_v1"`
- `supported_styles` contains only `breaking_news_v1`
- `unsupported_styles` lists all 4 non-exportable preview styles
- `audio.supports_audio_mux == True`
- Limits are correctly declared

### Phase 2: Security Guards
- `style_id: "research_briefing_v1"` → 400 with `error_type: "invalid_style_id"`
- Invalid `audio_url` values all raise `ValueError` in `resolve_safe_audio_url()`:
  - External URLs (`https://...`)
  - `file://` URLs
  - Windows absolute paths
  - Path traversal (`/outputs/../../../secret.wav`)
  - Wrong extensions (`.txt`, `.flac`)
  - `None` and `""` return `None` (no audio mux, correct)

### Phase 3: Pending Delete Protection
- A pending export is created via `write_episode_export_status()`
- `DELETE /api/episode/exports/{id}` returns `{ok: False, error: "...pending..."}`
- Confirms running/pending exports cannot be deleted

### Phase 4: Async Export Without Audio
- POST with no `audio_url` → 202
- Poll until `completed`
- `result.has_audio == False`
- `export_meta.json.has_audio == False`
- `export_meta.json.audio_url == None`
- `GET /outputs/.../output.mp4` → 200, `video/mp4`
- `GET /outputs/.../animation.html` → 200
- Export ID appears in history list

### Phase 5: Async Export With Audio
- Generates 1-second silence WAV at `outputs/test_audio/cp40_8_silence.wav`
- POST with `audio_url: "/outputs/test_audio/cp40_8_silence.wav"` → 202
- Poll until `completed`
- `result.has_audio == True`
- `export_meta.json.has_audio == True`
- `export_meta.json.audio_url == /outputs/test_audio/cp40_8_silence.wav`
- `export_meta.json.audio_ext == ".wav"`
- `export_meta.json.audio_size_bytes > 0`
- `output.mp4` exists at expected path
- If `ffprobe` is installed: `has_audio_stream(mp4_path)` passes
- If `ffprobe` is not installed: prints SKIP, test continues

### Phase 6: Delete Export
- `DELETE /api/episode/exports/{id}` → 200 `{ok: True, deleted: True}`
- Subsequent `GET /api/episode/exports/{id}` → 404

### Phase 7: Cleanup Endpoint (dry_run)
- `POST /api/episode/exports/cleanup` with `dry_run: True`
- Returns `{ok: True, dry_run: True, deleted_count: ..., skipped: [...]}`
- No actual deletions occur

### Phase 8: Invalid Export ID Handling
- Malformed IDs (`bad`, `episode_export_123`, `episode_export_gggggggggggg`) → 400/404
- Confirms export_id validation works

## 6. ffprobe Handling

```python
ffprobe = shutil.which("ffprobe")
if ffprobe:
    assert has_audio_stream(mp4_path)  # raises on failure
    print("[PASS] ffprobe confirmed audio stream")
else:
    print("[SKIP] ffprobe not found — stream-level assertion skipped")
```

If ffprobe is not installed, stream-level verification is skipped but no test fails. All metadata checks still run.

## 7. Cleanup Strategy

The script maintains a `created_export_ids: list[str]` and cleans up in `finally`:

1. `cleanup_test_audio()` — removes `outputs/test_audio/cp40_8_silence.wav`
2. `cleanup_created_exports(created_export_ids)`:
   - First tries `DELETE /api/episode/exports/{id}` for each ID
   - If that fails, falls back to `shutil.rmtree()` on the export directory

This ensures test artifacts don't accumulate in `outputs/episode_exports/`.

## 8. What CP40.8 Does Not Do

- No browser automation (no Playwright, no Selenium)
- No real LLM calls
- No real TTS calls
- No `/api/jobs` integration
- No Remotion
- No cloud storage interactions
- No performance benchmarks
- No frontend UI testing (capabilities init is backend-tested only)
- Does not implement any new product features

## 9. Manual Run Command

```bash
# Run full E2E suite
python scripts/test_episode_export_e2e.py

# Run alongside other existing tests
python scripts/test_episode_export_audio_mux.py
python scripts/test_episode_export_endpoint.py
python scripts/smoke_test_render_episode_html.py
```

## 10. Known Limitations

- **Pending/running delete protection** is tested for pending status only. A running status is harder to hit reliably in a test because the export completes before we can issue the DELETE request. The pending test proves the guard logic works.
- **Browser init** (`loadEpisodeExportCapabilities()` called on page load) is not browser-tested. It is tested indirectly via the API — the endpoint itself is correct.
- **ffprobe** is optional. Stream-level verification is skipped if ffprobe is absent, but all metadata checks still run.
- The test creates real MP4 files via `export_video()` and ffmpeg. It is not fast.

## 11. Next Checkpoint

CP40.9: Episode Export Concurrent Job Limit — limit the number of concurrent running exports per session to prevent resource exhaustion.
