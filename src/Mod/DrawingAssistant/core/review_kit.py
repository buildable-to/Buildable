# SPDX-License-Identifier: LGPL-2.1-or-later
"""
Review Kit - Generates on-demand review files for AI self-review.

After code execution, produces a "review kit" of files on disk:
- Top-down view screenshot (full scene)
- Focused screenshots per changed object/group
- inspection.json with serialized object properties

Claude reads these on-demand via the Read tool during self-review,
inspecting only what it needs rather than receiving all images upfront.
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import FreeCAD
import FreeCADGui

from . import snapshot as SnapshotModule
from .changes import ChangeSet


_SKIP_TYPES = ("App::Origin", "App::Plane", "App::Line", "App::Point")

# Types to skip for focus screenshots (no useful 3D geometry to zoom into)
_SKIP_FOCUS_TYPES = (
    "TechDraw::DrawPage",
    "TechDraw::DrawSVGTemplate",
    "TechDraw::DrawViewPart",
    "TechDraw::DrawViewDraft",
    "TechDraw::DrawViewSpreadsheet",
)

# Properties that are internal/noise — never useful for drawing review
_SKIP_PROPERTIES = frozenset({
    "AttacherType",
    "AttachmentOffset",
    "AttachmentSupport",
    "MapMode",
    "MapPathParameter",
    "MapReversed",
    "_ElementMapVersion",
    "ExpressionEngine",
    "Symbol",  # TechDraw DrawViewDraft: full rendered SVG markup
    "EditableTexts",  # TechDraw template: raw editable text list
})


@dataclass
class ReviewKit:
    """Describes the generated review files on disk."""

    top_view_path: Optional[str] = None
    focus_paths: Dict[str, str] = field(default_factory=dict)
    inspection_path: Optional[str] = None
    change_summary: str = ""


def generate_review_kit(
    change_set: ChangeSet,
    project_dir: str,
    max_focus: int = 5,
) -> ReviewKit:
    """Generate review kit files on disk.

    Args:
        change_set: Detected changes from before/after snapshots.
        project_dir: Project directory (contains screenshots/ subfolder).
        max_focus: Maximum number of focused screenshots to capture.

    Returns:
        ReviewKit with paths to generated files.
    """
    screenshots_dir = Path(project_dir) / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    # Clean up stale files from previous runs
    for stale in screenshots_dir.glob("review_*"):
        try:
            stale.unlink()
        except OSError:
            pass
    for stale in screenshots_dir.glob("inspection.json"):
        try:
            stale.unlink()
        except OSError:
            pass
    # Also clean legacy files
    for stale in screenshots_dir.glob("latest_*"):
        try:
            stale.unlink()
        except OSError:
            pass

    kit = ReviewKit()
    kit.change_summary = _build_change_summary(change_set)

    # 1. Top-down view (full scene)
    kit.top_view_path = _capture_top_view(screenshots_dir)

    # 2. Focused screenshots per changed object/group
    kit.focus_paths = _capture_focus_screenshots(
        change_set, screenshots_dir, max_focus
    )

    # 3. Inspection JSON with object properties
    kit.inspection_path = _write_inspection_json(change_set, screenshots_dir)

    return kit


def format_review_prompt(kit: ReviewKit) -> str:
    """Generate the review prompt text listing available files."""
    lines = [
        "I just executed drawing code. Review the result.",
        "",
        f"Changes: {kit.change_summary}",
        "",
        "Available files for inspection (use Read tool as needed):",
    ]

    if kit.top_view_path:
        lines.append(f"- Top view screenshot: {kit.top_view_path}")

    for label, path in kit.focus_paths.items():
        lines.append(f'- Focus on "{label}": {path}')

    if kit.inspection_path:
        lines.append(f"- Object properties (exact numerical values): {kit.inspection_path}")

    lines.extend(
        [
            "",
            "CHECKS:",
            "- Geometry positioned correctly",
            "- Dimensions showing correct values",
            "- Text labels readable, no overlaps",
            "- No missing or overlapping geometry",
            "",
            'If CORRECT: respond with "LOOKS_GOOD"',
            "If PROBLEMS: explain briefly and edit the relevant page file to fix.",
        ]
    )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_change_summary(change_set: ChangeSet) -> str:
    """Build a one-line summary of changes."""
    parts = []
    if change_set.created:
        labels = [c.object_label for c in change_set.created[:5]]
        suffix = f" (+{len(change_set.created) - 5} more)" if len(change_set.created) > 5 else ""
        parts.append(f"Created {len(change_set.created)} ({', '.join(labels)}{suffix})")
    if change_set.modified:
        labels = [c.object_label for c in change_set.modified[:5]]
        parts.append(f"Modified {len(change_set.modified)} ({', '.join(labels)})")
    if change_set.deleted:
        labels = [c.object_label for c in change_set.deleted[:5]]
        parts.append(f"Deleted {len(change_set.deleted)} ({', '.join(labels)})")
    return ". ".join(parts) if parts else "No object changes detected"


def _ensure_3d_view():
    """Activate the 3D view MDI tab and return the view.

    After TechDraw page creation, FreeCAD may auto-activate the TechDraw tab.
    Uses FreeCADGui.activateView() to switch back to the 3D view.
    """
    if not FreeCADGui.ActiveDocument:
        return None

    view = FreeCADGui.ActiveDocument.ActiveView
    if hasattr(view, "saveImage"):
        return view

    # Use the built-in API to activate (or create) the 3D view
    try:
        FreeCADGui.activateView("Gui::View3DInventor", True)
        FreeCADGui.updateGui()
        view = FreeCADGui.ActiveDocument.ActiveView
        if hasattr(view, "saveImage"):
            return view
    except Exception:
        pass

    return None


def _capture_top_view(screenshots_dir: Path) -> Optional[str]:
    """Capture a top-down view of the full scene."""
    view = _ensure_3d_view()
    if not view or not hasattr(view, "saveImage"):
        FreeCAD.Console.PrintWarning(
            "DrawingAssistant: No 3D view for top screenshot\n"
        )
        return None

    filepath = screenshots_dir / "review_top.png"

    saved_camera = None
    if hasattr(view, "getCamera"):
        saved_camera = view.getCamera()
    if hasattr(view, "setAnimationEnabled"):
        view.setAnimationEnabled(False)

    try:
        view.viewTop()
        view.fitAll()
        FreeCADGui.updateGui()
        view.saveImage(str(filepath), 1200, 900)
        FreeCAD.Console.PrintMessage(
            f"DrawingAssistant: Captured review_top.png\n"
        )
        return str(filepath)
    except Exception as e:
        FreeCAD.Console.PrintWarning(
            f"DrawingAssistant: Top view capture failed: {e}\n"
        )
        return None
    finally:
        if saved_camera and hasattr(view, "setCamera"):
            view.setCamera(saved_camera)
            FreeCADGui.updateGui()
        if hasattr(view, "setAnimationEnabled"):
            view.setAnimationEnabled(True)


def _capture_focus_screenshots(
    change_set: ChangeSet,
    screenshots_dir: Path,
    max_focus: int,
) -> Dict[str, str]:
    """Capture zoomed screenshots for changed objects/groups."""
    doc = FreeCAD.ActiveDocument
    if not doc:
        return {}

    view = _ensure_3d_view()
    if not view or not hasattr(view, "saveImage"):
        return {}

    # Collect changed object names
    changed_names = set()
    for change in change_set.created:
        changed_names.add(change.object_name)
    for change in change_set.modified:
        changed_names.add(change.object_name)

    if not changed_names:
        return {}

    # Group by App::DocumentObjectGroup parent
    groups: Dict[str, List] = {}  # group_label -> [obj, ...]
    ungrouped: List = []

    for name in changed_names:
        obj = doc.getObject(name)
        if not obj or obj.TypeId in _SKIP_TYPES:
            continue
        # TechDraw objects have no 3D geometry to zoom into
        if obj.TypeId in _SKIP_FOCUS_TYPES:
            continue

        parent_group = _find_parent_group(obj)
        if parent_group:
            label = parent_group.Label
            groups.setdefault(label, []).append(parent_group)
            # Deduplicate — we add the group itself, not individual children
        else:
            ungrouped.append(obj)

    # Build focus targets: (label, [objects_to_select])
    targets = []

    # Groups first (deduplicated)
    seen_groups = set()
    for label, group_refs in groups.items():
        if label not in seen_groups:
            seen_groups.add(label)
            # Select all children of the group for a full view
            group_obj = group_refs[0]
            children = _get_group_children(group_obj)
            if children:
                targets.append((label, children))

    # Then ungrouped individual objects
    for obj in ungrouped:
        targets.append((obj.Label, [obj]))

    # Cap at max_focus
    targets = targets[:max_focus]

    # Capture each target
    saved_camera = None
    if hasattr(view, "getCamera"):
        saved_camera = view.getCamera()
    if hasattr(view, "setAnimationEnabled"):
        view.setAnimationEnabled(False)

    result = {}
    used_filenames = set()
    try:
        for label, objects in targets:
            safe_label = re.sub(r"[^\w\-]", "_", label).strip("_") or "obj"
            # Prevent filename collisions
            if safe_label in used_filenames:
                counter = 2
                while f"{safe_label}_{counter}" in used_filenames:
                    counter += 1
                safe_label = f"{safe_label}_{counter}"
            used_filenames.add(safe_label)
            filepath = screenshots_dir / f"review_focus_{safe_label}.png"

            try:
                FreeCADGui.Selection.clearSelection()
                for obj in objects:
                    FreeCADGui.Selection.addSelection(obj)

                view.viewTop()
                FreeCADGui.SendMsgToActiveView("ViewSelection")
                FreeCADGui.updateGui()
                view.saveImage(str(filepath), 1200, 900)
                result[label] = str(filepath)

                FreeCAD.Console.PrintMessage(
                    f"DrawingAssistant: Captured review_focus_{safe_label}.png\n"
                )
            except Exception as e:
                FreeCAD.Console.PrintWarning(
                    f"DrawingAssistant: Focus capture failed for {label}: {e}\n"
                )
            finally:
                FreeCADGui.Selection.clearSelection()
    finally:
        if saved_camera and hasattr(view, "setCamera"):
            view.setCamera(saved_camera)
            FreeCADGui.updateGui()
        if hasattr(view, "setAnimationEnabled"):
            view.setAnimationEnabled(True)

    return result


def _find_parent_group(obj):
    """Find the App::DocumentObjectGroup parent of an object, if any."""
    try:
        for parent in obj.InList:
            if parent.TypeId == "App::DocumentObjectGroup":
                return parent
    except Exception:
        pass
    return None


def _get_group_children(group_obj) -> List:
    """Get all child objects of a group (including the group itself)."""
    children = []
    try:
        if hasattr(group_obj, "Group"):
            children.extend(group_obj.Group)
        # Include the group itself so ViewSelection encompasses it
        children.append(group_obj)
    except Exception:
        pass
    return children


def _write_inspection_json(
    change_set: ChangeSet, screenshots_dir: Path
) -> Optional[str]:
    """Write a 2D-focused inspection report for changed objects."""
    doc = FreeCAD.ActiveDocument
    if not doc:
        return None

    # Collect changed object names and their change type
    changed = {}
    for c in change_set.created:
        changed[c.object_name] = "created"
    for c in change_set.modified:
        changed[c.object_name] = "modified"
    for c in change_set.deleted:
        changed[c.object_name] = "deleted"

    if not changed:
        return None

    objects_data = []
    for name, change_type in changed.items():
        if change_type == "deleted":
            # Deleted objects no longer exist in document
            objects_data.append({"name": name, "change": "deleted"})
            continue

        obj = doc.getObject(name)
        if not obj:
            continue

        entry = _serialize_object_2d(obj, change_type)
        objects_data.append(entry)

    report = {
        "summary": _build_change_summary(change_set),
        "objects": objects_data,
    }

    filepath = screenshots_dir / "inspection.json"
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)
        FreeCAD.Console.PrintMessage("DrawingAssistant: Wrote inspection.json\n")
        return str(filepath)
    except Exception as e:
        FreeCAD.Console.PrintWarning(
            f"DrawingAssistant: Failed to write inspection.json: {e}\n"
        )
        return None


def _serialize_object_2d(obj, change_type: str) -> dict:
    """Serialize a FreeCAD object in a flat, 2D-focused format."""
    entry = {
        "label": obj.Label,
        "name": obj.Name,
        "type": obj.TypeId,
        "change": change_type,
    }

    # Position (2D: x, y only)
    if hasattr(obj, "Placement"):
        pos = obj.Placement.Base
        entry["position"] = {"x": round(pos.x, 2), "y": round(pos.y, 2)}

    # Key properties via snapshot module
    props = SnapshotModule._capture_properties(obj)
    if props:
        flat_props = {}
        for prop_name, prop_data in props.items():
            if prop_name in _SKIP_PROPERTIES:
                continue
            val = prop_data.get("value")
            # Skip large string values (e.g. SVG markup, BREP)
            if isinstance(val, str) and len(val) > 500:
                continue
            if isinstance(val, dict) and "x" in val and "y" in val:
                # Vector — keep x,y only
                flat_props[prop_name] = {"x": round(val["x"], 2), "y": round(val["y"], 2)}
            elif isinstance(val, list):
                # Point lists — flatten z
                flat_props[prop_name] = val
            else:
                flat_props[prop_name] = val
        if flat_props:
            entry["properties"] = flat_props

    # Bounding box (2D)
    if hasattr(obj, "Shape") and obj.Shape and hasattr(obj.Shape, "BoundBox"):
        bb = obj.Shape.BoundBox
        entry["bounding_box"] = {
            "min": [round(bb.XMin, 2), round(bb.YMin, 2)],
            "max": [round(bb.XMax, 2), round(bb.YMax, 2)],
        }

    # Group children
    if hasattr(obj, "Group") and obj.Group:
        entry["children"] = [child.Label for child in obj.Group]

    # TechDraw page specifics
    if obj.TypeId == "TechDraw::DrawPage":
        entry["views"] = []
        if hasattr(obj, "Views"):
            for v in obj.Views:
                view_info = {"label": v.Label, "type": v.TypeId}
                if hasattr(v, "Scale"):
                    view_info["scale"] = v.Scale
                if hasattr(v, "X") and hasattr(v, "Y"):
                    vx = v.X.Value if hasattr(v.X, "Value") else v.X
                    vy = v.Y.Value if hasattr(v.Y, "Value") else v.Y
                    view_info["position_on_page"] = {"x": round(vx, 2), "y": round(vy, 2)}
                entry["views"].append(view_info)

    return entry
