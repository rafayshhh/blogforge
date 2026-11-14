"""Data models for Project definitions, brand profiles, products, and links."""

import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class InternalLink(BaseModel):
    """An internal reference URL for contextual in-article linking."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    url: str
    title: str
    description: Optional[str] = None
    type: str = "Blog"
    keywords: List[str] = Field(default_factory=list)
    active: bool = True

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v_stripped = v.strip()
        if not (v_stripped.startswith("http://") or v_stripped.startswith("https://") or v_stripped.startswith("/")):
            raise ValueError("URL must be absolute (http/https) or relative starting with '/'")
        return v_stripped


class Product(BaseModel):
    """A product or service associated with the brand."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    type: str = "Tool"
    url: Optional[str] = None
    features: List[str] = Field(default_factory=list)
    target_audience: Optional[str] = None
    status: str = "Active"


class BrandProfile(BaseModel):
    """Brand identity guidelines and writing voice rules."""
    brand_name: str = ""
    description: str = ""
    mission: str = ""
    target_audience: str = ""
    tone: str = "Professional"
    writing_style: str = "Clear and direct"
    preferred_terms: List[str] = Field(default_factory=list)
    avoided_terms: List[str] = Field(default_factory=list)
    language: str = "English"
    locale: str = "en-US"
    author_name: str = ""
    author_bio: str = ""
    content_rules: List[str] = Field(default_factory=list)


class NextJSIntegration(BaseModel):
    """Configuration settings for automated Next.js export."""
    enabled: bool = False
    project_directory: Optional[str] = None
    content_directory: Optional[str] = None
    image_directory: Optional[str] = None
    export_format: str = "JSON"


class Project(BaseModel):
    """Core Project entity encapsulating brand rules, products, and configurations."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    website_url: Optional[str] = None
    brand_profile: BrandProfile = Field(default_factory=BrandProfile)
    products: List[Product] = Field(default_factory=list)
    internal_links: List[InternalLink] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    active: bool = True
    nextjs_integration: NextJSIntegration = Field(default_factory=NextJSIntegration)
