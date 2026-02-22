# SPDX-License-Identifier: LGPL-2.1-or-later
"""
Review Kit - Generates per-group screenshots and inspection data for AI review.

After code execution, captures a screenshot per App::DocumentObjectGroup,
organized by sheet file:

    screenshots/
    ├── 01_foundation/
    │   ├── PlanGroup.png
    │   ├── SectionAGroup.png
    │   └── SectionBGroup.png
    └── 02_reinforcement/
        └── RebarSectionAGroup.png

Screenshots persist across turns — only the changed sheet file's groups
are recaptured.  Claude reads them on-demand via the Read tool.
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

import FreeCAD
import FreeCADGui

from . import snapshot as SnapshotModule
from .changes import ChangeSet


_SKIP_TYPES = ("App::Origin", "App::Plane", "App::Line", "App::Point")

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

    group_screenshots: Dict[str, Dict[str, str]] = field(default_factory=dict)
    inspection_path: Optional[str] = None
    change_summary: str = ""
    changed_files: List[str] = field(default_factory=list)


# =============================================================================
# Public API
# =============================================================================


def capture_group_screenshots(
    project_dir: str,
    page_object_map: Optional[Dict[str, Set[str]]] = None,
    changed_files: Optional[List[str]] = None,
) -> Dict[str, Dict[str, str]]:
    """Capture a screenshot per App::DocumentObjectGroup, organized by sheet file.

    Args:
        project_dir: Project directory (contains screenshots/ subfolder).
        page_object_map: Mapping from filename -> set of object Names.
                         Used to associate groups with their sheet file.
        changed_files: If provided, only recapture groups from these files.
                       Other files' existing screenshots are preserved.

    Returns:
        Nested dict: {sheet_stem: {group_label: screenshot_path}}
    """
    doc = FreeCAD.ActiveDocument
    if not doc:
        return {}

    screenshots_dir = Path(project_dir) / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    view = _ensure_3d_view()
    if not view or not hasattr(view, "saveImage"):
        FreeCAD.Console.PrintWarning(
            "DrawingAssistant: No 3D view for group screenshots\n"
        )
        return {}

    # Build reverse map: object Name -> filename
    obj_to_file: Dict[str, str] = {}
    if page_object_map:
        for filename, obj_names in page_object_map.items():
            for name in obj_names:
                obj_to_file[name] = filename

    # Find all groups and map to their sheet file
    file_groups: Dict[str, List] = {}  # filename -> [group_obj, ...]

    for obj in doc.Objects:
        if obj.TypeId != "App::DocumentObjectGroup":
            continue

        filename = obj_to_file.get(obj.Name)
        if not filename:
            # Group not tracked — try to find via any child
            if hasattr(obj, "Group"):
                for child in obj.Group:
                    filename = obj_to_file.get(child.Name)
                    if filename:
                        break
        if not filename:
            filename = "_ungrouped"

        file_groups.setdefault(filename, []).append(obj)

    # Determine which files need recapture
    files_to_capture = set()
    if changed_files is not None:
        files_to_capture = set(changed_files)
    else:
        # Capture all
        files_to_capture = set(file_groups.keys())

    # Clean old screenshots for files being recaptured
    for filename in files_to_capture:
        stem = Path(filename).stem
        subdir = screenshots_dir / stem
        if subdir.exists():
            for old_png in subdir.glob("*.png"):
                try:
                    old_png.unlink()
                except OSError:
                    pass

    # Also clean legacy review_* files from old system
    for stale in screenshots_dir.glob("review_*"):
        try:
            stale.unlink()
        except OSError:
            pass

    # Capture screenshots
    saved_camera = None
    if hasattr(view, "getCamera"):
        saved_camera = view.getCamera()
    if hasattr(view, "setAnimationEnabled"):
        view.setAnimationEnabled(False)

    result: Dict[str, Dict[str, str]] = {}
    total_captured = 0

    try:
        for filename, groups in file_groups.items():
            if filename not in files_to_capture:
                continue

            stem = Path(filename).stem
            subdir = screenshots_dir / stem
            subdir.mkdir(parents=True, exist_ok=True)

            sheet_screenshots: Dict[str, str] = {}
            used_names: set = set()

            for group_obj in groups:
                children = _get_group_children(group_obj)
                if not children:
                    continue

                # Safe filename from group label
                safe_label = re.sub(r"[^\w\-]", "_", group_obj.Label).strip("_") or "group"
                if safe_label in used_names:
                    counter = 2
                    while f"{safe_label}_{counter}" in used_names:
                        counter += 1
                    safe_label = f"{safe_label}_{counter}"
                used_names.add(safe_label)

                filepath = subdir / f"{safe_label}.png"

                try:
                    FreeCADGui.Selection.clearSelection()
                    for child in children:
                        FreeCADGui.Selection.addSelection(child)

                    view.viewTop()
                    FreeCADGui.SendMsgToActiveView("ViewSelection")
                    FreeCADGui.updateGui()
                    view.saveImage(str(filepath), 1200, 900)

                    sheet_screenshots[group_obj.Label] = str(filepath)
                    total_captured += 1
                except Exception as e:
                    FreeCAD.Console.PrintWarning(
                        f"DrawingAssistant: Screenshot failed for {group_obj.Label}: {e}\n"
                    )
                finally:
                    FreeCADGui.Selection.clearSelection()

            if sheet_screenshots:
                result[stem] = sheet_screenshots

    finally:
        if saved_camera and hasattr(view, "setCamera"):
            view.setCamera(saved_camera)
            FreeCADGui.updateGui()
        if hasattr(view, "setAnimationEnabled"):
            view.setAnimationEnabled(True)

    FreeCAD.Console.PrintMessage(
        f"DrawingAssistant: Captured {total_captured} group screenshots\n"
    )
    return result


def list_available_screenshots(project_dir: str) -> Dict[str, Dict[str, str]]:
    """Scan screenshots/ directory for persisted group screenshots.

    No document access needed — reads from disk only.

    Returns:
        Nested dict: {sheet_stem: {group_label: absolute_path}}
        group_label is derived from the PNG filename (underscores → spaces).
    """
    screenshots_dir = Path(project_dir) / "screenshots"
    if not screenshots_dir.exists():
        return {}

    result: Dict[str, Dict[str, str]] = {}

    for subdir in sorted(screenshots_dir.iterdir()):
        if not subdir.is_dir():
            continue

        sheet_stem = subdir.name
        group_shots: Dict[str, str] = {}

        for png in sorted(subdir.glob("*.png")):
            label = png.stem.replace("_", " ")
            group_shots[label] = str(png)

        if group_shots:
            result[sheet_stem] = group_shots

    return result


def generate_review_kit(
    change_set: ChangeSet,
    project_dir: str,
    page_object_map: Optional[Dict[str, Set[str]]] = None,
    changed_files: Optional[List[str]] = None,
) -> ReviewKit:
    """Generate review kit: per-group screenshots + inspection JSON.

    Args:
        change_set: Detected changes from before/after snapshots.
        project_dir: Project directory (contains screenshots/ subfolder).
        page_object_map: Mapping from filename -> set of object Names.
        changed_files: If provided, only recapture these files' groups.

    Returns:
        ReviewKit with paths to generated files.
    """
    kit = ReviewKit()
    kit.change_summary = _build_change_summary(change_set)
    kit.changed_files = list(changed_files) if changed_files else []

    # 1. Per-group screenshots (incremental)
    kit.group_screenshots = capture_group_screenshots(
        project_dir, page_object_map, changed_files
    )

    # 2. Inspection JSON with object properties
    screenshots_dir = Path(project_dir) / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    kit.inspection_path = _write_inspection_json(change_set, screenshots_dir)

    return kit


def format_review_prompt(kit: ReviewKit) -> str:
    """Generate the review prompt text listing available files."""
    lines = [
        "I just executed drawing code. Review the result.",
        "",
        f"Changes: {kit.change_summary}",
        "",
        "Available screenshots (use Read tool to view):",
    ]

    for sheet_stem, groups in kit.group_screenshots.items():
        for label, path in groups.items():
            lines.append(f"- {sheet_stem} / {label}: {path}")

    if kit.inspection_path:
        lines.append(f"- Object properties (numerical values): {kit.inspection_path}")

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


# =============================================================================
# Internal helpers
# =============================================================================


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
