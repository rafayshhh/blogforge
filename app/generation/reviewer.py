"""Article reviewer and FAQ generator using structured LLM evaluations."""

from app.providers.base import AIProvider
from app.generation.models import ArticleReview, FAQData
from app.generation.prompts import REVIEW_PROMPT, FAQ_PROMPT, SYSTEM_DEFENSE


class ArticleReviewer:
    """Performs critical quality audits and generates contextual FAQs."""

    def __init__(self, ai_provider: AIProvider):
        self.ai = ai_provider

    def review_article(self, topic: str, content: str) -> ArticleReview:
        """Audits an article draft for repetition, gaps, and claim validity."""
        prompt = REVIEW_PROMPT.format(topic=topic, draft=content)
        return self.ai.generate_structured(
            prompt=prompt,
            response_model=ArticleReview,
            system_instructions=SYSTEM_DEFENSE
        )

    def generate_faq(self, topic: str, content: str) -> FAQData:
        """Generates relevant FAQ items from article content."""
        prompt = FAQ_PROMPT.format(topic=topic, draft=content)
        return self.ai.generate_structured(
            prompt=prompt,
            response_model=FAQData,
            system_instructions=SYSTEM_DEFENSE
        )
