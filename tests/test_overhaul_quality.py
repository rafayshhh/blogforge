"""Comprehensive QA and validation tests for performance, source verification, anti-cliché filters, and diagnostics."""

import os
from unittest.mock import MagicMock, patch
from app.research.sources import (
    canonicalize_url,
    classify_credibility,
    extract_claims_from_snippet,
    deduplicate_and_verify_sources,
    format_reference_list
)
from app.research.models import SearchLandscape, SearchResult, VerifiedSource
from app.generation.reviewer import (
    detect_repeated_ngrams,
    detect_duplicate_paragraphs,
    check_brand_avoided_terms,
    detect_ai_cliches,
    ArticleReviewer
)
from app.generation.models import ArticleReview
from app.providers.gemini import GeminiProvider
from app.core.config import save_config_value


def test_url_canonicalization_and_tracking_removal():
    """Verify tracking parameters and fragments are stripped from URLs."""
    raw_url = "https://example.com/blog/guide?utm_source=twitter&utm_medium=social&fbclid=12345&id=99#section-2"
    canonical = canonicalize_url(raw_url)
    assert "utm_source" not in canonical
    assert "fbclid" not in canonical
    assert "#section-2" not in canonical
    assert "id=99" in canonical
    assert canonical == "https://example.com/blog/guide?id=99"

    # Trailing slash normalization
    assert canonicalize_url("https://example.com/docs/") == "https://example.com/docs"
    # Port normalization
    assert canonicalize_url("https://example.com:443/api") == "https://example.com/api"


def test_source_credibility_tiering():
    """Verify domains and path patterns are categorized into proper credibility tiers."""
    assert classify_credibility("nist.gov", "https://nist.gov/publications") == "Primary"
    assert classify_credibility("rfc-editor.org", "https://rfc-editor.org/rfc/rfc9110.txt") == "Primary"
    assert classify_credibility("arxiv.org", "https://arxiv.org/abs/2301.00000") == "Primary"
    assert classify_credibility("github.com", "https://github.com/org/repo/releases/v1.0") == "Primary"

    assert classify_credibility("cloud.google.com", "https://cloud.google.com/architecture") == "Institutional"
    assert classify_credibility("aws.amazon.com", "https://aws.amazon.com/blogs/architecture") == "Institutional"
    assert classify_credibility("kubernetes.io", "https://kubernetes.io/docs/concepts") == "Institutional"

    assert classify_credibility("techcrunch.com", "https://techcrunch.com/article") == "Industry"
    assert classify_credibility("medium.com", "https://medium.com/@user/post") == "Secondary"
    assert classify_credibility("randomblog.xyz", "https://randomblog.xyz/tips") == "Secondary"


def test_claim_extraction_from_snippets():
    """Verify numeric data, metrics, and empirical technical assertions are extracted."""
    snippet_1 = "The v2 architecture reduces API latency by 45% under 10k QPS load. Setup takes minutes."
    claims = extract_claims_from_snippet(snippet_1)
    assert len(claims) >= 1
    assert "reduces API latency by 45%" in claims[0]

    empty_snippet = ""
    assert extract_claims_from_snippet(empty_snippet) == []


def test_deduplicate_and_verify_sources():
    """Verify duplicate search results across queries are merged and ranked by credibility."""
    landscapes = [
        SearchLandscape(
            query="serverless performance",
            results=[
                SearchResult(
                    title="Docs",
                    url="https://docs.docker.com/guide/?utm_source=seo",
                    domain="docs.docker.com",
                    snippet="Docker reduces cold start latency by 30%."
                ),
                SearchResult(
                    title="Blog Post",
                    url="https://medium.com/post-1",
                    domain="medium.com",
                    snippet="A nice blog about serverless."
                )
            ]
        ),
        SearchLandscape(
            query="docker cold starts",
            results=[
                SearchResult(
                    title="Docs Duplicate",
                    url="https://docs.docker.com/guide/",
                    domain="docs.docker.com",
                    snippet="Docker reduces cold start latency by 30% and memory footprint by 50MB."
                ),
            ]
        )
    ]

    verified, claims = deduplicate_and_verify_sources(landscapes, "serverless performance")

    # Should deduplicate docs.docker.com
    assert len(verified) == 2
    # Primary/Institutional ranked ahead of Secondary
    assert verified[0].credibility in ("Primary", "Institutional")
    assert verified[0].domain == "docs.docker.com"
    # Grounded claims extracted
    assert any("cold start" in c.claim for c in claims)


def test_anti_cliche_and_ngram_auditor():
    """Verify deterministic detection of AI clichés, repeated phrases, and avoided terms."""
    cliche_text = (
        "In today's fast-paced digital world, serverless computing has emerged as a game-changer. "
        "It is a testament to modern engineering. Let us delve into the details."
    )
    cliches = detect_ai_cliches(cliche_text)
    assert len(cliches) >= 3
    assert any("in today's fast-paced" in c.lower() for c in cliches)
    assert any("game-changer" in c.lower() for c in cliches)
    assert any("delve into" in c.lower() for c in cliches)

    # N-gram repetition
    repeated_text = (
        "zero downtime deployment is critical. Every zero downtime deployment requires "
        "canary testing for zero downtime deployment."
    )
    repeated = detect_repeated_ngrams(repeated_text, n=3, threshold=3)
    assert len(repeated) >= 1
    assert "zero downtime deployment" in repeated[0].lower()

    # Avoided brand terms
    avoided_terms = ["synergy", "paradigm shift", "leverage"]
    doc_text = "We will leverage new tooling to achieve corporate synergy across teams."
    violations = check_brand_avoided_terms(doc_text, avoided_terms)
    assert len(violations) == 2
    assert any("leverage" in v for v in violations)
    assert any("synergy" in v for v in violations)


def test_duplicate_paragraph_detection():
    """Verify exact duplicate paragraphs are caught."""
    text = (
        "This is paragraph one with plenty of details and explanation.\n\n"
        "This is paragraph two explaining architectural tradeoffs.\n\n"
        "This is paragraph one with plenty of details and explanation.\n\n"
    )
    duplicates = detect_duplicate_paragraphs(text)
    assert len(duplicates) == 1
    assert "Duplicate paragraph detected" in duplicates[0]


def test_article_reviewer_deterministic_scoring():
    """Verify ArticleReviewer docks points deterministically for brand violations and clichés."""
    mock_ai = MagicMock()
    mock_ai.generate_structured.return_value = ArticleReview(
        unsupported_claims=[],
        repetition_issues=[],
        overall_score=95
    )

    reviewer = ArticleReviewer(mock_ai)
    dirty_content = (
        "In today's fast-paced digital world, our software is a game-changer. "
        "We leverage synergy to build better pipelines."
    )
    review = reviewer.review_article(
        topic="Modern Software",
        content=dirty_content,
        avoided_terms=["synergy", "leverage"]
    )

    # Score should be docked for 2 avoided terms and 2 cliches
    assert review.overall_score < 95
    assert len(review.brand_violations) == 2
    assert len(review.suggestions) >= 2


def test_gemini_diagnose_connection_error_mapping():
    """Verify diagnose_connection accurately categorizes failure codes."""
    # Missing key
    ok, msg, details = GeminiProvider.diagnose_connection(api_key="")
    assert ok is False
    assert details["status"] == "MISSING_KEY"

    # Mocked 401 error
    with patch("google.genai.Client") as mock_client:
        mock_instance = MagicMock()
        mock_instance.models.list.side_effect = Exception("401 API_KEY_INVALID: User key not recognized")
        mock_client.return_value = mock_instance

        ok, msg, details = GeminiProvider.diagnose_connection(api_key="BAD_KEY")
        assert ok is False
        assert details["status"] == "AUTHENTICATION_FAILED"
        assert "401" in msg

    # Mocked 429 quota error
    with patch("google.genai.Client") as mock_client:
        mock_instance = MagicMock()
        mock_instance.models.list.side_effect = Exception("429 RESOURCE_EXHAUSTED: Quota exceeded")
        mock_client.return_value = mock_instance

        ok, msg, details = GeminiProvider.diagnose_connection(api_key="VALID_KEY")
        assert ok is False
        assert details["status"] == "QUOTA_EXHAUSTED"
        assert "quota" in msg.lower()


def test_config_value_persistence(tmp_path):
    """Verify save_config_value updates existing lines and appends new ones safely."""
    test_env = str(tmp_path / ".env.test")
    with open(test_env, "w", encoding="utf-8") as f:
        f.write("# Environment settings\nEXISTING_VAR=initial\n")

    save_config_value("EXISTING_VAR", "updated", env_path=test_env)
    save_config_value("NEW_VAR", "added_value", env_path=test_env)

    with open(test_env, "r", encoding="utf-8") as f:
        content = f.read()

    assert "EXISTING_VAR=updated" in content
    assert "NEW_VAR=added_value" in content
    assert "# Environment settings" in content
    assert os.getenv("EXISTING_VAR") == "updated"
    assert os.getenv("NEW_VAR") == "added_value"


def test_format_reference_list():
    """Verify references are grouped into hierarchical credibility sections."""
    sources = [
        VerifiedSource(
            url="https://w3.org/TR/spec",
            canonical_url="https://w3.org/TR/spec",
            title="W3C Spec",
            domain="w3.org",
            snippet="...",
            credibility="Primary"
        ),
        VerifiedSource(
            url="https://cloud.google.com/doc",
            canonical_url="https://cloud.google.com/doc",
            title="Google Cloud Guide",
            domain="cloud.google.com",
            snippet="...",
            credibility="Institutional"
        ),
        VerifiedSource(
            url="https://techcrunch.com/tech",
            canonical_url="https://techcrunch.com/tech",
            title="Tech Crunch News",
            domain="techcrunch.com",
            snippet="...",
            credibility="Industry"
        )
    ]
    ref_md = format_reference_list(sources)
    assert "## References & Verified Sources" in ref_md
    assert "### Primary Standards & Documentation" in ref_md
    assert "### Institutional & Architecture Reports" in ref_md
    assert "### Industry & Technical Analysis" in ref_md
    assert "[W3C Spec](https://w3.org/TR/spec)" in ref_md
