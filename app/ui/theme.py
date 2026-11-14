"""Desktop theme styling and UI design system for BlogForge."""

import platform
from PySide6.QtGui import QFont

# Modern Cyber Dark Palette
BG_APP = "#0A0B0E"
BG_SURFACE = "#12141A"
BG_CARD = "#191C24"
BG_INPUT = "#1E222B"
ACCENT = "#00F0FF"
ACCENT_HOVER = "#33F3FF"
TEXT_PRIMARY = "#FFFFFF"
TEXT_SECONDARY = "#8B949E"
BORDER = "#2D313A"
ERROR = "#FF453A"
SUCCESS = "#32D74B"
WARNING = "#FF9F0A"


def apply_theme(app) -> None:
    """Applies global dark cyber theme and platform font styling to QApplication."""
    font_family = "Segoe UI" if platform.system() == "Windows" else "sans-serif"
    default_font = QFont(font_family, 10)
    app.setFont(default_font)

    stylesheet = f"""
    QWidget {{
        background-color: {BG_APP};
        color: {TEXT_PRIMARY};
        font-family: "{font_family}";
        font-size: 14px;
    }}

    /* Sidebars and Panels */
    QListWidget {{
        background-color: {BG_SURFACE};
        border-right: 1px solid {BORDER};
        outline: none;
    }}
    QListWidget::item {{
        padding: 12px 16px;
        border-radius: 4px;
        margin: 4px 8px;
        color: {TEXT_SECONDARY};
    }}
    QListWidget::item:selected {{
        background-color: {BG_CARD};
        color: {ACCENT};
        font-weight: bold;
    }}
    QListWidget::item:hover:!selected {{
        background-color: {BG_INPUT};
        color: {TEXT_PRIMARY};
    }}

    /* Buttons */
    QPushButton {{
        background-color: {BG_CARD};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        padding: 8px 16px;
        border-radius: 6px;
        font-weight: bold;
    }}
    QPushButton:hover {{
        background-color: {BG_INPUT};
        border-color: {ACCENT};
    }}
    QPushButton:pressed {{
        background-color: {BG_SURFACE};
    }}
    QPushButton:disabled {{
        background-color: {BG_SURFACE};
        color: {TEXT_SECONDARY};
        border-color: {BORDER};
    }}

    /* Primary Action Buttons */
    QPushButton#primaryBtn {{
        background-color: {ACCENT};
        color: #000000;
        border: none;
    }}
    QPushButton#primaryBtn:hover {{
        background-color: {ACCENT_HOVER};
    }}
    QPushButton#primaryBtn:disabled {{
        background-color: {BORDER};
        color: {TEXT_SECONDARY};
    }}

    /* Inputs */
    QLineEdit, QTextEdit, QComboBox {{
        background-color: {BG_INPUT};
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 8px;
        color: {TEXT_PRIMARY};
    }}
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
        border: 1px solid {ACCENT};
    }}

    /* Labels */
    QLabel {{
        color: {TEXT_PRIMARY};
    }}
    QLabel#h1 {{
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 16px;
    }}
    QLabel#h2 {{
        font-size: 18px;
        font-weight: bold;
        color: {ACCENT};
        margin-top: 16px;
        margin-bottom: 8px;
    }}
    QLabel#subtitle {{
        color: {TEXT_SECONDARY};
        font-size: 13px;
    }}

    /* Scrollbars */
    QScrollBar:vertical {{
        background: {BG_SURFACE};
        width: 10px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {BORDER};
        min-height: 20px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {ACCENT};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    """
    app.setStyleSheet(stylesheet)
