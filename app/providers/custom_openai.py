"""Custom OpenAI-compatible provider for Cursor, OpenRouter, Ollama, and local proxies."""

import logging
import os
from typing import Optional, ClassVar, List, Tuple, Dict, Any
from app.providers.openai import OpenAIProvider

logger = logging.getLogger(__name__)


class CustomOpenAIProvider(OpenAIProvider):
    """Integrates with Cursor proxies, OpenRouter, Ollama, and custom OpenAI-compatible endpoints."""

    DEFAULT_MODEL: ClassVar[str] = "cursor-small"
    DEFAULT_BASE_URL: ClassVar[str] = "http://localhost:11434/v1"

    CANDIDATE_MODELS: ClassVar[List[str]] = [
        "cursor-small",
        "deepseek-chat",
        "claude-3-5-sonnet",
        "gpt-4o",
        "meta-llama/llama-3.3-70b-instruct",
        "qwen-2.5-coder-32b",
    ]

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        configured_key = api_key or os.getenv("CURSOR_API_KEY") or os.getenv("CUSTOM_OPENAI_API_KEY")
        configured_url = (
            base_url
            or os.getenv("CURSOR_BASE_URL")
            or os.getenv("CUSTOM_OPENAI_BASE_URL")
            or self.DEFAULT_BASE_URL
        )
        configured_model = (
            default_model
            or os.getenv("CURSOR_MODEL")
            or os.getenv("CUSTOM_OPENAI_MODEL")
            or self.DEFAULT_MODEL
        )

        # Local endpoints like Ollama or local proxies might not require a real key
        final_key = configured_key or "sk-local-proxy-key"

        super().__init__(
            api_key=final_key,
            default_model=configured_model,
            base_url=configured_url
        )

    @classmethod
    def list_available_models(
        cls,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs: Any
    ) -> List[str]:
        """Discovers models from custom endpoint, falling back to candidates."""
        url = base_url or os.getenv("CURSOR_BASE_URL") or os.getenv("CUSTOM_OPENAI_BASE_URL") or cls.DEFAULT_BASE_URL
        key = api_key or os.getenv("CURSOR_API_KEY") or os.getenv("CUSTOM_OPENAI_API_KEY") or "sk-local-proxy-key"

        return super().list_available_models(api_key=key, base_url=url, **kwargs)

    @classmethod
    def diagnose_connection(
        cls,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs: Any
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Tests connectivity against custom OpenAI-compatible endpoint."""
        url = base_url or os.getenv("CURSOR_BASE_URL") or os.getenv("CUSTOM_OPENAI_BASE_URL") or cls.DEFAULT_BASE_URL
        key = api_key or os.getenv("CURSOR_API_KEY") or os.getenv("CUSTOM_OPENAI_API_KEY") or "sk-local-proxy-key"
        target_model = model or os.getenv("CURSOR_MODEL") or os.getenv("CUSTOM_OPENAI_MODEL") or cls.DEFAULT_MODEL

        res, msg, data = super().diagnose_connection(api_key=key, model=target_model, base_url=url, **kwargs)
        if res:
            msg = f"Connected successfully to endpoint ({url}). Model '{target_model}' is active."
            data["base_url"] = url
        return res, msg, data
