# CP40.6: Audio Mux Support

## 1. Baseline

- **Branch**: `feat/cp40.5-episode-export-history-cleanup` (commit `ba71bbf`)
- CP40.5 completed episode export history list, per-item delete, and bulk cleanup.
- CP40.6 adds optional audio mux: when a `dialogue.wav` audio artifact exists in the current preview, it can be muxed into the exported MP4.

## 2. Goal

Support muxing an existing local audio artifact (e.g. `/outputs/jobs/{job_id}/audio/dialogue.wav`) into the episode export MP4, without generating new audio, calling real TTS, or calling real LLM.

## 3. Request Contract

`POST /api/episode/export` body:

```json
{
  "contract": { ... },
  "style_id": "breaking_news_v1",
  "width": 720,
  "height": 1280,
  "fps": 30,
  "audio_url": "/outputs/jobs/job_abc123/audio/dialogue.wav"
}
```

`audio_url` is optional. When `null` or omitted, behavior matches CP40.5 (video-only export).

## 4. Audio URL Safety Rules

`resolve_safe_audio_url(audio_url)` in `src/episode_export.py` enforces:

1. `None` or empty string → `None` (no audio mux)
2. Must start with `/outputs/`
3. No `http://`, `https://`, `file://` protocols
4. No backslash (`\`) — rejects Windows absolute paths
5. No `..` path traversal components
6. No query string or hash fragment
7. Extension must be in `.wav`, `.mp3`, `.m4a`, `.aac`
8. Resolved path must be under `PROJECT_ROOT/outputs/`
9. Must be an existing file (not directory)
10. Raises `ValueError` on any violation → API returns 400

## 5. Backend Flow

```
POST /api/episode/export { audio_url: "/outputs/..." }
  → resolve_safe_audio_url() validates
  → start_episode_export_background(audio_url=...)
    → resolve_safe_audio_url() again (defense in depth)
    → pass safe_audio_path to _run_episode_export_worker()
      → export_video(..., audio_path=str(safe_audio_path))
      → write export_meta.json with has_audio, audio_url, audio_size_bytes
      → write status.json result.has_audio
```

The `export_video()` function already supports `audio_path` and calls ffmpeg to mux audio.

## 6. Metadata Changes

### export_meta.json

```json
{
  "has_audio": true,
  "audio_url": "/outputs/jobs/job_abc/audio/dialogue.wav",
  "audio_size_bytes": 186042,
  "audio_path": "/absolute/local/path.wav"  (internal only, not exposed to frontend)
}
```

### status.json result

```json
{
  "has_audio": true,
  "mp4_url": "...",
  ...
}
```

No absolute local paths are written to `status.json`.

## 7. Frontend Option

In the `episode-export-panel` below the download link:

- Checkbox: `check-episode-export-audio` — "使用当前预览音频一起导出"
- Hint: `episode-export-audio-hint` — "仅当当前作品已有音频时可用"

Logic:
- `getCurrentEpisodeAudioUrlForExport()` reads `preview-audio.src`, strips origin, validates it starts with `/outputs/`
- Default: unchecked (no audio)
- If checked but no valid `/outputs/` audio URL → hint shown, export proceeds without audio
- Status messages include "（含音频）" when audio is included

## 8. Supported Audio Formats

- `.wav` — WAV/PCM
- `.mp3` — MP3
- `.m4a` — AAC in M4A container
- `.aac` — Raw AAC

These are passed directly to ffmpeg's `-i` option.

## 9. Test Result

### Security validation tests (no real export needed)

```python
# All raise ValueError
resolve_safe_audio_url("https://evil.com/audio.wav")
resolve_safe_audio_url("file:///tmp/audio.wav")
resolve_safe_audio_url("C:\\Windows\\audio.wav")
resolve_safe_audio_url("/etc/passwd")
resolve_safe_audio_url("/outputs/../../../secrets.wav")
resolve_safe_audio_url("/outputs/jobs/audio.txt")
resolve_safe_audio_url(None)  # → None (OK, no audio mux)

# Valid
resolve_safe_audio_url("/outputs/jobs/job_abc/audio/dialogue.wav")  # → Path
resolve_safe_audio_url("/outputs/episode_exports/.../audio.mp3")   # → Path
```

### Manual test steps

1. Start server: `python -m src.server`
2. Open `http://127.0.0.1:8777`
3. Add 2-4 hot AI news items → generate with dialogue (mock TTS)
4. Wait for `preview-audio` to load `dialogue.wav`
5. Check "使用当前预览音频一起导出"
6. Click "导出 MP4"
7. Status shows "（含音频）"
8. Completed MP4 has audio track (verify with ffprobe or playback)
9. `export_meta.json` has `has_audio: true`

## 10. What CP40.6 Does Not Do

- No real TTS generation
- No real LLM
- No audio upload
- No arbitrary audio path from frontend
- No external audio URL
- No `/api/jobs` integration
- No Remotion
- No waveform visualization
- No audio-only preview
- No audio format conversion (relies on ffmpeg)

## 11. Known Limitations

- If the checked `/outputs/` audio file is deleted before export completes, ffmpeg will fail and the export will be marked `failed`
- The audio checkbox does not validate that the file actually exists before export starts
- MP4 muxing uses ffmpeg default AAC encoding for MP3/M4A/AAC input — quality is lossy

## 12. Next Checkpoint

CP40.7: Episode export style picker — allow selecting a non-breaking_news_v1 style for episode MP4 export.
