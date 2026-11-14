"""Abstract base interface for search research providers."""

from abc import ABC, abstractmethod
from app.research.models import SearchLandscape


class SearchProvider(ABC):
    """Abstract interface for querying external search sources and landscapes."""

    @abstractmethod
    def search(self, query: str, num_results: int = 10) -> SearchLandscape:
        """Executes a search query and returns structured search landscape data."""
        pass
