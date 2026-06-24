"""MiniMax TTS provider.

Endpoint and credentials are configured via config/tts.yaml or environment variables.
Do NOT hardcode any MiniMax TTS endpoint here.
"""


import os
from pathlib import Path

import requests

from .base import TTSProvider


class MiniMaxTTSProvider(TTSProvider):
    def __init__(self, cfg: dict | None = None):
        self.cfg = cfg or {}
        self.timeout = int(self.cfg.get("timeout_seconds", 60))
        self.format = self.cfg.get("format", "wav")
        self.sample_rate = int(self.cfg.get("sample_rate", 24000))
        self.voice_id = self.cfg.get("voice_id", "") or ""
        self.voice_id_env = self.cfg.get("voice_id_env", "")
        self.speed = float(self.cfg.get("speed", 1.0))

        # Resolve base_url
        self.base_url = self._resolve(
            self.cfg.get("base_url"), self.cfg.get("base_url_env"), "base_url"
        )
        # Resolve endpoint_path
        self.endpoint_path = self._resolve(
            self.cfg.get("endpoint_path"), self.cfg.get("endpoint_path_env"), "endpoint_path"
        )
        # Resolve model
        self.model = self._resolve(
            self.cfg.get("model"), self.cfg.get("model_env"), "model"
        )
        # Resolve API key
        api_key_env = self.cfg.get("api_key_env", "MINIMAX_API_KEY")
        self.api_key = (os.environ.get(api_key_env) or "").strip()

        if not self.base_url:
            raise RuntimeError(
                f"MiniMax TTS requires 'base_url'. "
                f"Set it in config/tts.yaml or via env var '{self.cfg.get('base_url_env')}'."
            )
        if not self.endpoint_path:
            raise RuntimeError(
                f"MiniMax TTS requires 'endpoint_path'. "
                f"Set it in config/tts.yaml or via env var '{self.cfg.get('endpoint_path_env')}'."
            )
        if not self.api_key:
            raise RuntimeError(
                f"MiniMax TTS requires API key in env var '{api_key_env}'."
            )
        if not self.voice_id:
            voice = self._resolve("", self.voice_id_env, "voice_id")
            self.voice_id = voice

        self.endpoint = self.base_url.rstrip("/") + "/" + self.endpoint_path.lstrip("/")

    @staticmethod
    def _resolve(static_val, env_key, field_name):
        if env_key:
            env_val = (os.environ.get(env_key) or "").strip()
            if env_val:
                return env_val
        return (str(static_val) if static_val is not None else "").strip()

    def synthesize(
        self,
        text: str,
        output_path: Path,
        *,
        voice: str | None = None,
        speed: float = 1.0,
        format: str = "wav",
    ) -> dict:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        effective_voice = voice or self.voice_id
        if not effective_voice:
            raise RuntimeError(
                "MiniMax TTS requires a voice_id. "
                "Set voice_id in config/tts.yaml or via MINIMAX_TTS_VOICE_ID env var."
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "text": text,
            "voice_setting": {
                "voice_id": effective_voice,
            },
            "audio_setting": {
                "sample_rate": self.sample_rate,
                "format": "wav",
            },
            "speed": speed,
        }

        try:
            resp = requests.post(
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
        except requests.exceptions.RequestException as e:
            raise RuntimeError(
                f"[minimax_tts] HTTP request failed: {e}"
            ) from e

        if resp.status_code != 200:
            # Don't include response body in error - could contain sensitive info
            raise RuntimeError(
                f"[minimax_tts] HTTP {resp.status_code} from {self.endpoint}"
            )

        # Parse JSON response - MiniMax returns hex-encoded audio in data.audio
        try:
            data = resp.json()
        except Exception as e:
            raise RuntimeError(
                f"[minimax_tts] failed to parse JSON response: {e}"
            ) from e

        # Check API-level error via base_resp.status_code
        base_resp = data.get("base_resp", {})
        status_code = base_resp.get("status_code")
        if status_code != 0:
            status_msg = base_resp.get("status_msg", "unknown error")
            raise RuntimeError(
                f"[minimax_tts] API error {status_code}: {status_msg}"
            )

        # Extract hex-encoded audio
        audio_hex = data.get("data", {}).get("audio")
        if not audio_hex:
            raise RuntimeError("[minimax_tts] response missing data.audio")

        try:
            audio_bytes = bytes.fromhex(audio_hex)
        except Exception as e:
            raise RuntimeError(f"[minimax_tts] failed to decode audio hex: {e}") from e

        output_path.write_bytes(audio_bytes)

        # Get duration from extra_info.audio_length (milliseconds) if available
        extra = data.get("extra_info", {})
        audio_length_ms = extra.get("audio_length")
        if audio_length_ms is not None:
            duration = audio_length_ms / 1000.0
        else:
            # Fallback: estimate from file size
            duration = max(1.0, len(audio_bytes) / (self.sample_rate * 2))

        # Get sample rate from response if available
        audio_sample_rate = extra.get("audio_sample_rate", self.sample_rate)

        return {
            "text": text,
            "audio_path": str(output_path),
            "duration": duration,
            "provider": "minimax",
            "voice": effective_voice,
            "format": format,
            "sample_rate": audio_sample_rate,
        }
