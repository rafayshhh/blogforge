"""Dashboard overview widget displaying metrics, checklist, and quick actions."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
)
from PySide6.QtCore import Signal
from app.core.constants import APP_NAME


class DashboardWidget(QWidget):
    """Landing dashboard providing workflow shortcuts and status overview."""
    navigate_to = Signal(int)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)

        lbl_welcome = QLabel(f"Welcome to {APP_NAME}")
        lbl_welcome.setObjectName("h1")
        layout.addWidget(lbl_welcome)

        lbl_sub = QLabel("Research. Write. Optimize. Ship.")
        lbl_sub.setObjectName("subtitle")
        layout.addWidget(lbl_sub)

        lbl_privacy = QLabel("Your projects stay on your device. Gemini is used only when you trigger an AI operation.")
        lbl_privacy.setStyleSheet("color: #8B949E; font-size: 12px; margin-top: 4px;")
        layout.addWidget(lbl_privacy)

        layout.addSpacing(16)

        btn_new = QPushButton("+ New Article")
        btn_new.setObjectName("primaryBtn")
        btn_new.setFixedSize(160, 42)
        btn_new.setToolTip("Jump to the article generation workflow.")
        btn_new.clicked.connect(lambda: self.navigate_to.emit(2))
        layout.addWidget(btn_new)

        layout.addSpacing(24)

        lbl_setup = QLabel("Getting Started")
        lbl_setup.setObjectName("h2")
        layout.addWidget(lbl_setup)

        self.checklist_layout = QVBoxLayout()
        layout.addLayout(self.checklist_layout)
        self.update_checklist(False, False, False)

        layout.addSpacing(24)

        lbl_active = QLabel("Overview")
        lbl_active.setObjectName("h2")
        layout.addWidget(lbl_active)

        stats_layout = QHBoxLayout()
        self.stat_labels = {}
        for stat in ["Articles", "Research", "Drafts"]:
            card = QWidget()
            card.setStyleSheet("background-color: #191C24; border-radius: 8px; border: 1px solid #2D313A;")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 16, 16, 16)

            l1 = QLabel(stat)
            l1.setStyleSheet("color: #8B949E; font-size: 12px; text-transform: uppercase;")
            l2 = QLabel("0")
            l2.setStyleSheet("font-size: 28px; font-weight: bold; margin-bottom: 0px;")

            card_layout.addWidget(l1)
            card_layout.addWidget(l2)
            stats_layout.addWidget(card)
            self.stat_labels[stat] = l2

        layout.addLayout(stats_layout)
        layout.addStretch()

    def update_checklist(self, has_gemini: bool, has_project: bool, has_nextjs: bool) -> None:
        """Renders onboarding task state."""
        while self.checklist_layout.count():
            item = self.checklist_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        steps = [
            ("① Connect Gemini — Add your API key in Settings", has_gemini),
            ("② Create a Project — Set up your brand and content rules", has_project),
            ("③ Configure Next.js export (optional)", has_nextjs),
        ]

        for text, done in steps:
            icon = "✓ " if done else "○ "
            color = "color: #32D74B;" if done else "color: #8B949E;"
            lbl = QLabel(f"{icon}{text}")
            lbl.setStyleSheet(f"{color} font-size: 14px; padding: 4px 0;")
            self.checklist_layout.addWidget(lbl)

    def update_stats(self, articles_count: int, research_count: int, drafts_count: int) -> None:
        """Updates metric card totals."""
        if "Articles" in self.stat_labels:
            self.stat_labels["Articles"].setText(str(articles_count))
        if "Research" in self.stat_labels:
            self.stat_labels["Research"].setText(str(research_count))
        if "Drafts" in self.stat_labels:
            self.stat_labels["Drafts"].setText(str(drafts_count))
