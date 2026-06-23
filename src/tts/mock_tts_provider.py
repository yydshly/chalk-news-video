"""Mock TTS provider that generates silent/silent-tone WAV files without network.

Uses Python standard library (wave + math) only — no external dependencies.
"""


import math
import struct
import wave
from pathlib import Path

from .base import TTSProvider


# Voice → (frequency_Hz, amplitude) pairs to make different voices distinguishable
_VOICE_PARAMS = {
    "default": (440.0, 16000),   # A4 note, moderate volume
    "host": (440.0, 16000),      # A4 note, same as default
    "expert": (330.0, 14000),    # E4 note, slightly lower volume
}


class MockTTSProvider(TTSProvider):
    def __init__(self, cfg: dict | None = None):
        self.cfg = cfg or {}
        self.sample_rate = int(self.cfg.get("sample_rate", 24000))
        self.format = self.cfg.get("format", "wav")
        self.speed = float(self.cfg.get("speed", 1.0))
        self.voice = self.cfg.get("voice", "default")

    def synthesize(
        self,
        text: str,
        output_path: Path,
        *,
        voice: str | None = None,
        speed: float = 1.0,
        format: str = "wav",
    ) -> dict:
        """Generate a WAV file with a gentle sine wave tone (mock audio)."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Duration: max(1.5, min(8.0, len(text) / 6.0))
        duration = max(1.5, min(8.0, len(text) / 6.0))
        num_samples = int(self.sample_rate * duration)

        # Resolve voice: passed voice > configured voice > "default"
        resolved_voice = voice or self.voice or "default"
        frequency, amplitude = _VOICE_PARAMS.get(resolved_voice, _VOICE_PARAMS["default"])

        # Write WAV file with a gentle sine wave at voice-specific frequency
        with wave.open(str(output_path), "w") as wav_file:
            wav_file.setnchannels(1)  # mono
            wav_file.setsampwidth(2)  # 2 bytes = 16-bit
            wav_file.setframerate(self.sample_rate)

            for i in range(num_samples):
                t = i / self.sample_rate
                # Apply simple fade in/out to avoid clicks
                fade_samples = int(0.05 * self.sample_rate)
                if i < fade_samples:
                    envelope = i / fade_samples
                elif i > num_samples - fade_samples:
                    envelope = (num_samples - i) / fade_samples
                else:
                    envelope = 1.0

                value = int(amplitude * envelope * math.sin(2 * math.pi * frequency * t))
                wav_file.writeframes(struct.pack("<h", value))

        return {
            "text": text,
            "audio_path": str(output_path),
            "duration": duration,
            "sample_rate": self.sample_rate,
            "provider": "mock",
            "voice": resolved_voice,
            "format": format,
        }
