# SPDX-License-Identifier: LGPL-2.1-or-later
"""AIAssistant GUI initialization."""

# Note: FreeCAD and FreeCADGui are pre-loaded by FreeCAD before this runs
FreeCAD.Console.PrintMessage(">>> AIAssistant InitGui loading\n")

_panel = None
_observer = None


def show_panel():
    """Show the AI Assistant panel."""
    global _panel

    mw = FreeCADGui.getMainWindow()
    if mw is None:
        FreeCAD.Console.PrintWarning("AIAssistant: No main window\n")
        return None

    if _panel is None:
        try:
            from PySide6 import QtCore
            # Use absolute import instead of relative
            import AIAssistant.AIPanel as AIPanel
            _panel = AIPanel.AIAssistantDockWidget()
            _panel.setObjectName("AIAssistantDockWidget")
            mw.addDockWidget(QtCore.Qt.RightDockWidgetArea, _panel)
            FreeCAD.Console.PrintMessage(">>> AIAssistant panel created\n")
        except Exception as e:
            FreeCAD.Console.PrintError(f"AIAssistant error: {e}\n")
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


class AIAssistantCommand:
    """Command to toggle AI Assistant."""

    def GetResources(self):
        return {
            "MenuText": "3D Assistant",
            "ToolTip": "Toggle 3D Assistant panel",
            "Accel": "Ctrl+Shift+A",
        }

    def Activated(self):
        # Import the module to access functions that persist
        import AIAssistant
        AIAssistant.toggle()

    def IsActive(self):
        return True


# Register the command
FreeCADGui.addCommand("Std_AIAssistant", AIAssistantCommand())
FreeCAD.Console.PrintMessage(">>> AIAssistant command registered\n")


# Add to View menu after delay
def _setup_menu():
    FreeCAD.Console.PrintMessage(">>> AIAssistant setting up menu\n")
    try:
        from PySide6 import QtGui  # QAction is in QtGui in PySide6
        mw = FreeCADGui.getMainWindow()
        if mw:
            for action in mw.menuBar().actions():
                if "View" in action.text():
                    menu = action.menu()
                    if menu:
                        act = QtGui.QAction("3D Assistant", mw)
                        act.setShortcut("Ctrl+Shift+A")
                        # Use the registered command instead of direct function reference
                        act.triggered.connect(lambda: FreeCADGui.runCommand("Std_AIAssistant"))
                        menu.addAction(act)
                        FreeCAD.Console.PrintMessage(">>> AIAssistant added to View menu\n")
                        return
    except Exception as e:
        FreeCAD.Console.PrintWarning(f"AIAssistant menu error: {e}\n")


from PySide6 import QtCore
QtCore.QTimer.singleShot(3000, _setup_menu)


def _setup_document_observer():
    """Register the document observer to auto-open AI Assistant."""
    global _observer

    def _show_panel_safe():
        """Show panel using module import to avoid scope issues."""
        try:
            import AIAssistant
            AIAssistant.show()
        except Exception as e:
            FreeCAD.Console.PrintWarning(f"AIAssistant: Failed to show panel: {e}\n")

    class _DocumentObserver:
        """Document observer that auto-opens AI Assistant when a document is created/opened."""

        def slotCreatedDocument(self, doc):
            """Called when a new document is created."""
            # Skip internal/sandbox documents
            if doc.Name.startswith("__"):
                return
            FreeCAD.Console.PrintMessage(f">>> AIAssistant: Document created: {doc.Name}\n")
            from PySide6 import QtCore
            QtCore.QTimer.singleShot(100, _show_panel_safe)

        def slotOpenedDocument(self, doc):
            """Called when an existing document is opened."""
            if doc.Name.startswith("__"):
                return
            FreeCAD.Console.PrintMessage(f">>> AIAssistant: Document opened: {doc.Name}\n")
            from PySide6 import QtCore
            QtCore.QTimer.singleShot(100, _show_panel_safe)

    try:
        _observer = _DocumentObserver()
        FreeCAD.addDocumentObserver(_observer)
        FreeCAD.Console.PrintMessage(">>> AIAssistant document observer registered\n")
    except Exception as e:
        FreeCAD.Console.PrintWarning(f"AIAssistant observer error: {e}\n")


# Register observer after a short delay to ensure FreeCAD is fully initialized
QtCore.QTimer.singleShot(1000, _setup_document_observer)

FreeCAD.Console.PrintMessage(">>> AIAssistant InitGui loaded\n")
