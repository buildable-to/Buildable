# SPDX-License-Identifier: LGPL-2.1-or-later
"""
Context Selection Widget - UI for selecting which objects to include in LLM context.
Provides All/Selected/Custom modes with collapsible object list.
"""

import FreeCAD
import FreeCADGui
from PySide6 import QtCore, QtWidgets, QtGui
from typing import List, Optional, Set
from .. import Theme


class ContextMode:
    """Context selection modes."""
    ALL = "all"
    SELECTED = "selected"
    CUSTOM = "custom"


class ContextSelectionWidget(QtWidgets.QFrame):
    """Widget for selecting objects to include in LLM context.

    Provides three modes:
    - All objects: Include entire document context
    - Selected: Include only FreeCAD selection
    - Custom: Manual selection via checkboxes

    Signals:
        selectionChanged: Emitted when context selection changes
    """

    selectionChanged = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mode = ContextMode.ALL
        self._custom_objects: Set[str] = set()  # Object names for custom mode
        self._expanded = False
        self._setup_ui()

        # Connect to FreeCAD selection observer
        self._setup_selection_observer()

    def _setup_ui(self):
        """Set up the widget UI."""
        self.setObjectName("ContextSelectionWidget")
        self.setStyleSheet(f"""
            #ContextSelectionWidget {{
                background-color: transparent;
                border: none;
            }}
        """)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(8)

        layout.addStretch()

        # Show review feedback toggle (for self-review descriptions)
        self._show_review_cb = QtWidgets.QCheckBox("Review")
        self._show_review_cb.setChecked(True)  # ON by default - agentic self-review catches visual issues
        self._show_review_cb.setToolTip("AI reviews screenshots before showing preview (catches visual bugs)")
        self._show_review_cb.setStyleSheet(f"""
            QCheckBox {{
                color: {Theme.COLORS['text_muted']};
                font-size: {Theme.FONTS['size_xs']};
                background: transparent;
                spacing: 4px;
            }}
            QCheckBox::indicator {{
                width: 12px;
                height: 12px;
                border-radius: 2px;
                border: 1px solid {Theme.COLORS['border_default']};
                background: {Theme.COLORS['bg_secondary']};
            }}
            QCheckBox::indicator:checked {{
                background: {Theme.COLORS['accent_primary']};
                border-color: {Theme.COLORS['accent_primary']};
            }}
        """)
        layout.addWidget(self._show_review_cb)

        # Keep these for API compatibility but don't use them
        self._mode = ContextMode.ALL
        self._custom_objects: Set[str] = set()
        self._expanded = False

    def _setup_selection_observer(self):
        """Set up FreeCAD selection observer."""
        pass

    def get_context_objects(self) -> Optional[List[str]]:
        """Get list of object names to include in context.

        Returns:
            None for 'All' mode (include everything)
        """
        return None  # Always include all

    def get_mode(self) -> str:
        """Get current context mode."""
        return ContextMode.ALL

    def set_mode(self, mode: str):
        """Set context mode programmatically."""
        pass

    def refresh(self):
        """Refresh the widget."""
        pass

    def show_review_feedback(self) -> bool:
        """Check if review feedback should be shown in previews."""
        return self._show_review_cb.isChecked()
