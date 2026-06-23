"""LLM client factory.

Reads config/llm.yaml, picks a profile (default or --profile), creates the
provider (openai_compatible | anthropic_messages | mock), and exposes a thin
LLMClient wrapper with a single generate_text(system, user) -> str method.

This module does NOT compose business prompts — that's the caller's job
(e.g. src.generate_ir).
"""


from ..config_loader import load_env_file, load_yaml
from .anthropic_messages_provider import AnthropicMessagesProvider
from .base import LLMProvider
from .openai_compatible_provider import OpenAICompatibleProvider


# Path to the bundled config; resolve relative to project root.
def _project_root():
    from pathlib import Path
    return Path(__file__).resolve().parent.parent.parent


DEFAULT_LLM_CONFIG = _project_root() / "config" / "llm.yaml"


class LLMClient:
    """Thin wrapper over an LLMProvider."""

    def __init__(self, provider):
        if not isinstance(provider, LLMProvider):
            raise TypeError(f"provider must be an LLMProvider, got {type(provider).__name__}")
        self.provider = provider

    def generate_text(self, system_prompt, user_prompt):
        return self.provider.generate_text(system_prompt, user_prompt)


class MockProvider(LLMProvider):
    """Deterministic offline provider. Used for tests and CI without keys.

    Reads a `payload` field from the profile (a JSON string), and returns it
    verbatim as the assistant message. If no payload is set, returns an empty
    string.
    """

    def __init__(self, cfg):
        self.cfg = cfg or {}
        self.timeout = int(cfg.get("timeout_seconds", 1))

    def generate_text(self, system_prompt, user_prompt):
        return self.cfg.get("payload", "")


def _resolve_profile(config, profile_name=None):
    """Pick a profile dict from llm.yaml.

    Falls back to config['default_profile'] when profile_name is None.
    Raises ValueError on missing / unknown profile.
    """
    if not isinstance(config, dict):
        raise ValueError("llm.yaml is empty or not a mapping")
    profiles = config.get("profiles") or {}
    if not profiles:
        raise ValueError("llm.yaml has no 'profiles' section")

    if profile_name is None:
        profile_name = config.get("default_profile")
    if not profile_name:
        raise ValueError(
            "No profile specified and no 'default_profile' in llm.yaml."
        )
    if profile_name not in profiles:
        raise ValueError(
            f"Profile '{profile_name}' not found in llm.yaml. "
            f"Available: {sorted(profiles.keys())}"
        )
    return profiles[profile_name]


def create_llm_client(profile_name=None, config_path=None, env_path=None):
    """Create an LLMClient for the given profile.

    Args:
        profile_name: which profile to use. Defaults to llm.yaml default_profile.
        config_path: path to llm.yaml. Defaults to config/llm.yaml.
        env_path: optional .env file to load BEFORE constructing the provider
                  (so api_key_env / base_url_env / model_env resolve correctly).

    Returns:
        LLMClient
    """
    cfg_path = config_path or DEFAULT_LLM_CONFIG
    config = load_yaml(cfg_path)

    # Load .env first so env-var resolution in providers sees the values.
    if env_path is not None:
        load_env_file(env_path)

    profile = _resolve_profile(config, profile_name)

    protocol = profile.get("protocol")
    if protocol == "openai_compatible":
        provider = OpenAICompatibleProvider(profile)
    elif protocol == "anthropic_messages":
        provider = AnthropicMessagesProvider(profile)
    elif protocol == "mock":
        provider = MockProvider(profile)
    else:
        raise ValueError(
            f"Unknown protocol '{protocol}' for profile "
            f"'{profile_name}'. Supported: openai_compatible, anthropic_messages, mock."
        )

    return LLMClient(provider)
