"""Configuration loaders for chalk-news-video.

Reads YAML files from `config/` and a `.env` file (if present).

This module does NOT call any LLM. It only loads structured config.
"""


import os
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_DIR = PROJECT_ROOT / "config"
DEFAULT_DOTENV = PROJECT_ROOT / ".env"


def load_yaml(path):
    """Load a YAML file as a Python object. Raises FileNotFoundError if missing."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config file not found: {p}")
    with open(p, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if data is not None else {}


def load_sources(config_dir=None):
    """Load config/sources.yaml. Returns a dict with a 'sources' list."""
    config_dir = Path(config_dir) if config_dir else DEFAULT_CONFIG_DIR
    return load_yaml(config_dir / "sources.yaml")


def load_llm_config(config_dir=None):
    """Load config/llm.yaml. Returns the full provider dict."""
    config_dir = Path(config_dir) if config_dir else DEFAULT_CONFIG_DIR
    return load_yaml(config_dir / "llm.yaml")


def load_app_config(config_dir=None):
    """Load config/app.yaml. Returns the app config dict."""
    config_dir = Path(config_dir) if config_dir else DEFAULT_CONFIG_DIR
    return load_yaml(config_dir / "app.yaml")


def load_env_file(env_path=None, override=False):
    """Tiny .env loader.

    Lines: KEY=value, blank lines ignored, lines starting with '#' ignored.
    Surrounding quotes on the value are stripped.

    Side effect: also populates `os.environ` so downstream code that reads
    `os.environ.get(...)` sees the values.

    Priority:
        - System environment wins by default (`override=False`, uses setdefault).
        - Pass `override=True` to let .env values overwrite system env.

    Missing file is not an error: returns {} and leaves os.environ untouched.

    Args:
        env_path: path to .env file. Defaults to PROJECT_ROOT/.env.
        override: if True, overwrite existing os.environ values with .env values.

    Returns:
        dict of {key: value} parsed from the file.
    """
    p = Path(env_path) if env_path else DEFAULT_DOTENV
    if not p.exists():
        return {}
    out = {}
    with open(p, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            out[k] = v
            if override:
                os.environ[k] = v
            else:
                # System env wins; .env only fills gaps.
                os.environ.setdefault(k, v)
    return out


def get_api_key(provider_cfg, env_path=None):
    """Resolve an API key from the environment, optionally loading .env first."""
    env_key = provider_cfg.get("api_key_env") if provider_cfg else None
    if not env_key:
        return None
    # Try system env first.
    val = os.environ.get(env_key)
    if val:
        return val
    # Fall back to .env file (does not override os.environ unless override=True).
    env = load_env_file(env_path)
    return env.get(env_key)
