"""Research orchestration engine synthesizing queries, landscapes, and strategies."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.providers.base import AIProvider
from app.research.providers.base import SearchProvider
from app.research.models import ResearchRun, SearchLandscape, ContentStrategy


class QueryList(BaseModel):
    """Pydantic model for structured list of search queries."""
    queries: List[str] = Field(default_factory=list)


class ResearchEngine:
    """Coordinates search intelligence, competitive landscape analysis, and strategy drafting."""

    def __init__(self, ai_provider: AIProvider, search_provider: SearchProvider):
        self.ai = ai_provider
        self.search = search_provider

    def generate_queries(self, topic: str, count: int = 3) -> List[str]:
        """Generates targeted search queries to explore a topic."""
        prompt = (
            f"Generate a list of {count} strategic search queries to research the topic: '{topic}'.\n"
            "Include intent-based, comparison, and practical search variations."
        )
        res: QueryList = self.ai.generate_structured(prompt, QueryList)
        return res.queries if res and res.queries else [topic]

    def run_research(
        self,
        topic: str,
        depth: str = "Standard",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ResearchRun:
        """Executes full research cycle: query generation, landscape fetching, and strategy synthesis."""
        meta = metadata or {}
        meta["depth"] = depth

        queries = self.generate_queries(topic)
        landscapes: List[SearchLandscape] = []
        for q in queries:
            landscapes.append(self.search.search(q))

        # Synthesize strategic content angles from landscape
        landscape_summary = "\n".join([
            f"Query: {landscape.query}\nTop Results: {', '.join([r.title for r in landscape.results[:3]])}"
            for landscape in landscapes
        ])

        strategy_prompt = (
            f"Based on the following search landscape for topic '{topic}', "
            f"produce a comprehensive ContentStrategy:\n\n{landscape_summary}"
        )

        strategy: ContentStrategy = self.ai.generate_structured(strategy_prompt, ContentStrategy)

        return ResearchRun(
            topic=topic,
            queries=queries,
            search_landscape=landscapes,
            strategy=strategy,
            created_at=datetime.now().isoformat(),
            metadata=meta
        )
