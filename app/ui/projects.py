"""Projects and brand profiles management widget."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QMessageBox, QTextEdit,
    QTabWidget, QInputDialog, QComboBox, QCheckBox, QFileDialog
)
from app.projects.service import ProjectService
from app.projects.models import Product, InternalLink
from app.integrations.nextjs.exporter import NextJSExporter


class ProjectsWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.service = ProjectService()
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(32, 32, 32, 32)

        # Left Panel: List
        left_layout = QVBoxLayout()
        lbl_head = QLabel("Projects")
        lbl_head.setObjectName("h1")
        left_layout.addWidget(lbl_head)

        self.project_list = QListWidget()
        self.project_list.itemSelectionChanged.connect(self.load_project)
        left_layout.addWidget(self.project_list)

        self.btn_new = QPushButton("+ New Project")
        self.btn_new.clicked.connect(self.new_project)
        left_layout.addWidget(self.btn_new)

        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        left_widget.setFixedWidth(250)
        self.layout.addWidget(left_widget)

        # Right Panel: Tabs
        self.right_layout = QVBoxLayout()
        self.tabs = QTabWidget()

        # --- Tab: Core ---
        tab_core = QWidget()
        core_layout = QVBoxLayout(tab_core)
        self.name_input = QLineEdit()
        self.desc_input = QTextEdit()
        core_layout.addWidget(QLabel("Project Name:"))
        core_layout.addWidget(self.name_input)
        core_layout.addWidget(QLabel("Project Description:"))
        core_layout.addWidget(self.desc_input)

        self.brand_tone_input = QLineEdit()
        core_layout.addWidget(QLabel("Brand Tone (e.g. Professional):"))
        core_layout.addWidget(self.brand_tone_input)

        self.btn_save = QPushButton("Save Project Settings")
        self.btn_save.setObjectName("primaryBtn")
        self.btn_save.clicked.connect(self.save_project)
        core_layout.addWidget(self.btn_save)
        self.tabs.addTab(tab_core, "Core Settings")

        # --- Tab: Products ---
        tab_prod = QWidget()
        prod_layout = QVBoxLayout(tab_prod)
        self.prod_list = QListWidget()
        prod_layout.addWidget(QLabel("Products / Services associated with this brand:"))
        prod_layout.addWidget(self.prod_list)

        p_btns = QHBoxLayout()
        btn_add_prod = QPushButton("+ Add Product")
        btn_add_prod.clicked.connect(self.add_product)
        btn_del_prod = QPushButton("Delete Product")
        btn_del_prod.clicked.connect(self.del_product)
        p_btns.addWidget(btn_add_prod)
        p_btns.addWidget(btn_del_prod)
        prod_layout.addLayout(p_btns)
        self.tabs.addTab(tab_prod, "Products")

        # --- Tab: URLs ---
        tab_url = QWidget()
        url_layout = QVBoxLayout(tab_url)
        self.url_list = QListWidget()
        url_layout.addWidget(QLabel("Internal URLs used for linking:"))
        url_layout.addWidget(self.url_list)

        u_btns = QHBoxLayout()
        btn_add_url = QPushButton("+ Add URL")
        btn_add_url.clicked.connect(self.add_url)
        btn_del_url = QPushButton("Delete URL")
        btn_del_url.clicked.connect(self.del_url)
        u_btns.addWidget(btn_add_url)
        u_btns.addWidget(btn_del_url)
        url_layout.addLayout(u_btns)
        self.tabs.addTab(tab_url, "Internal Links")

        # --- Tab: Integrations ---
        tab_int = QWidget()
        int_layout = QVBoxLayout(tab_int)

        self.nextjs_enabled = QCheckBox("Enable Next.js Integration")
        int_layout.addWidget(self.nextjs_enabled)

        self.nextjs_proj_dir = QLineEdit()
        self.nextjs_content_dir = QLineEdit()

        def browse_proj():
            d = QFileDialog.getExistingDirectory(self, "Select Next.js Project Directory")
            if d:
                self.nextjs_proj_dir.setText(d)

        def browse_content():
            d = QFileDialog.getExistingDirectory(self, "Select Next.js Content Directory")
            if d:
                self.nextjs_content_dir.setText(d)

        btn_b_proj = QPushButton("Browse...")
        btn_b_proj.clicked.connect(browse_proj)
        btn_b_cont = QPushButton("Browse...")
        btn_b_cont.clicked.connect(browse_content)

        l1 = QHBoxLayout()
        l1.addWidget(self.nextjs_proj_dir)
        l1.addWidget(btn_b_proj)

        l2 = QHBoxLayout()
        l2.addWidget(self.nextjs_content_dir)
        l2.addWidget(btn_b_cont)

        int_layout.addWidget(QLabel("Next.js Project Directory:"))
        int_layout.addLayout(l1)
        int_layout.addWidget(QLabel("Next.js Content Directory:"))
        int_layout.addLayout(l2)

        self.nextjs_format = QComboBox()
        self.nextjs_format.addItems(["JSON", "MARKDOWN"])
        int_layout.addWidget(QLabel("Export Format:"))
        int_layout.addWidget(self.nextjs_format)

        self.btn_test_nextjs = QPushButton("Test Project")
        self.btn_test_nextjs.clicked.connect(self.test_nextjs)
        int_layout.addWidget(self.btn_test_nextjs)
        int_layout.addStretch()

        self.tabs.addTab(tab_int, "Integrations")

        self.right_layout.addWidget(self.tabs)
        self.layout.addLayout(self.right_layout)

        self.current_project_id = None
        self.refresh_list()

    def refresh_list(self):
        self.project_list.blockSignals(True)
        self.project_list.clear()
        projects = self.service.list_projects()
        selected_idx = -1
        for idx, p in enumerate(projects):
            self.project_list.addItem(p.name)
            item = self.project_list.item(idx)
            item.setData(32, p.id)
            if self.current_project_id == p.id:
                selected_idx = idx
        self.project_list.blockSignals(False)
        if selected_idx >= 0:
            self.project_list.setCurrentRow(selected_idx)
        self.main_window.refresh_project_switcher()

    def new_project(self):
        self.current_project_id = None
        self.name_input.clear()
        self.desc_input.clear()
        self.brand_tone_input.clear()
        self.prod_list.clear()
        self.url_list.clear()
        self.project_list.clearSelection()
        self.nextjs_enabled.setChecked(False)
        self.nextjs_proj_dir.clear()
        self.nextjs_content_dir.clear()
        self.nextjs_format.setCurrentIndex(0)

    def load_project(self):
        items = self.project_list.selectedItems()
        if not items:
            return

        pid = items[0].data(32)
        proj = self.service.get_project(pid)
        if proj:
            self.current_project_id = proj.id
            self.name_input.setText(proj.name)
            self.desc_input.setPlainText(proj.description or "")
            self.brand_tone_input.setText(proj.brand_profile.tone)

            self.prod_list.clear()
            for prod in proj.products:
                self.prod_list.addItem(f"{prod.name} - {prod.description}")
                item = self.prod_list.item(self.prod_list.count() - 1)
                item.setData(32, prod.id)

            self.url_list.clear()
            for url in proj.internal_links:
                self.url_list.addItem(f"{url.title} ({url.url})")
                item = self.url_list.item(self.url_list.count() - 1)
                item.setData(32, url.id)

            self.nextjs_enabled.setChecked(proj.nextjs_integration.enabled)
            self.nextjs_proj_dir.setText(proj.nextjs_integration.project_directory or "")
            self.nextjs_content_dir.setText(proj.nextjs_integration.content_directory or "")
            self.nextjs_format.setCurrentText(proj.nextjs_integration.export_format)

    def save_project(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Name is required")
            return

        if self.current_project_id:
            proj = self.service.get_project(self.current_project_id)
            if not proj:
                QMessageBox.warning(self, "Error", "Project not found.")
                return
            proj.name = name
            proj.description = self.desc_input.toPlainText()
            proj.brand_profile.tone = self.brand_tone_input.text()

            proj.nextjs_integration.enabled = self.nextjs_enabled.isChecked()
            proj.nextjs_integration.project_directory = self.nextjs_proj_dir.text()
            proj.nextjs_integration.content_directory = self.nextjs_content_dir.text()
            proj.nextjs_integration.export_format = self.nextjs_format.currentText()

            self.service.update_project(proj)
        else:
            proj = self.service.create_project(name=name, description=self.desc_input.toPlainText())
            proj.brand_profile.tone = self.brand_tone_input.text()

            proj.nextjs_integration.enabled = self.nextjs_enabled.isChecked()
            proj.nextjs_integration.project_directory = self.nextjs_proj_dir.text()
            proj.nextjs_integration.content_directory = self.nextjs_content_dir.text()
            proj.nextjs_integration.export_format = self.nextjs_format.currentText()

            self.service.update_project(proj)
            self.current_project_id = proj.id

        self.refresh_list()

    def test_nextjs(self):
        if not self.current_project_id:
            QMessageBox.warning(self, "Save First", "Please save the project first.")
            return

        proj = self.service.get_project(self.current_project_id)
        if not proj:
            QMessageBox.warning(self, "Error", "Project not found.")
            return
        exporter = NextJSExporter()
        try:
            exporter.test_connection(proj)
            QMessageBox.information(self, "Success", "✓ Looks good! Directory is writable.")
        except Exception as e:
            QMessageBox.warning(self, "Test Failed", str(e))

    def add_product(self):
        if not self.current_project_id:
            QMessageBox.warning(self, "Save First", "Please save the project first.")
            return
        name, ok1 = QInputDialog.getText(self, "Product", "Product Name:")
        if not ok1 or not name:
            return
        desc, ok2 = QInputDialog.getText(self, "Product", "Product Description:")
        if not ok2:
            return

        proj = self.service.get_project(self.current_project_id)
        if not proj:
            QMessageBox.warning(self, "Error", "Project not found.")
            return
        proj.products.append(Product(name=name, description=desc))
        self.service.update_project(proj)
        self.load_project()

    def del_product(self):
        if not self.current_project_id:
            return
        sel = self.prod_list.selectedItems()
        if not sel:
            return
        pid = sel[0].data(32)
        proj = self.service.get_project(self.current_project_id)
        if not proj:
            return
        proj.products = [p for p in proj.products if p.id != pid]
        self.service.update_project(proj)
        self.load_project()

    def add_url(self):
        if not self.current_project_id:
            QMessageBox.warning(self, "Save First", "Please save the project first.")
            return
        title, ok1 = QInputDialog.getText(self, "URL", "Link Title:")
        if not ok1 or not title:
            return
        url, ok2 = QInputDialog.getText(self, "URL", "Link URL (http://... or /...):")
        if not ok2 or not url:
            return

        try:
            link = InternalLink(title=title, url=url)
            proj = self.service.get_project(self.current_project_id)
            if not proj:
                QMessageBox.warning(self, "Error", "Project not found.")
                return
            proj.internal_links.append(link)
            self.service.update_project(proj)
            self.load_project()
        except Exception as e:
            QMessageBox.warning(self, "Invalid URL", f"Please enter a valid URL. Error: {e}")

    def del_url(self):
        if not self.current_project_id:
            return
        sel = self.url_list.selectedItems()
        if not sel:
            return
        uid = sel[0].data(32)
        proj = self.service.get_project(self.current_project_id)
        if not proj:
            return
        proj.internal_links = [item for item in proj.internal_links if item.id != uid]
        self.service.update_project(proj)
        self.load_project()
