"""Anthropic Claude AI Provider implementing anthropic SDK."""

import logging
import os
from typing import Optional, Type, Any, ClassVar, List, Tuple, Dict
from pydantic import BaseModel
import anthropic
from anthropic import (
    APIError,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    APIConnectionError,
)
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from app.providers.base import AIProvider
from app.models.provider import ProviderResponse, ProviderUsage
from app.core.exceptions import (
    ProviderError,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderResponseError,
    ProviderTimeoutError,
)

logger = logging.getLogger(__name__)


class AnthropicProvider(AIProvider):
    """Integrates with Anthropic Claude SDK for Claude 3.5 and 3.7 models."""

    DEFAULT_MODEL: ClassVar[str] = "claude-3-5-sonnet-20241022"

    CANDIDATE_MODELS: ClassVar[List[str]] = [
        "claude-3-7-sonnet-20250219",
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
        "claude-3-opus-20240229",
    ]

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            logger.error("Anthropic API key is not configured.")
            raise ProviderAuthenticationError("Anthropic API key is not configured.")

        self.default_model = default_model or os.getenv("ANTHROPIC_MODEL", self.DEFAULT_MODEL)
        self.base_url = base_url or os.getenv("ANTHROPIC_BASE_URL")

        client_kwargs: Dict[str, Any] = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url

        try:
            self.client = anthropic.Anthropic(**client_kwargs)
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")
            raise ProviderError(f"Could not initialize Anthropic client: {e}")

    def generate(
        self,
        prompt: str,
        system_instructions: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> ProviderResponse:
        """Generates raw text response for the given prompt with exponential backoff."""
        target_model: str = model or self.default_model or self.DEFAULT_MODEL

        @retry(
            reraise=True,
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type((RateLimitError, APIConnectionError)),
            before_sleep=before_sleep_log(logger, logging.WARNING),
        )
        def _execute_generate() -> ProviderResponse:
            try:
                kwargs: Dict[str, Any] = {
                    "model": target_model,
                    "max_tokens": 4096,
                    "messages": [{"role": "user", "content": prompt}],
                }
                if system_instructions:
                    kwargs["system"] = system_instructions
                if temperature is not None:
                    kwargs["temperature"] = temperature

                response = self.client.messages.create(**kwargs)

                text = ""
                for block in response.content:
                    if getattr(block, "type", "") == "text":
                        text += getattr(block, "text", "")

                input_tokens = getattr(response.usage, "input_tokens", 0) or 0
                output_tokens = getattr(response.usage, "output_tokens", 0) or 0
                usage = ProviderUsage(
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=input_tokens + output_tokens,
                )

                return ProviderResponse(
                    text=text,
                    model=target_model,
                    provider="anthropic",
                    usage=usage,
                )
            except AuthenticationError as e:
                raise ProviderAuthenticationError(f"Anthropic authentication failed: {e}")
            except RateLimitError as e:
                raise ProviderRateLimitError(f"Anthropic rate limit exceeded: {e}")
            except NotFoundError as e:
                raise ProviderError(f"Anthropic model '{target_model}' not found: {e}")
            except APIConnectionError as e:
                raise ProviderTimeoutError(f"Anthropic connection error: {e}")
            except APIError as e:
                raise ProviderError(f"Anthropic API error: {e}")
            except Exception as e:
                raise ProviderError(f"Unexpected error communicating with Anthropic: {e}")

        return _execute_generate()

    def generate_structured(
        self,
        prompt: str,
        response_model: Type[BaseModel],
        system_instructions: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> Any:
        """Generates structured output parsed into the specified Pydantic model."""
        target_model: str = model or self.default_model or self.DEFAULT_MODEL
        schema = response_model.model_json_schema()
        tool_name = "record_structured_output"

        tools = [
            {
                "name": tool_name,
                "description": f"Output schema for {response_model.__name__}",
                "input_schema": schema,
            }
        ]

        @retry(
            reraise=True,
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type((RateLimitError, APIConnectionError)),
            before_sleep=before_sleep_log(logger, logging.WARNING),
        )
        def _execute_structured():
            try:
                kwargs: Dict[str, Any] = {
                    "model": target_model,
                    "max_tokens": 4096,
                    "messages": [{"role": "user", "content": prompt}],
                    "tools": tools,
                    "tool_choice": {"type": "tool", "name": tool_name},
                }
                if system_instructions:
                    kwargs["system"] = system_instructions
                if temperature is not None:
                    kwargs["temperature"] = temperature

                response = self.client.messages.create(**kwargs)

                # Extract tool use call
                for block in response.content:
                    if getattr(block, "type", "") == "tool_use" and getattr(block, "name", "") == tool_name:
                        tool_input = getattr(block, "input", None)
                        if isinstance(tool_input, dict):
                            return response_model.model_validate(tool_input)

                # Fallback: inspect raw text blocks for JSON
                raw_text = ""
                for block in response.content:
                    if getattr(block, "type", "") == "text":
                        raw_text += getattr(block, "text", "")

                stripped = raw_text.strip()
                if stripped.startswith("```"):
                    lines = stripped.splitlines()
                    if len(lines) > 2 and lines[0].startswith("```"):
                        stripped = "\n".join(lines[1:-1]).strip()

                if not stripped:
                    raise ProviderResponseError("Anthropic returned an empty response.")

                return response_model.model_validate_json(stripped)

            except AuthenticationError as e:
                raise ProviderAuthenticationError(f"Anthropic authentication failed: {e}")
            except RateLimitError as e:
                raise ProviderRateLimitError(f"Anthropic rate limit exceeded: {e}")
            except APIConnectionError as e:
                raise ProviderTimeoutError(f"Anthropic connection error: {e}")
            except (ProviderResponseError, ProviderAuthenticationError, ProviderRateLimitError):
                raise
            except Exception as e:
                raise ProviderError(f"Failed to produce structured output from Anthropic: {e}")

        return _execute_structured()

    @classmethod
    def list_available_models(
        cls,
        api_key: Optional[str] = None,
        **kwargs: Any
    ) -> List[str]:
        """Returns candidate Claude models supported by BlogForge."""
        return list(cls.CANDIDATE_MODELS)

    @classmethod
    def diagnose_connection(
        cls,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs: Any
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Tests Anthropic Claude connectivity and authentication."""
        key = api_key if api_key is not None else os.getenv("ANTHROPIC_API_KEY", "")
        key = (key or "").strip()

        target_model = (model or os.getenv("ANTHROPIC_MODEL") or cls.DEFAULT_MODEL).strip()
        if not target_model:
            return (
                False,
                "Configuration error: Model identifier cannot be empty.",
                {"status": "INVALID_MODEL", "code": 400}
            )

        if not key:
            return (
                False,
                "Authentication failed: Anthropic API key is missing or not configured.",
                {"status": "MISSING_KEY", "code": 401}
            )

        try:
            client = anthropic.Anthropic(api_key=key)
            client.messages.create(
                model=target_model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Ping"}]
            )
            return (
                True,
                f"Connected successfully to Anthropic. Model '{target_model}' is active.",
                {"status": "SUCCESS", "code": 200, "model": target_model}
            )
        except AuthenticationError:
            return (
                False,
                "Authentication failed (HTTP 401): Invalid Anthropic API key.",
                {"status": "AUTHENTICATION_FAILED", "code": 401}
            )
        except RateLimitError:
            return (
                False,
                "Rate limit exceeded (HTTP 429): Anthropic account quota or burst limit reached.",
                {"status": "QUOTA_EXHAUSTED", "code": 429}
            )
        except NotFoundError:
            return (
                False,
                f"Model '{target_model}' was not found or is unavailable for this Anthropic account (HTTP 404).",
                {"status": "MODEL_NOT_FOUND", "code": 404}
            )
        except APIConnectionError:
            return (
                False,
                "Network error: Unable to connect to Anthropic API servers.",
                {"status": "NETWORK_ERROR", "code": 503}
            )
        except Exception as e:
            return (
                False,
                f"Connection failed: {str(e)}",
                {"status": "ERROR", "code": 500, "error": str(e)}
            )
