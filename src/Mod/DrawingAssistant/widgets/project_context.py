# SPDX-License-Identifier: LGPL-2.1-or-later
"""
Project Context Widget - Collapsible panel for engineer's project notes and reference documents.
Provides persistent project knowledge (materials, naming, rules) and PDF reference management.
"""

import shutil
from pathlib import Path

from PySide6 import QtCore, QtWidgets
from .. import Theme


class ProjectContextWidget(QtWidgets.QFrame):
    """Collapsible panel showing project notes (text) and reference documents (files).

    Sits between the header and chat area. Collapsed by default, showing a
    one-line summary. Expanded shows a text editor and file list.

    Signals:
        contextChanged: Emitted when notes or file list changes.
    """

    contextChanged = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._project_dir = None
        self._collapsed = True
        self._save_timer = QtCore.QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(2000)
        self._save_timer.timeout.connect(self._save_notes)
        self._setup_ui()

    # ── UI Setup ──────────────────────────────────────────────────────

    def _setup_ui(self):
        self.setObjectName("ProjectContextWidget")
        self.setStyleSheet(f"""
            #ProjectContextWidget {{
                background-color: transparent;
                border: none;
            }}
        """)

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(10, 4, 10, 4)
        root.setSpacing(0)

        # ── Header row (always visible) ──
        header = QtWidgets.QWidget()
        header.setStyleSheet("background: transparent;")
        header.setCursor(QtCore.Qt.PointingHandCursor)
        header_layout = QtWidgets.QHBoxLayout(header)
        header_layout.setContentsMargins(4, 2, 4, 2)
        header_layout.setSpacing(6)

        self._arrow = QtWidgets.QLabel("\u25b6")  # ▶
        self._arrow.setStyleSheet(f"""
            color: {Theme.COLORS['text_muted']};
            font-size: {Theme.FONTS['size_xs']};
            background: transparent;
        """)
        header_layout.addWidget(self._arrow)

        title = QtWidgets.QLabel("Project Context")
        title.setStyleSheet(f"""
            color: {Theme.COLORS['text_muted']};
            font-size: {Theme.FONTS['size_xs']};
            font-weight: {Theme.FONTS['weight_medium']};
            background: transparent;
        """)
        header_layout.addWidget(title)

        self._badge = QtWidgets.QLabel("")
        self._badge.setStyleSheet(f"""
            color: {Theme.COLORS['text_muted']};
            font-size: {Theme.FONTS['size_xs']};
            background: transparent;
        """)
        header_layout.addWidget(self._badge)

        header_layout.addStretch()

        # Make header clickable
        header.mousePressEvent = lambda _: self._toggle_collapsed()
        root.addWidget(header)

        # ── Content area (hidden when collapsed) ──
        self._content = QtWidgets.QFrame()
        self._content.setObjectName("ProjectContextContent")
        self._content.setStyleSheet(f"""
            #ProjectContextContent {{
                background-color: {Theme.COLORS['bg_secondary']};
                border: 1px solid {Theme.COLORS['border_subtle']};
                border-radius: {Theme.RADIUS['md']};
            }}
        """)
        content_layout = QtWidgets.QVBoxLayout(self._content)
        content_layout.setContentsMargins(12, 10, 12, 10)
        content_layout.setSpacing(8)

        # Notes label
        notes_label = QtWidgets.QLabel("Project notes")
        notes_label.setStyleSheet(f"""
            color: {Theme.COLORS['text_secondary']};
            font-size: {Theme.FONTS['size_xs']};
            font-weight: {Theme.FONTS['weight_medium']};
            background: transparent;
        """)
        content_layout.addWidget(notes_label)

        # Text area for notes
        self._notes_edit = QtWidgets.QPlainTextEdit()
        self._notes_edit.setPlaceholderText(
            "Add project notes here \u2014 materials, naming conventions, "
            "drawing preferences, title block info..."
        )
        self._notes_edit.setMinimumHeight(80)
        self._notes_edit.setMaximumHeight(120)
        self._notes_edit.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {Theme.COLORS['bg_primary']};
                color: {Theme.COLORS['text_primary']};
                border: 1px solid {Theme.COLORS['border_subtle']};
                border-radius: {Theme.RADIUS['sm']};
                padding: 8px;
                font-size: {Theme.FONTS['size_sm']};
                font-family: {Theme.FONTS['family_sans']};
            }}
            QPlainTextEdit:focus {{
                border-color: {Theme.COLORS['accent_primary']};
            }}
        """)
        self._notes_edit.textChanged.connect(self._on_notes_changed)
        content_layout.addWidget(self._notes_edit)

        # Reference documents label
        docs_label = QtWidgets.QLabel("Reference documents")
        docs_label.setStyleSheet(f"""
            color: {Theme.COLORS['text_secondary']};
            font-size: {Theme.FONTS['size_xs']};
            font-weight: {Theme.FONTS['weight_medium']};
            background: transparent;
        """)
        content_layout.addWidget(docs_label)

        # File list container
        self._file_list = QtWidgets.QVBoxLayout()
        self._file_list.setSpacing(4)
        content_layout.addLayout(self._file_list)

        # "No documents" placeholder
        self._no_docs_label = QtWidgets.QLabel("No reference documents added")
        self._no_docs_label.setStyleSheet(f"""
            color: {Theme.COLORS['text_muted']};
            font-size: {Theme.FONTS['size_xs']};
            background: transparent;
            padding: 4px 0;
        """)
        self._file_list.addWidget(self._no_docs_label)

        # Add document button
        add_btn = QtWidgets.QPushButton("+ Add document")
        add_btn.setCursor(QtCore.Qt.PointingHandCursor)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.COLORS['accent_primary']};
                border: 1px dashed {Theme.COLORS['border_default']};
                border-radius: {Theme.RADIUS['sm']};
                padding: 6px 12px;
                font-size: {Theme.FONTS['size_xs']};
                font-weight: {Theme.FONTS['weight_medium']};
            }}
            QPushButton:hover {{
                background-color: {Theme.COLORS['bg_hover']};
                border-color: {Theme.COLORS['accent_primary']};
            }}
        """)
        add_btn.clicked.connect(self._add_document)
        content_layout.addWidget(add_btn)

        self._content.hide()
        root.addWidget(self._content)

        self._update_badge()

    # ── Public API ────────────────────────────────────────────────────

    def set_project_dir(self, project_dir):
        """Load project notes and reference docs from project directory."""
        self._project_dir = project_dir
        if not project_dir:
            self._notes_edit.setPlainText("")
            self._clear_file_list()
            self._update_badge()
            return

        project_dir = Path(project_dir)

        # Ensure reference_docs/ exists
        ref_dir = project_dir / "reference_docs"
        ref_dir.mkdir(parents=True, exist_ok=True)

        # Load project.md
        project_md = project_dir / "project.md"
        if project_md.exists():
            try:
                text = project_md.read_text(encoding="utf-8")
                self._notes_edit.blockSignals(True)
                self._notes_edit.setPlainText(text)
                self._notes_edit.blockSignals(False)
            except Exception:
                pass
        else:
            self._notes_edit.blockSignals(True)
            self._notes_edit.setPlainText("")
            self._notes_edit.blockSignals(False)

        self._refresh_file_list()
        self._update_badge()

    def get_notes_text(self):
        """Get current project notes text."""
        return self._notes_edit.toPlainText()

    def get_reference_docs(self):
        """Get list of reference document paths."""
        if not self._project_dir:
            return []
        ref_dir = Path(self._project_dir) / "reference_docs"
        if not ref_dir.exists():
            return []
        return sorted(
            f for f in ref_dir.iterdir()
            if f.is_file() and not f.name.startswith(".")
        )

    # ── Collapse / Expand ─────────────────────────────────────────────

    def _toggle_collapsed(self):
        self._collapsed = not self._collapsed
        self._content.setVisible(not self._collapsed)
        self._arrow.setText("\u25bc" if not self._collapsed else "\u25b6")  # ▼ / ▶
        self._update_badge()

    # ── Notes Management ──────────────────────────────────────────────

    def _on_notes_changed(self):
        """Debounced save on text change."""
        self._save_timer.start()
        self._update_badge()

    def _save_notes(self):
        """Write notes text to project.md."""
        if not self._project_dir:
            return
        project_md = Path(self._project_dir) / "project.md"
        try:
            project_md.write_text(
                self._notes_edit.toPlainText(), encoding="utf-8"
            )
            self.contextChanged.emit()
        except Exception:
            pass

    # ── File List Management ──────────────────────────────────────────

    def _clear_file_list(self):
        """Remove all file row widgets from the file list."""
        while self._file_list.count() > 0:
            item = self._file_list.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        # Re-add placeholder
        self._no_docs_label = QtWidgets.QLabel("No reference documents added")
        self._no_docs_label.setStyleSheet(f"""
            color: {Theme.COLORS['text_muted']};
            font-size: {Theme.FONTS['size_xs']};
            background: transparent;
            padding: 4px 0;
        """)
        self._file_list.addWidget(self._no_docs_label)

    def _refresh_file_list(self):
        """Rescan reference_docs/ and rebuild file list UI."""
        self._clear_file_list()
        docs = self.get_reference_docs()

        if docs:
            self._no_docs_label.hide()
        else:
            self._no_docs_label.show()

        for doc_path in docs:
            row = self._make_file_row(doc_path)
            self._file_list.addWidget(row)

        self._update_badge()

    def _make_file_row(self, file_path):
        """Create a row widget for a reference document."""
        row = QtWidgets.QWidget()
        row.setStyleSheet("background: transparent;")
        row_layout = QtWidgets.QHBoxLayout(row)
        row_layout.setContentsMargins(0, 2, 0, 2)
        row_layout.setSpacing(8)

        # File name + size
        size_kb = file_path.stat().st_size / 1024
        if size_kb > 1024:
            size_str = f"{size_kb / 1024:.1f} MB"
        else:
            size_str = f"{size_kb:.0f} KB"

        label = QtWidgets.QLabel(f"{file_path.name}  ({size_str})")
        label.setStyleSheet(f"""
            color: {Theme.COLORS['text_primary']};
            font-size: {Theme.FONTS['size_xs']};
            background: transparent;
        """)
        row_layout.addWidget(label, stretch=1)

        # Remove button
        remove_btn = QtWidgets.QPushButton("\u00d7")  # ×
        remove_btn.setFixedSize(20, 20)
        remove_btn.setCursor(QtCore.Qt.PointingHandCursor)
        remove_btn.setToolTip("Remove document")
        remove_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.COLORS['text_muted']};
                border: none;
                font-size: {Theme.FONTS['size_sm']};
                border-radius: {Theme.RADIUS['xs']};
            }}
            QPushButton:hover {{
                color: {Theme.COLORS['error']};
                background-color: {Theme.COLORS['bg_hover']};
            }}
        """)
        remove_btn.clicked.connect(lambda checked=False, p=file_path: self._remove_document(p))
        row_layout.addWidget(remove_btn)

        return row

    def _add_document(self):
        """Open file dialog and copy selected file to reference_docs/."""
        if not self._project_dir:
            return

        file_paths, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            "Add Reference Documents",
            "",
            "Documents (*.pdf *.png *.jpg *.jpeg *.svg *.dxf *.dwg);;All Files (*)",
        )
        if not file_paths:
            return

        ref_dir = Path(self._project_dir) / "reference_docs"
        ref_dir.mkdir(parents=True, exist_ok=True)

        for src in file_paths:
            src_path = Path(src)
            dest = ref_dir / src_path.name
            # Avoid overwriting — append number if exists
            if dest.exists():
                stem = src_path.stem
                suffix = src_path.suffix
                counter = 1
                while dest.exists():
                    dest = ref_dir / f"{stem}_{counter}{suffix}"
                    counter += 1
            shutil.copy2(str(src_path), str(dest))

        self._refresh_file_list()
        self.contextChanged.emit()

    def _remove_document(self, file_path):
        """Delete a reference document."""
        try:
            file_path.unlink()
        except Exception:
            pass
        self._refresh_file_list()
        self.contextChanged.emit()

    # ── Badge ─────────────────────────────────────────────────────────

    def _update_badge(self):
        """Update the collapsed-state summary badge."""
        parts = []
        notes = self._notes_edit.toPlainText().strip()
        if notes:
            line_count = len([l for l in notes.splitlines() if l.strip()])
            parts.append(f"{line_count} line{'s' if line_count != 1 else ''}")
        docs = self.get_reference_docs()
        if docs:
            parts.append(f"{len(docs)} doc{'s' if len(docs) != 1 else ''}")

        if parts:
            self._badge.setText(f"({', '.join(parts)})")
        else:
            self._badge.setText("")
