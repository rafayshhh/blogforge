"""Abstract base interface for AI providers."""

from abc import ABC, abstractmethod
from typing import Optional, Type, Any
from pydantic import BaseModel
from app.models.provider import ProviderResponse


class AIProvider(ABC):
    """Abstract interface defining required generation capabilities for AI models."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_instructions: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> ProviderResponse:
        """Generates raw text response for the given prompt."""
        pass

    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        response_model: Type[BaseModel],
        system_instructions: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> Any:
        """Generates a structured response validated against a Pydantic model."""
        pass
