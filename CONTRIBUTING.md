# Contributing to BlogForge

Thank you for your interest in contributing to BlogForge! We welcome contributions from developers, technical writers, and designers of all skill levels.

---

## 1. Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## 2. How to Contribute

### 2.1 Reporting Bugs
- Check existing [GitHub Issues](https://github.com/your-username/BlogForge/issues) to avoid duplicate reports.
- If you find a new bug, submit an issue using our [Bug Report Template](.github/ISSUE_TEMPLATE/bug_report.md).
- Include steps to reproduce, Python and OS versions, and any error logs from `logs/blogforge.log`.

### 2.2 Proposing Features
- Open a feature request using our [Feature Request Template](.github/ISSUE_TEMPLATE/feature_request.md).
- Describe the problem your feature solves and how it fits into the desktop workflow.

### 2.3 Submitting Pull Requests
1. **Fork** the repository and create your feature branch:
   ```bash
   git checkout -b feature/my-cool-feature
   ```
2. **Set up** your development environment following the [Development Guide](docs/DEVELOPMENT.md).
3. **Write Tests:** Ensure new or modified behavior is backed by automated tests under `tests/`.
4. **Format & Lint:** Check code style with `flake8`:
   ```bash
   flake8 app tests --max-line-length=120
   ```
5. **Run Tests:** Ensure all tests pass:
   ```bash
   pytest tests/
   ```
6. **Commit with Clear Messages:** Follow conventional commits (e.g. `feat: add export to Hugo frontmatter`, `fix: handle empty API key gracefully`).
7. **Submit a Pull Request** against the `main` branch referencing your issue.

---

## 3. Coding Guidelines

- **Python Version:** BlogForge targets Python 3.11+.
- **Type Hints:** Use PEP 484 type annotations for function signatures and class definitions.
- **Pydantic Validation:** All domain models and structured LLM schemas must inherit from `pydantic.BaseModel`.
- **UI Decoupling:** Keep Qt / PySide6 widgets focused on presentation; delegate business logic to services in `app/projects/`, `app/generation/`, and `app/research/`.
- **Security:** Never hardcode credentials, URLs with embedded auth tokens, or private endpoints.
