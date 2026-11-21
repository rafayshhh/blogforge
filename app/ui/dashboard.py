"""Home workspace overview widget focused on recent documents, active project, and editorial shortcuts."""

import os
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame
)
from PySide6.QtCore import Signal, Qt


class DashboardWidget(QWidget):
    """Calm editorial home screen displaying active work, document library, and shortcuts."""
    navigate_to = Signal(int)
    open_article_requested = Signal(str)

    def __init__(self):
        super().__init__()
        self._project_lookup = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 24, 36, 24)
        layout.setSpacing(18)

        # ---------------------------------------------------------------------
        # 1. Editorial Header (Warm, understated, literary)
        # ---------------------------------------------------------------------
        header_row = QHBoxLayout()
        header_text = QVBoxLayout()
        header_text.setSpacing(3)

        lbl_welcome = QLabel("Editorial Workspace")
        lbl_welcome.setObjectName("h1")
        header_text.addWidget(lbl_welcome)

        self.lbl_workspace_meta = QLabel("Active Project: Default Workspace • Local Publishing Studio")
        self.lbl_workspace_meta.setObjectName("subtitle")
        header_text.addWidget(self.lbl_workspace_meta)

        header_row.addLayout(header_text)
        header_row.addStretch()

        # Primary Quick Actions
        actions_bar = QHBoxLayout()
        actions_bar.setSpacing(8)

        btn_new_draft = QPushButton("+ New Draft")
        btn_new_draft.setObjectName("primaryBtn")
        btn_new_draft.setFixedHeight(34)
        btn_new_draft.setCursor(Qt.PointingHandCursor)
        btn_new_draft.clicked.connect(lambda: self.navigate_to.emit(2))
        actions_bar.addWidget(btn_new_draft)

        btn_editor = QPushButton("Writing Studio")
        btn_editor.setFixedHeight(34)
        btn_editor.setCursor(Qt.PointingHandCursor)
        btn_editor.clicked.connect(lambda: self.navigate_to.emit(2))
        actions_bar.addWidget(btn_editor)

        btn_research = QPushButton("Research")
        btn_research.setFixedHeight(34)
        btn_research.setCursor(Qt.PointingHandCursor)
        btn_research.clicked.connect(lambda: self.navigate_to.emit(3))
        actions_bar.addWidget(btn_research)

        btn_projects = QPushButton("Style Guide")
        btn_projects.setFixedHeight(34)
        btn_projects.setCursor(Qt.PointingHandCursor)
        btn_projects.clicked.connect(lambda: self.navigate_to.emit(1))
        actions_bar.addWidget(btn_projects)

        header_row.addLayout(actions_bar)
        layout.addLayout(header_row)

        # ---------------------------------------------------------------------
        # 2. Workspace Status & Summary Strip (Quiet, non-intrusive)
        # ---------------------------------------------------------------------
        status_strip = QFrame()
        status_strip.setObjectName("statusStrip")
        status_strip.setStyleSheet("""
            #statusStrip {
                background-color: #F4F1EA;
                border: 1px solid #E0DDD5;
                border-radius: 6px;
            }
            #statusStrip QLabel {
                background-color: transparent;
                border: none;
                border-radius: 0px;
                padding: 0px;
            }
        """)
        strip_layout = QHBoxLayout(status_strip)
        strip_layout.setContentsMargins(14, 8, 14, 8)
        strip_layout.setSpacing(20)

        # Readiness Checklist indicators
        readiness_box = QHBoxLayout()
        readiness_box.setSpacing(14)

        self.chk_gemini = QLabel("● Gemini API Configured")
        self.chk_gemini.setStyleSheet("color: #15803D; font-size: 12px; font-weight: 500;")
        readiness_box.addWidget(self.chk_gemini)

        self.chk_project = QLabel("● Project Active")
        self.chk_project.setStyleSheet("color: #15803D; font-size: 12px; font-weight: 500;")
        readiness_box.addWidget(self.chk_project)

        self.chk_nextjs = QLabel("○ Next.js Sync Optional")
        self.chk_nextjs.setStyleSheet("color: #8C877F; font-size: 12px;")
        readiness_box.addWidget(self.chk_nextjs)

        strip_layout.addLayout(readiness_box)
        strip_layout.addStretch()

        # Content Summary Counters (preserved for test contracts)
        summary_box = QHBoxLayout()
        summary_box.setSpacing(16)

        self.stat_labels = {}
        for metric in ["Articles", "Drafts", "Research"]:
            lbl_val = QLabel("0")
            lbl_val.setStyleSheet("font-weight: 700; color: #1C1917; font-size: 12px;")
            self.stat_labels[metric] = lbl_val

            lbl_txt = QLabel(f"{metric}:")
            lbl_txt.setStyleSheet("color: #57534E; font-size: 12px;")

            item_box = QHBoxLayout()
            item_box.setSpacing(4)
            item_box.addWidget(lbl_txt)
            item_box.addWidget(lbl_val)
            summary_box.addLayout(item_box)

        strip_layout.addLayout(summary_box)
        layout.addWidget(status_strip)

        # ---------------------------------------------------------------------
        # 3. Recent Articles & Editorial Drafts (Core work area)
        # ---------------------------------------------------------------------
        doc_header = QHBoxLayout()
        lbl_recent = QLabel("RECENT ARTICLES & EDITORIAL DRAFTS")
        lbl_recent.setObjectName("sectionHead")
        doc_header.addWidget(lbl_recent)
        doc_header.addStretch()

        btn_refresh_docs = QPushButton("Refresh List")
        btn_refresh_docs.setObjectName("ghostBtn")
        btn_refresh_docs.setFixedHeight(26)
        btn_refresh_docs.clicked.connect(self.load_recent_articles)
        doc_header.addWidget(btn_refresh_docs)
        layout.addLayout(doc_header)

        # Clean Table on White Paper
        self.doc_table = QTableWidget(0, 5)
        self.doc_table.setHorizontalHeaderLabels(["Title", "Status", "Word Count", "Target Project", "Actions"])
        header = self.doc_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.doc_table.cellClicked.connect(self._on_doc_cell_clicked)
        self.doc_table.cellDoubleClicked.connect(lambda r, c: self._on_doc_cell_clicked(r, 4))
        layout.addWidget(self.doc_table, 1)

        # Empty State Message
        self.empty_state_frame = QFrame()
        self.empty_state_frame.setObjectName("emptyStateFrame")
        self.empty_state_frame.setStyleSheet("""
            #emptyStateFrame {
                background-color: #FFFFFF;
                border: 1px dashed #D6D3D1;
                border-radius: 6px;
                padding: 32px;
            }
            #emptyStateFrame QLabel {
                background-color: transparent;
                border: none;
                border-radius: 0px;
                padding: 0px;
            }
        """)
        empty_layout = QVBoxLayout(self.empty_state_frame)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setSpacing(8)

        lbl_empty_title = QLabel("No articles found in current project")
        lbl_empty_title.setStyleSheet("font-family: Georgia; font-size: 16px; font-weight: 600; color: #1C1917;")
        empty_layout.addWidget(lbl_empty_title, alignment=Qt.AlignmentFlag.AlignCenter)

        lbl_empty_desc = QLabel(
            "Start by drafting a new article in the Writing Studio, or explore topics in the Research Workspace."
        )
        lbl_empty_desc.setStyleSheet("color: #8C877F; font-size: 13px;")
        empty_layout.addWidget(lbl_empty_desc, alignment=Qt.AlignmentFlag.AlignCenter)

        btn_empty_start = QPushButton("+ Create First Draft")
        btn_empty_start.setObjectName("primaryBtn")
        btn_empty_start.setFixedHeight(32)
        btn_empty_start.clicked.connect(lambda: self.navigate_to.emit(2))
        empty_layout.addWidget(btn_empty_start, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.empty_state_frame)
        self.empty_state_frame.hide()

    def update_stats(self, articles_count: int, research_count: int, drafts_count: int) -> None:
        """Updates the quiet workspace counter indicators."""
        if "Articles" in self.stat_labels:
            self.stat_labels["Articles"].setText(str(articles_count))
        if "Research" in self.stat_labels:
            self.stat_labels["Research"].setText(str(research_count))
        if "Drafts" in self.stat_labels:
            self.stat_labels["Drafts"].setText(str(drafts_count))

    def _on_doc_cell_clicked(self, row: int, col: int) -> None:
        """Handles table clicks, routing Open action with target article filepath or slug."""
        if col in (0, 4):
            item = self.doc_table.item(row, 0)
            target = item.data(int(Qt.ItemDataRole.UserRole)) if item else None
            if target:
                self.open_article_requested.emit(str(target))
            else:
                self.navigate_to.emit(2)

    def update_checklist(
        self,
        has_gemini: bool,
        has_project: bool,
        has_nextjs: bool,
        provider_name: str = "Gemini"
    ) -> None:
        """Updates the system readiness indicators with multi-provider awareness."""
        display_prov = provider_name.capitalize()
        if has_gemini:
            self.chk_gemini.setText(f"● {display_prov} Configured")
            self.chk_gemini.setStyleSheet("color: #15803D; font-size: 12px; font-weight: 500;")
        else:
            self.chk_gemini.setText(f"○ {display_prov} Missing")
            self.chk_gemini.setStyleSheet("color: #B91C1C; font-size: 12px;")

        if has_project:
            self.chk_project.setText("● Project Active")
            self.chk_project.setStyleSheet("color: #15803D; font-size: 12px; font-weight: 500;")
        else:
            self.chk_project.setText("○ No Project Selected")
            self.chk_project.setStyleSheet("color: #B45309; font-size: 12px;")

        if has_nextjs:
            self.chk_nextjs.setText("● Next.js Connected")
            self.chk_nextjs.setStyleSheet("color: #15803D; font-size: 12px; font-weight: 500;")
        else:
            self.chk_nextjs.setText("○ Next.js Sync Off")
            self.chk_nextjs.setStyleSheet("color: #8C877F; font-size: 12px;")

    def set_active_project_name(self, name: str) -> None:
        self.lbl_workspace_meta.setText(f"Active Workspace: {name} • Local Publishing Studio")

    def load_recent_articles(self, project_lookup: dict | None = None) -> None:
        """Reads articles and drafts from local storage and populates the recent work table chronologically."""
        if project_lookup is not None:
            self._project_lookup = project_lookup

        self.doc_table.setRowCount(0)

        # Collect items from both published articles and drafts
        collected_entries = []
        directories = [("data/articles", False), ("data/generation", True)]

        for directory, is_draft in directories:
            if os.path.exists(directory):
                for filename in os.listdir(directory):
                    if filename.endswith(".json") and not filename.endswith("_partial.json"):
                        filepath = os.path.join(directory, filename)
                        try:
                            mtime = os.path.getmtime(filepath)
                            with open(filepath, "r", encoding="utf-8") as f:
                                data = json.load(f)
                            collected_entries.append((mtime, filepath, is_draft, data))
                        except Exception:
                            continue

        if not collected_entries:
            self.doc_table.hide()
            self.empty_state_frame.show()
            return

        self.doc_table.show()
        self.empty_state_frame.hide()

        # Sort chronologically by latest modification
        collected_entries.sort(key=lambda x: x[0], reverse=True)

        for _, filepath, is_draft, data in collected_entries[:15]:
            try:
                title = data.get("title") or os.path.basename(filepath)
                content = data.get("content", "")
                word_count = len(content.split()) if content else 0
                proj_id = data.get("project_id")

                # Resolve project friendly name without leaking raw UUIDs
                if not proj_id or proj_id in ("default", "Default"):
                    proj_display = "Default Workspace"
                elif proj_id in self._project_lookup:
                    proj_display = self._project_lookup[proj_id]
                else:
                    proj_display = "Unassigned"

                row = self.doc_table.rowCount()
                self.doc_table.insertRow(row)

                title_item = QTableWidgetItem(title)
                # Store filepath in user role so opening by exact file is guaranteed
                title_item.setData(int(Qt.ItemDataRole.UserRole), filepath)
                self.doc_table.setItem(row, 0, title_item)

                # Status pill
                if is_draft:
                    status_str = "Draft"
                else:
                    status_str = "Draft" if word_count < 300 else "Completed"
                status_item = QTableWidgetItem(status_str)
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.doc_table.setItem(row, 1, status_item)

                self.doc_table.setItem(row, 2, QTableWidgetItem(f"{word_count:,} words"))
                self.doc_table.setItem(row, 3, QTableWidgetItem(proj_display))

                # Action column
                act_item = QTableWidgetItem("Open →")
                act_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.doc_table.setItem(row, 4, act_item)
            except Exception:
                continue
