"""Extended tests for Markdown, HTML, JSON, and Next.js content exporters."""

import os
import json
import pytest
from app.models.article import Article, ArticleSection, FAQItem
from app.export.markdown import export_markdown
from app.export.html import export_html
from app.export.json import export_json
from app.integrations.nextjs.exporter import NextJSExporter
from app.projects.models import Project


def test_markdown_exporter_edge_cases():
    """Verify Markdown exporter handles boundary heading levels, empty fields, and formatting."""
    article = Article(
        title="Edge Case Markdown",
        slug="edge-case-md",
        description="",  # Empty description should omit blockquote
        sections=[
            ArticleSection(id="1", heading="Level Zero", level=0, content="Content 0"),
            ArticleSection(id="2", heading="Level One", level=1, content="Content 1"),
            ArticleSection(id="3", heading="Level Seven", level=7, content="Content 7"),
        ],
        faq=[]  # Empty FAQ should omit FAQ section
    )

    md = export_markdown(article)
    assert "# Edge Case Markdown" in md
    assert "> " not in md  # No blockquote when description empty
    assert "# Level Zero" in md  # 0 clamped to 1
    assert "# Level One" in md  # 1 clamped to 1
    assert "###### Level Seven" in md  # 7 clamped to 6
    assert "## FAQ" not in md


def test_html_exporter_xss_escaping():
    """Verify HTML exporter rigorously escapes HTML tags and script payloads to prevent XSS."""
    xss_payload = "<script>alert('XSS')</script>"
    img_payload = '<img src=x onerror="alert(1)">'

    article = Article(
        title=f"Security Test {xss_payload}",
        slug="security-test",
        description=f"Desc with {img_payload}",
        sections=[
            ArticleSection(
                id="s1",
                heading=f"Section {xss_payload}",
                level=2,
                content=f"Paragraph 1 {img_payload}\n\nParagraph 2 with <b>raw html</b>"
            )
        ],
        faq=[
            FAQItem(question=f"Question {xss_payload}", answer=f"Answer {img_payload}")
        ]
    )

    html = export_html(article)

    # Must NOT contain unescaped script or img payload tags
    assert "<script>" not in html
    assert "<img src=x" not in html
    assert "<b>raw html</b>" not in html

    # Must contain HTML escaped equivalents
    assert "&lt;script&gt;alert(&#x27;XSS&#x27;)&lt;/script&gt;" in html or "&lt;script&gt;" in html
    assert "&lt;img src=x" in html


def test_html_exporter_semantic_structure():
    """Verify HTML output semantic hierarchy and structure."""
    article = Article(
        title="Semantic Title",
        slug="semantic-title",
        description="Semantic Description",
        sections=[
            ArticleSection(id="s1", heading="Section Heading", level=2, content="Para 1\n\nPara 2")
        ],
        faq=[FAQItem(question="Is it semantic?", answer="Yes, fully semantic.")]
    )

    html = export_html(article)
    assert "<h1>Semantic Title</h1>" in html
    assert "<p class='description'>Semantic Description</p>" in html
    assert "<h2>Section Heading</h2>" in html
    assert "<p>Para 1</p>" in html
    assert "<p>Para 2</p>" in html
    assert "<h2>FAQ</h2>" in html
    assert "<dl class='faq'>" in html
    assert "<dt>Is it semantic?</dt>" in html
    assert "<dd>Yes, fully semantic.</dd>" in html


def test_nextjs_exporter_path_traversal_prevention(tmp_path):
    """Verify NextJSExporter prevents path traversal attacks in article slug."""
    exporter = NextJSExporter()
    content_dir = tmp_path / "next_app" / "content"
    proj = Project(
        name="Security Proj",
        nextjs_integration={"enabled": True, "content_directory": str(content_dir), "export_format": "JSON"}
    )

    # Attempt path traversal via slug
    article = Article(
        title="Malicious Article",
        slug="../../malicious_escape",
        content="Exploit attempt"
    )

    exported_path = exporter.export(article, proj)
    # File must be stored strictly inside content_dir, not two levels up
    assert os.path.dirname(os.path.abspath(exported_path)) == os.path.abspath(str(content_dir))
    assert os.path.exists(exported_path)


def test_json_exporter_roundtrip():
    """Verify JSON export produces valid JSON deserializable by standard json and Article model."""
    article = Article(
        title="JSON Validation",
        slug="json-val",
        content="Direct markdown text",
        keywords=["test", "json"]
    )

    exported_json_str = export_json(article)
    parsed = json.loads(exported_json_str)

    assert parsed["title"] == "JSON Validation"
    assert parsed["keywords"] == ["test", "json"]

    reloaded = Article.model_validate_json(exported_json_str)
    assert reloaded.title == article.title
    assert reloaded.slug == article.slug


def test_nextjs_exporter_validation_and_connection(tmp_path):
    """Verify NextJSExporter validates configuration and connection."""
    exporter = NextJSExporter()

    # Unconfigured project
    proj_unconfigured = Project(name="No Config")
    with pytest.raises(ValueError, match="No Next.js project or content directory specified"):
        exporter.test_connection(proj_unconfigured)

    with pytest.raises(ValueError, match="Target Next.js content directory is not configured"):
        exporter.export(Article(title="T", slug="t"), proj_unconfigured)

    # Valid configured project
    content_dir = tmp_path / "valid_nextjs_content"
    proj_valid = Project(
        name="Valid NextJS",
        nextjs_integration={
            "enabled": True,
            "content_directory": str(content_dir),
            "export_format": "JSON"
        }
    )

    assert exporter.test_connection(proj_valid) is True

    # Probe file must be cleaned up
    probe_path = content_dir / ".blogforge_probe.tmp"
    assert not probe_path.exists()


def test_nextjs_exporter_export_formats(tmp_path):
    """Verify NextJSExporter exports JSON and Markdown formats accurately."""
    exporter = NextJSExporter()
    content_dir = tmp_path / "next_app" / "content"

    article = Article(
        title="Next.js Article",
        slug="nextjs-article",
        content="Content body for Next.js",
        sections=[ArticleSection(id="1", heading="Intro", level=2, content="Section text")]
    )

    # 1. JSON Export
    proj_json = Project(
        name="JSON App",
        nextjs_integration={"enabled": True, "content_directory": str(content_dir), "export_format": "JSON"}
    )
    json_path = exporter.export(article, proj_json)
    assert json_path.endswith(".json")
    assert os.path.exists(json_path)
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["title"] == "Next.js Article"

    # 2. Markdown Export
    proj_md = Project(
        name="MD App",
        nextjs_integration={"enabled": True, "content_directory": str(content_dir), "export_format": "MARKDOWN"}
    )
    md_path = exporter.export(article, proj_md)
    assert md_path.endswith(".md")
    assert os.path.exists(md_path)
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()
        assert "# Next.js Article" in md_text
        assert "## Intro" in md_text
