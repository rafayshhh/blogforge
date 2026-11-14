"""Main desktop application window and navigation shell for BlogForge."""

import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QStackedWidget, QLabel, QComboBox
)

from app.core.constants import APP_NAME, APP_VERSION
from app.projects.service import ProjectService
from app.ui.dashboard import DashboardWidget
from app.ui.projects import ProjectsWidget
from app.ui.articles import ArticlesWidget
from app.ui.settings import SettingsWidget


class MainWindow(QMainWindow):
    """Root application window coordinating navigation views and project context."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION} — Local AI Content Studio")
        self.resize(1180, 800)

        self.project_service = ProjectService()

        # Root container
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Header / Navigation Bar
        header = QWidget()
        header.setStyleSheet("background-color: #12141A; border-bottom: 1px solid #2D313A;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 12, 24, 12)

        lbl_logo = QLabel(f"⚡ {APP_NAME}")
        lbl_logo.setStyleSheet("font-size: 18px; font-weight: bold; color: #00F0FF;")
        header_layout.addWidget(lbl_logo)

        header_layout.addSpacing(32)

        # Nav Buttons
        self.nav_buttons = []
        nav_items = ["Dashboard", "Projects", "Articles & Drafts", "Settings"]
        for idx, text in enumerate(nav_items):
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    color: #8B949E;
                    font-size: 14px;
                    padding: 8px 16px;
                }
                QPushButton:hover {
                    color: #FFFFFF;
                }
                QPushButton:checked {
                    color: #00F0FF;
                    font-weight: bold;
                    border-bottom: 2px solid #00F0FF;
                }
            """)
            btn.clicked.connect(lambda checked=False, i=idx: self.switch_tab(i))
            header_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        header_layout.addStretch()

        # Project Switcher
        header_layout.addWidget(QLabel("Active Project:"))
        self.project_switcher = QComboBox()
        self.project_switcher.setMinimumWidth(180)
        self.project_switcher.currentIndexChanged.connect(self.on_project_switched)
        header_layout.addWidget(self.project_switcher)

        root_layout.addWidget(header)

        # Stacked Views
        self.stack = QStackedWidget()
        self.dashboard_view = DashboardWidget()
        self.projects_view = ProjectsWidget(self)
        self.articles_view = ArticlesWidget(self)
        self.settings_view = SettingsWidget()

        self.stack.addWidget(self.dashboard_view)  # 0
        self.stack.addWidget(self.projects_view)   # 1
        self.stack.addWidget(self.articles_view)   # 2
        self.stack.addWidget(self.settings_view)   # 3

        # Connect internal navigation signals
        self.dashboard_view.navigate_to.connect(self.switch_tab)

        root_layout.addWidget(self.stack)

        self.refresh_project_switcher()
        self.switch_tab(0)
        self.refresh_dashboard_state()

    def switch_tab(self, index: int) -> None:
        """Switches the active stack widget and highlights the active button."""
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        if index == 0:
            self.refresh_dashboard_state()
        elif index == 2:
            self.articles_view.refresh_articles()

    def refresh_project_switcher(self) -> None:
        """Reloads available projects into the header dropdown."""
        self.project_switcher.blockSignals(True)
        self.project_switcher.clear()
        projects = self.project_service.list_projects()
        for p in projects:
            self.project_switcher.addItem(p.name, p.id)
        self.project_switcher.blockSignals(False)

    def on_project_switched(self, index: int) -> None:
        """Handles switching the global project context."""
        pid = self.project_switcher.currentData()
        if pid:
            self.projects_view.current_project_id = pid
            self.projects_view.load_project()

    def refresh_dashboard_state(self) -> None:
        """Recalculates status checklist items and article counts for the dashboard."""
        has_gemini = bool(os.getenv("GEMINI_API_KEY"))
        projects = self.project_service.list_projects()
        has_project = len(projects) > 0
        has_nextjs = any(p.nextjs_integration.enabled for p in projects)
        self.dashboard_view.update_checklist(has_gemini, has_project, has_nextjs)

        articles_count = 0
        if os.path.exists("data/articles"):
            articles_count = len([f for f in os.listdir("data/articles") if f.endswith(".json")])

        drafts_count = 0
        if os.path.exists("data/generation"):
            drafts_count = len([f for f in os.listdir("data/generation") if f.endswith(".json")])

        self.dashboard_view.update_stats(articles_count, 0, drafts_count)
