# BlogForge Development Guide

This guide details how to set up, build, test, and contribute to BlogForge on your local machine.

---

## 1. Prerequisites

- **Python:** 3.11, 3.12, or 3.13 (recommended: Python 3.12).
- **Google Gemini API Key:** Required for AI operations. Get one at [Google AI Studio](https://aistudio.google.com/).
- **Git:** Version control.

---

## 2. Setting Up Your Development Environment

### 2.1 Clone the Repository
```bash
git clone https://github.com/your-username/BlogForge.git
cd BlogForge
```

### 2.2 Create a Virtual Environment
On Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2.3 Install Dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .
```

### 2.4 Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and add your Gemini API key:
```env
GEMINI_API_KEY=your_actual_key_here
GEMINI_MODEL=gemini-3.7-flash
LOG_LEVEL=DEBUG
```

---

## 3. Running BlogForge

Launch the desktop application:
```bash
python -m app.main
```
Or use the convenience scripts:
- Windows: `run.bat`
- Linux/macOS: `./run.sh`

---

## 4. Running Tests

Run the full pytest suite:
```bash
pytest tests/
```

Run tests with verbose output and coverage:
```bash
pytest -v --tb=short tests/
```

Run a specific test module:
```bash
pytest tests/test_generation/test_pipeline.py
```

---

## 5. Code Quality & Linting

We enforce PEP 8 style standards using `flake8`:
```bash
flake8 app tests --max-line-length=120
```

---

## 6. Project Layout

```
BlogForge/
├── app/                  # Application source code
│   ├── core/             # Configuration, logging, constants, exceptions
│   ├── models/           # Domain schemas (Article, SEO, Provider)
│   ├── projects/         # Project & Brand models, repository, service
│   ├── providers/        # AI & Search providers (Gemini, Mock)
│   ├── generation/       # Pipeline, outline, writer, reviewer, prompts
│   ├── content/          # Topic-aware context filtering
│   ├── export/           # Markdown, HTML, JSON exporters
│   ├── integrations/     # Next.js exporter integration
│   └── ui/               # PySide6 desktop views, theme, and main window
├── data/                 # Local data storage (ignored by git)
│   ├── articles/         # Saved article JSON records
│   ├── generation/       # Intermediate generation runs
│   ├── projects/         # Project definition JSON records
│   └── research/         # Research run reports
├── docs/                 # Architectural & operational documentation
├── tests/                # Automated pytest suite
├── .env.example          # Safe configuration template
├── pyproject.toml        # Build and packaging configuration
├── requirements.txt      # Production runtime dependencies
└── requirements-dev.txt  # Development and test dependencies
```
