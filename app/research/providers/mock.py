"""Mock search provider for testing without external web access."""

from app.research.providers.base import SearchProvider
from app.research.models import SearchLandscape, SearchResult, SearchQuestion


class MockSearchProvider(SearchProvider):
    def search(self, query: str, num_results: int = 10) -> SearchLandscape:
        results = [
            SearchResult(
                title=f"Guide to {query} - Example 1",
                url="https://example.com/guide-1",
                domain="example.com",
                snippet=f"An in-depth look at {query} covering basic methods and advanced techniques.",
                position=1
            ),
            SearchResult(
                title=f"How to solve {query} easily",
                url="https://test.org/solve",
                domain="test.org",
                snippet=f"Quick tutorial on {query}. We explain the pros and cons.",
                position=2
            )
        ]
        questions = [
            SearchQuestion(question=f"What is the best way to do {query}?", source="people_also_ask")
        ]
        return SearchLandscape(
            query=query,
            results=results,
            related_queries=[f"{query} tutorial", f"{query} free"],
            questions=questions
        )
