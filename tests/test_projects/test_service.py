"""Unit tests for the project domain service and repository."""

import pytest

from app.projects.models import Product, InternalLink
from app.projects.repository import ProjectRepository
from app.projects.service import ProjectService


@pytest.fixture
def temp_project_service(tmp_path):
    repo = ProjectRepository(data_dir=str(tmp_path / "projects"))
    return ProjectService(repo=repo)


def test_create_and_get_project(temp_project_service):
    proj = temp_project_service.create_project(name="Alpha Project", description="Test Desc")
    assert proj.id is not None
    assert proj.name == "Alpha Project"

    fetched = temp_project_service.get_project(proj.id)
    assert fetched is not None
    assert fetched.name == "Alpha Project"
    assert fetched.description == "Test Desc"


def test_update_project(temp_project_service):
    proj = temp_project_service.create_project(name="Beta")
    proj.products.append(Product(name="Tool 1", description="A helpful tool"))
    proj.internal_links.append(InternalLink(url="/docs", title="Documentation"))

    updated = temp_project_service.update_project(proj)
    assert len(updated.products) == 1
    assert len(updated.internal_links) == 1

    fetched = temp_project_service.get_project(proj.id)
    assert len(fetched.products) == 1
    assert fetched.products[0].name == "Tool 1"


def test_archive_project(temp_project_service):
    proj = temp_project_service.create_project(name="Gamma")
    assert proj.active is True

    archived = temp_project_service.archive_project(proj.id)
    assert archived is True

    fetched = temp_project_service.get_project(proj.id)
    assert fetched.active is False

    active_projects = temp_project_service.list_projects(active_only=True)
    assert not any(p.id == proj.id for p in active_projects)


def test_internal_link_url_validation():
    with pytest.raises(ValueError, match="URL must be absolute"):
        InternalLink(url="invalid_url_without_slash", title="Bad Link")
