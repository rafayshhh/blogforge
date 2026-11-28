"""Research workspace widget connecting topic intelligence, search landscapes, and editorial strategy."""

import os
import uuid
import json
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QTextEdit, QTabWidget, QListWidget, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal

from app.research.engine import ResearchEngine
from app.research.providers.gemini_search import GeminiSearchProvider
from app.research.providers.mock import MockSearchProvider
from app.research.models import ResearchRun
from app.providers.factory import resolve_active_provider


class ResearchWorkerThread(QThread):
    """Background worker executing research query generation and landscape synthesis."""
    finished_research = Signal(bool, object, str)

    def __init__(
        self,
        topic: str,
        depth: str,
        api_key: Optional[str] = None,
        use_live_search: bool = True,
    ):
        super().__init__()
        self.topic = topic
        self.depth = depth
        self.api_key = api_key
        self.use_live_search = use_live_search

    def run(self):
        try:
            key_param = self.api_key if self.api_key else None
            ai_prov = resolve_active_provider(api_key=key_param)
            search_prov = (
                GeminiSearchProvider(api_key=key_param)
                if self.use_live_search
                else MockSearchProvider()
            )
            engine = ResearchEngine(ai_provider=ai_prov, search_provider=search_prov)

            run_result = engine.run_research(topic=self.topic, depth=self.depth)
            mode_label = "live Google Search grounding" if self.use_live_search else "offline mode"
            msg = f"Research completed successfully with Google Gemini ({mode_label})."
            self.finished_research.emit(True, run_result, msg)
        except Exception as e:
            self.finished_research.emit(False, None, f"Research error: {str(e)}")


class ResearchWidget(QWidget):
    """Dedicated editorial research studio for topic exploration, competitor landscape, and strategy."""

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.research_dir = "data/research"
        os.makedirs(self.research_dir, exist_ok=True)
        self.current_run: Optional[ResearchRun] = None
        self.current_run_path: Optional[str] = None
        self.worker: Optional[ResearchWorkerThread] = None

        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(28, 20, 28, 20)
        layout.setSpacing(20)

        # ---------------------------------------------------------------------
        # Left Panel: Research Controls & Query Pipeline
        # ---------------------------------------------------------------------
        left_panel = QWidget()
        left_panel.setFixedWidth(310)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        lbl_head = QLabel("RESEARCH INITIATION")
        lbl_head.setObjectName("sectionHead")
        left_layout.addWidget(lbl_head)

        lbl_topic = QLabel("Topic or Keyword Brief")
        lbl_topic.setObjectName("caption")
        left_layout.addWidget(lbl_topic)

        self.topic_input = QLineEdit()
        self.topic_input.setPlaceholderText("e.g. Serverless Architecture Trends 2026")
        self.topic_input.setFixedHeight(34)
        left_layout.addWidget(self.topic_input)

        lbl_depth = QLabel("Research Depth")
        lbl_depth.setObjectName("caption")
        left_layout.addWidget(lbl_depth)

        self.depth_combo = QComboBox()
        self.depth_combo.addItems(["Standard", "Deep", "Competitive Analysis"])
        self.depth_combo.setFixedHeight(32)
        left_layout.addWidget(self.depth_combo)

        lbl_mode = QLabel("Search Source Mode")
        lbl_mode.setObjectName("caption")
        left_layout.addWidget(lbl_mode)

        self.search_mode_combo = QComboBox()
        self.search_mode_combo.addItems([
            "Live Web Search (Google Gemini)",
            "Offline Mock Search (Deterministic)",
        ])
        self.search_mode_combo.setFixedHeight(32)
        left_layout.addWidget(self.search_mode_combo)

        self.btn_run = QPushButton("Run Topic Research")
        self.btn_run.setObjectName("primaryBtn")
        self.btn_run.setFixedHeight(36)
        self.btn_run.setCursor(Qt.PointingHandCursor)
        self.btn_run.clicked.connect(self.start_research)
        left_layout.addWidget(self.btn_run)

        self.lbl_status = QLabel("Ready for topic research.")
        self.lbl_status.setStyleSheet("color: #8C877F; font-size: 12px;")
        self.lbl_status.setWordWrap(True)
        left_layout.addWidget(self.lbl_status)

        # Generated Queries List
        lbl_queries = QLabel("GENERATED SEARCH QUERIES")
        lbl_queries.setObjectName("sectionHead")
        left_layout.addWidget(lbl_queries)

        self.queries_list = QListWidget()
        self.queries_list.setFixedHeight(110)
        left_layout.addWidget(self.queries_list)

        # Past Research Runs History
        lbl_history = QLabel("PAST RESEARCH RUNS")
        lbl_history.setObjectName("sectionHead")
        left_layout.addWidget(lbl_history)

        self.history_combo = QComboBox()
        self.history_combo.setFixedHeight(30)
        self.history_combo.currentIndexChanged.connect(self.load_selected_history_run)
        left_layout.addWidget(self.history_combo)

        history_btn_layout = QHBoxLayout()
        self.btn_del_run = QPushButton("Delete Run")
        self.btn_del_run.setObjectName("dangerBtn")
        self.btn_del_run.setFixedHeight(28)
        self.btn_del_run.clicked.connect(self.delete_selected_history_run)
        history_btn_layout.addWidget(self.btn_del_run)
        left_layout.addLayout(history_btn_layout)

        left_layout.addSpacing(10)

        # Bridge: Draft with AI Studio
        self.btn_draft_studio = QPushButton("Draft with AI Studio →")
        self.btn_draft_studio.setObjectName("primaryBtn")
        self.btn_draft_studio.setFixedHeight(34)
        self.btn_draft_studio.setCursor(Qt.PointingHandCursor)
        self.btn_draft_studio.setToolTip("Open AI Article Production Studio pre-filled with this research.")
        self.btn_draft_studio.clicked.connect(self.draft_article_from_research)
        left_layout.addWidget(self.btn_draft_studio)

        left_layout.addStretch()
        layout.addWidget(left_panel)

        # ---------------------------------------------------------------------
        # Right Panel: Landscapes, Strategy & Notes
        # ---------------------------------------------------------------------
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)

        self.tabs = QTabWidget()

        # Tab 1: Sources & Landscape
        tab_sources = QWidget()
        ts_layout = QVBoxLayout(tab_sources)
        ts_layout.setContentsMargins(16, 16, 16, 16)
        ts_layout.setSpacing(10)

        lbl_src_title = QLabel("Discovered Sources & Competitor Landscape")
        lbl_src_title.setObjectName("h2")
        ts_layout.addWidget(lbl_src_title)

        self.sources_table = QTableWidget(0, 3)
        self.sources_table.setHorizontalHeaderLabels(["Query", "Source Title", "Snippet"])
        header = self.sources_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        self.sources_table.itemSelectionChanged.connect(self.on_source_selected)
        ts_layout.addWidget(self.sources_table, 2)

        self.source_detail = QTextEdit()
        self.source_detail.setReadOnly(True)
        self.source_detail.setPlaceholderText("Select a source row above to inspect snippet and URL.")
        self.source_detail.setFixedHeight(90)
        ts_layout.addWidget(self.source_detail, 1)

        self.tabs.addTab(tab_sources, "Sources && Landscape")

        # Tab 2: Content Strategy
        tab_strategy = QWidget()
        strat_layout = QVBoxLayout(tab_strategy)
        strat_layout.setContentsMargins(16, 16, 16, 16)
        strat_layout.setSpacing(10)

        lbl_strat_title = QLabel("Synthesized Editorial Content Strategy")
        lbl_strat_title.setObjectName("h2")
        strat_layout.addWidget(lbl_strat_title)

        self.strategy_view = QTextEdit()
        self.strategy_view.setReadOnly(True)
        self.strategy_view.setPlaceholderText("Editorial angles, audience insights, and content gaps will appear here.")
        strat_layout.addWidget(self.strategy_view)

        self.tabs.addTab(tab_strategy, "Content Strategy && Angles")

        # Tab 3: Research Notes
        tab_notes = QWidget()
        notes_layout = QVBoxLayout(tab_notes)
        notes_layout.setContentsMargins(16, 16, 16, 16)
        notes_layout.setSpacing(10)

        lbl_notes_title = QLabel("Editorial Scratchpad & Research Notes")
        lbl_notes_title.setObjectName("h2")
        notes_layout.addWidget(lbl_notes_title)

        self.notes_editor = QTextEdit()
        self.notes_editor.setPlaceholderText("Record quotes, citations, key findings, and thesis outlines...")
        notes_layout.addWidget(self.notes_editor)

        notes_btn_row = QHBoxLayout()
        notes_btn_row.addStretch()
        self.btn_save_notes = QPushButton("Save Research Notes")
        self.btn_save_notes.setObjectName("primaryBtn")
        self.btn_save_notes.setFixedHeight(32)
        self.btn_save_notes.setCursor(Qt.PointingHandCursor)
        self.btn_save_notes.clicked.connect(self.save_current_notes)
        notes_btn_row.addWidget(self.btn_save_notes)
        notes_layout.addLayout(notes_btn_row)

        self.tabs.addTab(tab_notes, "Research Notes")

        right_layout.addWidget(self.tabs)
        layout.addWidget(right_panel, 1)

        self.refresh_previous_runs()

    def start_research(self):
        topic = self.topic_input.text().strip()
        if not topic:
            QMessageBox.warning(self, "Topic Required", "Please enter a topic or keyword brief to research.")
            return

        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            QMessageBox.warning(
                self, "Missing API Credentials",
                "Google Gemini API key not found. Please configure it in Settings first."
            )
            return

        self.btn_run.setEnabled(False)
        self.lbl_status.setText("Synthesizing queries & analyzing landscape...")
        self.queries_list.clear()
        self.sources_table.setRowCount(0)
        self.strategy_view.clear()

        depth = self.depth_combo.currentText()
        use_live = self.search_mode_combo.currentIndex() == 0
        self.worker = ResearchWorkerThread(
            topic=topic,
            depth=depth,
            api_key=api_key,
            use_live_search=use_live,
        )
        self.worker.finished_research.connect(self.on_research_complete)
        self.worker.start()

    def on_research_complete(self, success: bool, result, message: str):
        self.btn_run.setEnabled(True)
        self.lbl_status.setText(message)

        if not success or not result:
            QMessageBox.warning(self, "Research Failed", message)
            return

        self.current_run = result
        self.current_run_path = None
        if hasattr(self, "notes_editor"):
            existing_notes = self.notes_editor.toPlainText().strip()
            if existing_notes and not result.notes:
                result.notes = existing_notes
        self.save_research_run(result)
        self.display_research_run(result)
        self.refresh_previous_runs()
        if self.main_window and hasattr(self.main_window, "refresh_dashboard_state"):
            self.main_window.refresh_dashboard_state()

    def save_research_run(self, run: ResearchRun) -> None:
        """Persists the ResearchRun to local JSON storage."""
        target_path = getattr(self, "current_run_path", None)
        if not target_path:
            run_id = str(uuid.uuid4())
            target_path = os.path.join(self.research_dir, f"{run_id}.json")
            self.current_run_path = target_path
        os.makedirs(self.research_dir, exist_ok=True)
        try:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(run.model_dump_json(indent=2))
        except Exception:
            pass

    def save_current_notes(self) -> None:
        """Saves manual scratchpad notes into the active ResearchRun on disk."""
        if not self.current_run:
            QMessageBox.warning(
                self, "No Active Research",
                "Run or select a saved research dossier before saving notes."
            )
            return
        self.current_run.notes = self.notes_editor.toPlainText()
        self.save_research_run(self.current_run)
        self.lbl_status.setText("✓ Research notes saved locally.")

    def refresh_previous_runs(self) -> None:
        """Populates the history combo box sorted chronologically newest-first."""
        self.history_combo.blockSignals(True)
        self.history_combo.clear()
        self.history_combo.addItem("Select previous research run...", None)

        entries = []
        if os.path.exists(self.research_dir):
            for fname in os.listdir(self.research_dir):
                if fname.endswith(".json"):
                    fpath = os.path.join(self.research_dir, fname)
                    try:
                        mtime = os.path.getmtime(fpath)
                        with open(fpath, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        topic = data.get("topic", fname)
                        entries.append((mtime, topic, fpath))
                    except Exception:
                        continue

        entries.sort(key=lambda x: x[0], reverse=True)
        selected_idx = 0
        active_path = getattr(self, "current_run_path", None)
        for idx, (_, topic, fpath) in enumerate(entries, start=1):
            self.history_combo.addItem(topic, fpath)
            if active_path and fpath == active_path:
                selected_idx = idx

        self.history_combo.setCurrentIndex(selected_idx)
        self.history_combo.blockSignals(False)

    def load_selected_history_run(self) -> None:
        """Loads and displays the research run selected from the history dropdown."""
        fpath = self.history_combo.currentData()
        if not fpath or not os.path.exists(fpath):
            return
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                run = ResearchRun.model_validate_json(f.read())
            self.current_run = run
            self.current_run_path = fpath
            self.topic_input.setText(run.topic)
            self.display_research_run(run)
            self.lbl_status.setText(f"Loaded saved research for: {run.topic}")
        except Exception as e:
            QMessageBox.warning(self, "Load Error", f"Failed to load research run: {e}")

    def display_research_run(self, run: ResearchRun):
        # Restore notes if UI initialized
        if hasattr(self, "notes_editor"):
            self.notes_editor.setPlainText(run.notes or "")

        # Display queries
        self.queries_list.clear()
        for q in run.queries:
            self.queries_list.addItem(q)

        # Display sources
        self.sources_table.setRowCount(0)
        for landscape in run.search_landscape:
            for res in landscape.results:
                row = self.sources_table.rowCount()
                self.sources_table.insertRow(row)
                self.sources_table.setItem(row, 0, QTableWidgetItem(landscape.query))
                title_item = QTableWidgetItem(res.title)
                title_item.setData(int(Qt.ItemDataRole.UserRole), res.url)
                self.sources_table.setItem(row, 1, title_item)

                self.sources_table.setItem(row, 2, QTableWidgetItem(res.snippet))

        # Display strategy
        if run.strategy:
            strat = run.strategy
            gaps_text = "\n".join([f"• {g.topic}: {g.description}" for g in strat.content_gaps])
            outline_text = "\n".join([f"• {s}" for s in strat.recommended_outline])
            questions_text = "\n".join([f"• {q}" for q in strat.questions_to_answer])

            formatted_strategy = (
                f"TARGET AUDIENCE:\n{strat.audience}\n\n"
                f"RECOMMENDED ANGLE:\n{strat.recommended_angle}\n\n"
                f"IDENTIFIED CONTENT GAPS:\n{gaps_text}\n\n"
                f"CORE QUESTIONS TO ANSWER:\n{questions_text}\n\n"
                f"RECOMMENDED OUTLINE:\n{outline_text}"
            )
            self.strategy_view.setPlainText(formatted_strategy)
        else:
            self.strategy_view.setPlainText("No automated strategy synthesized for this topic.")

    def on_source_selected(self):
        selected_rows = self.sources_table.selectedItems()
        if not selected_rows:
            return
        row = self.sources_table.currentRow()
        q_item = self.sources_table.item(row, 0)
        t_item = self.sources_table.item(row, 1)
        s_item = self.sources_table.item(row, 2)

        query = q_item.text() if q_item else ""
        title = t_item.text() if t_item else ""
        snippet = s_item.text() if s_item else ""
        url = t_item.data(int(Qt.ItemDataRole.UserRole)) if t_item else ""
        url_line = f"\nURL: {url}" if url else ""

        self.source_detail.setPlainText(f"SOURCE: {title}{url_line}\nSEARCH QUERY: {query}\n\nSNIPPET:\n{snippet}")

    def delete_selected_history_run(self):
        """Permanently deletes the currently selected research run from disk."""
        fpath = self.history_combo.currentData()
        if not fpath or not os.path.exists(fpath):
            QMessageBox.warning(self, "No Run Selected", "Please select a research run to delete.")
            return

        ans = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete this research run?",
            QMessageBox.Yes | QMessageBox.No
        )
        if ans == QMessageBox.Yes:
            try:
                os.remove(fpath)
                self.current_run = None
                self.current_run_path = None
                self.queries_list.clear()
                self.sources_table.setRowCount(0)
                self.source_detail.clear()
                self.strategy_view.clear()
                self.notes_editor.clear()
                self.lbl_status.setText("Research run deleted.")
                self.refresh_previous_runs()
                if self.main_window and hasattr(self.main_window, "refresh_dashboard_state"):
                    self.main_window.refresh_dashboard_state()
            except Exception as e:
                QMessageBox.warning(self, "Delete Error", f"Failed to delete research run: {e}")

    def draft_article_from_research(self):
        """Launches AI Article Production Studio pre-filled with this research's topic and sources."""
        topic = self.topic_input.text().strip()
        if not topic and self.current_run:
            topic = self.current_run.topic

        if not topic:
            QMessageBox.warning(
                self, "Topic Required",
                "Please run or select a research topic before launching the drafting studio."
            )
            return

        sources = []
        if self.current_run:
            if self.current_run.verified_sources:
                for src in self.current_run.verified_sources[:6]:
                    sources.append(f"{src.title} ({src.canonical_url})")
            else:
                for landscape in self.current_run.search_landscape:
                    for r in landscape.results:
                        if r.title:
                            sources.append(f"{r.title} ({r.url})" if r.url else r.title)

        strategy_parts = []
        if self.current_run and self.current_run.strategy:
            strategy_parts.append(self.current_run.strategy.recommended_angle)
        notes_txt = self.notes_editor.toPlainText().strip()
        if notes_txt:
            strategy_parts.append(f"Editorial Notes: {notes_txt}")
        strategy_summary = "\n".join(strategy_parts) if strategy_parts else None

        if self.main_window and hasattr(self.main_window, "launch_article_generator_with_context"):
            self.main_window.launch_article_generator_with_context(
                topic=topic,
                sources=sources,
                strategy=strategy_summary
            )
        elif self.main_window and hasattr(self.main_window, "launch_article_generator"):
            self.main_window.launch_article_generator()

    def cleanup_threads(self) -> None:
        """Gracefully stops active background worker threads prior to widget teardown."""
        if self.worker and self.worker.isRunning():
            self.worker.wait(2000)
