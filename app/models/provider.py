"""Data models for AI provider responses and token metrics."""

from typing import Optional
from pydantic import BaseModel


class ProviderUsage(BaseModel):
    """Token usage metrics returned by the AI provider."""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class ProviderResponse(BaseModel):
    """Standardized response from an AI provider."""
    text: str
    model: str = ""
    provider: str = ""
    usage: Optional[ProviderUsage] = None
