"""Article reviewer, deterministic heuristic auditor, and FAQ generator."""

import re
from typing import List, Optional
from collections import Counter

from app.providers.base import AIProvider
from app.generation.models import ArticleReview, FAQData, GenerationRequest
from app.models.article import Article
from app.generation.prompts import REVIEW_PROMPT, FAQ_PROMPT, SYSTEM_DEFENSE
from app.projects.service import ProjectService

AI_CLICHE_PATTERNS = [
    r"\bin today's fast[- ]paced\b",
    r"\bin today's interconnected\b",
    r"\bin today's rapidly evolving\b",
    r"\bdelve into\b",
    r"\bdive deep\b",
    r"\ba testament to\b",
    r"\btestament of\b",
    r"\bgame[- ]changer\b",
    r"\brevolutionize\b",
    r"\bparadigm shift\b",
    r"\btapestry\b",
    r"\bbeacon\b",
    r"\bdouble[- ]edged sword\b",
    r"\bharness the power of\b",
    r"\bit is important to remember\b",
    r"\bit is worth noting\b",
    r"\bnavigating the landscape\b",
    r"\bplethora\b",
    r"\bseamlessly integrate\b",
    r"\bdifferent ballgame\b",
    r"\bin the realm of\b",
    r"\blet's unpack\b",
    r"\bbuckle up\b",
    r"\bpanacea\b",
    r"\bsilver bullet\b",
    r"\bunlocking the potential\b",
    r"\bcrucial role\b",
    r"\bpivotal role\b",
    r"\bat the end of the day\b",
]


def detect_repeated_ngrams(text: str, n: int = 3, threshold: int = 3) -> List[str]:
    """Finds non-trivial n-grams repeated more than threshold times."""
    stop_words = {"the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "of", "with", "is", "are", "it"}
    words = [w.lower() for w in re.findall(r"\b[a-zA-Z]{3,}\b", text) if w.lower() not in stop_words]
    if len(words) < n:
        return []
    ngrams = [" ".join(words[i:i + n]) for i in range(len(words) - n + 1)]
    counts = Counter(ngrams)
    return [f"Repeated phrase '{phrase}' ({count}x)" for phrase, count in counts.items() if count >= threshold]


def detect_duplicate_paragraphs(text: str) -> List[str]:
    """Detects identical or near-identical paragraphs in the manuscript."""
    paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 30 and not p.strip().startswith("#")]
    seen = {}
    duplicates = []
    for p in paragraphs:
        norm = re.sub(r"\s+", " ", p.lower())
        if norm in seen:
            duplicates.append(f"Duplicate paragraph detected: '{p[:60]}...'")
        else:
            seen[norm] = True
    return duplicates


def check_brand_avoided_terms(text: str, avoided_terms: List[str]) -> List[str]:
    """Detects forbidden or avoided brand terminology."""
    violations = []
    for term in avoided_terms:
        if not term.strip():
            continue
        pattern = re.compile(rf"\b{re.escape(term.strip())}\b", re.IGNORECASE)
        matches = len(pattern.findall(text))
        if matches > 0:
            violations.append(f"Avoided term '{term}' appeared {matches} time(s)")
    return violations


def detect_ai_cliches(text: str) -> List[str]:
    """Scans text for common AI writing clichés."""
    cliches_found = []
    for pat in AI_CLICHE_PATTERNS:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            cliches_found.append(f"Detected AI cliché: '{match.group(0)}'")
    return cliches_found


class ArticleReviewer:
    """Performs critical quality audits combining structured LLM reviews with deterministic heuristics."""

    def __init__(self, ai_provider: AIProvider):
        self.ai = ai_provider
        self.project_service = ProjectService()

    def review_article(
        self,
        topic: str,
        content: str,
        avoided_terms: Optional[List[str]] = None
    ) -> ArticleReview:
        """Audits an article draft for repetition, gaps, clichés, and claim validity."""
        brand_rules_txt = f"Avoided terms: {', '.join(avoided_terms)}" if avoided_terms else "None"
        prompt = REVIEW_PROMPT.format(topic=topic, draft=content, brand_rules=brand_rules_txt)

        review: ArticleReview = self.ai.generate_structured(
            prompt=prompt,
            response_model=ArticleReview,
            system_instructions=SYSTEM_DEFENSE
        )

        # Deterministic heuristic augmentations
        ngram_issues = detect_repeated_ngrams(content)
        for issue in ngram_issues:
            if issue not in review.repetition_issues:
                review.repetition_issues.append(issue)

        dup_paras = detect_duplicate_paragraphs(content)
        review.duplicate_paragraphs.extend(dup_paras)

        if avoided_terms:
            violations = check_brand_avoided_terms(content, avoided_terms)
            review.brand_violations.extend(violations)

        cliches = detect_ai_cliches(content)
        for cl in cliches:
            if cl not in review.repetition_issues:
                review.repetition_issues.append(cl)
            review.suggestions.append(f"Replace cliché '{cl}' with direct, specific phrasing.")

        # Compute or adjust score deterministically
        base_score = review.overall_score if review.overall_score is not None else 85
        deductions = (len(review.brand_violations) * 10) + (len(cliches) * 5) + (len(dup_paras) * 15)
        final_score = max(min(base_score - deductions, 100), 20)

        review.overall_score = final_score
        review.quality_score = final_score

        return review

    def review(self, article: Article, req: GenerationRequest) -> ArticleReview:
        """Convenience method accepting Article and GenerationRequest."""
        avoided = []
        if req.project_id:
            proj = self.project_service.get_project(req.project_id)
            if proj:
                avoided = proj.brand_profile.avoided_terms

        return self.review_article(
            topic=req.topic,
            content=article.content,
            avoided_terms=avoided
        )

    def generate_faq(self, topic: str, content: str) -> FAQData:
        """Generates relevant FAQ items from article content."""
        prompt = FAQ_PROMPT.format(topic=topic, draft=content)
        return self.ai.generate_structured(
            prompt=prompt,
            response_model=FAQData,
            system_instructions=SYSTEM_DEFENSE
        )
