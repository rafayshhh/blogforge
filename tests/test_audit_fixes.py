"""Tests validating the bug fixes, UI synchronization, and persistence improvements."""

import os
from PySide6.QtWidgets import QApplication
from app.models.article import Article
from app.research.models import ResearchRun, ContentStrategy
from app.ui.dashboard import DashboardWidget
from app.ui.research import ResearchWidget
from app.ui.articles import ArticlesWidget


# Ensure a headless QApp exists for widget instantiation
app = QApplication.instance() or QApplication([])


def test_dashboard_resolves_project_names(tmp_path):
    """Verify that DashboardWidget resolves project UUIDs to friendly names instead of raw IDs."""
    dash = DashboardWidget()
    project_lookup = {
        "proj_12345": "Engineering Insights",
        "proj_67890": "Design System"
    }

    # Verify lookup logic and widget state
    dash._project_lookup = project_lookup
    assert dash._project_lookup.get("proj_12345") == "Engineering Insights"
    assert dash._project_lookup.get("proj_67890") == "Design System"
    assert dash._project_lookup.get("unknown_uuid", "Default Workspace") == "Default Workspace"


def test_dashboard_open_article_signal():
    """Verify DashboardWidget emits open_article_requested with correct slug."""
    dash = DashboardWidget()
    captured_slugs = []
    dash.open_article_requested.connect(lambda slug: captured_slugs.append(slug))

    # Populate a mock row
    dash.doc_table.setRowCount(1)
    from PySide6.QtWidgets import QTableWidgetItem
    from PySide6.QtCore import Qt

    title_item = QTableWidgetItem("My Article")
    title_item.setData(int(Qt.ItemDataRole.UserRole), "my-article-slug")
    dash.doc_table.setItem(0, 0, title_item)

    # Click col 4 (Open action)
    dash._on_doc_cell_clicked(0, 4)
    assert captured_slugs == ["my-article-slug"]


def test_research_widget_persistence_and_loading(tmp_path):
    """Verify ResearchWidget saves and reloads ResearchRun records."""
    res_widget = ResearchWidget.__new__(ResearchWidget)
    res_widget.research_dir = str(tmp_path / "research")
    os.makedirs(res_widget.research_dir, exist_ok=True)

    sample_run = ResearchRun(
        topic="Event-Driven Microservices",
        queries=["microservices event mesh", "kafka latency benchmarks"],
        search_landscape=[],
        strategy=ContentStrategy(
            primary_intent="Architectural Guide",
            audience="Senior Engineers",
            primary_topic="Microservices",
            recommended_angle="Pragmatic trade-offs"
        ),
        created_at="2026-11-19T12:00:00"
    )

    res_widget.save_research_run(sample_run)
    saved_files = os.listdir(res_widget.research_dir)
    assert len(saved_files) == 1
    assert saved_files[0].endswith(".json")


def test_article_editor_section_sync():
    """Verify that _sync_sections_from_content correctly synchronizes sections and titles."""
    widget = ArticlesWidget.__new__(ArticlesWidget)
    art = Article(title="Old", slug="test", content="")

    content = (
        "# High-Throughput Pipelines\n\n"
        "Lead paragraph explaining the pipeline.\n\n"
        "## Ingestion Layer\n"
        "Kafka brokers buffer streaming traffic.\n\n"
        "## Processing Layer\n"
        "Flink cluster computes aggregations."
    )

    widget._sync_sections_from_content(art, content)
    assert art.title == "High-Throughput Pipelines"
    assert len(art.sections) == 3
    assert art.sections[0].heading == "Introduction"
    assert "Lead paragraph" in art.sections[0].content
    assert art.sections[1].heading == "Ingestion Layer"
    assert "Kafka brokers" in art.sections[1].content
    assert art.sections[2].heading == "Processing Layer"
    assert "Flink cluster" in art.sections[2].content


def test_dashboard_chronological_and_unassigned_labels(tmp_path, monkeypatch):
    """Verify that DashboardWidget chronologically aggregates articles and drafts without raw UUID leaks."""
    monkeypatch.chdir(tmp_path)
    os.makedirs("data/articles", exist_ok=True)
    os.makedirs("data/generation", exist_ok=True)

    import time
    # Create an article with unknown project UUID
    art_path = "data/articles/art1.json"
    art_payload = (
        '{"title": "Published Post", "slug": "published-post", "content": "One two three", '
        '"project_id": "9be51c82-e18c-44f2-91d0-b6fef07b6204"}'
    )
    with open(art_path, "w", encoding="utf-8") as f:
        f.write(art_payload)

    time.sleep(0.05)
    # Create a draft
    draft_path = "data/generation/draft1.json"
    with open(draft_path, "w", encoding="utf-8") as f:
        f.write('{"title": "WIP Draft", "slug": "wip-draft", "content": "Drafting now", "project_id": null}')

    # Create a partial file which should be ignored
    partial_path = "data/generation/gen_partial.json"
    with open(partial_path, "w", encoding="utf-8") as f:
        f.write('{"title": "Broken Partial"}')

    dash = DashboardWidget()
    dash.load_recent_articles(project_lookup={})

    # Should have 2 rows (art1 and draft1), partial ignored
    assert dash.doc_table.rowCount() == 2
    # Row 0 should be the most recent (draft1)
    row0_title = dash.doc_table.item(0, 0).text()
    assert row0_title == "WIP Draft"
    # Row 1 should be art1 with Unassigned project label
    row1_proj = dash.doc_table.item(1, 3).text()
    assert row1_proj == "Unassigned"


def test_articles_widget_action_states():
    """Verify ArticlesWidget correctly toggles action button states when an article is loaded or cleared."""
    widget = ArticlesWidget.__new__(ArticlesWidget)
    from PySide6.QtWidgets import QPushButton, QFrame, QTextEdit
    widget.btn_save = QPushButton()
    widget.btn_export = QPushButton()
    widget.btn_del = QPushButton()
    widget.toolbar_strip = QFrame()
    widget.md_editor = QTextEdit()

    widget.current_article = None
    widget._update_action_states()
    assert not widget.btn_save.isEnabled()
    assert not widget.btn_export.isEnabled()
    assert not widget.btn_del.isEnabled()
    assert not widget.toolbar_strip.isEnabled()
    assert widget.md_editor.isReadOnly()

    widget.current_article = Article(title="Active", slug="active", content="Hello")
    widget._update_action_states()
    assert widget.btn_save.isEnabled()
    assert widget.btn_export.isEnabled()
    assert widget.btn_del.isEnabled()
    assert widget.toolbar_strip.isEnabled()
    assert not widget.md_editor.isReadOnly()
