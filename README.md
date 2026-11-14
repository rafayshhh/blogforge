# BlogForge ⚡

<p align="center">
  <strong>A local-first, privacy-focused desktop studio for AI-powered content research, long-form drafting, and multi-format publishing.</strong>
</p>

<p align="center">
  <a href="#key-features">Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#documentation">Documentation</a> •
  <a href="#contributing">Contributing</a>
</p>

---

## 1. Introduction

**BlogForge** is a modern desktop workspace engineered for technical writers, content creators, and developer marketers. It bridges the gap between chaotic raw AI chats and production-ready blog publishing.

Instead of generic, robotic AI text stuffed with hallucinations and buzzwords, BlogForge enforces strict **Brand Voice Profiles**, leverages a **Topic-Aware Context Engine**, and executes an **Iterative Multi-Stage Generation Pipeline** (Outline → Section-by-Section Writing → Critical Review → FAQ Synthesis) using Google's Gemini models.

Best of all, BlogForge is **local-first**: all your projects, brand guidelines, articles, and drafts remain strictly on your workstation.

---

## 2. Project Purpose

Content generation tools often fail developers and technical founders in three key areas:
1. **Cloud Lock-in & Privacy Leaks:** Projects and unpublished drafts are stored on remote multi-tenant databases.
2. **Context Bloat & Irrelevant Mentions:** Dumping entire brand guides into prompts causes models to mention unrelated products or spam internal links.
3. **Monolithic Hallucinations:** Asking an LLM to generate a 3,000-word article in a single prompt yields shallow, repetitive paragraphs with fabricated claims.

**BlogForge solves this** by providing:
- An offline-first local file store (`data/projects/` and `data/articles/`).
- Intelligent tokenized keyword matching that injects only relevant products and links for each specific topic.
- A section-by-section writing pipeline with system-level defenses against prompt injection and fake testimonials.

---

## 3. Key Features

- 🖥️ **Modern Desktop Experience (PySide6 / Qt):** Cyber-dark aesthetic designed for high focus with zero clutter.
- 🏢 **Multi-Brand & Project Governance:** Manage multiple websites or SaaS products with distinct brand tones, writing styles, preferred vocabulary, and rules.
- 🎯 **Topic-Aware Context Filtering:** Dynamically matches products and internal URLs relevant to the topic, eliminating keyword stuffing and context bloat.
- 🤖 **Powered by Google Gemini 3.x:** Native integration with `gemini-3.7-flash` (recommended for everyday speed and reasoning) and `gemini-3.1-pro-preview` using the official `google-genai` SDK.
- 🛡️ **Defensive Prompt Shielding (`SYSTEM_DEFENSE`):** Enforces strict isolation on research material to prevent prompt injection and prohibits inventing false claims or fabricated benchmarks.
- 📝 **Iterative Generation Pipeline:** Generates structured outlines first, writes each section independently with real-time UI progress updates, and saves intermediate drafts automatically.
- 🔍 **Autonomous Research Engine:** Generates strategic search queries, analyzes competitive search landscapes, and discovers untapped content gaps.
- 📋 **Integrated Fact-Check & Review:** Audits drafts for repetition, unsupported assertions, and missing strategic opportunities before publishing.
- 🌐 **Direct Next.js Export:** Validates directory permissions and exports structured Markdown or JSON directly into Next.js blog repositories.
- 📤 **Multi-Format Exporters:** Export articles as clean Markdown, semantic HTML, or JSON.

---

## 4. Technology Stack

- **Runtime:** Python 3.11+
- **Desktop UI:** PySide6 (Qt for Python)
- **AI SDK:** Google GenAI SDK (`google-genai>=2.20.0`)
- **Data Validation & Modeling:** Pydantic v2
- **Configuration:** Python-Dotenv
- **Resilience:** Tenacity (exponential backoff retry loops)
- **Syntax Highlighting:** Pygments
- **Testing:** Pytest

---

## 5. Application Interface

```
+------------------------------------------------------------------------------------+
| ⚡ BlogForge v1.0.0      [Dashboard]  [Projects]  [Articles & Drafts]  [Settings]   |
+------------------------------------------------------------------------------------+
|  Welcome to BlogForge                                Active Project: [ DevPortal ▼]|
|  Research. Write. Optimize. Ship.                                                  |
|                                                                                    |
|  [+ New Article]                                                                   |
|                                                                                    |
|  Getting Started                                     Overview                      |
|  ✓ ① Connect Gemini (Settings)                       +----------+ +--------------+ |
|  ✓ ② Create a Project (Brand & Rules)                | Articles | | Drafts       | |
|  ○ ③ Configure Next.js Export (Optional)             |    12    | |      3       | |
|                                                      +----------+ +--------------+ |
+------------------------------------------------------------------------------------+
```
*(Screenshots will be published in the release assets).*

---

## 6. Project Architecture

BlogForge strictly separates UI components from core business logic:

```
BlogForge/
├── app/
│   ├── core/              # Config loader, logging, exceptions, constants
│   ├── models/            # Domain models (Article, Section, SEO, Provider)
│   ├── projects/          # Project CRUD, brand profiles, and JSON repository
│   ├── providers/         # Gemini and Search providers
│   ├── generation/        # Outline, writer, reviewer, pipeline orchestration
│   ├── content/           # Topic-aware contextual filtering engine
│   ├── export/            # Markdown, HTML, JSON exporters
│   ├── integrations/      # Next.js export synchronization
│   └── ui/                # PySide6 desktop views, theme, and main window
├── data/                  # Local JSON data store (projects, articles, drafts)
├── docs/                  # In-depth architectural & developer guides
└── tests/                 # Unit and integration test suite
```

Detailed architectural diagrams are documented in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## 7. Prerequisites

- Python 3.11 or newer (Python 3.12 recommended).
- A Google Gemini API Key from [Google AI Studio](https://aistudio.google.com/).

---

## 8. Quick Start

### Windows (Automated Setup)
Clone the repository and run the setup script:
```cmd
git clone https://github.com/your-username/BlogForge.git
cd BlogForge
setup.bat
```
Then launch the application:
```cmd
run.bat
```

### Manual Installation (All Platforms)
1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/BlogForge.git
   cd BlogForge
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # Windows
   python -m venv .venv
   .\.venv\Scripts\activate

   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   pip install -e .
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   ```
   Add your Gemini API key inside `.env`:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-3.7-flash
   ```
   *(Note: You can also enter and test your API key directly within the app's **Settings** panel).*

5. **Run BlogForge:**
   ```bash
   python -m app.main
   ```

---

## 9. Testing & Quality Assurance

Run the automated test suite with pytest:
```bash
pytest tests/
```

Check code style with flake8:
```bash
flake8 app tests --max-line-length=120
```

---

## 10. Programmatic Python API

You can also import and use BlogForge's generation pipeline in your own scripts:

```python
from app.providers.gemini import GeminiProvider
from app.generation.pipeline import GenerationPipeline
from app.generation.models import GenerationRequest

ai = GeminiProvider(api_key="YOUR_KEY", default_model="gemini-3.7-flash")
pipeline = GenerationPipeline(ai)

req = GenerationRequest(
    topic="Optimizing Docker Builds for Python",
    audience="DevOps Engineers"
)

outline = pipeline.generate_outline(req)
article = pipeline.generate_article(req, outline)
final = pipeline.finalize_article(article, req)

print(f"Generated article '{final.title}' with {len(final.sections)} sections.")
```
For complete details, see [`docs/API.md`](docs/API.md).

---

## 11. Known Limitations

- **Web Search Provider:** BlogForge includes a `MockSearchProvider` out of the box for testing and deterministic generation. Integration with live search APIs (e.g. Google Search Grounding or Serper) is pluggable via `SearchProvider`.
- **Desktop Single-User:** BlogForge is optimized for single-workstation local development rather than multi-user concurrent team editing.

---

## 12. Documentation Index

- [Architecture Overview](docs/ARCHITECTURE.md)
- [Development Guide](docs/DEVELOPMENT.md)
- [Packaging & Distribution Guide](docs/DEPLOYMENT.md)
- [Python API Reference](docs/API.md)
- [Security Policy & Vulnerability Reporting](SECURITY.md)
- [Contributing Guidelines](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Changelog](CHANGELOG.md)

---

## 13. Contributing

Contributions are warmly welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on code style, issue reporting, and pull request procedures.

---

## 14. License

BlogForge is released as open-source software under the [MIT License](LICENSE).  
Copyright (c) 2026 RafayShhh.

---

## 15. Acknowledgments

- Built with [PySide6](https://www.qt.io/qt-for-python) (The Qt Company).
- Powered by [Google GenAI SDK](https://github.com/google-gemini/generative-ai-python) and the Gemini family of models.
- Structured with [Pydantic](https://docs.pydantic.dev/).
