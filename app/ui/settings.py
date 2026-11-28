"""Google Gemini configuration, model selection, reasoning budget, and API key management view."""

import os
import platform
from typing import Optional, List, Tuple
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QMessageBox,
    QScrollArea, QFrame, QDialog, QTextEdit
)
from PySide6.QtCore import QThread, Signal, QUrl, Qt
from PySide6.QtGui import QDesktopServices
from app.core.constants import APP_NAME, APP_VERSION
from app.core.config import save_config_value, get_thinking_level
from app.providers.gemini import GeminiProvider


class TestConnectionThread(QThread):
    """Asynchronously runs diagnostics against Google Gemini."""
    __test__ = False
    result = Signal(bool, str)

    def __init__(self, api_key: str = "", model: str = "gemini-3.8-flash"):
        super().__init__()
        self.api_key = api_key
        self.model = model

    def run(self):
        try:
            success, msg, _ = GeminiProvider.diagnose_connection(
                api_key=self.api_key, model=self.model
            )
            self.result.emit(success, msg)
        except Exception as e:
            self.result.emit(False, f"Connection failed (Google Gemini): {str(e)}")


class DiscoverModelsThread(QThread):
    """Discovers accessible Gemini models for the configured account."""
    __test__ = False
    finished_discovery = Signal(bool, list, str)

    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key

    def run(self):
        try:
            models = GeminiProvider.list_available_models(self.api_key)
            self.finished_discovery.emit(True, models, f"Discovered {len(models)} accessible models.")
        except Exception as e:
            self.finished_discovery.emit(False, [], str(e))


class SettingsWidget(QWidget):
    """Dedicated configuration studio for Google Gemini AI models, credentials, and storage."""
    settings_updated = Signal()

    CANDIDATE_MODELS: List[Tuple[str, str]] = [
        ("gemini-3.8-flash", "Recommended Default"),
        ("gemini-3.5-flash-lite", "Fast & Lightweight"),
        ("gemini-4-hydrogen", "High Performance Preview"),
        ("gemini-4-argon", "Balanced Multimodal Preview"),
        ("gemini-4-carbon", "Heavy Reasoning Preview"),
    ]

    def __init__(self):
        super().__init__()
        self.discovery_thread: Optional[DiscoverModelsThread] = None
        self.tester: Optional[TestConnectionThread] = None

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        # Responsive scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(36, 24, 36, 24)
        layout.setSpacing(18)

        # Header
        lbl_head = QLabel("Settings & Gemini Model Studio")
        lbl_head.setObjectName("h1")
        layout.addWidget(lbl_head)

        lbl_sub = QLabel(
            "Configure Google Gemini credentials, model selection, reasoning budget, and publishing storage."
        )
        lbl_sub.setObjectName("subtitle")
        layout.addWidget(lbl_sub)

        # ---------------------------------------------------------------------
        # Card 1: Google Gemini API & Credentials
        # ---------------------------------------------------------------------
        card_api, api_layout = self._create_card_with_layout(
            "GOOGLE GEMINI API & CREDENTIALS",
            "Manage Google AI Studio API key and test live connectivity"
        )
        api_layout.setSpacing(12)

        # API Key Row
        self.row_api = QHBoxLayout()
        self.lbl_key = QLabel("Gemini API Key:")
        self.lbl_key.setObjectName("caption")
        self.lbl_key.setFixedWidth(180)
        self.row_api.addWidget(self.lbl_key)

        self.api_input = QLineEdit()
        self.api_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_input.setPlaceholderText("Enter Google Gemini API Key (starts with AIza...)")
        self.api_input.setFixedHeight(34)
        self.api_input.setText(os.getenv("GEMINI_API_KEY", ""))
        self.row_api.addWidget(self.api_input, 1)

        self.btn_toggle_api = QPushButton("Show")
        self.btn_toggle_api.setObjectName("ghostBtn")
        self.btn_toggle_api.setFixedHeight(34)
        self.btn_toggle_api.setFixedWidth(64)
        self.btn_toggle_api.clicked.connect(self.toggle_api_visibility)
        self.row_api.addWidget(self.btn_toggle_api)

        self.btn_save_key = QPushButton("Save Key")
        self.btn_save_key.setObjectName("primaryBtn")
        self.btn_save_key.setFixedHeight(34)
        self.btn_save_key.clicked.connect(self.save_provider_settings)
        self.row_api.addWidget(self.btn_save_key)

        self.btn_test = QPushButton("Test Connection")
        self.btn_test.setFixedHeight(34)
        self.btn_test.clicked.connect(self.test_connection)
        self.row_api.addWidget(self.btn_test)

        api_layout.addLayout(self.row_api)

        self.lbl_status = QLabel("Google Gemini engine initialized.")
        self.lbl_status.setStyleSheet("color: #57534E; font-size: 12px;")
        api_layout.addWidget(self.lbl_status)

        layout.addWidget(card_api)

        # ---------------------------------------------------------------------
        # Card 2: Gemini Model Selection & Reasoning Configuration
        # ---------------------------------------------------------------------
        card_model, model_layout = self._create_card_with_layout(
            "GEMINI MODEL SELECTION & REASONING CONFIGURATION",
            "Select active model, reasoning depth, and discover account models"
        )
        model_layout.setSpacing(10)

        lbl_m = QLabel("Active Gemini Model")
        lbl_m.setObjectName("caption")
        model_layout.addWidget(lbl_m)

        row_model = QHBoxLayout()
        row_model.setSpacing(8)

        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.setFixedHeight(34)
        for m_id, m_label in self.CANDIDATE_MODELS:
            self.model_combo.addItem(f"{m_id} — {m_label}", m_id)

        saved_model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        found = False
        for i in range(self.model_combo.count()):
            if self.model_combo.itemData(i) == saved_model:
                self.model_combo.setCurrentIndex(i)
                found = True
                break
        if not found and saved_model:
            self.model_combo.addItem(f"{saved_model} (Custom)", saved_model)
            self.model_combo.setCurrentIndex(self.model_combo.count() - 1)

        row_model.addWidget(self.model_combo, 1)

        self.btn_discover = QPushButton("Discover Models")
        self.btn_discover.setFixedHeight(34)
        self.btn_discover.clicked.connect(self.discover_models)
        row_model.addWidget(self.btn_discover)

        model_layout.addLayout(row_model)

        row_meta = QHBoxLayout()
        self.lbl_active_model = QLabel(f"Active Model ID: {saved_model}")
        self.lbl_active_model.setStyleSheet("color: #57534E; font-size: 12px; font-weight: 500;")
        row_meta.addWidget(self.lbl_active_model)

        row_meta.addStretch()

        self.lbl_th = QLabel("Gemini Thinking Budget:")
        self.lbl_th.setStyleSheet("color: #57534E; font-size: 12px;")
        row_meta.addWidget(self.lbl_th)

        self.combo_thinking = QComboBox()
        self.combo_thinking.addItems(["medium", "low", "high"])
        self.combo_thinking.setFixedHeight(28)
        current_thinking = get_thinking_level()
        idx_th = self.combo_thinking.findText(current_thinking)
        if idx_th >= 0:
            self.combo_thinking.setCurrentIndex(idx_th)
        self.combo_thinking.currentTextChanged.connect(self.on_thinking_changed)
        row_meta.addWidget(self.combo_thinking)

        model_layout.addLayout(row_meta)
        layout.addWidget(card_model)

        # ---------------------------------------------------------------------
        # Card 3: Storage & Local Publishing Defaults
        # ---------------------------------------------------------------------
        card_storage, store_layout = self._create_card_with_layout(
            "LOCAL PUBLISHING & STORAGE",
            "File paths for documents, drafts, and research"
        )
        store_layout.setSpacing(6)

        store_info = [
            ("Projects Directory:", os.path.abspath("data/projects")),
            ("Articles Storage Directory:", os.path.abspath("data/articles")),
            ("Drafts & Generation Cache:", os.path.abspath("data/generation")),
            ("Research Database:", os.path.abspath("data/research")),
        ]
        for title, path in store_info:
            row_s = QHBoxLayout()
            row_s.setSpacing(12)
            lbl_t = QLabel(title)
            lbl_t.setMinimumWidth(185)
            lbl_t.setStyleSheet("color: #57534E; font-size: 12px; font-weight: 500;")
            lbl_p = QLabel(path)
            lbl_p.setWordWrap(True)
            lbl_p.setStyleSheet("color: #8C877F; font-size: 12px; font-family: monospace;")
            row_s.addWidget(lbl_t)
            row_s.addWidget(lbl_p, 1)
            store_layout.addLayout(row_s)

        layout.addWidget(card_storage)

        # ---------------------------------------------------------------------
        # Card 4: System Information
        # ---------------------------------------------------------------------
        card_sys, sys_layout = self._create_card_with_layout(
            "SYSTEM RUNTIME INFORMATION",
            "Local environment and dependencies"
        )
        sys_layout.setSpacing(6)

        sys_info = [
            ("Application Version:", f"{APP_NAME} v{APP_VERSION}"),
            ("Python Runtime:", f"{platform.python_version()} ({platform.architecture()[0]})"),
            ("Operating System:", f"{platform.system()} {platform.release()}"),
            ("Framework:", "PySide6 (Qt for Python 6.8+)"),
            ("AI Intelligence Engine:", "Google Gemini (Gemini 3.8 & 4 Series via google-genai SDK)"),
        ]
        for title, val in sys_info:
            row_inf = QHBoxLayout()
            row_inf.setSpacing(12)
            lbl_t = QLabel(title)
            lbl_t.setMinimumWidth(185)
            lbl_t.setStyleSheet("color: #57534E; font-size: 12px; font-weight: 500;")
            lbl_v = QLabel(val)
            lbl_v.setWordWrap(True)
            lbl_v.setStyleSheet("color: #8C877F; font-size: 12px;")
            row_inf.addWidget(lbl_t)
            row_inf.addWidget(lbl_v, 1)
            sys_layout.addLayout(row_inf)

        layout.addWidget(card_sys)

        # ---------------------------------------------------------------------
        # Card 5: Support & Transparency
        # ---------------------------------------------------------------------
        card_trans, trans_layout = self._create_card_with_layout(
            "SUPPORT & TRANSPARENCY",
            "Privacy policy, zero ads, and rate-limiting safeguards"
        )
        trans_layout.setSpacing(12)

        row_ad = QHBoxLayout()
        row_ad.setSpacing(12)
        lbl_ad_icon = QLabel("🛡️")
        lbl_ad_icon.setStyleSheet("font-size: 16px;")
        row_ad.addWidget(lbl_ad_icon)

        col_ad = QVBoxLayout()
        col_ad.setSpacing(2)
        lbl_ad_title = QLabel("100% Ad-Free & Local-First")
        lbl_ad_title.setStyleSheet("color: #1C1917; font-size: 13px; font-weight: 600;")
        col_ad.addWidget(lbl_ad_title)
        lbl_ad_sub = QLabel(
            "Zero advertisements, zero analytics tracking, and zero telemetry. All projects, brand profiles, "
            "drafts, and articles are saved locally on your disk."
        )
        lbl_ad_sub.setWordWrap(True)
        lbl_ad_sub.setStyleSheet("color: #78716C; font-size: 12px;")
        col_ad.addWidget(lbl_ad_sub)
        row_ad.addLayout(col_ad, 1)
        trans_layout.addLayout(row_ad)

        div_t = QFrame()
        div_t.setFrameShape(QFrame.Shape.HLine)
        div_t.setStyleSheet("color: #E7E5E4;")
        trans_layout.addWidget(div_t)

        row_cap = QHBoxLayout()
        row_cap.setSpacing(12)
        lbl_cap_icon = QLabel("⚡")
        lbl_cap_icon.setStyleSheet("font-size: 16px;")
        row_cap.addWidget(lbl_cap_icon)

        col_cap = QVBoxLayout()
        col_cap.setSpacing(2)
        lbl_cap_title = QLabel("Direct Gemini Connection & Safeguards")
        lbl_cap_title.setStyleSheet("color: #1C1917; font-size: 13px; font-weight: 600;")
        col_cap.addWidget(lbl_cap_title)
        lbl_cap_sub = QLabel(
            "Requests connect directly to Google Generative AI endpoints. Automatic exponential backoff "
            "and retry guards prevent API flood."
        )
        lbl_cap_sub.setWordWrap(True)
        lbl_cap_sub.setStyleSheet("color: #78716C; font-size: 12px;")
        col_cap.addWidget(lbl_cap_sub)
        row_cap.addLayout(col_cap, 1)

        badge_direct = QLabel("Direct Mode")
        badge_direct.setStyleSheet("""
            background-color: #FEF3C7;
            color: #92400E;
            border: 1px solid #FDE68A;
            border-radius: 4px;
            padding: 4px 8px;
            font-size: 11px;
            font-weight: 600;
        """)
        row_cap.addWidget(badge_direct)
        trans_layout.addLayout(row_cap)
        layout.addWidget(card_trans)

        # ---------------------------------------------------------------------
        # Card 6: About (Reference Design)
        # ---------------------------------------------------------------------
        card_about, about_layout = self._create_card_with_layout(
            "ABOUT",
            "Application metadata, developer, and licensing"
        )
        about_layout.setSpacing(10)

        # App Identity
        app_header_row = QHBoxLayout()
        app_header_row.setSpacing(12)
        lbl_app_icon = QLabel("✒️")
        lbl_app_icon.setStyleSheet("font-size: 26px; padding: 2px;")
        app_header_row.addWidget(lbl_app_icon)

        app_title_col = QVBoxLayout()
        app_title_col.setSpacing(2)
        lbl_app_name = QLabel(APP_NAME)
        lbl_app_name.setStyleSheet(
            "color: #1C1917; font-size: 16px; font-weight: 700; font-family: 'Newsreader', serif;"
        )
        app_title_col.addWidget(lbl_app_name)
        lbl_app_ver = QLabel(f"{APP_VERSION} (Build 2026.11)")
        lbl_app_ver.setStyleSheet("color: #78716C; font-size: 12px;")
        app_title_col.addWidget(lbl_app_ver)
        app_header_row.addLayout(app_title_col, 1)
        about_layout.addLayout(app_header_row)

        metadata_items = [
            ("Application Package ID", "com.rafayshhh.blogforge", None),
            ("Developer", "Muhammad Abdul Rafay", None),
            ("Website", "https://github.com/rafayshhh/blogforge", self.open_website),
            ("Privacy Policy", "Local-First Architecture • Zero Telemetry", self.show_privacy_policy),
            ("Terms of Service", "MIT Open Source License • Safe Commercial Use", self.show_terms_of_service),
        ]

        for label_text, val_text, action_fn in metadata_items:
            div_m = QFrame()
            div_m.setFrameShape(QFrame.Shape.HLine)
            div_m.setStyleSheet("color: #F0EDE8;")
            about_layout.addWidget(div_m)

            m_row = QHBoxLayout()
            m_row.setContentsMargins(0, 4, 0, 4)
            m_col = QVBoxLayout()
            m_col.setSpacing(2)

            lbl_title = QLabel(label_text)
            lbl_title.setStyleSheet("color: #1C1917; font-size: 13px; font-weight: 500;")
            m_col.addWidget(lbl_title)

            lbl_detail = QLabel(val_text)
            detail_color = "#C2410C" if action_fn else "#78716C"
            lbl_detail.setStyleSheet(f"color: {detail_color}; font-size: 12px;")
            m_col.addWidget(lbl_detail)
            m_row.addLayout(m_col, 1)

            if action_fn:
                btn_act = QPushButton("Open →" if "http" in val_text else "View")
                btn_act.setObjectName("ghostBtn")
                btn_act.setFixedHeight(26)
                btn_act.setCursor(Qt.PointingHandCursor)
                btn_act.clicked.connect(action_fn)
                m_row.addWidget(btn_act)

            about_layout.addLayout(m_row)

        div_lic = QFrame()
        div_lic.setFrameShape(QFrame.Shape.HLine)
        div_lic.setStyleSheet("color: #F0EDE8;")
        about_layout.addWidget(div_lic)

        lic_row = QHBoxLayout()
        lic_row.setContentsMargins(0, 4, 0, 4)
        lbl_lic_icon = QLabel("📄")
        lbl_lic_icon.setStyleSheet("font-size: 14px;")
        lic_row.addWidget(lbl_lic_icon)

        lbl_lic_text = QLabel("Open Source Licenses")
        lbl_lic_text.setStyleSheet("color: #1C1917; font-size: 13px; font-weight: 500;")
        lic_row.addWidget(lbl_lic_text, 1)

        btn_lic = QPushButton("›")
        btn_lic.setObjectName("ghostBtn")
        btn_lic.setStyleSheet("font-size: 18px; font-weight: 600; padding: 0 10px;")
        btn_lic.setFixedHeight(26)
        btn_lic.setCursor(Qt.PointingHandCursor)
        btn_lic.clicked.connect(self.show_licenses_dialog)
        lic_row.addWidget(btn_lic)

        about_layout.addLayout(lic_row)
        layout.addWidget(card_about)

        layout.addStretch()

        scroll.setWidget(container)
        root_layout.addWidget(scroll)

        self.model_combo.currentIndexChanged.connect(self.on_model_changed)
        self.model_combo.editTextChanged.connect(self._on_model_edit_text)
        self._refresh_key_status()

    def _create_card(self, title: str, subtitle: str) -> QFrame:
        card, _ = self._create_card_with_layout(title, subtitle)
        return card

    def _create_card_with_layout(self, title: str, subtitle: str) -> Tuple[QFrame, QVBoxLayout]:
        card = QFrame()
        card.setObjectName("settingsCard")
        card.setStyleSheet("""
            #settingsCard {
                background-color: #FFFFFF;
                border: 1px solid #E0DDD5;
                border-radius: 6px;
            }
            #settingsCard QLabel {
                background-color: transparent;
                border: none;
                border-radius: 0px;
                padding: 0px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(8)

        lbl_head = QLabel(title)
        lbl_head.setStyleSheet(
            "color: #9A3412; font-size: 11px; font-weight: 700; letter-spacing: 0.7px;"
        )
        card_layout.addWidget(lbl_head)

        if subtitle:
            lbl_sub = QLabel(subtitle)
            lbl_sub.setWordWrap(True)
            lbl_sub.setStyleSheet("color: #78716C; font-size: 12px;")
            card_layout.addWidget(lbl_sub)

        div_head = QFrame()
        div_head.setFrameShape(QFrame.Shape.HLine)
        div_head.setStyleSheet("color: #EFECE4;")
        card_layout.addWidget(div_head)

        return card, card_layout

    def get_selected_provider(self) -> str:
        return "gemini"

    def _refresh_key_status(self):
        key_len = len(self.api_input.text().strip())
        if key_len:
            self.lbl_status.setText(f"Google Gemini configured ({key_len} char API key present).")
        else:
            self.lbl_status.setText("Google Gemini API key is not configured.")
        self.lbl_status.setStyleSheet("color: #57534E; font-size: 12px;")

    def toggle_api_visibility(self):
        if self.api_input.echoMode() == QLineEdit.EchoMode.Password:
            self.api_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_toggle_api.setText("Hide")
        else:
            self.api_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_toggle_api.setText("Show")

    def save_provider_settings(self):
        key = self.api_input.text().strip()
        if not key:
            QMessageBox.warning(self, "Invalid Key", "Gemini API key cannot be empty.")
            return

        model = self.get_selected_model()
        save_config_value("AI_PROVIDER", "gemini")
        save_config_value("GEMINI_API_KEY", key)
        save_config_value("GEMINI_MODEL", model)

        self.lbl_status.setText(f"✓ Settings for Google Gemini ({model}) saved successfully.")
        self.lbl_status.setStyleSheet("color: #15803D; font-size: 12px; font-weight: 500;")
        self.settings_updated.emit()

    def save_api_key(self):
        """Backwards-compatible alias for saving provider credentials."""
        self.save_provider_settings()

    def get_selected_model(self) -> str:
        raw_text = self.model_combo.currentText().strip()
        idx = self.model_combo.currentIndex()
        if idx >= 0 and raw_text == self.model_combo.itemText(idx).strip():
            current_data = self.model_combo.itemData(idx)
            if current_data:
                return str(current_data)
        if " — " in raw_text:
            return raw_text.split(" — ")[0].strip()
        return raw_text

    def _on_model_edit_text(self, text: str) -> None:
        cleaned = text.split(" — ")[0].strip() if " — " in text else text.strip()
        if cleaned:
            self.lbl_active_model.setText(f"Active Model ID: {cleaned}")
            save_config_value("GEMINI_MODEL", cleaned)
            self.settings_updated.emit()

    def on_model_changed(self):
        model_id = self.get_selected_model()
        if model_id:
            self.lbl_active_model.setText(f"Active Model ID: {model_id}")
            save_config_value("GEMINI_MODEL", model_id)
            self.settings_updated.emit()

    def cleanup_threads(self) -> None:
        """Waits briefly for active background threads before window shutdown."""
        if self.tester and self.tester.isRunning():
            self.tester.wait(1500)
        if self.discovery_thread and self.discovery_thread.isRunning():
            self.discovery_thread.wait(1500)

    def on_thinking_changed(self, text: str):
        save_config_value("GEMINI_THINKING_LEVEL", text)
        self.settings_updated.emit()

    def discover_models(self):
        key = self.api_input.text().strip()
        if not key:
            QMessageBox.warning(self, "Key Required", "Enter a Gemini API key first to discover models.")
            return

        self.btn_discover.setEnabled(False)
        self.lbl_status.setText("Discovering accessible models from Google Gemini API...")
        self.lbl_status.setStyleSheet("color: #1E3A5F; font-size: 12px;")

        self.discovery_thread = DiscoverModelsThread(api_key=key)
        self.discovery_thread.finished_discovery.connect(self.on_models_discovered)
        self.discovery_thread.start()

    def on_models_discovered(self, success: bool, models: list, message: str):
        self.btn_discover.setEnabled(True)
        if success and models:
            self.lbl_status.setText(f"Verified {len(models)} accessible models from your Google AI Studio account.")
            self.lbl_status.setStyleSheet("color: #15803D; font-size: 12px; font-weight: 500;")

            existing_models = [self.model_combo.itemData(i) for i in range(self.model_combo.count())]
            for m in models:
                if m not in existing_models:
                    self.model_combo.addItem(f"{m} (Verified)", m)
        else:
            self.lbl_status.setText(f"✕ {message}")
            self.lbl_status.setStyleSheet("color: #B91C1C; font-size: 12px;")

    def test_connection(self):
        key = self.api_input.text().strip()
        selected_model = self.get_selected_model()

        self.btn_test.setEnabled(False)
        self.lbl_status.setText(f"Testing connection to Google Gemini with model '{selected_model}'...")
        self.lbl_status.setStyleSheet("color: #1E3A5F; font-size: 12px;")

        self.tester = TestConnectionThread(api_key=key, model=selected_model)
        self.tester.result.connect(self.on_test_result)
        self.tester.start()

    def on_test_result(self, success: bool, message: str):
        self.btn_test.setEnabled(True)
        if success:
            self.lbl_status.setText(f"✓ {message}")
            self.lbl_status.setStyleSheet("color: #15803D; font-size: 12px; font-weight: 500;")
        else:
            self.lbl_status.setText(f"✕ {message}")
            self.lbl_status.setStyleSheet("color: #B91C1C; font-size: 12px;")

    def open_website(self):
        """Opens the official BlogForge repository in user default browser."""
        QDesktopServices.openUrl(QUrl("https://github.com/rafayshhh/blogforge"))

    def show_privacy_policy(self):
        """Displays the local-first transparency policy."""
        msg = (
            "<h3>BlogForge Privacy & Local-First Architecture</h3>"
            "<p><b>Zero Telemetry & Local-First:</b> BlogForge operates completely on your local machine. "
            "Zero user data, telemetry, analytics, drafts, or article contents are transmitted to any external server "
            "except the official Google Gemini API when generating or researching content.</p>"
            "<p><b>API Key Security:</b> Your Google Gemini API key is stored locally in your "
            "workspace <code>.env</code> file and memory only. It is never transmitted to any third party.</p>"
            "<p><b>Developer:</b> Muhammad Abdul Rafay</p>"
        )
        dlg = QMessageBox(self)
        dlg.setWindowTitle("BlogForge — Privacy Policy")
        dlg.setText(msg)
        dlg.setTextFormat(Qt.TextFormat.RichText)
        dlg.exec()

    def show_terms_of_service(self):
        """Displays open source licensing and usage terms."""
        msg = (
            "<h3>BlogForge Terms of Service</h3>"
            "<p>BlogForge is released as open-source software under the <b>MIT License</b>.</p>"
            "<p>Permission is hereby granted, free of charge, to any person obtaining a copy "
            "of this software and associated documentation files, to deal in the Software without restriction, "
            "including without limitation the rights to use, copy, modify, merge, publish, distribute, "
            "sublicense, and/or sell copies of the Software.</p>"
            "<p>THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED.</p>"
            "<p><b>Developer:</b> Muhammad Abdul Rafay</p>"
        )
        dlg = QMessageBox(self)
        dlg.setWindowTitle("BlogForge — Terms of Service")
        dlg.setText(msg)
        dlg.setTextFormat(Qt.TextFormat.RichText)
        dlg.exec()

    def show_licenses_dialog(self):
        """Opens interactive viewer for open source components and licenses."""
        dlg = QDialog(self)
        dlg.setWindowTitle("BlogForge — Open Source Licenses")
        dlg.setFixedSize(580, 420)
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(12)

        lbl = QLabel("Open Source Components & Licenses")
        lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #1C1917;")
        lay.addWidget(lbl)

        txt = QTextEdit()
        txt.setReadOnly(True)
        txt.setStyleSheet(
            "background-color: #F9F8F6; border: 1px solid #E0DDD5; font-family: monospace; font-size: 11px;"
        )
        licenses_text = (
            "BlogForge is powered by open source software:\n\n"
            "• BlogForge (c) 2026 Muhammad Abdul Rafay — MIT License\n"
            "• PySide6 / Qt6 — LGPLv3 License\n"
            "• google-genai — Apache 2.0 License\n"
            "• Pydantic v2 — MIT License\n"
            "• Bleach & html5lib — Apache 2.0 License\n"
            "• Python-Markdown — BSD License\n"
            "• HTTPX — BSD-3-Clause License\n"
            "• PyYAML — MIT License\n"
            "• Rich — MIT License\n"
        )
        txt.setText(licenses_text)
        lay.addWidget(txt, 1)

        btn_close = QPushButton("Close")
        btn_close.setObjectName("primaryBtn")
        btn_close.setFixedHeight(32)
        btn_close.clicked.connect(dlg.accept)
        lay.addWidget(btn_close)

        dlg.exec()
