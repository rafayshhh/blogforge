"""OpenAI ChatGPT AI Provider implementing official openai SDK."""

import logging
import os
import json
from typing import Optional, Type, Any, ClassVar, List, Tuple, Dict
from pydantic import BaseModel
import openai
from openai import (
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


class OpenAIProvider(AIProvider):
    """Integrates with OpenAI SDK for GPT-4o, o1, o3-mini, and ChatGPT models."""

    DEFAULT_MODEL: ClassVar[str] = "gpt-4o"

    CANDIDATE_MODELS: ClassVar[List[str]] = [
        "gpt-4o",
        "gpt-4o-mini",
        "o1",
        "o3-mini",
        "gpt-4-turbo",
    ]

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.error("OpenAI API key is not configured.")
            raise ProviderAuthenticationError("OpenAI API key is not configured.")

        self.default_model = default_model or os.getenv("OPENAI_MODEL", self.DEFAULT_MODEL)
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")

        client_kwargs: Dict[str, Any] = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url

        try:
            self.client = openai.OpenAI(**client_kwargs)
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise ProviderError(f"Could not initialize OpenAI client: {e}")

    def _prepare_messages(
        self,
        prompt: str,
        system_instructions: Optional[str] = None,
        model: str = ""
    ) -> List[Dict[str, str]]:
        """Constructs chat completion messages, handling reasoning model constraints."""
        messages: List[Dict[str, str]] = []
        is_o_series = model.startswith("o1") or model.startswith("o3")

        if system_instructions:
            # o1 models support developer messages or system instructions in newer API versions
            role = "developer" if is_o_series else "system"
            messages.append({"role": role, "content": system_instructions})

        messages.append({"role": "user", "content": prompt})
        return messages

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
                messages = self._prepare_messages(prompt, system_instructions, target_model)
                kwargs: Dict[str, Any] = {
                    "model": target_model,
                    "messages": messages,
                }
                # o1 and o3 models do not accept custom temperature in standard endpoint
                if temperature is not None and not (target_model.startswith("o1") or target_model.startswith("o3")):
                    kwargs["temperature"] = temperature

                response = self.client.chat.completions.create(**kwargs)

                choice = response.choices[0] if response.choices else None
                text = choice.message.content or "" if choice and choice.message else ""

                usage_obj = response.usage
                input_tokens = getattr(usage_obj, "prompt_tokens", 0) or 0
                output_tokens = getattr(usage_obj, "completion_tokens", 0) or 0
                usage = ProviderUsage(
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=input_tokens + output_tokens,
                )

                return ProviderResponse(
                    text=text,
                    model=target_model,
                    provider="openai",
                    usage=usage,
                )
            except AuthenticationError as e:
                raise ProviderAuthenticationError(f"OpenAI authentication failed: {e}")
            except RateLimitError as e:
                raise ProviderRateLimitError(f"OpenAI rate limit exceeded: {e}")
            except NotFoundError as e:
                raise ProviderError(f"OpenAI model '{target_model}' not found: {e}")
            except APIConnectionError as e:
                raise ProviderTimeoutError(f"OpenAI connection error: {e}")
            except APIError as e:
                raise ProviderError(f"OpenAI API error: {e}")
            except Exception as e:
                raise ProviderError(f"Unexpected error communicating with OpenAI: {e}")

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

        @retry(
            reraise=True,
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type((RateLimitError, APIConnectionError)),
            before_sleep=before_sleep_log(logger, logging.WARNING),
        )
        def _execute_structured():
            try:
                messages = self._prepare_messages(prompt, system_instructions, target_model)

                # Attempt official structured outputs parsing
                try:
                    kwargs: Dict[str, Any] = {
                        "model": target_model,
                        "messages": messages,
                        "response_format": response_model,
                    }
                    if temperature is not None and not (target_model.startswith("o1") or target_model.startswith("o3")):
                        kwargs["temperature"] = temperature

                    completion = self.client.beta.chat.completions.parse(**kwargs)
                    if completion.choices and completion.choices[0].message.parsed:
                        return completion.choices[0].message.parsed
                except Exception as parse_err:
                    logger.debug(f"Direct parse fallback to JSON mode: {parse_err}")

                # Fallback to json_object response format
                schema = response_model.model_json_schema()
                json_prompt = (
                    f"{prompt}\n\nYou MUST respond strictly in valid JSON adhering to this JSON Schema:\n"
                    f"{json.dumps(schema)}"
                )
                fallback_messages = self._prepare_messages(json_prompt, system_instructions, target_model)
                fb_kwargs: Dict[str, Any] = {
                    "model": target_model,
                    "messages": fallback_messages,
                    "response_format": {"type": "json_object"},
                }
                if temperature is not None and not (target_model.startswith("o1") or target_model.startswith("o3")):
                    fb_kwargs["temperature"] = temperature

                raw_resp = self.client.chat.completions.create(**fb_kwargs)
                raw_text = raw_resp.choices[0].message.content or "" if raw_resp.choices else ""
                stripped = raw_text.strip()
                if stripped.startswith("```"):
                    lines = stripped.splitlines()
                    if len(lines) > 2 and lines[0].startswith("```"):
                        stripped = "\n".join(lines[1:-1]).strip()

                if not stripped:
                    raise ProviderResponseError("OpenAI returned an empty response.")

                return response_model.model_validate_json(stripped)

            except AuthenticationError as e:
                raise ProviderAuthenticationError(f"OpenAI authentication failed: {e}")
            except RateLimitError as e:
                raise ProviderRateLimitError(f"OpenAI rate limit exceeded: {e}")
            except APIConnectionError as e:
                raise ProviderTimeoutError(f"OpenAI connection error: {e}")
            except (ProviderResponseError, ProviderAuthenticationError, ProviderRateLimitError):
                raise
            except Exception as e:
                raise ProviderError(f"Failed to produce structured output from OpenAI: {e}")

        return _execute_structured()

    @classmethod
    def list_available_models(
        cls,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs: Any
    ) -> List[str]:
        """Queries OpenAI API or returns candidates."""
        key = api_key if api_key is not None else os.getenv("OPENAI_API_KEY", "")
        key = (key or "").strip()
        if not key:
            return list(cls.CANDIDATE_MODELS)

        try:
            client_kwargs: Dict[str, Any] = {"api_key": key}
            url = base_url or os.getenv("OPENAI_BASE_URL")
            if url:
                client_kwargs["base_url"] = url

            client = openai.OpenAI(**client_kwargs)
            models_list = client.models.list()
            discovered = [m.id for m in models_list.data if any(cand in m.id for cand in ("gpt", "o1", "o3"))]
            if discovered:
                return sorted(discovered)
            return list(cls.CANDIDATE_MODELS)
        except Exception:
            return list(cls.CANDIDATE_MODELS)

    @classmethod
    def diagnose_connection(
        cls,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs: Any
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Tests OpenAI connectivity and authentication."""
        key = api_key if api_key is not None else os.getenv("OPENAI_API_KEY", "")
        key = (key or "").strip()

        target_model = (model or os.getenv("OPENAI_MODEL") or cls.DEFAULT_MODEL).strip()
        if not target_model:
            return (
                False,
                "Configuration error: Model identifier cannot be empty.",
                {"status": "INVALID_MODEL", "code": 400}
            )

        if not key:
            return (
                False,
                "Authentication failed: OpenAI API key is missing or not configured.",
                {"status": "MISSING_KEY", "code": 401}
            )

        try:
            client_kwargs: Dict[str, Any] = {"api_key": key}
            url = base_url or os.getenv("OPENAI_BASE_URL")
            if url:
                client_kwargs["base_url"] = url

            client = openai.OpenAI(**client_kwargs)
            client.chat.completions.create(
                model=target_model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Ping"}]
            )
            return (
                True,
                f"Connected successfully to OpenAI. Model '{target_model}' is active.",
                {"status": "SUCCESS", "code": 200, "model": target_model}
            )
        except AuthenticationError:
            return (
                False,
                "Authentication failed (HTTP 401): Invalid OpenAI API key.",
                {"status": "AUTHENTICATION_FAILED", "code": 401}
            )
        except RateLimitError:
            return (
                False,
                "Rate limit exceeded (HTTP 429): OpenAI account quota or billing limit reached.",
                {"status": "QUOTA_EXHAUSTED", "code": 429}
            )
        except NotFoundError:
            return (
                False,
                f"Model '{target_model}' was not found or is unavailable for this OpenAI account (HTTP 404).",
                {"status": "MODEL_NOT_FOUND", "code": 404}
            )
        except APIConnectionError:
            return (
                False,
                "Network error: Unable to connect to OpenAI API servers.",
                {"status": "NETWORK_ERROR", "code": 503}
            )
        except Exception as e:
            return (
                False,
                f"Connection failed: {str(e)}",
                {"status": "ERROR", "code": 500, "error": str(e)}
            )
