"""Research orchestration engine synthesizing queries, landscapes, and grounded strategies."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.providers.base import AIProvider
from app.research.providers.base import SearchProvider
from app.research.models import ResearchRun, SearchLandscape, ContentStrategy
from app.research.sources import deduplicate_and_verify_sources


class QueryList(BaseModel):
    """Pydantic model for structured list of search queries."""
    queries: List[str] = Field(default_factory=list)


class ResearchEngine:
    """Coordinates search intelligence, source verification, claim grounding, and strategy drafting."""

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
        """Executes full research cycle: query generation, landscape fetching, source verification,
        and strategy synthesis."""
        meta = metadata or {}
        meta["depth"] = depth

        queries = self.generate_queries(topic)
        landscapes: List[SearchLandscape] = []
        for q in queries:
            landscapes.append(self.search.search(q))

        # Deduplicate, verify URLs, classify credibility, and extract claims
        verified_sources, grounded_claims = deduplicate_and_verify_sources(landscapes, topic)

        # Baseline summary retaining format expectations for backwards compatibility
        landscape_summary = "\n".join([
            f"Query: {landscape.query}\nTop Results: {', '.join([r.title for r in landscape.results[:3]])}"
            for landscape in landscapes
        ])

        # Enriched verified evidence sources
        sources_summary = "\n".join([
            f"- [{src.credibility}] {src.title} ({src.canonical_url}): {src.snippet[:200]}"
            for src in verified_sources[:6]
        ])

        claims_summary = "\n".join([
            f"* {c.claim} (Source: {c.source_title})"
            for c in grounded_claims[:8]
        ])

        full_evidence_summary = (
            f"{landscape_summary}\n\n"
            f"Verified Evidence Sources:\n{sources_summary or 'No external sources'}\n\n"
            f"Extracted Grounded Claims:\n{claims_summary or 'None'}"
        )

        strategy_prompt = (
            f"Based on the following search landscape for topic '{topic}', "
            f"produce a comprehensive ContentStrategy:\n\n{full_evidence_summary}"
        )

        strategy: ContentStrategy = self.ai.generate_structured(strategy_prompt, ContentStrategy)

        return ResearchRun(
            topic=topic,
            queries=queries,
            search_landscape=landscapes,
            verified_sources=verified_sources,
            grounded_claims=grounded_claims,
            strategy=strategy,
            created_at=datetime.now().isoformat(),
            metadata=meta
        )
