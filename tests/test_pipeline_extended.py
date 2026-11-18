"""Extended tests for GenerationPipeline, OutlineGenerator, ArticleWriter, and ArticleReviewer."""

import os
from unittest.mock import MagicMock
from app.generation.models import (
    GenerationRequest,
    ArticleOutline,
    OutlineSection,
    FAQData,
    ArticleReview,
)
from app.generation.pipeline import GenerationPipeline
from app.generation.outline import OutlineGenerator
from app.generation.writer import ArticleWriter
from app.models.article import FAQItem
from app.projects.models import Product
from app.projects.repository import ProjectRepository
from app.projects.service import ProjectService


def test_outline_generator_with_project_context(tmp_path, monkeypatch):
    """Verify OutlineGenerator injects filtered project brand context into the prompt."""
    monkeypatch.chdir(tmp_path)
    repo = ProjectRepository(data_dir=str(tmp_path / "data" / "projects"))
    service = ProjectService(repo=repo)

    proj = service.create_project(name="DevStudio", description="Developer Tools")
    proj.products.append(Product(name="CodeLint", description="Fast linter for Python"))
    service.update_project(proj)

    mock_ai = MagicMock()
    mock_outline = ArticleOutline(
        title="Modern Linting in Python",
        slug="modern-linting-python",
        description="Speed up CI/CD",
        sections=[OutlineSection(id="s1", heading="Linting Setup", level=2)]
    )
    mock_ai.generate_structured.return_value = mock_outline

    generator = OutlineGenerator(mock_ai)
    generator.project_service = service

    req = GenerationRequest(
        topic="Fast Linting Setup",
        project_id=proj.id,
        audience="Senior Developers",
        content_type="Technical Guide",
        strategy="Practical Tutorial",
        user_context="Focus on CI performance"
    )

    outline = generator.generate(req)
    assert outline.title == "Modern Linting in Python"

    # Verify prompt arguments passed to AI
    call_args = mock_ai.generate_structured.call_args[1]
    prompt_sent = call_args["prompt"]
    assert "DevStudio" in prompt_sent
    assert "Senior Developers" in prompt_sent
    assert "Technical Guide" in prompt_sent
    assert "CI performance" in prompt_sent


def test_article_writer_markdown_codeblock_stripping(tmp_path, monkeypatch):
    """Verify ArticleWriter strips triple-backtick markdown blocks if returned by AI."""
    monkeypatch.chdir(tmp_path)
    mock_ai = MagicMock()
    raw_markdown = "```markdown\nThis is pure text inside a markdown codeblock.\n```"
    mock_ai.generate.return_value = MagicMock(text=raw_markdown)

    writer = ArticleWriter(mock_ai)
    sec = OutlineSection(id="1", heading="Introduction", level=2, key_points=["kp1"])
    req = GenerationRequest(topic="Testing")

    content = writer.write_section(sec, req)
    assert content == "This is pure text inside a markdown codeblock."


def test_article_writer_with_project_context(tmp_path, monkeypatch):
    """Verify ArticleWriter passes filtered project context when project_id is provided."""
    monkeypatch.chdir(tmp_path)
    repo = ProjectRepository(data_dir=str(tmp_path / "data" / "projects"))
    service = ProjectService(repo=repo)

    proj = service.create_project(name="WebCorp", description="High performance web apps")
    proj.products.append(Product(name="TurboRouter", description="Ultra fast HTTP routing"))
    service.update_project(proj)

    mock_ai = MagicMock()
    mock_ai.generate.return_value = MagicMock(text="TurboRouter makes routing seamless.")

    writer = ArticleWriter(mock_ai)
    writer.project_service = service

    sec = OutlineSection(id="1", heading="Routing Engine", level=2)
    req = GenerationRequest(topic="High performance web apps routing", project_id=proj.id)

    content = writer.write_section(sec, req)
    assert "TurboRouter makes routing seamless." in content

    call_prompt = mock_ai.generate.call_args[0][0]
    assert "WebCorp" in call_prompt


def test_pipeline_progress_callbacks_and_intermediate_cleanup(tmp_path, monkeypatch):
    """Verify GenerationPipeline invokes progress callbacks and properly cleans up partial files."""
    monkeypatch.chdir(tmp_path)

    mock_ai = MagicMock()
    mock_outline = ArticleOutline(
        title="Full Lifecycle Test",
        slug="lifecycle-test",
        description="Testing complete lifecycle",
        sections=[
            OutlineSection(id="1", heading="Step 1", level=2),
            OutlineSection(id="2", heading="Step 2", level=3)
        ]
    )
    mock_ai.generate_structured.side_effect = [
        FAQData(faqs=[FAQItem(question="Complete?", answer="Yes.")]),
        ArticleReview(
            unsupported_claims=[],
            repetition_issues=["None detected"],
            missing_elements=[],
            original_value_suggestions=["Benchmark numbers"],
            overall_score=95
        )
    ]
    mock_ai.generate.side_effect = [
        MagicMock(text="Section 1 content body."),
        MagicMock(text="Section 2 content body.")
    ]

    pipeline = GenerationPipeline(mock_ai)
    req = GenerationRequest(topic="Full Lifecycle Test")

    callbacks_received = []

    def on_progress(msg):
        callbacks_received.append(msg)

    # 1. Generate Article
    article = pipeline.generate_article(req, mock_outline, progress_callback=on_progress)
    assert len(article.sections) == 2
    assert "Writing section 1 of 2: Step 1" in callbacks_received
    assert "Writing section 2 of 2: Step 2" in callbacks_received

    # Verify partial file exists in data/generation
    partial_file = tmp_path / "data" / "generation" / f"{pipeline.run_id}_partial.json"
    assert partial_file.exists()

    # 2. Finalize Article
    final_article = pipeline.finalize_article(article, req, progress_callback=on_progress)
    assert "Generating FAQ..." in callbacks_received
    assert len(final_article.faq) == 1

    # Verify final article file created and partial file deleted
    final_file = tmp_path / "data" / "articles" / f"{pipeline.run_id}.json"
    assert final_file.exists()
    assert not partial_file.exists()

    # 3. Review Article
    review = pipeline.review_article(final_article, req, progress_callback=on_progress)
    assert "Reviewing article..." in callbacks_received
    assert review is not None
    assert review.overall_score == 95


def test_pipeline_cancellation_during_generation_and_review(tmp_path, monkeypatch):
    """Verify pipeline respects cancellation at all workflow stages."""
    monkeypatch.chdir(tmp_path)
    mock_ai = MagicMock()
    mock_ai.generate.return_value = MagicMock(text="Some text")

    pipeline = GenerationPipeline(mock_ai)
    req = GenerationRequest(topic="Cancelled Pipeline")
    outline = ArticleOutline(
        title="Cancelled Outline",
        slug="cancelled-outline",
        sections=[
            OutlineSection(id="1", heading="Sec 1", level=2),
            OutlineSection(id="2", heading="Sec 2", level=2)
        ]
    )

    # Cancel before generation
    pipeline.cancel()
    cancelled_callbacks = []
    art = pipeline.generate_article(req, outline, progress_callback=lambda m: cancelled_callbacks.append(m))
    assert len(art.sections) == 0
    assert "Generation cancelled." in cancelled_callbacks

    # Finalize while cancelled should return article unchanged
    finalized = pipeline.finalize_article(art, req)
    assert finalized.faq == []
    # No file written
    assert not os.path.exists(f"data/articles/{pipeline.run_id}.json")

    # Review while cancelled should return None
    review = pipeline.review_article(art, req)
    assert review is None
