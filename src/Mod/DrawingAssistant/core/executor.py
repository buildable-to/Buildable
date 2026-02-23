# SPDX-License-Identifier: LGPL-2.1-or-later
"""
Code Executor - Safely executes AI-generated Python code in FreeCAD.
"""

from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

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

# Object-tracking state for incremental execution
_page_object_map: Optional[Dict[str, Set[str]]] = None
_tracked_doc_name: Optional[str] = None

# ============================================================
# DRAWING COMPLETENESS REQUIREMENTS
# ============================================================

ELEMENT_REQUIREMENTS = {
    "beam_complete": {
        "mandatory": [
            "rebar_geometry",
            "stirrups",
            "cross_section",
            "longitudinal_section",
            "anchorage_details",
            "bar_schedule",
            "bar_shape_diagrams",
            "material_spec",
            "general_notes",
            "dimensions",
            "span_dimension",
        ],
        "description": "Complete beam drawing with cross-section + longitudinal elevation (both views on same sheet)",
    },
    "beam_section": {
        "mandatory": [
            "rebar_geometry",
            "stirrups",
            "cross_section",
            "bar_schedule",
            "bar_shape_diagrams",
            "material_spec",
            "general_notes",
            "dimensions",
            "span_dimension",
        ],
        "description": "Beam reinforcement section drawing (cross-section perpendicular to span)",
    },
    "beam_elevation": {
        "mandatory": [
            "rebar_geometry",
            "stirrups",
            "longitudinal_section",
            "anchorage_details",
            "bar_schedule",
            "bar_shape_diagrams",
            "material_spec",
            "general_notes",
            "dimensions",
            "span_dimension",
        ],
        "description": "Beam elevation drawing (longitudinal section along span)",
    },
    "slab_section": {
        "mandatory": [
            "rebar_geometry",
            "transverse_bars",
            "bar_schedule",
            "material_spec",
            "dimensions",
            "span_dimension",
        ],
        "description": "Slab reinforcement section drawing",
    },
    "column_section": {
        "mandatory": [
            "rebar_geometry",
            "links",
            "cross_section",
            "bar_schedule",
            "material_spec",
            "dimensions",
        ],
        "description": "Column reinforcement section drawing",
    },
    "foundation_section": {
        "mandatory": ["rebar_geometry", "bar_schedule", "material_spec", "dimensions"],
        "description": "Foundation reinforcement section drawing",
    },
    "formwork": {
        "mandatory": ["outline_geometry", "dimensions"],
        "description": "Formwork/shuttering drawing (no reinforcement)",
    },
    "general": {
        "mandatory": [],
        "description": "General drawing (no specific requirements)",
    },
}


def parse_drawing_spec(code: str) -> Optional[Dict[str, str]]:
    """Parse DRAWING_SPEC comment header from page file content.

    Expected format (at file top, before any code):
    # DRAWING_SPEC:
    # type: beam_section
    # elements: rebar_geometry, stirrups, cross_section, bar_schedule, material_spec
    # rebar: 4d20 bottom, 2d12 top, d8@150 stirrups
    # concrete: C35/45, cover 40mm, exposure XC3

    Args:
        code: Python source code string

    Returns:
        Dict with parsed spec fields (e.g. {'type': 'beam_section', 'elements': '...'})
        or None if no DRAWING_SPEC header found.
    """
    spec = {}
    in_spec = False
    for line in code.split("\n"):
        stripped = line.strip()
        if stripped == "# DRAWING_SPEC:":
            in_spec = True
            continue
        if in_spec:
            if not stripped.startswith("#"):
                break  # End of spec block
            # Parse "# key: value" pairs
            content = stripped[1:].strip()  # Remove leading #
            if ": " in content:
                key, value = content.split(": ", 1)
                spec[key.strip()] = value.strip()
    return spec if spec else None


def validate_drawing_spec(spec: Optional[Dict[str, str]]) -> str:
    """Validate a parsed DRAWING_SPEC against ELEMENT_REQUIREMENTS.

    Args:
        spec: Parsed drawing spec dict (or None for backward compatibility)

    Returns:
        Empty string if valid or no spec found (backward compatible).
        Error message if spec is present but mandatory elements are missing.
    """
    if not spec:
        return ""  # No spec = backward compatible, allow through

    element_type = spec.get("type", "general")
    requirements = ELEMENT_REQUIREMENTS.get(element_type, ELEMENT_REQUIREMENTS["general"])

    declared_elements_str = spec.get("elements", "")
    declared_elements = {e.strip() for e in declared_elements_str.split(",") if e.strip()}

    mandatory = requirements["mandatory"]
    missing = [elem for elem in mandatory if elem not in declared_elements]

    if missing:
        missing_list = ", ".join(missing)
        return (
            f"DRAWING_SPEC validation failed for type '{element_type}': "
            f"Missing mandatory elements: {missing_list}. "
            f"Add these to the 'elements:' line in the DRAWING_SPEC header and implement them."
        )
    return ""

SKIP_TYPES = ("App::Origin", "App::Plane", "App::Line")


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


class _TopDownView:
    """Minimal stand-in for a 3D view when no real one is available.

    Draft's make_linear_dimension() calls get3DView().getViewDirection()
    to determine the dimension normal. For 2D drafting (XY plane), a
    top-down direction (0, 0, -1) is the correct default.
    """

    def getViewDirection(self):
        return FreeCAD.Vector(0, 0, -1)

    def getSceneGraph(self):
        return None


# Singleton — reused across guard installs
_fallback_view = _TopDownView()


class _View3DGuard:
    """Monkeypatch Draft's get_3d_view to survive TechDraw tab activation.

    When a TechDraw::DrawPage is created and doc.recompute() runs, FreeCAD
    activates the TechDraw MDI tab. Draft functions like make_linear_dimension()
    call gui_utils.get3DView().getViewDirection(), which returns None when the
    active window is a TechDraw page (no getSceneGraph). This guard patches
    get_3d_view to fall back to a cached view, live-scanned view, or a
    top-down dummy — it never returns None.
    """

    def __init__(self):
        self._original_fn = None
        self._cached_view = None
        self._gui_utils = None

    def install(self):
        """Patch gui_utils with a resilient get_3d_view."""
        try:
            from draftutils import gui_utils
            self._gui_utils = gui_utils
            self._original_fn = gui_utils.get_3d_view

            # Try to capture the 3D view now. If the MDI is in a bad state
            # (e.g. TechDraw tab lingering after object clearing), this may
            # return None — that's OK, the patch will find it lazily later.
            self._cached_view = gui_utils.get_3d_view() or _find_3d_view()

            guard = self

            def _safe_get_3d_view():
                # Fast path: original function finds active 3D view
                view = guard._original_fn()
                if view is not None:
                    return view
                # Cached from install or a previous miss
                if guard._cached_view is not None:
                    return guard._cached_view
                # Live scan: MDI may have settled since install time
                found = _find_3d_view()
                if found is not None:
                    guard._cached_view = found
                    return found
                # Last resort: top-down dummy so Draft never crashes
                return _fallback_view

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


# =============================================================================
# Tracked page execution (for incremental rebuild)
# =============================================================================


def execute_pages(page_paths: List[Path]) -> tuple:
    """Execute page scripts individually with per-page object tracking.

    Runs all pages in order using a shared namespace (so cross-page
    variables work). Records which document objects each page created
    in the module-level _page_object_map.

    Args:
        page_paths: Sorted list of page file paths to execute.

    Returns:
        Tuple of (success: bool, message: str, warnings: list)
    """
    global _page_object_map, _tracked_doc_name

    if not page_paths:
        return False, "No pages to execute", []

    # Read all pages and do a single safety check on combined content
    page_contents = {}
    combined = []
    for p in page_paths:
        try:
            content = p.read_text(encoding="utf-8")
        except Exception as e:
            return False, f"Failed to read {p.name}: {e}", []
        page_contents[p.name] = content
        combined.append(content)

    safety_result = _safety_check("\n".join(combined))
    if safety_result:
        return False, safety_result, []

    # Validate DRAWING_SPEC headers for mandatory elements
    for p_name, content in page_contents.items():
        if not p_name.startswith("_"):  # Skip helper files
            spec = parse_drawing_spec(content)
            spec_error = validate_drawing_spec(spec)
            if spec_error:
                return False, spec_error, []

    doc = FreeCAD.ActiveDocument
    if not doc:
        return False, "No active document", []

    namespace = _build_namespace()

    view_guard = _View3DGuard()
    view_guard.install()

    try:
        page_map: Dict[str, Set[str]] = {}

        with WarningCapture() as capture:
            sheet_index = 0
            for p in page_paths:
                # Inject SHEET_Y_OFFSET for non-helper files so each
                # sheet's geometry occupies a unique Y band in Draft space
                if not p.name.startswith("_"):
                    namespace["SHEET_Y_OFFSET"] = sheet_index * 100000
                    sheet_index += 1

                before = {
                    obj.Name for obj in doc.Objects if obj.TypeId not in SKIP_TYPES
                }
                exec(page_contents[p.name], namespace)
                after = {
                    obj.Name for obj in doc.Objects if obj.TypeId not in SKIP_TYPES
                }
                page_map[p.name] = after - before

            doc.recompute()

            try:
                if FreeCADGui.ActiveDocument and FreeCADGui.ActiveDocument.ActiveView:
                    FreeCADGui.ActiveDocument.ActiveView.fitAll()
            except Exception:
                pass

        _page_object_map = page_map
        _tracked_doc_name = doc.Name

        total = sum(len(v) for v in page_map.values())
        FreeCAD.Console.PrintMessage(
            f"DrawingAssistant: Tracked {total} objects across {len(page_map)} pages\n"
        )

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


def execute_single_page(
    page_path: Path,
    helper_paths: Optional[List[Path]] = None,
    sheet_index: int = 0,
) -> Tuple[bool, str, list, Set[str]]:
    """Execute a single page script for incremental rebuild.

    Uses a fresh namespace populated only with FreeCAD modules and
    optional helper files. Returns the set of new object names created.

    Args:
        page_path: Path to the page file to execute.
        helper_paths: Paths to _-prefixed helper files to pre-execute
                      (provides shared variables/functions).
        sheet_index: Position among non-helper files (for SHEET_Y_OFFSET).

    Returns:
        Tuple of (success, message, warnings, new_object_names).
    """
    try:
        code = page_path.read_text(encoding="utf-8")
    except Exception as e:
        return False, f"Failed to read {page_path.name}: {e}", [], set()

    safety_result = _safety_check(code)
    if safety_result:
        return False, safety_result, [], set()

    # Validate DRAWING_SPEC header for mandatory elements
    spec = parse_drawing_spec(code)
    spec_error = validate_drawing_spec(spec)
    if spec_error:
        return False, spec_error, [], set()

    doc = FreeCAD.ActiveDocument
    if not doc:
        return False, "No active document", [], set()

    namespace = _build_namespace()
    namespace["SHEET_Y_OFFSET"] = sheet_index * 100000

    view_guard = _View3DGuard()
    view_guard.install()

    try:
        with WarningCapture() as capture:
            # Pre-execute helpers so shared variables are available
            if helper_paths:
                for hp in helper_paths:
                    try:
                        helper_code = hp.read_text(encoding="utf-8")
                        exec(helper_code, namespace)
                    except Exception:
                        pass  # helpers failing is non-fatal

            before = {
                obj.Name for obj in doc.Objects if obj.TypeId not in SKIP_TYPES
            }
            exec(code, namespace)
            after = {
                obj.Name for obj in doc.Objects if obj.TypeId not in SKIP_TYPES
            }
            new_objects = after - before

            doc.recompute()

            try:
                if FreeCADGui.ActiveDocument and FreeCADGui.ActiveDocument.ActiveView:
                    FreeCADGui.ActiveDocument.ActiveView.fitAll()
            except Exception:
                pass

        return True, "OK", capture.warnings, new_objects

    except SyntaxError as e:
        return False, f"Syntax error at line {e.lineno}: {e.msg}", [], set()
    except NameError as e:
        return False, f"Name error: {e}", [], set()
    except AttributeError as e:
        return False, f"Attribute error: {e}", [], set()
    except Exception as e:
        return False, f"Execution error: {type(e).__name__}: {e}", [], set()
    finally:
        view_guard.uninstall()


# =============================================================================
# Page object map accessors
# =============================================================================


def get_page_object_map() -> Optional[Dict[str, Set[str]]]:
    """Return the current page-to-objects mapping, or None if not tracked."""
    return _page_object_map


def get_tracked_doc_name() -> Optional[str]:
    """Return the document name the mapping was built for."""
    return _tracked_doc_name


def update_page_object_map(filename: str, objects: Set[str]):
    """Replace the object set for a single page (after incremental re-execution)."""
    global _page_object_map
    if _page_object_map is None:
        _page_object_map = {}
    _page_object_map[filename] = objects


def remove_from_page_object_map(filename: str):
    """Remove a page's entry from the mapping (page was deleted)."""
    global _page_object_map
    if _page_object_map and filename in _page_object_map:
        del _page_object_map[filename]


def clear_page_object_map():
    """Clear the mapping entirely (forces full rebuild next time)."""
    global _page_object_map, _tracked_doc_name
    _page_object_map = None
    _tracked_doc_name = None


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
