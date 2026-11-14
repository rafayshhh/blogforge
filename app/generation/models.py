"""Pydantic schemas for the generation pipeline and outline stages."""

from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.article import FAQItem


class GenerationRequest(BaseModel):
    """User request parameters to initiate article generation."""
    topic: str
    project_id: Optional[str] = None
    audience: Optional[str] = None
    content_type: Optional[str] = "Article"
    strategy: Optional[str] = None
    user_context: Optional[str] = None


class OutlineSection(BaseModel):
    """Structured outline entry representing a planned section."""
    id: str
    heading: str
    level: int = 2
    purpose: str = ""
    key_points: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)


class ArticleOutline(BaseModel):
    """Complete planned outline structure before writing begins."""
    title: str
    slug: str
    description: Optional[str] = ""
    sections: List[OutlineSection] = Field(default_factory=list)


class ArticleReview(BaseModel):
    """Critical audit report of an article draft."""
    unsupported_claims: List[str] = Field(default_factory=list)
    repetition_issues: List[str] = Field(default_factory=list)
    missing_elements: List[str] = Field(default_factory=list)
    original_value_suggestions: List[str] = Field(default_factory=list)
    overall_score: Optional[int] = None


class FAQData(BaseModel):
    """Structured container for generated FAQ items."""
    faqs: List[FAQItem] = Field(default_factory=list)
