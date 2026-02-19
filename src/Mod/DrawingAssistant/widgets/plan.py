# SPDX-License-Identifier: LGPL-2.1-or-later
"""
Plan Widget - Shows AI's execution plan for user approval before code generation.
Part of the two-phase LLM flow: plan -> approve -> code -> preview -> execute.

Design: Rendered markdown display (same as assistant messages). User iterates
on the plan by typing follow-up messages, not by editing the text directly.
"""

import re
from PySide6 import QtCore, QtWidgets
from typing import List
from .. import Theme
from .message_delegate import _md_to_html


class PlanStep:
    """A single step in the execution plan (used for counting only)."""

    def __init__(self, number: int, action: str, description: str):
        self.number = number
        self.action = action
        self.description = description

    @staticmethod
    def parse_plan(plan_text: str) -> List["PlanStep"]:
        """Parse plan text to count steps."""
        steps = []
        chunks = re.split(r'(?=(?:^|\n)\s*\d+\.\s)', plan_text)
        for chunk in chunks:
            chunk = chunk.strip()
            if not chunk:
                continue
            match = re.match(
                r'(\d+)\.\s+\*?\*?([^*:\n]+?)\*?\*?\s*:\s*(.*)',
                chunk, re.DOTALL,
            )
            if match:
                steps.append(PlanStep(
                    number=int(match.group(1)),
                    action=match.group(2).strip(),
                    description=" ".join(match.group(3).strip().split()),
                ))
        return steps


class PlanWidget(QtWidgets.QFrame):
    """Execution plan rendered as markdown with approve/iterate buttons.

    Signals:
        planApproved: User approved the plan
        planCancelled: User cancelled the plan
        planKeepPlanning: User wants to refine the plan via follow-up message
    """

    planApproved = QtCore.Signal()
    planCancelled = QtCore.Signal()
    planKeepPlanning = QtCore.Signal()

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
                background-color: {Theme.COLORS['assistant_card_bg']};
                border: 1px solid {Theme.COLORS['assistant_card_border']};
                border-radius: {Theme.RADIUS['lg']};
            }}
        """)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # ── Header ──
        header = QtWidgets.QHBoxLayout()
        header.setSpacing(8)

        title = QtWidgets.QLabel("Execution Plan")
        title.setStyleSheet(f"""
            font-size: {Theme.FONTS['size_sm']};
            font-weight: {Theme.FONTS['weight_semibold']};
            color: {Theme.COLORS['accent_primary']};
            background: transparent;
        """)
        header.addWidget(title)

        if self._steps:
            count = QtWidgets.QLabel(f"{len(self._steps)} steps")
            count.setStyleSheet(f"""
                color: {Theme.COLORS['text_muted']};
                font-size: {Theme.FONTS['size_xs']};
                background: transparent;
            """)
            header.addWidget(count)

        header.addStretch()
        layout.addLayout(header)

        # ── Rendered markdown content ──
        html = _md_to_html(self._plan_text)
        self._content_label = QtWidgets.QLabel(html)
        self._content_label.setTextFormat(QtCore.Qt.RichText)
        self._content_label.setWordWrap(True)
        self._content_label.setTextInteractionFlags(
            QtCore.Qt.TextSelectableByMouse | QtCore.Qt.LinksAccessibleByMouse
        )
        self._content_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.COLORS['assistant_text']};
                font-size: {Theme.FONTS['size_sm']};
                line-height: {Theme.FONTS['line_height_normal']};
                background: transparent;
            }}
        """)
        layout.addWidget(self._content_label)

        # ── Buttons ──
        self._btn_container = QtWidgets.QWidget()
        btn_layout = QtWidgets.QHBoxLayout(self._btn_container)
        btn_layout.setContentsMargins(0, 4, 0, 0)
        btn_layout.setSpacing(10)

        keep_btn = QtWidgets.QPushButton("Keep Planning")
        keep_btn.setCursor(QtCore.Qt.PointingHandCursor)
        keep_btn.setStyleSheet(f"""
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
        keep_btn.clicked.connect(self._on_keep_planning)
        btn_layout.addWidget(keep_btn)

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

        layout.addWidget(self._btn_container)

    def _setup_entry_animation(self):
        """Fade-in animation, removed after completion to not block events."""
        self._opacity_effect = QtWidgets.QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)
        self._opacity_effect.setOpacity(0.0)

        self._fade_anim = QtCore.QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_anim.setDuration(Theme.ANIMATION['duration_normal'])
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        self._fade_anim.finished.connect(lambda: self.setGraphicsEffect(None))
        self._fade_anim.start()

    def _on_approve(self):
        self.planApproved.emit()

    def _on_keep_planning(self):
        self.planKeepPlanning.emit()

    def set_disabled(self, disabled: bool):
        """Dim widget and hide buttons after approval/cancellation."""
        if disabled:
            self._btn_container.hide()
            self._content_label.setStyleSheet(f"""
                QLabel {{
                    color: {Theme.COLORS['text_muted']};
                    font-size: {Theme.FONTS['size_sm']};
                    line-height: {Theme.FONTS['line_height_normal']};
                    background: transparent;
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
        """Get the plan text."""
        return self._plan_text
