"""Source normalization, verification, credibility classification, and evidence grounding."""

import re
import urllib.parse
from typing import List, Tuple, Dict
from app.research.models import SearchLandscape, VerifiedSource, ClaimGrounding

TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "ref", "source", "trk", "mc_eid", "session_id", "sp_id", "igshid"
}

PRIMARY_DOMAINS = {
    "ietf.org", "rfc-editor.org", "w3.org", "arxiv.org", "doi.org", "nih.gov",
    "nist.gov", "iso.org", "acm.org", "ieee.org"
}

INSTITUTIONAL_DOMAINS = {
    "cloud.google.com", "aws.amazon.com", "azure.microsoft.com", "developer.mozilla.org",
    "kubernetes.io", "python.org", "nodejs.org", "github.com", "docker.com"
}


def canonicalize_url(url: str) -> str:
    """Normalizes URLs by stripping tracking parameters, fragments, and standardizing casing."""
    if not url or not isinstance(url, str):
        return ""
    url = url.strip()
    try:
        parsed = urllib.parse.urlsplit(url)
        scheme = parsed.scheme.lower() or "https"
        netloc = parsed.netloc.lower()
        if ":" in netloc:
            host, port = netloc.split(":", 1)
            if (scheme == "http" and port == "80") or (scheme == "https" and port == "443"):
                netloc = host

        # Strip tracking queries
        query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=False)
        clean_pairs = [(k, v) for k, v in query_pairs if k.lower() not in TRACKING_PARAMS]
        clean_query = urllib.parse.urlencode(clean_pairs)

        path = parsed.path
        if path.endswith("/") and len(path) > 1:
            path = path[:-1]

        canonical = urllib.parse.urlunsplit((scheme, netloc, path, clean_query, ""))
        return canonical
    except Exception:
        return url


def classify_credibility(domain: str, url: str) -> str:
    """Classifies source credibility into Primary, Institutional, Industry, or Secondary."""
    d = (domain or "").lower()
    u = (url or "").lower()

    if any(d.endswith(suffix) for suffix in [".gov", ".edu", ".mil"]):
        return "Primary"
    if any(p in d for p in PRIMARY_DOMAINS):
        return "Primary"
    if "/releases" in u or "/rfc" in u or "docs." in d or "spec." in d:
        return "Primary"

    if any(inst in d for inst in INSTITUTIONAL_DOMAINS) or "engineering." in d or "developer." in d:
        return "Institutional"

    if any(ind in d for ind in ["techcrunch.com", "wired.com", "theverge.com", "infoworld.com", "zdnet.com"]):
        return "Industry"

    return "Secondary"


def calculate_relevance(topic: str, query: str, title: str, snippet: str) -> float:
    """Heuristic relevance scoring based on topic and query keyword overlap."""
    stop_words = {"a", "an", "the", "and", "or", "in", "on", "for", "with", "of", "to", "is", "by", "how", "what"}
    topic_words = set(re.findall(r"\w+", (topic + " " + query).lower())) - stop_words
    if not topic_words:
        return 0.5

    text_words = set(re.findall(r"\w+", (title + " " + snippet).lower()))
    matches = topic_words.intersection(text_words)
    score = len(matches) / max(len(topic_words), 1)
    return min(max(round(score, 2), 0.1), 1.0)


def extract_claims_from_snippet(snippet: str) -> List[str]:
    """Extracts factual, data-driven, or technical assertion statements from a snippet."""
    if not snippet:
        return []
    # Split into sentences
    sentences = re.split(r"(?<=[.!?])\s+", snippet.strip())
    claims = []
    # Evidence indicators: numbers, metrics, versions, percentages, or concrete technical terms
    evidence_pattern = re.compile(
        r"(\d+(\.\d+)?%?|\b(reduces|increases|benchmarks|RFC|API|supports|deprecated|latency|ms|MB|GB)\b)",
        re.IGNORECASE
    )
    for sent in sentences:
        s = sent.strip()
        if len(s) > 20 and evidence_pattern.search(s):
            claims.append(s)
    if not claims and sentences and len(sentences[0]) > 15:
        claims.append(sentences[0])
    return claims


def deduplicate_and_verify_sources(
    landscapes: List[SearchLandscape],
    topic: str
) -> Tuple[List[VerifiedSource], List[ClaimGrounding]]:
    """Deduplicates results across search queries, canonicalizes URLs, and extracts grounded claims."""
    seen_canonical: Dict[str, VerifiedSource] = {}
    verified: List[VerifiedSource] = []
    grounded_claims: List[ClaimGrounding] = []

    for landscape in landscapes:
        for res in landscape.results:
            can_url = canonicalize_url(res.url)
            if not can_url:
                continue

            if can_url in seen_canonical:
                # Merge snippet if longer
                existing: VerifiedSource = seen_canonical[can_url]
                if len(res.snippet) > len(existing.snippet):
                    existing.snippet = res.snippet
                continue

            credibility = classify_credibility(res.domain, can_url)
            relevance = calculate_relevance(topic, landscape.query, res.title, res.snippet)
            extracted = extract_claims_from_snippet(res.snippet)

            src = VerifiedSource(
                url=res.url,
                canonical_url=can_url,
                title=res.title or res.domain,
                domain=res.domain or urllib.parse.urlparse(can_url).netloc,
                snippet=res.snippet,
                credibility=credibility,
                is_accessible=True,
                http_status=200,
                extracted_claims=extracted,
                relevance_score=relevance
            )
            seen_canonical[can_url] = src
            verified.append(src)

            for c in extracted:
                grounded_claims.append(ClaimGrounding(
                    claim=c,
                    source_id=src.id,
                    source_url=src.canonical_url,
                    source_title=src.title,
                    credibility_tier=src.credibility,
                    confidence=relevance
                ))

    # Sort sources: Primary first, then by relevance descending
    tier_order = {"Primary": 0, "Institutional": 1, "Industry": 2, "Secondary": 3}
    verified.sort(key=lambda s: (tier_order.get(s.credibility, 4), -s.relevance_score))
    return verified, grounded_claims


def format_reference_list(sources: List[VerifiedSource]) -> str:
    """Generates an editorial Markdown reference section categorized by credibility tier."""
    if not sources:
        return ""

    primary = [s for s in sources if s.credibility == "Primary"]
    institutional = [s for s in sources if s.credibility == "Institutional"]
    industry = [s for s in sources if s.credibility == "Industry"]
    secondary = [s for s in sources if s.credibility == "Secondary"]

    lines = ["\n\n## References & Verified Sources\n"]

    def _render_tier(heading: str, items: List[VerifiedSource]):
        if not items:
            return
        lines.append(f"\n### {heading}\n")
        for idx, src in enumerate(items, 1):
            lines.append(f"- [{src.title}]({src.canonical_url}) — *{src.domain}* ({src.credibility})")

    _render_tier("Primary Standards & Documentation", primary)
    _render_tier("Institutional & Architecture Reports", institutional)
    _render_tier("Industry & Technical Analysis", industry)
    _render_tier("Additional Reading", secondary)

    return "\n".join(lines) + "\n"
