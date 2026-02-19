# SPDX-License-Identifier: LGPL-2.1-or-later
"""
Project Context Widget - Full-panel view for project notes and reference documents.
Shown when the user selects the "Context" tab in the mode switcher.
"""

import shutil
from pathlib import Path

from PySide6 import QtCore, QtWidgets
from .. import Theme


class _FileChip(QtWidgets.QFrame):
    """Compact chip showing a reference document with remove button."""

    removeClicked = QtCore.Signal(Path)

    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self._path = file_path
        self.setObjectName("FileChip")
        self.setStyleSheet(f"""
            #FileChip {{
                background-color: {Theme.COLORS['bg_tertiary']};
                border: 1px solid {Theme.COLORS['border_subtle']};
                border-radius: {Theme.RADIUS['sm']};
            }}
            #FileChip:hover {{
                border-color: {Theme.COLORS['border_default']};
            }}
        """)

        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(10, 5, 6, 5)
        lay.setSpacing(6)

        size_kb = file_path.stat().st_size / 1024
        size_str = f"{size_kb / 1024:.1f} MB" if size_kb > 1024 else f"{size_kb:.0f} KB"

        name = QtWidgets.QLabel(file_path.name)
        name.setStyleSheet(f"""
            color: {Theme.COLORS['text_primary']};
            font-size: {Theme.FONTS['size_sm']};
            background: transparent;
        """)
        lay.addWidget(name)

        size_lbl = QtWidgets.QLabel(size_str)
        size_lbl.setStyleSheet(f"""
            color: {Theme.COLORS['text_muted']};
            font-size: {Theme.FONTS['size_xs']};
            background: transparent;
        """)
        lay.addWidget(size_lbl)

        x_btn = QtWidgets.QPushButton("\u00d7")
        x_btn.setFixedSize(18, 18)
        x_btn.setCursor(QtCore.Qt.PointingHandCursor)
        x_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.COLORS['text_muted']};
                border: none;
                font-size: 13px;
                padding: 0;
            }}
            QPushButton:hover {{
                color: {Theme.COLORS['accent_error']};
            }}
        """)
        x_btn.clicked.connect(lambda: self.removeClicked.emit(self._path))
        lay.addWidget(x_btn)


class ProjectContextWidget(QtWidgets.QWidget):
    """Full-panel view for editing project notes and managing reference documents.

    Replaces the chat view when the user selects the "Context" tab.

    Signals:
        contextChanged: Emitted when notes or file list changes.
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

        # ── Section: Reference Documents ──────────────────────────────
        docs_header_row = QtWidgets.QHBoxLayout()
        docs_header_row.setSpacing(8)

        docs_header = QtWidgets.QLabel("Reference documents")
        docs_header.setStyleSheet(f"""
            color: {Theme.COLORS['text_secondary']};
            font-size: {Theme.FONTS['size_xs']};
            font-weight: {Theme.FONTS['weight_semibold']};
            text-transform: uppercase;
            letter-spacing: 0.5px;
            background: transparent;
        """)
        docs_header_row.addWidget(docs_header)
        docs_header_row.addStretch()

        add_btn = QtWidgets.QPushButton("+ Add")
        add_btn.setCursor(QtCore.Qt.PointingHandCursor)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.COLORS['accent_primary']};
                border: none;
                font-size: {Theme.FONTS['size_xs']};
                font-weight: {Theme.FONTS['weight_medium']};
                padding: 2px 8px;
            }}
            QPushButton:hover {{
                text-decoration: underline;
            }}
        """)
        add_btn.clicked.connect(self._add_document)
        docs_header_row.addWidget(add_btn)

        root.addLayout(docs_header_row)

        # File chips area (scrollable)
        self._docs_scroll = QtWidgets.QScrollArea()
        self._docs_scroll.setWidgetResizable(True)
        self._docs_scroll.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: 1px solid {Theme.COLORS['border_subtle']};
                border-radius: {Theme.RADIUS['md']};
            }}
        """)
        self._docs_scroll.setMinimumHeight(80)
        self._docs_scroll.setMaximumHeight(200)

        self._docs_container = QtWidgets.QWidget()
        self._docs_container.setStyleSheet(
            f"background-color: {Theme.COLORS['bg_secondary']};"
        )
        self._docs_layout = _FlowLayout(
            self._docs_container, h_spacing=8, v_spacing=8
        )
        self._docs_layout.setContentsMargins(12, 12, 12, 12)
        self._docs_scroll.setWidget(self._docs_container)

        root.addWidget(self._docs_scroll)

        # Empty state label (shown when no docs)
        self._empty_label = QtWidgets.QLabel(
            "Drop PDFs, drawings, or specifications here"
        )
        self._empty_label.setAlignment(QtCore.Qt.AlignCenter)
        self._empty_label.setStyleSheet(f"""
            color: {Theme.COLORS['text_muted']};
            font-size: {Theme.FONTS['size_xs']};
            background: transparent;
            padding: 20px;
        """)

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
        """Load project notes and reference docs from project directory."""
        self._project_dir = project_dir
        if not project_dir:
            self._notes_edit.blockSignals(True)
            self._notes_edit.setPlainText("")
            self._notes_edit.blockSignals(False)
            self._refresh_file_list()
            return

        project_dir = Path(project_dir)
        (project_dir / "reference_docs").mkdir(parents=True, exist_ok=True)

        project_md = project_dir / "project.md"
        self._notes_edit.blockSignals(True)
        if project_md.exists():
            try:
                self._notes_edit.setPlainText(
                    project_md.read_text(encoding="utf-8")
                )
            except Exception:
                self._notes_edit.setPlainText("")
        else:
            self._notes_edit.setPlainText("")
        self._notes_edit.blockSignals(False)

        self._refresh_file_list()

    def get_notes_text(self):
        return self._notes_edit.toPlainText()

    def get_reference_docs(self):
        if not self._project_dir:
            return []
        ref_dir = Path(self._project_dir) / "reference_docs"
        if not ref_dir.exists():
            return []
        return sorted(
            f for f in ref_dir.iterdir()
            if f.is_file() and not f.name.startswith(".")
        )

    # ── Notes ─────────────────────────────────────────────────────────

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
        except Exception:
            pass

    # ── File Management ───────────────────────────────────────────────

    def _refresh_file_list(self):
        # Clear existing chips
        while self._docs_layout.count() > 0:
            item = self._docs_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        docs = self.get_reference_docs()

        if not docs:
            self._docs_layout.addWidget(self._empty_label)
            self._empty_label.show()
        else:
            self._empty_label.hide()
            self._empty_label.setParent(None)
            for doc_path in docs:
                chip = _FileChip(doc_path)
                chip.removeClicked.connect(self._remove_document)
                self._docs_layout.addWidget(chip)

    def _add_document(self):
        if not self._project_dir:
            return
        paths, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self, "Add Reference Documents", "",
            "Documents (*.pdf *.png *.jpg *.jpeg *.svg *.dxf *.dwg);;All Files (*)",
        )
        if not paths:
            return

        ref_dir = Path(self._project_dir) / "reference_docs"
        ref_dir.mkdir(parents=True, exist_ok=True)
        for src in paths:
            src_path = Path(src)
            dest = ref_dir / src_path.name
            if dest.exists():
                stem, suffix = src_path.stem, src_path.suffix
                c = 1
                while dest.exists():
                    dest = ref_dir / f"{stem}_{c}{suffix}"
                    c += 1
            shutil.copy2(str(src_path), str(dest))

        self._refresh_file_list()
        self.contextChanged.emit()

    def _remove_document(self, file_path):
        try:
            file_path.unlink()
        except Exception:
            pass
        self._refresh_file_list()
        self.contextChanged.emit()


# ─── Flow Layout ─────────────────────────────────────────────────────

class _FlowLayout(QtWidgets.QLayout):
    """Wraps widgets horizontally — overflow flows to the next line."""

    def __init__(self, parent=None, h_spacing=6, v_spacing=4):
        super().__init__(parent)
        self._h = h_spacing
        self._v = v_spacing
        self._items = []

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        return self._items[index] if 0 <= index < len(self._items) else None

    def takeAt(self, index):
        return self._items.pop(index) if 0 <= index < len(self._items) else None

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._lay(QtCore.QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._lay(rect)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        s = QtCore.QSize()
        for it in self._items:
            s = s.expandedTo(it.minimumSize())
        m = self.contentsMargins()
        return s + QtCore.QSize(m.left() + m.right(), m.top() + m.bottom())

    def _lay(self, rect, test=False):
        m = self.contentsMargins()
        r = rect.adjusted(m.left(), m.top(), -m.right(), -m.bottom())
        x, y, lh = r.x(), r.y(), 0
        for it in self._items:
            w = it.widget()
            if w and not w.isVisible():
                continue
            sz = it.sizeHint()
            nx = x + sz.width() + self._h
            if nx - self._h > r.right() and lh > 0:
                x, y = r.x(), y + lh + self._v
                nx = x + sz.width() + self._h
                lh = 0
            if not test:
                it.setGeometry(QtCore.QRect(QtCore.QPoint(x, y), sz))
            x = nx
            lh = max(lh, sz.height())
        return y + lh - rect.y() + m.bottom()
