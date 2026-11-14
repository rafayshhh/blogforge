"""Factory functions to instantiate configured AI providers."""

from app.providers.base import AIProvider
from app.providers.gemini import GeminiProvider
from app.core.exceptions import ConfigurationError


def create_provider(provider_name: str, **kwargs) -> AIProvider:
    if not provider_name:
        raise ConfigurationError("AI provider name must be specified.")
    if provider_name.lower() == 'gemini':
        return GeminiProvider(**kwargs)
    else:
        raise ConfigurationError(f"Unsupported provider: {provider_name}")
