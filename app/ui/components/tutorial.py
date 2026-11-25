"""Interactive multi-step GUI guided tutorial for BlogForge."""

from typing import Optional, List, Dict, Any
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QStackedWidget, QWidget
)
from PySide6.QtCore import Qt


class TutorialDialog(QDialog):
    """Interactive multi-step visual walkthrough guiding users through BlogForge workflows."""

    STEPS: List[Dict[str, Any]] = [
        {
            "step_num": 1,
            "badge": "STEP 1: CONFIGURATION",
            "title": "Configure Google Gemini AI",
            "subtitle": "Connect your Google AI Studio credentials and choose your default reasoning model.",
            "content": (
                "BlogForge is powered exclusively by <b>Google Gemini</b> (Gemini 3.8 and Gemini 4 series).<br><br>"
                "<b>Quick Setup:</b><br>"
                "• Navigate to <b>Settings</b> and paste your Google AI Studio API key (starts with "
                "<code>AIza...</code>).<br>"
                "• Click <b>Save Key</b> then <b>Test Connection</b> to verify real-time connectivity.<br>"
                "• Select your preferred active model (e.g. <i>gemini-3.8-flash</i> for fast drafting, "
                "or <i>gemini-4-carbon</i> for deep analytical reasoning).<br>"
                "• Configure your <b>Thinking Budget</b> (low, medium, high) to control reasoning expenditure."
            ),
            "tip": (
                "💡 Tip: You can discover all models accessible to your Google account via "
                "the 'Discover Models' button."
            ),
            "target_tab": 4,
            "action_text": "Open Settings Studio",
        },
        {
            "step_num": 2,
            "badge": "STEP 2: BRAND IDENTITY",
            "title": "Create & Customize Brand Projects",
            "subtitle": "Establish unique editorial voices, target reader personas, and product catalogs.",
            "content": (
                "Workspaces in BlogForge are organized into <b>Projects</b>.<br><br>"
                "<b>Key Capabilities:</b><br>"
                "• <b>Brand Profile:</b> Define audience, editorial tone (e.g., Authoritative, Conversational), "
                "style guidelines, and banned cliché terms.<br>"
                "• <b>Product Catalog:</b> Register internal products/services with descriptions and CTAs "
                "so Gemini weaves them naturally.<br>"
                "• <b>Internal Links:</b> Supply high-priority URL targets that Gemini will contextually "
                "hyperlink into relevant paragraphs."
            ),
            "tip": "💡 Tip: Switch active workspace anytime using the top-bar 'Workspace' dropdown.",
            "target_tab": 1,
            "action_text": "Open Projects Studio",
        },
        {
            "step_num": 3,
            "badge": "STEP 3: DEEP RESEARCH",
            "title": "Topic Exploration & Competitor Research",
            "subtitle": "Synthesize web research, fact-check claims, and uncover high-intent content angles.",
            "content": (
                "Great articles begin with rigorous research.<br><br>"
                "<b>How It Works:</b><br>"
                "• Navigate to the <b>Research</b> tab and enter your primary topic query.<br>"
                "• Gemini automatically analyzes search results, identifies market consensus, and compiles "
                "key verified statistics.<br>"
                "• <b>Verified Sources:</b> High-authority references are stored directly with your project "
                "and injected into outlines and citations."
            ),
            "tip": "💡 Tip: Research dossiers are cached locally in data/research for offline editing.",
            "target_tab": 3,
            "action_text": "Open Research Studio",
        },
        {
            "step_num": 4,
            "badge": "STEP 4: AI PRODUCTION",
            "title": "Autonomous Article Generation",
            "subtitle": "Transform concepts into long-form, anti-slop articles with one click.",
            "content": (
                "Launch the <b>AI Studio</b> modal dialog from the top header or Home dashboard.<br><br>"
                "<b>The Production Pipeline:</b><br>"
                "1. <b>Outline Generation:</b> Gemini architects an exhaustive multi-level outline with specific "
                "section purposes.<br>"
                "2. <b>Sequential Section Synthesis:</b> Each section is generated with flow continuity and "
                "anti-slop heuristics.<br>"
                "3. <b>FAQ & SEO Generation:</b> Automatically creates FAQ schemas, meta descriptions, and "
                "keyword tags.<br>"
                "4. <b>Editorial Review:</b> Evaluates readability, tone compliance, and flags fluff."
            ),
            "tip": "💡 Tip: The pipeline saves incremental checkpoints so you never lose generation progress.",
            "target_tab": -1,  # Special action: launch AI Studio dialog
            "action_text": "Launch AI Studio Dialog",
        },
        {
            "step_num": 5,
            "badge": "STEP 5: EDITING & EXPORT",
            "title": "Writing Studio & Multi-Format Export",
            "subtitle": "Polish manuscripts side-by-side with live HTML preview and export anywhere.",
            "content": (
                "The <b>Writing</b> studio gives you full control over your final publication.<br><br>"
                "<b>Editor Features:</b><br>"
                "• <b>Split View:</b> Side-by-side Markdown source editor and typography-accurate HTML preview.<br>"
                "• <b>Focus Mode:</b> Switch between Editor Only, Split View, or Preview Only.<br>"
                "• <b>Live Word & Reading Metrics:</b> Real-time word count and estimated reading time.<br>"
                "• <b>Multi-Format Export:</b> Export cleanly to <b>Markdown (.md)</b>, <b>HTML (.html)</b>, "
                "<b>JSON (.json)</b>, or directly to a <b>Next.js App Router / Contentlayer</b> repository."
            ),
            "tip": "💡 Shortcuts: Press Ctrl+S to save draft locally. Press Ctrl+N to create a blank draft.",
            "target_tab": 2,
            "action_text": "Open Writing Studio",
        },
    ]

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.main_window = parent
        self.current_step = 0

        self.setWindowTitle("BlogForge — Guided Tour & Workflow Tutorial")
        self.setFixedSize(760, 540)
        self.setStyleSheet("""
            QDialog {
                background-color: #FDFCFA;
                color: #1C1917;
            }
            #stepCard {
                background-color: #FFFFFF;
                border: 1px solid #E0DDD5;
                border-radius: 8px;
            }
            #badgeLabel {
                color: #C2410C;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 1px;
            }
            #titleLabel {
                color: #1C1917;
                font-size: 20px;
                font-weight: 700;
                font-family: 'Newsreader', 'Georgia', serif;
            }
            #subtitleLabel {
                color: #78716C;
                font-size: 13px;
                font-weight: 400;
            }
            #contentLabel {
                color: #292524;
                font-size: 13px;
                line-height: 1.5;
            }
            #tipCard {
                background-color: #FFFBEB;
                border: 1px solid #FEF3C7;
                border-radius: 6px;
                padding: 10px;
            }
            #tipLabel {
                color: #92400E;
                font-size: 12px;
                font-weight: 500;
            }
            #counterLabel {
                color: #A8A29E;
                font-size: 12px;
                font-weight: 600;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(16)

        # Top Bar: Logo & Step indicator
        top_bar = QHBoxLayout()
        lbl_brand = QLabel("BLOGFORGE • USER GUIDE")
        lbl_brand.setObjectName("badgeLabel")
        top_bar.addWidget(lbl_brand)
        top_bar.addStretch()

        self.lbl_counter = QLabel("Step 1 of 5")
        self.lbl_counter.setObjectName("counterLabel")
        top_bar.addWidget(self.lbl_counter)
        layout.addLayout(top_bar)

        # Stacked Step Cards
        self.stack = QStackedWidget()
        for step in self.STEPS:
            card = self._build_step_card(step)
            self.stack.addWidget(card)
        layout.addWidget(self.stack, 1)

        # Step Indicators (Dots)
        self.indicator_layout = QHBoxLayout()
        self.indicator_layout.setSpacing(6)
        self.dots: List[QLabel] = []
        for i in range(len(self.STEPS)):
            dot = QLabel("●" if i == 0 else "○")
            dot.setStyleSheet("color: #C2410C; font-size: 14px;" if i == 0 else "color: #D6D3D1; font-size: 14px;")
            self.indicator_layout.addWidget(dot)
            self.dots.append(dot)
        self.indicator_layout.addStretch()

        # Bottom Navigation Controls
        bottom_bar = QHBoxLayout()
        bottom_bar.addLayout(self.indicator_layout)

        self.btn_action = QPushButton("Open Settings Studio")
        self.btn_action.setObjectName("ghostBtn")
        self.btn_action.setFixedHeight(34)
        self.btn_action.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_action.clicked.connect(self._handle_action_shortcut)
        bottom_bar.addWidget(self.btn_action)

        bottom_bar.addSpacing(12)

        self.btn_prev = QPushButton("Back")
        self.btn_prev.setFixedHeight(34)
        self.btn_prev.setFixedWidth(80)
        self.btn_prev.setEnabled(False)
        self.btn_prev.clicked.connect(self._prev_step)
        bottom_bar.addWidget(self.btn_prev)

        self.btn_next = QPushButton("Next →")
        self.btn_next.setObjectName("primaryBtn")
        self.btn_next.setFixedHeight(34)
        self.btn_next.setFixedWidth(90)
        self.btn_next.clicked.connect(self._next_step)
        bottom_bar.addWidget(self.btn_next)

        layout.addLayout(bottom_bar)
        self._update_ui_state()

    def _build_step_card(self, step: Dict[str, Any]) -> QWidget:
        container = QFrame()
        container.setObjectName("stepCard")
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(24, 20, 24, 20)
        c_layout.setSpacing(12)

        lbl_b = QLabel(step["badge"])
        lbl_b.setObjectName("badgeLabel")
        c_layout.addWidget(lbl_b)

        lbl_t = QLabel(step["title"])
        lbl_t.setObjectName("titleLabel")
        c_layout.addWidget(lbl_t)

        lbl_sub = QLabel(step["subtitle"])
        lbl_sub.setObjectName("subtitleLabel")
        c_layout.addWidget(lbl_sub)

        lbl_c = QLabel(step["content"])
        lbl_c.setObjectName("contentLabel")
        lbl_c.setWordWrap(True)
        lbl_c.setTextFormat(Qt.TextFormat.RichText)
        c_layout.addWidget(lbl_c, 1)

        # Tip box
        tip_frame = QFrame()
        tip_frame.setObjectName("tipCard")
        tip_lay = QVBoxLayout(tip_frame)
        tip_lay.setContentsMargins(10, 8, 10, 8)
        lbl_tip = QLabel(step["tip"])
        lbl_tip.setObjectName("tipLabel")
        lbl_tip.setWordWrap(True)
        tip_lay.addWidget(lbl_tip)
        c_layout.addWidget(tip_frame)

        return container

    def _update_ui_state(self):
        step = self.STEPS[self.current_step]
        self.stack.setCurrentIndex(self.current_step)
        self.lbl_counter.setText(f"Step {self.current_step + 1} of {len(self.STEPS)}")
        self.btn_prev.setEnabled(self.current_step > 0)

        if self.current_step == len(self.STEPS) - 1:
            self.btn_next.setText("Finish ✓")
        else:
            self.btn_next.setText("Next →")

        # Action button text
        self.btn_action.setText(step["action_text"])

        # Update dots
        for i, dot in enumerate(self.dots):
            if i == self.current_step:
                dot.setText("●")
                dot.setStyleSheet("color: #C2410C; font-size: 14px;")
            else:
                dot.setText("○")
                dot.setStyleSheet("color: #D6D3D1; font-size: 14px;")

    def _next_step(self):
        if self.current_step < len(self.STEPS) - 1:
            self.current_step += 1
            self._update_ui_state()
        else:
            self.accept()

    def _prev_step(self):
        if self.current_step > 0:
            self.current_step -= 1
            self._update_ui_state()

    def _handle_action_shortcut(self):
        step = self.STEPS[self.current_step]
        target_tab = step["target_tab"]
        self.accept()
        if self.main_window:
            if target_tab >= 0 and hasattr(self.main_window, "switch_tab"):
                self.main_window.switch_tab(target_tab)
            elif target_tab == -1 and hasattr(self.main_window, "launch_article_generator"):
                self.main_window.launch_article_generator()
