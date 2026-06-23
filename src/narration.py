"""Generate narration audio from semantic_ir beats.

Checkpoint 6 (V0.10): Single-voice TTS narration generation.

Usage:
    python -m src.narration --semantic-ir outputs/latest/semantic_ir.json --profile mock
    python -m src.narration --semantic-ir outputs/latest/semantic_ir.json --profile minimax_speech
"""


import argparse
import sys
import wave
import struct
from datetime import datetime, timezone
from pathlib import Path

from .tts import create_tts_client
from .utils import PROJECT_ROOT, load_json, save_json


OUTPUT_DIR = PROJECT_ROOT / "outputs" / "latest"
AUDIO_DIR = OUTPUT_DIR / "audio"
DEFAULT_NARRATION_MANIFEST_PATH = OUTPUT_DIR / "narration_manifest.json"


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


def generate_narration(semantic_ir_path: str | Path, profile: str = "mock") -> dict:
    """Generate narration audio for each beat and produce a manifest.

    Args:
        semantic_ir_path: Path to semantic_ir.json
        profile: TTS profile name (from config/tts.yaml)

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

    # Concatenate all beat audio files
    combined_audio_path = audio_dir / "narration.wav"
    if beat_audio_paths:
        _concat_wavs(beat_audio_paths, combined_audio_path)
        total_duration = _get_wav_duration(combined_audio_path)
    else:
        combined_audio_path = None
        total_duration = 0.0

    manifest = {
        "schema_version": "0.1",
        "provider": profile,
        "audio_format": "wav",
        "sample_rate": 24000,
        "total_duration": round(total_duration, 3),
        "beats": manifest_beats,
        "combined_audio_path": str(combined_audio_path) if combined_audio_path else None,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    manifest_path = DEFAULT_NARRATION_MANIFEST_PATH
    save_json(manifest, manifest_path)
    print(f"[narration] wrote {manifest_path}")

    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate narration audio from semantic_ir beats.",
    )
    parser.add_argument(
        "--semantic-ir",
        type=str,
        default=str(OUTPUT_DIR / "semantic_ir.json"),
        help="Path to semantic_ir.json",
    )
    parser.add_argument(
        "--profile",
        type=str,
        default="mock",
        help="TTS profile name (from config/tts.yaml)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_NARRATION_MANIFEST_PATH),
        help="Output path for narration_manifest.json",
    )
    args = parser.parse_args(argv)

    try:
        manifest = generate_narration(args.semantic_ir, profile=args.profile)
        print(f"[narration] generated {len(manifest['beats'])} beat audio(s)")
        print(f"[narration] combined audio: {manifest['combined_audio_path']}")
        print(f"[narration] total_duration: {manifest['total_duration']}s")
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
