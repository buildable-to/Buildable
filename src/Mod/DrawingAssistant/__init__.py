# SPDX-License-Identifier: LGPL-2.1-or-later
"""
DrawingAssistant - AI-powered 2D structural drawing assistant for FreeCAD.

This module provides an AI chat interface specialized for producing
2D structural shop drawings using Draft, TechDraw, and Spreadsheet workbenches.

Usage:
    import DrawingAssistant
    DrawingAssistant.show()

    Or press Ctrl+Shift+D
"""

__version__ = "0.1.0"

_panel = None


def show():
    """Show the Drawing Assistant panel (hides AI Assistant if visible)."""
    global _panel
    import FreeCAD
    import FreeCADGui
    from PySide6 import QtCore, QtWidgets
    from . import DrawingPanel

    mw = FreeCADGui.getMainWindow()
    if mw is None:
        FreeCAD.Console.PrintWarning("DrawingAssistant: No main window\n")
        return None

    # Hide AI Assistant if present (mutual exclusivity)
    ai_panel = mw.findChild(QtWidgets.QDockWidget, "AIAssistantDockWidget")
    if ai_panel and ai_panel.isVisible():
        ai_panel.hide()

    # Hide chooser if present
    chooser = mw.findChild(QtWidgets.QDockWidget, "AssistantChooserDockWidget")
    if chooser and chooser.isVisible():
        chooser.hide()

    if _panel is None:
        _panel = DrawingPanel.DrawingAssistantDockWidget()
        _panel.setObjectName("DrawingAssistantDockWidget")
        mw.addDockWidget(QtCore.Qt.RightDockWidgetArea, _panel)

    # Save mode preference
    try:
        FreeCAD.ParamGet("User parameter:BaseApp/Preferences/AIAssistant").SetString("LastMode", "drawing")
    except Exception:
        pass

    _panel.show()
    _panel.raise_()
    return _panel


def hide():
    """Hide the Drawing Assistant panel."""
    global _panel
    if _panel:
        _panel.hide()


def toggle():
    """Toggle the Drawing Assistant panel."""
    global _panel
    if _panel is None:
        show()
    elif _panel.isVisible():
        _panel.hide()
    else:
        show()
