"""Unit tests for Anthropic Claude provider."""

from unittest.mock import MagicMock, patch
import pytest
from pydantic import BaseModel
from anthropic import AuthenticationError, RateLimitError

from app.providers.anthropic import AnthropicProvider
from app.core.exceptions import (
    ProviderAuthenticationError,
    ProviderRateLimitError,
)


class SampleSchema(BaseModel):
    title: str
    score: int


def test_anthropic_missing_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ProviderAuthenticationError):
        AnthropicProvider(api_key=None)


def test_anthropic_default_configuration():
    provider = AnthropicProvider(api_key="sk-ant-test-key")
    assert provider.default_model == AnthropicProvider.DEFAULT_MODEL
    assert len(provider.CANDIDATE_MODELS) >= 3


def test_anthropic_generate_text_success():
    provider = AnthropicProvider(api_key="sk-ant-test-key")

    mock_block = MagicMock()
    mock_block.type = "text"
    mock_block.text = "Hello from Claude!"

    mock_resp = MagicMock()
    mock_resp.content = [mock_block]
    mock_resp.usage = MagicMock(input_tokens=15, output_tokens=8)

    with patch.object(provider.client.messages, "create", return_value=mock_resp) as mock_create:
        res = provider.generate("Hi Claude", system_instructions="Be concise")

        assert res.text == "Hello from Claude!"
        assert res.provider == "anthropic"
        assert res.usage.input_tokens == 15
        assert res.usage.output_tokens == 8
        assert res.usage.total_tokens == 23

        mock_create.assert_called_once()
        kwargs = mock_create.call_args[1]
        assert kwargs["system"] == "Be concise"
        assert kwargs["model"] == provider.default_model


def test_anthropic_generate_structured_via_tool_call():
    provider = AnthropicProvider(api_key="sk-ant-test-key")

    mock_tool_block = MagicMock()
    mock_tool_block.type = "tool_use"
    mock_tool_block.name = "record_structured_output"
    mock_tool_block.input = {"title": "Architecture Guide", "score": 95}

    mock_resp = MagicMock()
    mock_resp.content = [mock_tool_block]

    with patch.object(provider.client.messages, "create", return_value=mock_resp):
        res: SampleSchema = provider.generate_structured("Generate data", SampleSchema)
        assert res.title == "Architecture Guide"
        assert res.score == 95


def test_anthropic_generate_structured_fallback_json():
    provider = AnthropicProvider(api_key="sk-ant-test-key")

    mock_text_block = MagicMock()
    mock_text_block.type = "text"
    mock_text_block.text = '```json\n{"title": "Fallback Guide", "score": 88}\n```'

    mock_resp = MagicMock()
    mock_resp.content = [mock_text_block]

    with patch.object(provider.client.messages, "create", return_value=mock_resp):
        res: SampleSchema = provider.generate_structured("Generate data", SampleSchema)
        assert res.title == "Fallback Guide"
        assert res.score == 88


def test_anthropic_generate_rate_limit_retry_exhaustion():
    provider = AnthropicProvider(api_key="sk-ant-test-key")

    with patch.object(provider.client.messages, "create") as mock_create:
        mock_create.side_effect = RateLimitError(
            message="Rate limit exceeded",
            response=MagicMock(status_code=429),
            body=None
        )
        with pytest.raises(ProviderRateLimitError):
            provider.generate("Test prompt")


def test_anthropic_diagnose_connection():
    # 1. Missing key
    success, msg, data = AnthropicProvider.diagnose_connection(api_key="")
    assert not success
    assert data["status"] == "MISSING_KEY"

    # 2. Empty model
    success, msg, data = AnthropicProvider.diagnose_connection(api_key="sk-ant-key", model="   ")
    assert not success
    assert data["status"] == "INVALID_MODEL"

    # 3. Successful ping
    with patch("anthropic.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock()

        success, msg, data = AnthropicProvider.diagnose_connection(api_key="sk-ant-valid-key")
        assert success
        assert data["status"] == "SUCCESS"
        assert "Connected successfully" in msg

    # 4. Authentication failure (401)
    with patch("anthropic.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.messages.create.side_effect = AuthenticationError(
            message="Invalid key",
            response=MagicMock(status_code=401),
            body=None
        )

        success, msg, data = AnthropicProvider.diagnose_connection(api_key="sk-ant-bad-key")
        assert not success
        assert data["status"] == "AUTHENTICATION_FAILED"
