"""Comprehensive unit and error-handling tests for GeminiProvider with mocked Google GenAI client."""

from unittest.mock import MagicMock, patch
import pytest
from pydantic import BaseModel
from google.genai.errors import APIError

from app.providers.gemini import GeminiProvider
from app.core.exceptions import (
    ProviderError,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderResponseError,
    ProviderServiceUnavailableError,
    ProviderTimeoutError,
)


class DummyModel(BaseModel):
    name: str
    score: int


def test_gemini_provider_missing_key(monkeypatch):
    """Verify GeminiProvider raises ProviderAuthenticationError if API key is absent."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ProviderAuthenticationError, match="Gemini API key is not configured"):
        GeminiProvider(api_key=None)


def test_gemini_provider_init_client_failure():
    """Verify GeminiProvider wraps underlying client init errors in ProviderError."""
    with patch("google.genai.Client", side_effect=RuntimeError("SDK Init Failed")):
        with pytest.raises(ProviderError, match="Failed to initialize Gemini client"):
            GeminiProvider(api_key="TEST_KEY")


def test_exception_mapping():
    """Verify _map_exception correctly maps HTTP status codes and timeout strings."""
    provider = GeminiProvider(api_key="TEST_KEY")

    # APIError with HTTP 401 / 403
    err_401 = APIError(401, {"message": "Unauthorized"})
    assert isinstance(provider._map_exception(err_401), ProviderAuthenticationError)

    err_403 = APIError(403, {"message": "Forbidden"})
    assert isinstance(provider._map_exception(err_403), ProviderAuthenticationError)

    # APIError with HTTP 429
    err_429 = APIError(429, {"message": "Rate Limit"})
    assert isinstance(provider._map_exception(err_429), ProviderRateLimitError)

    # APIError with HTTP 500, 503
    err_500 = APIError(500, {"message": "Internal"})
    assert isinstance(provider._map_exception(err_500), ProviderServiceUnavailableError)

    err_503 = APIError(503, {"message": "Unavailable"})
    assert isinstance(provider._map_exception(err_503), ProviderServiceUnavailableError)

    # APIError with HTTP 400
    err_400 = APIError(400, {"message": "Bad Request"})
    assert isinstance(provider._map_exception(err_400), ProviderResponseError)

    # Timeout string in Exception
    timeout_err = RuntimeError("Connection timeout exceeded")
    assert isinstance(provider._map_exception(timeout_err), ProviderTimeoutError)

    # Generic unmapped exception
    generic_err = ValueError("Something strange")
    assert isinstance(provider._map_exception(generic_err), ProviderError)


def test_default_configuration(monkeypatch):
    """Verify GeminiProvider defaults to gemini-3.8-flash and medium thinking level."""
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.delenv("GEMINI_THINKING_LEVEL", raising=False)

    provider = GeminiProvider(api_key="TEST_KEY")
    assert provider.default_model == "gemini-3.8-flash"
    assert provider.thinking_level == "medium"


def test_thinking_level_validation():
    """Verify thinking level validation accepts low/medium/high, falls back for minimal/invalid."""
    # Valid levels
    for lvl in ["low", "medium", "high"]:
        p = GeminiProvider(api_key="TEST_KEY", thinking_level=lvl)
        assert p.thinking_level == lvl

    # Minimal is rejected/avoided on Gemini 3.8 Flash, falls back to medium
    p_min = GeminiProvider(api_key="TEST_KEY", thinking_level="minimal")
    assert p_min.thinking_level == "medium"

    # Arbitrary invalid level falls back to medium
    p_inv = GeminiProvider(api_key="TEST_KEY", thinking_level="invalid_level")
    assert p_inv.thinking_level == "medium"


def test_prepare_config():
    """Verify _prepare_config sets thinking config, schemas, automatic function calling, and instructions."""
    provider = GeminiProvider(api_key="TEST_KEY", default_model="gemini-3.8-flash", thinking_level="high")

    # With gemini-3.8-flash model
    cfg_3 = provider._prepare_config(
        system_instructions="Act as Architect",
        model="gemini-3.8-flash",
        temperature=0.7,
        response_model=DummyModel
    )
    assert cfg_3.system_instruction == "Act as Architect"
    assert cfg_3.temperature == 0.7
    assert cfg_3.response_mime_type == "application/json"
    assert cfg_3.response_schema == DummyModel
    assert cfg_3.thinking_config is not None
    assert cfg_3.thinking_config.thinking_level.name == "HIGH"
    assert cfg_3.automatic_function_calling.disable is True

    # With Gemini 4 model
    cfg_4 = provider._prepare_config(
        model="gemini-4-carbon"
    )
    assert cfg_4.thinking_config is not None

    # With legacy gemini-2 model (no thinking config)
    cfg_2 = provider._prepare_config(
        model="gemini-2.5-flash"
    )
    assert cfg_2.thinking_config is None


def test_extract_response_text_with_thought_tokens():
    """Verify _extract_response_text skips internal thought segments."""
    provider = GeminiProvider(api_key="TEST_KEY")

    # Direct text property present
    mock_resp_simple = MagicMock()
    mock_resp_simple.text = "Direct output"
    assert provider._extract_response_text(mock_resp_simple) == "Direct output"

    # Direct text is None, parts contain thoughts and actual text
    mock_part_thought = MagicMock()
    mock_part_thought.thought = True
    mock_part_thought.text = "Internal thought reasoning process"

    mock_part_text = MagicMock()
    mock_part_text.thought = False
    mock_part_text.text = "Final published response"

    mock_candidate = MagicMock()
    mock_candidate.content.parts = [mock_part_thought, mock_part_text]

    mock_resp_parts = MagicMock()
    mock_resp_parts.text = None
    mock_resp_parts.candidates = [mock_candidate]

    extracted = provider._extract_response_text(mock_resp_parts)
    assert extracted == "Final published response"


def test_list_available_models_success():
    """Verify list_available_models filters for generateContent and strips models/ prefix."""
    m1 = MagicMock()
    m1.name = "models/gemini-3.8-flash"
    m1.supported_actions = ["generateContent"]

    m2 = MagicMock()
    m2.name = "models/gemini-4-hydrogen"
    m2.supported_actions = ["generateContent", "countTokens"]

    m3 = MagicMock()
    m3.name = "models/text-embedding-004"
    m3.supported_actions = ["embedContent"]

    with patch("google.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.models.list.return_value = [m1, m2, m3]
        mock_client_cls.return_value = mock_client

        models = GeminiProvider.list_available_models(api_key="TEST_KEY")
        assert models == ["gemini-3.8-flash", "gemini-4-hydrogen"]


def test_list_available_models_missing_key(monkeypatch):
    """Verify list_available_models raises ProviderAuthenticationError if key missing."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ProviderAuthenticationError):
        GeminiProvider.list_available_models(api_key=None)


def test_get_accessible_candidate_models():
    """Verify get_accessible_candidate_models returns candidate models intersecting available list."""
    with patch.object(
        GeminiProvider,
        "list_available_models",
        return_value=["gemini-3.8-flash", "gemini-4-argon", "custom-experimental-model"]
    ):
        candidates = GeminiProvider.get_accessible_candidate_models(api_key="TEST_KEY")
        assert "gemini-3.8-flash" in candidates
        assert "gemini-4-argon" in candidates
        assert "gemini-3.5-flash-lite" not in candidates

    # If list_available_models raises error, fallback safely to default
    with patch.object(GeminiProvider, "list_available_models", side_effect=RuntimeError("API failure")):
        fallback = GeminiProvider.get_accessible_candidate_models(api_key="TEST_KEY")
        assert fallback == ["gemini-3.8-flash"]


def test_generate_text_success():
    """Verify successful text generation and token usage extraction."""
    provider = GeminiProvider(api_key="TEST_KEY")

    mock_resp = MagicMock()
    mock_resp.text = "Generated blog content body."
    mock_meta = MagicMock()
    mock_meta.prompt_token_count = 120
    mock_meta.candidates_token_count = 350
    mock_meta.total_token_count = 470
    mock_resp.usage_metadata = mock_meta

    provider.client.models.generate_content = MagicMock(return_value=mock_resp)

    resp = provider.generate("Write an article on Python.")
    assert resp.text == "Generated blog content body."
    assert resp.provider == "gemini"
    assert resp.usage is not None
    assert resp.usage.input_tokens == 120
    assert resp.usage.output_tokens == 350
    assert resp.usage.total_tokens == 470


@patch("time.sleep", return_value=None)
def test_generate_transient_retry_and_recovery(mock_sleep):
    """Verify generate retries on transient errors and recovers if subsequent attempt succeeds."""
    provider = GeminiProvider(api_key="TEST_KEY")

    transient_err = APIError(429, {"message": "Rate Limit"})

    mock_success = MagicMock()
    mock_success.text = "Success on attempt 2"
    mock_success.usage_metadata = None

    provider.client.models.generate_content = MagicMock(
        side_effect=[transient_err, mock_success]
    )

    resp = provider.generate("Test prompt")
    assert resp.text == "Success on attempt 2"
    assert provider.client.models.generate_content.call_count == 2
    assert mock_sleep.called


@patch("time.sleep", return_value=None)
def test_generate_fatal_error_no_retry(mock_sleep):
    """Verify fatal authentication errors halt immediately without retrying."""
    provider = GeminiProvider(api_key="TEST_KEY")

    auth_err = APIError(401, {"message": "Invalid API key"})

    provider.client.models.generate_content = MagicMock(side_effect=auth_err)

    with pytest.raises(ProviderAuthenticationError):
        provider.generate("Test prompt")

    # Call count should be exactly 1, no retries
    assert provider.client.models.generate_content.call_count == 1
    assert not mock_sleep.called


def test_generate_structured_with_parsed():
    """Verify generate_structured returns client parsed object if present."""
    provider = GeminiProvider(api_key="TEST_KEY")

    mock_resp = MagicMock()
    mock_resp.parsed = DummyModel(name="Architecture", score=100)
    provider.client.models.generate_content = MagicMock(return_value=mock_resp)

    result = provider.generate_structured("Prompt", DummyModel)
    assert isinstance(result, DummyModel)
    assert result.name == "Architecture"
    assert result.score == 100


def test_generate_structured_fallback_json_parsing():
    """Verify generate_structured parses raw JSON with markdown backtick stripping."""
    provider = GeminiProvider(api_key="TEST_KEY")

    # Markdown formatted JSON
    mock_resp = MagicMock()
    mock_resp.parsed = None
    mock_resp.text = '```json\n{"name": "Clean Code", "score": 95}\n```'
    provider.client.models.generate_content = MagicMock(return_value=mock_resp)

    result = provider.generate_structured("Prompt", DummyModel)
    assert isinstance(result, DummyModel)
    assert result.name == "Clean Code"
    assert result.score == 95


def test_generate_structured_empty_response():
    """Verify generate_structured raises ProviderResponseError when response is blank."""
    provider = GeminiProvider(api_key="TEST_KEY")

    mock_resp = MagicMock()
    mock_resp.parsed = None
    mock_resp.text = "   "
    provider.client.models.generate_content = MagicMock(return_value=mock_resp)

    with pytest.raises(ProviderResponseError, match="Gemini returned an empty response"):
        provider.generate_structured("Prompt", DummyModel)


@patch("time.sleep", return_value=None)
def test_generate_structured_transient_exhaustion(mock_sleep):
    """Verify generate_structured raises mapped error after exhausting max attempts."""
    provider = GeminiProvider(api_key="TEST_KEY")

    server_err = APIError(503, {"message": "Service Unavailable"})

    provider.client.models.generate_content = MagicMock(side_effect=server_err)

    with pytest.raises(ProviderServiceUnavailableError):
        provider.generate_structured("Prompt", DummyModel)

    assert provider.client.models.generate_content.call_count == 3
    assert mock_sleep.call_count == 2
