"""Unit tests for the multi-stage generation pipeline."""

from unittest.mock import MagicMock

from app.generation.models import GenerationRequest, ArticleOutline, OutlineSection
from app.generation.pipeline import GenerationPipeline


def test_pipeline_generate_outline():
    ai = MagicMock()
    mock_outline = ArticleOutline(
        title="Test",
        slug="test",
        description="intro",
        sections=[OutlineSection(id="1", heading="H1", level=2, purpose="p", key_points=["k"])]
    )
    ai.generate_structured.return_value = mock_outline

    pipeline = GenerationPipeline(ai)
    req = GenerationRequest(topic="Test")
    outline = pipeline.generate_outline(req)

    assert outline.title == "Test"
    assert len(outline.sections) == 1


def test_pipeline_generate_article(tmp_path):
    ai = MagicMock()
    mock_response = MagicMock(text="Mock section content")
    ai.generate.return_value = mock_response

    gen_dir = str(tmp_path / "generation")
    art_dir = str(tmp_path / "articles")
    pipeline = GenerationPipeline(ai, generation_dir=gen_dir, articles_dir=art_dir)
    req = GenerationRequest(topic="Test")
    outline = ArticleOutline(
        title="Test Title",
        slug="test-title",
        description="intro",
        sections=[OutlineSection(id="1", heading="H1", level=2, purpose="p", key_points=["k"])]
    )

    article = pipeline.generate_article(req, outline)
    assert article.title == "Test Title"
    assert len(article.sections) == 1
    assert "Mock section content" in article.content


def test_pipeline_cancellation(tmp_path):
    ai = MagicMock()
    ai.generate.return_value = MagicMock(text="Content")

    gen_dir = str(tmp_path / "generation")
    art_dir = str(tmp_path / "articles")
    pipeline = GenerationPipeline(ai, generation_dir=gen_dir, articles_dir=art_dir)
    req = GenerationRequest(topic="Test")
    outline = ArticleOutline(
        title="Test Title",
        slug="test-title",
        description="intro",
        sections=[
            OutlineSection(id="1", heading="H1", level=2, purpose="p", key_points=["k"]),
            OutlineSection(id="2", heading="H2", level=2, purpose="p", key_points=["k"])
        ]
    )

    pipeline.cancel()
    article = pipeline.generate_article(req, outline)
    assert len(article.sections) == 0
