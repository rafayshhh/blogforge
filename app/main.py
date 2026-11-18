"""Application entry point for BlogForge desktop studio."""

import sys
from PySide6.QtWidgets import QApplication

from app.core.config import load_config
from app.core.logging import setup_logging
from app.ui.theme import apply_theme
from app.ui.main_window import MainWindow


def main() -> None:
    """Initializes environment, logging, UI theme, and launches the main desktop window."""
    load_config()
    setup_logging()

    app = QApplication.instance() or QApplication(sys.argv)
    if isinstance(app, QApplication):
        app.setStyle("Fusion")
        apply_theme(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
