# SPDX-License-Identifier: LGPL-2.1-or-later
"""DrawingAssistant GUI initialization."""

# Note: FreeCAD and FreeCADGui are pre-loaded by FreeCAD before this runs
FreeCAD.Console.PrintMessage(">>> DrawingAssistant InitGui loading\n")

_panel = None


def show_panel():
    """Show the Drawing Assistant panel."""
    global _panel

    mw = FreeCADGui.getMainWindow()
    if mw is None:
        FreeCAD.Console.PrintWarning("DrawingAssistant: No main window\n")
        return None

    if _panel is None:
        try:
            from PySide6 import QtCore
            import DrawingAssistant.DrawingPanel as DrawingPanel

            _panel = DrawingPanel.DrawingAssistantDockWidget()
            _panel.setObjectName("DrawingAssistantDockWidget")
            mw.addDockWidget(QtCore.Qt.RightDockWidgetArea, _panel)
            FreeCAD.Console.PrintMessage(">>> DrawingAssistant panel created\n")
        except Exception as e:
            FreeCAD.Console.PrintError(f"DrawingAssistant error: {e}\n")
            import traceback

            traceback.print_exc()
            return None

    _panel.show()
    _panel.raise_()
    return _panel


def toggle_panel():
    """Toggle panel visibility."""
    global _panel
    if _panel is None:
        show_panel()
    elif _panel.isVisible():
        _panel.hide()
    else:
        _panel.show()
        _panel.raise_()


class DrawingAssistantCommand:
    """Command to toggle Drawing Assistant."""

    def GetResources(self):
        return {
            "MenuText": "Drawing Assistant",
            "ToolTip": "Toggle Drawing Assistant panel for 2D structural drawings",
            "Accel": "Ctrl+Shift+D",
        }

    def Activated(self):
        import DrawingAssistant

        DrawingAssistant.toggle()

    def IsActive(self):
        return True


# Register the command
FreeCADGui.addCommand("Std_DrawingAssistant", DrawingAssistantCommand())
FreeCAD.Console.PrintMessage(">>> DrawingAssistant command registered\n")


# Add to View menu after delay
def _setup_menu():
    FreeCAD.Console.PrintMessage(">>> DrawingAssistant setting up menu\n")
    try:
        from PySide6 import QtGui

        mw = FreeCADGui.getMainWindow()
        if mw:
            for action in mw.menuBar().actions():
                if "View" in action.text():
                    menu = action.menu()
                    if menu:
                        act = QtGui.QAction("Drawing Assistant", mw)
                        act.setShortcut("Ctrl+Shift+D")
                        act.triggered.connect(
                            lambda: FreeCADGui.runCommand("Std_DrawingAssistant")
                        )
                        menu.addAction(act)
                        FreeCAD.Console.PrintMessage(
                            ">>> DrawingAssistant added to View menu\n"
                        )
                        return
    except Exception as e:
        FreeCAD.Console.PrintWarning(f"DrawingAssistant menu error: {e}\n")


from PySide6 import QtCore

QtCore.QTimer.singleShot(3000, _setup_menu)


FreeCAD.Console.PrintMessage(">>> DrawingAssistant InitGui loaded\n")
