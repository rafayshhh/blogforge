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
        filename = f"{article.slug or 'article'}{ext}"
        filepath = os.path.join(target_dir, filename)

        if fmt == "JSON":
            content = export_json(article)
        else:
            content = export_markdown(article)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return filepath
