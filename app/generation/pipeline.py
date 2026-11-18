"""Multi-stage article generation pipeline orchestrator with flow continuity and source tracking."""

import datetime
import os
import uuid
from typing import Optional, Callable
from app.providers.base import AIProvider
from app.generation.models import GenerationRequest, ArticleOutline, ArticleReview
from app.models.article import Article, ArticleSection
from app.generation.outline import OutlineGenerator
from app.generation.writer import ArticleWriter
from app.generation.reviewer import ArticleReviewer
from app.projects.service import ProjectService
from app.content.context import FilteredProjectContext


class GenerationPipeline:
    def __init__(self, ai_provider: AIProvider):
        self.ai = ai_provider
        self.outline_gen = OutlineGenerator(self.ai)
        self.writer = ArticleWriter(self.ai)
        self.reviewer = ArticleReviewer(self.ai)
        self.project_service = ProjectService()
        self.is_cancelled = False
        self.run_id = str(uuid.uuid4())

    def cancel(self):
        self.is_cancelled = True

    def generate_outline(self, req: GenerationRequest) -> ArticleOutline:
        return self.outline_gen.generate(req)

    def generate_article(
        self,
        req: GenerationRequest,
        outline: ArticleOutline,
        progress_callback: Optional[Callable] = None
    ) -> Article:
        article = Article(
            project_id=req.project_id,
            title=outline.title,
            slug=outline.slug,
            description="",
            content="",
            sections=[],
            faq=[],
            sources=list(req.verified_sources) if req.verified_sources else [],
            internal_links=[],
            seo={}
        )

        # Pre-cache project context for the entire pipeline run
        if req.project_id:
            proj = self.project_service.get_project(req.project_id)
            if proj:
                filtered_ctx = FilteredProjectContext(proj, req.topic)
                self.writer.set_cached_context(
                    project_id=req.project_id,
                    context_txt=filtered_ctx.format_for_prompt(),
                    avoided_terms=proj.brand_profile.avoided_terms
                )

        full_markdown = f"# {outline.title}\n\n"
        previous_context = ""

        for idx, sec in enumerate(outline.sections):
            if self.is_cancelled:
                if progress_callback:
                    progress_callback("Generation cancelled.")
                break

            if progress_callback:
                progress_callback(f"Writing section {idx + 1} of {len(outline.sections)}: {sec.heading}")

            content = self.writer.write_section(sec, req, previous_context=previous_context)

            # Extract concluding thoughts to pass into next section for natural continuity
            content_lines = [
                line.strip() for line in content.splitlines()
                if line.strip() and not line.strip().startswith("#")
            ]
            previous_context = content_lines[-1] if content_lines else sec.heading

            # Use the actual heading level from the outline
            prefix = "#" * min(max(sec.level, 1), 6)
            full_markdown += f"\n{prefix} {sec.heading}\n\n{content}\n"

            # Track section sources in article sources collection
            for s in sec.sources:
                if s and s not in article.sources:
                    article.sources.append(s)

            article.sections.append(ArticleSection(
                id=sec.id,
                heading=sec.heading,
                level=sec.level,
                content=content,
                sources=sec.sources
            ))

            self._save_intermediate(article)

        article.content = full_markdown
        return article

    def finalize_article(
        self,
        article: Article,
        req: GenerationRequest,
        progress_callback: Optional[Callable] = None
    ) -> Article:
        if self.is_cancelled:
            return article

        if progress_callback:
            progress_callback("Generating FAQ...")
        faq_data = self.reviewer.generate_faq(req.topic, article.content)
        article.faq = faq_data.faqs or []

        now = datetime.datetime.now().isoformat()
        if not article.created_at:
            article.created_at = now
        article.updated_at = now

        os.makedirs("data/articles", exist_ok=True)
        path = f"data/articles/{self.run_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            f.write(article.model_dump_json(indent=2))

        # Clean up intermediate partial file to avoid duplicate listings
        partial_path = f"data/generation/{self.run_id}_partial.json"
        if os.path.exists(partial_path):
            try:
                os.remove(partial_path)
            except OSError:
                pass

        return article

    def review_article(
        self,
        article: Article,
        req: GenerationRequest,
        progress_callback: Optional[Callable] = None
    ) -> Optional[ArticleReview]:
        if self.is_cancelled:
            return None
        if progress_callback:
            progress_callback("Reviewing article...")

        avoided = []
        if req.project_id:
            proj = self.project_service.get_project(req.project_id)
            if proj:
                avoided = proj.brand_profile.avoided_terms

        return self.reviewer.review_article(
            topic=req.topic,
            content=article.content,
            avoided_terms=avoided
        )

    def _save_intermediate(self, article: Article):
        os.makedirs("data/generation", exist_ok=True)
        path = f"data/generation/{self.run_id}_partial.json"
        with open(path, "w", encoding="utf-8") as f:
            f.write(article.model_dump_json(indent=2))
