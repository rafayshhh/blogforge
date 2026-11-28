"""Outline generator utilizing AI structured output with anti-cliché directives."""

from app.providers.base import AIProvider
from app.generation.models import GenerationRequest, ArticleOutline
from app.generation.prompts import OUTLINE_GENERATION_PROMPT, ANTI_CLICHE_RULES, SYSTEM_DEFENSE
from app.projects.service import ProjectService
from app.content.context import FilteredProjectContext


class OutlineGenerator:
    """Generates structured article outlines according to project brand context."""

    def __init__(self, ai_provider: AIProvider):
        self.ai = ai_provider
        self.project_service = ProjectService()

    def generate(self, req: GenerationRequest) -> ArticleOutline:
        """Constructs and executes outline generation."""
        project_context_txt = "None"
        if req.project_id:
            proj = self.project_service.get_project(req.project_id)
            if proj:
                filtered_ctx = FilteredProjectContext(proj, req.topic)
                project_context_txt = filtered_ctx.format_for_prompt()

        prompt = OUTLINE_GENERATION_PROMPT.format(
            project_context=project_context_txt,
            topic=req.topic,
            audience=req.audience or "General Audience",
            content_type=req.content_type or "Article",
            tone=req.tone or "Project default",
            target_word_count=req.target_word_count or req.word_count_target or 1200,
            keywords=", ".join(req.keywords) if req.keywords else "None",
            verified_sources=", ".join(req.verified_sources) if req.verified_sources else "None",
            strategy=req.strategy or "None",
            user_context=req.user_context or "None",
            anti_cliche_rules=ANTI_CLICHE_RULES
        )

        return self.ai.generate_structured(
            prompt=prompt,
            response_model=ArticleOutline,
            system_instructions=SYSTEM_DEFENSE
        )
