# SPDX-License-Identifier: LGPL-2.1-or-later
"""Segmented control for switching between 3D and Drawing assistant modes."""

from PySide6 import QtWidgets, QtCore


class ModeSegmentedControl(QtWidgets.QWidget):
    """Pill-shaped segmented control: [ 3D | Drawing ]."""

    modeChanged = QtCore.Signal(str)  # "3d" or "drawing"

    def __init__(self, active_mode: str = "3d", theme_module=None, parent=None):
        super().__init__(parent)
        self._active = active_mode
        self._theme = theme_module
        self._setup_ui()

    def _setup_ui(self):
        T = self._theme
        self.setFixedHeight(28)
        self.setStyleSheet(f"""
            ModeSegmentedControl {{
                background-color: {T.COLORS['bg_tertiary']};
                border: 1px solid {T.COLORS['border_subtle']};
                border-radius: 14px;
            }}
        """)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)

        self._btn_3d = self._make_button("3D", "3d")
        self._btn_drawing = self._make_button("Drawing", "drawing")
        layout.addWidget(self._btn_3d)
        layout.addWidget(self._btn_drawing)
        self._update_styles()

    def _make_button(self, text, mode):
        btn = QtWidgets.QPushButton(text)
        btn.setCursor(QtCore.Qt.PointingHandCursor)
        btn.setFixedHeight(24)
        btn.clicked.connect(lambda: self._on_clicked(mode))
        return btn

    def _on_clicked(self, mode):
        if mode != self._active:
            self._active = mode
            self._update_styles()
            self.modeChanged.emit(mode)

    def _update_styles(self):
        T = self._theme
        active_style = f"""
            QPushButton {{
                background-color: {T.COLORS['accent_primary']};
                color: #ffffff;
                border: none;
                border-radius: 12px;
                font-size: {T.FONTS['size_sm']};
                font-weight: {T.FONTS['weight_medium']};
                padding: 2px 14px;
            }}
        """
        inactive_style = f"""
            QPushButton {{
                background-color: transparent;
                color: {T.COLORS['text_secondary']};
                border: none;
                border-radius: 12px;
                font-size: {T.FONTS['size_sm']};
                font-weight: {T.FONTS['weight_medium']};
                padding: 2px 14px;
            }}
            QPushButton:hover {{
                color: {T.COLORS['text_primary']};
                background-color: {T.COLORS['bg_hover']};
            }}
        """
        self._btn_3d.setStyleSheet(
            active_style if self._active == "3d" else inactive_style
        )
        self._btn_drawing.setStyleSheet(
            active_style if self._active == "drawing" else inactive_style
        )

    def refresh_theme(self):
        """Re-apply styles after a theme change."""
        T = self._theme
        self.setStyleSheet(f"""
            ModeSegmentedControl {{
                background-color: {T.COLORS['bg_tertiary']};
                border: 1px solid {T.COLORS['border_subtle']};
                border-radius: 14px;
            }}
        """)
        self._update_styles()

    def set_active(self, mode: str):
        """Set active mode without emitting signal."""
        self._active = mode
        self._update_styles()
