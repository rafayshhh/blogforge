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
