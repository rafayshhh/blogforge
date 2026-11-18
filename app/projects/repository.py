"""Local JSON filesystem repository for Project persistence."""

import os
from typing import List, Optional
from app.projects.models import Project


class ProjectRepository:
    """Handles file-based JSON persistence for projects in data/projects with caching."""

    def __init__(self, data_dir: str = "data/projects"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self._cache: dict[str, tuple[float, Project]] = {}

    def _file_path(self, project_id: str) -> str:
        return os.path.join(self.data_dir, f"{project_id}.json")

    def save(self, project: Project) -> None:
        """Saves or updates a project JSON file and updates memory cache."""
        os.makedirs(self.data_dir, exist_ok=True)
        path = self._file_path(project.id)
        with open(path, "w", encoding="utf-8") as f:
            f.write(project.model_dump_json(indent=2))
        try:
            mtime = os.path.getmtime(path)
            self._cache[project.id] = (mtime, project)
        except OSError:
            pass

    def get(self, project_id: str) -> Optional[Project]:
        """Loads a project by ID from disk or cache."""
        path = self._file_path(project_id)
        if not os.path.exists(path):
            self._cache.pop(project_id, None)
            return None
        try:
            mtime = os.path.getmtime(path)
            if project_id in self._cache and self._cache[project_id][0] == mtime:
                return self._cache[project_id][1]
            with open(path, "r", encoding="utf-8") as f:
                project = Project.model_validate_json(f.read())
            self._cache[project_id] = (mtime, project)
            return project
        except Exception:
            return None

    def list_all(self) -> List[Project]:
        """Loads all projects found in the data directory using stat-validated cache."""
        if not os.path.exists(self.data_dir):
            return []
        projects = []
        try:
            with os.scandir(self.data_dir) as entries:
                for entry in entries:
                    if entry.is_file() and entry.name.endswith(".json"):
                        project_id = entry.name[:-5]
                        try:
                            stat_info = entry.stat()
                            mtime = stat_info.st_mtime
                            if project_id in self._cache and self._cache[project_id][0] == mtime:
                                projects.append(self._cache[project_id][1])
                                continue
                            with open(entry.path, "r", encoding="utf-8") as f:
                                project = Project.model_validate_json(f.read())
                            self._cache[project_id] = (mtime, project)
                            projects.append(project)
                        except Exception:
                            continue
        except OSError:
            return []
        return projects

    def delete(self, project_id: str) -> bool:
        """Removes a project file by ID and evicts from cache."""
        self._cache.pop(project_id, None)
        path = self._file_path(project_id)
        if os.path.exists(path):
            try:
                os.remove(path)
                return True
            except OSError:
                return False
        return False
