"""Script to render and capture high-resolution screenshots of the redesigned BlogForge interface."""

import os
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap

from app.ui.theme import apply_theme
from app.ui.main_window import MainWindow
from app.ui.components.dialogs import ArticleGeneratorDialog
from app.models.article import Article, ArticleSection
from app.projects.models import Product, InternalLink, BrandProfile
from app.research.models import ResearchRun, SearchLandscape, SearchResult, ContentStrategy, ContentGap


def capture_all():
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance() or QApplication(sys.argv)
    apply_theme(app)

    out_dir = "screenshots/editorial_paper"
    os.makedirs(out_dir, exist_ok=True)

    window = MainWindow()
    window.resize(1280, 840)

    # 1. Setup sample project
    proj = window.project_service.create_project(
        name="The Pragmatic Architect",
        description="High-craft technical publication exploring distributed systems, modern AI, and data pipelines."
    )
    proj.brand_profile = BrandProfile(
        brand_name="The Pragmatic Architect",
        description="Deep engineering perspectives for senior architects.",
        mission="Deconstruct complex systems into elegant, maintainable primitives.",
        target_audience="Principal Engineers, Tech Leads, Cloud Architects",
        tone="Authoritative, pragmatic, deeply technical, concise",
        writing_style="Clear active voice, grounded in empirical data and production precedents."
    )
    proj.products = [
        Product(name="ApexQuery", description="Ultra-low latency columnar storage engine for high-throughput analytics."),
        Product(name="CacheMesh", description="Distributed memory fabric for resilient edge synchronization.")
    ]
    proj.internal_links = [
        InternalLink(title="Architecture Blueprints", url="/blueprints"),
        InternalLink(title="Distributed Systems Guide", url="/guides/distributed-systems"),
        InternalLink(title="Performance Benchmarks", url="/benchmarks")
    ]
    window.project_service.update_project(proj)
    window.refresh_project_switcher()

    # 2. Setup realistic long sample article
    long_article_content = """# Principles of Modern High-Throughput Event-Driven Architectures

Modern software engineering demands systems capable of processing millions of concurrent transactions with sub-millisecond latencies, bulletproof fault isolation, and minimal operational complexity. While microservices and RESTful HTTP boundaries served the industry well during the previous decade, they routinely falter under high-concurrency event bursts.

> "A well-architected distributed system treats latency not as a static measurement, but as an empirical probability distribution across variable network conditions."

## 1. The Anatomy of Modern Event Brokers

Event-driven architectures decouple state mutation from synchronous request-response lifecycles. Rather than invoking downstream RPC boundaries, producers emit immutable state transitions into partitioned append-only logs.

### Key Tenets of Log-Centric Persistence:
- **Append-Only Immutability:** Write amplification is minimized by writing sequential blocks to non-volatile storage.
- **Consumer Independence:** Downstream subscribers advance their respective offset pointers independently without head-of-line blocking.
- **Replayability:** In the event of catastrophic downstream worker degradation, offsets can be rewound to restore historical state deterministically.

```python
from typing import AsyncGenerator, Dict, Any
import asyncio

class ResilientStreamConsumer:
    def __init__(self, broker_uri: str, group_id: str):
        self.uri = broker_uri
        self.group = group_id
        self._connected = True

    async def consume_partition(self, partition_id: int) -> AsyncGenerator[Dict[str, Any], None]:
        while self._connected:
            batch = await self._fetch_offset_batch(partition_id, limit=500)
            for event in batch:
                yield event
            await asyncio.sleep(0.005)
```

## 2. Managing Distributed Consistency

Balancing consistency and partition tolerance remains the defining challenge of distributed system architects. In mission-critical financial ledgers and real-time inventory systems, eventual consistency is often insufficient.

| Paradigm | Throughput (Tx/sec) | P99 Latency | Failure Recovery |
| :--- | :--- | :--- | :--- |
| Two-Phase Commit (2PC) | ~1,200 | 45ms | Heavy coordinator locks |
| Saga Orchestration | ~25,000 | 8ms | Compensating transactions |
| Outbox Pattern with CDC | ~85,000 | 1.8ms | Debezium transactional log tailing |

### Recommended Migration Path:
1. Isolate the operational database transaction boundary.
2. Publish transactional outbox events to a dedicated Apache Kafka or Redpanda partition.
3. Decouple analytics consumers and search indexes into autonomous asynchronous read-models.

By adopting this disciplined separation of concerns, engineering organizations can dramatically increase deployment velocity while keeping latency profiles strictly contained.
"""

    art = Article(
        project_id=proj.id,
        title="Principles of Modern High-Throughput Event-Driven Architectures",
        slug="modern-event-driven-architectures",
        description="A technical guide to distributed event streaming, log-centric architectures, and consistency patterns.",
        content=long_article_content,
        sections=[
            ArticleSection(id="sec1", heading="The Anatomy of Modern Event Brokers", level=2, content="..."),
            ArticleSection(id="sec2", heading="Managing Distributed Consistency", level=2, content="...")
        ]
    )

    art_dir = "data/articles"
    os.makedirs(art_dir, exist_ok=True)
    art_path = os.path.join(art_dir, f"{art.slug}.json")
    with open(art_path, "w", encoding="utf-8") as f:
        f.write(art.model_dump_json(indent=2))

    # Also save a draft
    draft_art = Article(
        project_id=proj.id,
        title="Zero-Downtime Database Migration Strategies",
        slug="zero-downtime-migrations",
        description="Dual-writing and shadow routing patterns for PostgreSQL.",
        content="# Zero-Downtime Database Migration Strategies\n\nDraft in progress...",
        sections=[ArticleSection(id="d1", heading="Introduction", level=2, content="")]
    )
    gen_dir = "data/generation"
    os.makedirs(gen_dir, exist_ok=True)
    with open(os.path.join(gen_dir, f"{draft_art.slug}.json"), "w", encoding="utf-8") as f:
        f.write(draft_art.model_dump_json(indent=2))

    # Populate sample research
    mock_run = ResearchRun(
        topic="Event-Driven Microservices 2026",
        queries=[
            "event-driven architecture performance benchmarks 2026",
            "kafka vs redpanda vs nats high throughput",
            "transactional outbox pattern cdc postgres"
        ],
        search_landscape=[
            SearchLandscape(
                query="event-driven architecture performance benchmarks 2026",
                results=[
                    SearchResult(
                        title="High-Throughput Streaming in Cloud Environments",
                        url="https://engineering.architecture.io/streaming-2026",
                        domain="engineering.architecture.io",
                        snippet="Comparative analysis of log-based brokers processing 1M events/sec."
                    ),
                    SearchResult(
                        title="Zero-Loss Event Processing with Debezium CDC",
                        url="https://distributed.systems/cdc-patterns",
                        domain="distributed.systems",
                        snippet="Production architecture patterns for dual-write avoidance."
                    )
                ]
            )
        ],
        strategy=ContentStrategy(
            primary_intent="Architecture Evaluation",
            audience="Senior Staff Software Engineers & Cloud Architects",
            primary_topic="Event-Driven Streaming",
            recommended_angle="Pragmatic production benchmarks contrasting log brokers with transactional CDC",
            content_gaps=[
                ContentGap(
                    topic="Operational Failure Modes",
                    description="Lack of documented recovery protocols during split-brain partitions",
                    importance="High",
                    evidence="Search result gaps across major vendor tutorials"
                )
            ],
            recommended_outline=[
                "1. Executive Summary & Problem Framing",
                "2. Log Storage Engines Compared (Kafka vs Redpanda)",
                "3. Transactional Outbox Pattern Architecture",
                "4. Benchmark Methodology & P99 Latencies"
            ]
        ),
        created_at="2026-11-14T11:00:00",
        metadata={"depth": "Deep"}
    )
    window.research_view.display_research_run(mock_run)

    # -------------------------------------------------------------------------
    # Render & Capture Views
    # -------------------------------------------------------------------------
    def save_screen(filename: str):
        pixmap = window.grab()
        pixmap.save(os.path.join(out_dir, filename))
        print(f"Captured: {filename} ({window.width()}x{window.height()})")

    # 1. Home / Workspace Overview
    window.switch_tab(0)
    window.dashboard_view.load_recent_articles()
    save_screen("01_home_workspace.png")

    # 2. Projects & Editorial Style Guide
    window.switch_tab(1)
    window.projects_view.tabs.setCurrentIndex(0)
    save_screen("02_projects_style_guide.png")

    # 3. Product Catalog
    window.projects_view.tabs.setCurrentIndex(1)
    save_screen("03_projects_product_catalog.png")

    # 4. Internal Links
    window.projects_view.tabs.setCurrentIndex(2)
    save_screen("04_projects_internal_links.png")

    # 5. Article Editor — Split Mode
    window.switch_tab(2)
    window.articles_view.refresh_articles()
    window.articles_view.select_article_by_slug("modern-event-driven-architectures")
    window.articles_view.set_view_mode("split")
    save_screen("05_editorial_studio_split.png")

    # 6. Article Editor — Write Only Mode (Distraction-Free)
    window.articles_view.set_view_mode("write")
    save_screen("06_editorial_studio_write_only.png")

    # 7. Article Editor — Preview Only Mode (Typeset Publication)
    window.articles_view.set_view_mode("preview")
    save_screen("07_editorial_studio_preview_only.png")

    # Reset to split
    window.articles_view.set_view_mode("split")

    # 8. Research Studio
    window.switch_tab(3)
    save_screen("08_research_studio.png")

    # 9. Settings
    window.switch_tab(4)
    save_screen("09_settings_preferences.png")

    # 10. AI Article Production Studio Dialog
    dialog = ArticleGeneratorDialog(window, active_project=proj)
    dialog.topic_input.setText("Autonomous Agent Protocols for Cloud Orchestration")
    dialog.keywords_input.setText("mcp, open-telemetry, tool-use, fault-isolation")
    dialog.resize(620, 540)
    dlg_pix = dialog.grab()
    dlg_pix.save(os.path.join(out_dir, "10_ai_production_studio_modal.png"))
    print("Captured: 10_ai_production_studio_modal.png (620x540)")

    # 11. Laptop Viewport 1024x700 — Editor Split
    window.resize(1024, 700)
    window.switch_tab(2)
    save_screen("11_laptop_1024x700_editor_split.png")

    # 12. Laptop Viewport 1024x700 — Home
    window.switch_tab(0)
    save_screen("12_laptop_1024x700_home.png")

    # 13. Widescreen 1440x900 — Editor Split
    window.resize(1440, 900)
    window.switch_tab(2)
    save_screen("13_widescreen_1440x900_editor.png")

    # 14. Full HD 1920x1080 — Editor Split
    window.resize(1920, 1080)
    window.switch_tab(2)
    save_screen("14_fullhd_1920x1080_editor.png")

    print("\nAll 14 editorial paper screenshots successfully generated.")


if __name__ == "__main__":
    capture_all()
