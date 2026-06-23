"""Anthropic Messages-style provider.

Used for MiniMax (and any provider exposing an Anthropic-compatible /messages
endpoint). The actual base_url is read from config / env — never hardcoded.

Headers:
  x-api-key: {api_key}
  anthropic-version: 2023-06-01
  Content-Type: application/json

Body:
  {
    "model": "...",
    "max_tokens": 4000,
    "temperature": 0.2,
    "system": "...",
    "messages": [{"role": "user", "content": "..."}]
  }
"""


import os

import requests

from .base import LLMProvider


class AnthropicMessagesProvider(LLMProvider):
    def __init__(self, cfg):
        self.cfg = cfg or {}
        self.timeout = int(cfg.get("timeout_seconds", 60))

        base_url, _ = self._resolve(cfg.get("base_url"), cfg.get("base_url_env"))
        if not base_url:
            raise RuntimeError(
                f"anthropic_messages provider requires 'base_url'. "
                f"Set it in llm.yaml or via env var '{cfg.get('base_url_env')}'."
            )
        self.base_url = base_url.rstrip("/")

        if self.base_url.endswith("/messages"):
            self.endpoint = self.base_url
        else:
            self.endpoint = self.base_url + "/messages"

        model, _ = self._resolve(cfg.get("model"), cfg.get("model_env"))
        if not model:
            raise RuntimeError(
                f"anthropic_messages provider requires 'model'. "
                f"Set it in llm.yaml or via env var '{cfg.get('model_env')}'."
            )
        self.model = model

        api_key_env = cfg.get("api_key_env")
        if api_key_env:
            self.api_key = (os.environ.get(api_key_env) or "").strip()
        else:
            self.api_key = ""
        if not self.api_key:
            raise RuntimeError(
                f"anthropic_messages provider requires API key in env var "
                f"'{api_key_env}'."
            )

        self.anthropic_version = cfg.get("anthropic_version", "2023-06-01")
        self.temperature = float(cfg.get("temperature", 0.2))
        self.max_tokens = int(cfg.get("max_tokens", 4000))

    @staticmethod
    def _resolve(static_val, env_key):
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
            "x-api-key": self.api_key,
            "anthropic-version": self.anthropic_version,
            "Content-Type": "application/json",
            "User-Agent": "chalk-news-video/0.7",
        }
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt},
            ],
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
                f"anthropic_messages provider returned HTTP {resp.status_code}: "
                f"{resp.text[:500]}"
            )

        try:
            data = resp.json()
            # Anthropic-style: content is a list of blocks; we want the first text block.
            for block in data.get("content", []) or []:
                if isinstance(block, dict) and block.get("type") == "text":
                    return block.get("text", "")
            # Fallback: some MiniMax deployments may use a simpler shape
            if "text" in data:
                return data["text"]
            raise KeyError("no text block in response.content")
        except (KeyError, IndexError, ValueError) as e:
            raise RuntimeError(
                f"Failed to parse anthropic_messages response: {e}. "
                f"Body[:500]: {resp.text[:500]}"
            ) from e
