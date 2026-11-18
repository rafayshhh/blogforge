"""Extended tests for ProjectService, ProjectRepository, and Project models."""

import os
import pytest
from app.projects.models import Project, Product, InternalLink, BrandProfile, NextJSIntegration
from app.projects.repository import ProjectRepository
from app.projects.service import ProjectService


@pytest.fixture
def repo_dir(tmp_path):
    d = tmp_path / "projects_data"
    d.mkdir()
    return str(d)


@pytest.fixture
def project_service(repo_dir):
    repo = ProjectRepository(data_dir=repo_dir)
    return ProjectService(repo=repo)


def test_project_default_models():
    """Verify default sub-models on Project creation."""
    proj = Project(name="Default Project")
    assert isinstance(proj.brand_profile, BrandProfile)
    assert isinstance(proj.nextjs_integration, NextJSIntegration)
    assert proj.brand_profile.tone == "Professional"
    assert proj.nextjs_integration.enabled is False
    assert proj.products == []
    assert proj.internal_links == []
    assert proj.active is True


def test_list_projects_empty_and_populated(project_service):
    """Verify list_projects returns empty list initially and all created projects thereafter."""
    assert project_service.list_projects() == []

    project_service.create_project("Project Alpha")
    project_service.create_project("Project Beta")

    all_projs = project_service.list_projects()
    assert len(all_projs) == 2
    assert {p.name for p in all_projs} == {"Project Alpha", "Project Beta"}


def test_archive_and_active_filtering(project_service):
    """Verify active_only filtering accurately isolates archived projects."""
    p1 = project_service.create_project("Active Project")
    p2 = project_service.create_project("To Be Archived")

    assert len(project_service.list_projects(active_only=True)) == 2

    # Archive p2
    success = project_service.archive_project(p2.id)
    assert success is True

    active_list = project_service.list_projects(active_only=True)
    assert len(active_list) == 1
    assert active_list[0].id == p1.id

    # Archiving an already archived project or non-existent project
    assert project_service.archive_project("non_existent_id") is False


def test_export_and_import_project(project_service):
    """Verify project export to JSON and import into repository."""
    proj = project_service.create_project(
        name="Exportable Brand",
        description="A brand for export verification"
    )
    proj.products.append(Product(name="SaaS Cloud", description="Cloud tools"))
    proj.internal_links.append(InternalLink(url="/pricing", title="Pricing Page"))
    project_service.update_project(proj)

    json_export = project_service.export_project(proj.id)
    assert '"name": "Exportable Brand"' in json_export
    assert '"SaaS Cloud"' in json_export

    # Import into another project
    imported = project_service.import_project(json_export)
    assert imported.id == proj.id
    assert imported.name == "Exportable Brand"
    assert len(imported.products) == 1
    assert len(imported.internal_links) == 1

    # Attempting to export non-existent project
    with pytest.raises(ValueError, match="Project not found"):
        project_service.export_project("invalid_id_999")


def test_repository_delete(repo_dir):
    """Verify repository deletion removes project file from filesystem."""
    repo = ProjectRepository(data_dir=repo_dir)
    service = ProjectService(repo=repo)

    proj = service.create_project("Deletable Project")
    file_path = os.path.join(repo_dir, f"{proj.id}.json")
    assert os.path.exists(file_path)

    # Delete existing
    deleted = repo.delete(proj.id)
    assert deleted is True
    assert not os.path.exists(file_path)

    # Delete non-existent
    assert repo.delete(proj.id) is False


def test_corrupted_project_file_handling(repo_dir):
    """Verify repository gracefully skips corrupted or invalid JSON files."""
    repo = ProjectRepository(data_dir=repo_dir)
    service = ProjectService(repo=repo)

    # Create a valid project
    valid_proj = service.create_project("Valid Project")

    # Manually write a corrupted JSON file
    corrupt_file = os.path.join(repo_dir, "corrupt_proj.json")
    with open(corrupt_file, "w", encoding="utf-8") as f:
        f.write("{ invalid json content !!!")

    # Repository should load valid project and skip corrupt one
    projs = repo.list_all()
    assert len(projs) == 1
    assert projs[0].id == valid_proj.id

    # Getting corrupt project directly should return None
    assert repo.get("corrupt_proj") is None


def test_repository_nonexistent_directory(tmp_path):
    """Verify repository handles missing directory cleanly without throwing."""
    missing_dir = str(tmp_path / "does_not_exist_yet")
    repo = ProjectRepository(data_dir=missing_dir)
    assert repo.get("none") is None
    assert repo.list_all() == []


def test_persistence_across_restarts(repo_dir):
    """Verify project state persists accurately across multiple service and repository instances."""
    repo1 = ProjectRepository(data_dir=repo_dir)
    service1 = ProjectService(repo=repo1)

    proj = service1.create_project(name="Persistent Brand", description="Session 1")
    proj_id = proj.id

    # Simulate app close and restart by instantiating new repository and service
    repo2 = ProjectRepository(data_dir=repo_dir)
    service2 = ProjectService(repo=repo2)

    loaded = service2.get_project(proj_id)
    assert loaded is not None
    assert loaded.name == "Persistent Brand"
    assert loaded.description == "Session 1"
