"""Google Gemini AI Provider implementing google-genai SDK."""

import logging
import os
import time
from typing import Optional, Type, Any, ClassVar
from pydantic import BaseModel
from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.providers.base import AIProvider
from app.models.provider import ProviderResponse, ProviderUsage
from app.core.exceptions import (
    ProviderError,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderResponseError,
    ProviderServiceUnavailableError,
    ProviderTimeoutError,
)

logger = logging.getLogger(__name__)


class GeminiProvider(AIProvider):
    """Integrates with Google GenAI SDK for Gemini 3.x and Gemini 4 models."""

    DEFAULT_MODEL: ClassVar[str] = "gemini-3.8-flash"
    DEFAULT_THINKING_LEVEL: ClassVar[str] = "medium"

    # Supported thinking levels for Gemini 3.8 Flash and modern reasoning models
    SUPPORTED_THINKING_LEVELS: ClassVar[dict[str, types.ThinkingLevel]] = {
        "low": types.ThinkingLevel.LOW,
        "medium": types.ThinkingLevel.MEDIUM,
        "high": types.ThinkingLevel.HIGH,
    }

    # Verified candidate models
    CANDIDATE_MODELS: ClassVar[list[str]] = [
        "gemini-3.8-flash",
        "gemini-3.5-flash-lite",
        "gemini-4-hydrogen",
        "gemini-4-argon",
        "gemini-4-carbon",
    ]

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: Optional[str] = None,
        thinking_level: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.error("Gemini API key is not configured.")
            raise ProviderAuthenticationError("Gemini API key is not configured.")

        self.default_model = default_model or os.getenv("GEMINI_MODEL", self.DEFAULT_MODEL)

        # Validate thinking level (minimal is NOT supported by Gemini 3.8 Flash)
        configured_level = thinking_level or os.getenv("GEMINI_THINKING_LEVEL") or self.DEFAULT_THINKING_LEVEL
        raw_level = configured_level.lower().strip()

        if raw_level in self.SUPPORTED_THINKING_LEVELS:
            self.thinking_level = raw_level
        else:
            if raw_level == "minimal":
                logger.warning(
                    "Thinking level 'minimal' is unsupported by Gemini 3.8 Flash. Falling back to 'medium'."
                )
            else:
                logger.warning(
                    f"Invalid thinking level '{raw_level}'. Falling back to default '{self.DEFAULT_THINKING_LEVEL}'."
                )
            self.thinking_level = self.DEFAULT_THINKING_LEVEL

        try:
            self.client = genai.Client(api_key=self.api_key)
            logger.info(
                f"Gemini provider initialized (model: {self.default_model}, thinking_level: {self.thinking_level})"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise ProviderError(f"Failed to initialize Gemini client: {e}")

    @classmethod
    def list_available_models(cls, api_key: Optional[str] = None, **kwargs: Any) -> list[str]:
        """Queries Google's official Gemini API to retrieve models available to the account.

        Filters models that support content generation ('generateContent' action).
        """
        key = api_key or os.getenv("GEMINI_API_KEY")
        if not key:
            raise ProviderAuthenticationError("Gemini API key is required to list available models.")

        try:
            client = genai.Client(api_key=key)
            models_pager = client.models.list()
            available: list[str] = []
            for m in models_pager:
                raw_name = getattr(m, "name", "") or ""
                model_id = (
                    raw_name.removeprefix("models/")
                    if hasattr(raw_name, "removeprefix")
                    else raw_name.replace("models/", "")
                )
                actions = getattr(m, "supported_actions", None) or []
                if not actions or "generateContent" in actions or "generate_content" in actions:
                    available.append(model_id)

            return available
        except Exception as e:
            if isinstance(e, ProviderAuthenticationError):
                raise
            logger.error(f"Failed to query available models from Gemini API: {e}")
            raise ProviderError(f"Failed to query available models: {e}")

    @classmethod
    def get_accessible_candidate_models(cls, api_key: Optional[str] = None) -> list[str]:
        """Returns candidate models verified as accessible to the configured account.

        If listing succeeds, only candidate models that appear in the available list are returned.
        Falls back safely to [cls.DEFAULT_MODEL] if query fails or returns no matches.
        """
        try:
            available = cls.list_available_models(api_key)
            accessible = [m for m in cls.CANDIDATE_MODELS if m in available]
            if accessible:
                return accessible
            if cls.DEFAULT_MODEL in available:
                return [cls.DEFAULT_MODEL]
            return available if available else [cls.DEFAULT_MODEL]
        except Exception:
            return [cls.DEFAULT_MODEL]

    def get_available_models(self) -> list[str]:
        """Queries official Gemini API for models available with the provider's API key."""
        return self.list_available_models(api_key=self.api_key)

    @classmethod
    def diagnose_connection(
        cls,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs: Any
    ) -> tuple[bool, str, dict[str, Any]]:
        """Performs a nuanced connection health check distinguishing failure modes."""
        key = api_key if api_key is not None else os.getenv("GEMINI_API_KEY", "")
        key = (key or "").strip()

        if model is not None:
            cleaned_model = model.strip()
            if not cleaned_model:
                return (
                    False,
                    "Configuration error: Model identifier cannot be empty.",
                    {"status": "INVALID_MODEL", "code": 400}
                )
            target_model: str = cleaned_model
        else:
            env_model = (os.getenv("GEMINI_MODEL") or "").strip()
            target_model = env_model if env_model else cls.DEFAULT_MODEL

        if not key:
            return (
                False,
                "Authentication failed: Gemini API key is missing or not configured.",
                {"status": "MISSING_KEY", "code": 401}
            )

        try:
            client = genai.Client(api_key=key)
            models_pager = client.models.list()
            available_models = []
            for m in models_pager:
                raw_name = getattr(m, "name", "") or ""
                model_id = (
                    raw_name.removeprefix("models/")
                    if hasattr(raw_name, "removeprefix")
                    else raw_name.replace("models/", "")
                )
                available_models.append(model_id)

            config = types.GenerateContentConfig(
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                temperature=0.0
            )
            client.models.generate_content(
                model=target_model,
                contents="Ping",
                config=config
            )

            model_status = "Verified Accessible" if target_model in available_models else "Inferred Available"
            msg = (
                f"Connected successfully. Model '{target_model}' is active "
                f"({model_status}; {len(available_models)} account models discovered)."
            )
            return (
                True,
                msg,
                {"status": "SUCCESS", "code": 200, "model": target_model, "available_count": len(available_models)}
            )

        except Exception as raw_e:
            err_msg = str(raw_e).lower()
            if "401" in err_msg or "403" in err_msg or "api_key_invalid" in err_msg or "permission_denied" in err_msg:
                return (
                    False,
                    "Authentication failed (HTTP 401/403): Invalid or unauthorized API key.",
                    {"status": "AUTHENTICATION_FAILED", "code": 401, "error": err_msg}
                )
            elif "429" in err_msg or "quota" in err_msg or "resource_exhausted" in err_msg:
                return (
                    False,
                    "Rate limit or quota exhausted (HTTP 429): Google Cloud billing or quota limit reached.",
                    {"status": "QUOTA_EXHAUSTED", "code": 429, "error": err_msg}
                )
            elif "404" in err_msg or "not_found" in err_msg:
                return (
                    False,
                    f"Model '{target_model}' was not found or is unavailable for this account (HTTP 404).",
                    {"status": "MODEL_UNAVAILABLE", "code": 404, "error": err_msg}
                )
            elif "timeout" in err_msg or "connect" in err_msg or "dns" in err_msg or "unreachable" in err_msg:
                return (
                    False,
                    "Network error: Unable to connect to Google Gemini API servers. Check your internet connection.",
                    {"status": "NETWORK_ERROR", "code": 0, "error": err_msg}
                )
            elif "500" in err_msg or "503" in err_msg:
                return (
                    False,
                    "Google Gemini service is temporarily unavailable (HTTP 503). Please try again later.",
                    {"status": "SERVICE_UNAVAILABLE", "code": 503, "error": err_msg}
                )
            return (
                False,
                f"Connection error: {raw_e}",
                {"status": "UNKNOWN_ERROR", "code": 500, "error": err_msg}
            )

    def _map_exception(self, e: Exception) -> Exception:
        """Translates underlying google-genai errors into domain exceptions."""
        if isinstance(e, ProviderError):
            return e

        if isinstance(e, APIError):
            code = getattr(e, "code", None)
            if code in (401, 403):
                return ProviderAuthenticationError("Gemini authentication failed. Please verify your API key.")
            elif code == 429:
                return ProviderRateLimitError("Gemini rate limit reached. Please wait and try again.")
            elif code in (500, 502, 503, 504):
                return ProviderServiceUnavailableError(f"Gemini service temporarily unavailable (HTTP {code}).")
            return ProviderResponseError(f"Gemini returned an unexpected response: {e}")

        err_str = str(e).lower()
        if "timeout" in err_str:
            return ProviderTimeoutError(f"Gemini request timed out: {e}")

        return ProviderError(f"Gemini provider error: {e}")

    def _prepare_config(
        self,
        system_instructions: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        response_model: Optional[Type[BaseModel]] = None
    ) -> types.GenerateContentConfig:
        """Constructs GenerateContentConfig including thinking options and structured schemas."""
        kwargs: dict[str, Any] = {}

        if system_instructions:
            kwargs["system_instruction"] = system_instructions

        if temperature is not None:
            kwargs["temperature"] = temperature

        target_model: str = str(model or self.default_model or self.DEFAULT_MODEL)
        target_lower = target_model.lower()

        # Apply thinking configuration for Gemini 3 and Gemini 4 models
        if "gemini-3" in target_lower or "gemini-4" in target_lower:
            level_enum = self.SUPPORTED_THINKING_LEVELS.get(
                self.thinking_level, types.ThinkingLevel.MEDIUM
            )
            kwargs["thinking_config"] = types.ThinkingConfig(thinking_level=level_enum)

        # Explicitly disable automatic function calling where not needed
        kwargs["automatic_function_calling"] = types.AutomaticFunctionCallingConfig(disable=True)

        if response_model is not None:
            kwargs["response_mime_type"] = "application/json"
            kwargs["response_schema"] = response_model

        return types.GenerateContentConfig(**kwargs)

    def _extract_response_text(self, response: Any) -> str:
        """Extracts text from response, excluding internal thought parts and thought signatures."""
        if hasattr(response, "text") and response.text is not None:
            return response.text

        # Inspect candidates and parts if .text is None or not present
        if hasattr(response, "candidates") and response.candidates:
            first_candidate = response.candidates[0]
            if hasattr(first_candidate, "content") and first_candidate.content:
                parts = getattr(first_candidate.content, "parts", None)
                if parts:
                    text_parts: list[str] = []
                    for part in parts:
                        # Exclude internal thought parts and thought signatures
                        if getattr(part, "thought", False):
                            continue
                        part_text = getattr(part, "text", None)
                        if isinstance(part_text, str) and part_text:
                            text_parts.append(part_text)
                    if text_parts:
                        return "".join(text_parts)

        return ""

    def generate(
        self,
        prompt: str,
        system_instructions: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> ProviderResponse:
        """Generates raw text with exponential backoff on transient errors."""
        target_model: str = str(model or self.default_model or self.DEFAULT_MODEL)
        config = self._prepare_config(
            system_instructions=system_instructions,
            model=target_model,
            temperature=temperature
        )

        max_attempts = 3
        delay = 2.0

        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"Generation request started (model: {target_model})")
                response = self.client.models.generate_content(
                    model=target_model,
                    contents=prompt,
                    config=config
                )

                usage = None
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    meta = response.usage_metadata
                    usage = ProviderUsage(
                        input_tokens=getattr(meta, "prompt_token_count", 0) or 0,
                        output_tokens=getattr(meta, "candidates_token_count", 0) or 0,
                        total_tokens=getattr(meta, "total_token_count", 0) or 0
                    )

                text = self._extract_response_text(response)
                logger.info("Generation completed successfully.")
                return ProviderResponse(
                    text=text,
                    model=target_model,
                    provider="gemini",
                    usage=usage
                )
            except Exception as raw_e:
                mapped_e = self._map_exception(raw_e)
                transient = (ProviderRateLimitError, ProviderServiceUnavailableError, ProviderTimeoutError)
                if isinstance(mapped_e, transient):
                    if attempt < max_attempts:
                        logger.warning(
                            f"Transient error: {mapped_e}. Retrying {attempt + 1}/{max_attempts} after {delay}s."
                        )
                        time.sleep(delay)
                        delay = min(delay * 2, 8.0)
                        continue
                logger.error(f"Generation failed after {attempt} attempts: {mapped_e}")
                raise mapped_e

        raise ProviderError("Generation failed.")

    def generate_structured(
        self,
        prompt: str,
        response_model: Type[BaseModel],
        system_instructions: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> Any:
        """Generates structured output parsed into the specified Pydantic model."""
        target_model: str = str(model or self.default_model or self.DEFAULT_MODEL)
        config = self._prepare_config(
            system_instructions=system_instructions,
            model=target_model,
            temperature=temperature,
            response_model=response_model
        )

        max_attempts = 3
        delay = 2.0

        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"Structured generation request started (model: {target_model})")
                response = self.client.models.generate_content(
                    model=target_model,
                    contents=prompt,
                    config=config
                )

                if hasattr(response, "parsed") and response.parsed is not None:
                    if isinstance(response.parsed, dict):
                        logger.info("Structured generation completed via response.parsed dict conversion.")
                        return response_model.model_validate(response.parsed)
                    logger.info("Structured generation completed successfully via response.parsed.")
                    return response.parsed

                raw_text = self._extract_response_text(response)
                stripped = raw_text.strip()
                if stripped.startswith("```"):
                    lines = stripped.splitlines()
                    if lines and lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].strip() == "```":
                        lines = lines[:-1]
                    stripped = "\n".join(lines).strip()

                if not stripped:
                    raise ProviderResponseError("Gemini returned an empty response.")

                try:
                    parsed_model = response_model.model_validate_json(stripped)
                except Exception:
                    first_brace = stripped.find("{")
                    last_brace = stripped.rfind("}")
                    if first_brace != -1 and last_brace > first_brace:
                        parsed_model = response_model.model_validate_json(
                            stripped[first_brace:last_brace + 1]
                        )
                    else:
                        raise
                logger.info("Structured generation completed successfully via JSON fallback.")
                return parsed_model

            except Exception as raw_e:
                mapped_e = self._map_exception(raw_e)
                transient = (ProviderRateLimitError, ProviderServiceUnavailableError, ProviderTimeoutError)
                if isinstance(mapped_e, transient):
                    if attempt < max_attempts:
                        logger.warning(
                            f"Transient error: {mapped_e}. Retrying {attempt + 1}/{max_attempts} after {delay}s."
                        )
                        time.sleep(delay)
                        delay = min(delay * 2, 8.0)
                        continue
                logger.error(f"Structured generation failed after {attempt} attempts: {mapped_e}")
                raise mapped_e

        raise ProviderError("Structured generation failed.")
