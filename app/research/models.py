"""Pydantic data models for the research engine and search landscapes."""

from typing import List, Optional
from pydantic import BaseModel


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


class ResearchRun(BaseModel):
    topic: str
    queries: List[str]
    search_landscape: List[SearchLandscape]
    strategy: ContentStrategy
    created_at: str
    metadata: dict
