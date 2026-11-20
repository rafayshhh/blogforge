"""Projects and editorial style guide management widget."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QMessageBox, QTextEdit,
    QTabWidget, QInputDialog, QCheckBox, QFileDialog, QScrollArea,
    QFrame
)
from PySide6.QtCore import Qt

from app.projects.service import ProjectService
from app.projects.models import Product, InternalLink
from app.integrations.nextjs.exporter import NextJSExporter


class ProjectsWidget(QWidget):
    """Management interface for brand style guides, product catalogs, and publishing targets."""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.service = ProjectService()
        self.current_project_id = None

        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(28, 20, 28, 20)
        root_layout.setSpacing(20)

        # ---------------------------------------------------------------------
        # 1. Left Panel: Project Library & Selection
        # ---------------------------------------------------------------------
        left_panel = QWidget()
        left_panel.setFixedWidth(270)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        lbl_head = QLabel("PROJECT DIRECTORY")
        lbl_head.setObjectName("sectionHead")
        left_layout.addWidget(lbl_head)

        self.project_list = QListWidget()
        self.project_list.itemSelectionChanged.connect(self.load_project)
        left_layout.addWidget(self.project_list)

        left_actions = QHBoxLayout()
        left_actions.setSpacing(8)

        self.btn_new = QPushButton("+ New Project")
        self.btn_new.setObjectName("primaryBtn")
        self.btn_new.setFixedHeight(34)
        self.btn_new.setCursor(Qt.PointingHandCursor)
        self.btn_new.clicked.connect(self.new_project)
        left_actions.addWidget(self.btn_new)

        btn_delete_proj = QPushButton("Delete")
        btn_delete_proj.setObjectName("dangerBtn")
        btn_delete_proj.setFixedHeight(34)
        btn_delete_proj.clicked.connect(self.delete_project)
        left_actions.addWidget(btn_delete_proj)

        left_layout.addLayout(left_actions)
        root_layout.addWidget(left_panel)

        # ---------------------------------------------------------------------
        # 2. Right Panel: Editorial Style Guide & Configuration Workspace
        # ---------------------------------------------------------------------
        right_container = QWidget()
        self.right_layout = QVBoxLayout(right_container)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(12)

        # Workspace Header with Save Trigger
        top_bar = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        self.lbl_editing_project = QLabel("Editorial Style Guide & Brand Rules")
        self.lbl_editing_project.setObjectName("h2")
        title_box.addWidget(self.lbl_editing_project)

        self.lbl_sub = QLabel("Configure voice, tone guidelines, products, and publishing targets.")
        self.lbl_sub.setObjectName("caption")
        title_box.addWidget(self.lbl_sub)
        top_bar.addLayout(title_box)

        top_bar.addStretch()

        self.btn_save = QPushButton("Save Project Settings")
        self.btn_save.setObjectName("primaryBtn")
        self.btn_save.setFixedHeight(34)
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.clicked.connect(self.save_project)
        top_bar.addWidget(self.btn_save)

        self.right_layout.addLayout(top_bar)

        # Tabs for Configuration
        self.tabs = QTabWidget()

        # Tab 1: Editorial Style Guide (Brand identity, Voice, Tone, Rules)
        tab_style_guide = QWidget()
        sg_scroll = QScrollArea()
        sg_scroll.setWidgetResizable(True)
        sg_scroll.setFrameShape(QFrame.Shape.NoFrame)
        sg_scroll.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")

        sg_inner = QWidget()
        sg_layout = QVBoxLayout(sg_inner)
        sg_layout.setContentsMargins(18, 16, 18, 16)
        sg_layout.setSpacing(14)

        # Project Name
        lbl_pname = QLabel("Project & Brand Name *")
        lbl_pname.setObjectName("caption")
        sg_layout.addWidget(lbl_pname)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Acme Tech Insights")
        self.name_input.setFixedHeight(34)
        sg_layout.addWidget(self.name_input)

        # Description / Mission
        lbl_desc = QLabel("Mission, Positioning & Brand Summary")
        lbl_desc.setObjectName("caption")
        sg_layout.addWidget(lbl_desc)
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Describe the core mission, brand identity, and editorial objective...")
        self.desc_input.setFixedHeight(75)
        sg_layout.addWidget(self.desc_input)

        # Target Audience
        lbl_aud = QLabel("Target Audience & Reader Persona")
        lbl_aud.setObjectName("caption")
        sg_layout.addWidget(lbl_aud)
        self.audience_input = QLineEdit()
        self.audience_input.setPlaceholderText("e.g. Senior Backend Engineers, CTOs, Technical Architects")
        self.audience_input.setFixedHeight(34)
        sg_layout.addWidget(self.audience_input)

        # Voice and Tone
        lbl_tone = QLabel("Editorial Voice & Tone Guidelines")
        lbl_tone.setObjectName("caption")
        sg_layout.addWidget(lbl_tone)
        self.brand_tone_input = QLineEdit()
        self.brand_tone_input.setPlaceholderText("e.g. Pragmatic, authoritative, analytical, concise")
        self.brand_tone_input.setFixedHeight(34)
        sg_layout.addWidget(self.brand_tone_input)

        # Writing Guidelines & Restrictions
        lbl_rules = QLabel("Editorial Rules, Preferred Terminology & Restrictions")
        lbl_rules.setObjectName("caption")
        sg_layout.addWidget(lbl_rules)
        self.editorial_rules_input = QTextEdit()
        self.editorial_rules_input.setPlaceholderText(
            "List specific guidelines, phrases to use, buzzwords to avoid, and editorial standards..."
        )
        self.editorial_rules_input.setFixedHeight(85)
        sg_layout.addWidget(self.editorial_rules_input)

        sg_layout.addStretch()
        sg_scroll.setWidget(sg_inner)

        tab_style_layout = QVBoxLayout(tab_style_guide)
        tab_style_layout.setContentsMargins(0, 0, 0, 0)
        tab_style_layout.addWidget(sg_scroll)
        self.tabs.addTab(tab_style_guide, "Editorial Style Guide")

        # Tab 2: Product Catalog
        tab_products = QWidget()
        prod_layout = QVBoxLayout(tab_products)
        prod_layout.setContentsMargins(18, 16, 18, 16)
        prod_layout.setSpacing(10)

        lbl_prod_info = QLabel("Indexed Products & Features for Contextual Mention")
        lbl_prod_info.setObjectName("caption")
        prod_layout.addWidget(lbl_prod_info)

        self.prod_list = QListWidget()
        prod_layout.addWidget(self.prod_list)

        prod_btn_row = QHBoxLayout()
        btn_add_prod = QPushButton("+ Add Product")
        btn_add_prod.setFixedHeight(32)
        btn_add_prod.clicked.connect(self.add_product)
        prod_btn_row.addWidget(btn_add_prod)

        btn_del_prod = QPushButton("Remove Selected")
        btn_del_prod.setObjectName("dangerBtn")
        btn_del_prod.setFixedHeight(32)
        btn_del_prod.clicked.connect(self.del_product)
        prod_btn_row.addWidget(btn_del_prod)
        prod_btn_row.addStretch()
        prod_layout.addLayout(prod_btn_row)

        self.tabs.addTab(tab_products, "Product Catalog")

        # Tab 3: Internal Links Inventory
        tab_links = QWidget()
        link_layout = QVBoxLayout(tab_links)
        link_layout.setContentsMargins(18, 16, 18, 16)
        link_layout.setSpacing(10)

        lbl_link_info = QLabel("Target Internal URLs for Organic Cross-Linking")
        lbl_link_info.setObjectName("caption")
        link_layout.addWidget(lbl_link_info)

        self.url_list = QListWidget()
        link_layout.addWidget(self.url_list)

        link_btn_row = QHBoxLayout()
        btn_add_link = QPushButton("+ Add Internal Link")
        btn_add_link.setFixedHeight(32)
        btn_add_link.clicked.connect(self.add_url)
        link_btn_row.addWidget(btn_add_link)

        btn_del_link = QPushButton("Remove Selected")
        btn_del_link.setObjectName("dangerBtn")
        btn_del_link.setFixedHeight(32)
        btn_del_link.clicked.connect(self.del_url)
        link_btn_row.addWidget(btn_del_link)
        link_btn_row.addStretch()
        link_layout.addLayout(link_btn_row)

        self.tabs.addTab(tab_links, "Internal Links")

        # Tab 4: Publishing & Next.js Target
        tab_publish = QWidget()
        pub_layout = QVBoxLayout(tab_publish)
        pub_layout.setContentsMargins(18, 16, 18, 16)
        pub_layout.setSpacing(14)

        self.nextjs_enabled = QCheckBox("Enable automated Next.js blog sync on export")
        pub_layout.addWidget(self.nextjs_enabled)

        lbl_cont = QLabel("Next.js Content Directory Path (e.g. apps/web/content/posts)")
        lbl_cont.setObjectName("caption")
        pub_layout.addWidget(lbl_cont)

        row_cont = QHBoxLayout()
        self.nextjs_content_dir = QLineEdit()
        self.nextjs_content_dir.setFixedHeight(34)
        row_cont.addWidget(self.nextjs_content_dir)

        btn_pick_cont = QPushButton("Browse...")
        btn_pick_cont.setFixedHeight(34)
        btn_pick_cont.clicked.connect(lambda: self.browse_directory(self.nextjs_content_dir))
        row_cont.addWidget(btn_pick_cont)
        pub_layout.addLayout(row_cont)

        lbl_img = QLabel("Next.js Public Media Directory (e.g. apps/web/public/images/blog)")
        lbl_img.setObjectName("caption")
        pub_layout.addWidget(lbl_img)

        row_img = QHBoxLayout()
        self.nextjs_images_dir = QLineEdit()
        self.nextjs_images_dir.setFixedHeight(34)
        row_img.addWidget(self.nextjs_images_dir)

        btn_pick_img = QPushButton("Browse...")
        btn_pick_img.setFixedHeight(34)
        btn_pick_img.clicked.connect(lambda: self.browse_directory(self.nextjs_images_dir))
        row_img.addWidget(btn_pick_img)
        pub_layout.addLayout(row_img)

        self.btn_test_nextjs = QPushButton("Verify Next.js Directory Access")
        self.btn_test_nextjs.setFixedHeight(34)
        self.btn_test_nextjs.clicked.connect(self.test_nextjs)
        pub_layout.addWidget(self.btn_test_nextjs)

        pub_layout.addStretch()
        self.tabs.addTab(tab_publish, "Publishing Integration")

        self.right_layout.addWidget(self.tabs)
        root_layout.addWidget(right_container, 1)

        self.refresh_projects()

    def refresh_projects(self):
        """Reloads project list from service, preserving active selection if present."""
        self.project_list.blockSignals(True)
        self.project_list.clear()
        projects = self.service.list_projects()
        target_row = 0
        for idx, p in enumerate(projects):
            self.project_list.addItem(p.name)
            if self.current_project_id and p.id == self.current_project_id:
                target_row = idx

        if projects:
            self.project_list.setCurrentRow(target_row)
            self.project_list.blockSignals(False)
            self.load_project()
        else:
            self.project_list.blockSignals(False)
            self.new_project()

    def load_project(self):
        """Loads selected project details into the form."""
        row = self.project_list.currentRow()
        projects = self.service.list_projects()
        if 0 <= row < len(projects):
            p = projects[row]
            self.current_project_id = p.id
            self.name_input.setText(p.name)
            self.desc_input.setPlainText(p.description or "")
            self.brand_tone_input.setText(p.brand_profile.tone or "")
            self.audience_input.setText(p.brand_profile.target_audience or "")
            self.editorial_rules_input.setPlainText(p.brand_profile.writing_style or "")

            self.lbl_editing_project.setText(f"Editorial Style Guide: {p.name}")

            # Populate products
            self.prod_list.clear()
            for prod in p.products:
                self.prod_list.addItem(f"{prod.name} — {prod.description or ''}")

            # Populate URLs
            self.url_list.clear()
            for url in p.internal_links:
                self.url_list.addItem(f"{url.title} ({url.url})")

            # Next.js Settings
            if p.nextjs_integration:
                self.nextjs_enabled.setChecked(p.nextjs_integration.enabled)
                self.nextjs_content_dir.setText(p.nextjs_integration.content_directory or "")
                self.nextjs_images_dir.setText(p.nextjs_integration.image_directory or "")
            else:
                self.nextjs_enabled.setChecked(False)
                self.nextjs_content_dir.clear()
                self.nextjs_images_dir.clear()

    def new_project(self):
        """Resets the form to create a new project."""
        self.current_project_id = None
        self.name_input.clear()
        self.desc_input.clear()
        self.brand_tone_input.clear()
        self.audience_input.clear()
        self.editorial_rules_input.clear()
        self.prod_list.clear()
        self.url_list.clear()
        self.nextjs_enabled.setChecked(False)
        self.nextjs_content_dir.clear()
        self.nextjs_images_dir.clear()
        self.lbl_editing_project.setText("Create New Project & Style Guide")
        self.name_input.setFocus()

    def save_project(self):
        """Saves current project form."""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Project name is required.")
            return

        desc = self.desc_input.toPlainText().strip()
        tone = self.brand_tone_input.text().strip()

        if self.current_project_id:
            proj = self.service.get_project(self.current_project_id)
            if not proj:
                QMessageBox.warning(self, "Error", "Project not found.")
                return
            proj.name = name
            proj.description = desc
            proj.brand_profile.tone = tone
            proj.brand_profile.target_audience = self.audience_input.text().strip()
            proj.brand_profile.writing_style = self.editorial_rules_input.toPlainText().strip()

            proj.nextjs_integration.enabled = self.nextjs_enabled.isChecked()
            proj.nextjs_integration.content_directory = self.nextjs_content_dir.text().strip()
            proj.nextjs_integration.image_directory = self.nextjs_images_dir.text().strip()

            self.service.update_project(proj)
        else:
            proj = self.service.create_project(name=name, description=desc)
            proj.brand_profile.tone = tone
            proj.brand_profile.target_audience = self.audience_input.text().strip()
            proj.brand_profile.writing_style = self.editorial_rules_input.toPlainText().strip()

            proj.nextjs_integration.enabled = self.nextjs_enabled.isChecked()
            proj.nextjs_integration.content_directory = self.nextjs_content_dir.text().strip()
            proj.nextjs_integration.image_directory = self.nextjs_images_dir.text().strip()

            self.service.update_project(proj)
            self.current_project_id = proj.id

        self.refresh_projects()
        if self.main_window and hasattr(self.main_window, "refresh_project_switcher"):
            self.main_window.refresh_project_switcher()

    def delete_project(self):
        """Deletes the active project."""
        if not self.current_project_id:
            return
        ans = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to permanently delete this project and style guide?",
            QMessageBox.Yes | QMessageBox.No
        )
        if ans == QMessageBox.Yes:
            self.service.repo.delete(self.current_project_id)
            self.refresh_projects()
            if self.main_window and hasattr(self.main_window, "refresh_project_switcher"):
                self.main_window.refresh_project_switcher()

    def add_product(self):
        """Adds a product via prompt or dialog."""
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
            return
        proj.products.append(Product(name=name, description=desc))
        self.service.update_project(proj)
        self.load_project()

    def del_product(self):
        if not self.current_project_id:
            return
        row = self.prod_list.currentRow()
        if row < 0:
            return
        proj = self.service.get_project(self.current_project_id)
        if not proj or row >= len(proj.products):
            return
        proj.products.pop(row)
        self.service.update_project(proj)
        self.load_project()

    def add_url(self):
        """Adds an internal URL via prompt or dialog."""
        if not self.current_project_id:
            QMessageBox.warning(self, "Save First", "Please save the project first.")
            return

        title, ok1 = QInputDialog.getText(self, "Link Title", "Link Title:")
        if not ok1 or not title:
            return
        url, ok2 = QInputDialog.getText(self, "Target URL", "Link URL (http://... or /...):")
        if not ok2 or not url:
            return

        try:
            link = InternalLink(title=title, url=url)
            proj = self.service.get_project(self.current_project_id)
            if not proj:
                return
            proj.internal_links.append(link)
            self.service.update_project(proj)
            self.load_project()
        except Exception as e:
            QMessageBox.warning(self, "Invalid URL", f"Please enter a valid URL: {e}")

    def del_url(self):
        if not self.current_project_id:
            return
        row = self.url_list.currentRow()
        if row < 0:
            return
        proj = self.service.get_project(self.current_project_id)
        if not proj or row >= len(proj.internal_links):
            return
        proj.internal_links.pop(row)
        self.service.update_project(proj)
        self.load_project()

    def browse_directory(self, target_line_edit: QLineEdit):
        folder = QFileDialog.getExistingDirectory(self, "Select Directory")
        if folder:
            target_line_edit.setText(folder)

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
            QMessageBox.information(self, "Success", "Looks good! Directory is writable.")
        except Exception as e:
            QMessageBox.warning(self, "Test Failed", str(e))
