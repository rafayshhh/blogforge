"""Desktop theme styling and UI design system for BlogForge.

Provides a sophisticated, light-first Editorial Paper design system inspired by
mature desktop productivity software (Notion, Ulysses, Obsidian, Bear, iA Writer).
Features warm alabaster and paper surfaces, rich charcoal ink typography,
quiet hairline dividers, and an understated terracotta editorial accent.
"""

import platform
from PySide6.QtGui import QFont

# --- Design Tokens: Editorial Paper Palette ---
BG_APP = "#F9F8F6"           # Warm alabaster desk surface
BG_SURFACE = "#FFFFFF"       # Crisp paper canvas for writing and elevated panels
BG_PANEL = "#F4F1EA"         # Warm stone/ivory panels and subtle sidebars
BG_HEADER = "#FFFFFF"        # Top application bar
BG_HOVER = "#EFECE4"         # Soft warm hover on buttons and list items
BG_ACTIVE = "#E5E1D5"        # Pressed/selected states
BG_INPUT = "#FFFFFF"         # Crisp white form fields
BG_INPUT_HOVER = "#FAF9F7"   # Input hover tint
BG_ELEVATED = "#FFFFFF"      # Menus, popovers, and dialogs

# Primary Accent: Warm Terracotta / Burnt Sienna (literary, craft, editorial)
ACCENT = "#9A3412"
ACCENT_HOVER = "#B45309"
ACCENT_PRESSED = "#7C2D12"
ACCENT_LIGHT = "#FDF2E9"
ACCENT_BORDER = "#FDBA74"

# Secondary Inks
NAVY_INK = "#1E3A5F"         # Archive navy for publishing and metadata
FOREST_INK = "#15803D"       # Editorial forest for success and validation

# Semantic Indicators (Calm, legible, non-neon)
SUCCESS = "#15803D"
SUCCESS_BG = "#F0FDF4"
SUCCESS_BORDER = "#BBF7D0"

WARNING = "#B45309"
WARNING_BG = "#FFFBEB"
WARNING_BORDER = "#FDE68A"

ERROR = "#B91C1C"
ERROR_BG = "#FEF2F2"
ERROR_BORDER = "#FECACA"

INFO = "#1E3A5F"
INFO_BG = "#F0F9FF"
INFO_BORDER = "#BAE6FD"

# Text & Ink Hierarchy
TEXT_PRIMARY = "#1C1917"     # Deep carbon ink (warm, rich, optimal contrast)
TEXT_SECONDARY = "#57534E"   # Warm charcoal for subheadings and field labels
TEXT_MUTED = "#8C877F"       # Pencil lead for captions, hints, and placeholders
TEXT_INVERTED = "#FFFFFF"    # Crisp white for accented buttons

# Borders and Rules
BORDER_SUBTLE = "#ECEAE3"    # Hairline 1px dividers
BORDER_DEFAULT = "#E0DDD5"   # Standard component outlines
BORDER_HOVER = "#C5C0B3"     # Interactive hover outline
BORDER_FOCUS = "#9A3412"     # Focused outline

# Typography Fonts
FONT_UI = "Segoe UI" if platform.system() == "Windows" else "sans-serif"
FONT_SERIF = "Georgia" if platform.system() == "Windows" else "Charter, serif"
FONT_MONO = "Consolas" if platform.system() == "Windows" else "monospace"


def get_preview_html_styles() -> str:
    """Returns CSS rules for rendering the live publication preview in HTML."""
    return f"""
    <style>
        body {{
            font-family: {FONT_SERIF};
            font-size: 15px;
            line-height: 1.72;
            color: {TEXT_PRIMARY};
            background-color: {BG_SURFACE};
            margin: 0;
            padding: 24px 32px;
            max-width: 760px;
        }}
        h1, h2, h3, h4, h5, h6 {{
            font-family: {FONT_SERIF};
            color: {TEXT_PRIMARY};
            font-weight: 700;
            line-height: 1.3;
            margin-top: 1.6em;
            margin-bottom: 0.5em;
        }}
        h1 {{ font-size: 26px; border-bottom: 1px solid {BORDER_DEFAULT}; padding-bottom: 8px; }}
        h2 {{ font-size: 21px; }}
        h3 {{ font-size: 17px; }}
        p {{
            margin-top: 0;
            margin-bottom: 1.2em;
        }}
        blockquote {{
            margin: 1.4em 0;
            padding: 8px 18px;
            border-left: 3px solid {ACCENT};
            background-color: {BG_APP};
            color: {TEXT_SECONDARY};
            font-style: italic;
        }}
        code {{
            font-family: {FONT_MONO};
            font-size: 13px;
            background-color: {BG_PANEL};
            border: 1px solid {BORDER_DEFAULT};
            border-radius: 4px;
            padding: 2px 6px;
            color: {ACCENT};
        }}
        pre {{
            background-color: {BG_PANEL};
            border: 1px solid {BORDER_DEFAULT};
            border-radius: 6px;
            padding: 14px;
            overflow-x: auto;
            font-family: {FONT_MONO};
            font-size: 13px;
            line-height: 1.5;
            color: {TEXT_PRIMARY};
        }}
        pre code {{
            border: none;
            padding: 0;
            background-color: transparent;
            color: inherit;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1.4em 0;
        }}
        th, td {{
            border: 1px solid {BORDER_DEFAULT};
            padding: 8px 12px;
            text-align: left;
        }}
        th {{
            background-color: {BG_PANEL};
            font-weight: 600;
            color: {TEXT_PRIMARY};
        }}
        a {{
            color: {ACCENT};
            text-decoration: underline;
        }}
        ul, ol {{
            margin-top: 0;
            margin-bottom: 1.2em;
            padding-left: 24px;
        }}
        li {{
            margin-bottom: 0.4em;
        }}
        hr {{
            border: none;
            border-top: 1px solid {BORDER_DEFAULT};
            margin: 2em 0;
        }}
    </style>
    """


def apply_theme(app) -> None:
    """Applies the light-first Editorial Paper design system to QApplication."""
    default_font = QFont(FONT_UI, 10)
    app.setFont(default_font)

    stylesheet = f"""
    /* --- Base Application Canvas --- */
    QWidget {{
        background-color: {BG_APP};
        color: {TEXT_PRIMARY};
        font-family: "{FONT_UI}";
        font-size: 13px;
        selection-background-color: {ACCENT_LIGHT};
        selection-color: {ACCENT};
    }}

    QLabel {{
        background-color: transparent;
        border: none;
    }}

    /* --- Root Window & Elevated Panes --- */
    QMainWindow {{
        background-color: {BG_APP};
    }}

    QDialog {{
        background-color: {BG_SURFACE};
        border: 1px solid {BORDER_DEFAULT};
        border-radius: 6px;
    }}

    /* --- Top Navigation Bar & Chrome --- */
    #topHeaderBar {{
        background-color: {BG_HEADER};
        border-bottom: 1px solid {BORDER_DEFAULT};
    }}

    /* --- Navigation Tabs --- */
    #navTabBtn {{
        background-color: transparent;
        border: none;
        border-bottom: 2px solid transparent;
        border-radius: 0px;
        color: {TEXT_SECONDARY};
        font-size: 13px;
        font-weight: 500;
        padding: 0 14px;
        height: 48px;
    }}
    #navTabBtn:hover {{
        background-color: {BG_HOVER};
        color: {TEXT_PRIMARY};
    }}
    #navTabBtn:checked {{
        background-color: transparent;
        color: {ACCENT};
        font-weight: 600;
        border-bottom: 2px solid {ACCENT};
    }}

    /* --- Lists (Projects, Articles, Resources) --- */
    QListWidget {{
        background-color: {BG_SURFACE};
        border: 1px solid {BORDER_DEFAULT};
        border-radius: 6px;
        outline: none;
        padding: 4px;
    }}
    QListWidget::item {{
        padding: 8px 10px;
        border-radius: 4px;
        margin: 1px 2px;
        color: {TEXT_PRIMARY};
        font-size: 13px;
        border: 1px solid transparent;
    }}
    QListWidget::item:selected {{
        background-color: {ACCENT_LIGHT};
        color: {ACCENT};
        font-weight: 600;
        border-color: {ACCENT_BORDER};
    }}
    QListWidget::item:hover:!selected {{
        background-color: {BG_HOVER};
        color: {TEXT_PRIMARY};
    }}

    /* --- Standard Push Buttons --- */
    QPushButton {{
        background-color: {BG_SURFACE};
        border: 1px solid {BORDER_DEFAULT};
        border-radius: 5px;
        padding: 6px 14px;
        color: {TEXT_PRIMARY};
        font-size: 13px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background-color: {BG_HOVER};
        border-color: {BORDER_HOVER};
        color: {TEXT_PRIMARY};
    }}
    QPushButton:pressed {{
        background-color: {BG_ACTIVE};
    }}
    QPushButton:disabled {{
        background-color: {BG_PANEL};
        border-color: {BORDER_SUBTLE};
        color: {TEXT_MUTED};
    }}

    /* Primary Accent Button (Terracotta Editorial) */
    QPushButton#primaryBtn {{
        background-color: {ACCENT};
        border: 1px solid {ACCENT};
        color: {TEXT_INVERTED};
        font-weight: 600;
    }}
    QPushButton#primaryBtn:hover {{
        background-color: {ACCENT_HOVER};
        border-color: {ACCENT_HOVER};
    }}
    QPushButton#primaryBtn:pressed {{
        background-color: {ACCENT_PRESSED};
    }}
    QPushButton#primaryBtn:disabled {{
        background-color: {BORDER_DEFAULT};
        border-color: {BORDER_DEFAULT};
        color: {TEXT_MUTED};
    }}

    /* Ghost / Minimal Toolbar Button */
    QPushButton#ghostBtn {{
        background-color: transparent;
        border: 1px solid transparent;
        color: {TEXT_SECONDARY};
    }}
    QPushButton#ghostBtn:hover {{
        background-color: {BG_HOVER};
        border-color: {BORDER_SUBTLE};
        color: {TEXT_PRIMARY};
    }}
    QPushButton#ghostBtn:checked {{
        background-color: {ACCENT_LIGHT};
        border-color: {ACCENT_BORDER};
        color: {ACCENT};
        font-weight: 600;
    }}

    /* Danger Button */
    QPushButton#dangerBtn {{
        background-color: {BG_SURFACE};
        border: 1px solid {ERROR_BORDER};
        color: {ERROR};
    }}
    QPushButton#dangerBtn:hover {{
        background-color: {ERROR_BG};
        border-color: {ERROR};
    }}
    QPushButton#dangerBtn:pressed {{
        background-color: #FEE2E2;
    }}

    /* --- Form Controls: Inputs & ComboBoxes --- */
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {BG_INPUT};
        border: 1px solid {BORDER_DEFAULT};
        border-radius: 5px;
        padding: 6px 10px;
        color: {TEXT_PRIMARY};
        font-size: 13px;
    }}
    QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover {{
        border-color: {BORDER_HOVER};
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border: 1px solid {BORDER_FOCUS};
        background-color: {BG_SURFACE};
    }}
    QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
        background-color: {BG_PANEL};
        color: {TEXT_MUTED};
    }}

    QComboBox {{
        background-color: {BG_SURFACE};
        border: 1px solid {BORDER_DEFAULT};
        border-radius: 5px;
        padding: 5px 10px;
        color: {TEXT_PRIMARY};
        font-size: 13px;
        min-height: 24px;
    }}
    QComboBox:hover {{
        border-color: {BORDER_HOVER};
    }}
    QComboBox:focus {{
        border-color: {BORDER_FOCUS};
    }}
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 24px;
        border-left: 1px solid {BORDER_SUBTLE};
    }}
    QComboBox QAbstractItemView {{
        background-color: {BG_SURFACE};
        border: 1px solid {BORDER_DEFAULT};
        border-radius: 4px;
        selection-background-color: {ACCENT_LIGHT};
        selection-color: {ACCENT};
        outline: none;
        padding: 4px;
    }}

    /* --- Tab Widgets --- */
    QTabWidget::pane {{
        border: 1px solid {BORDER_DEFAULT};
        border-radius: 6px;
        background-color: {BG_SURFACE};
        top: -1px;
    }}
    QTabBar::tab {{
        background-color: {BG_PANEL};
        border: 1px solid {BORDER_DEFAULT};
        border-bottom: none;
        border-top-left-radius: 5px;
        border-top-right-radius: 5px;
        padding: 7px 16px;
        margin-right: 2px;
        color: {TEXT_SECONDARY};
        font-size: 13px;
        font-weight: 500;
    }}
    QTabBar::tab:hover {{
        background-color: {BG_HOVER};
        color: {TEXT_PRIMARY};
    }}
    QTabBar::tab:selected {{
        background-color: {BG_SURFACE};
        border-color: {BORDER_DEFAULT};
        border-bottom: 1px solid {BG_SURFACE};
        color: {ACCENT};
        font-weight: 600;
    }}

    /* --- Tables --- */
    QTableWidget {{
        background-color: {BG_SURFACE};
        border: 1px solid {BORDER_DEFAULT};
        border-radius: 6px;
        gridline-color: {BORDER_SUBTLE};
        selection-background-color: {ACCENT_LIGHT};
        selection-color: {ACCENT};
    }}
    QHeaderView::section {{
        background-color: {BG_PANEL};
        border: none;
        border-right: 1px solid {BORDER_SUBTLE};
        border-bottom: 1px solid {BORDER_DEFAULT};
        padding: 8px 10px;
        font-size: 11px;
        font-weight: 700;
        color: {TEXT_SECONDARY};
        letter-spacing: 0.5px;
    }}
    QTableWidget::item {{
        padding: 6px 10px;
        color: {TEXT_PRIMARY};
    }}

    /* --- Subtle Scrollbars --- */
    QScrollBar:vertical {{
        background-color: transparent;
        width: 6px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background-color: {BORDER_DEFAULT};
        border-radius: 3px;
        min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {BORDER_HOVER};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar:horizontal {{
        background-color: transparent;
        height: 6px;
        margin: 0;
    }}
    QScrollBar::handle:horizontal {{
        background-color: {BORDER_DEFAULT};
        border-radius: 3px;
        min-width: 24px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background-color: {BORDER_HOVER};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    /* --- Splitters --- */
    QSplitter::handle {{
        background-color: {BORDER_SUBTLE};
    }}
    QSplitter::handle:hover {{
        background-color: {ACCENT};
    }}

    /* --- Checkboxes --- */
    QCheckBox {{
        spacing: 8px;
        color: {TEXT_PRIMARY};
        font-size: 13px;
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border: 1px solid {BORDER_DEFAULT};
        border-radius: 4px;
        background-color: {BG_SURFACE};
    }}
    QCheckBox::indicator:hover {{
        border-color: {BORDER_HOVER};
    }}
    QCheckBox::indicator:checked {{
        background-color: {ACCENT};
        border-color: {ACCENT};
    }}

    /* --- Status Bar --- */
    QStatusBar {{
        background-color: {BG_PANEL};
        border-top: 1px solid {BORDER_DEFAULT};
        color: {TEXT_SECONDARY};
        font-size: 12px;
        min-height: 26px;
    }}

    /* --- Progress Bar --- */
    QProgressBar {{
        background-color: {BG_PANEL};
        border: 1px solid {BORDER_DEFAULT};
        border-radius: 4px;
        height: 8px;
        text-align: center;
        font-size: 11px;
    }}
    QProgressBar::chunk {{
        background-color: {ACCENT};
        border-radius: 3px;
    }}

    /* --- Semantic Classes & Custom Labels --- */
    QLabel#h1 {{
        font-family: "{FONT_SERIF}";
        font-size: 22px;
        font-weight: 700;
        color: {TEXT_PRIMARY};
    }}
    QLabel#h2 {{
        font-family: "{FONT_SERIF}";
        font-size: 17px;
        font-weight: 700;
        color: {TEXT_PRIMARY};
    }}
    QLabel#sectionHead {{
        font-size: 11px;
        font-weight: 700;
        color: {TEXT_SECONDARY};
        letter-spacing: 0.6px;
    }}
    QLabel#subtitle {{
        font-size: 13px;
        color: {TEXT_SECONDARY};
    }}
    QLabel#caption {{
        font-size: 11px;
        color: {TEXT_MUTED};
    }}
    """
    app.setStyleSheet(stylesheet)
