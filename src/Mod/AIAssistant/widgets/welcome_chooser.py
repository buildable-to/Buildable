# SPDX-License-Identifier: LGPL-2.1-or-later
"""Welcome chooser — shown on first document open to pick 3D or Drawing mode."""

from PySide6 import QtWidgets, QtCore


class AssistantChooserDockWidget(QtWidgets.QDockWidget):
    """Welcome screen with two mode cards: 3D Modeling / 2D Drawing."""

    modeChosen = QtCore.Signal(str)  # "3d" or "drawing"

    def __init__(self, theme_module=None, parent=None):
        super().__init__("Assistant", parent)
        self.setObjectName("AssistantChooserDockWidget")
        self.setAllowedAreas(
            QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea
        )
        self._theme = theme_module
        self._setup_ui()

    def _setup_ui(self):
        T = self._theme
        main = QtWidgets.QWidget()
        main.setStyleSheet(f"background-color: {T.COLORS['bg_primary']};")
        layout = QtWidgets.QVBoxLayout(main)
        layout.setContentsMargins(24, 40, 24, 24)
        layout.setSpacing(16)

        # Header
        header = QtWidgets.QLabel("Choose your mode")
        header.setAlignment(QtCore.Qt.AlignCenter)
        header.setStyleSheet(f"""
            QLabel {{
                color: {T.COLORS['text_primary']};
                font-size: {T.FONTS['size_lg']};
                font-weight: {T.FONTS['weight_semibold']};
                background: transparent;
            }}
        """)
        layout.addWidget(header)

        subtitle = QtWidgets.QLabel("You can switch anytime from the header")
        subtitle.setAlignment(QtCore.Qt.AlignCenter)
        subtitle.setStyleSheet(f"""
            QLabel {{
                color: {T.COLORS['text_muted']};
                font-size: {T.FONTS['size_sm']};
                background: transparent;
            }}
        """)
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        # 3D card
        card_3d = self._make_card(
            "3D Modeling",
            "Design and modify 3D parametric\nmodels using natural language",
            "Ctrl+Shift+A",
            "3d",
        )
        layout.addWidget(card_3d)

        # Drawing card
        card_drawing = self._make_card(
            "2D Drawing",
            "Create structural shop drawings\nwith Draft + TechDraw",
            "Ctrl+Shift+D",
            "drawing",
        )
        layout.addWidget(card_drawing)

        layout.addStretch()

        self.setWidget(main)
        self.setMinimumWidth(380)

    def _make_card(self, title, description, shortcut, mode):
        T = self._theme
        btn = QtWidgets.QPushButton()
        btn.setCursor(QtCore.Qt.PointingHandCursor)
        btn.setMinimumHeight(100)
        btn.clicked.connect(lambda: self.modeChosen.emit(mode))

        btn_layout = QtWidgets.QVBoxLayout(btn)
        btn_layout.setContentsMargins(16, 14, 16, 14)
        btn_layout.setSpacing(6)

        title_label = QtWidgets.QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {T.COLORS['text_primary']};
                font-size: {T.FONTS['size_base']};
                font-weight: {T.FONTS['weight_semibold']};
                background: transparent;
            }}
        """)
        btn_layout.addWidget(title_label)

        desc_label = QtWidgets.QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"""
            QLabel {{
                color: {T.COLORS['text_secondary']};
                font-size: {T.FONTS['size_sm']};
                background: transparent;
            }}
        """)
        btn_layout.addWidget(desc_label)

        shortcut_label = QtWidgets.QLabel(shortcut)
        shortcut_label.setStyleSheet(f"""
            QLabel {{
                color: {T.COLORS['text_muted']};
                font-size: {T.FONTS['size_xs']};
                background: transparent;
            }}
        """)
        btn_layout.addWidget(shortcut_label)

        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {T.COLORS['bg_secondary']};
                border: 1px solid {T.COLORS['border_default']};
                border-radius: {T.RADIUS['md']};
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {T.COLORS['bg_hover']};
                border-color: {T.COLORS['border_hover']};
            }}
        """)

        return btn
