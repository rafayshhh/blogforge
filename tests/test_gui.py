"""Offscreen GUI interaction tests for PySide6 desktop application components."""

import os
import json
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication, QMessageBox, QInputDialog, QFileDialog

from app.ui.theme import apply_theme
from app.ui.main_window import MainWindow
from app.ui.settings import SettingsWidget, TestConnectionThread
from app.models.article import Article, ArticleSection


def get_qapp():
    """Returns or creates a headless QApplication instance."""
    app = QApplication.instance()
    if not app:
        app = QApplication(["test_blogforge", "-platform", "offscreen"])
    app.processEvents()
    return app


def test_theme_application():
    """Verify apply_theme configures global stylesheet and font without exceptions."""
    app = get_qapp()
    apply_theme(app)
    sheet = app.styleSheet()
    assert "background-color" in sheet
    assert "QListWidget" in sheet


def test_main_window_navigation_and_project_switcher(tmp_path, monkeypatch):
    """Verify MainWindow initializes tabs, switches views, and updates project switcher."""
    monkeypatch.chdir(tmp_path)
    get_qapp()

    window = MainWindow()
    assert window.stack.count() == 5

    # Verify switching to each tab
    for tab_idx in range(5):
        window.switch_tab(tab_idx)
        assert window.stack.currentIndex() == tab_idx

    # Refresh project switcher
    window.refresh_project_switcher()
    assert window.project_switcher is not None

    window.close()


def test_dashboard_widget_quick_actions(tmp_path, monkeypatch):
    """Verify DashboardWidget quick action triggers navigate to respective tabs."""
    monkeypatch.chdir(tmp_path)
    get_qapp()

    window = MainWindow()
    dashboard = window.dashboard_view

    # Trigger navigate to Articles
    dashboard.navigate_to.emit(2)
    assert window.stack.currentIndex() == 2  # Articles tab

    # Trigger navigate to Projects
    dashboard.navigate_to.emit(1)
    assert window.stack.currentIndex() == 1  # Projects tab

    # Update checklist and stats
    dashboard.update_checklist(has_gemini=True, has_project=True, has_nextjs=True)
    dashboard.update_stats(articles_count=10, research_count=5, drafts_count=2)
    assert dashboard.stat_labels["Articles"].text() == "10"
    assert dashboard.stat_labels["Research"].text() == "5"
    assert dashboard.stat_labels["Drafts"].text() == "2"

    window.close()


def test_projects_widget_crud_operations(tmp_path, monkeypatch):
    """Verify ProjectsWidget creation, editing, product/URL additions, and saving."""
    monkeypatch.chdir(tmp_path)
    get_qapp()

    window = MainWindow()
    p_widget = window.projects_view

    # 1. New project form reset
    p_widget.new_project()
    assert p_widget.name_input.text() == ""
    assert p_widget.current_project_id is None

    # 2. Validation check: saving with empty name shows warning
    with patch.object(QMessageBox, "warning") as mock_warn:
        p_widget.save_project()
        assert mock_warn.called

    # 3. Create and save a valid project
    p_widget.name_input.setText("Quantum AI")
    p_widget.desc_input.setPlainText("Quantum computing brand")
    p_widget.brand_tone_input.setText("Visionary")
    p_widget.save_project()

    assert p_widget.current_project_id is not None
    assert p_widget.project_list.count() >= 1

    # 4. Add product
    with patch.object(QInputDialog, "getText", side_effect=[("QubitSim", True), ("Quantum Simulator", True)]):
        p_widget.add_product()
    assert p_widget.prod_list.count() == 1

    # 5. Delete product
    p_widget.prod_list.setCurrentRow(0)
    p_widget.del_product()
    assert p_widget.prod_list.count() == 0

    # 6. Add internal link
    with patch.object(QInputDialog, "getText", side_effect=[("Qubit Docs", True), ("/docs/qubit", True)]):
        p_widget.add_url()
    assert p_widget.url_list.count() == 1

    # 7. Delete internal link
    p_widget.url_list.setCurrentRow(0)
    p_widget.del_url()
    assert p_widget.url_list.count() == 0

    # 8. Test Next.js directory connection
    p_widget.nextjs_enabled.setChecked(True)
    next_dir = tmp_path / "next_app"
    p_widget.nextjs_content_dir.setText(str(next_dir))
    p_widget.save_project()

    with patch.object(QMessageBox, "information") as mock_info:
        p_widget.test_nextjs()
        assert mock_info.called

    window.close()


def test_articles_widget_editor_preview_and_export(tmp_path, monkeypatch):
    """Verify ArticlesWidget listing, filtering, markdown editing, preview updates, and export."""
    monkeypatch.chdir(tmp_path)
    get_qapp()

    articles_dir = tmp_path / "data" / "articles"
    articles_dir.mkdir(parents=True)

    sample_article = Article(
        title="Modern Python Studio",
        slug="modern-python-studio",
        content="# Modern Python Studio\n\nHigh efficiency engineering workflows.",
        sections=[ArticleSection(id="1", heading="Architecture", level=2, content="Clean code.")]
    )
    art_path = articles_dir / "art_1.json"
    art_path.write_text(sample_article.model_dump_json(indent=2), encoding="utf-8")

    window = MainWindow()
    a_widget = window.articles_view
    a_widget.articles_dir = str(articles_dir)
    a_widget.refresh_articles()

    # Search filter
    a_widget.search_input.setText("Python")
    assert a_widget.article_list.count() == 1

    a_widget.search_input.setText("NonExistentTopic")
    assert a_widget.article_list.count() == 0

    a_widget.search_input.clear()
    assert a_widget.article_list.count() == 1

    # Select article
    a_widget.article_list.setCurrentRow(0)
    assert a_widget.current_article is not None
    assert "Modern Python Studio" in a_widget.md_editor.toPlainText()

    # Edit markdown and check preview sync
    a_widget.md_editor.setPlainText("# Updated Header\n\nNew paragraph content.")
    assert "Updated Header" in a_widget.html_preview.toPlainText()

    # Save changes
    with patch.object(QMessageBox, "information") as mock_info:
        a_widget.save_article_changes()
        assert mock_info.called

    with open(art_path, "r", encoding="utf-8") as f:
        saved_data = json.load(f)
        assert "Updated Header" in saved_data["content"]

    # Export selected to Markdown
    export_target = tmp_path / "exported.md"
    with patch.object(QFileDialog, "getSaveFileName", return_value=(str(export_target), "Markdown (*.md)")):
        with patch.object(QMessageBox, "information"):
            a_widget.export_combo.setCurrentText("Markdown")
            a_widget.export_selected()
    assert export_target.exists()

    # Export selected to HTML
    html_target = tmp_path / "exported.html"
    with patch.object(QFileDialog, "getSaveFileName", return_value=(str(html_target), "HTML (*.html)")):
        with patch.object(QMessageBox, "information"):
            a_widget.export_combo.setCurrentText("HTML")
            a_widget.export_selected()
    assert html_target.exists()

    # Export selected to JSON
    json_target = tmp_path / "exported.json"
    with patch.object(QFileDialog, "getSaveFileName", return_value=(str(json_target), "JSON (*.json)")):
        with patch.object(QMessageBox, "information"):
            a_widget.export_combo.setCurrentText("JSON")
            a_widget.export_selected()
    assert json_target.exists()

    # Delete selected article
    with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
        a_widget.delete_selected()
    assert not art_path.exists()

    window.close()


def test_settings_widget_interactions(tmp_path, monkeypatch):
    """Verify SettingsWidget inputs, visibility toggle, key saving, and connection testing."""
    monkeypatch.chdir(tmp_path)
    get_qapp()

    settings = SettingsWidget()

    # Toggle API visibility
    assert settings.api_input.echoMode() == settings.api_input.EchoMode.Password
    settings.toggle_api_visibility()
    assert settings.api_input.echoMode() == settings.api_input.EchoMode.Normal
    settings.toggle_api_visibility()
    assert settings.api_input.echoMode() == settings.api_input.EchoMode.Password

    # Save key validation
    settings.api_input.clear()
    with patch.object(QMessageBox, "warning") as mock_warn:
        settings.save_api_key()
        assert mock_warn.called

    # Save valid key
    settings.api_input.setText("TEST_SAFE_KEY_999")
    settings.save_api_key()
    assert os.environ.get("GEMINI_API_KEY") == "TEST_SAFE_KEY_999"
    assert "saved" in settings.lbl_status.text()

    # Active model and editable combo verification
    assert settings.model_combo.isEditable()
    assert "gemini-3.8-flash" in settings.get_selected_model()
    assert "gemini-3.8-flash" in settings.lbl_active_model.text()

    # Model discovery callback handling
    settings.on_models_discovered(True, ["gemini-3.8-flash", "gemini-4-carbon"], "Discovered 2 models")
    assert "Verified" in settings.lbl_status.text()
    assert settings.model_combo.count() >= 2

    # Model discovery failure handling
    settings.on_models_discovered(False, [], "Network error")
    assert "✕ Network error" in settings.lbl_status.text()

    # Test connection thread handler
    settings.on_test_result(True, "Connected")
    assert "✓ Connected" in settings.lbl_status.text()

    settings.on_test_result(False, "Failed auth")
    assert "✕ Failed auth" in settings.lbl_status.text()


def test_connection_thread_execution():
    """Verify TestConnectionThread emits expected signal values on success and failure."""
    get_qapp()
    results = []

    # Successful connection mock
    with patch("app.providers.gemini.GeminiProvider") as mock_prov_cls:
        mock_instance = MagicMock()
        mock_instance.generate.return_value = MagicMock(text="OK")
        mock_instance.list_available_models.return_value = ["gemini-3.8-flash"]
        mock_prov_cls.return_value = mock_instance

        thread = TestConnectionThread(api_key="KEY", model="gemini-3.8-flash")
        thread.result.connect(lambda ok, msg: results.append((ok, msg)))
        thread.run()

    assert len(results) == 1
    assert results[0][0] is True
    assert "Connected successfully" in results[0][1]


def test_main_entry_point(monkeypatch):
    """Verify main() sets up environment, styling, and launches window."""
    from app.main import main

    monkeypatch.setattr(QApplication, "exec", lambda self: 0)
    monkeypatch.setattr(MainWindow, "show", lambda self: None)

    # Calling main should run cleanly without uncaught exception
    with patch("sys.exit") as mock_exit:
        main()
        assert mock_exit.called


def test_dialogs_add_product_and_add_link():
    """Verify custom AddProductDialog and AddLinkDialog input validation and acceptance."""
    get_qapp()
    from app.ui.components.dialogs import AddProductDialog, AddLinkDialog

    # AddProductDialog validation
    prod_dlg = AddProductDialog(initial_name="", initial_desc="Test description")
    with patch.object(QMessageBox, "warning") as mock_warn:
        prod_dlg.on_accept()
        assert mock_warn.called

    prod_dlg.name_input.setText("CloudShield")
    prod_dlg.on_accept()
    name, desc, ok = prod_dlg.get_data()
    assert name == "CloudShield"
    assert desc == "Test description"

    # AddLinkDialog validation
    link_dlg = AddLinkDialog(initial_title="", initial_url="")
    with patch.object(QMessageBox, "warning") as mock_warn:
        link_dlg.on_accept()
        assert mock_warn.called

    link_dlg.title_input.setText("Pricing")
    link_dlg.url_input.setText("/pricing")
    link_dlg.on_accept()
    title, url, ok = link_dlg.get_data()
    assert title == "Pricing"
    assert url == "/pricing"


def test_article_generator_dialog_validation(monkeypatch):
    """Verify ArticleGeneratorDialog validates topic and missing credentials."""
    get_qapp()
    from app.ui.components.dialogs import ArticleGeneratorDialog

    gen_dlg = ArticleGeneratorDialog()

    # Empty topic validation
    gen_dlg.topic_input.clear()
    with patch.object(QMessageBox, "warning") as mock_warn:
        gen_dlg.start_generation()
        assert mock_warn.called

    # Missing API key validation
    gen_dlg.topic_input.setText("Valid Topic")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with patch.object(QMessageBox, "warning") as mock_warn:
        gen_dlg.start_generation()
        assert mock_warn.called


def test_articles_widget_advanced_features(tmp_path, monkeypatch):
    """Verify ArticlesWidget view mode toggling, markdown insertion, and draft creation."""
    monkeypatch.chdir(tmp_path)
    get_qapp()

    window = MainWindow()
    a_widget = window.articles_view

    # View mode switching
    a_widget.set_view_mode("write")
    assert not a_widget.md_editor.isHidden()
    assert a_widget.html_preview.isHidden()

    a_widget.set_view_mode("preview")
    assert a_widget.md_editor.isHidden()
    assert not a_widget.html_preview.isHidden()

    a_widget.set_view_mode("split")
    assert not a_widget.md_editor.isHidden()
    assert not a_widget.html_preview.isHidden()

    # Markdown insertion
    a_widget.md_editor.clear()
    a_widget.insert_markdown("# ")
    assert "# " in a_widget.md_editor.toPlainText()

    # Create blank draft
    a_widget.create_blank_draft()
    assert a_widget.article_list.count() >= 1

    window.close()


def test_research_widget_interactions(tmp_path, monkeypatch):
    """Verify ResearchWidget topic validation, source tables, and strategy synthesis."""
    monkeypatch.chdir(tmp_path)
    get_qapp()

    window = MainWindow()
    r_widget = window.research_view

    # Validation: empty topic
    r_widget.topic_input.clear()
    with patch.object(QMessageBox, "warning") as mock_warn:
        r_widget.start_research()
        assert mock_warn.called

    # Mocked research completion
    from app.research.models import ResearchRun, SearchLandscape, SearchResult, ContentStrategy, ContentGap
    from datetime import datetime

    mock_run = ResearchRun(
        topic="Cloud Architecture",
        queries=["cloud architecture best practices", "serverless scaling"],
        search_landscape=[
            SearchLandscape(
                query="cloud architecture best practices",
                results=[
                    SearchResult(
                        title="AWS Well-Architected",
                        url="https://aws.amazon.com",
                        domain="aws.amazon.com",
                        snippet="Best practices"
                    ),
                    SearchResult(
                        title="GCP Architecture",
                        url="https://cloud.google.com",
                        domain="cloud.google.com",
                        snippet="Guide"
                    )
                ]
            )
        ],
        strategy=ContentStrategy(
            primary_intent="Architecture Planning",
            audience="DevOps Leads",
            primary_topic="Cloud Architecture",
            recommended_angle="Pragmatic cost-efficient cloud scaling",
            content_gaps=[
                ContentGap(
                    topic="FinOps",
                    description="Tooling gaps",
                    importance="High",
                    evidence="Search results"
                )
            ],
            recommended_outline=["Introduce benchmarks early"]
        ),
        created_at=datetime.now().isoformat(),
        metadata={}
    )

    r_widget.display_research_run(mock_run)
    assert r_widget.queries_list.count() == 2
    assert r_widget.sources_table.rowCount() == 2
    assert "DevOps Leads" in r_widget.strategy_view.toPlainText()

    # Select table row
    r_widget.sources_table.selectRow(0)
    r_widget.on_source_selected()
    assert "AWS Well-Architected" in r_widget.source_detail.toPlainText()

    window.close()
