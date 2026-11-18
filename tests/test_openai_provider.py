"""Unit tests for OpenAI ChatGPT provider."""

from unittest.mock import MagicMock, patch
import pytest
from pydantic import BaseModel
from openai import AuthenticationError

from app.providers.openai import OpenAIProvider
from app.core.exceptions import (
    ProviderAuthenticationError,
)


class SampleSchema(BaseModel):
    name: str
    word_count: int


def test_openai_missing_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ProviderAuthenticationError):
        OpenAIProvider(api_key=None)


def test_openai_default_configuration():
    provider = OpenAIProvider(api_key="sk-test-key")
    assert provider.default_model == OpenAIProvider.DEFAULT_MODEL
    assert "gpt-4o" in provider.CANDIDATE_MODELS


def test_openai_generate_text_success():
    provider = OpenAIProvider(api_key="sk-test-key")

    mock_choice = MagicMock()
    mock_choice.message.content = "OpenAI response text"

    mock_resp = MagicMock()
    mock_resp.choices = [mock_choice]
    mock_resp.usage = MagicMock(prompt_tokens=20, completion_tokens=10)

    with patch.object(provider.client.chat.completions, "create", return_value=mock_resp) as mock_create:
        res = provider.generate("Prompt here", system_instructions="Act as editor")

        assert res.text == "OpenAI response text"
        assert res.provider == "openai"
        assert res.usage.input_tokens == 20
        assert res.usage.output_tokens == 10
        assert res.usage.total_tokens == 30

        mock_create.assert_called_once()
        kwargs = mock_create.call_args[1]
        assert len(kwargs["messages"]) == 2
        assert kwargs["messages"][0]["role"] == "system"
        assert kwargs["messages"][0]["content"] == "Act as editor"


def test_openai_generate_structured_success():
    provider = OpenAIProvider(api_key="sk-test-key")

    mock_parsed_obj = SampleSchema(name="Article Title", word_count=1200)
    mock_parse_choice = MagicMock()
    mock_parse_choice.message.parsed = mock_parsed_obj

    mock_completion = MagicMock()
    mock_completion.choices = [mock_parse_choice]

    with patch.object(provider.client.beta.chat.completions, "parse", return_value=mock_completion):
        res = provider.generate_structured("Produce schema", SampleSchema)
        assert res.name == "Article Title"
        assert res.word_count == 1200


def test_openai_generate_structured_fallback_json():
    provider = OpenAIProvider(api_key="sk-test-key")

    mock_choice = MagicMock()
    mock_choice.message.content = '{"name": "Fallback Schema", "word_count": 800}'
    mock_resp = MagicMock()
    mock_resp.choices = [mock_choice]

    with patch.object(provider.client.beta.chat.completions, "parse", side_effect=Exception("Beta parse failed")):
        with patch.object(provider.client.chat.completions, "create", return_value=mock_resp):
            res: SampleSchema = provider.generate_structured("Produce schema", SampleSchema)
            assert res.name == "Fallback Schema"
            assert res.word_count == 800


def test_openai_diagnose_connection():
    # 1. Missing key
    success, msg, data = OpenAIProvider.diagnose_connection(api_key="")
    assert not success
    assert data["status"] == "MISSING_KEY"

    # 2. Successful ping
    with patch("openai.OpenAI") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock()

        success, msg, data = OpenAIProvider.diagnose_connection(api_key="sk-valid-key")
        assert success
        assert data["status"] == "SUCCESS"
        assert "Connected successfully to OpenAI" in msg

    # 3. Authentication failure (401)
    with patch("openai.OpenAI") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.chat.completions.create.side_effect = AuthenticationError(
            message="Incorrect API key",
            response=MagicMock(status_code=401),
            body=None
        )

        success, msg, data = OpenAIProvider.diagnose_connection(api_key="sk-bad-key")
        assert not success
        assert data["status"] == "AUTHENTICATION_FAILED"
