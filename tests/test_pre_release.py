"""Comprehensive pre-release verification tests covering all critical system behaviors."""

import os
from unittest.mock import MagicMock

from app.core.config import load_config
from app.models.article import Article, ArticleSection, FAQItem
from app.projects.models import Project, Product, InternalLink
from app.projects.repository import ProjectRepository
from app.projects.service import ProjectService
from app.generation.models import GenerationRequest, ArticleOutline, OutlineSection, FAQData
from app.generation.pipeline import GenerationPipeline
from app.export.markdown import export_markdown
from app.export.html import export_html
from app.export.json import export_json
from app.integrations.nextjs.exporter import NextJSExporter
from app.providers.gemini import GeminiProvider


def test_configuration_loading(tmp_path, monkeypatch):
    """Verify configuration loading correctly parses environment variables."""
    fake_env = tmp_path / ".env"
    fake_env.write_text("TEST_VAR=BLOGFORGE_TEST_OK\nGEMINI_MODEL=gemini-3.8-flash\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    load_config()
    assert os.getenv("TEST_VAR") == "BLOGFORGE_TEST_OK"
    assert os.getenv("GEMINI_MODEL") == "gemini-3.8-flash"


def test_gemini_provider_safe_initialization(monkeypatch):
    """Verify GeminiProvider initializes cleanly with placeholder credentials without making external calls."""
    monkeypatch.setenv("GEMINI_API_KEY", "PLACEHOLDER_SAFE_TEST_KEY_12345")
    provider = GeminiProvider(api_key="PLACEHOLDER_SAFE_TEST_KEY_12345", default_model="gemini-3.8-flash")
    assert provider.api_key == "PLACEHOLDER_SAFE_TEST_KEY_12345"
    assert provider.default_model == "gemini-3.8-flash"
    assert provider.client is not None


def test_article_generation_pipeline_mocked():
    """Verify full end-to-end article generation workflow with mocked external API calls."""
    mock_ai = MagicMock()

    mock_outline = ArticleOutline(
        title="Modern Python Architecture",
        slug="modern-python-architecture",
        description="A comprehensive guide to modern Python architectures.",
        sections=[
            OutlineSection(id="s1", heading="Introduction", level=2, purpose="Intro", key_points=["kp1"]),
            OutlineSection(id="s2", heading="Core Patterns", level=2, purpose="Patterns", key_points=["kp2"]),
        ]
    )
    mock_ai.generate_structured.side_effect = [
        mock_outline,  # generate_outline
        FAQData(faqs=[FAQItem(question="Is this scalable?", answer="Yes, highly Scalable.")]),  # finalize_article faq
    ]
    mock_ai.generate.side_effect = [
        MagicMock(text="Introduction content paragraph."),
        MagicMock(text="Core patterns content paragraph."),
    ]

    pipeline = GenerationPipeline(mock_ai)
    req = GenerationRequest(topic="Modern Python Architecture")

    # Step 1: Outline
    outline = pipeline.generate_outline(req)
    assert outline.title == "Modern Python Architecture"
    assert len(outline.sections) == 2

    # Step 2: Section-by-section writing
    article = pipeline.generate_article(req, outline)
    assert len(article.sections) == 2
    assert "Introduction content paragraph." in article.content
    assert "Core patterns content paragraph." in article.content

    # Step 3: Finalization & FAQ
    final = pipeline.finalize_article(article, req)
    assert len(final.faq) == 1
    assert final.faq[0].question == "Is this scalable?"


def test_cancellation_behavior():
    """Verify that canceling the generation pipeline halts section processing immediately."""
    mock_ai = MagicMock()
    mock_ai.generate.return_value = MagicMock(text="Section text")

    pipeline = GenerationPipeline(mock_ai)
    req = GenerationRequest(topic="Cancelled Topic")
    outline = ArticleOutline(
        title="Cancelled",
        slug="cancelled",
        sections=[
            OutlineSection(id="1", heading="Sec 1", level=2),
            OutlineSection(id="2", heading="Sec 2", level=2),
        ]
    )

    pipeline.cancel()
    article = pipeline.generate_article(req, outline)
    assert len(article.sections) == 0


def test_export_functionality_all_formats(tmp_path):
    """Verify that all exporters (Markdown, HTML, JSON, Next.js) output valid formatted content."""
    article = Article(
        title="Export Test",
        slug="export-test",
        description="Testing exporters",
        content="Sample content body.",
        sections=[
            ArticleSection(id="1", heading="Overview", level=2, content="Detailed section overview.")
        ],
        faq=[FAQItem(question="Ready?", answer="Yes.")]
    )

    # Markdown
    md = export_markdown(article)
    assert "# Export Test" in md
    assert "## Overview" in md
    assert "Detailed section overview." in md
    assert "## FAQ" in md

    # HTML
    html = export_html(article)
    assert "<h1>Export Test</h1>" in html
    assert "<h2>Overview</h2>" in html
    assert "<dt>Ready?</dt>" in html

    # JSON
    json_str = export_json(article)
    assert '"title": "Export Test"' in json_str

    # Next.js export
    project = Project(
        name="NextJS Project",
        nextjs_integration={
            "enabled": True,
            "content_directory": str(tmp_path / "nextjs_content"),
            "export_format": "MARKDOWN"
        }
    )
    exporter = NextJSExporter()
    assert exporter.test_connection(project) is True
    exported_file = exporter.export(article, project)
    assert os.path.exists(exported_file)
    with open(exported_file, "r", encoding="utf-8") as f:
        assert "# Export Test" in f.read()


def test_project_persistence_and_service(tmp_path):
    """Verify local filesystem JSON project repository and service operations."""
    repo = ProjectRepository(data_dir=str(tmp_path / "projects"))
    service = ProjectService(repo=repo)

    # Create
    proj = service.create_project(name="SaaS Brand", description="B2B Tooling")
    proj.products.append(Product(name="Analyzer", description="Code analysis"))
    proj.internal_links.append(InternalLink(url="/analyzer", title="Tool Page"))
    service.update_project(proj)

    # Read back from fresh service instance
    reloaded_service = ProjectService(repo=ProjectRepository(data_dir=str(tmp_path / "projects")))
    fetched = reloaded_service.get_project(proj.id)
    assert fetched is not None
    assert fetched.name == "SaaS Brand"
    assert len(fetched.products) == 1
    assert len(fetched.internal_links) == 1


def test_desktop_application_startup():
    """Verify desktop application widgets and main window initialize cleanly offscreen."""
    from PySide6.QtWidgets import QApplication
    from app.ui.main_window import MainWindow

    app = QApplication.instance() or QApplication(["test", "-platform", "offscreen"])
    assert app is not None
    window = MainWindow()
    assert window.windowTitle().startswith("BlogForge")
    assert window.stack.count() == 5
    # Switch through all tabs
    for idx in range(5):
        window.switch_tab(idx)
        assert window.stack.currentIndex() == idx
    window.close()
