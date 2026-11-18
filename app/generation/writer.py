"""Article section writer applying anti-cliché directives, flow continuity, and context injection."""

import re
from typing import Optional, List
from app.providers.base import AIProvider
from app.generation.models import OutlineSection, GenerationRequest
from app.generation.prompts import SECTION_WRITING_PROMPT, ANTI_CLICHE_RULES
from app.projects.service import ProjectService
from app.content.context import FilteredProjectContext


class ArticleWriter:
    def __init__(self, ai_provider: AIProvider):
        self.ai_instance = ai_provider
        self.project_service = ProjectService()
        self._cached_project_id: Optional[str] = None
        self._cached_context_txt: Optional[str] = None
        self._cached_avoided_terms: List[str] = []

    def set_cached_context(self, project_id: str, context_txt: str, avoided_terms: Optional[List[str]] = None):
        """Allows pipeline to pre-seed project context to avoid redundant disk I/O."""
        self._cached_project_id = project_id
        self._cached_context_txt = context_txt
        self._cached_avoided_terms = avoided_terms or []

    def write_section(
        self,
        section: OutlineSection,
        req: GenerationRequest,
        previous_context: str = ""
    ) -> str:
        project_context_txt = "None"
        avoided_terms: List[str] = []

        if req.project_id:
            if self._cached_project_id == req.project_id and self._cached_context_txt:
                project_context_txt = self._cached_context_txt
                avoided_terms = self._cached_avoided_terms
            else:
                proj = self.project_service.get_project(req.project_id)
                if proj:
                    filtered_ctx = FilteredProjectContext(proj, req.topic)
                    project_context_txt = filtered_ctx.format_for_prompt()
                    avoided_terms = proj.brand_profile.avoided_terms
                    self.set_cached_context(req.project_id, project_context_txt, avoided_terms)

        claims_txt = ", ".join(section.claims) if getattr(section, "claims", None) else "None"
        target_words = getattr(section, "target_words", 250)

        prompt = SECTION_WRITING_PROMPT.format(
            topic=req.topic,
            project_context=project_context_txt,
            heading=section.heading,
            level=section.level,
            purpose=section.purpose,
            key_points=", ".join(str(kp) for kp in section.key_points) if section.key_points else "None",
            target_words=target_words,
            previous_context=previous_context or "Beginning of article.",
            sources=", ".join(section.sources) if section.sources else "None",
            claims=claims_txt,
            user_context=req.user_context or "None provided",
            avoided_terms=", ".join(avoided_terms) if avoided_terms else "None",
            anti_cliche_rules=ANTI_CLICHE_RULES
        )

        response = self.ai_instance.generate(prompt)
        content = response.text.strip()

        # Strip markdown codeblock enclosures if present
        if content.startswith("```"):
            lines = content.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()

        # Clean any accidental leading heading duplicates matching section heading
        escaped_heading = re.escape(section.heading)
        content = re.sub(rf"^#+\s+{escaped_heading}\s*\n+", "", content, flags=re.IGNORECASE).strip()

        return content
