"""JSON export utility for Article models."""

from app.models.article import Article


def export_json(article: Article) -> str:
    """Exports an Article model to formatted JSON string."""
    return article.model_dump_json(indent=2)
