"""Base TTS provider interface."""


from pathlib import Path
from typing import Protocol


class TTSProvider(Protocol):
    """Interface for a TTS (Text-to-Speech) provider."""

    def synthesize(
        self,
        text: str,
        output_path: Path,
        *,
        voice: str | None = None,
        speed: float = 1.0,
        format: str = "wav",
    ) -> dict:
        """Synthesize speech from text.

        Args:
            text: The text to synthesize.
            output_path: Path to write the audio file.
            voice: Optional voice identifier.
            speed: Playback speed multiplier (1.0 = normal).
            format: Audio format (e.g., "wav", "mp3").

        Returns:
            dict with keys: text, audio_path, duration, provider, voice, format
        """
        ...
