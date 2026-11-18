"""Abstract base interface for AI providers."""

from abc import ABC, abstractmethod
from typing import Optional, Type, Any, List, Tuple, Dict
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

    @classmethod
    def diagnose_connection(
        cls,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs: Any
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Tests provider connectivity and authentication status."""
        return (False, "diagnose_connection not implemented for this provider.", {"status": "UNIMPLEMENTED"})

    @classmethod
    def list_available_models(
        cls,
        api_key: Optional[str] = None,
        **kwargs: Any
    ) -> List[str]:
        """Discovers or lists models accessible to this provider."""
        return []
