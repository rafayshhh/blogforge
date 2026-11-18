"""Pydantic schemas for the generation pipeline and outline stages."""

from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.article import FAQItem


class GenerationRequest(BaseModel):
    """User request parameters to initiate article generation."""
    model_config = {"extra": "allow"}

    topic: str
    project_id: Optional[str] = None
    audience: Optional[str] = None
    content_type: Optional[str] = "Article"
    strategy: Optional[str] = None
    user_context: Optional[str] = None
    target_word_count: Optional[int] = 1200
    word_count_target: Optional[int] = None
    tone: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    verified_sources: List[str] = Field(default_factory=list)


class OutlineSection(BaseModel):
    """Structured outline entry representing a planned section."""
    model_config = {"extra": "allow"}

    id: str
    heading: str
    level: int = 2
    purpose: str = ""
    target_words: int = 250
    key_points: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    claims: List[str] = Field(default_factory=list)


class ArticleOutline(BaseModel):
    """Complete planned outline structure before writing begins."""
    model_config = {"extra": "allow"}

    title: str
    slug: str
    description: Optional[str] = ""
    sections: List[OutlineSection] = Field(default_factory=list)


class ArticleReview(BaseModel):
    """Critical audit report of an article draft."""
    model_config = {"extra": "allow"}

    unsupported_claims: List[str] = Field(default_factory=list)
    repetition_issues: List[str] = Field(default_factory=list)
    missing_elements: List[str] = Field(default_factory=list)
    original_value_suggestions: List[str] = Field(default_factory=list)
    brand_violations: List[str] = Field(default_factory=list)
    duplicate_paragraphs: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    overall_score: Optional[int] = None
    quality_score: Optional[int] = None

    def model_post_init(self, __context):
        if self.overall_score is not None and self.quality_score is None:
            self.quality_score = self.overall_score
        elif self.quality_score is not None and self.overall_score is None:
            self.overall_score = self.quality_score


class FAQData(BaseModel):
    """Structured container for generated FAQ items."""
    model_config = {"extra": "allow"}

    faqs: List[FAQItem] = Field(default_factory=list)
