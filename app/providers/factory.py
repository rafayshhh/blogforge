"""Factory functions to instantiate configured AI providers (exclusively Google Gemini)."""

import os
from typing import Optional, Any
from app.providers.base import AIProvider
from app.providers.gemini import GeminiProvider
from app.core.exceptions import ConfigurationError


def create_provider(provider_name: str = "gemini", **kwargs: Any) -> AIProvider:
    """Instantiates the Google Gemini AI provider."""
    if not provider_name:
        raise ConfigurationError("AI provider name must be specified.")

    p = provider_name.lower().strip()
    if p in ("gemini", "google"):
        return GeminiProvider(**kwargs)

    raise ConfigurationError(
        f"Unsupported provider: '{provider_name}'. BlogForge only supports Google Gemini."
    )


def resolve_active_provider(
    provider_name: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    **kwargs: Any
) -> AIProvider:
    """Resolves and instantiates the active Google Gemini provider."""
    call_kwargs = dict(kwargs)
    if api_key is not None:
        call_kwargs["api_key"] = api_key
    if model is not None:
        call_kwargs["default_model"] = model

    active_name = (provider_name or os.getenv("AI_PROVIDER") or "gemini").lower().strip()
    return create_provider(active_name, **call_kwargs)
