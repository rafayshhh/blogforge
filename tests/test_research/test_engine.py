"""Unit tests for the research query and strategy engine."""

from unittest.mock import MagicMock

from app.research.engine import ResearchEngine, QueryList
from app.research.models import ContentStrategy, SearchLandscape


def test_engine_generate_queries():
    ai = MagicMock()
    search = MagicMock()
    ai.generate_structured.return_value = QueryList(queries=["q1", "q2"])

    engine = ResearchEngine(ai, search)
    queries = engine.generate_queries("test")

    assert len(queries) == 2
    assert "q1" in queries


def test_engine_run_research():
    ai = MagicMock()
    search = MagicMock()
    ai.generate_structured.side_effect = [
        QueryList(queries=["q1"]),
        ContentStrategy(
            primary_intent="info",
            secondary_intents=[],
            audience="devs",
            primary_topic="test",
            secondary_topics=[],
            questions_to_answer=[],
            content_gaps=[],
            recommended_angle="Deep dive",
            recommended_outline=[],
            differentiators=[],
            sources=[]
        )
    ]
    search.search.return_value = SearchLandscape(
        query="q1",
        results=[],
        related_queries=[],
        questions=[]
    )

    engine = ResearchEngine(ai, search)
    run = engine.run_research("Test topic", depth="Quick")

    assert run.topic == "Test topic"
    assert len(run.queries) == 1
    assert run.strategy.primary_intent == "info"
    assert run.metadata["depth"] == "Quick"
