"""Topic-aware contextual filtering for project brand, products, and links."""

import re
from typing import Optional, List
from app.projects.models import Project, Product, InternalLink


class FilteredProjectContext:
    """Selectively extracts and formats project brand details relevant to a specific topic."""

    def __init__(self, project: Project, topic: Optional[str] = None):
        self.project = project
        self.topic = (topic or "").strip()
        self.brand = project.brand_profile
        self.products: List[Product] = self._filter_products()
        self.internal_links: List[InternalLink] = self._filter_internal_links()

    def _tokenize(self, text: str) -> set[str]:
        return set(re.findall(r"\w+", text.lower()))

    def _filter_products(self) -> List[Product]:
        active_products = [p for p in self.project.products if p.status.lower() == "active"]
        if len(active_products) <= 5 or not self.topic:
            return active_products

        topic_tokens = self._tokenize(self.topic)
        matched = []
        for prod in active_products:
            prod_text = f"{prod.name} {prod.description or ''} {' '.join(prod.features)}"
            prod_tokens = self._tokenize(prod_text)
            if topic_tokens.intersection(prod_tokens):
                matched.append(prod)

        return matched if matched else active_products[:5]

    def _filter_internal_links(self) -> List[InternalLink]:
        active_links = [link for link in self.project.internal_links if link.active]
        if len(active_links) <= 5 or not self.topic:
            return active_links

        topic_tokens = self._tokenize(self.topic)
        matched = []
        for link in active_links:
            link_text = f"{link.title} {link.url} {' '.join(link.keywords)}"
            link_tokens = self._tokenize(link_text)
            if topic_tokens.intersection(link_tokens):
                matched.append(link)

        return matched if matched else active_links[:5]

    def format_for_prompt(self) -> str:
        """Formats the context into a clean text block for inclusion in LLM prompts."""
        lines = [
            f"Brand: {self.project.name}",
            f"Tone: {self.brand.tone}",
            f"Style: {self.brand.writing_style}",
            f"Target Audience: {self.brand.target_audience or 'General audience'}"
        ]

        if self.brand.preferred_terms:
            lines.append(f"Preferred Terms: {', '.join(self.brand.preferred_terms)}")
        if self.brand.avoided_terms:
            lines.append(f"Avoided Terms: {', '.join(self.brand.avoided_terms)}")
        if self.brand.content_rules:
            lines.append(f"Content Rules: {'; '.join(self.brand.content_rules)}")

        if self.products:
            lines.append("\nRelevant Products/Services to mention naturally where appropriate:")
            for p in self.products:
                desc = f": {p.description}" if p.description else ""
                url = f" ({p.url})" if p.url else ""
                lines.append(f"- {p.name}{url}{desc}")

        if self.internal_links:
            lines.append("\nRelevant Internal URLs to link where contextually helpful:")
            for link in self.internal_links:
                lines.append(f"- {link.title}: {link.url}")

        return "\n".join(lines)
