"""Comprehensive End-to-End user workflows testing realistic user journeys in isolated environments."""

import os
import json
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication

from app.models.article import Article, ArticleSection, FAQItem
from app.projects.models import Project, Product
from app.projects.repository import ProjectRepository
from app.projects.service import ProjectService
from app.generation.models import GenerationRequest, ArticleOutline, OutlineSection, FAQData
from app.generation.pipeline import GenerationPipeline
from app.export.markdown import export_markdown
from app.export.html import export_html
from app.export.json import export_json
from app.integrations.nextjs.exporter import NextJSExporter
from app.providers.gemini import GeminiProvider
from app.core.exceptions import ProviderAuthenticationError
from app.ui.main_window import MainWindow


def get_qapp():
    """Ensure headless QApplication is initialized."""
    app = QApplication.instance()
    if not app:
        app = QApplication(["test_workflow", "-platform", "offscreen"])
    app.processEvents()
    return app


def test_workflow_1_project_lifecycle_persistence(tmp_path, monkeypatch):
    """WORKFLOW 1: Launch application → Create project → Save project → Close → Reopen → Verify persistence."""
    monkeypatch.chdir(tmp_path)
    get_qapp()

    # Step 1: Launch app
    window1 = MainWindow()
    p_widget1 = window1.projects_view

    # Step 2 & 3: Create & save project
    p_widget1.name_input.setText("E-Commerce Brand")
    p_widget1.desc_input.setPlainText("Online storefront")
    p_widget1.brand_tone_input.setText("Persuasive")
    p_widget1.save_project()
    saved_pid = p_widget1.current_project_id
    assert saved_pid is not None

    # Step 4: Close application
    window1.close()

    # Step 5 & 6: Reopen and verify persistence
    window2 = MainWindow()
    p_widget2 = window2.projects_view
    reloaded_proj = p_widget2.service.get_project(saved_pid)

    assert reloaded_proj is not None
    assert reloaded_proj.name == "E-Commerce Brand"
    assert reloaded_proj.brand_profile.tone == "Persuasive"
    window2.close()


def test_workflow_2_content_generation_end_to_end(tmp_path, monkeypatch):
    """WORKFLOW 2: Create project → Configure settings → Enter topic → Generate outline → Review → Generate → Save."""
    monkeypatch.chdir(tmp_path)

    repo = ProjectRepository(data_dir=str(tmp_path / "data" / "projects"))
    service = ProjectService(repo=repo)

    # 1. Create project with brand rules
    proj = service.create_project(name="DevOps Central", description="Cloud infrastructure guides")
    proj.products.append(Product(name="KubeDeploy", description="Automated Kubernetes deployments"))
    service.update_project(proj)

    # 2. Mock Gemini AI
    mock_ai = MagicMock()
    mock_outline = ArticleOutline(
        title="Automating Kubernetes in 2026",
        slug="automating-kubernetes-2026",
        description="A practical cloud guide",
        sections=[
            OutlineSection(id="s1", heading="Cluster Setup", level=2, key_points=["Infra as Code"]),
            OutlineSection(id="s2", heading="Deployment Pipelines", level=2, key_points=["CI/CD"])
        ]
    )
    mock_ai.generate_structured.side_effect = [
        mock_outline,
        FAQData(faqs=[FAQItem(question="Is this production ready?", answer="Yes, verified at scale.")])
    ]
    mock_ai.generate.side_effect = [
        MagicMock(text="Cluster setup details using KubeDeploy."),
        MagicMock(text="Deployment pipelines automated with GitHub Actions.")
    ]

    pipeline = GenerationPipeline(mock_ai)
    req = GenerationRequest(topic="Automating Kubernetes in 2026", project_id=proj.id)

    # 3. Generate and review outline
    outline = pipeline.generate_outline(req)
    assert outline.title == "Automating Kubernetes in 2026"
    assert len(outline.sections) == 2

    # 4. Generate article
    article = pipeline.generate_article(req, outline)
    assert len(article.sections) == 2
    assert "Cluster setup details" in article.content

    # 5. Finalize and save
    final_article = pipeline.finalize_article(article, req)
    assert len(final_article.faq) == 1
    assert os.path.exists(f"data/articles/{pipeline.run_id}.json")


def test_workflow_3_article_editor_and_word_count(tmp_path, monkeypatch):
    """WORKFLOW 3: Open existing article → Edit content → Preview article → Verify word count → Save changes."""
    monkeypatch.chdir(tmp_path)
    get_qapp()

    articles_dir = tmp_path / "data" / "articles"
    articles_dir.mkdir(parents=True)

    art = Article(
        title="SEO Optimization Guide",
        slug="seo-guide",
        content="# SEO Guide\n\nInitial short content.",
        sections=[ArticleSection(id="1", heading="Intro", level=2, content="Initial short content.")]
    )
    file_path = articles_dir / "article_workflow3.json"
    file_path.write_text(art.model_dump_json(indent=2), encoding="utf-8")

    window = MainWindow()
    art_view = window.articles_view
    art_view.articles_dir = str(articles_dir)
    art_view.refresh_articles()

    # Select article
    art_view.article_list.setCurrentRow(0)
    assert art_view.current_article.title == "SEO Optimization Guide"

    # Edit content
    expanded_content = (
        "# SEO Optimization Guide\n\n"
        "Comprehensive techniques to rank on modern search engines. " * 30
    )
    art_view.md_editor.setPlainText(expanded_content)

    # Verify preview and word count update
    assert "Comprehensive techniques" in art_view.html_preview.toPlainText()
    expected_words = len(expanded_content.split())
    assert str(expected_words) in art_view.meta_label.text()

    # Save changes
    with patch("PySide6.QtWidgets.QMessageBox.information"):
        art_view.save_article_changes()

    # Verify persistence
    with open(file_path, "r", encoding="utf-8") as f:
        reloaded = Article.model_validate_json(f.read())
        assert len(reloaded.content.split()) == expected_words

    window.close()


def test_workflow_4_multi_format_export(tmp_path):
    """WORKFLOW 4: Create article → Export Markdown → Export HTML → Export JSON → Verify files."""
    article = Article(
        title="Multi-Format Publishing",
        slug="multi-format-publishing",
        description="Testing Markdown, HTML, and JSON outputs.",
        sections=[
            ArticleSection(id="s1", heading="Architecture", level=2, content="Paragraph 1\n\nParagraph 2")
        ],
        faq=[FAQItem(question="Supported formats?", answer="Markdown, HTML, JSON, and Next.js.")]
    )

    out_dir = tmp_path / "exports"
    out_dir.mkdir()

    # 1. Export Markdown
    md_file = out_dir / "output.md"
    md_file.write_text(export_markdown(article), encoding="utf-8")
    assert "# Multi-Format Publishing" in md_file.read_text(encoding="utf-8")

    # 2. Export HTML
    html_file = out_dir / "output.html"
    html_file.write_text(export_html(article), encoding="utf-8")
    html_content = html_file.read_text(encoding="utf-8")
    assert "<h1>Multi-Format Publishing</h1>" in html_content
    assert "<dt>Supported formats?</dt>" in html_content

    # 3. Export JSON
    json_file = out_dir / "output.json"
    json_file.write_text(export_json(article), encoding="utf-8")
    loaded = json.loads(json_file.read_text(encoding="utf-8"))
    assert loaded["title"] == "Multi-Format Publishing"
    assert len(loaded["sections"]) == 1


def test_workflow_5_nextjs_integration_pipeline(tmp_path):
    """WORKFLOW 5: Configure Next.js integration → Export article → Verify expected output structure."""
    nextjs_app_dir = tmp_path / "my_nextjs_app"
    content_dir = nextjs_app_dir / "content" / "posts"

    project = Project(
        name="NextJS Production",
        nextjs_integration={
            "enabled": True,
            "project_directory": str(nextjs_app_dir),
            "content_directory": str(content_dir),
            "export_format": "MARKDOWN"
        }
    )

    article = Article(
        title="Next.js Static Site Generation",
        slug="nextjs-ssg-guide",
        content="# Next.js SSG\n\nFast static sites.",
        sections=[ArticleSection(id="s1", heading="SSG Overview", level=2, content="Fast static sites.")]
    )

    exporter = NextJSExporter()
    assert exporter.test_connection(project) is True

    exported_path = exporter.export(article, project)
    assert os.path.exists(exported_path)
    assert exported_path.endswith("nextjs-ssg-guide.md")

    with open(exported_path, "r", encoding="utf-8") as f:
        file_body = f.read()
        assert "# Next.js Static Site Generation" in file_body


@patch("time.sleep", return_value=None)
def test_workflow_6_error_recovery_and_retry(mock_sleep):
    """WORKFLOW 6: Start generation → Simulate provider failure → Verify error handling → Retry → Recovery."""
    from google.genai.errors import APIError
    provider = GeminiProvider(api_key="TEST_KEY")

    # Simulate rate limit failure on first attempt, recovery on second attempt
    transient_err = APIError(429, {"message": "Rate limit reached"})
    mock_success_resp = MagicMock()
    mock_success_resp.text = "Recovered content after transient error."
    mock_success_resp.usage_metadata = None

    provider.client.models.generate_content = MagicMock(
        side_effect=[transient_err, mock_success_resp]
    )

    resp = provider.generate("Resilient prompt")
    assert resp.text == "Recovered content after transient error."
    assert provider.client.models.generate_content.call_count == 2


def test_workflow_7_cancellation_and_responsiveness(tmp_path, monkeypatch):
    """WORKFLOW 7: Start generation → Cancel operation → Verify clean cancellation and responsiveness."""
    monkeypatch.chdir(tmp_path)
    mock_ai = MagicMock()
    mock_ai.generate.return_value = MagicMock(text="Paragraph")

    pipeline = GenerationPipeline(mock_ai)
    req = GenerationRequest(topic="Long Running Generation")
    outline = ArticleOutline(
        title="Long Topic",
        slug="long-topic",
        sections=[OutlineSection(id=str(i), heading=f"Sec {i}", level=2) for i in range(10)]
    )

    # Cancel immediately
    pipeline.cancel()
    article = pipeline.generate_article(req, outline)

    # Verify no sections generated and no hang
    assert len(article.sections) == 0
    assert pipeline.is_cancelled is True


def test_workflow_8_missing_configuration_graceful_handling(monkeypatch):
    """WORKFLOW 8: Open application with missing configuration → Verify useful error handling."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    # Initializing provider without key should provide clear guidance
    try:
        GeminiProvider(api_key=None)
        assert False, "Should have raised ProviderAuthenticationError"
    except ProviderAuthenticationError as e:
        assert "Gemini API key is not configured" in str(e)


def test_workflow_9_corrupted_local_data_isolation(tmp_path):
    """WORKFLOW 9: Open application with corrupted local data → Verify safe failure and data preservation."""
    projects_dir = tmp_path / "data" / "projects"
    projects_dir.mkdir(parents=True)

    # Create a legitimate project
    repo = ProjectRepository(data_dir=str(projects_dir))
    valid_proj = Project(name="Good Project", description="Intact data")
    repo.save(valid_proj)

    # Introduce a completely corrupted file and an empty file
    (projects_dir / "corrupted_bad.json").write_text("<<< NOT JSON >>>", encoding="utf-8")
    (projects_dir / "empty.json").write_text("", encoding="utf-8")

    # Reopening repository should isolate valid project and ignore corrupted files
    fresh_repo = ProjectRepository(data_dir=str(projects_dir))
    projs = fresh_repo.list_all()

    assert len(projs) == 1
    assert projs[0].name == "Good Project"
    # Ensure good project file is untouched
    assert fresh_repo.get(valid_proj.id) is not None


def test_workflow_10_multi_project_data_isolation(tmp_path):
    """WORKFLOW 10: Create multiple projects and articles → Switch between projects → Verify data isolation."""
    repo = ProjectRepository(data_dir=str(tmp_path / "data" / "projects"))
    service = ProjectService(repo=repo)

    # Create Project A
    p_a = service.create_project(name="Project A", description="Brand A")
    p_a.products.append(Product(name="Product A1", description="Description A1"))
    service.update_project(p_a)

    # Create Project B
    p_b = service.create_project(name="Project B", description="Brand B")
    p_b.products.append(Product(name="Product B1", description="Description B1"))
    service.update_project(p_b)

    # Verify isolation
    loaded_a = service.get_project(p_a.id)
    loaded_b = service.get_project(p_b.id)

    assert loaded_a.name == "Project A"
    assert [p.name for p in loaded_a.products] == ["Product A1"]

    assert loaded_b.name == "Project B"
    assert [p.name for p in loaded_b.products] == ["Product B1"]
    assert loaded_a.id != loaded_b.id
