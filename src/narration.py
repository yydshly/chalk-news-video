"""Generate narration audio from semantic_ir beats.

Checkpoint 6 (V0.10): Single-voice TTS narration generation.
CP6.1: Audio timing is source of truth for render_ir.timeline.
CP7: Dual-host dialogue with host/expert voices.
CP8: Add dialogue_profile mapping and speaker_profiles in manifest.

Usage:
    python -m src.narration --semantic-ir outputs/latest/semantic_ir.json --profile mock
    python -m src.narration --semantic-ir outputs/latest/semantic_ir.json --profile minimax_speech
    python -m src.narration --semantic-ir outputs/latest/semantic_ir.json --dialogue --host-profile mock_host --expert-profile mock_expert
    python -m src.narration --dialogue-script outputs/latest/dialogue_script.json --dialogue --dialogue-profile mock_dialogue
"""


import argparse
import sys
import wave
import struct
from datetime import datetime, timezone
from pathlib import Path

from .tts import create_tts_client
from .config_loader import load_yaml
from .utils import PROJECT_ROOT, load_json, save_json


OUTPUT_DIR = PROJECT_ROOT / "outputs" / "latest"
AUDIO_DIR = OUTPUT_DIR / "audio"
DEFAULT_NARRATION_MANIFEST_PATH = OUTPUT_DIR / "narration_manifest.json"
DEFAULT_DIALOGUE_MANIFEST_PATH = OUTPUT_DIR / "dialogue_manifest.json"

# Default tail silence appended after the last beat
DEFAULT_TAIL_SILENCE_SEC = 0.5

# Speaker → TTS profile mapping for dialogue mode (legacy, used when no dialogue_profile)
SPEAKER_PROFILE_MAP = {
    "host": "mock_host",
    "expert": "mock_expert",
}

# Default dialogue profile when --dialogue-profile not specified
DEFAULT_DIALOGUE_PROFILE = "mock_dialogue"


def _get_dialogue_profile_mapping(dialogue_profile_name: str) -> dict:
    """Load dialogue_profile mapping from config/tts.yaml."""
    from pathlib import Path as P
    config_path = P(__file__).resolve().parent.parent / "config" / "tts.yaml"
    config = load_yaml(config_path)
    dialogue_profiles = config.get("dialogue_profiles", {})
    if dialogue_profile_name not in dialogue_profiles:
        raise ValueError(
            f"Dialogue profile '{dialogue_profile_name}' not found in config/tts.yaml. "
            f"Available: {sorted(dialogue_profiles.keys())}"
        )
    return dialogue_profiles[dialogue_profile_name]


def _resolve_speaker_voice(speaker: str, speaker_profiles: dict | None) -> str | None:
    """Resolve the voice for a speaker from the dialogue_profile speaker_profiles mapping.

    Rules:
    1. If speaker_profiles is None/empty, return None.
    2. If speaker_profiles[speaker] has 'voice', return it.
    3. If speaker_profiles[speaker] has 'voice_id', return it.
    4. If speaker_profiles[speaker] has 'voice_env':
       - Read from os.environ[voice_env]
       - If exists and non-empty, return the env value
       - If not set, raise RuntimeError with env var name (masked value)
    6. Return None if nothing found.

    Sensitive voice values from env are NOT returned; only env var name is used
    in error messages. The actual resolved value is returned only if non-sensitive.
    """
    import os

    if not speaker_profiles:
        return None

    sp = speaker_profiles.get(speaker, {})
    if not sp:
        return None

    # Direct voice value (e.g., "host", "expert" for mock)
    if "voice" in sp:
        return sp["voice"]

    # Direct voice_id (e.g., from config)
    if "voice_id" in sp:
        return sp["voice_id"]

    # Env-based voice_id (e.g., MINIMAX_TTS_HOST_VOICE_ID)
    if "voice_env" in sp:
        env_key = sp["voice_env"]
        env_val = (os.environ.get(env_key) or "").strip()
        if not env_val:
            raise RuntimeError(
                f"TTS voice requires env var '{env_key}' to be set for speaker '{speaker}', "
                f"but it is not set or empty. Please configure it in your .env file."
            )
        return env_val

    return None


def _get_wav_duration(path: Path) -> float:
    """Get duration of a WAV file in seconds."""
    with wave.open(str(path), "r") as w:
        frames = w.getnframes()
        rate = w.getframerate()
        return frames / float(rate)


def _concat_wavs(wav_paths: list[Path], output_path: Path):
    """Concatenate multiple WAV files into one."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Determine params from first file
    with wave.open(str(wav_paths[0]), "r") as first:
        nchannels = first.getnchannels()
        sampwidth = first.getsampwidth()
        framerate = first.getframerate()

    with wave.open(str(output_path), "wb") as out:
        out.setnchannels(nchannels)
        out.setsampwidth(sampwidth)
        out.setframerate(framerate)
        for wav_path in wav_paths:
            with wave.open(str(wav_path), "r") as w:
                out.writeframes(w.readframes(w.getnframes()))


def _write_silence_wav(output_path: Path, duration_sec: float, sample_rate: int = 24000):
    """Write a silent WAV file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    num_samples = int(sample_rate * duration_sec)
    with wave.open(str(output_path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        # Write silence (zeros)
        wav_file.writeframes(b"\x00\x00" * num_samples)


def generate_narration(
    semantic_ir_path: str | Path,
    profile: str = "mock",
    output_path: Path | str | None = None,
    tail_silence_sec: float = DEFAULT_TAIL_SILENCE_SEC,
) -> dict:
    """Generate narration audio for each beat and produce a manifest.

    Args:
        semantic_ir_path: Path to semantic_ir.json
        profile: TTS profile name (from config/tts.yaml)
        output_path: Optional override for narration_manifest.json output path
        tail_silence_sec: Silence duration appended after the last beat (default 0.5s)

    Returns:
        narration_manifest dict
    """
    semantic_ir_path = Path(semantic_ir_path)
    sem = load_json(semantic_ir_path)

    beats = sem.get("beats", [])
    if not beats:
        raise ValueError("semantic_ir has no beats")

    provider = create_tts_client(profile_name=profile)

    audio_dir = AUDIO_DIR
    audio_dir.mkdir(parents=True, exist_ok=True)

    beat_audio_paths = []
    manifest_beats = []
    current_time = 0.0
    sample_rate = 24000  # will be updated from first provider result

    for i, beat in enumerate(beats):
        beat_id = beat.get("id", f"b{i+1}")
        reveal = beat.get("reveal", "")
        narration = beat.get("narration", "").strip()

        if not narration:
            continue  # skip empty narrations

        audio_filename = f"beat_{beat_id}.wav"
        audio_path = audio_dir / audio_filename

        result = provider.synthesize(
            text=narration,
            output_path=audio_path,
            voice=None,
            speed=1.0,
            format="wav",
        )

        # Use sample_rate from provider result
        sample_rate = int(result.get("sample_rate", sample_rate))
        duration = _get_wav_duration(audio_path)

        manifest_beats.append({
            "beat_id": beat_id,
            "reveal": reveal,
            "text": narration,
            "audio_path": str(audio_path),
            "start": round(current_time, 3),
            "duration": round(duration, 3),
            "end": round(current_time + duration, 3),
        })

        beat_audio_paths.append(audio_path)
        current_time += duration

    # speech_duration = end of last beat
    speech_duration = round(current_time, 3)

    # Concatenate all beat audio files
    combined_audio_path = audio_dir / "narration.wav"
    if beat_audio_paths:
        # First concat beat WAVs to a temp file
        temp_combined = audio_dir / "narration_beats.wav"
        _concat_wavs(beat_audio_paths, temp_combined)
        if tail_silence_sec > 0:
            # Append tail silence: concat beats + silence into final path
            silence_path = audio_dir / "tail_silence.wav"
            _write_silence_wav(silence_path, tail_silence_sec, sample_rate)
            _concat_wavs([temp_combined, silence_path], combined_audio_path)
            silence_path.unlink(missing_ok=True)
        else:
            temp_combined.rename(combined_audio_path)
        temp_combined.unlink(missing_ok=True)
        total_duration = _get_wav_duration(combined_audio_path)
    else:
        combined_audio_path = None
        total_duration = 0.0

    manifest = {
        "schema_version": "0.1",
        "provider": profile,
        "audio_format": "wav",
        "sample_rate": sample_rate,
        "tail_silence": tail_silence_sec,
        "speech_duration": speech_duration,
        "total_duration": round(total_duration, 3),
        "beats": manifest_beats,
        "combined_audio_path": str(combined_audio_path) if combined_audio_path else None,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    manifest_path = Path(output_path) if output_path else DEFAULT_NARRATION_MANIFEST_PATH
    save_json(manifest, manifest_path)
    print(f"[narration] wrote {manifest_path}")

    return manifest


def generate_dialogue(
    semantic_ir_path: str | Path,
    host_profile: str = "mock_host",
    expert_profile: str = "mock_expert",
    output_path: Path | str | None = None,
    tail_silence_sec: float = DEFAULT_TAIL_SILENCE_SEC,
) -> dict:
    """Generate dual-host dialogue audio and produce a dialogue_manifest.

    Args:
        semantic_ir_path: Path to semantic_ir.json
        host_profile: TTS profile for "host" speaker
        expert_profile: TTS profile for "expert" speaker
        output_path: Optional override for dialogue_manifest.json output path
        tail_silence_sec: Silence duration appended after the last beat (default 0.5s)

    Returns:
        dialogue_manifest dict
    """
    semantic_ir_path = Path(semantic_ir_path)
    sem = load_json(semantic_ir_path)

    beats = sem.get("beats", [])
    if not beats:
        raise ValueError("semantic_ir has no beats")

    audio_dir = AUDIO_DIR
    audio_dir.mkdir(parents=True, exist_ok=True)

    # Create providers for each speaker
    host_provider = create_tts_client(profile_name=host_profile)
    expert_provider = create_tts_client(profile_name=expert_profile)

    beat_audio_paths = []
    manifest_beats = []
    current_time = 0.0
    sample_rate = 24000  # will be updated from first provider result
    speakers_used = set()

    for i, beat in enumerate(beats):
        beat_id = beat.get("id", f"b{i+1}")
        reveal = beat.get("reveal", "")
        narration = beat.get("narration", "").strip()
        speaker = beat.get("speaker", "host")  # default to host if not specified
        speakers_used.add(speaker)

        if not narration:
            continue  # skip empty narrations

        # Select provider based on speaker
        if speaker == "expert":
            provider = expert_provider
        else:
            provider = host_provider

        audio_filename = f"beat_{beat_id}.wav"
        audio_path = audio_dir / audio_filename

        result = provider.synthesize(
            text=narration,
            output_path=audio_path,
            voice=None,
            speed=1.0,
            format="wav",
        )

        # Use sample_rate from provider result
        sample_rate = int(result.get("sample_rate", sample_rate))
        duration = _get_wav_duration(audio_path)

        manifest_beats.append({
            "beat_id": beat_id,
            "reveal": reveal,
            "speaker": speaker,
            "text": narration,
            "audio_path": str(audio_path),
            "start": round(current_time, 3),
            "duration": round(duration, 3),
            "end": round(current_time + duration, 3),
        })

        beat_audio_paths.append(audio_path)
        current_time += duration

    # speech_duration = end of last beat
    speech_duration = round(current_time, 3)

    # Concatenate all beat audio files (interleaved by speaker)
    combined_audio_path = audio_dir / "dialogue.wav"
    if beat_audio_paths:
        temp_combined = audio_dir / "dialogue_beats.wav"
        _concat_wavs(beat_audio_paths, temp_combined)
        if tail_silence_sec > 0:
            silence_path = audio_dir / "tail_silence.wav"
            _write_silence_wav(silence_path, tail_silence_sec, sample_rate)
            _concat_wavs([temp_combined, silence_path], combined_audio_path)
            silence_path.unlink(missing_ok=True)
        else:
            temp_combined.rename(combined_audio_path)
        temp_combined.unlink(missing_ok=True)
        total_duration = _get_wav_duration(combined_audio_path)
    else:
        combined_audio_path = None
        total_duration = 0.0

    manifest = {
        "schema_version": "0.1",
        "provider": f"{host_profile}+{expert_profile}",
        "audio_format": "wav",
        "sample_rate": sample_rate,
        "tail_silence": tail_silence_sec,
        "speech_duration": speech_duration,
        "total_duration": round(total_duration, 3),
        "host_profile": host_profile,
        "expert_profile": expert_profile,
        "speakers": sorted(speakers_used),
        "beats": manifest_beats,
        "combined_audio_path": str(combined_audio_path) if combined_audio_path else None,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    manifest_path = Path(output_path) if output_path else DEFAULT_DIALOGUE_MANIFEST_PATH
    save_json(manifest, manifest_path)
    print(f"[dialogue] wrote {manifest_path}")

    return manifest


def generate_dialogue_audio(
    dialogue_script_path: str | Path,
    host_profile: str = "mock_host",
    expert_profile: str = "mock_expert",
    output_path: Path | str | None = None,
    tail_silence_sec: float = DEFAULT_TAIL_SILENCE_SEC,
    dialogue_profile: str | None = None,
    speaker_profiles: dict | None = None,
) -> dict:
    """Generate dual-host dialogue audio from dialogue_script.json and produce a dialogue_manifest.

    This is the CP7.1 main path: dialogue_script.turns → audio → dialogue_manifest.

    Args:
        dialogue_script_path: Path to dialogue_script.json
        host_profile: TTS profile for "host" speaker (used if dialogue_profile not set)
        expert_profile: TTS profile for "expert" speaker (used if dialogue_profile not set)
        output_path: Optional override for dialogue_manifest.json output path
        tail_silence_sec: Silence duration appended after the last turn (default 0.5s)
        dialogue_profile: Name of dialogue profile from config/tts.yaml (CP8)
        speaker_profiles: Dict mapping speaker to {profile, voice/voice_env} (CP8)

    Returns:
        dialogue_manifest dict
    """
    dialogue_script_path = Path(dialogue_script_path)
    dialogue_script = load_json(dialogue_script_path)

    turns = dialogue_script.get("turns", [])
    if not turns:
        raise ValueError("dialogue_script has no turns")

    audio_dir = AUDIO_DIR
    audio_dir.mkdir(parents=True, exist_ok=True)

    # Resolve speaker to profile mapping (CP8 dialogue_profile takes priority)
    if dialogue_profile and speaker_profiles:
        host_profile = speaker_profiles.get("host", {}).get("profile", host_profile)
        expert_profile = speaker_profiles.get("expert", {}).get("profile", expert_profile)

    # Create providers for each speaker
    host_provider = create_tts_client(profile_name=host_profile)
    expert_provider = create_tts_client(profile_name=expert_profile)

    turn_audio_paths = []
    manifest_turns = []
    current_time = 0.0
    sample_rate = 24000  # will be updated from first provider result
    speakers_used = set()

    for turn in turns:
        turn_id = turn.get("id", "")
        speaker = turn.get("speaker", "host")
        text = turn.get("text", "").strip()
        beat_id = turn.get("beat_id", "")
        reveal = turn.get("reveal", "")
        speakers_used.add(speaker)

        if not text:
            continue  # skip empty turns

        # Select provider based on speaker
        provider = expert_provider if speaker == "expert" else host_provider

        # Resolve voice for this speaker from dialogue_profile mapping (CP8.1)
        resolved_voice = _resolve_speaker_voice(speaker, speaker_profiles)

        audio_filename = f"turn_{turn_id}.wav"
        audio_path = audio_dir / audio_filename

        result = provider.synthesize(
            text=text,
            output_path=audio_path,
            voice=resolved_voice,
            speed=1.0,
            format="wav",
        )

        sample_rate = int(result.get("sample_rate", sample_rate))
        duration = _get_wav_duration(audio_path)

        # Build turn manifest entry with voice info (CP8.1)
        # For sensitive voices (from env), record voice_env not the actual value
        sp_entry = (speaker_profiles or {}).get(speaker, {})
        turn_entry = {
            "turn_id": turn_id,
            "speaker": speaker,
            "beat_id": beat_id,
            "reveal": reveal,
            "text": text,
            "audio_path": str(audio_path),
            "start": round(current_time, 3),
            "duration": round(duration, 3),
            "end": round(current_time + duration, 3),
        }
        if "voice_env" in sp_entry:
            turn_entry["voice_env"] = sp_entry["voice_env"]
        elif resolved_voice:
            turn_entry["voice"] = resolved_voice
        manifest_turns.append(turn_entry)

        turn_audio_paths.append(audio_path)
        current_time += duration

    speech_duration = round(current_time, 3)

    # Concatenate all turn audio files
    combined_audio_path = audio_dir / "dialogue.wav"
    if turn_audio_paths:
        temp_combined = audio_dir / "dialogue_turns.wav"
        _concat_wavs(turn_audio_paths, temp_combined)
        if tail_silence_sec > 0:
            silence_path = audio_dir / "tail_silence.wav"
            _write_silence_wav(silence_path, tail_silence_sec, sample_rate)
            _concat_wavs([temp_combined, silence_path], combined_audio_path)
            silence_path.unlink(missing_ok=True)
        else:
            temp_combined.rename(combined_audio_path)
        temp_combined.unlink(missing_ok=True)
        total_duration = _get_wav_duration(combined_audio_path)
    else:
        combined_audio_path = None
        total_duration = 0.0

    # Build manifest (CP8: add dialogue_profile and speaker_profiles)
    manifest = {
        "schema_version": "0.1",
        "provider": f"{host_profile}+{expert_profile}",
        "source_dialogue_script": {
            "schema_version": dialogue_script.get("schema_version", "0.1"),
        },
        "total_duration": round(total_duration, 3),
        "turns": manifest_turns,
        "combined_audio_path": str(combined_audio_path) if combined_audio_path else None,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    # CP8: record dialogue_profile and speaker_profiles (mask sensitive voice values)
    if dialogue_profile:
        manifest["dialogue_profile"] = dialogue_profile
    if speaker_profiles:
        # Build safe speaker_profiles for manifest: mask real voice_id values
        safe_speaker_profiles = {}
        for sp_key, sp_val in speaker_profiles.items():
            if not isinstance(sp_val, dict):
                safe_speaker_profiles[sp_key] = sp_val
                continue
            safe_entry = dict(sp_val)
            # If voice_env is set, the resolved voice is sensitive - remove real voice value
            if "voice_env" in safe_entry:
                # voice_env is safe (just an env var name), but resolved voice is sensitive
                safe_entry.pop("voice_id", None)  # remove if present
                # don't add voice field for env-based voices
            # For non-env voices (mock), voice value is safe to record
            safe_speaker_profiles[sp_key] = safe_entry
        manifest["speaker_profiles"] = safe_speaker_profiles

    manifest_path = Path(output_path) if output_path else DEFAULT_DIALOGUE_MANIFEST_PATH
    save_json(manifest, manifest_path)
    print(f"[dialogue_audio] wrote {manifest_path}")

    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate narration audio from semantic_ir or dialogue_script.",
    )
    parser.add_argument(
        "--semantic-ir",
        type=str,
        default=str(OUTPUT_DIR / "semantic_ir.json"),
        help="Path to semantic_ir.json",
    )
    parser.add_argument(
        "--dialogue-script",
        type=str,
        default=str(OUTPUT_DIR / "dialogue_script.json"),
        help="Path to dialogue_script.json (CP7.1 main path)",
    )
    parser.add_argument(
        "--profile",
        type=str,
        default="mock",
        help="TTS profile name (from config/tts.yaml) for single-voice mode",
    )
    parser.add_argument(
        "--dialogue",
        action="store_true",
        help="Enable dual-host dialogue mode using dialogue_script (CP7.1).",
    )
    parser.add_argument(
        "--dialogue-legacy",
        action="store_true",
        help="Enable dual-host dialogue using semantic_ir.beats[].speaker (CP7 compatibility).",
    )
    parser.add_argument(
        "--dialogue-profile",
        type=str,
        default=None,
        help="Dialogue profile name from config/tts.yaml (e.g. mock_dialogue, minimax_dialogue). "
             "Takes priority over --host-profile/--expert-profile when set.",
    )
    parser.add_argument(
        "--host-profile",
        type=str,
        default="mock_host",
        help="TTS profile for host speaker (used when --dialogue-profile not set)",
    )
    parser.add_argument(
        "--expert-profile",
        type=str,
        default="mock_expert",
        help="TTS profile for expert speaker (used when --dialogue-profile not set)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output path for manifest.json",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for audio and manifest (default: outputs/latest). (CP14)",
    )
    args = parser.parse_args(argv)

    # Apply output-dir override
    if getattr(args, "output_dir", None):
        output_dir = Path(args.output_dir).resolve()
        # Override module-level OUTPUT_DIR and AUDIO_DIR for this invocation
        import sys
        this_module = sys.modules[__name__]
        setattr(this_module, "OUTPUT_DIR", output_dir)
        setattr(this_module, "AUDIO_DIR", output_dir / "audio")
        # Set default --output if not explicitly provided
        if args.output is None:
            if getattr(args, "dialogue", False) or getattr(args, "dialogue_legacy", False):
                args.output = str(output_dir / "dialogue_manifest.json")
            else:
                args.output = str(output_dir / "narration_manifest.json")

    try:
        if args.dialogue:
            # Resolve dialogue_profile speaker mapping (CP8)
            dialogue_profile = args.dialogue_profile
            speaker_profiles = None
            if dialogue_profile:
                mapping = _get_dialogue_profile_mapping(dialogue_profile)
                speaker_profiles = mapping
                print(f"[dialogue_audio] using dialogue_profile={dialogue_profile}")
                print(f"[dialogue_audio] host -> {mapping.get('host', {}).get('profile')}")
                print(f"[dialogue_audio] expert -> {mapping.get('expert', {}).get('profile')}")

            # CP7.1 main path: dialogue_script.turns → dialogue_manifest
            manifest = generate_dialogue_audio(
                args.dialogue_script,
                host_profile=args.host_profile,
                expert_profile=args.expert_profile,
                output_path=args.output,
                dialogue_profile=dialogue_profile,
                speaker_profiles=speaker_profiles,
            )
            print(f"[dialogue_audio] generated {len(manifest['turns'])} turn audio(s)")
            print(f"[dialogue_audio] combined audio: {manifest['combined_audio_path']}")
            print(f"[dialogue_audio] total_duration: {manifest['total_duration']}s")
        elif args.dialogue_legacy:
            # CP7 compatibility path: semantic_ir.beats[].speaker → dialogue_manifest
            manifest = generate_dialogue(
                args.semantic_ir,
                host_profile=args.host_profile,
                expert_profile=args.expert_profile,
                output_path=args.output,
            )
            print(f"[dialogue_legacy] generated {len(manifest['beats'])} beat audio(s)")
            print(f"[dialogue_legacy] speakers: {manifest['speakers']}")
            print(f"[dialogue_legacy] combined audio: {manifest['combined_audio_path']}")
            print(f"[dialogue_legacy] total_duration: {manifest['total_duration']}s")
        else:
            manifest = generate_narration(
                args.semantic_ir,
                profile=args.profile,
                output_path=args.output,
            )
            print(f"[narration] generated {len(manifest['beats'])} beat audio(s)")
            print(f"[narration] combined audio: {manifest['combined_audio_path']}")
            print(f"[narration] total_duration: {manifest['total_duration']}s")
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
