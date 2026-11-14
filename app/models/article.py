"""Domain models representing articles, sections, SEO metadata, and FAQs."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ArticleSection(BaseModel):
    """Represents an individual section of an article."""
    id: str
    heading: str
    level: int = 2
    content: str = ""
    sources: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FAQItem(BaseModel):
    """Represents a question and answer pair for article FAQs."""
    question: str
    answer: str


class SEOMetadata(BaseModel):
    """Search Engine Optimization and Open Graph metadata."""
    seo_title: Optional[str] = None
    meta_description: Optional[str] = None
    slug: Optional[str] = None
    canonical_url: Optional[str] = None
    primary_keyword: Optional[str] = None
    secondary_keywords: List[str] = Field(default_factory=list)
    og_title: Optional[str] = None
    og_description: Optional[str] = None


class Article(BaseModel):
    """Core domain model representing a complete or draft article."""
    project_id: Optional[str] = None
    title: str
    slug: str
    description: Optional[str] = ""
    category: Optional[str] = None
    author: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    content: str = ""
    sections: List[ArticleSection] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    faq: List[FAQItem] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    internal_links: List[str] = Field(default_factory=list)
    seo: Dict[str, Any] = Field(default_factory=dict)
    seo_metadata: Optional[SEOMetadata] = Field(default_factory=SEOMetadata)
    seo_audit: Optional[Any] = None
