"""LLM Provider Layer for chalk-news-video.

Public surface:
- src.llm.client.create_llm_client(profile_name=None, config_path=None, env_path=None)
- src.llm.json_utils.extract_json_object(text)

Provider protocols supported (config-driven):
- openai_compatible : OpenAI /chat/completions style
- anthropic_messages : Anthropic /messages style (also used by some MiniMax deployments)
- mock : local deterministic generator for offline testing
"""
