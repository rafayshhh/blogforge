"""Application configuration, multi-provider model selection, and API key management view."""

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
from app.core.config import (
    save_config_value,
    get_active_provider_name,
)
from app.providers.factory import create_provider
from app.providers.gemini import GeminiProvider
from app.providers.anthropic import AnthropicProvider
from app.providers.openai import OpenAIProvider
from app.providers.custom_openai import CustomOpenAIProvider


class TestConnectionThread(QThread):
    """Asynchronously runs diagnostics against the configured AI provider."""
    __test__ = False
    result = Signal(bool, str)

    def __init__(
        self,
        provider_name: str = "gemini",
        api_key: str = "",
        model: str = "gemini-3.8-flash",
        base_url: Optional[str] = None
    ):
        super().__init__()
        self.provider_name = provider_name
        self.api_key = api_key
        self.model = model
        self.base_url = base_url

    def run(self):
        try:
            kwargs = {"api_key": self.api_key, "model": self.model}
            if self.base_url:
                kwargs["base_url"] = self.base_url

            p_lower = self.provider_name.lower().strip()
            if p_lower in ("gemini", "google"):
                from app.providers.gemini import GeminiProvider
                provider = GeminiProvider(api_key=self.api_key, default_model=self.model)
                response = provider.generate("Reply with exactly: OK")
                if not response or not response.text:
                    self.result.emit(False, f"Connection failed with model '{self.model}': empty response.")
                    return
                extra_info = ""
                try:
                    available = (
                        provider.list_available_models(self.api_key)
                        if hasattr(provider, "list_available_models") else []
                    )
                    if self.model in available:
                        extra_info = f" (Verified accessible; {len(available)} account models)"
                    else:
                        extra_info = f" (Model '{self.model}' active; {len(available)} account models)"
                except Exception:
                    pass
                self.result.emit(True, f"Connected successfully. Model: {self.model}{extra_info}")
                return
            elif p_lower in ("anthropic", "claude"):
                success, msg, _ = AnthropicProvider.diagnose_connection(
                    api_key=self.api_key, model=self.model, base_url=self.base_url
                )
            elif p_lower in ("openai", "chatgpt"):
                success, msg, _ = OpenAIProvider.diagnose_connection(
                    api_key=self.api_key, model=self.model, base_url=self.base_url
                )
            elif p_lower in ("cursor", "custom", "custom_openai"):
                success, msg, _ = CustomOpenAIProvider.diagnose_connection(
                    api_key=self.api_key, model=self.model, base_url=self.base_url
                )
            else:
                provider = create_provider(self.provider_name, api_key=self.api_key, default_model=self.model)
                resp = provider.generate("Reply with exactly: OK")
                success = bool(resp and resp.text)
                msg = f"Connected successfully to {self.provider_name}. Model '{self.model}' is active."

            self.result.emit(success, msg)
        except Exception as e:
            self.result.emit(False, f"Connection failed ({self.provider_name}): {str(e)}")


class DiscoverModelsThread(QThread):
    """Discovers accessible models for the active AI provider."""
    __test__ = False
    finished_discovery = Signal(bool, list, str)

    def __init__(self, provider_name: str, api_key: str, base_url: Optional[str] = None):
        super().__init__()
        self.provider_name = provider_name
        self.api_key = api_key
        self.base_url = base_url

    def run(self):
        try:
            p_lower = self.provider_name.lower().strip()
            if p_lower in ("gemini", "google"):
                models = GeminiProvider.list_available_models(self.api_key)
            elif p_lower in ("anthropic", "claude"):
                models = AnthropicProvider.list_available_models(self.api_key)
            elif p_lower in ("openai", "chatgpt"):
                models = OpenAIProvider.list_available_models(self.api_key, base_url=self.base_url)
            elif p_lower in ("cursor", "custom", "custom_openai"):
                models = CustomOpenAIProvider.list_available_models(self.api_key, base_url=self.base_url)
            else:
                models = []
            self.finished_discovery.emit(True, models, f"Discovered {len(models)} accessible models.")
        except Exception as e:
            self.finished_discovery.emit(False, [], str(e))


class SettingsWidget(QWidget):
    """Multi-provider configuration studio supporting Gemini, Claude, ChatGPT, and Cursor."""
    settings_updated = Signal()

    PROVIDER_CHOICES: List[Tuple[str, str]] = [
        ("gemini", "Google Gemini (Gemini 3.8 / 4 Series)"),
        ("anthropic", "Anthropic Claude (Claude 3.7 / 3.5 Sonnet & Haiku)"),
        ("openai", "OpenAI ChatGPT (GPT-4o, o1, o3-mini)"),
        ("cursor", "Cursor / Custom OpenAI-Compatible (Local & Proxy)"),
    ]

    PROVIDER_CANDIDATE_MODELS = {
        "gemini": [
            ("gemini-3.8-flash", "Gemini 3.8 Flash — Recommended Default"),
            ("gemini-3.5-flash-lite", "Gemini 3.5 Flash-Lite — Fast & Lightweight"),
            ("gemini-4-hydrogen", "Gemini 4 Hydrogen — High Performance"),
            ("gemini-4-argon", "Gemini 4 Argon — Balanced Multimodal"),
            ("gemini-4-carbon", "Gemini 4 Carbon — Heavy Reasoning"),
        ],
        "anthropic": [
            ("claude-3-5-sonnet-20241022", "Claude 3.5 Sonnet — Recommended Default"),
            ("claude-3-7-sonnet-20250219", "Claude 3.7 Sonnet — Hybrid Reasoning"),
            ("claude-3-5-haiku-20241022", "Claude 3.5 Haiku — Fast & Concise"),
            ("claude-3-opus-20240229", "Claude 3 Opus — Deep Analysis"),
        ],
        "openai": [
            ("gpt-4o", "GPT-4o — Recommended Multimodal Flagship"),
            ("gpt-4o-mini", "GPT-4o Mini — Fast & Cost-Efficient"),
            ("o3-mini", "o3-mini — Advanced STEM & Code Reasoning"),
            ("o1", "o1 — Complex Long-Horizon Reasoning"),
            ("gpt-4-turbo", "GPT-4 Turbo — Legacy High Precision"),
        ],
        "cursor": [
            ("cursor-small", "cursor-small — Default Cursor Fast Model"),
            ("deepseek-chat", "DeepSeek Chat (V3 / R1)"),
            ("claude-3-5-sonnet", "Claude 3.5 Sonnet (via Proxy/OpenRouter)"),
            ("gpt-4o", "GPT-4o (via Proxy/OpenRouter)"),
            ("meta-llama/llama-3.3-70b-instruct", "Llama 3.3 70B (via Ollama/OpenRouter)"),
        ],
    }

    def __init__(self):
        super().__init__()
        self.discovery_thread = None
        self.tester = None

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
        lbl_head = QLabel("Settings & Model Studio")
        lbl_head.setObjectName("h1")
        layout.addWidget(lbl_head)

        lbl_sub = QLabel(
            "Configure multi-provider AI credentials, model selection, custom endpoints, and publishing storage."
        )
        lbl_sub.setObjectName("subtitle")
        layout.addWidget(lbl_sub)

        # ---------------------------------------------------------------------
        # Card 1: AI Provider & Credentials
        # ---------------------------------------------------------------------
        card_api = self._create_card(
            "ACTIVE AI PROVIDER & CREDENTIALS",
            "Select active intelligence provider and manage API keys"
        )
        api_layout = QVBoxLayout(card_api)
        api_layout.setContentsMargins(18, 16, 18, 16)
        api_layout.setSpacing(12)

        # Provider Selector Row
        row_prov = QHBoxLayout()
        lbl_prov = QLabel("Primary Intelligence Provider:")
        lbl_prov.setObjectName("caption")
        lbl_prov.setFixedWidth(200)
        row_prov.addWidget(lbl_prov)

        self.provider_combo = QComboBox()
        self.provider_combo.setFixedHeight(34)
        for p_id, p_label in self.PROVIDER_CHOICES:
            self.provider_combo.addItem(p_label, p_id)

        active_p = get_active_provider_name()
        for idx in range(self.provider_combo.count()):
            if self.provider_combo.itemData(idx) == active_p:
                self.provider_combo.setCurrentIndex(idx)
                break
        self.provider_combo.currentIndexChanged.connect(self.on_provider_changed)
        row_prov.addWidget(self.provider_combo, 1)
        api_layout.addLayout(row_prov)

        # Base URL Row (for Cursor / Custom / OpenRouter)
        self.row_base_url = QHBoxLayout()
        self.lbl_base_url = QLabel("Endpoint / Base URL:")
        self.lbl_base_url.setObjectName("caption")
        self.lbl_base_url.setFixedWidth(200)
        self.row_base_url.addWidget(self.lbl_base_url)

        self.base_url_input = QLineEdit()
        self.base_url_input.setPlaceholderText("http://localhost:11434/v1 or https://openrouter.ai/api/v1")
        self.base_url_input.setFixedHeight(34)
        self.row_base_url.addWidget(self.base_url_input, 1)
        api_layout.addLayout(self.row_base_url)

        # API Key Row
        self.row_api = QHBoxLayout()
        self.lbl_key = QLabel("API Key:")
        self.lbl_key.setObjectName("caption")
        self.lbl_key.setFixedWidth(200)
        self.row_api.addWidget(self.lbl_key)

        self.api_input = QLineEdit()
        self.api_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_input.setFixedHeight(34)
        self.row_api.addWidget(self.api_input, 1)

        self.btn_toggle_api = QPushButton("Show")
        self.btn_toggle_api.setObjectName("ghostBtn")
        self.btn_toggle_api.setFixedHeight(34)
        self.btn_toggle_api.setFixedWidth(64)
        self.btn_toggle_api.clicked.connect(self.toggle_api_visibility)
        self.row_api.addWidget(self.btn_toggle_api)

        self.btn_save_key = QPushButton("Save Settings")
        self.btn_save_key.setObjectName("primaryBtn")
        self.btn_save_key.setFixedHeight(34)
        self.btn_save_key.clicked.connect(self.save_provider_settings)
        self.row_api.addWidget(self.btn_save_key)

        self.btn_test = QPushButton("Test Connection")
        self.btn_test.setFixedHeight(34)
        self.btn_test.clicked.connect(self.test_connection)
        self.row_api.addWidget(self.btn_test)

        api_layout.addLayout(self.row_api)

        self.lbl_status = QLabel("Provider initialized.")
        self.lbl_status.setStyleSheet("color: #57534E; font-size: 12px;")
        api_layout.addWidget(self.lbl_status)

        layout.addWidget(card_api)

        # ---------------------------------------------------------------------
        # Card 2: AI Model Selection & Architecture
        # ---------------------------------------------------------------------
        card_model = self._create_card(
            "MODEL SELECTION & REASONING CONFIGURATION",
            "Select active model and configure reasoning depth"
        )
        model_layout = QVBoxLayout(card_model)
        model_layout.setContentsMargins(18, 16, 18, 16)
        model_layout.setSpacing(10)

        lbl_m = QLabel("Active Model")
        lbl_m.setObjectName("caption")
        model_layout.addWidget(lbl_m)

        row_model = QHBoxLayout()
        row_model.setSpacing(8)

        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.setFixedHeight(34)
        row_model.addWidget(self.model_combo, 1)

        self.btn_discover = QPushButton("Discover Models")
        self.btn_discover.setFixedHeight(34)
        self.btn_discover.clicked.connect(self.discover_models)
        row_model.addWidget(self.btn_discover)

        model_layout.addLayout(row_model)

        row_meta = QHBoxLayout()
        self.lbl_active_model = QLabel("Active Model ID: -")
        self.lbl_active_model.setStyleSheet("color: #57534E; font-size: 12px; font-weight: 500;")
        row_meta.addWidget(self.lbl_active_model)

        row_meta.addStretch()

        self.lbl_th = QLabel("Gemini Thinking Budget:")
        self.lbl_th.setStyleSheet("color: #57534E; font-size: 12px;")
        row_meta.addWidget(self.lbl_th)

        self.combo_thinking = QComboBox()
        self.combo_thinking.addItems(["medium", "low", "high", "off"])
        self.combo_thinking.setFixedHeight(28)
        default_thinking = os.getenv("GEMINI_THINKING_LEVEL", "medium")
        idx_th = self.combo_thinking.findText(default_thinking)
        if idx_th >= 0:
            self.combo_thinking.setCurrentIndex(idx_th)
        self.combo_thinking.currentTextChanged.connect(self.on_thinking_changed)
        row_meta.addWidget(self.combo_thinking)

        model_layout.addLayout(row_meta)
        layout.addWidget(card_model)

        # ---------------------------------------------------------------------
        # Card 3: Storage & Local Publishing Defaults
        # ---------------------------------------------------------------------
        card_storage = self._create_card("LOCAL PUBLISHING & STORAGE", "File paths for documents, drafts, and research")
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
            ("Framework:", "PySide6 (Qt for Python 6.12.0)"),
            ("Supported AI Providers:", "Google Gemini, Anthropic Claude, OpenAI ChatGPT, Cursor / Custom"),
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

        # Populate initial provider inputs
        self.update_provider_ui(active_p)
        self.model_combo.currentIndexChanged.connect(self.on_model_changed)

    def _create_card(self, title: str, subtitle: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E0DDD5;
                border-radius: 6px;
            }
        """)
        return card

    def get_selected_provider(self) -> str:
        return self.provider_combo.currentData() or "gemini"

    def update_provider_ui(self, provider_id: str):
        """Refreshes UI fields and candidate models for selected provider."""
        self.model_combo.blockSignals(True)
        self.model_combo.clear()

        # Update candidate models
        models = self.PROVIDER_CANDIDATE_MODELS.get(provider_id, [])
        for m_id, m_label in models:
            self.model_combo.addItem(f"{m_id} — {m_label}", m_id)

        # Load existing key and model from env
        if provider_id == "gemini":
            self.lbl_key.setText("Gemini API Key:")
            self.api_input.setPlaceholderText("Enter Google Gemini API Key (starts with AIza...)")
            self.api_input.setText(os.getenv("GEMINI_API_KEY", ""))
            self.lbl_base_url.setVisible(False)
            self.base_url_input.setVisible(False)
            self.lbl_th.setVisible(True)
            self.combo_thinking.setVisible(True)
            saved_model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        elif provider_id == "anthropic":
            self.lbl_key.setText("Anthropic API Key:")
            self.api_input.setPlaceholderText("Enter Anthropic API Key (starts with sk-ant-...)")
            self.api_input.setText(os.getenv("ANTHROPIC_API_KEY", ""))
            self.lbl_base_url.setVisible(True)
            self.base_url_input.setVisible(True)
            self.base_url_input.setPlaceholderText("Optional (leave empty for standard api.anthropic.com)")
            self.base_url_input.setText(os.getenv("ANTHROPIC_BASE_URL", ""))
            self.lbl_th.setVisible(False)
            self.combo_thinking.setVisible(False)
            saved_model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        elif provider_id == "openai":
            self.lbl_key.setText("OpenAI API Key:")
            self.api_input.setPlaceholderText("Enter OpenAI API Key (starts with sk-...)")
            self.api_input.setText(os.getenv("OPENAI_API_KEY", ""))
            self.lbl_base_url.setVisible(True)
            self.base_url_input.setVisible(True)
            self.base_url_input.setPlaceholderText("Optional (leave empty for standard api.openai.com)")
            self.base_url_input.setText(os.getenv("OPENAI_BASE_URL", ""))
            self.lbl_th.setVisible(False)
            self.combo_thinking.setVisible(False)
            saved_model = os.getenv("OPENAI_MODEL", "gpt-4o")
        else:  # cursor / custom
            self.lbl_key.setText("Proxy / API Key:")
            self.api_input.setPlaceholderText("Optional proxy key (or leave blank for Ollama/local)")
            self.api_input.setText(os.getenv("CURSOR_API_KEY", ""))
            self.lbl_base_url.setVisible(True)
            self.base_url_input.setVisible(True)
            self.base_url_input.setPlaceholderText("http://localhost:11434/v1 or custom proxy")
            self.base_url_input.setText(os.getenv("CURSOR_BASE_URL", "http://localhost:11434/v1"))
            self.lbl_th.setVisible(False)
            self.combo_thinking.setVisible(False)
            saved_model = os.getenv("CURSOR_MODEL", "cursor-small")

        # Select saved model
        found = False
        for i in range(self.model_combo.count()):
            if self.model_combo.itemData(i) == saved_model:
                self.model_combo.setCurrentIndex(i)
                found = True
                break
        if not found and saved_model:
            self.model_combo.addItem(f"{saved_model} (Custom)", saved_model)
            self.model_combo.setCurrentIndex(self.model_combo.count() - 1)

        self.lbl_active_model.setText(f"Active Model ID: {saved_model}")
        self.model_combo.blockSignals(False)

        key_len = len(self.api_input.text().strip())
        if key_len:
            status_text = f"Active Provider: {provider_id.capitalize()} ({key_len} char key configured)"
        else:
            status_text = f"Active Provider: {provider_id.capitalize()} (Key not configured)"
        self.lbl_status.setText(status_text)
        self.lbl_status.setStyleSheet("color: #57534E; font-size: 12px;")

    def on_provider_changed(self):
        provider_id = self.get_selected_provider()
        save_config_value("AI_PROVIDER", provider_id)
        self.update_provider_ui(provider_id)
        self.settings_updated.emit()

    def toggle_api_visibility(self):
        if self.api_input.echoMode() == QLineEdit.EchoMode.Password:
            self.api_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_toggle_api.setText("Hide")
        else:
            self.api_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_toggle_api.setText("Show")

    def save_provider_settings(self):
        provider_id = self.get_selected_provider()
        key = self.api_input.text().strip()
        if not key and provider_id != "cursor":
            QMessageBox.warning(self, "Invalid Key", "API key cannot be empty.")
            return

        model = self.get_selected_model()
        base_url = self.base_url_input.text().strip()

        save_config_value("AI_PROVIDER", provider_id)

        if provider_id == "gemini":
            save_config_value("GEMINI_API_KEY", key)
            save_config_value("GEMINI_MODEL", model)
        elif provider_id == "anthropic":
            save_config_value("ANTHROPIC_API_KEY", key)
            save_config_value("ANTHROPIC_MODEL", model)
            if base_url:
                save_config_value("ANTHROPIC_BASE_URL", base_url)
        elif provider_id == "openai":
            save_config_value("OPENAI_API_KEY", key)
            save_config_value("OPENAI_MODEL", model)
            if base_url:
                save_config_value("OPENAI_BASE_URL", base_url)
        elif provider_id == "cursor":
            save_config_value("CURSOR_API_KEY", key)
            save_config_value("CURSOR_MODEL", model)
            save_config_value("CURSOR_BASE_URL", base_url or "http://localhost:11434/v1")

        self.lbl_status.setText(f"✓ Settings for {provider_id.capitalize()} ({model}) saved successfully.")
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
        provider_id = self.get_selected_provider()
        if provider_id == "gemini":
            save_config_value("GEMINI_MODEL", model_id)
        elif provider_id == "anthropic":
            save_config_value("ANTHROPIC_MODEL", model_id)
        elif provider_id == "openai":
            save_config_value("OPENAI_MODEL", model_id)
        elif provider_id == "cursor":
            save_config_value("CURSOR_MODEL", model_id)
        self.settings_updated.emit()

    def on_thinking_changed(self, text: str):
        save_config_value("GEMINI_THINKING_LEVEL", text)

    def discover_models(self):
        provider_id = self.get_selected_provider()
        key = self.api_input.text().strip()
        base_url = self.base_url_input.text().strip() or None

        self.btn_discover.setEnabled(False)
        self.lbl_status.setText(f"Discovering accessible models from {provider_id.capitalize()}...")
        self.lbl_status.setStyleSheet("color: #1E3A5F; font-size: 12px;")

        self.discovery_thread = DiscoverModelsThread(provider_name=provider_id, api_key=key, base_url=base_url)
        self.discovery_thread.finished_discovery.connect(self.on_models_discovered)
        self.discovery_thread.start()

    def on_models_discovered(self, success: bool, models: list, message: str):
        self.btn_discover.setEnabled(True)
        if success and models:
            self.lbl_status.setText(f"Verified {len(models)} accessible models from your account/endpoint.")
            self.lbl_status.setStyleSheet("color: #15803D; font-size: 12px; font-weight: 500;")

            existing_models = [self.model_combo.itemData(i) for i in range(self.model_combo.count())]
            for m in models:
                if m not in existing_models:
                    self.model_combo.addItem(f"{m} (Verified)", m)
        else:
            self.lbl_status.setText(f"✕ {message}")
            self.lbl_status.setStyleSheet("color: #B91C1C; font-size: 12px;")

    def test_connection(self):
        provider_id = self.get_selected_provider()
        key = self.api_input.text().strip()
        base_url = self.base_url_input.text().strip() or None
        selected_model = self.get_selected_model()

        self.btn_test.setEnabled(False)
        self.lbl_status.setText(f"Testing connection to {provider_id.capitalize()} with model '{selected_model}'...")
        self.lbl_status.setStyleSheet("color: #1E3A5F; font-size: 12px;")

        self.tester = TestConnectionThread(
            provider_name=provider_id,
            api_key=key,
            model=selected_model,
            base_url=base_url
        )
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
