# SPDX-License-Identifier: LGPL-2.1-or-later
"""
Project Context Widget - Collapsible panel for engineer's project notes and reference documents.
Provides persistent project knowledge (materials, naming, rules) and PDF reference management.
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
        lay.setContentsMargins(8, 3, 4, 3)
        lay.setSpacing(4)

        size_kb = file_path.stat().st_size / 1024
        size_str = f"{size_kb / 1024:.1f} MB" if size_kb > 1024 else f"{size_kb:.0f} KB"

        name = QtWidgets.QLabel(file_path.name)
        name.setStyleSheet(f"""
            color: {Theme.COLORS['text_primary']};
            font-size: {Theme.FONTS['size_xs']};
            background: transparent;
        """)
        lay.addWidget(name)

        size = QtWidgets.QLabel(size_str)
        size.setStyleSheet(f"""
            color: {Theme.COLORS['text_muted']};
            font-size: 10px;
            background: transparent;
        """)
        lay.addWidget(size)

        x_btn = QtWidgets.QPushButton("\u00d7")
        x_btn.setFixedSize(16, 16)
        x_btn.setCursor(QtCore.Qt.PointingHandCursor)
        x_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.COLORS['text_muted']};
                border: none;
                font-size: 12px;
                padding: 0;
            }}
            QPushButton:hover {{
                color: {Theme.COLORS['accent_error']};
            }}
        """)
        x_btn.clicked.connect(lambda: self.removeClicked.emit(self._path))
        lay.addWidget(x_btn)


class ProjectContextWidget(QtWidgets.QFrame):
    """Collapsible panel showing project notes (text) and reference documents (files).

    Sits between the header and chat area. Collapsed by default, showing a
    one-line summary. Expanded shows a compact text editor and file chips.

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
        self.setStyleSheet("""
            #ProjectContextWidget { background: transparent; border: none; }
        """)

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(12, 0, 12, 0)
        root.setSpacing(0)

        # ── Header bar (always visible) ──────────────────────────────
        self._header = QtWidgets.QFrame()
        self._header.setObjectName("PCHeader")
        self._header.setCursor(QtCore.Qt.PointingHandCursor)
        self._header.setStyleSheet(f"""
            #PCHeader {{
                background: transparent;
                border-bottom: 1px solid {Theme.COLORS['border_subtle']};
            }}
        """)
        h_lay = QtWidgets.QHBoxLayout(self._header)
        h_lay.setContentsMargins(2, 6, 2, 6)
        h_lay.setSpacing(6)

        self._arrow = QtWidgets.QLabel("\u25b8")  # ▸
        self._arrow.setStyleSheet(f"""
            color: {Theme.COLORS['text_muted']};
            font-size: 10px;
            background: transparent;
        """)
        h_lay.addWidget(self._arrow)

        title = QtWidgets.QLabel("Project Context")
        title.setStyleSheet(f"""
            color: {Theme.COLORS['text_muted']};
            font-size: {Theme.FONTS['size_xs']};
            background: transparent;
        """)
        h_lay.addWidget(title)

        self._badge = QtWidgets.QLabel("")
        self._badge.setStyleSheet(f"""
            color: {Theme.COLORS['text_muted']};
            font-size: 10px;
            background: transparent;
        """)
        h_lay.addWidget(self._badge)

        h_lay.addStretch()

        self._header.mousePressEvent = lambda _: self._toggle_collapsed()
        root.addWidget(self._header)

        # ── Content area (hidden when collapsed) ─────────────────────
        self._content = QtWidgets.QWidget()
        self._content.setStyleSheet("background: transparent;")
        c_lay = QtWidgets.QVBoxLayout(self._content)
        c_lay.setContentsMargins(0, 8, 0, 8)
        c_lay.setSpacing(6)

        # Text area — compact, placeholder is the label
        self._notes_edit = QtWidgets.QPlainTextEdit()
        self._notes_edit.setPlaceholderText(
            "Materials, naming conventions, drawing preferences, title block\u2026"
        )
        self._notes_edit.setFixedHeight(64)
        self._notes_edit.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {Theme.COLORS['bg_secondary']};
                color: {Theme.COLORS['text_primary']};
                border: 1px solid {Theme.COLORS['border_subtle']};
                border-radius: {Theme.RADIUS['sm']};
                padding: 6px 8px;
                font-size: {Theme.FONTS['size_xs']};
                font-family: {Theme.FONTS['family_sans']};
            }}
            QPlainTextEdit:focus {{
                border-color: {Theme.COLORS['accent_primary']};
            }}
        """)
        self._notes_edit.textChanged.connect(self._on_notes_changed)
        c_lay.addWidget(self._notes_edit)

        # Documents: flow layout with chips + add button inline
        self._docs_row = QtWidgets.QWidget()
        self._docs_row.setStyleSheet("background: transparent;")
        self._docs_flow = _FlowLayout(self._docs_row, h_spacing=6, v_spacing=4)
        self._docs_flow.setContentsMargins(0, 0, 0, 0)
        c_lay.addWidget(self._docs_row)

        # "Add docs" — small inline button, always last in flow
        self._add_btn = QtWidgets.QPushButton("+ Add docs")
        self._add_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self._add_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.COLORS['text_muted']};
                border: 1px dashed {Theme.COLORS['border_default']};
                border-radius: {Theme.RADIUS['sm']};
                padding: 3px 10px;
                font-size: 10px;
            }}
            QPushButton:hover {{
                color: {Theme.COLORS['accent_primary']};
                border-color: {Theme.COLORS['accent_primary']};
            }}
        """)
        self._add_btn.clicked.connect(self._add_document)
        self._docs_flow.addWidget(self._add_btn)

        self._content.hide()
        root.addWidget(self._content)

        self._update_badge()

    # ── Public API ────────────────────────────────────────────────────

    def set_project_dir(self, project_dir):
        """Load project notes and reference docs from project directory."""
        self._project_dir = project_dir
        if not project_dir:
            self._notes_edit.blockSignals(True)
            self._notes_edit.setPlainText("")
            self._notes_edit.blockSignals(False)
            self._refresh_file_list()
            self._update_badge()
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
        self._update_badge()

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

    # ── Collapse / Expand ─────────────────────────────────────────────

    def _toggle_collapsed(self):
        self._collapsed = not self._collapsed
        self._content.setVisible(not self._collapsed)
        self._arrow.setText("\u25be" if not self._collapsed else "\u25b8")  # ▾ / ▸

    # ── Notes Management ──────────────────────────────────────────────

    def _on_notes_changed(self):
        self._save_timer.start()
        self._update_badge()

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

    # ── File List Management ──────────────────────────────────────────

    def _refresh_file_list(self):
        # Remove all except the add button
        while self._docs_flow.count() > 0:
            item = self._docs_flow.takeAt(0)
            w = item.widget()
            if w and w is not self._add_btn:
                w.deleteLater()

        for doc_path in self.get_reference_docs():
            chip = _FileChip(doc_path)
            chip.removeClicked.connect(self._remove_document)
            self._docs_flow.insertWidget(self._docs_flow.count(), chip)

        # Add button always last
        self._docs_flow.addWidget(self._add_btn)
        self._update_badge()

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

    # ── Badge ─────────────────────────────────────────────────────────

    def _update_badge(self):
        parts = []
        notes = self._notes_edit.toPlainText().strip()
        if notes:
            n = len([ln for ln in notes.splitlines() if ln.strip()])
            parts.append(f"{n} note{'s' if n != 1 else ''}")
        docs = self.get_reference_docs()
        if docs:
            parts.append(f"{len(docs)} doc{'s' if len(docs) != 1 else ''}")
        self._badge.setText(f"\u00b7 {', '.join(parts)}" if parts else "")


# ─── Flow Layout ─────────────────────────────────────────────────────
# Wraps widgets like text — items that overflow the row flow to the next line.

class _FlowLayout(QtWidgets.QLayout):

    def __init__(self, parent=None, h_spacing=6, v_spacing=4):
        super().__init__(parent)
        self._h = h_spacing
        self._v = v_spacing
        self._items = []

    def addItem(self, item):
        self._items.append(item)

    def insertWidget(self, index, widget):
        self.addChildWidget(widget)
        self._items.insert(index, QtWidgets.QWidgetItem(widget))
        self.invalidate()

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
