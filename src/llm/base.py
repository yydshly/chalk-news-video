"""Base class for LLM providers."""


class LLMProvider:
    """Abstract LLM provider interface.

    Subclasses must implement `generate_text` and may resolve their
    configuration (base_url, api_key, model, etc.) in their constructor.
    """

    def generate_text(self, system_prompt, user_prompt):
        """Generate text from the LLM.

        Args:
            system_prompt: System message content.
            user_prompt: User message content.

        Returns:
            Raw text response from the LLM.

        Raises:
            RuntimeError: on any HTTP, auth, or parse failure.
        """
        raise NotImplementedError
