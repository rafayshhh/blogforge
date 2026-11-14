"""Application configuration, model selection, and API key management view."""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QMessageBox, QGroupBox
)
from PySide6.QtCore import QThread, Signal
from app.core.constants import APP_NAME, APP_VERSION


class TestConnectionThread(QThread):
    result = Signal(bool, str)

    def __init__(self, api_key: str, model: str = "gemini-3.7-flash"):
        super().__init__()
        self.api_key = api_key
        self.model = model

    def run(self):
        try:
            from app.providers.gemini import GeminiProvider
            provider = GeminiProvider(api_key=self.api_key, default_model=self.model)
            response = provider.generate("Reply with exactly: OK")
            if response and response.text:
                self.result.emit(True, f"Connected successfully. Model: {self.model}")
            else:
                self.result.emit(False, "Connection failed: empty response.")
        except Exception as e:
            self.result.emit(False, f"Connection failed. Error: {str(e)}")


class SettingsWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)

        lbl_head = QLabel("Settings")
        lbl_head.setObjectName("h1")
        layout.addWidget(lbl_head)

        # AI Provider Group
        grp_ai = QGroupBox("AI Provider")
        ai_lay = QVBoxLayout()
        grp_ai.setLayout(ai_lay)

        self.provider_combo = QComboBox()
        self.provider_combo.addItem("gemini")
        ai_lay.addWidget(QLabel("Provider:"))
        ai_lay.addWidget(self.provider_combo)

        self.model_combo = QComboBox()
        self.model_combo.addItem("Gemini 3.7 Flash — Recommended", "gemini-3.7-flash")
        self.model_combo.addItem("Gemini 3.1 Pro — Maximum Quality", "gemini-3.1-pro-preview")
        self.model_combo.setToolTip(
            "Gemini 3.7 Flash: Fast, powerful, and recommended for everyday BlogForge workflows.\n"
            "Gemini 3.1 Pro: Higher-end reasoning model for demanding content strategy and complex tasks."
        )

        current_model = os.getenv("GEMINI_MODEL", "gemini-3.7-flash")
        index = self.model_combo.findData(current_model)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)

        ai_lay.addWidget(QLabel("Model:"))
        ai_lay.addWidget(self.model_combo)

        ai_lay.addWidget(QLabel("Gemini API Key:"))
        api_layout = QHBoxLayout()
        self.api_input = QLineEdit()
        self.api_input.setEchoMode(QLineEdit.Password)
        self.api_input.setPlaceholderText("Paste your Gemini API key here")
        self.api_input.setText(os.getenv("GEMINI_API_KEY", ""))

        self.btn_toggle = QPushButton("Show")
        self.btn_toggle.clicked.connect(self.toggle_api_visibility)
        api_layout.addWidget(self.api_input)
        api_layout.addWidget(self.btn_toggle)
        ai_lay.addLayout(api_layout)

        btn_row = QHBoxLayout()
        self.btn_save = QPushButton("Save Key")
        self.btn_save.setObjectName("primaryBtn")
        self.btn_save.setToolTip("Save this API key to your .env file and activate it for this session.")
        self.btn_save.clicked.connect(self.save_api_key)
        btn_row.addWidget(self.btn_save)

        self.btn_test = QPushButton("Test Connection")
        self.btn_test.setToolTip("Send a test request to Gemini to verify your API key works.")
        self.btn_test.clicked.connect(self.test_connection)
        btn_row.addWidget(self.btn_test)
        btn_row.addStretch()
        ai_lay.addLayout(btn_row)

        self.lbl_status = QLabel("")
        ai_lay.addWidget(self.lbl_status)
        layout.addWidget(grp_ai)

        # About Group
        grp_abt = QGroupBox("About")
        abt_lay = QVBoxLayout()
        grp_abt.setLayout(abt_lay)
        about_text = (
            f"{APP_NAME}\nVersion {APP_VERSION}\n\n"
            "A local-first AI workspace for researching, writing,\n"
            "reviewing, and optimizing content.\n\nOpen Source"
        )
        lbl_abt = QLabel(about_text)
        abt_lay.addWidget(lbl_abt)
        layout.addWidget(grp_abt)

        layout.addStretch()

    def toggle_api_visibility(self):
        if self.api_input.echoMode() == QLineEdit.Password:
            self.api_input.setEchoMode(QLineEdit.Normal)
            self.btn_toggle.setText("Hide")
        else:
            self.api_input.setEchoMode(QLineEdit.Password)
            self.btn_toggle.setText("Show")

    def save_api_key(self):
        key = self.api_input.text().strip()
        model = self.model_combo.currentData()
        if not key:
            QMessageBox.warning(self, "Empty Key", "Please enter an API key first.")
            return

        os.environ["GEMINI_API_KEY"] = key
        os.environ["GEMINI_MODEL"] = model

        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env")
        env_path = os.path.normpath(env_path)
        try:
            lines = []
            key_found = False
            model_found = False
            if os.path.exists(env_path):
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip().startswith("GEMINI_API_KEY"):
                            lines.append(f"GEMINI_API_KEY={key}\n")
                            key_found = True
                        elif line.strip().startswith("GEMINI_MODEL"):
                            lines.append(f"GEMINI_MODEL={model}\n")
                            model_found = True
                        else:
                            lines.append(line)
            if not key_found:
                lines.append(f"GEMINI_API_KEY={key}\n")
            if not model_found:
                lines.append(f"GEMINI_MODEL={model}\n")
            with open(env_path, "w", encoding="utf-8") as f:
                f.writelines(lines)

            self.lbl_status.setStyleSheet("color: #32D74B;")
            self.lbl_status.setText("✓ API key and model saved.")
        except Exception as e:
            self.lbl_status.setStyleSheet("color: #FF9F0A;")
            self.lbl_status.setText(f"Settings active for this session (could not write .env: {e})")

    def test_connection(self):
        key = self.api_input.text().strip()
        model = self.model_combo.currentData()
        if not key:
            QMessageBox.warning(self, "Empty Key", "Please enter an API key first.")
            return

        os.environ["GEMINI_API_KEY"] = key
        os.environ["GEMINI_MODEL"] = model

        self.btn_test.setEnabled(False)
        self.lbl_status.setStyleSheet("color: white;")
        self.lbl_status.setText("Testing connection...")

        self.tester = TestConnectionThread(key, model)
        self.tester.result.connect(self.on_test_result)
        self.tester.start()

    def on_test_result(self, success, msg):
        self.btn_test.setEnabled(True)
        if success:
            self.lbl_status.setStyleSheet("color: #32D74B;")
            self.lbl_status.setText(f"✓ {msg}")
        else:
            self.lbl_status.setStyleSheet("color: #FF453A;")
            self.lbl_status.setText(f"✕ {msg}")
