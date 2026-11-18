"""Unit tests for AI provider factory and active provider resolution."""

import pytest
from app.providers.factory import create_provider, resolve_active_provider
from app.providers.gemini import GeminiProvider
from app.providers.anthropic import AnthropicProvider
from app.providers.openai import OpenAIProvider
from app.providers.custom_openai import CustomOpenAIProvider
from app.core.exceptions import ConfigurationError


def test_create_provider_gemini():
    p = create_provider("gemini", api_key="AIzaSyDummyKey")
    assert isinstance(p, GeminiProvider)


def test_create_provider_anthropic():
    p = create_provider("anthropic", api_key="sk-ant-dummy")
    assert isinstance(p, AnthropicProvider)

    p_claude = create_provider("claude", api_key="sk-ant-dummy")
    assert isinstance(p_claude, AnthropicProvider)


def test_create_provider_openai():
    p = create_provider("openai", api_key="sk-dummy")
    assert isinstance(p, OpenAIProvider)

    p_chatgpt = create_provider("chatgpt", api_key="sk-dummy")
    assert isinstance(p_chatgpt, OpenAIProvider)


def test_create_provider_cursor():
    p = create_provider("cursor")
    assert isinstance(p, CustomOpenAIProvider)

    p_custom = create_provider("custom")
    assert isinstance(p_custom, CustomOpenAIProvider)


def test_create_provider_errors():
    with pytest.raises(ConfigurationError):
        create_provider("")

    with pytest.raises(ConfigurationError):
        create_provider("unsupported_provider_xyz")


def test_resolve_active_provider(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "anthropic")
    p = resolve_active_provider(api_key="sk-ant-test")
    assert isinstance(p, AnthropicProvider)

    monkeypatch.setenv("AI_PROVIDER", "openai")
    p = resolve_active_provider(api_key="sk-test")
    assert isinstance(p, OpenAIProvider)

    monkeypatch.setenv("AI_PROVIDER", "cursor")
    p = resolve_active_provider()
    assert isinstance(p, CustomOpenAIProvider)
