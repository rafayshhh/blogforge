"""HTML export utility for Article models with safe HTML entity escaping."""

import html
import re
from app.models.article import Article


def export_html(article: Article) -> str:
    """Exports an Article model to clean, safe semantic HTML with all user content escaped."""
    elements = [f"<h1>{html.escape(article.title)}</h1>"]

    if article.description:
        elements.append(f"<p class='description'>{html.escape(article.description)}</p>")

    if article.sections:
        for sec in article.sections:
            clamped_level = min(max(sec.level, 1), 6)
            elements.append(f"<h{clamped_level}>{html.escape(sec.heading)}</h{clamped_level}>")
            paragraphs = [p.strip() for p in sec.content.split("\n\n") if p.strip()]
            for p in paragraphs:
                elements.append(f"<p>{html.escape(p)}</p>")
    elif article.content and article.content.strip():
        paragraphs = [p.strip() for p in article.content.split("\n\n") if p.strip()]
        for p in paragraphs:
            if p.startswith("#"):
                m = re.match(r"^(#{1,6})\s+(.*)$", p)
                if m:
                    lvl = len(m.group(1))
                    elements.append(f"<h{lvl}>{html.escape(m.group(2))}</h{lvl}>")
                    continue
            elements.append(f"<p>{html.escape(p)}</p>")

    if article.faq:
        elements.append("<h2>FAQ</h2>")
        elements.append("<dl class='faq'>")
        for item in article.faq:
            elements.append(f"  <dt>{html.escape(item.question)}</dt>")
            elements.append(f"  <dd>{html.escape(item.answer)}</dd>")
        elements.append("</dl>")

    return "\n".join(elements) + "\n"
