# SPDX-License-Identifier: LGPL-2.1-or-later
"""
Code Executor - Safely executes AI-generated Python code in FreeCAD.
"""

import FreeCAD
import FreeCADGui

# Patterns that might indicate dangerous operations
BLOCKED_PATTERNS = [
    "os.system",
    "subprocess",
    "shutil.rmtree",
    "shutil.remove",
    "__import__('os')",
    "__import__(\"os\")",
    "eval(",
    "open(",
    "file(",
    ".write(",
    "requests.",
    "urllib.",
    "socket.",
]

# Module-level storage for captured warnings
_captured_warnings = []


class WarningCapture:
    """Context manager to capture FreeCAD console warnings during execution."""

    def __init__(self):
        self._original_warning = None
        self._original_dev_warning = None
        self._original_user_warning = None
        self.warnings = []

    def __enter__(self):
        global _captured_warnings
        _captured_warnings = []
        self.warnings = _captured_warnings

        # Store original functions
        self._original_warning = FreeCAD.Console.PrintWarning
        self._original_dev_warning = FreeCAD.Console.PrintDeveloperWarning
        self._original_user_warning = FreeCAD.Console.PrintUserWarning

        # Create capturing wrapper
        def capture_warning(msg):
            self.warnings.append(msg.rstrip('\n'))
            self._original_warning(msg)

        def capture_dev_warning(msg):
            self.warnings.append(msg.rstrip('\n'))
            self._original_dev_warning(msg)

        def capture_user_warning(msg):
            self.warnings.append(msg.rstrip('\n'))
            self._original_user_warning(msg)

        # Monkeypatch - this works because Python Console methods are
        # module-level functions that can be replaced
        FreeCAD.Console.PrintWarning = capture_warning
        FreeCAD.Console.PrintDeveloperWarning = capture_dev_warning
        FreeCAD.Console.PrintUserWarning = capture_user_warning

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original functions
        FreeCAD.Console.PrintWarning = self._original_warning
        FreeCAD.Console.PrintDeveloperWarning = self._original_dev_warning
        FreeCAD.Console.PrintUserWarning = self._original_user_warning
        return False


def _find_3d_view():
    """Find a 3D view by scanning MDI sub-windows.

    Unlike gui_utils.get_3d_view() which only returns the *active* window,
    this searches ALL MDI sub-windows for one with getSceneGraph (a 3D view).
    Works even when a TechDraw page tab is currently active.
    """
    try:
        mw = FreeCADGui.getMainWindow()
        mdi = mw.centralWidget()
        for sub in mdi.subWindowList():
            widget = sub.widget()
            if hasattr(widget, "getSceneGraph"):
                return widget
    except Exception:
        pass
    return None


class _View3DGuard:
    """Monkeypatch Draft's get_3d_view to survive TechDraw tab activation.

    When a TechDraw::DrawPage is created and doc.recompute() runs, FreeCAD
    activates the TechDraw MDI tab. Draft functions like make_linear_dimension()
    call gui_utils.get3DView().getViewDirection(), which returns None when the
    active window is a TechDraw page (no getSceneGraph). This guard stores
    the 3D view before execution and falls back to it if get_3d_view returns None.
    """

    def __init__(self):
        self._original_fn = None
        self._stored_view = None
        self._gui_utils = None

    def install(self):
        """Store current 3D view and patch gui_utils."""
        try:
            from draftutils import gui_utils
            self._gui_utils = gui_utils
            self._original_fn = gui_utils.get_3d_view

            # Find the 3D view even if a TechDraw tab is currently active.
            # gui_utils.get_3d_view() only returns the active window, which
            # may be a TechDraw page. _find_3d_view() scans all MDI windows.
            self._stored_view = gui_utils.get_3d_view() or _find_3d_view()

            if self._stored_view is None:
                return  # No 3D view available — nothing to guard

            def _safe_get_3d_view():
                view = self._original_fn()
                if view is None:
                    return self._stored_view
                return view

            gui_utils.get_3d_view = _safe_get_3d_view
            gui_utils.get3DView = _safe_get_3d_view
        except Exception:
            pass  # Draft not available — nothing to guard

    def uninstall(self):
        """Restore original get_3d_view."""
        if self._gui_utils and self._original_fn:
            try:
                self._gui_utils.get_3d_view = self._original_fn
                self._gui_utils.get3DView = self._original_fn
            except Exception:
                pass


def execute(code: str) -> tuple:
    """
    Execute Python code in FreeCAD's environment.

    Args:
        code: Python code string to execute

    Returns:
        Tuple of (success: bool, message: str, warnings: list)
        The warnings list contains any deprecation or other warnings captured during execution.
    """
    # Clean the code
    code = _clean_code(code)

    if not code.strip():
        return False, "No code to execute", []

    # Safety check
    safety_result = _safety_check(code)
    if safety_result:
        return False, safety_result, []

    # Build execution namespace with FreeCAD modules
    namespace = _build_namespace()

    # Guard against TechDraw page tabs stealing focus from the 3D view.
    # Draft.make_linear_dimension() etc. call gui_utils.get3DView().getViewDirection(),
    # which returns None when a TechDraw page is the active MDI window.
    view_guard = _View3DGuard()
    view_guard.install()

    try:
        # Execute with warning capture
        with WarningCapture() as capture:
            # Execute the code
            exec(code, namespace)

            # Recompute document
            if FreeCAD.ActiveDocument:
                FreeCAD.ActiveDocument.recompute()

            # Fit view to show results
            try:
                if FreeCADGui.ActiveDocument and FreeCADGui.ActiveDocument.ActiveView:
                    FreeCADGui.ActiveDocument.ActiveView.fitAll()
            except Exception:
                pass

        return True, "Code executed successfully", capture.warnings

    except SyntaxError as e:
        return False, f"Syntax error at line {e.lineno}: {e.msg}", []

    except NameError as e:
        return False, f"Name error: {e}", []

    except AttributeError as e:
        return False, f"Attribute error: {e}", []

    except Exception as e:
        return False, f"Execution error: {type(e).__name__}: {e}", []

    finally:
        view_guard.uninstall()


def get_last_warnings() -> list:
    """Get warnings captured from the last execution."""
    return _captured_warnings.copy()


def _clean_code(code: str) -> str:
    """Clean up code - remove markdown formatting if present."""
    code = code.strip()

    # Remove markdown code fences
    lines = code.split("\n")
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]

    return "\n".join(lines).strip()


def _safety_check(code: str) -> str:
    """
    Check code for potentially dangerous operations.

    Returns:
        Error message if dangerous pattern found, empty string if safe.
    """
    code_lower = code.lower()

    for pattern in BLOCKED_PATTERNS:
        if pattern.lower() in code_lower:
            return f"Blocked potentially dangerous operation: {pattern}"

    return ""


def _build_namespace() -> dict:
    """Build the execution namespace with FreeCAD modules."""
    namespace = {
        "FreeCAD": FreeCAD,
        "FreeCADGui": FreeCADGui,
        "App": FreeCAD,
        "Gui": FreeCADGui,
        # Provide 'doc' for convenience - matches sandbox preview environment
        "doc": FreeCAD.ActiveDocument,
    }

    # Import 2D-focused workbench modules (each wrapped in try/except for optional ones)
    modules_to_import = [
        "Draft",
        "TechDraw",
        "Spreadsheet",
        "Part",           # Needed for Draft internals (Part::Part2DObject)
        "DraftGeomUtils",
    ]

    for mod_name in modules_to_import:
        try:
            namespace[mod_name] = __import__(mod_name)
        except ImportError:
            pass

    return namespace


def validate_code(code: str) -> tuple:
    """
    Validate code without executing it.

    Returns:
        Tuple of (is_valid: bool, message: str)
    """
    code = _clean_code(code)

    if not code.strip():
        return False, "Empty code"

    # Safety check
    safety_result = _safety_check(code)
    if safety_result:
        return False, safety_result

    # Try to compile
    try:
        compile(code, "<ai_generated>", "exec")
        return True, "Code is valid"
    except SyntaxError as e:
        return False, f"Syntax error at line {e.lineno}: {e.msg}"
