# BlogForge Python API Reference

While BlogForge includes a full PySide6 desktop GUI, its core engines can also be imported and used programmatically as a Python library for automation pipelines.

---

## 1. Generation Pipeline

The `GenerationPipeline` orchestrates outline generation, section drafting, and fact-checking.

```python
from app.providers.gemini import GeminiProvider
from app.generation.pipeline import GenerationPipeline
from app.generation.models import GenerationRequest

# Initialize AI provider
provider = GeminiProvider(api_key="YOUR_API_KEY", default_model="gemini-3.7-flash")
pipeline = GenerationPipeline(provider)

# Define request
req = GenerationRequest(
    topic="Optimizing Next.js Web Vitals with Server Components",
    audience="Senior Frontend Engineers",
    content_type="Technical Guide"
)

# Step 1: Generate Outline
outline = pipeline.generate_outline(req)
print(f"Generated {len(outline.sections)} planned sections.")

# Step 2: Write Sections Iteratively
article = pipeline.generate_article(
    req=req,
    outline=outline,
    progress_callback=lambda msg: print(f"Progress: {msg}")
)

# Step 3: Finalize (Generates FAQs, SEO tags, and saves to data/articles)
final_article = pipeline.finalize_article(article, req)
print(f"Article saved! Total length: {len(final_article.content)} chars.")
```

---

## 2. Research Engine

The `ResearchEngine` generates targeted search queries, compiles search landscapes, and derives strategic angles.

```python
from app.providers.gemini import GeminiProvider
from app.research.providers.mock import MockSearchProvider
from app.research.engine import ResearchEngine

provider = GeminiProvider()
search = MockSearchProvider() # Replace with live search provider if configured

engine = ResearchEngine(ai_provider=provider, search_provider=search)
run = engine.run_research(topic="Edge AI Deployment Patterns", depth="Deep")

print("Primary Intent:", run.strategy.primary_intent)
print("Recommended Angle:", run.strategy.recommended_angle)
for gap in run.strategy.content_gaps:
    print(f"- Content Gap: {gap.topic} ({gap.importance})")
```

---

## 3. Project & Brand Service

Manage brand rules, products, and internal linking strategies.

```python
from app.projects.service import ProjectService
from app.projects.models import Product, InternalLink

service = ProjectService()

# Create a project
project = service.create_project(name="DevSaaS", description="Developer Tools Suite")
project.brand_profile.tone = "Authoritative, technical, and concise"

# Add contextual products
project.products.append(Product(
    name="DevMetrics",
    description="Real-time distributed tracing platform",
    status="Active"
))

# Add internal links
project.internal_links.append(InternalLink(
    url="/blog/distributed-tracing-guide",
    title="Comprehensive Tracing Guide"
))

service.update_project(project)
```

---

## 4. Multi-Format Exporters

Convert `Article` domain objects into destination formats.

```python
from app.export.markdown import export_markdown
from app.export.html import export_html
from app.export.json import export_json

markdown_text = export_markdown(article)
html_markup = export_html(article)
json_payload = export_json(article)
```
