# CP8 Real Dialogue LLM Validation

## Test Date
[To be filled: YYYY-MM-DD]

## Test Environment

- OS: Windows 11 / macOS / Linux
- Python: 3.10+
- Node.js: [version if applicable]
- FFmpeg: [version]

## LLM Configuration

```bash
# .env configuration used
MINIMAX_API_KEY=<key present: YES/NO>
MINIMAX_BASE_URL=https://api.minimaxi.com/v1
MINIMAX_MODEL=MiniMax-M3
```

## Test 1: Real LLM Dialogue Generation

### Command
```bash
python -m src.generate_dialogue \
    --semantic-ir outputs/latest/semantic_ir.json \
    --profile minimax_m3_openai \
    --validate --repair
```

### Expected Behavior

1. **Success path**: dialogue_script.json valid → proceed to TTS
2. **Failure path**:
   - HTTP 401/403 → authentication error
   - Rate limit → 429 Too Many Requests
   - Model unavailable → 400 Bad Request
   - Invalid JSON from LLM → JSON parse error
   - Validation failed after repair → exit 5

### Actual Result

| Field | Value |
|-------|-------|
| Exit code | [TBD] |
| HTTP status | [TBD] |
| LLM call made | YES/NO/ERROR |
| Repair triggered | YES/NO |
| dialogue_script.json valid | YES/NO |
| Validation issues (if any) | [TBD] |

### Notes
[To be filled after test run]

---

## Test 2: Real LLM Dialogue via Pipeline

### Command
```bash
python -m src.pipeline \
    --auto \
    --news outputs/latest/latest_news.json \
    --profile minimax_m3_openai \
    --tts --dialogue \
    --dialogue-profile mock_dialogue
```

### Expected Behavior

1. generate_ir → validate_ir
2. generate_dialogue (real LLM + repair)
3. dialogue_manifest generation
4. apply_narration_timing
5. render_html → export_video

### Actual Result

| Field | Value |
|-------|-------|
| Exit code | [TBD] |
| dialogue_script.json valid | YES/NO |
| dialogue_manifest.json generated | YES/NO |
| render_ir.json generated | YES/NO |
| output.mp4 generated | YES/NO |
| total_duration | [TBD]s |

### Notes
[To be filled after test run]

---

## Test 3: Dialogue Profile Mapping (mock_dialogue)

### Command
```bash
python -m src.narration \
    --dialogue-script outputs/latest/dialogue_script.json \
    --dialogue \
    --dialogue-profile mock_dialogue
```

### Expected Manifest Structure (CP8)
```json
{
  "schema_version": "0.1",
  "provider": "mock_host+mock_expert",
  "dialogue_profile": "mock_dialogue",
  "speaker_profiles": {
    "host": {
      "profile": "mock_host",
      "voice": "host"
    },
    "expert": {
      "profile": "mock_expert",
      "voice": "expert"
    }
  },
  "source_dialogue_script": {...},
  "total_duration": 31.167,
  "turns": [...]
}
```

### Actual Result

| Field | Value |
|-------|-------|
| dialogue_profile in manifest | YES/NO |
| speaker_profiles in manifest | YES/NO |
| host profile correct | YES/NO |
| expert profile correct | YES/NO |

### Notes
[To be filled after test run]

---

## Summary

**Status**: PENDING (awaiting real API key test)

- [ ] Real LLM dialogue generation works
- [ ] Repair flow functions correctly
- [ ] dialogue_profile mapping works in manifest
- [ ] Full pipeline end-to-end passes

**Next Steps**:
1. Obtain valid MiniMax API key
2. Run tests above and record results
3. If MiniMax TTS available, test minimax_dialogue profile
