"""Google Gemini configuration, model selection, reasoning budget, and API key management view."""

import os
import platform
from typing import Optional, List, Tuple
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QMessageBox,
    QScrollArea, QFrame
)
from PySide6.QtCore import QThread, Signal
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
        ("gemini-3.8-flash", "Gemini 3.8 Flash — Recommended Default"),
        ("gemini-3.5-flash-lite", "Gemini 3.5 Flash-Lite — Fast & Lightweight"),
        ("gemini-4-hydrogen", "Gemini 4 Hydrogen — High Performance Preview"),
        ("gemini-4-argon", "Gemini 4 Argon — Balanced Multimodal Preview"),
        ("gemini-4-carbon", "Gemini 4 Carbon — Heavy Reasoning Preview"),
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
        card_api = self._create_card(
            "GOOGLE GEMINI API & CREDENTIALS",
            "Manage Google AI Studio API key and test live connectivity"
        )
        api_layout = QVBoxLayout(card_api)
        api_layout.setContentsMargins(18, 16, 18, 16)
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
        card_model = self._create_card(
            "GEMINI MODEL SELECTION & REASONING CONFIGURATION",
            "Select active model, reasoning depth, and discover account models"
        )
        model_layout = QVBoxLayout(card_model)
        model_layout.setContentsMargins(18, 16, 18, 16)
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
        card_storage = self._create_card(
            "LOCAL PUBLISHING & STORAGE",
            "File paths for documents, drafts, and research"
        )
        store_layout = QVBoxLayout(card_storage)
        store_layout.setContentsMargins(18, 16, 18, 16)
        store_layout.setSpacing(6)

        store_info = [
            ("Projects Directory:", os.path.abspath("data/projects")),
            ("Articles Storage Directory:", os.path.abspath("data/articles")),
            ("Drafts & Generation Cache:", os.path.abspath("data/generation")),
            ("Research Database:", os.path.abspath("data/research")),
        ]
        for title, path in store_info:
            row_s = QHBoxLayout()
            lbl_t = QLabel(title)
            lbl_t.setStyleSheet("color: #57534E; font-size: 12px; font-weight: 500;")
            lbl_p = QLabel(path)
            lbl_p.setStyleSheet("color: #8C877F; font-size: 12px; font-family: monospace;")
            row_s.addWidget(lbl_t)
            row_s.addWidget(lbl_p, 1)
            store_layout.addLayout(row_s)

        layout.addWidget(card_storage)

        # ---------------------------------------------------------------------
        # Card 4: System Information
        # ---------------------------------------------------------------------
        card_sys = self._create_card("SYSTEM RUNTIME INFORMATION", "Local environment and dependencies")
        sys_layout = QVBoxLayout(card_sys)
        sys_layout.setContentsMargins(18, 16, 18, 16)
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
            lbl_t = QLabel(title)
            lbl_t.setStyleSheet("color: #57534E; font-size: 12px; font-weight: 500;")
            lbl_v = QLabel(val)
            lbl_v.setStyleSheet("color: #8C877F; font-size: 12px;")
            row_inf.addWidget(lbl_t)
            row_inf.addWidget(lbl_v, 1)
            sys_layout.addLayout(row_inf)

        layout.addWidget(card_sys)
        layout.addStretch()

        scroll.setWidget(container)
        root_layout.addWidget(scroll)

        self.model_combo.currentIndexChanged.connect(self.on_model_changed)
        self._refresh_key_status()

    def _create_card(self, title: str, subtitle: str) -> QFrame:
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
        return card

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
        current_data = self.model_combo.currentData()
        if current_data:
            return current_data
        raw_text = self.model_combo.currentText().strip()
        if " — " in raw_text:
            return raw_text.split(" — ")[0].strip()
        return raw_text

    def on_model_changed(self):
        model_id = self.get_selected_model()
        self.lbl_active_model.setText(f"Active Model ID: {model_id}")
        save_config_value("GEMINI_MODEL", model_id)
        self.settings_updated.emit()

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
