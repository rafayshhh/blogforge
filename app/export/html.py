"""HTML export utility for Article models."""

from app.models.article import Article


def export_html(article: Article) -> str:
    """Exports an Article model to clean semantic HTML."""
    elements = [f"<h1>{article.title}</h1>"]

    if article.description:
        elements.append(f"<p class='description'>{article.description}</p>")

    if article.sections:
        for sec in article.sections:
            clamped_level = min(max(sec.level, 1), 6)
            elements.append(f"<h{clamped_level}>{sec.heading}</h{clamped_level}>")
            paragraphs = [p.strip() for p in sec.content.split("\n\n") if p.strip()]
            for p in paragraphs:
                elements.append(f"<p>{p}</p>")
    elif article.content:
        paragraphs = [p.strip() for p in article.content.split("\n\n") if p.strip()]
        for p in paragraphs:
            elements.append(f"<p>{p}</p>")

    if article.faq:
        elements.append("<h2>FAQ</h2>")
        elements.append("<dl class='faq'>")
        for item in article.faq:
            elements.append(f"  <dt>{item.question}</dt>")
            elements.append(f"  <dd>{item.answer}</dd>")
        elements.append("</dl>")

    return "\n".join(elements) + "\n"
