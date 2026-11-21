"""Unit tests for AI provider factory and active provider resolution (Google Gemini)."""

import pytest
from app.providers.factory import create_provider, resolve_active_provider
from app.providers.gemini import GeminiProvider
from app.core.exceptions import ConfigurationError


def test_create_provider_gemini():
    p = create_provider("gemini", api_key="AIzaSyDummyKey")
    assert isinstance(p, GeminiProvider)

    p_google = create_provider("google", api_key="AIzaSyDummyKey")
    assert isinstance(p_google, GeminiProvider)


def test_create_provider_unsupported_providers():
    """Verify non-Google providers are cleanly rejected with ConfigurationError."""
    unsupported = ["anthropic", "claude", "openai", "chatgpt", "cursor", "custom", "openrouter"]
    for prov in unsupported:
        with pytest.raises(ConfigurationError, match="BlogForge only supports Google Gemini"):
            create_provider(prov, api_key="dummy-key")


def test_create_provider_errors():
    with pytest.raises(ConfigurationError, match="AI provider name must be specified"):
        create_provider("")

    with pytest.raises(ConfigurationError, match="BlogForge only supports Google Gemini"):
        create_provider("unsupported_provider_xyz")


def test_resolve_active_provider(monkeypatch):
    """Verify resolve_active_provider creates GeminiProvider."""
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSyTestKey")
    p = resolve_active_provider()
    assert isinstance(p, GeminiProvider)
    assert p.api_key == "AIzaSyTestKey"
