from app.models.article import Article, ArticleSection, FAQItem
from app.export.markdown import export_markdown
from app.export.html import export_html
from app.content.context import FilteredProjectContext
from app.projects.models import Project


def test_export_markdown_with_sections():
    article = Article(
        title="Test Title",
        slug="test-title",
        description="A short desc",
        sections=[
            ArticleSection(id="1", heading="Intro", level=2, content="This is intro."),
            ArticleSection(id="2", heading="Deep Dive", level=10, content="Deep content.")  # clamped level
        ],
        faq=[FAQItem(question="Q1?", answer="A1.")]
    )
    md = export_markdown(article)
    assert "# Test Title" in md
    assert "> A short desc" in md
    assert "## Intro" in md
    assert "###### Deep Dive" in md  # clamped from 10 to 6
    assert "## FAQ" in md
    assert "**Q1?**" in md


def test_export_markdown_fallback_content():
    article = Article(
        title="No Sections",
        slug="no-sections",
        content="Direct markdown content here without sections."
    )
    md = export_markdown(article)
    assert "Direct markdown content here without sections." in md


def test_export_html_with_sections_and_fallback():
    article = Article(
        title="HTML Test",
        slug="html-test",
        description="Desc",
        sections=[
            # clamped to h1
            ArticleSection(id="s1", heading="Section 1", level=0, content="Content paragraph 1\n\nContent paragraph 2")
        ],
        faq=[FAQItem(question="Why?", answer="Because.")]
    )
    html = export_html(article)
    assert "<h1>HTML Test</h1>" in html
    assert "<p class='description'>Desc</p>" in html
    assert "<h1>Section 1</h1>" in html
    assert "<p>Content paragraph 1</p>" in html
    assert "<dt>Why?</dt>" in html
    assert "<dd>Because.</dd>" in html


def test_filtered_project_context_none_topic():
    p = Project(name="Test Project")
    ctx = FilteredProjectContext(p, None)
    assert ctx.topic == ""
    prompt_str = ctx.format_for_prompt()
    assert "Brand:" in prompt_str


def test_editor_sync_sections_and_export():
    """Verify that editing manuscript content and re-syncing updates sections and exporters."""
    from app.ui.articles import ArticlesWidget
    article = Article(
        title="Initial Title",
        slug="sync-test",
        content="# Initial Title\n\n## Old Section\nOld content",
        sections=[ArticleSection(id="1", heading="Old Section", level=2, content="Old content")]
    )

    # Simulated user edit
    updated_markdown = (
        "# Revised Architecture Title\n\n"
        "## Architecture Foundations\n"
        "Updated high-throughput consensus explanation.\n\n"
        "### Cluster Topology\n"
        "Three-node RAFT replication.\n\n"
        "## Performance Metrics\n"
        "100k writes/sec benchmark."
    )

    # Use widget sync method without full Qt app
    widget = ArticlesWidget.__new__(ArticlesWidget)
    widget._sync_sections_from_content(article, updated_markdown)

    assert article.title == "Revised Architecture Title"
    assert len(article.sections) == 3
    assert article.sections[0].heading == "Architecture Foundations"
    assert "Updated high-throughput" in article.sections[0].content
    assert article.sections[1].heading == "Cluster Topology"
    assert article.sections[1].level == 3
    assert article.sections[2].heading == "Performance Metrics"

    # Verify exporters respect updated sections
    md_output = export_markdown(article)
    assert "# Revised Architecture Title" in md_output
    assert "## Architecture Foundations" in md_output
    assert "### Cluster Topology" in md_output
    assert "## Performance Metrics" in md_output

    html_output = export_html(article)
    assert "<h1>Revised Architecture Title</h1>" in html_output
    assert "<h2>Architecture Foundations</h2>" in html_output
    assert "<h3>Cluster Topology</h3>" in html_output
