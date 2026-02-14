# SPDX-License-Identifier: LGPL-2.1-or-later
"""
Context Builder - Gathers lean FreeCAD document state for AI context.
Adapted for 2D structural drawings: Draft wires, TechDraw pages,
Spreadsheet sheets, dimensions, and annotations.
"""

import FreeCAD
import FreeCADGui
from collections import deque


# Global buffer for console messages (errors and warnings)
_console_buffer = deque(maxlen=50)  # Keep last 50 messages
_console_observer = None


class ConsoleObserver:
    """Observer that captures FreeCAD console messages."""

    def __init__(self, buffer):
        self._buffer = buffer

    def Error(self, msg):
        """Capture error messages."""
        self._buffer.append(("error", msg.strip()))

    def Warning(self, msg):
        """Capture warning messages."""
        self._buffer.append(("warning", msg.strip()))

    def Message(self, msg):
        """Capture regular messages (optional, filtered)."""
        msg_stripped = msg.strip()
        if msg_stripped and any(
            kw in msg_stripped.lower()
            for kw in ["failed", "invalid", "cannot", "error", "exception"]
        ):
            self._buffer.append(("message", msg_stripped))

    def Log(self, msg):
        """Capture log messages (skip most, too verbose)."""
        pass


def start_console_observer():
    """Start capturing console messages."""
    pass


def stop_console_observer():
    """Stop capturing console messages."""
    pass


def get_console_buffer():
    """Get the current console buffer contents."""
    return list(_console_buffer)


def clear_console_buffer():
    """Clear the console buffer."""
    _console_buffer.clear()


# =============================================================================
# CONTEXT BUILDING
# =============================================================================


def _get_environment_context() -> str:
    """Get FreeCAD environment info as a single line."""
    lines = []

    try:
        version = FreeCAD.Version()
        if version and len(version) >= 2:
            ver_str = f"{version[0]}.{version[1]}"
            if len(version) > 2 and version[2]:
                ver_str += f".{version[2]}"
            lines.append(f"FreeCAD {ver_str}")
    except Exception:
        lines.append("FreeCAD (version unknown)")

    try:
        wb = FreeCADGui.activeWorkbench()
        if wb:
            wb_name = wb.name() if hasattr(wb, "name") else str(type(wb).__name__)
            wb_name = wb_name.replace("Workbench", "").strip()
            lines.append(f"Workbench: {wb_name}")
    except Exception:
        pass

    try:
        from FreeCAD import Units

        schema = Units.getSchema()
        decimals = Units.getDecimals()
        lines.append(f"Units: {schema} ({decimals} decimals)")
    except Exception:
        pass

    return " | ".join(lines) if lines else ""


def _get_selection_details() -> str:
    """Get detailed selection info for 2D objects.

    Unlike the 3D version, does not filter by Face/Edge/Vertex
    sub-elements since those are less relevant for 2D drawings.
    """
    try:
        sel_ex = FreeCADGui.Selection.getSelectionEx()
        if not sel_ex:
            return ""

        details = []
        for sel in sel_ex[:3]:
            obj_name = sel.Object.Label
            sub_elements = sel.SubElementNames

            if sub_elements:
                details.append(f"{obj_name} ({len(sub_elements)} sub-elements)")
            else:
                details.append(f"{obj_name} (whole object)")

        if details:
            return "Selection: " + "; ".join(details)
    except Exception:
        pass
    return ""


def _is_internal_object(obj) -> bool:
    """Check if object is internal (Origin, planes, etc.)."""
    type_id = obj.TypeId
    if type_id in ("App::Origin", "App::Plane", "App::Line", "App::Point"):
        return True
    if "Origin" in obj.Label:
        return True
    return False


def _describe_object_lean(obj) -> str:
    """One-line summary for 2D drawing objects."""
    type_short = obj.TypeId.split("::")[-1]
    parts = [f"  {obj.Label} ({type_short})"]

    # Draft wire/polyline
    if hasattr(obj, "Points") and obj.Points:
        parts.append(f"[{len(obj.Points)} points]")
        if hasattr(obj, "Closed"):
            parts.append("closed" if obj.Closed else "open")

    # Draft circle
    if hasattr(obj, "Radius") and not hasattr(obj, "Points"):
        try:
            val = obj.Radius
            r = val.Value if hasattr(val, "Value") else float(val)
            if r > 0:
                parts.append(f"[R={r:.0f}mm]")
        except (AttributeError, RuntimeError, TypeError):
            pass

    # TechDraw page
    if obj.TypeId == "TechDraw::DrawPage":
        template = ""
        if hasattr(obj, "Template") and obj.Template:
            template = obj.Template.Label
        view_count = len([o for o in obj.OutList if "DrawView" in o.TypeId])
        parts.append(f"[template={template}, {view_count} views]")

    # TechDraw template
    elif obj.TypeId == "TechDraw::DrawSVGTemplate":
        if hasattr(obj, "Template") and obj.Template:
            from pathlib import Path as P

            parts.append(f"[{P(obj.Template).name}]")

    # Spreadsheet
    elif obj.TypeId == "Spreadsheet::Sheet":
        try:
            headers = []
            for col in "ABCDEFGH":
                val = obj.getContents(f"{col}1")
                if val:
                    headers.append(str(val))
            if headers:
                parts.append(f"[headers: {', '.join(headers[:5])}]")
        except Exception:
            pass

    # Draft Dimension
    if hasattr(obj, "Distance"):
        try:
            val = obj.Distance
            d = val.Value if hasattr(val, "Value") else float(val)
            if d > 0:
                parts.append(f"[{d:.0f}mm]")
        except (AttributeError, RuntimeError, TypeError):
            pass

    # Draft Text
    if "Text" in type_short and hasattr(obj, "Text") and obj.Text:
        try:
            text_val = obj.Text
            if isinstance(text_val, (list, tuple)):
                text_preview = str(text_val[0])[:30] if text_val else ""
            else:
                text_preview = str(text_val)[:30]
            if text_preview:
                parts.append(f'["{text_preview}"]')
        except Exception:
            pass

    # Position (X,Y only for 2D)
    try:
        if hasattr(obj, "Placement"):
            pos = obj.Placement.Base
            if abs(pos.x) > 0.1 or abs(pos.y) > 0.1:
                parts.append(f"at ({pos.x:.0f},{pos.y:.0f})")
    except Exception:
        pass

    return " ".join(parts)


def _extract_expressions(objects) -> list:
    """Extract expressions (parametric relationships) from all objects."""
    expressions = []

    for obj in objects:
        try:
            if hasattr(obj, "ExpressionEngine") and obj.ExpressionEngine:
                for prop, expr in obj.ExpressionEngine:
                    expressions.append(
                        {
                            "object": obj.Label,
                            "property": prop,
                            "expression": expr,
                        }
                    )
        except Exception:
            pass

    return expressions


def _describe_expressions(expressions) -> str:
    """Format expressions for context output."""
    if not expressions:
        return ""

    lines = ["\n### Expressions:"]
    for expr in expressions[:15]:
        lines.append(f"  {expr['object']}.{expr['property']} = {expr['expression']}")

    if len(expressions) > 15:
        lines.append(f"  ... and {len(expressions) - 15} more")

    return "\n".join(lines)


def _get_console_errors() -> list:
    """Get recent console errors and warnings."""
    buffer = get_console_buffer()
    errors = [(t, m) for t, m in buffer if t in ("error", "warning")]
    return errors[-10:] if len(errors) > 10 else errors


def _describe_console_errors(errors) -> str:
    """Format console errors for context."""
    if not errors:
        return ""

    lines = ["\n### Recent Issues:"]
    for err_type, msg in errors:
        prefix = "ERROR" if err_type == "error" else "WARN"
        display_msg = msg[:100] + "..." if len(msg) > 100 else msg
        lines.append(f"  [{prefix}] {display_msg}")

    return "\n".join(lines)


def _get_pages_context() -> str:
    """Get summary of drawing pages in pages/ directory.

    Shows per file: name, line count, tags (TechDraw/Spreadsheet/Draft count),
    first comment, group names, and label prefixes.  This helps Claude decide
    which existing file to edit rather than creating a new one.
    """
    try:
        from . import source as SourceManager

        pages_meta = SourceManager.list_pages_metadata()
        if not pages_meta:
            return ""

        lines = [f"\n### Drawing Pages ({len(pages_meta)} files):"]
        for meta in pages_meta:
            parts = [f"  {meta['filename']} ({meta['line_count']} lines)"]

            # Tags: [TechDraw, Spreadsheet, N Draft objects]
            tags = []
            if meta.get("has_techdraw"):
                tags.append("TechDraw")
            if meta.get("has_spreadsheet"):
                tags.append("Spreadsheet")
            draft_count = meta.get("draft_object_count", 0)
            if draft_count > 0:
                tags.append(f"{draft_count} Draft objects")
            if tags:
                parts.append(f"[{', '.join(tags)}]")

            if meta.get("first_comment"):
                parts.append(f"— {meta['first_comment']}")

            # Group names show which TechDraw groups this file feeds
            group_names = meta.get("group_names", [])
            if group_names:
                parts.append(f"-> {', '.join(group_names)}")

            # Label prefixes show what kind of objects the file creates
            label_prefixes = meta.get("label_prefixes", [])
            if label_prefixes and not group_names:
                shown = label_prefixes[:5]
                suffix = f" +{len(label_prefixes) - 5}" if len(label_prefixes) > 5 else ""
                parts.append(f"labels: {', '.join(shown)}{suffix}")

            lines.append(" ".join(parts))

        return "\n".join(lines)
    except Exception:
        return ""


def build_context(objects_filter: list = None) -> str:
    """Build lean context: document state, not strategy.

    Args:
        objects_filter: Optional list of object names to include.
                       None = all objects. Empty list = environment only.
    """
    lines = []

    # Environment (1 line)
    env_context = _get_environment_context()
    if env_context:
        lines.append(f"Environment: {env_context}")

    doc = FreeCAD.ActiveDocument
    if doc is None:
        lines.append("No active document.")
        return "\n".join(lines)

    lines.append(f"Document: {doc.Name}")

    # Get objects
    all_objects = doc.Objects
    if objects_filter is not None:
        objects_set = set(objects_filter)
        objects = [obj for obj in all_objects if obj.Name in objects_set]
    else:
        objects = all_objects

    # Filter out internal objects
    visible_objects = [obj for obj in objects if not _is_internal_object(obj)]

    if not visible_objects:
        lines.append("Document is empty.")
    else:
        # Object list (one line per object)
        lines.append(f"\nObjects ({len(visible_objects)}):")
        for obj in visible_objects:
            lines.append(_describe_object_lean(obj))

    # Drawing pages listing
    pages_context = _get_pages_context()
    if pages_context:
        lines.append(pages_context)

    # Selection details
    selection_details = _get_selection_details()
    if selection_details:
        lines.append(f"\n{selection_details}")

    # Expressions (parametric relationships)
    expressions = _extract_expressions(objects if visible_objects else [])
    if expressions:
        lines.append(_describe_expressions(expressions))

    # Console errors
    console_errors = _get_console_errors()
    if console_errors:
        lines.append(_describe_console_errors(console_errors))

    return "\n".join(lines)


def get_selected_objects() -> list:
    """Get currently selected objects."""
    try:
        return FreeCADGui.Selection.getSelection()
    except Exception:
        return []


def get_selection_summary() -> str:
    """Get a summary of the current selection."""
    selected = get_selected_objects()
    if not selected:
        return "Nothing selected"

    return f"Selected: {', '.join(o.Label for o in selected)}"
