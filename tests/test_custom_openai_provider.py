"""Unit tests for Custom OpenAI / Cursor compatible provider."""

from unittest.mock import MagicMock, patch
from app.providers.custom_openai import CustomOpenAIProvider


def test_custom_openai_defaults(monkeypatch):
    monkeypatch.delenv("CURSOR_API_KEY", raising=False)
    monkeypatch.delenv("CURSOR_BASE_URL", raising=False)
    monkeypatch.delenv("CURSOR_MODEL", raising=False)

    provider = CustomOpenAIProvider()
    assert provider.default_model == CustomOpenAIProvider.DEFAULT_MODEL
    assert provider.base_url == CustomOpenAIProvider.DEFAULT_BASE_URL
    assert provider.client.base_url is not None


def test_custom_openai_configured(monkeypatch):
    monkeypatch.setenv("CURSOR_BASE_URL", "https://api.cursor.sh/v1")
    monkeypatch.setenv("CURSOR_API_KEY", "cursor-test-token")
    monkeypatch.setenv("CURSOR_MODEL", "cursor-small")

    provider = CustomOpenAIProvider()
    assert provider.default_model == "cursor-small"
    assert provider.base_url == "https://api.cursor.sh/v1"


def test_custom_openai_diagnose_connection():
    with patch("openai.OpenAI") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock()

        success, msg, data = CustomOpenAIProvider.diagnose_connection(
            api_key="proxy-key",
            model="deepseek-chat",
            base_url="https://openrouter.ai/api/v1"
        )
        assert success
        assert data["status"] == "SUCCESS"
        assert "Connected successfully to endpoint" in msg
        assert data["base_url"] == "https://openrouter.ai/api/v1"
