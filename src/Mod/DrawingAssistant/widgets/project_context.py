# SPDX-License-Identifier: LGPL-2.1-or-later
"""
Project Context Widget - Full-panel view for project notes.
Shown when the user selects the "Context" tab in the mode switcher.
"""

from pathlib import Path

import FreeCAD
from PySide6 import QtCore, QtWidgets
from .. import Theme


class ProjectContextWidget(QtWidgets.QWidget):
    """Full-panel view for editing project notes.

    Replaces the chat view when the user selects the "Context" tab.

    Signals:
        contextChanged: Emitted when notes change.
    """

    contextChanged = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._project_dir = None
        self._save_timer = QtCore.QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(2000)
        self._save_timer.timeout.connect(self._save_notes)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"background-color: {Theme.COLORS['bg_primary']};")

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        # ── Section: Project Notes ────────────────────────────────────
        notes_header = QtWidgets.QLabel("Project notes")
        notes_header.setStyleSheet(f"""
            color: {Theme.COLORS['text_secondary']};
            font-size: {Theme.FONTS['size_xs']};
            font-weight: {Theme.FONTS['weight_semibold']};
            text-transform: uppercase;
            letter-spacing: 0.5px;
            background: transparent;
        """)
        root.addWidget(notes_header)

        self._notes_edit = QtWidgets.QPlainTextEdit()
        self._notes_edit.setPlaceholderText(
            "Add project notes for the AI assistant.\n\n"
            "Examples:\n"
            "  - Concrete: C25/30, Rebar: B500B\n"
            "  - Cover: 40mm, Stirrups: T12@200\n"
            "  - Foundations: FS-XX, Beams: B-XXX\n"
            "  - Scale: 1:50 for details, 1:100 for plans\n"
            "  - Company: Acme Engineering, Project: P-2025-042"
        )
        self._notes_edit.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {Theme.COLORS['bg_secondary']};
                color: {Theme.COLORS['text_primary']};
                border: 1px solid {Theme.COLORS['border_subtle']};
                border-radius: {Theme.RADIUS['md']};
                padding: 12px;
                font-size: {Theme.FONTS['size_sm']};
                font-family: {Theme.FONTS['family_sans']};
                line-height: 1.5;
            }}
            QPlainTextEdit:focus {{
                border-color: {Theme.COLORS['accent_primary']};
            }}
        """)
        self._notes_edit.textChanged.connect(self._on_notes_changed)
        root.addWidget(self._notes_edit, stretch=1)

        # Auto-save hint at bottom
        hint = QtWidgets.QLabel("Changes are saved automatically")
        hint.setAlignment(QtCore.Qt.AlignCenter)
        hint.setStyleSheet(f"""
            color: {Theme.COLORS['text_muted']};
            font-size: 10px;
            background: transparent;
            padding: 4px;
        """)
        root.addWidget(hint)

    # ── Public API ────────────────────────────────────────────────────

    def set_project_dir(self, project_dir):
        """Load project notes from project directory."""
        self._project_dir = project_dir
        if not project_dir:
            self._notes_edit.blockSignals(True)
            self._notes_edit.setPlainText("")
            self._notes_edit.blockSignals(False)
            return

        project_dir = Path(project_dir)

        project_md = project_dir / "project.md"
        self._notes_edit.blockSignals(True)
        if project_md.exists():
            try:
                self._notes_edit.setPlainText(
                    project_md.read_text(encoding="utf-8")
                )
            except Exception as e:
                FreeCAD.Console.PrintWarning(
                    f"DrawingAssistant: Failed to read project notes: {e}\n"
                )
                self._notes_edit.setPlainText("")
        else:
            self._notes_edit.setPlainText("")
        self._notes_edit.blockSignals(False)

    def get_notes_text(self):
        return self._notes_edit.toPlainText()

    # ── Notes ─────────────────────────────────────────────────────────

    def flush_notes(self):
        """Stop debounce timer and save notes immediately."""
        if self._save_timer.isActive():
            self._save_timer.stop()
            self._save_notes()

    def _on_notes_changed(self):
        self._save_timer.start()

    def _save_notes(self):
        if not self._project_dir:
            return
        try:
            (Path(self._project_dir) / "project.md").write_text(
                self._notes_edit.toPlainText(), encoding="utf-8"
            )
            self.contextChanged.emit()
        except Exception as e:
            FreeCAD.Console.PrintWarning(
                f"DrawingAssistant: Failed to save project notes: {e}\n"
            )
