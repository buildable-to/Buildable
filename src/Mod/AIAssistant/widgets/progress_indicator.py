# SPDX-License-Identifier: LGPL-2.1-or-later
"""
PhasedProgressIndicator - Shows meaningful workflow phases during AI processing.

Replaces generic skeleton bars with actual progress through:
1. Reading source.py
2. Understanding design
3. Generating changes
4. Awaiting approval
"""

from enum import Enum, auto
from PySide6 import QtWidgets, QtCore, QtGui

from ..Theme import Theme


class Phase(Enum):
    """Workflow phases during AI processing."""
    READING = auto()
    UNDERSTANDING = auto()
    GENERATING = auto()
    AWAITING_APPROVAL = auto()


class PhaseState(Enum):
    """Visual state of a phase step."""
    PENDING = "pending"      # Empty circle
    ACTIVE = "active"        # Animated spinner
    COMPLETE = "complete"    # Checkmark


# Phase display configuration
PHASE_CONFIG = {
    Phase.READING: {
        "label": "Reading source.py",
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
    """Shows workflow phases during AI processing."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._steps: dict[Phase, PhaseStepWidget] = {}
        self._current_phase: Phase | None = None
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

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(2)

        # Create step widgets for each phase
        for phase in Phase:
            step = PhaseStepWidget(phase)
            self._steps[phase] = step
            layout.addWidget(step)

        # Start with first phase active
        self.set_phase(Phase.READING)

    def set_phase(self, phase: Phase):
        """Set the current active phase, completing previous phases."""
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
        for step in self._steps.values():
            step.set_state(PhaseState.COMPLETE)
        self._current_phase = None

    def reset(self):
        """Reset all phases to pending."""
        for step in self._steps.values():
            step.set_state(PhaseState.PENDING)
        self._current_phase = None

    def update_from_tool(self, tool_name: str, tool_input: dict):
        """Update phase based on tool call from backend."""
        file_path = tool_input.get("file_path", "")
        pattern = tool_input.get("pattern", "")

        # Determine phase from tool
        if tool_name == "Read" and "source.py" in file_path:
            target_phase = Phase.READING
        elif tool_name in ("Glob", "Grep", "Read"):
            target_phase = Phase.UNDERSTANDING
        elif tool_name in ("Edit", "Write"):
            target_phase = Phase.GENERATING
        else:
            # Unknown tool, don't change phase
            return

        # Only advance forward, never backward
        if self._current_phase is None:
            self.set_phase(target_phase)
        elif target_phase.value > self._current_phase.value:
            self.set_phase(target_phase)

    def set_awaiting_approval(self):
        """Set to awaiting approval phase (called when response complete)."""
        self.set_phase(Phase.AWAITING_APPROVAL)


# Backwards compatibility
ThinkingIndicator = PhasedProgressIndicator
