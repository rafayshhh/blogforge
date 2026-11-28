"""Main desktop application window and navigation shell for BlogForge.

Adopts an editorial desktop layout featuring a top navigation chrome,
active workspace selector, maximized writing canvas, and lightweight status bar.
"""

import os
from typing import Optional
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QStackedWidget, QLabel, QComboBox, QStatusBar, QDialog,
    QFrame
)
from PySide6.QtCore import Qt

from app.core.constants import APP_NAME, APP_VERSION
from app.projects.service import ProjectService
from app.projects.models import Project
from app.ui.dashboard import DashboardWidget
from app.ui.projects import ProjectsWidget
from app.ui.articles import ArticlesWidget
from app.ui.research import ResearchWidget
from app.ui.settings import SettingsWidget
from app.ui.components.dialogs import ArticleGeneratorDialog
from app.ui.components.tutorial import TutorialDialog


class MainWindow(QMainWindow):
    """Root application window coordinating navigation views, project context, and status."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} — Editorial Publishing Studio (v{APP_VERSION})")
        self.resize(1280, 840)
        self.setMinimumSize(960, 640)

        self.project_service = ProjectService()

        # Root container
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ---------------------------------------------------------------------
        # 1. Top Navigation Chrome & Project Switcher (48px)
        # ---------------------------------------------------------------------
        top_header = QFrame()
        top_header.setObjectName("topHeaderBar")
        top_header.setFixedHeight(48)
        top_layout = QHBoxLayout(top_header)
        top_layout.setContentsMargins(16, 0, 16, 0)
        top_layout.setSpacing(10)

        # Brand Mark
        lbl_logo = QLabel("BLOGFORGE")
        lbl_logo.setStyleSheet("""
            font-family: Georgia, serif;
            font-size: 15px;
            font-weight: 700;
            letter-spacing: 1.2px;
            color: #1C1917;
        """)
        top_layout.addWidget(lbl_logo)

        # Subtle divider
        lbl_div = QLabel("│")
        lbl_div.setStyleSheet("color: #E0DDD5; font-size: 14px;")
        top_layout.addWidget(lbl_div)

        # Project Context Selector
        proj_label = QLabel("Workspace:")
        proj_label.setStyleSheet("color: #8C877F; font-size: 12px; font-weight: 500;")
        top_layout.addWidget(proj_label)

        self.project_switcher = QComboBox()
        self.project_switcher.setFixedHeight(28)
        self.project_switcher.setMinimumWidth(140)
        self.project_switcher.setMaximumWidth(200)
        self.project_switcher.currentIndexChanged.connect(self.on_project_switched)
        top_layout.addWidget(self.project_switcher)

        top_layout.addSpacing(8)

        # Segmented Navigation Tabs
        self.nav_buttons = []
        nav_items = [
            ("Home", "Recent articles & workspace overview"),
            ("Projects", "Editorial style guide, products & links"),
            ("Writing", "Manuscript editor & publication preview"),
            ("Research", "Topic exploration, landscapes & strategy"),
            ("Settings", "AI models, API credentials & preferences")
        ]

        for idx, (title, tooltip) in enumerate(nav_items):
            btn = QPushButton(title)
            btn.setObjectName("navTabBtn")
            btn.setCheckable(True)
            btn.setToolTip(tooltip)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, i=idx: self.switch_tab(i))
            top_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        top_layout.addStretch()

        # Active Model Indicator
        self.lbl_top_model = QLabel("gemini-3.8-flash")
        self.lbl_top_model.setStyleSheet("color: #8C877F; font-size: 11px; font-family: monospace;")
        self.lbl_top_model.setToolTip("Active Google Gemini model")
        top_layout.addWidget(self.lbl_top_model)

        top_layout.addSpacing(6)

        # Quick Action: Guided Tutorial
        self.btn_top_tutorial = QPushButton("Tutorial")
        self.btn_top_tutorial.setObjectName("ghostBtn")
        self.btn_top_tutorial.setFixedHeight(28)
        self.btn_top_tutorial.setCursor(Qt.PointingHandCursor)
        self.btn_top_tutorial.setToolTip("Launch the interactive BlogForge guided tour and workflow tutorial.")
        self.btn_top_tutorial.clicked.connect(self.launch_tutorial)
        top_layout.addWidget(self.btn_top_tutorial)

        # Quick Action: AI Studio
        self.btn_top_studio = QPushButton("AI Studio")
        self.btn_top_studio.setObjectName("primaryBtn")
        self.btn_top_studio.setFixedHeight(28)
        self.btn_top_studio.setCursor(Qt.PointingHandCursor)
        self.btn_top_studio.setToolTip("Launch the interactive AI Article Production Studio.")
        self.btn_top_studio.clicked.connect(self.launch_article_generator)
        top_layout.addWidget(self.btn_top_studio)

        root_layout.addWidget(top_header)

        # ---------------------------------------------------------------------
        # 2. Main Workspace (QStackedWidget)
        # ---------------------------------------------------------------------
        self.stack = QStackedWidget()
        self.dashboard_view = DashboardWidget()
        self.projects_view = ProjectsWidget(self)
        self.articles_view = ArticlesWidget(self)
        self.research_view = ResearchWidget(self)
        self.settings_view = SettingsWidget()

        self.stack.addWidget(self.dashboard_view)  # 0: Home
        self.stack.addWidget(self.projects_view)   # 1: Projects
        self.stack.addWidget(self.articles_view)   # 2: Writing
        self.stack.addWidget(self.research_view)   # 3: Research
        self.stack.addWidget(self.settings_view)   # 4: Settings

        # Connect internal navigation signals
        self.dashboard_view.navigate_to.connect(self.switch_tab)
        self.dashboard_view.open_article_requested.connect(self.open_article_from_dashboard)
        self.settings_view.settings_updated.connect(self.on_settings_updated)

        root_layout.addWidget(self.stack, 1)

        # ---------------------------------------------------------------------
        # 3. Bottom Status Bar
        # ---------------------------------------------------------------------
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        self.status_msg = QLabel("Ready")
        self.status_msg.setStyleSheet("color: #8C877F; font-size: 11px;")
        status_bar.addWidget(self.status_msg)

        self.status_right_info = QLabel("BlogForge Local-First Studio")
        self.status_right_info.setStyleSheet("color: #8C877F; font-size: 11px; margin-right: 12px;")
        status_bar.addPermanentWidget(self.status_right_info)

        self.refresh_project_switcher()
        self.switch_tab(0)
        self.update_top_model_label()

    def switch_tab(self, index: int) -> None:
        """Switches active view and updates top tab button state."""
        if not (0 <= index < self.stack.count()):
            return
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)

        tab_names = ["Home", "Projects & Style Guide", "Editorial Writing Studio", "Research", "Settings"]
        if index < len(tab_names):
            self.status_msg.setText(f"Active View: {tab_names[index]}")

        if index == 0:
            self.refresh_dashboard_state()
        elif index == 2:
            self.articles_view.refresh_articles()

    def refresh_project_switcher(self) -> None:
        """Reloads projects from disk into top switcher, preserving active selection if present."""
        current_id = self.project_switcher.currentData()
        self.project_switcher.blockSignals(True)
        self.project_switcher.clear()
        projects = self.project_service.list_projects()

        target_idx = 0
        for idx, p in enumerate(projects):
            self.project_switcher.addItem(p.name, p.id)
            if current_id and p.id == current_id:
                target_idx = idx

        if not projects:
            self.project_switcher.addItem("No Projects", None)
        else:
            self.project_switcher.setCurrentIndex(target_idx)

        self.project_switcher.blockSignals(False)
        self.on_project_switched()

    def select_project(self, project_id: Optional[str]) -> None:
        """Selects a project by ID in the top switcher without re-entrant signals."""
        if not project_id:
            return
        for i in range(self.project_switcher.count()):
            if self.project_switcher.itemData(i) == project_id:
                if self.project_switcher.currentIndex() != i:
                    self.project_switcher.blockSignals(True)
                    self.project_switcher.setCurrentIndex(i)
                    self.project_switcher.blockSignals(False)
                    self.on_project_switched(notify_projects_view=False)
                break

    def on_project_switched(self, notify_projects_view: bool = True) -> None:
        """Handles project dropdown selection changes."""
        proj_id = self.project_switcher.currentData()
        proj_name = self.project_switcher.currentText()
        if proj_id:
            self.dashboard_view.set_active_project_name(proj_name)
            self.status_msg.setText(f"Active Project: {proj_name}")
            if notify_projects_view and hasattr(self, "projects_view"):
                self.projects_view.set_active_project_id(proj_id)
        else:
            self.dashboard_view.set_active_project_name("None")
            self.status_msg.setText("No Active Project (Create one in Projects)")

    def get_active_project(self) -> Optional[Project]:
        """Returns currently selected Project model."""
        proj_id = self.project_switcher.currentData()
        if proj_id:
            return self.project_service.get_project(proj_id)
        return None

    def open_article_from_dashboard(self, slug_or_path: str) -> None:
        """Switches to Writing Studio and selects the requested article by path or slug."""
        self.switch_tab(2)
        self.articles_view.refresh_articles()
        if os.path.exists(slug_or_path):
            self.articles_view.select_article_by_path(slug_or_path)
        else:
            self.articles_view.select_article_by_slug(slug_or_path)

    def on_settings_updated(self) -> None:
        """Reacts to provider or model changes in settings."""
        self.update_top_model_label()
        self.refresh_dashboard_state()

    def refresh_dashboard_state(self) -> None:
        """Syncs environment status and counts with the dashboard view."""
        has_key = bool(os.getenv("GEMINI_API_KEY"))

        active_p = self.get_active_project()
        has_proj = active_p is not None

        # Check if Next.js export directory is set
        has_nextjs = bool(
            active_p and active_p.nextjs_integration and active_p.nextjs_integration.enabled
        )

        self.dashboard_view.update_checklist(
            has_gemini=has_key,
            has_project=has_proj,
            has_nextjs=has_nextjs
        )

        # Build project lookup dictionary for friendly names
        projects = self.project_service.list_projects()
        project_lookup = {p.id: p.name for p in projects}

        # Count articles and drafts
        art_count = 0
        if os.path.exists("data/articles"):
            art_count = len([f for f in os.listdir("data/articles") if f.endswith(".json")])

        draft_count = 0
        if os.path.exists("data/generation"):
            draft_count = len([
                f for f in os.listdir("data/generation")
                if f.endswith(".json") and not f.endswith("_partial.json")
            ])

        res_count = 0
        if os.path.exists("data/research"):
            res_count = len([f for f in os.listdir("data/research") if f.endswith(".json")])

        self.dashboard_view.update_stats(
            articles_count=art_count,
            research_count=res_count,
            drafts_count=draft_count
        )
        self.dashboard_view.load_recent_articles(project_lookup)

    def update_top_model_label(self) -> None:
        """Updates model text in top navigation bar."""
        model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        thinking = os.getenv("GEMINI_THINKING_LEVEL", "medium")
        self.lbl_top_model.setText(f"{model} ({thinking})")
        self.lbl_top_model.setToolTip(f"Active Google Gemini model ({model})")

    def launch_tutorial(self) -> None:
        """Opens the interactive GUI tutorial walkthrough."""
        dlg = TutorialDialog(self)
        dlg.exec()

    def launch_article_generator(self) -> None:
        """Opens the AI Article Production Studio dialog."""
        active_proj = self.get_active_project()
        dlg = ArticleGeneratorDialog(self, active_project=active_proj)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            article = dlg.get_article()
            if article:
                self.switch_tab(2)
                self.articles_view.refresh_articles()
                self.articles_view.select_article_by_slug(article.slug)

    def launch_article_generator_with_context(
        self,
        topic: str,
        sources: Optional[list[str]] = None,
        strategy: Optional[str] = None
    ) -> None:
        """Opens the AI Article Production Studio pre-filled with research findings."""
        active_proj = self.get_active_project()
        dlg = ArticleGeneratorDialog(
            self,
            active_project=active_proj,
            initial_strategy=strategy,
            initial_sources=sources,
        )
        if hasattr(dlg, "topic_input") and topic:
            dlg.topic_input.setText(topic)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            article = dlg.get_article()
            if article:
                self.switch_tab(2)
                self.articles_view.refresh_articles()
                self.articles_view.select_article_by_slug(article.slug)

    def closeEvent(self, event) -> None:
        """Ensures background threads terminate cleanly on window close."""
        if hasattr(self, "settings_view") and hasattr(self.settings_view, "cleanup_threads"):
            self.settings_view.cleanup_threads()
        if hasattr(self, "research_view") and hasattr(self.research_view, "cleanup_threads"):
            self.research_view.cleanup_threads()
        super().closeEvent(event)
