"""Application service orchestrating Project domain operations."""

from datetime import datetime
from typing import List, Optional
from app.projects.models import Project
from app.projects.repository import ProjectRepository


class ProjectService:
    """Provides high-level business operations for managing projects."""

    def __init__(self, repo: Optional[ProjectRepository] = None):
        self.repo = repo or ProjectRepository()

    def create_project(self, name: str, description: Optional[str] = None) -> Project:
        """Creates and persists a new project."""
        project = Project(name=name, description=description)
        self.repo.save(project)
        return project

    def update_project(self, project: Project) -> Project:
        """Updates an existing project with an updated timestamp."""
        project.updated_at = datetime.now().isoformat()
        self.repo.save(project)
        return project

    def get_project(self, project_id: str) -> Optional[Project]:
        """Retrieves a project by its unique ID."""
        return self.repo.get(project_id)

    def list_projects(self, active_only: bool = False) -> List[Project]:
        """Lists projects, optionally filtering to only active ones."""
        projects = self.repo.list_all()
        if active_only:
            return [p for p in projects if p.active]
        return projects

    def archive_project(self, project_id: str) -> bool:
        """Deactivates/archives a project."""
        project = self.repo.get(project_id)
        if not project:
            return False
        project.active = False
        self.update_project(project)
        return True

    def export_project(self, project_id: str) -> str:
        """Exports a project definition as formatted JSON."""
        project = self.repo.get(project_id)
        if not project:
            raise ValueError("Project not found")
        return project.model_dump_json(indent=2)

    def import_project(self, json_data: str) -> Project:
        """Parses and saves a project from JSON string data."""
        project = Project.model_validate_json(json_data)
        self.repo.save(project)
        return project
