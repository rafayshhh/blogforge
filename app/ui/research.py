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
from app.research.providers.mock import MockSearchProvider
from app.research.models import ResearchRun
from app.providers.factory import resolve_active_provider
from app.core.config import get_active_provider_name


class ResearchWorkerThread(QThread):
    """Background worker executing research query generation and landscape synthesis."""
    finished_research = Signal(bool, object, str)

    def __init__(self, topic: str, depth: str, api_key: Optional[str] = None):
        super().__init__()
        self.topic = topic
        self.depth = depth
        self.api_key = api_key

    def run(self):
        try:
            p_name = get_active_provider_name()
            key_param = self.api_key if self.api_key else None
            ai_prov = resolve_active_provider(provider_name=p_name, api_key=key_param)
            search_prov = MockSearchProvider()
            engine = ResearchEngine(ai_provider=ai_prov, search_provider=search_prov)

            run_result = engine.run_research(topic=self.topic, depth=self.depth)
            msg = f"Research completed successfully with {p_name.capitalize()}."
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

        self.tabs.addTab(tab_sources, "Sources & Landscape")

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

        self.tabs.addTab(tab_strategy, "Content Strategy & Angles")

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

        self.tabs.addTab(tab_notes, "Research Notes")

        right_layout.addWidget(self.tabs)
        layout.addWidget(right_panel, 1)

        self.refresh_previous_runs()

    def start_research(self):
        topic = self.topic_input.text().strip()
        if not topic:
            QMessageBox.warning(self, "Topic Required", "Please enter a topic or keyword brief to research.")
            return

        p_name = get_active_provider_name()
        api_key = None
        if p_name == "gemini":
            api_key = os.getenv("GEMINI_API_KEY", "")
        elif p_name == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY", "")
        elif p_name == "openai":
            api_key = os.getenv("OPENAI_API_KEY", "")
        elif p_name == "cursor":
            api_key = os.getenv("CURSOR_API_KEY", "") or "sk-local-proxy-key"

        if not api_key and p_name != "cursor":
            QMessageBox.warning(
                self, "Missing API Credentials",
                f"{p_name.capitalize()} credentials not found. Please configure them in Settings."
            )
            return

        self.btn_run.setEnabled(False)
        self.lbl_status.setText("Synthesizing queries & analyzing landscape...")
        self.queries_list.clear()
        self.sources_table.setRowCount(0)
        self.strategy_view.clear()

        depth = self.depth_combo.currentText()
        self.worker = ResearchWorkerThread(topic=topic, depth=depth, api_key=api_key)
        self.worker.finished_research.connect(self.on_research_complete)
        self.worker.start()

    def on_research_complete(self, success: bool, result, message: str):
        self.btn_run.setEnabled(True)
        self.lbl_status.setText(message)

        if not success or not result:
            QMessageBox.warning(self, "Research Failed", message)
            return

        self.current_run = result
        self.save_research_run(result)
        self.display_research_run(result)
        self.refresh_previous_runs()
        if self.main_window and hasattr(self.main_window, "refresh_dashboard_state"):
            self.main_window.refresh_dashboard_state()

    def save_research_run(self, run: ResearchRun) -> None:
        """Persists the ResearchRun to local JSON storage."""
        run_id = str(uuid.uuid4())
        path = os.path.join(self.research_dir, f"{run_id}.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(run.model_dump_json(indent=2))
        except Exception:
            pass

    def refresh_previous_runs(self) -> None:
        """Populates the history combo box with saved research runs."""
        self.history_combo.blockSignals(True)
        self.history_combo.clear()
        self.history_combo.addItem("Select previous research run...", None)

        if os.path.exists(self.research_dir):
            for fname in sorted(os.listdir(self.research_dir), reverse=True):
                if fname.endswith(".json"):
                    fpath = os.path.join(self.research_dir, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        topic = data.get("topic", fname)
                        self.history_combo.addItem(topic, fpath)
                    except Exception:
                        continue

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
            self.topic_input.setText(run.topic)
            self.display_research_run(run)
            self.lbl_status.setText(f"Loaded saved research for: {run.topic}")
        except Exception as e:
            QMessageBox.warning(self, "Load Error", f"Failed to load research run: {e}")

    def display_research_run(self, run: ResearchRun):
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
