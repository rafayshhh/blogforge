"""Local JSON filesystem repository for Project persistence."""

import os
from typing import List, Optional
from app.projects.models import Project


class ProjectRepository:
    """Handles file-based JSON persistence for projects in data/projects."""

    def __init__(self, data_dir: str = "data/projects"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

    def _file_path(self, project_id: str) -> str:
        return os.path.join(self.data_dir, f"{project_id}.json")

    def save(self, project: Project) -> None:
        """Saves or updates a project JSON file."""
        os.makedirs(self.data_dir, exist_ok=True)
        path = self._file_path(project.id)
        with open(path, "w", encoding="utf-8") as f:
            f.write(project.model_dump_json(indent=2))

    def get(self, project_id: str) -> Optional[Project]:
        """Loads a project by ID from disk."""
        path = self._file_path(project_id)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return Project.model_validate_json(f.read())
        except Exception:
            return None

    def list_all(self) -> List[Project]:
        """Loads all projects found in the data directory."""
        if not os.path.exists(self.data_dir):
            return []
        projects = []
        for fname in os.listdir(self.data_dir):
            if fname.endswith(".json"):
                path = os.path.join(self.data_dir, fname)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        projects.append(Project.model_validate_json(f.read()))
                except Exception:
                    continue
        return projects

    def delete(self, project_id: str) -> bool:
        """Removes a project file by ID."""
        path = self._file_path(project_id)
        if os.path.exists(path):
            try:
                os.remove(path)
                return True
            except OSError:
                return False
        return False
