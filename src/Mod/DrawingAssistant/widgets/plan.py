# SPDX-License-Identifier: LGPL-2.1-or-later
"""
Plan Widget - Shows AI's execution plan for user approval before code generation.
Part of the two-phase LLM flow: plan -> approve -> code -> preview -> execute.

Design: A single editable text document. Users read the plan, edit freely if
needed, then approve or cancel. No card splitting — just clean typography.
"""

import re
from PySide6 import QtCore, QtWidgets, QtGui
from typing import List
from .. import Theme


class PlanStep:
    """A single step in the execution plan (used for counting only)."""

    def __init__(self, number: int, action: str, description: str):
        self.number = number
        self.action = action
        self.description = description

    @staticmethod
    def parse_plan(plan_text: str) -> List["PlanStep"]:
        """Parse plan text into PlanStep objects.

        Expected format:
        ## Plan
        1. **Action**: Description (may span multiple lines)
        2. Action: Description
        """
        steps = []
        chunks = re.split(r'(?=(?:^|\n)\s*\d+\.\s)', plan_text)

        for chunk in chunks:
            chunk = chunk.strip()
            if not chunk:
                continue

            match = re.match(
                r'(\d+)\.\s+\*?\*?([^*:\n]+?)\*?\*?\s*:\s*(.*)',
                chunk,
                re.DOTALL,
            )
            if not match:
                continue

            number = int(match.group(1))
            action = match.group(2).strip()
            raw_desc = match.group(3).strip()
            description = " ".join(raw_desc.split())

            steps.append(PlanStep(
                number=number,
                action=action,
                description=description,
            ))

        return steps


class PlanWidget(QtWidgets.QFrame):
    """Execution plan as a single editable text document.

    Signals:
        planApproved: User approved the plan without edits
        planEdited(str): User edited and approved, new text provided
        planCancelled: User cancelled the plan
    """

    planApproved = QtCore.Signal()
    planEdited = QtCore.Signal(str)
    planCancelled = QtCore.Signal()

    def __init__(self, plan_text: str, user_request: str = "", parent=None):
        super().__init__(parent)
        self._plan_text = plan_text
        self._user_request = user_request
        self._steps = PlanStep.parse_plan(plan_text)
        self._setup_ui()
        self._setup_entry_animation()

    def _setup_ui(self):
        self.setObjectName("PlanWidget")
        self.setStyleSheet(f"""
            #PlanWidget {{
                background-color: {Theme.COLORS['bg_secondary']};
                border: 1px solid {Theme.COLORS['border_default']};
                border-radius: {Theme.RADIUS['lg']};
            }}
        """)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        # ── Header ──
        header_layout = QtWidgets.QHBoxLayout()
        header_layout.setSpacing(8)

        title_label = QtWidgets.QLabel("Execution Plan")
        title_label.setStyleSheet(f"""
            font-size: {Theme.FONTS['size_base']};
            font-weight: {Theme.FONTS['weight_semibold']};
            color: {Theme.COLORS['text_primary']};
            background: transparent;
        """)
        header_layout.addWidget(title_label)

        count_text = f"{len(self._steps)} steps" if self._steps else ""
        count_label = QtWidgets.QLabel(count_text)
        count_label.setStyleSheet(f"""
            color: {Theme.COLORS['text_muted']};
            font-size: {Theme.FONTS['size_xs']};
            background: transparent;
        """)
        header_layout.addWidget(count_label)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # ── Plan text editor ──
        self._editor = QtWidgets.QPlainTextEdit()
        self._editor.setPlainText(self._plan_text)
        self._editor.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {Theme.COLORS['bg_primary']};
                color: {Theme.COLORS['text_secondary']};
                border: 1px solid {Theme.COLORS['border_subtle']};
                border-radius: {Theme.RADIUS['sm']};
                padding: 12px;
                font-family: {Theme.FONTS['family_sans']};
                font-size: {Theme.FONTS['size_sm']};
                selection-background-color: {Theme.COLORS['accent_primary']};
            }}
            QPlainTextEdit:focus {{
                border-color: {Theme.COLORS['border_focus']};
            }}
        """)
        # Size to content, with reasonable bounds
        self._editor.setMinimumHeight(150)
        self._editor.setMaximumHeight(450)
        self._adjust_height()
        self._editor.textChanged.connect(self._adjust_height)
        layout.addWidget(self._editor)

        # ── Buttons ──
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.setSpacing(10)

        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.setCursor(QtCore.Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.COLORS['text_secondary']};
                border: 1px solid {Theme.COLORS['border_default']};
                border-radius: {Theme.RADIUS['sm']};
                padding: 8px 20px;
                font-size: {Theme.FONTS['size_sm']};
                font-weight: {Theme.FONTS['weight_medium']};
            }}
            QPushButton:hover {{
                background-color: {Theme.COLORS['bg_hover']};
                color: {Theme.COLORS['text_primary']};
            }}
        """)
        cancel_btn.clicked.connect(self._on_cancel)
        btn_layout.addWidget(cancel_btn)

        btn_layout.addStretch()

        approve_btn = QtWidgets.QPushButton("Approve Plan")
        approve_btn.setCursor(QtCore.Qt.PointingHandCursor)
        approve_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.COLORS['accent_primary']};
                color: white;
                border: none;
                border-radius: {Theme.RADIUS['sm']};
                padding: 8px 24px;
                font-size: {Theme.FONTS['size_sm']};
                font-weight: {Theme.FONTS['weight_medium']};
            }}
            QPushButton:hover {{
                background-color: {Theme.COLORS['accent_primary_hover']};
            }}
        """)
        approve_btn.clicked.connect(self._on_approve)
        btn_layout.addWidget(approve_btn)

        layout.addLayout(btn_layout)

    def _adjust_height(self):
        """Resize editor to fit content within min/max bounds."""
        doc = self._editor.document()
        # documentSize height + padding
        content_height = int(doc.size().height()) + 30
        clamped = max(150, min(450, content_height))
        self._editor.setFixedHeight(clamped)

    def _setup_entry_animation(self):
        """Setup fade-in animation."""
        self._opacity_effect = QtWidgets.QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)
        self._opacity_effect.setOpacity(0.0)

        self._fade_anim = QtCore.QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_anim.setDuration(Theme.ANIMATION['duration_normal'])
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        self._fade_anim.finished.connect(self._remove_opacity_effect)
        self._fade_anim.start()

    def _remove_opacity_effect(self):
        """Remove opacity effect so editor receives input events."""
        self.setGraphicsEffect(None)

    def _on_approve(self):
        """Handle approve — emit edited signal if text was changed."""
        current = self._editor.toPlainText()
        if current != self._plan_text:
            self.planEdited.emit(current)
        else:
            self.planApproved.emit()

    def _on_cancel(self):
        self.planCancelled.emit()

    def set_disabled(self, disabled: bool):
        """Disable widget after approval/cancellation — visually dim it."""
        if disabled:
            self._editor.setReadOnly(True)
            # Hide buttons, dim the whole widget
            for btn in self.findChildren(QtWidgets.QPushButton):
                btn.hide()
            self._editor.setStyleSheet(f"""
                QPlainTextEdit {{
                    background-color: {Theme.COLORS['bg_tertiary']};
                    color: {Theme.COLORS['text_muted']};
                    border: 1px solid {Theme.COLORS['border_subtle']};
                    border-radius: {Theme.RADIUS['sm']};
                    padding: 12px;
                    font-family: {Theme.FONTS['family_sans']};
                    font-size: {Theme.FONTS['size_sm']};
                }}
            """)
            self.setStyleSheet(f"""
                #PlanWidget {{
                    background-color: {Theme.COLORS['bg_tertiary']};
                    border: 1px solid {Theme.COLORS['border_subtle']};
                    border-radius: {Theme.RADIUS['lg']};
                }}
            """)

    def get_plan_text(self) -> str:
        """Get current plan text (possibly edited)."""
        return self._editor.toPlainText()
