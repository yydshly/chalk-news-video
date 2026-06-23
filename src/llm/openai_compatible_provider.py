"""OpenAI-compatible LLM provider.

POST {base_url}/chat/completions (or {base_url} if it already ends in /chat/completions).

Headers:
  Authorization: Bearer {api_key}
  Content-Type: application/json

Body:
  {
    "model": "...",
    "messages": [{"role": "system", "content": ...}, {"role": "user", "content": ...}],
    "temperature": 0.2,
    "max_tokens": 4000
  }
"""


import os

import requests

from .base import LLMProvider


class OpenAICompatibleProvider(LLMProvider):
    def __init__(self, cfg):
        self.cfg = cfg or {}
        self.timeout = int(cfg.get("timeout_seconds", 60))

        # Resolve base_url from config + env
        base_url, url_src = self._resolve(
            cfg.get("base_url"), cfg.get("base_url_env"), "base_url"
        )
        if not base_url:
            raise RuntimeError(
                f"openai_compatible provider requires 'base_url'. "
                f"Set it in llm.yaml or via env var '{cfg.get('base_url_env')}'."
            )
        self.base_url = base_url.rstrip("/")

        # Append /chat/completions only if not already present
        if self.base_url.endswith("/chat/completions"):
            self.endpoint = self.base_url
        else:
            self.endpoint = self.base_url + "/chat/completions"

        # Resolve model
        model, _ = self._resolve(cfg.get("model"), cfg.get("model_env"), "model")
        if not model:
            raise RuntimeError(
                "openai_compatible provider requires 'model'. "
                f"Set it in llm.yaml or via env var '{cfg.get('model_env')}'."
            )
        self.model = model

        # Resolve API key
        api_key_env = cfg.get("api_key_env")
        if api_key_env:
            self.api_key = (os.environ.get(api_key_env) or "").strip()
        else:
            self.api_key = ""
        if not self.api_key:
            raise RuntimeError(
                f"openai_compatible provider requires API key in env var "
                f"'{api_key_env}'."
            )

        self.temperature = float(cfg.get("temperature", 0.2))
        self.max_tokens = int(cfg.get("max_tokens", 4000))

    @staticmethod
    def _resolve(static_val, env_key, field_name):
        """Prefer static config value; fall back to env var."""
        static = (str(static_val) if static_val is not None else "").strip()
        if static:
            return static, "config"
        if env_key:
            env_val = (os.environ.get(env_key) or "").strip()
            if env_val:
                return env_val, "env"
        return "", None

    def generate_text(self, system_prompt, user_prompt):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "chalk-news-video/0.7",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
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
                f"HTTP request to {self.endpoint} failed: {e}"
            ) from e

        if resp.status_code != 200:
            raise RuntimeError(
                f"openai_compatible provider returned HTTP {resp.status_code}: "
                f"{resp.text[:500]}"
            )

        try:
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError) as e:
            raise RuntimeError(
                f"Failed to parse openai_compatible response: {e}. "
                f"Body[:500]: {resp.text[:500]}"
            ) from e
