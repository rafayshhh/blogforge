# BlogForge System Architecture

## 1. Architectural Principles

BlogForge is designed around four core architectural principles:

1. **Local-First Privacy:** All project configurations, brand voice profiles, product definitions, research data, article drafts, and logs reside strictly on the user's local disk under `data/` and `logs/`. No telemetry or project data is sent to external servers.
2. **Defensive AI Orchestration:** External web data gathered during research is treated as untrusted input. The generation pipeline enforces strict prompt boundaries (`SYSTEM_DEFENSE`) to prevent prompt injection and hallucinated facts.
3. **Strict Separation of Concerns:** Clear demarcation between Presentation (PySide6 desktop shell), Domain / Application Services, and External Providers.
4. **Decoupled Publishing:** Independent exporters format articles into clean Markdown, HTML, JSON, or sync them directly into external static site generator directories (e.g. Next.js).

---

## 2. High-Level Component Diagram

```
+-----------------------------------------------------------------------------+
|                               UI LAYER (Qt)                                 |
|                                                                             |
|  MainWindow (Shell & Global Navigation)                                     |
|  +-------------------+  +-------------------+  +-------------------------+  |
|  |  DashboardWidget  |  |  ProjectsWidget   |  |     ArticlesWidget      |  |
|  +-------------------+  +-------------------+  +-------------------------+  |
|  +-------------------+                                                      |
|  |  SettingsWidget   |                                                      |
|  +-------------------+                                                      |
+--------------------------------------+--------------------------------------+
                                       |
                                       v
+-----------------------------------------------------------------------------+
|                          APPLICATION / CORE LAYER                           |
|                                                                             |
|  +-------------------------+            +--------------------------------+  |
|  |   GenerationPipeline    |            |         ResearchEngine         |  |
|  | - OutlineGenerator      |            | - Query Generation             |  |
|  | - ArticleWriter         |            | - Landscape Analysis           |  |
|  | - ArticleReviewer       |            | - Content Strategy Synthesis   |  |
|  | - FAQ Generator         |            +--------------------------------+  |
|  +-------------------------+                                                |
|                                                                             |
|  +-------------------------+            +--------------------------------+  |
|  |     ProjectService      |            |    FilteredProjectContext      |  |
|  | (Business Logic & CRUD) |            | (Topic-Aware Keyword Matching) |  |
|  +-------------------------+            +--------------------------------+  |
+--------------------------------------+--------------------------------------+
                                       |
                   +-------------------+-------------------+
                   |                                       |
                   v                                       v
+------------------------------------+  +------------------------------------+
|         PERSISTENCE LAYER          |  |          PROVIDER LAYER            |
|                                    |  |                                    |
| - ProjectRepository (Local JSON)   |  | - AIProvider (Abstract Base)       |
| - File Exporters:                  |  | - GeminiProvider (google-genai)    |
|   * Markdown Exporter              |  | - Provider Factory & Resolution    |
|   * HTML Exporter                  |  | - SearchProvider (Mock / Pluggable)|
|   * JSON Exporter                  |  |                                    |
|   * NextJSExporter (SSG sync)      |  |                                    |
|                                    |  |                                    |
+------------------------------------+  +------------------------------------+
```

---

## 3. Core Subsystems

### 3.1 Domain Models (`app/models/` and `app/projects/models.py`)
All entities are modeled with **Pydantic v2**:
- **`Article`:** Central entity containing sections, full markdown, SEO metadata, keyword tags, and FAQs.
- **`ArticleSection`:** Heading, level (1–6), content, and source citations.
- **`Project`:** Brand guidelines (tone, audience, style, rules), products/services, internal URLs, and Next.js export settings.
- **`BrandProfile`:** Target audience, writing style, preferred and avoided vocabulary, content rules.

### 3.2 Context Filtering Engine (`app/content/context.py`)
To prevent token waste and irrelevant mentions, `FilteredProjectContext` analyzes the target topic against the project's brand portfolio:
- If fewer than 5 products or links exist, all active entries are retained.
- If more than 5 exist, tokenized keyword matching evaluates product titles, features, descriptions, and URL paths against topic tokens.
- Only relevant assets are injected into the prompt.

### 3.3 Multi-Stage Generation Pipeline (`app/generation/`)
Article generation follows a strict multi-step workflow:
1. **Outline Generation (`OutlineGenerator`):** Transforms topic and project context into a structured `ArticleOutline` with purpose notes and key points per section.
2. **Iterative Section Writing (`ArticleWriter`):** Generates each section independently, avoiding context length bottlenecks and enabling real-time UI progress updates and intermediate saving.
3. **Anti-AI Slop Enforcement:** Systematic prompts ban 35+ buzzwords, require concrete technical mechanics, prohibit rhetorical question openings, and enforce sentence variety.
4. **Heuristic Quality Review (`ArticleReviewer`):** Scans drafts for machine clichés, repeated n-grams, duplicate paragraphs, and brand vocabulary compliance.
5. **FAQ Synthesis:** Extracts logical reader questions and synthesizes concise answers.
6. **Persistence:** Saves the completed artifact to `data/articles/{run_id}.json` and purges partial drafts.

### 3.4 Google Gemini AI Architecture (`app/providers/`)
The AI provider layer couples business logic to Google's official `google-genai` SDK through an extensible abstract interface:
- **`AIProvider`:** Abstract base defining `generate()`, `generate_structured()`, `diagnose_connection()`, and `list_available_models()`.
- **`GeminiProvider`:** Uses Google's official `google-genai` SDK. Supports Gemini 3.8/3.5 and 4 series with thinking budgets (`thinking_level="medium"`), account model discovery, and native structured Pydantic schemas.
- **Factory & Resolver (`app/providers/factory.py`):** Centralizes instantiation and dynamic environment resolution via `resolve_active_provider()`.
- **Resilience:** All network calls implement exponential backoff retry loops on transient HTTP 429 and 5xx errors via `tenacity`.
