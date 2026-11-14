"""Articles and drafts viewer, editor, and multi-format exporter widget."""

import os
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QPushButton, QTextEdit, QMessageBox, QSplitter, QFileDialog,
    QComboBox, QLineEdit
)
from PySide6.QtCore import Qt

from app.models.article import Article
from app.export.markdown import export_markdown
from app.export.json import export_json
from app.export.html import export_html


class ArticlesWidget(QWidget):
    """Article management interface supporting Markdown editing and export."""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.articles_dir = "data/articles"
        self.generation_dir = "data/generation"
        os.makedirs(self.articles_dir, exist_ok=True)
        os.makedirs(self.generation_dir, exist_ok=True)

        self.current_article = None
        self.current_file_path = None
        self.all_items = []

        self.init_ui()
        self.refresh_articles()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 32, 32, 32)

        header_layout = QHBoxLayout()
        lbl_head = QLabel("Articles & Drafts")
        lbl_head.setObjectName("h1")
        header_layout.addWidget(lbl_head)
        header_layout.addStretch()

        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self.refresh_articles)
        header_layout.addWidget(btn_refresh)
        main_layout.addLayout(header_layout)

        splitter = QSplitter(Qt.Horizontal)

        # Left Column: Browser & Search
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search articles...")
        self.search_input.textChanged.connect(self.filter_articles)
        left_layout.addWidget(self.search_input)

        self.article_list = QListWidget()
        self.article_list.itemSelectionChanged.connect(self.on_select_article)
        left_layout.addWidget(self.article_list)

        btn_del = QPushButton("Delete Selected")
        btn_del.clicked.connect(self.delete_selected)
        left_layout.addWidget(btn_del)

        left_widget.setFixedWidth(280)
        splitter.addWidget(left_widget)

        # Right Column: Editor & Preview
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.meta_label = QLabel("Select an article to view details.")
        self.meta_label.setObjectName("subtitle")
        right_layout.addWidget(self.meta_label)

        editor_splitter = QSplitter(Qt.Horizontal)

        self.md_editor = QTextEdit()
        self.md_editor.setPlaceholderText("Article content...")
        self.md_editor.textChanged.connect(self.on_content_changed)
        editor_splitter.addWidget(self.md_editor)

        self.html_preview = QTextEdit()
        self.html_preview.setPlaceholderText("Rendered preview...")
        self.html_preview.setReadOnly(True)
        editor_splitter.addWidget(self.html_preview)

        right_layout.addWidget(editor_splitter)

        # Action Buttons
        actions_layout = QHBoxLayout()
        self.btn_save = QPushButton("Save Changes")
        self.btn_save.setObjectName("primaryBtn")
        self.btn_save.clicked.connect(self.save_article_changes)
        actions_layout.addWidget(self.btn_save)

        self.export_combo = QComboBox()
        self.export_combo.addItems(["Markdown", "HTML", "JSON"])
        actions_layout.addWidget(self.export_combo)

        btn_export = QPushButton("Export")
        btn_export.clicked.connect(self.export_selected)
        actions_layout.addWidget(btn_export)

        actions_layout.addStretch()
        right_layout.addLayout(actions_layout)

        splitter.addWidget(right_widget)
        main_layout.addWidget(splitter)

    def refresh_articles(self):
        self.article_list.blockSignals(True)
        self.article_list.clear()
        self.all_items = []

        directories = [(self.articles_dir, False), (self.generation_dir, True)]
        for directory, is_draft in directories:
            if os.path.exists(directory):
                for fname in os.listdir(directory):
                    if fname.endswith(".json"):
                        full_path = os.path.join(directory, fname)
                        try:
                            with open(full_path, "r", encoding="utf-8") as f:
                                data = json.load(f)
                            title = data.get("title") or "Untitled Article"
                            slug = data.get("slug") or fname
                            prefix = "[Draft] " if is_draft else ""
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

    def filter_articles(self, query: str = ""):
        q = (query or "").strip().lower()
        self.article_list.clear()
        for item in self.all_items:
            if not q or q in item["label"].lower() or q in item["slug"].lower():
                self.article_list.addItem(item["label"])
                list_item = self.article_list.item(self.article_list.count() - 1)
                list_item.setData(Qt.UserRole, item["path"])

    def on_select_article(self):
        items = self.article_list.selectedItems()
        if not items:
            self.current_article = None
            self.current_file_path = None
            self.md_editor.clear()
            self.html_preview.clear()
            self.meta_label.setText("Select an article to view details.")
            return

        path = items[0].data(Qt.UserRole)
        self.current_file_path = path

        try:
            with open(path, "r", encoding="utf-8") as f:
                self.current_article = Article.model_validate_json(f.read())

            md_text = self.current_article.content or export_markdown(self.current_article)
            self.md_editor.setPlainText(md_text)
            self.html_preview.setMarkdown(md_text)

            words = len(md_text.split())
            self.meta_label.setText(
                f"Title: {self.current_article.title} | Slug: {self.current_article.slug} "
                f"| Sections: {len(self.current_article.sections)} | ~{words} words"
            )
        except Exception as e:
            QMessageBox.warning(self, "Load Error", f"Failed to load article: {e}")

    def on_content_changed(self):
        txt = self.md_editor.toPlainText()
        self.html_preview.setMarkdown(txt)

    def save_article_changes(self):
        if not self.current_article or not self.current_file_path:
            QMessageBox.warning(self, "No Article", "Please select an article first.")
            return

        try:
            self.current_article.content = self.md_editor.toPlainText()
            with open(self.current_file_path, "w", encoding="utf-8") as f:
                f.write(self.current_article.model_dump_json(indent=2))
            QMessageBox.information(self, "Saved", "Article changes saved successfully.")
        except Exception as e:
            QMessageBox.warning(self, "Save Error", f"Failed to save changes: {e}")

    def delete_selected(self):
        items = self.article_list.selectedItems()
        if not items or not self.current_file_path:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this article?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                if os.path.exists(self.current_file_path):
                    os.remove(self.current_file_path)
                self.refresh_articles()
                self.md_editor.clear()
                self.html_preview.clear()
                self.meta_label.setText("Article deleted.")
            except Exception as e:
                QMessageBox.warning(self, "Delete Error", f"Failed to delete article: {e}")

    def export_selected(self):
        if not self.current_article:
            QMessageBox.warning(self, "No Article", "Please select an article to export.")
            return

        fmt = self.export_combo.currentText()
        slug = self.current_article.slug or "article"

        if fmt == "Markdown":
            path, _ = QFileDialog.getSaveFileName(self, "Export Markdown", f"{slug}.md", "Markdown (*.md)")
            if path:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(export_markdown(self.current_article))
                QMessageBox.information(self, "Exported", f"Saved to {path}")
        elif fmt == "JSON":
            path, _ = QFileDialog.getSaveFileName(self, "Export JSON", f"{slug}.json", "JSON (*.json)")
            if path:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(export_json(self.current_article))
                QMessageBox.information(self, "Exported", f"Saved to {path}")
        elif fmt == "HTML":
            path, _ = QFileDialog.getSaveFileName(self, "Export HTML", f"{slug}.html", "HTML (*.html)")
            if path:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(export_html(self.current_article))
                QMessageBox.information(self, "Exported", f"Saved to {path}")
