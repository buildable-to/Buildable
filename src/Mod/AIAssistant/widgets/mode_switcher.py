# SPDX-License-Identifier: LGPL-2.1-or-later
"""Segmented control for switching between assistant modes."""

from PySide6 import QtWidgets, QtCore


class ModeSegmentedControl(QtWidgets.QWidget):
    """Pill-shaped segmented control: [ 3D | Drawing | ... ]."""

    modeChanged = QtCore.Signal(str)

    # Default modes when none provided (backwards compatible)
    _DEFAULT_MODES = [
        {"label": "3D BETA", "value": "3d"},
        {"label": "Drawing", "value": "drawing"},
    ]

    def __init__(self, active_mode: str = "3d", theme_module=None,
                 modes=None, parent=None):
        super().__init__(parent)
        self._active = active_mode
        self._theme = theme_module
        self._modes = modes or self._DEFAULT_MODES
        self._buttons = {}
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

        for mode_def in self._modes:
            btn = self._make_button(mode_def["label"], mode_def["value"])
            self._buttons[mode_def["value"]] = btn
            layout.addWidget(btn)

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
        for value, btn in self._buttons.items():
            btn.setStyleSheet(active_style if value == self._active else inactive_style)

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
