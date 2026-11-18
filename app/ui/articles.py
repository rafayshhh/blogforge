"""Editorial writing studio, markdown canvas, publication preview, and multi-format exporter."""

import os
import json
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QPushButton, QTextEdit, QMessageBox, QSplitter, QFileDialog,
    QComboBox, QLineEdit, QDialog, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QTextCursor

from app.models.article import Article, ArticleSection
from app.export.markdown import export_markdown
from app.export.json import export_json
from app.export.html import export_html
from app.ui.components.dialogs import ArticleGeneratorDialog
from app.ui.theme import get_preview_html_styles


class ArticlesWidget(QWidget):
    """The central editorial workspace for writing, reviewing, typesetting, and publishing articles."""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.articles_dir = "data/articles"
        self.generation_dir = "data/generation"
        os.makedirs(self.articles_dir, exist_ok=True)
        os.makedirs(self.generation_dir, exist_ok=True)

        self.current_article: Optional[Article] = None
        self.current_file_path: Optional[str] = None
        self.all_items = []

        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ---------------------------------------------------------------------
        # 1. Left Sidebar: Document Library & Drafts
        # ---------------------------------------------------------------------
        left_container = QWidget()
        left_container.setFixedWidth(240)
        left_container.setStyleSheet("""
            QWidget {
                background-color: #F6F4EE;
                border-right: 1px solid #E0DDD5;
            }
        """)
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(14, 16, 14, 14)
        left_layout.setSpacing(10)

        # Navigation Header
        nav_header = QHBoxLayout()
        lbl_doc_title = QLabel("DOCUMENT LIBRARY")
        lbl_doc_title.setObjectName("sectionHead")
        nav_header.addWidget(lbl_doc_title)
        nav_header.addStretch()

        btn_new_draft = QPushButton("+ Draft")
        btn_new_draft.setObjectName("primaryBtn")
        btn_new_draft.setFixedHeight(26)
        btn_new_draft.setToolTip("Create a new blank article draft.")
        btn_new_draft.clicked.connect(self.create_blank_draft)
        nav_header.addWidget(btn_new_draft)
        left_layout.addLayout(nav_header)

        # Search Filter Bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter documents...")
        self.search_input.setFixedHeight(30)
        self.search_input.textChanged.connect(self.filter_articles)
        left_layout.addWidget(self.search_input)

        # Document List
        self.article_list = QListWidget()
        self.article_list.itemSelectionChanged.connect(self.on_select_article)
        left_layout.addWidget(self.article_list)

        # Bottom Actions
        left_bottom = QHBoxLayout()
        self.btn_del = QPushButton("Delete Draft")
        self.btn_del.setObjectName("dangerBtn")
        self.btn_del.setFixedHeight(28)
        self.btn_del.clicked.connect(self.delete_selected)
        left_bottom.addWidget(self.btn_del)

        btn_refresh = QPushButton("Refresh")
        btn_refresh.setObjectName("ghostBtn")
        btn_refresh.setFixedHeight(28)
        btn_refresh.clicked.connect(self.refresh_articles)
        left_bottom.addWidget(btn_refresh)
        left_layout.addLayout(left_bottom)

        main_layout.addWidget(left_container)

        # ---------------------------------------------------------------------
        # 2. Right Workspace: The Editorial Sanctuary
        # ---------------------------------------------------------------------
        right_container = QWidget()
        right_container.setStyleSheet("background-color: #F9F8F6;")
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(24, 14, 24, 14)
        right_layout.setSpacing(10)

        # Document Action & Publishing Bar
        header_bar = QHBoxLayout()
        header_bar.setSpacing(10)

        self.meta_label = QLabel("Select an article or create a new draft.")
        self.meta_label.setStyleSheet("color: #57534E; font-size: 13px; font-weight: 500;")
        header_bar.addWidget(self.meta_label, 1)

        # View Mode Toggle: Split / Write / Preview
        view_toggle_layout = QHBoxLayout()
        view_toggle_layout.setSpacing(2)

        self.btn_view_write = QPushButton("Write")
        self.btn_view_write.setObjectName("ghostBtn")
        self.btn_view_write.setFixedHeight(30)
        self.btn_view_write.setToolTip("Distraction-free single writing canvas")
        self.btn_view_write.clicked.connect(lambda: self.set_view_mode("write"))
        view_toggle_layout.addWidget(self.btn_view_write)

        self.btn_view_split = QPushButton("Split View")
        self.btn_view_split.setObjectName("ghostBtn")
        self.btn_view_split.setFixedHeight(30)
        self.btn_view_split.setToolTip("Side-by-side markdown editor and live preview")
        self.btn_view_split.clicked.connect(lambda: self.set_view_mode("split"))
        view_toggle_layout.addWidget(self.btn_view_split)

        self.btn_view_preview = QPushButton("Preview")
        self.btn_view_preview.setObjectName("ghostBtn")
        self.btn_view_preview.setFixedHeight(30)
        self.btn_view_preview.setToolTip("Full publication reading preview")
        self.btn_view_preview.clicked.connect(lambda: self.set_view_mode("preview"))
        view_toggle_layout.addWidget(self.btn_view_preview)

        header_bar.addLayout(view_toggle_layout)

        # AI Studio Trigger
        btn_studio = QPushButton("AI Production Studio")
        btn_studio.setFixedHeight(30)
        btn_studio.setToolTip("Launch the multi-stage AI research and drafting studio.")
        btn_studio.clicked.connect(self.open_generator_dialog)
        header_bar.addWidget(btn_studio)

        # Save Button
        self.btn_save = QPushButton("Save Draft")
        self.btn_save.setObjectName("primaryBtn")
        self.btn_save.setFixedHeight(30)
        self.btn_save.clicked.connect(self.save_article_changes)
        header_bar.addWidget(self.btn_save)

        # Export Format Dropdown & Trigger
        self.export_combo = QComboBox()
        self.export_combo.addItems(["Markdown", "HTML", "JSON"])
        self.export_combo.setFixedHeight(30)
        self.export_combo.setFixedWidth(105)
        header_bar.addWidget(self.export_combo)

        btn_export = QPushButton("Export")
        btn_export.setFixedHeight(30)
        btn_export.clicked.connect(self.export_selected)
        header_bar.addWidget(btn_export)

        right_layout.addLayout(header_bar)

        # Formatting Toolbar Strip
        toolbar_strip = QFrame()
        toolbar_strip.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E0DDD5;
                border-radius: 5px;
                padding: 2px 6px;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar_strip)
        toolbar_layout.setContentsMargins(6, 3, 6, 3)
        toolbar_layout.setSpacing(4)

        formatting_tools = [
            ("H1", "# ", "Heading 1"),
            ("H2", "## ", "Heading 2"),
            ("H3", "### ", "Heading 3"),
            ("B", "**", "Bold"),
            ("I", "*", "Italic"),
            ("Quote", "> ", "Blockquote"),
            ("Code", "`", "Inline Code"),
            ("List", "- ", "Bulleted List"),
            ("1. List", "1. ", "Numbered List"),
            ("Link", "[link](url)", "Hyperlink"),
        ]

        for label, tag, tip in formatting_tools:
            btn_t = QPushButton(label)
            btn_t.setObjectName("ghostBtn")
            btn_t.setFixedHeight(24)
            btn_t.setToolTip(f"Insert {tip}")
            btn_t.clicked.connect(lambda checked=False, t=tag: self.insert_markdown(t))
            toolbar_layout.addWidget(btn_t)

        toolbar_layout.addStretch()

        self.reading_time_label = QLabel("0 words • ~0 min read")
        self.reading_time_label.setStyleSheet("color: #8C877F; font-size: 12px; font-weight: 500;")
        toolbar_layout.addWidget(self.reading_time_label)

        right_layout.addWidget(toolbar_strip)

        # Center Splitter: Markdown Writing Canvas + Publication Preview
        self.editor_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.editor_splitter.setStyleSheet("QSplitter::handle { background-color: #E0DDD5; width: 1px; }")

        # Markdown Editor Canvas
        self.md_editor = QTextEdit()
        self.md_editor.setPlaceholderText("Start composing your manuscript here in Markdown...")
        self.md_editor.setFont(QFont("Consolas", 11))
        self.md_editor.setStyleSheet("""
            QTextEdit {
                background-color: #FFFFFF;
                border: 1px solid #E0DDD5;
                border-radius: 6px;
                padding: 22px 28px;
                color: #1C1917;
                font-family: "Consolas", "Cascadia Code", monospace;
                font-size: 13px;
                line-height: 1.65;
            }
        """)
        self.md_editor.textChanged.connect(self.on_content_changed)
        self.editor_splitter.addWidget(self.md_editor)

        # Live Typeset Publication Preview
        self.html_preview = QTextEdit()
        self.html_preview.setPlaceholderText("Live typeset publication preview will render here...")
        self.html_preview.setReadOnly(True)
        self.html_preview.setStyleSheet("""
            QTextEdit {
                background-color: #FFFFFF;
                border: 1px solid #E0DDD5;
                border-radius: 6px;
                padding: 22px 32px;
                color: #1C1917;
                font-family: "Georgia", "Charter", serif;
                font-size: 14px;
                line-height: 1.7;
            }
        """)
        self.editor_splitter.addWidget(self.html_preview)

        # Balanced initial split
        self.editor_splitter.setSizes([520, 520])
        right_layout.addWidget(self.editor_splitter, 1)

        # Bottom Document Status Line
        self.lbl_save_status = QLabel("Document Status: Ready")
        self.lbl_save_status.setStyleSheet("color: #8C877F; font-size: 11px;")
        right_layout.addWidget(self.lbl_save_status)

        main_layout.addWidget(right_container, 1)

    def set_view_mode(self, mode: str):
        """Toggles between Split View, Write-Only, and Preview-Only."""
        if mode == "split":
            self.md_editor.setVisible(True)
            self.html_preview.setVisible(True)
            self.editor_splitter.setSizes([520, 520])
        elif mode == "write":
            self.md_editor.setVisible(True)
            self.html_preview.setVisible(False)
        elif mode == "preview":
            self.md_editor.setVisible(False)
            self.html_preview.setVisible(True)

    def insert_markdown(self, tag: str):
        """Wraps selected text or inserts markdown syntax at cursor."""
        cursor = self.md_editor.textCursor()
        selected = cursor.selectedText()

        if tag in ("# ", "## ", "### ", "> ", "- ", "1. "):
            cursor.insertText(f"\n{tag}{selected}")
        elif tag in ("**", "*", "`"):
            if selected:
                cursor.insertText(f"{tag}{selected}{tag}")
            else:
                cursor.insertText(f"{tag}{tag}")
                cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.MoveAnchor, len(tag))
                self.md_editor.setTextCursor(cursor)
        elif tag == "[link](url)":
            if selected:
                cursor.insertText(f"[{selected}](https://)")
            else:
                cursor.insertText("[Title](https://)")
        self.md_editor.setFocus()

    def open_generator_dialog(self):
        """Opens the full AI Article Generation Studio dialog."""
        active_proj = self.main_window.get_active_project() if hasattr(self.main_window, "get_active_project") else None
        dialog = ArticleGeneratorDialog(self, active_project=active_proj)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            article = dialog.get_article()
            if article:
                self.refresh_articles()
                self.select_article_by_slug(article.slug)

    def select_article_by_slug(self, slug: str):
        """Finds and selects the article item matching the specified slug."""
        for idx, item in enumerate(self.all_items):
            if item.get("slug") == slug:
                self.article_list.setCurrentRow(idx)
                break

    def create_blank_draft(self):
        """Creates and persists an empty draft article."""
        import time
        ts = int(time.time())
        blank_slug = f"draft-{ts}"
        blank_article = Article(
            title="Untitled Draft",
            slug=blank_slug,
            content="# Untitled Draft\n\nBegin writing here...",
            sections=[ArticleSection(id="s1", heading="Introduction", level=2, content="")]
        )
        target_path = os.path.join(self.generation_dir, f"{blank_slug}.json")
        try:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(blank_article.model_dump_json(indent=2))
            self.refresh_articles()
            self.select_article_by_slug(blank_slug)
        except Exception as e:
            QMessageBox.warning(self, "Draft Creation Error", f"Could not create draft: {e}")

    def refresh_articles(self):
        """Reloads all articles and drafts from disk."""
        self.article_list.blockSignals(True)
        self.article_list.clear()
        self.all_items = []

        directories = [(self.articles_dir, False), (self.generation_dir, True)]
        for directory, is_draft in directories:
            if os.path.exists(directory):
                for fname in sorted(os.listdir(directory)):
                    if fname.endswith(".json"):
                        full_path = os.path.join(directory, fname)
                        try:
                            with open(full_path, "r", encoding="utf-8") as f:
                                data = json.load(f)
                            title = data.get("title") or "Untitled Article"
                            slug = data.get("slug") or fname
                            prefix = "Draft: " if is_draft else ""
                            label = f"{prefix}{title}"
                            self.all_items.append({
                                "label": label,
                                "slug": slug,
                                "path": full_path,
                                "is_draft": is_draft
                            })
                        except Exception:
                            continue

        self.article_list.blockSignals(False)
        self.filter_articles(self.search_input.text())
        if self.article_list.count() > 0 and not self.current_article:
            self.article_list.setCurrentRow(0)

    def filter_articles(self, query: str = ""):
        q = (query or "").strip().lower()
        self.article_list.clear()
        for item in self.all_items:
            if not q or q in item["label"].lower() or q in item["slug"].lower():
                self.article_list.addItem(item["label"])
                list_item = self.article_list.item(self.article_list.count() - 1)
                list_item.setData(int(Qt.ItemDataRole.UserRole), item["path"])

    def on_select_article(self):
        items = self.article_list.selectedItems()
        if not items:
            self.current_article = None
            self.current_file_path = None
            self.md_editor.clear()
            self.html_preview.clear()
            self.meta_label.setText("Select an article to view details.")
            self.reading_time_label.setText("0 words • ~0 min read")
            self.lbl_save_status.setText("Document Status: No active article")
            return

        path = items[0].data(int(Qt.ItemDataRole.UserRole))
        self.current_file_path = path

        try:
            with open(path, "r", encoding="utf-8") as f:
                self.current_article = Article.model_validate_json(f.read())

            md_text = self.current_article.content or export_markdown(self.current_article)
            self.md_editor.blockSignals(True)
            self.md_editor.setPlainText(md_text)
            self.md_editor.blockSignals(False)
            self.html_preview.setMarkdown(md_text)

            self._update_metrics(md_text)
            self.lbl_save_status.setText(f"Document Status: Saved locally ({os.path.basename(path)})")
        except Exception as e:
            QMessageBox.warning(self, "Load Error", f"Failed to load article: {e}")

    def on_content_changed(self):
        txt = self.md_editor.toPlainText()
        self.html_preview.setMarkdown(txt)
        if self.current_article:
            self._update_metrics(txt)
        self.lbl_save_status.setText("Document Status: Unsaved changes")

    def _update_metrics(self, text: str):
        words = len(text.split())
        mins = max(1, round(words / 200)) if words > 0 else 0
        sections_count = len(self.current_article.sections) if self.current_article else 0
        slug = self.current_article.slug if self.current_article else "untitled"
        title = self.current_article.title if self.current_article else "Untitled"

        self.meta_label.setText(
            f"{title}  (slug: {slug} • {sections_count} sections • {words} words)"
        )
        self.reading_time_label.setText(f"{words:,} words • ~{mins} min read")

    def save_article_changes(self):
        if not self.current_article or not self.current_file_path:
            QMessageBox.warning(self, "No Document", "No article selected to save.")
            return

        new_content = self.md_editor.toPlainText()
        self.current_article.content = new_content

        try:
            with open(self.current_file_path, "w", encoding="utf-8") as f:
                f.write(self.current_article.model_dump_json(indent=2))
            QMessageBox.information(self, "Saved", "Article changes saved successfully.")
            self.lbl_save_status.setText(
                f"Document Status: Saved locally ({os.path.basename(self.current_file_path)})"
            )
        except Exception as e:
            QMessageBox.warning(self, "Save Error", f"Failed to save article: {e}")

    def delete_selected(self):
        if not self.current_file_path or not os.path.exists(self.current_file_path):
            QMessageBox.warning(self, "No Document", "No article selected for deletion.")
            return

        ans = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to permanently delete this article draft?",
            QMessageBox.Yes | QMessageBox.No
        )
        if ans == QMessageBox.Yes:
            try:
                os.remove(self.current_file_path)
                self.current_article = None
                self.current_file_path = None
                self.refresh_articles()
            except Exception as e:
                QMessageBox.warning(self, "Delete Error", f"Could not delete: {e}")

    def export_selected(self):
        if not self.current_article:
            QMessageBox.warning(self, "No Article", "Select an article first.")
            return

        fmt = self.export_combo.currentText().lower()
        slug = self.current_article.slug or "untitled"

        if fmt == "markdown":
            path, _ = QFileDialog.getSaveFileName(self, "Export Markdown", f"{slug}.md", "Markdown (*.md)")
            if path:
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(export_markdown(self.current_article))
                    QMessageBox.information(self, "Export Successful", f"Saved Markdown to:\n{path}")
                except Exception as e:
                    QMessageBox.warning(self, "Export Failed", str(e))

        elif fmt == "html":
            path, _ = QFileDialog.getSaveFileName(self, "Export HTML", f"{slug}.html", "HTML (*.html)")
            if path:
                try:
                    html_content = export_html(self.current_article)
                    styled_html = (
                        "<!DOCTYPE html>\n<html>\n<head>\n"
                        f"{get_preview_html_styles()}\n"
                        "</head>\n<body>\n"
                        f"{html_content}\n"
                        "</body>\n</html>"
                    )
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(styled_html)
                    QMessageBox.information(self, "Export Successful", f"Saved HTML to:\n{path}")
                except Exception as e:
                    QMessageBox.warning(self, "Export Failed", str(e))

        elif fmt == "json":
            path, _ = QFileDialog.getSaveFileName(self, "Export JSON", f"{slug}.json", "JSON (*.json)")
            if path:
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(export_json(self.current_article))
                    QMessageBox.information(self, "Export Successful", f"Saved JSON to:\n{path}")
                except Exception as e:
                    QMessageBox.warning(self, "Export Failed", str(e))
