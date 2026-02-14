# SPDX-License-Identifier: LGPL-2.1-or-later
"""
AIAssistant - Natural language CAD modeling assistant for FreeCAD.

This module provides an AI-powered chat interface that converts natural
language descriptions into FreeCAD Python code.

Usage:
    import AIAssistant
    AIAssistant.show()

    Or press Ctrl+Shift+A
"""

__version__ = "0.1.0"

_panel = None
_chooser = None


def _get_last_mode():
    """Get last used assistant mode from FreeCAD parameters."""
    try:
        import FreeCAD
        grp = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/AIAssistant")
        return grp.GetString("LastMode", "") or None
    except Exception:
        return None


def _save_last_mode(mode):
    """Save last used assistant mode to FreeCAD parameters."""
    try:
        import FreeCAD
        grp = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/AIAssistant")
        grp.SetString("LastMode", mode)
    except Exception:
        pass


def show_chooser():
    """Show the mode chooser (first time) or restore last used mode."""
    global _chooser

    last = _get_last_mode()
    if last == "3d":
        show()
    else:
        # Default to drawing mode
        import DrawingAssistant
        DrawingAssistant.show()


def _on_chooser_mode(mode):
    """Handle mode selection from chooser."""
    global _chooser
    _save_last_mode(mode)
    if _chooser:
        _chooser.hide()
        _chooser.deleteLater()
        _chooser = None
    if mode == "3d":
        show()
    else:
        import DrawingAssistant
        DrawingAssistant.show()


def show():
    """Show the 3D Assistant panel (hides Drawing Assistant if visible)."""
    global _panel
    import FreeCAD
    import FreeCADGui
    from PySide6 import QtCore, QtWidgets
    from . import AIPanel

    mw = FreeCADGui.getMainWindow()
    if mw is None:
        FreeCAD.Console.PrintWarning("AIAssistant: No main window\n")
        return None

    # Hide Drawing Assistant if present (mutual exclusivity)
    drawing_panel = mw.findChild(QtWidgets.QDockWidget, "DrawingAssistantDockWidget")
    if drawing_panel and drawing_panel.isVisible():
        drawing_panel.hide()

    # Hide chooser if present
    chooser = mw.findChild(QtWidgets.QDockWidget, "AssistantChooserDockWidget")
    if chooser and chooser.isVisible():
        chooser.hide()

    if _panel is None:
        _panel = AIPanel.AIAssistantDockWidget()
        _panel.setObjectName("AIAssistantDockWidget")
        mw.addDockWidget(QtCore.Qt.RightDockWidgetArea, _panel)

    _save_last_mode("3d")
    _panel.show()
    _panel.raise_()
    return _panel


def hide():
    """Hide the 3D Assistant panel."""
    global _panel
    if _panel:
        _panel.hide()


def toggle():
    """Toggle the 3D Assistant panel."""
    global _panel
    if _panel is None:
        show()
    elif _panel.isVisible():
        _panel.hide()
    else:
        _panel.show()
        _panel.raise_()
