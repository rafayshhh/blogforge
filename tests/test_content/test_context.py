from app.projects.models import Project, Product, InternalLink
from app.content.context import FilteredProjectContext


def test_filtered_context():
    p = Project(name="Test")
    # Add dummy products to exceed the threshold of 5
    for i in range(5):
        p.products.append(Product(name=f"Dummy {i}", description="Nothing", status="Active"))
        p.internal_links.append(InternalLink(url=f"/dummy{i}", title=f"Dummy {i}"))

    p.products.append(Product(name="Image Resizer", description="Resizes images", status="Active"))
    p.products.append(Product(name="PDF Compressor", description="Compresses PDFs", status="Active"))
    p.internal_links.append(InternalLink(url="/pdf", title="PDF Tool"))

    ctx = FilteredProjectContext(p, "How to compress PDF files")

    assert any(prod.name == "PDF Compressor" for prod in ctx.products)

    prompt_str = ctx.format_for_prompt()
    assert "PDF Compressor" in prompt_str
    assert "Image Resizer" not in prompt_str
    assert "/pdf" in prompt_str
