# SPDX-License-Identifier: LGPL-2.1-or-later
"""
PhasedProgressIndicator - Shows meaningful workflow phases during AI processing.

Starts with a simple "Thinking..." spinner. When tool calls arrive, transitions
to phased steps showing progress through the design change workflow:
1. Reading page files
2. Understanding design
3. Generating changes
4. Awaiting approval
"""

from enum import Enum, auto
from PySide6 import QtWidgets, QtCore, QtGui

from .. import Theme


class Phase(Enum):
    """Workflow phases during AI processing."""
    READING = auto()
    UNDERSTANDING = auto()
    GENERATING = auto()
    REVIEWING = auto()
    AWAITING_APPROVAL = auto()


class PhaseState(Enum):
    """Visual state of a phase step."""
    PENDING = "pending"      # Empty circle
    ACTIVE = "active"        # Animated spinner
    COMPLETE = "complete"    # Checkmark


# Phase display configuration
PHASE_CONFIG = {
    Phase.READING: {
        "label": "Reading page files",
        "description": "Loading current design",
    },
    Phase.UNDERSTANDING: {
        "label": "Understanding design",
        "description": "Analyzing structure",
    },
    Phase.GENERATING: {
        "label": "Generating changes",
        "description": "Writing code",
    },
    Phase.REVIEWING: {
        "label": "Reviewing changes",
        "description": "Self-review",
    },
    Phase.AWAITING_APPROVAL: {
        "label": "Awaiting approval",
        "description": "Review changes",
    },
}


class PhaseIcon(QtWidgets.QWidget):
    """Animated phase icon showing pending/active/complete state."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = PhaseState.PENDING
        self._rotation = 0
        self._animation = None
        self.setFixedSize(20, 20)
        self._setup_animation()

    def _setup_animation(self):
        """Setup rotation animation for active state."""
        self._animation = QtCore.QPropertyAnimation(self, b"rotation")
        self._animation.setDuration(1000)
        self._animation.setStartValue(0)
        self._animation.setEndValue(360)
        self._animation.setLoopCount(-1)  # Infinite

    def get_rotation(self):
        return self._rotation

    def set_rotation(self, value):
        self._rotation = value
        self.update()

    rotation = QtCore.Property(int, get_rotation, set_rotation)

    def set_state(self, state: PhaseState):
        """Update the icon state."""
        self._state = state
        if state == PhaseState.ACTIVE:
            self._animation.start()
        else:
            self._animation.stop()
            self._rotation = 0
        self.update()

    def paintEvent(self, event):
        """Draw the phase icon."""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        rect = self.rect()
        center = rect.center()
        radius = 8

        if self._state == PhaseState.PENDING:
            # Empty circle
            pen = QtGui.QPen(QtGui.QColor(Theme.COLORS['text_muted']))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.drawEllipse(center, radius, radius)

        elif self._state == PhaseState.ACTIVE:
            # Spinning arc
            pen = QtGui.QPen(QtGui.QColor(Theme.COLORS['accent_primary']))
            pen.setWidth(2)
            pen.setCapStyle(QtCore.Qt.RoundCap)
            painter.setPen(pen)
            painter.setBrush(QtCore.Qt.NoBrush)

            arc_rect = QtCore.QRectF(
                center.x() - radius,
                center.y() - radius,
                radius * 2,
                radius * 2
            )
            # Draw arc with rotation
            start_angle = (self._rotation * 16) % 5760
            span_angle = 270 * 16  # 270 degrees
            painter.drawArc(arc_rect, start_angle, span_angle)

        elif self._state == PhaseState.COMPLETE:
            # Filled circle with checkmark
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QtGui.QColor(Theme.COLORS['accent_success']))
            painter.drawEllipse(center, radius, radius)

            # Draw checkmark
            pen = QtGui.QPen(QtGui.QColor("#ffffff"))
            pen.setWidth(2)
            pen.setCapStyle(QtCore.Qt.RoundCap)
            pen.setJoinStyle(QtCore.Qt.RoundJoin)
            painter.setPen(pen)

            # Checkmark path
            path = QtGui.QPainterPath()
            path.moveTo(center.x() - 4, center.y())
            path.lineTo(center.x() - 1, center.y() + 3)
            path.lineTo(center.x() + 5, center.y() - 3)
            painter.drawPath(path)

        painter.end()


class PhaseStepWidget(QtWidgets.QWidget):
    """Single phase step with icon and label."""

    def __init__(self, phase: Phase, parent=None):
        super().__init__(parent)
        self._phase = phase
        self._state = PhaseState.PENDING
        self._setup_ui()

    def _setup_ui(self):
        """Build the step UI."""
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(12)

        # Phase icon
        self._icon = PhaseIcon()
        layout.addWidget(self._icon)

        # Label
        config = PHASE_CONFIG[self._phase]
        self._label = QtWidgets.QLabel(config["label"])
        self._update_label_style()
        layout.addWidget(self._label)
        layout.addStretch()

    def _update_label_style(self):
        """Update label styling based on state."""
        if self._state == PhaseState.PENDING:
            color = Theme.COLORS['text_muted']
            weight = Theme.FONTS['weight_normal']
        elif self._state == PhaseState.ACTIVE:
            color = Theme.COLORS['text_primary']
            weight = Theme.FONTS['weight_medium']
        else:  # COMPLETE
            color = Theme.COLORS['text_secondary']
            weight = Theme.FONTS['weight_normal']

        self._label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: {Theme.FONTS['size_sm']};
                font-weight: {weight};
                background: transparent;
            }}
        """)

    def set_state(self, state: PhaseState):
        """Update the step state."""
        self._state = state
        self._icon.set_state(state)
        self._update_label_style()

    @property
    def phase(self) -> Phase:
        return self._phase


class PhasedProgressIndicator(QtWidgets.QFrame):
    """Shows workflow phases during AI processing.

    Starts in "thinking" mode (simple spinner + label).
    Transitions to phased steps when tool calls arrive.
    """

    def __init__(self, parent=None, show_review_phase: bool = True):
        super().__init__(parent)
        self._steps: dict[Phase, PhaseStepWidget] = {}
        self._current_phase: Phase | None = None
        self._show_review_phase = show_review_phase
        self._in_thinking_mode = True
        self._setup_ui()

    def _setup_ui(self):
        """Build the indicator UI."""
        self.setObjectName("phasedProgress")
        self.setStyleSheet(f"""
            QFrame#phasedProgress {{
                background-color: {Theme.COLORS['assistant_card_bg']};
                border: 1px solid {Theme.COLORS['assistant_card_border']};
                border-radius: {Theme.RADIUS['lg']};
            }}
        """)

        self._layout = QtWidgets.QVBoxLayout(self)
        self._layout.setContentsMargins(16, 14, 16, 14)
        self._layout.setSpacing(2)

        # --- Thinking mode widget (shown initially) ---
        self._thinking_widget = QtWidgets.QWidget()
        thinking_layout = QtWidgets.QHBoxLayout(self._thinking_widget)
        thinking_layout.setContentsMargins(0, 4, 0, 4)
        thinking_layout.setSpacing(12)

        self._thinking_icon = PhaseIcon()
        self._thinking_icon.set_state(PhaseState.ACTIVE)
        thinking_layout.addWidget(self._thinking_icon)

        thinking_label = QtWidgets.QLabel("Thinking...")
        thinking_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.COLORS['text_primary']};
                font-size: {Theme.FONTS['size_sm']};
                font-weight: {Theme.FONTS['weight_medium']};
                background: transparent;
            }}
        """)
        thinking_layout.addWidget(thinking_label)
        thinking_layout.addStretch()

        self._layout.addWidget(self._thinking_widget)

        # --- Phased steps (hidden initially) ---
        self._phases_container = QtWidgets.QWidget()
        phases_layout = QtWidgets.QVBoxLayout(self._phases_container)
        phases_layout.setContentsMargins(0, 0, 0, 0)
        phases_layout.setSpacing(2)

        for phase in Phase:
            step = PhaseStepWidget(phase)
            self._steps[phase] = step
            if phase == Phase.REVIEWING and not self._show_review_phase:
                step.hide()
            phases_layout.addWidget(step)

        self._phases_container.hide()
        self._layout.addWidget(self._phases_container)

    def _switch_to_phased_mode(self):
        """Transition from thinking mode to phased steps."""
        if not self._in_thinking_mode:
            return
        self._in_thinking_mode = False
        self._thinking_icon.set_state(PhaseState.PENDING)  # Stop animation
        self._thinking_widget.hide()
        self._phases_container.show()

    def set_review_phase_visible(self, visible: bool):
        """Show or hide the reviewing phase."""
        self._show_review_phase = visible
        if Phase.REVIEWING in self._steps:
            self._steps[Phase.REVIEWING].setVisible(visible)

    def set_phase(self, phase: Phase):
        """Set the current active phase, completing previous phases."""
        self._switch_to_phased_mode()
        self._current_phase = phase

        for p in Phase:
            if p.value < phase.value:
                self._steps[p].set_state(PhaseState.COMPLETE)
            elif p.value == phase.value:
                self._steps[p].set_state(PhaseState.ACTIVE)
            else:
                self._steps[p].set_state(PhaseState.PENDING)

    def advance_phase(self):
        """Move to the next phase."""
        if self._current_phase is None:
            self.set_phase(Phase.READING)
            return

        phases = list(Phase)
        current_idx = phases.index(self._current_phase)
        if current_idx < len(phases) - 1:
            self.set_phase(phases[current_idx + 1])

    def complete_all(self):
        """Mark all phases as complete."""
        self._switch_to_phased_mode()
        for step in self._steps.values():
            step.set_state(PhaseState.COMPLETE)
        self._current_phase = None

    def reset(self):
        """Reset to thinking mode."""
        # Reset phased steps
        for step in self._steps.values():
            step.set_state(PhaseState.PENDING)
        self._current_phase = None

        # Return to thinking mode
        self._in_thinking_mode = True
        self._thinking_icon.set_state(PhaseState.ACTIVE)
        self._thinking_widget.show()
        self._phases_container.hide()

    def update_from_tool(self, tool_name: str, tool_input: dict):
        """Update phase based on tool call from backend."""
        file_path = tool_input.get("file_path", "")

        # Determine phase from tool
        if tool_name == "Read" and "/pages/" in file_path:
            target_phase = Phase.READING
        elif tool_name in ("Glob", "Grep", "Read"):
            target_phase = Phase.UNDERSTANDING
        elif tool_name in ("Edit", "Write"):
            target_phase = Phase.GENERATING
        else:
            # Unknown tool, don't change phase
            return

        # First tool call transitions from thinking to phased
        # Only advance forward, never backward
        if self._current_phase is None:
            self.set_phase(target_phase)
        elif target_phase.value > self._current_phase.value:
            self.set_phase(target_phase)

    def set_reviewing(self):
        """Set to reviewing phase (called when self-review starts)."""
        self.set_phase(Phase.REVIEWING)

    def set_awaiting_approval(self):
        """Set to awaiting approval phase (called when response complete)."""
        self.set_phase(Phase.AWAITING_APPROVAL)


# Backwards compatibility
ThinkingIndicator = PhasedProgressIndicator
