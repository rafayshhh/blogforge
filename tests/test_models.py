"""Comprehensive tests for article, section, SEO, and FAQ domain models."""

import pytest
from pydantic import ValidationError
from app.models.article import Article, ArticleSection, FAQItem, SEOMetadata


def test_article_section_creation_and_defaults():
    """Verify ArticleSection default field values and assignments."""
    sec = ArticleSection(id="sec-1", heading="Architecture Principles")
    assert sec.id == "sec-1"
    assert sec.heading == "Architecture Principles"
    assert sec.level == 2
    assert sec.content == ""
    assert sec.sources == []
    assert sec.metadata == {}


def test_article_section_custom_values():
    """Verify ArticleSection preserves complex metadata and source lists."""
    sec = ArticleSection(
        id="sec-2",
        heading="Deep Dive",
        level=3,
        content="Technical analysis details.",
        sources=["https://example.com/source1", "https://example.com/source2"],
        metadata={"reviewed": True, "token_count": 420}
    )
    assert sec.level == 3
    assert len(sec.sources) == 2
    assert sec.metadata["reviewed"] is True
    assert sec.metadata["token_count"] == 420


def test_faq_item_validations():
    """Verify FAQItem validation of required fields."""
    faq = FAQItem(question="What is BlogForge?", answer="An open-source AI content studio.")
    assert faq.question == "What is BlogForge?"
    assert faq.answer == "An open-source AI content studio."

    # Missing required field
    with pytest.raises(ValidationError):
        FAQItem(question="Missing Answer?")


def test_seo_metadata_defaults_and_assignments():
    """Verify SEOMetadata default values and custom assignments."""
    seo_default = SEOMetadata()
    assert seo_default.seo_title is None
    assert seo_default.meta_description is None
    assert seo_default.secondary_keywords == []

    seo_custom = SEOMetadata(
        seo_title="Best Python Practices 2026",
        meta_description="A complete guide to modern Python engineering.",
        slug="best-python-practices-2026",
        primary_keyword="python practices",
        secondary_keywords=["clean code", "pydantic", "pyside6"],
        og_title="Best Python Practices",
        og_description="Modern Python guide"
    )
    assert seo_custom.seo_title == "Best Python Practices 2026"
    assert len(seo_custom.secondary_keywords) == 3
    assert seo_custom.og_title == "Best Python Practices"


def test_article_creation_defaults():
    """Verify Article default fields upon creation."""
    article = Article(title="Test Article", slug="test-article")
    assert article.title == "Test Article"
    assert article.slug == "test-article"
    assert article.description == ""
    assert article.content == ""
    assert article.sections == []
    assert article.keywords == []
    assert article.faq == []
    assert article.sources == []
    assert article.internal_links == []
    assert isinstance(article.seo_metadata, SEOMetadata)


def test_article_missing_required_fields():
    """Verify Article raises ValidationError if title or slug are missing."""
    with pytest.raises(ValidationError):
        Article(title="Only Title")

    with pytest.raises(ValidationError):
        Article(slug="only-slug")


def test_article_json_serialization_roundtrip():
    """Verify complete lossless JSON serialization and deserialization."""
    original = Article(
        project_id="proj-123",
        title="Comprehensive System Design",
        slug="system-design-guide",
        description="Comprehensive guide to high-throughput systems.",
        category="Engineering",
        author="Lead Architect",
        created_at="2026-11-14T10:00:00Z",
        updated_at="2026-11-14T10:30:00Z",
        content="# Comprehensive System Design\n\nFull article content.",
        sections=[
            ArticleSection(id="s1", heading="Introduction", level=2, content="Intro paragraph."),
            ArticleSection(id="s2", heading="Scalability", level=2, content="Scale paragraph.")
        ],
        keywords=["architecture", "scale", "performance"],
        faq=[
            FAQItem(question="Is it scalable?", answer="Yes, linearly scalable.")
        ],
        sources=["https://arxiv.org/abs/example"],
        internal_links=["/docs/architecture"],
        seo={"custom_meta": "value"},
        seo_metadata=SEOMetadata(
            seo_title="System Design Guide 2026",
            meta_description="Guide to systems",
            primary_keyword="system design"
        )
    )

    json_str = original.model_dump_json(indent=2)
    deserialized = Article.model_validate_json(json_str)

    assert deserialized.project_id == original.project_id
    assert deserialized.title == original.title
    assert deserialized.slug == original.slug
    assert len(deserialized.sections) == 2
    assert deserialized.sections[0].heading == "Introduction"
    assert len(deserialized.faq) == 1
    assert deserialized.faq[0].answer == "Yes, linearly scalable."
    assert deserialized.seo_metadata.primary_keyword == "system design"
    assert deserialized.keywords == ["architecture", "scale", "performance"]


def test_article_unicode_and_emojis():
    """Verify Article handles diverse unicode alphabets, symbols, and emojis seamlessly."""
    unicode_title = "Modern AI 🚀: 日本語のテスト & العربية and Accents (é, è, ç, ñ)"
    unicode_content = (
        "Emoji test: 🛠️ ⚡ 🌐 💡 🔒 🚀\n"
        "Cyrillic: Тестирование системы BlogForge\n"
        "Chinese: 博客锻造系统架构测试\n"
        "Mathematical symbols: ∑(x_i) = ∫ f(x)dx ≈ ∞"
    )

    article = Article(
        title=unicode_title,
        slug="modern-ai-test",
        content=unicode_content,
        sections=[
            ArticleSection(id="u1", heading="セクション 1 🚀", level=2, content=unicode_content)
        ],
        faq=[
            FAQItem(question="هل يعمل مع اللغة العربية؟", answer="نعم، يعمل بشكل ممتاز! 🌟")
        ]
    )

    json_data = article.model_dump_json()
    reloaded = Article.model_validate_json(json_data)

    assert reloaded.title == unicode_title
    assert reloaded.sections[0].heading == "セクション 1 🚀"
    assert reloaded.faq[0].question == "هل يعمل مع اللغة العربية؟"
    assert "🚀" in reloaded.content


def test_article_large_content():
    """Verify Article handles large content bodies (10,000+ words) without degradation."""
    large_paragraph = "BlogForge provides high performance automated content generation workflows. " * 50
    sections = [
        ArticleSection(id=f"sec-{i}", heading=f"Chapter {i}", level=2, content=large_paragraph)
        for i in range(25)
    ]
    full_text = "\n\n".join(s.content for s in sections)

    article = Article(
        title="Large Scale Document",
        slug="large-scale-doc",
        content=full_text,
        sections=sections
    )

    word_count = len(article.content.split())
    assert word_count >= 10000

    json_str = article.model_dump_json()
    restored = Article.model_validate_json(json_str)
    assert len(restored.sections) == 25
    assert len(restored.content.split()) == word_count
