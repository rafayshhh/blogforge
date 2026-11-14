# Changelog

All notable changes to the BlogForge project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-11-14

### Added
- **Desktop Application (PySide6):** Modern dark cyber aesthetic UI with custom color palette and responsive controls.
- **Project & Brand Governance:** Full local CRUD for multiple brand profiles, including tone, writing style, vocabulary guidelines, products, and internal linking strategies.
- **Context Filtering Engine:** Automatic topic-aware extraction of relevant products and internal URLs to inject into article generation prompts without bloating context.
- **Multi-Stage Generation Pipeline:**
  - Automated outline generator structuring logical H2/H3 headings and section objectives.
  - Section-by-section iterative writer with live progress tracking and intermediate auto-saving.
  - Critical fact-checking and repetition audit reviewer.
  - Contextual FAQ generator.
- **Content Research Engine:** Strategic search query generation, competitive landscape analysis, and gap detection.
- **Exporters:** Multi-format export to Markdown, semantic HTML, and structured JSON.
- **Next.js Integration:** Direct export and directory connection verification for Next.js static site generator workflows.
- **Configuration & Security:**
  - Secure `.env` local loading with `.env.example` template.
  - `SYSTEM_DEFENSE` prompt shielding preventing prompt injection from external research sources.
  - Dynamic Gemini model selection supporting `gemini-3.7-flash` and `gemini-3.1-pro-preview`.
  - In-app live connection tester verifying credentials against Google GenAI.
- **Developer Experience:**
  - Automated test suite using `pytest` covering domain models, services, exporters, and generation pipeline.
  - Windows (`setup.bat`, `run.bat`) and Unix (`run.sh`) launch scripts.
  - GitHub Actions CI workflow for Python 3.11, 3.12, and 3.13.
  - Comprehensive documentation: Architecture, Development, Deployment, API, Contributing, and Security guidelines.
