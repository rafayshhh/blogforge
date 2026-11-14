# Security Policy

## Supported Versions

The following table outlines the status of currently maintained releases of BlogForge:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

---

## Reporting a Vulnerability

We take the security and privacy of BlogForge very seriously. As BlogForge is a local-first application handling local files and AI credentials, securing environment variables and API integrations is paramount.

If you believe you have discovered a security vulnerability, **please do not open a public GitHub issue**.

### Reporting Process
1. Contact the maintainers privately via GitHub Security Advisories or by emailing the project maintainer.
2. Please provide:
   - A detailed description of the vulnerability.
   - Clear steps to reproduce the issue (code snippets, terminal inputs, or mock configuration).
   - Potential impact on local file integrity, credentials, or remote services.
3. You will receive an acknowledgment within 48 hours.
4. We will coordinate a remediation release before public disclosure.

---

## Best Practices for BlogForge Users

- **Keep `.env` Private:** Never commit `.env` or files containing `GEMINI_API_KEY` to public repositories.
- **Review Research Sources:** BlogForge includes system-level safeguards against prompt injection from scraped web data, but users should always inspect external research sources.
- **Regular Updates:** Keep dependencies updated using `pip install --upgrade -r requirements.txt`.
