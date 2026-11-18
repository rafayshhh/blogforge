"""Factory functions to instantiate configured AI providers."""

import os
from typing import Optional, Any
from app.providers.base import AIProvider
from app.providers.gemini import GeminiProvider
from app.providers.anthropic import AnthropicProvider
from app.providers.openai import OpenAIProvider
from app.providers.custom_openai import CustomOpenAIProvider
from app.core.exceptions import ConfigurationError


def create_provider(provider_name: str, **kwargs: Any) -> AIProvider:
    """Instantiates a provider by name."""
    if not provider_name:
        raise ConfigurationError("AI provider name must be specified.")

    p = provider_name.lower().strip()
    if p in ("gemini", "google"):
        return GeminiProvider(**kwargs)
    elif p in ("anthropic", "claude"):
        return AnthropicProvider(**kwargs)
    elif p in ("openai", "chatgpt"):
        return OpenAIProvider(**kwargs)
    elif p in ("cursor", "custom", "custom_openai", "openrouter"):
        return CustomOpenAIProvider(**kwargs)
    else:
        raise ConfigurationError(f"Unsupported provider: {provider_name}")


def resolve_active_provider(
    provider_name: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    **kwargs: Any
) -> AIProvider:
    """Resolves and instantiates the active AI provider based on environment or explicit parameters."""
    active_name = (provider_name or os.getenv("AI_PROVIDER") or "gemini").lower().strip()

    call_kwargs = dict(kwargs)
    if api_key is not None:
        call_kwargs["api_key"] = api_key
    if model is not None:
        call_kwargs["default_model"] = model

    return create_provider(active_name, **call_kwargs)
