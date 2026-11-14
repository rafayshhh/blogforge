"""Google Gemini AI Provider implementing google-genai SDK."""

import logging
import os
import time
from typing import Optional, Type, Any
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
    """Integrates with Google GenAI SDK for Gemini 2.5 / 3.x models."""

    def __init__(self, api_key: Optional[str] = None, default_model: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.error("Gemini API key is not configured.")
            raise ProviderAuthenticationError("Gemini API key is not configured.")

        self.default_model = default_model or os.getenv("GEMINI_MODEL", "gemini-3.7-flash")
        try:
            self.client = genai.Client(api_key=self.api_key)
            logger.info(f"Gemini provider initialized with default model: {self.default_model}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise ProviderError(f"Failed to initialize Gemini client: {e}")

    def _map_exception(self, e: Exception) -> Exception:
        """Translates underlying google-genai errors into domain exceptions."""
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

        target_model = model or self.default_model
        if "gemini-3" in target_model.lower():
            kwargs["thinking_config"] = types.ThinkingConfig(thinking_level="medium")

        kwargs["automatic_function_calling"] = types.AutomaticFunctionCallingConfig(disable=True)

        if response_model is not None:
            kwargs["response_mime_type"] = "application/json"
            kwargs["response_schema"] = response_model

        return types.GenerateContentConfig(**kwargs)

    def generate(
        self,
        prompt: str,
        system_instructions: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> ProviderResponse:
        """Generates raw text with exponential backoff on transient errors."""
        target_model = model or self.default_model
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

                logger.info("Generation completed successfully.")
                return ProviderResponse(
                    text=response.text or "",
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
        target_model = model or self.default_model
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
                    logger.info("Structured generation completed successfully.")
                    return response.parsed

                raw_text = response.text or ""
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

                parsed_model = response_model.model_validate_json(stripped)
                logger.info("Structured generation completed successfully.")
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
