"""TTS (Text-to-Speech) providers and client factory."""

from .base import TTSProvider
from .client import create_tts_client
from .mock_tts_provider import MockTTSProvider
from .minimax_tts_provider import MiniMaxTTSProvider

__all__ = [
    "TTSProvider",
    "MockTTSProvider",
    "MiniMaxTTSProvider",
    "create_tts_client",
]
