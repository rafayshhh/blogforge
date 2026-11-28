"""Google Gemini Search Grounding provider for real-time web research."""

import logging
import os
import urllib.parse
from typing import Dict, List, Optional
from google import genai
from google.genai import types

from app.core.exceptions import ProviderAuthenticationError, ProviderError
from app.research.models import SearchLandscape, SearchQuestion, SearchResult
from app.research.providers.base import SearchProvider

logger = logging.getLogger(__name__)


class GeminiSearchProvider(SearchProvider):
    """Executes live web search using Google Gemini's built-in Google Search grounding tool."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ProviderAuthenticationError("Gemini API key is required for live web search.")
        self.model: str = str(model or os.getenv("GEMINI_MODEL") or "gemini-3.8-flash")
        self.client = genai.Client(api_key=self.api_key)

    def search(self, query: str, num_results: int = 10) -> SearchLandscape:
        """Runs a Gemini query grounded in Google Search and maps results into a SearchLandscape."""
        prompt = (
            f"Research this topic thoroughly using Google Search and summarize key factual findings, "
            f"benchmarks, documentation references, and common practitioner questions:\n\nQuery: {query}"
        )
        config = types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.2,
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config,
            )
        except Exception as e:
            logger.error(f"Live Gemini web search failed for query '{query}': {e}")
            raise ProviderError(f"Live Gemini web search failed: {e}")

        response_text = (getattr(response, "text", None) or "").strip()
        candidates = getattr(response, "candidates", None) or []
        grounding_meta = getattr(candidates[0], "grounding_metadata", None) if candidates else None

        chunks = getattr(grounding_meta, "grounding_chunks", None) or []
        supports = getattr(grounding_meta, "grounding_supports", None) or []
        web_queries = list(getattr(grounding_meta, "web_search_queries", None) or [])

        # Group supporting grounded text snippets by chunk index
        snippets_by_idx: Dict[int, List[str]] = {}
        for support in supports:
            segment = getattr(support, "segment", None)
            seg_text = (getattr(segment, "text", None) or "").strip() if segment else ""
            indices = getattr(support, "grounding_chunk_indices", None) or []
            if seg_text:
                for idx in indices:
                    snippets_by_idx.setdefault(idx, []).append(seg_text)

        results: List[SearchResult] = []
        for idx, chunk in enumerate(chunks[:num_results]):
            web = getattr(chunk, "web", None)
            if not web:
                continue
            url = (getattr(web, "uri", None) or "").strip()
            title = (getattr(web, "title", None) or "").strip()
            if not url:
                continue

            domain = urllib.parse.urlparse(url).netloc or title or "web"
            chunk_snippets = snippets_by_idx.get(idx, [])
            snippet = " ".join(chunk_snippets).strip() or response_text[:280]
            results.append(SearchResult(
                title=title or domain,
                url=url,
                domain=domain,
                snippet=snippet,
                position=len(results) + 1,
            ))

        if not results and response_text:
            results.append(SearchResult(
                title=f"Gemini Grounded Synthesis: {query}",
                url="https://ai.google.dev/",
                domain="ai.google.dev",
                snippet=response_text[:500],
                position=1,
            ))

        questions = [
            SearchQuestion(question=q, source="google_search_grounding")
            for q in web_queries[:5] if isinstance(q, str) and q.strip()
        ]

        return SearchLandscape(
            query=query,
            results=results,
            related_queries=[q for q in web_queries if isinstance(q, str) and q.strip()],
            questions=questions,
        )
