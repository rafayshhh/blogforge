"""Article section writer applying prompt constraints and context injection."""

from app.providers.base import AIProvider
from app.generation.models import OutlineSection, GenerationRequest
from app.generation.prompts import SECTION_WRITING_PROMPT
from app.projects.service import ProjectService
from app.content.context import FilteredProjectContext


class ArticleWriter:
    def __init__(self, ai_provider: AIProvider):
        self.ai_instance = ai_provider
        self.project_service = ProjectService()

    def write_section(self, section: OutlineSection, req: GenerationRequest) -> str:
        project_context_txt = "None"
        if req.project_id:
            proj = self.project_service.get_project(req.project_id)
            if proj:
                filtered_ctx = FilteredProjectContext(proj, req.topic)
                project_context_txt = filtered_ctx.format_for_prompt()

        prompt = SECTION_WRITING_PROMPT.format(
            topic=req.topic,
            project_context=project_context_txt,
            heading=section.heading,
            level=section.level,
            purpose=section.purpose,
            key_points=", ".join(str(kp) for kp in section.key_points) if section.key_points else "None",
            sources=", ".join(section.sources) if section.sources else "None",
            user_context=req.user_context or "None provided"
        )
        response = self.ai_instance.generate(prompt)
        content = response.text.strip()
        if content.startswith("```"):
            lines = content.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()
        return content
