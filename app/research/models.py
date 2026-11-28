"""Pydantic data models for the research engine, search landscapes, and evidence grounding."""

import uuid
from typing import List, Optional
from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    title: str
    url: str
    domain: str
    snippet: str
    position: Optional[int] = None


class SearchQuestion(BaseModel):
    question: str
    source: str


class SearchLandscape(BaseModel):
    query: str
    results: List[SearchResult] = []
    related_queries: List[str] = []
    questions: List[SearchQuestion] = []


class ContentGap(BaseModel):
    topic: str
    description: str
    importance: str
    evidence: str


class ContentStrategy(BaseModel):
    primary_intent: str
    secondary_intents: List[str] = []
    audience: str
    primary_topic: str
    secondary_topics: List[str] = []
    questions_to_answer: List[str] = []
    content_gaps: List[ContentGap] = []
    recommended_angle: str
    recommended_outline: List[str] = []
    differentiators: List[str] = []
    sources: List[str] = []


class VerifiedSource(BaseModel):
    """Enriched, deduplicated, and verified research reference."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    url: str
    canonical_url: str
    title: str
    domain: str
    snippet: str
    credibility: str = "Secondary"  # "Primary", "Institutional", "Industry", "Secondary"
    is_accessible: bool = True
    http_status: int = 200
    published_date: Optional[str] = None
    extracted_claims: List[str] = Field(default_factory=list)
    relevance_score: float = 1.0


class ClaimGrounding(BaseModel):
    """Specific factual claim tied to evidence and verifiable source."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    claim: str
    source_id: str
    source_url: str
    source_title: str
    credibility_tier: str = "Primary"
    confidence: float = 1.0


class ResearchRun(BaseModel):
    topic: str
    queries: List[str]
    search_landscape: List[SearchLandscape]
    strategy: ContentStrategy
    created_at: str
    metadata: dict = Field(default_factory=dict)
    verified_sources: List[VerifiedSource] = Field(default_factory=list)
    grounded_claims: List[ClaimGrounding] = Field(default_factory=list)
    notes: str = ""
