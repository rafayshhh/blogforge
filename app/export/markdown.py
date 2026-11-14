"""Markdown export utility for Article models."""

from app.models.article import Article


def export_markdown(article: Article) -> str:
    """Exports an Article model to formatted Markdown text."""
    parts = [f"# {article.title}"]

    if article.description:
        parts.append(f"\n> {article.description}\n")

    if article.sections:
        for sec in article.sections:
            clamped_level = min(max(sec.level, 1), 6)
            hashes = "#" * clamped_level
            parts.append(f"\n{hashes} {sec.heading}\n\n{sec.content.strip()}\n")
    elif article.content:
        parts.append(f"\n{article.content.strip()}\n")

    if article.faq:
        parts.append("\n## FAQ\n")
        for item in article.faq:
            parts.append(f"\n**{item.question}**\n\n{item.answer}\n")

    return "\n".join(parts).strip() + "\n"
