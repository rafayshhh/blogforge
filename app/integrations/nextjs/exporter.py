"""Next.js static site generator content exporter."""

import os
from app.projects.models import Project
from app.models.article import Article
from app.export.markdown import export_markdown
from app.export.json import export_json


class NextJSExporter:
    """Exports articles directly into a Next.js content or pages directory."""

    def test_connection(self, project: Project) -> bool:
        """Validates that configured Next.js directories exist and are writable."""
        config = project.nextjs_integration
        target_dir = config.content_directory or config.project_directory

        if not target_dir:
            raise ValueError("No Next.js project or content directory specified.")

        os.makedirs(target_dir, exist_ok=True)
        probe_file = os.path.join(target_dir, ".blogforge_probe.tmp")
        try:
            with open(probe_file, "w", encoding="utf-8") as f:
                f.write("probe")
            os.remove(probe_file)
            return True
        except Exception as e:
            raise PermissionError(f"Directory '{target_dir}' is not writable: {e}")

    def export(self, article: Article, project: Project) -> str:
        """Writes the article to the configured Next.js content directory."""
        config = project.nextjs_integration
        target_dir = config.content_directory or config.project_directory

        if not target_dir:
            raise ValueError("Target Next.js content directory is not configured.")

        os.makedirs(target_dir, exist_ok=True)
        fmt = (config.export_format or "JSON").upper()
        ext = ".json" if fmt == "JSON" else ".md"

        # Sanitize slug against directory traversal
        clean_slug = os.path.basename(article.slug or "article").strip()
        filename = f"{clean_slug or 'article'}{ext}"
        filepath = os.path.abspath(os.path.join(target_dir, filename))
        target_abs = os.path.abspath(target_dir)

        # Enforce strict directory boundary
        try:
            common = os.path.commonpath([target_abs, filepath])
            if common != target_abs:
                raise ValueError(f"Path traversal detected in slug: {article.slug}")
        except ValueError:
            raise ValueError(f"Path traversal detected in slug: {article.slug}")

        if fmt == "JSON":
            content = export_json(article)
        else:
            content = export_markdown(article)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return filepath
