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
        top_layout.setContentsMargins(20, 0, 20, 0)
        top_layout.setSpacing(16)

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
        self.project_switcher.setMinimumWidth(160)
        self.project_switcher.setMaximumWidth(220)
        self.project_switcher.currentIndexChanged.connect(self.on_project_switched)
        top_layout.addWidget(self.project_switcher)

        top_layout.addSpacing(16)

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
        """Reloads projects from disk into top switcher."""
        self.project_switcher.blockSignals(True)
        self.project_switcher.clear()
        projects = self.project_service.list_projects()

        for p in projects:
            self.project_switcher.addItem(p.name, p.id)

        self.project_switcher.blockSignals(False)
        self.on_project_switched()

    def on_project_switched(self) -> None:
        """Handles project dropdown selection changes."""
        proj_id = self.project_switcher.currentData()
        proj_name = self.project_switcher.currentText()
        if proj_id:
            self.dashboard_view.set_active_project_name(proj_name)
            self.status_msg.setText(f"Active Project: {proj_name}")

    def get_active_project(self) -> Optional[Project]:
        """Returns currently selected Project model."""
        proj_id = self.project_switcher.currentData()
        if proj_id:
            return self.project_service.get_project(proj_id)
        return None

    def refresh_dashboard_state(self) -> None:
        """Syncs environment status and counts with the dashboard view."""
        has_gemini = bool(os.getenv("GEMINI_API_KEY"))
        has_proj = self.project_switcher.count() > 0

        # Check if Next.js export directory is set
        active_p = self.get_active_project()
        has_nextjs = bool(
            active_p and active_p.nextjs_integration and active_p.nextjs_integration.enabled
        )

        self.dashboard_view.update_checklist(
            has_gemini=has_gemini,
            has_project=has_proj,
            has_nextjs=has_nextjs
        )

        # Count articles and drafts
        art_count = 0
        if os.path.exists("data/articles"):
            art_count = len([f for f in os.listdir("data/articles") if f.endswith(".json")])

        draft_count = 0
        if os.path.exists("data/generation"):
            draft_count = len([f for f in os.listdir("data/generation") if f.endswith(".json")])

        res_count = 0
        if os.path.exists("data/research"):
            res_count = len([f for f in os.listdir("data/research") if f.endswith(".json")])

        self.dashboard_view.update_stats(
            articles_count=art_count,
            research_count=res_count,
            drafts_count=draft_count
        )
        self.dashboard_view.load_recent_articles()

    def update_top_model_label(self) -> None:
        """Updates model text in top navigation bar."""
        model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        thinking = os.getenv("GEMINI_THINKING_LEVEL", "medium")
        self.lbl_top_model.setText(f"{model} ({thinking})")

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
