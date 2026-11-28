"""Reusable modal dialogs for products, links, and multi-stage AI article generation."""

import os
from typing import List, Optional, Tuple
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QMessageBox, QProgressBar,
    QComboBox, QFrame
)
from PySide6.QtCore import QThread, Signal

from app.models.article import Article
from app.generation.models import GenerationRequest
from app.generation.pipeline import GenerationPipeline
from app.providers.factory import resolve_active_provider


class AddProductDialog(QDialog):
    """Compact modal to capture a product name and description."""

    def __init__(self, parent=None, initial_name: str = "", initial_desc: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Add Product to Catalog")
        self.setFixedSize(440, 260)
        self.result_data: Optional[Tuple[str, str, bool]] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        lbl_head = QLabel("Product Specification")
        lbl_head.setObjectName("h2")
        layout.addWidget(lbl_head)

        lbl_n = QLabel("Product Name *")
        lbl_n.setObjectName("caption")
        layout.addWidget(lbl_n)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. CloudScale Pro")
        self.name_input.setFixedHeight(34)
        self.name_input.setText(initial_name)
        layout.addWidget(self.name_input)

        lbl_d = QLabel("Description & Value Proposition")
        lbl_d.setObjectName("caption")
        layout.addWidget(lbl_d)

        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Key features, benefits, and context for mention in articles...")
        self.desc_input.setFixedHeight(75)
        self.desc_input.setText(initial_desc)
        layout.addWidget(self.desc_input)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("ghostBtn")
        btn_cancel.setFixedHeight(32)
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_ok = QPushButton("Add Product")
        btn_ok.setObjectName("primaryBtn")
        btn_ok.setFixedHeight(32)
        btn_ok.clicked.connect(self.on_accept)
        btn_row.addWidget(btn_ok)

        layout.addLayout(btn_row)

    def on_accept(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Product name cannot be empty.")
            return
        desc = self.desc_input.toPlainText().strip()
        self.result_data = (name, desc, True)
        self.accept()

    def get_data(self) -> Tuple[str, str, bool]:
        if self.result_data:
            return self.result_data
        return ("", "", False)


class AddLinkDialog(QDialog):
    """Compact modal to capture an internal target URL and link anchor text."""

    def __init__(self, parent=None, initial_title: str = "", initial_url: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Add Internal Link")
        self.setFixedSize(440, 240)
        self.result_data: Optional[Tuple[str, str, bool]] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        lbl_head = QLabel("Internal Link Details")
        lbl_head.setObjectName("h2")
        layout.addWidget(lbl_head)

        lbl_t = QLabel("Anchor / Page Title *")
        lbl_t.setObjectName("caption")
        layout.addWidget(lbl_t)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g. Enterprise Pricing Guide")
        self.title_input.setFixedHeight(34)
        self.title_input.setText(initial_title)
        layout.addWidget(self.title_input)

        lbl_u = QLabel("Destination URL or Path *")
        lbl_u.setObjectName("caption")
        layout.addWidget(lbl_u)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("e.g. /pricing or https://example.com/pricing")
        self.url_input.setFixedHeight(34)
        self.url_input.setText(initial_url)
        layout.addWidget(self.url_input)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("ghostBtn")
        btn_cancel.setFixedHeight(32)
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_ok = QPushButton("Add Link")
        btn_ok.setObjectName("primaryBtn")
        btn_ok.setFixedHeight(32)
        btn_ok.clicked.connect(self.on_accept)
        btn_row.addWidget(btn_ok)

        layout.addLayout(btn_row)

    def on_accept(self):
        title = self.title_input.text().strip()
        url = self.url_input.text().strip()
        if not title or not url:
            QMessageBox.warning(self, "Validation Error", "Both Title and Target URL are required.")
            return
        self.result_data = (title, url, True)
        self.accept()

    def get_data(self) -> Tuple[str, str, bool]:
        if self.result_data:
            return self.result_data
        return ("", "", False)


class GeneratorWorkerThread(QThread):
    """Executes multi-stage article generation pipeline in a background thread."""
    progress_status = Signal(str, int)
    finished_generation = Signal(bool, object, str)

    def __init__(self, request: GenerationRequest, api_key: Optional[str] = None):
        super().__init__()
        self.request = request
        self.api_key = api_key
        self.pipeline: Optional[GenerationPipeline] = None

    def cancel(self):
        if self.pipeline:
            self.pipeline.cancel()

    def run(self):
        try:
            self.progress_status.emit("Initializing Google Gemini AI engine...", 10)
            provider = resolve_active_provider(api_key=self.api_key if self.api_key else None)
            self.pipeline = GenerationPipeline(ai_provider=provider)

            self.progress_status.emit("Synthesizing structural article outline...", 25)
            outline = self.pipeline.generate_outline(self.request)
            if not outline or not outline.sections:
                self.finished_generation.emit(False, None, "Failed to produce article outline.")
                return

            def on_progress(msg: str):
                self.progress_status.emit(msg, 60)

            self.progress_status.emit(f"Drafting {len(outline.sections)} sections...", 50)
            article = self.pipeline.generate_article(self.request, outline, progress_callback=on_progress)

            if self.pipeline.is_cancelled:
                self.finished_generation.emit(False, None, "Generation cancelled by user.")
                return

            self.progress_status.emit("Performing automated editorial review...", 85)
            try:
                review = self.pipeline.review_article(article, self.request)
                if review:
                    article.seo_audit = {
                        "overall_score": review.overall_score,
                        "suggestions": list(review.suggestions[:5]),
                        "brand_violations": list(review.brand_violations),
                    }
            except Exception:
                pass

            self.progress_status.emit("Finalizing manuscript & FAQs...", 95)
            article = self.pipeline.finalize_article(article, self.request)

            self.progress_status.emit("Article production complete.", 100)
            score_note = ""
            if isinstance(article.seo_audit, dict) and article.seo_audit.get("overall_score") is not None:
                score_note = f" (Quality score: {article.seo_audit['overall_score']}/100)"
            self.finished_generation.emit(True, article, f"Article successfully generated{score_note}.")
        except Exception as e:
            self.finished_generation.emit(False, None, f"Generation error: {str(e)}")


class ArticleGeneratorDialog(QDialog):
    """Guided editorial production studio dialog for multi-stage article drafting."""

    def __init__(
        self,
        parent=None,
        active_project=None,
        initial_strategy: Optional[str] = None,
        initial_sources: Optional[List[str]] = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("AI Article Production Studio")
        self.setMinimumSize(680, 560)
        self.resize(720, 580)
        self.active_project = active_project
        self.initial_strategy = initial_strategy
        self.initial_sources: List[str] = list(initial_sources) if initial_sources else []
        self.worker: Optional[GeneratorWorkerThread] = None
        self.generated_article: Optional[Article] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(14)

        # Header
        header_box = QVBoxLayout()
        header_box.setSpacing(3)
        lbl_head = QLabel("AI Article Production Studio")
        lbl_head.setObjectName("h1")
        header_box.addWidget(lbl_head)

        proj_name = self.active_project.name if self.active_project else "Default Workspace"
        lbl_sub = QLabel(f"Project Style Guide: {proj_name} • Multi-stage drafting & review")
        lbl_sub.setObjectName("subtitle")
        lbl_sub.setWordWrap(True)
        header_box.addWidget(lbl_sub)
        layout.addLayout(header_box)

        # Workflow Stage Indicator Bar
        stage_strip = QFrame()
        stage_strip.setObjectName("stageStrip")
        stage_strip.setStyleSheet("""
            #stageStrip {
                background-color: #F4F1EA;
                border: 1px solid #E0DDD5;
                border-radius: 5px;
            }
            #stageStrip QLabel {
                background-color: transparent;
                border: none;
                border-radius: 0px;
                padding: 0px;
            }
        """)
        stage_layout = QHBoxLayout(stage_strip)
        stage_layout.setContentsMargins(12, 6, 12, 6)
        stage_layout.setSpacing(10)

        stages = ["1. Brief", "2. Outline", "3. Drafting", "4. Review"]
        for s in stages:
            lbl_s = QLabel(s)
            lbl_s.setStyleSheet("color: #57534E; font-size: 11px; font-weight: 600;")
            stage_layout.addWidget(lbl_s)
            if s != stages[-1]:
                lbl_arr = QLabel("→")
                lbl_arr.setStyleSheet("color: #8C877F; font-size: 11px;")
                stage_layout.addWidget(lbl_arr)
        layout.addWidget(stage_strip)

        # Form Fields Card
        form_card = QFrame()
        form_card.setObjectName("formCard")
        form_card.setStyleSheet("""
            #formCard {
                background-color: #FFFFFF;
                border: 1px solid #E0DDD5;
                border-radius: 6px;
            }
            #formCard QLabel {
                background-color: transparent;
                border: none;
                border-radius: 0px;
                padding: 0px;
            }
        """)
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(18, 16, 18, 16)
        form_layout.setSpacing(10)

        lbl_t = QLabel("Article Topic & Thesis *")
        lbl_t.setObjectName("caption")
        form_layout.addWidget(lbl_t)

        self.topic_input = QLineEdit()
        self.topic_input.setPlaceholderText("e.g. Next-Generation Cloud Migration Strategies for Fintech")
        self.topic_input.setFixedHeight(34)
        form_layout.addWidget(self.topic_input)

        row_params = QHBoxLayout()
        row_params.setSpacing(12)

        box_words = QVBoxLayout()
        box_words.setSpacing(4)
        lbl_wc = QLabel("Target Word Count")
        lbl_wc.setObjectName("caption")
        box_words.addWidget(lbl_wc)

        self.word_count_combo = QComboBox()
        self.word_count_combo.addItems(["1,200 words", "1,800 words", "2,500 words", "3,500 words"])
        self.word_count_combo.setFixedHeight(32)
        box_words.addWidget(self.word_count_combo)
        row_params.addLayout(box_words)

        box_style = QVBoxLayout()
        box_style.setSpacing(4)
        lbl_st = QLabel("Target Audience & Tone")
        lbl_st.setObjectName("caption")
        box_style.addWidget(lbl_st)

        self.tone_input = QLineEdit()
        default_tone = "Pragmatic, authoritative"
        if (
            self.active_project
            and hasattr(self.active_project, "brand_profile")
            and self.active_project.brand_profile.tone
        ):
            default_tone = self.active_project.brand_profile.tone
        self.tone_input.setText(default_tone)
        self.tone_input.setFixedHeight(32)
        box_style.addWidget(self.tone_input)
        row_params.addLayout(box_style)

        form_layout.addLayout(row_params)

        lbl_kw = QLabel("Keywords & Topics to Cover (comma-separated)")
        lbl_kw.setObjectName("caption")
        form_layout.addWidget(lbl_kw)

        self.keywords_input = QLineEdit()
        self.keywords_input.setPlaceholderText("e.g. zero-downtime, database replication, compliance")
        self.keywords_input.setFixedHeight(34)
        form_layout.addWidget(self.keywords_input)

        layout.addWidget(form_card)

        # Progress and Status
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        initial_msg = "Ready to configure and generate."
        if self.initial_sources or self.initial_strategy:
            initial_msg = (
                f"Research context attached ({len(self.initial_sources)} verified sources). "
                "Ready to configure and generate."
            )
        self.lbl_status = QLabel(initial_msg)
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setStyleSheet("color: #57534E; font-size: 12px;")
        layout.addWidget(self.lbl_status)

        layout.addStretch()

        # Action Buttons
        btn_row = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("ghostBtn")
        self.btn_cancel.setFixedHeight(34)
        self.btn_cancel.clicked.connect(self.cancel_or_close)
        btn_row.addWidget(self.btn_cancel)

        btn_row.addStretch()

        self.btn_start = QPushButton("Begin Article Production")
        self.btn_start.setObjectName("primaryBtn")
        self.btn_start.setFixedHeight(34)
        self.btn_start.clicked.connect(self.start_generation)
        btn_row.addWidget(self.btn_start)

        layout.addLayout(btn_row)

    def start_generation(self):
        topic = self.topic_input.text().strip()
        if not topic:
            QMessageBox.warning(self, "Topic Required", "Please enter an article topic to begin generation.")
            return

        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            QMessageBox.warning(
                self, "Missing API Credentials",
                "Google Gemini credentials not found. Please configure your API key in Settings first."
            )
            return

        wc_str = self.word_count_combo.currentText().replace(",", "").replace("words", "").strip()
        try:
            wc_target = int(wc_str)
        except ValueError:
            wc_target = 1800

        # Prepare request
        audience_val = None
        if self.active_project and hasattr(self.active_project, "brand_profile"):
            audience_val = self.active_project.brand_profile.target_audience or None

        req = GenerationRequest(
            project_id=self.active_project.id if self.active_project else "default",
            topic=topic,
            audience=audience_val,
            strategy=self.initial_strategy,
            keywords=[k.strip() for k in self.keywords_input.text().split(",") if k.strip()],
            verified_sources=list(self.initial_sources),
            tone=self.tone_input.text().strip(),
            target_word_count=wc_target,
            word_count_target=wc_target
        )

        self.btn_start.setEnabled(False)
        self.btn_cancel.setText("Abort Production")
        self.progress_bar.show()
        self.progress_bar.setValue(5)
        self.lbl_status.setText("Connecting to editorial pipeline...")

        self.worker = GeneratorWorkerThread(request=req, api_key=api_key)
        self.worker.progress_status.connect(self.on_worker_progress)
        self.worker.finished_generation.connect(self.on_worker_finished)
        self.worker.start()

    def on_worker_progress(self, msg: str, val: int):
        self.lbl_status.setText(msg)
        self.progress_bar.setValue(val)

    def on_worker_finished(self, success: bool, article: Optional[Article], msg: str):
        self.btn_start.setEnabled(True)
        self.btn_cancel.setText("Close")

        if success and article:
            self.generated_article = article
            self.lbl_status.setText(f"✓ {msg}")
            self.lbl_status.setStyleSheet("color: #15803D; font-size: 12px; font-weight: 500;")

            QMessageBox.information(
                self, "Production Succeeded",
                f"Article '{article.title}' drafted successfully!\nIt has been loaded into your Editorial Studio."
            )
            self.accept()
        else:
            self.lbl_status.setText(f"✕ {msg}")
            self.lbl_status.setStyleSheet("color: #B91C1C; font-size: 12px;")
            QMessageBox.warning(self, "Generation Incomplete", msg)

    def cancel_or_close(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.lbl_status.setText("Cancelling production...")
            self.worker.wait(2000)
            self.reject()
        else:
            self.reject()

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(2000)
        super().closeEvent(event)

    def get_article(self) -> Optional[Article]:
        return self.generated_article
