"""TTS client factory.

Reads config/tts.yaml, picks a profile, creates the TTS provider.
"""


from pathlib import Path

from ..config_loader import load_yaml, load_env_file
from .base import TTSProvider
from .mock_tts_provider import MockTTSProvider
from .minimax_tts_provider import MiniMaxTTSProvider


def _project_root():
    from pathlib import Path
    return Path(__file__).resolve().parent.parent.parent


DEFAULT_TTS_CONFIG = _project_root() / "config" / "tts.yaml"
DEFAULT_DOTENV = _project_root() / ".env"


def create_tts_client(profile_name=None, config_path=None, env_path=None) -> TTSProvider:
    """Create a TTSProvider for the given profile.

    Args:
        profile_name: which profile to use. Defaults to default_profile in tts.yaml.
        config_path: path to tts.yaml.
        env_path: path to .env file.
    """
    cfg_path = config_path or DEFAULT_TTS_CONFIG
    config = load_yaml(cfg_path)

    # Load env
    effective_env_path = env_path if env_path is not None else DEFAULT_DOTENV
    load_env_file(effective_env_path)

    profiles = config.get("profiles") or {}
    if not profiles:
        raise ValueError("tts.yaml has no 'profiles' section")

    if profile_name is None:
        profile_name = config.get("default_profile")
    if not profile_name:
        raise ValueError("No profile specified and no 'default_profile' in tts.yaml")
    if profile_name not in profiles:
        raise ValueError(
            f"Profile '{profile_name}' not found in tts.yaml. "
            f"Available: {sorted(profiles.keys())}"
        )

    profile = profiles[profile_name]
    provider_type = profile.get("provider")

    if provider_type == "mock":
        return MockTTSProvider(profile)
    elif provider_type == "minimax":
        return MiniMaxTTSProvider(profile)
    else:
        raise ValueError(
            f"Unknown TTS provider type '{provider_type}' for profile '{profile_name}'. "
            f"Supported: mock, minimax."
        )
