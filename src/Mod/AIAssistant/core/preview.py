# SPDX-License-Identifier: LGPL-2.1-or-later
"""
Preview Manager - Manages 3D preview of objects before actual execution.

Executes code in a temporary document and shows preview objects as
green transparent shapes in the main document. User can approve or cancel.

For deletion operations, highlights target objects in red instead of sandbox.
"""

import re
import FreeCAD
import FreeCADGui
import Part
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any


def _build_sandbox_globals(doc):
    """Build execution globals with all workbench modules for sandbox execution."""
    exec_globals = {
        'FreeCAD': FreeCAD,
        'Part': Part,
        'doc': doc,
    }

    for mod_name in [
        "Draft", "Arch", "BIM", "Sketcher", "PartDesign",
        "Mesh", "TechDraw", "Spreadsheet", "Surface",
        "Points", "FEM", "CAM",
    ]:
        try:
            exec_globals[mod_name] = __import__(mod_name)
        except ImportError:
            pass

    return exec_globals

# Preview styling for creation
PREVIEW_COLOR = (0.1, 0.9, 0.3)  # Green
PREVIEW_TRANSPARENCY = 70  # 70% transparent

# Preview styling for deletion
DELETION_COLOR = (0.9, 0.2, 0.2)  # Red
DELETION_TRANSPARENCY = 50  # 50% transparent

# Patterns that indicate deletion operations
_DELETION_PATTERNS = [
    r'\.removeObject\s*\(\s*["\'](\w+)["\']\s*\)',  # doc.removeObject('Name')
    r'\.removeObjectsFromDocument\s*\(',             # bulk removal
]


@dataclass
class SandboxReviewSession:
    """Tracks a persistent sandbox for self-review iterations.

    The sandbox document is kept alive through multiple self-review cycles,
    allowing Claude to iterate and fix issues before the user sees the preview.
    """
    sandbox_doc_name: str = ""
    main_doc_name: str = ""
    source_content: str = ""  # Current source.py being reviewed
    iteration: int = 0
    max_iterations: int = 3
    preview_objects: List[str] = field(default_factory=list)  # Preview shapes in main doc
    object_shapes: Dict[str, Any] = field(default_factory=dict)  # Shapes from sandbox
    is_active: bool = False


class PreviewManager:
    """Manages preview objects before actual execution.

    Workflow:
    1. create_preview(code) - Execute in temp doc, show green preview
    2. User sees preview in 3D view
    3. approve() or cancel() - Clear preview, optionally execute for real
    """

    def __init__(self):
        self._preview_objects: List[str] = []  # Names of preview objects in main doc
        self._temp_doc = None
        self._main_doc_name: Optional[str] = None
        self._pending_code: str = ""

        # Deletion preview state
        self._is_deletion: bool = False
        self._deletion_targets: List[str] = []  # Object names to be deleted
        self._deletion_originals: Dict[str, Dict] = {}  # Original appearance to restore

        # Modification preview state (same name, different geometry)
        self._modified_names: List[str] = []  # Object names being modified

        # Warnings captured during sandbox execution (for agentic learning)
        self._last_sandbox_warnings: List[str] = []

    def get_last_warnings(self) -> List[str]:
        """Get warnings captured during the last sandbox execution.

        Used for agentic learning - warnings are fed back to Claude
        so it can learn to avoid deprecated APIs.

        Returns:
            List of warning messages
        """
        return self._last_sandbox_warnings.copy()

    def clear_warnings(self):
        """Clear stored warnings after they've been consumed."""
        self._last_sandbox_warnings = []

    def create_preview(self, code: str) -> tuple:
        """Create preview - route to deletion or creation path.

        For deletion operations (code contains removeObject), highlights
        target objects in red. For creation, executes in sandbox and
        shows green transparent preview.

        Args:
            code: Python code to execute

        Returns:
            Tuple of (success: bool, error_message: str)
        """
        main_doc = FreeCAD.ActiveDocument
        if not main_doc:
            FreeCAD.Console.PrintWarning("AIAssistant: No active document for preview\n")
            return (False, "No active document")

        self._main_doc_name = main_doc.Name
        self._pending_code = code

        # Clear any existing preview
        self.clear_preview()

        # Check if this is a deletion operation
        deletion_targets = self._detect_deletion_targets(code)

        if deletion_targets:
            # Deletion path - red highlight on existing objects
            self._is_deletion = True
            return self._create_deletion_preview(deletion_targets)
        else:
            # Creation path - sandbox execution
            self._is_deletion = False
            return self._create_sandbox_preview(code)

    def _detect_deletion_targets(self, code: str) -> List[str]:
        """Parse code to find objects targeted for deletion.

        Args:
            code: Python code to analyze

        Returns:
            List of object names to be deleted, or empty if not deletion
        """
        targets = []
        for pattern in _DELETION_PATTERNS:
            matches = re.findall(pattern, code)
            if matches:
                FreeCAD.Console.PrintMessage(
                    f"AIAssistant: Pattern '{pattern}' matched: {matches}\n"
                )
            targets.extend(matches)
        result = list(set(targets))  # dedupe
        if result:
            FreeCAD.Console.PrintMessage(
                f"AIAssistant: Detected deletion targets: {result}\n"
            )
        return result

    def _create_deletion_preview(self, target_names: List[str]) -> tuple:
        """Create deletion preview by highlighting target objects in red.

        Args:
            target_names: Object names to be deleted

        Returns:
            Tuple of (success: bool, error_message: str)
        """
        doc = FreeCAD.ActiveDocument
        if not doc:
            return (False, "No active document")

        found = []
        not_found = []

        for name in target_names:
            obj = doc.getObject(name)
            if obj and hasattr(obj, 'ViewObject') and obj.ViewObject:
                # Store original appearance
                vo = obj.ViewObject
                self._deletion_originals[name] = {
                    'color': vo.ShapeColor if hasattr(vo, 'ShapeColor') else None,
                    'transparency': vo.Transparency if hasattr(vo, 'Transparency') else None,
                    'line_color': vo.LineColor if hasattr(vo, 'LineColor') else None,
                }
                # Apply red highlight
                if hasattr(vo, 'ShapeColor'):
                    vo.ShapeColor = DELETION_COLOR
                if hasattr(vo, 'Transparency'):
                    vo.Transparency = DELETION_TRANSPARENCY
                if hasattr(vo, 'LineColor'):
                    vo.LineColor = (0.7, 0.1, 0.1)  # Dark red edges
                found.append(name)
            else:
                not_found.append(name)

        self._deletion_targets = found

        if not found:
            msg = f"Objects not found: {', '.join(not_found)}"
            FreeCAD.Console.PrintWarning(f"AIAssistant: {msg}\n")
            return (False, msg)

        FreeCAD.Console.PrintMessage(
            f"AIAssistant: Created deletion preview for {len(found)} objects\n"
        )

        if not_found:
            # Partial success - some objects found, some not
            FreeCAD.Console.PrintWarning(
                f"AIAssistant: Objects not found: {', '.join(not_found)}\n"
            )

        return (True, "")

    def _create_sandbox_preview(self, code: str) -> tuple:
        """Execute code in temp doc and show preview in main doc.

        The sandbox first runs source.py to establish the baseline state,
        then runs the LLM's new code on top. This ensures variables from
        source.py (like `width`, `length`) are available.

        Only NEW objects (created by LLM code) are shown as green preview.

        Args:
            code: Python code to execute

        Returns:
            Tuple of (success: bool, error_message: str)
        """
        # Create temporary document
        try:
            self._temp_doc = FreeCAD.newDocument("__AIPreview__", hidden=True)
        except TypeError:
            # Older FreeCAD versions may not support hidden parameter
            self._temp_doc = FreeCAD.newDocument("__AIPreview__")

        try:
            # Build execution environment for temp doc
            exec_globals = _build_sandbox_globals(self._temp_doc)

            # Temporarily set temp doc as active
            FreeCAD.setActiveDocument(self._temp_doc.Name)

            try:
                # STEP 1: Run source.py first to establish baseline
                # This makes variables like `width`, `length` available to LLM code
                from . import SourceManager
                source_content = SourceManager.read_source()

                baseline_objects = set()
                if source_content and source_content.strip():
                    FreeCAD.Console.PrintMessage(
                        "AIAssistant: Running source.py in sandbox to establish baseline...\n"
                    )
                    exec(source_content, exec_globals)
                    self._temp_doc.recompute()
                    # Record baseline objects (from source.py)
                    baseline_objects = set(
                        obj.Name for obj in self._temp_doc.Objects
                        if obj.TypeId not in ("App::Origin", "App::Plane", "App::Line")
                    )
                    FreeCAD.Console.PrintMessage(
                        f"AIAssistant: Baseline has {len(baseline_objects)} objects\n"
                    )

                # STEP 2: Run LLM's new code on top of baseline
                exec(code, exec_globals)
                self._temp_doc.recompute()

            finally:
                # ALWAYS restore original active document, even on failure
                if self._main_doc_name and FreeCAD.getDocument(self._main_doc_name):
                    FreeCAD.setActiveDocument(self._main_doc_name)

            # Validate geometry - catch "silent" failures
            validation_errors = []
            for obj in self._temp_doc.Objects:
                if obj.TypeId in ("App::Origin", "App::Plane", "App::Line"):
                    continue
                if hasattr(obj, 'State') and 'Touched' in obj.State:
                    validation_errors.append(
                        f"Object '{obj.Label}' ({obj.Name}) failed to compute"
                    )
                if hasattr(obj, 'Shape'):
                    shape = obj.Shape
                    if shape is None or shape.isNull():
                        validation_errors.append(
                            f"Object '{obj.Label}' ({obj.Name}) has null shape"
                        )
                    elif not shape.isValid():
                        validation_errors.append(
                            f"Object '{obj.Label}' ({obj.Name}) has invalid geometry"
                        )

            if validation_errors:
                error_msg = "Geometry validation failed:\n" + "\n".join(validation_errors)
                FreeCAD.Console.PrintError(f"AIAssistant: {error_msg}\n")
                self.clear_preview()
                return (False, error_msg)

            # STEP 3: Identify NEW objects (created by LLM code, not in baseline)
            all_objects = set(
                obj.Name for obj in self._temp_doc.Objects
                if obj.TypeId not in ("App::Origin", "App::Plane", "App::Line")
            )
            new_objects = all_objects - baseline_objects

            main_doc = FreeCAD.ActiveDocument

            # Copy only NEW shapes (from LLM code) to main doc as preview
            preview_count = 0
            for obj in self._temp_doc.Objects:
                # Skip origin objects
                if obj.TypeId in ("App::Origin", "App::Plane", "App::Line"):
                    continue

                # Only preview objects created by LLM code, not baseline from source.py
                if obj.Name not in new_objects:
                    continue

                if hasattr(obj, 'Shape') and obj.Shape and not obj.Shape.isNull():
                    self._add_preview_shape(main_doc, obj)
                    preview_count += 1

            main_doc.recompute()

            # Fit view to show preview
            try:
                if FreeCADGui.ActiveDocument and FreeCADGui.ActiveDocument.ActiveView:
                    FreeCADGui.ActiveDocument.ActiveView.fitAll()
            except Exception:
                pass

            FreeCAD.Console.PrintMessage(f"AIAssistant: Created preview with {preview_count} objects\n")

            if preview_count > 0:
                return (True, "")
            else:
                return (False, "No preview objects created - code may not produce visible geometry")

        except Exception as e:
            import traceback
            error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            FreeCAD.Console.PrintError(f"AIAssistant: Preview failed: {e}\n")
            self.clear_preview()
            return (False, error_msg)

    def _add_preview_shape(self, doc, source_obj):
        """Add a preview shape to main document.

        Args:
            doc: Target document (main doc)
            source_obj: Source object from temp doc
        """
        try:
            preview_name = f"__preview_{source_obj.Name}"
            preview = doc.addObject("Part::Feature", preview_name)
            preview.Shape = source_obj.Shape.copy()
            preview.Label = f"[Preview] {source_obj.Label}"

            # Style as green transparent
            if hasattr(preview, 'ViewObject') and preview.ViewObject:
                preview.ViewObject.ShapeColor = PREVIEW_COLOR
                preview.ViewObject.Transparency = PREVIEW_TRANSPARENCY
                preview.ViewObject.DisplayMode = "Shaded"
                # Make slightly darker line color for edges
                preview.ViewObject.LineColor = (0.0, 0.7, 0.2)

            self._preview_objects.append(preview_name)

        except Exception as e:
            FreeCAD.Console.PrintWarning(f"AIAssistant: Failed to add preview for {source_obj.Name}: {e}\n")

    def clear_preview(self):
        """Remove all preview objects and restore deletion highlights."""
        # Clear creation preview objects
        if self._main_doc_name:
            try:
                doc = FreeCAD.getDocument(self._main_doc_name)
                if doc:
                    for name in self._preview_objects:
                        if doc.getObject(name):
                            doc.removeObject(name)
                    doc.recompute()
            except Exception as e:
                FreeCAD.Console.PrintWarning(f"AIAssistant: Error clearing preview: {e}\n")

        self._preview_objects = []

        # Clear deletion preview (restore original appearance)
        self._clear_deletion_preview()

        # Close temp document
        if self._temp_doc:
            try:
                FreeCAD.closeDocument(self._temp_doc.Name)
            except Exception:
                pass
            self._temp_doc = None

    def _clear_deletion_preview(self):
        """Restore original appearance of deletion-highlighted objects."""
        doc = FreeCAD.ActiveDocument
        if not doc:
            self._deletion_originals = {}
            self._deletion_targets = []
            self._modified_names = []
            return

        for name, original in self._deletion_originals.items():
            obj = doc.getObject(name)
            if obj and hasattr(obj, 'ViewObject') and obj.ViewObject:
                vo = obj.ViewObject
                if original.get('color') and hasattr(vo, 'ShapeColor'):
                    vo.ShapeColor = original['color']
                if original.get('transparency') is not None and hasattr(vo, 'Transparency'):
                    vo.Transparency = original['transparency']
                if original.get('line_color') and hasattr(vo, 'LineColor'):
                    vo.LineColor = original['line_color']

        self._deletion_originals = {}
        self._deletion_targets = []
        self._modified_names = []
        self._is_deletion = False

    def approve(self) -> str:
        """Approve preview - clear preview and return code for real execution.

        Returns:
            The code to execute for real
        """
        code = self._pending_code
        self.clear_preview()
        self._pending_code = ""
        return code

    def cancel(self):
        """Cancel preview - clear preview without executing."""
        self.clear_preview()
        self._pending_code = ""
        FreeCAD.Console.PrintMessage("AIAssistant: Preview cancelled\n")

    def get_preview_summary(self) -> List[Dict]:
        """Get list of objects that will be created or deleted.

        Returns:
            List of dicts with name, label, type for each object
        """
        # For deletion preview, return info about objects to be deleted
        if self._is_deletion and self._deletion_targets:
            return self._get_deletion_summary()

        # For creation preview, return info from temp doc
        if not self._temp_doc:
            return []

        result = []
        for obj in self._temp_doc.Objects:
            # Skip origin objects
            if obj.TypeId in ("App::Origin", "App::Plane", "App::Line"):
                continue

            # Get human-readable type
            type_name = obj.TypeId.split("::")[-1] if "::" in obj.TypeId else obj.TypeId

            # Get dimensions if it's a shape
            dimensions = {}
            if hasattr(obj, 'Shape') and obj.Shape and not obj.Shape.isNull():
                bbox = obj.Shape.BoundBox
                dimensions = {
                    "width": round(bbox.XLength, 2),
                    "depth": round(bbox.YLength, 2),
                    "height": round(bbox.ZLength, 2),
                }

            result.append({
                "name": obj.Name,
                "label": obj.Label,
                "type": type_name,
                "dimensions": dimensions
            })

        return result

    def _get_deletion_summary(self) -> List[Dict]:
        """Get summary of objects to be deleted.

        Returns:
            List of dicts with name, label, type for each deletion target
        """
        doc = FreeCAD.ActiveDocument
        if not doc:
            return []

        result = []
        for name in self._deletion_targets:
            obj = doc.getObject(name)
            if obj:
                # Get human-readable type
                type_name = obj.TypeId.split("::")[-1] if "::" in obj.TypeId else obj.TypeId

                # Get dimensions if it's a shape
                dimensions = {}
                if hasattr(obj, 'Shape') and obj.Shape and not obj.Shape.isNull():
                    bbox = obj.Shape.BoundBox
                    dimensions = {
                        "width": round(bbox.XLength, 2),
                        "depth": round(bbox.YLength, 2),
                        "height": round(bbox.ZLength, 2),
                    }

                result.append({
                    "name": obj.Name,
                    "label": obj.Label,
                    "type": type_name,
                    "dimensions": dimensions
                })

        return result

    # =========================================================================
    # Direct Source Editing - Diff Preview
    # =========================================================================

    def _shapes_equal(self, shape1, shape2) -> bool:
        """Compare two shapes for equality.

        Uses volume and bounding box as a fast heuristic. Two shapes are
        considered equal if they have the same volume (within tolerance)
        and the same bounding box dimensions.

        Args:
            shape1: First Part.Shape
            shape2: Second Part.Shape

        Returns:
            True if shapes appear to be identical
        """
        if shape1 is None or shape2 is None:
            return shape1 is shape2

        if shape1.isNull() or shape2.isNull():
            return shape1.isNull() and shape2.isNull()

        # Compare volume (with tolerance for floating point)
        vol1 = shape1.Volume
        vol2 = shape2.Volume
        vol_tolerance = max(abs(vol1), abs(vol2)) * 1e-6 + 1e-9
        if abs(vol1 - vol2) > vol_tolerance:
            return False

        # Compare bounding box dimensions
        bb1 = shape1.BoundBox
        bb2 = shape2.BoundBox

        dim_tolerance = 1e-6
        if (abs(bb1.XLength - bb2.XLength) > dim_tolerance or
            abs(bb1.YLength - bb2.YLength) > dim_tolerance or
            abs(bb1.ZLength - bb2.ZLength) > dim_tolerance):
            return False

        # Compare bounding box position (center)
        center1 = bb1.Center
        center2 = bb2.Center
        pos_tolerance = 1e-6
        if (abs(center1.x - center2.x) > pos_tolerance or
            abs(center1.y - center2.y) > pos_tolerance or
            abs(center1.z - center2.z) > pos_tolerance):
            return False

        return True

    def create_diff_preview(self, old_source: str, new_source: str) -> tuple:
        """Create preview showing diff between old and new source.py.

        Executes both versions in sandbox, compares resulting objects:
        - Objects in OLD but not NEW = deleted (red highlight in main doc)
        - Objects in NEW but not OLD = created (green preview)
        - Objects in BOTH but with different geometry = modified (red old + green new)

        Used for direct source editing flow where Claude edits source.py.

        Args:
            old_source: Previous source.py content (from backup)
            new_source: New source.py content (after Claude's edit)

        Returns:
            Tuple of (success: bool, error_message: str)
        """
        main_doc = FreeCAD.ActiveDocument
        if not main_doc:
            FreeCAD.Console.PrintWarning("AIAssistant: No active document for preview\n")
            return (False, "No active document")

        self._main_doc_name = main_doc.Name
        self._pending_code = new_source  # Store new source for execution on approve

        # Clear any existing preview
        self.clear_preview()

        try:
            # Execute OLD source in sandbox
            FreeCAD.Console.PrintMessage(
                "AIAssistant: Executing old source.py in sandbox...\n"
            )
            old_objects, old_shapes, old_error, old_warnings = self._execute_source_in_sandbox(old_source)
            if old_error:
                # Old source failed - this shouldn't happen normally
                FreeCAD.Console.PrintWarning(
                    f"AIAssistant: Old source.py failed (unusual): {old_error[:100]}...\n"
                )
            FreeCAD.Console.PrintMessage(
                f"AIAssistant: Old source objects: {sorted(old_objects)}\n"
            )

            # Execute NEW source in sandbox
            FreeCAD.Console.PrintMessage(
                "AIAssistant: Executing new source.py in sandbox...\n"
            )
            new_objects, new_shapes, new_error, new_warnings = self._execute_source_in_sandbox(new_source)
            if new_error:
                # New source failed - return error so AIPanel can request fix from Claude
                FreeCAD.Console.PrintError(
                    f"AIAssistant: New source.py execution failed\n"
                )
                return (False, f"EXECUTION_ERROR:{new_error}")
            FreeCAD.Console.PrintMessage(
                f"AIAssistant: New source objects: {sorted(new_objects)}\n"
            )

            # Store warnings from new source execution for agentic learning
            # (these will be fed back to Claude on next request)
            self._last_sandbox_warnings = new_warnings

            # Compute diff
            deleted_names = old_objects - new_objects  # Objects removed
            created_names = new_objects - old_objects  # Objects added
            common_names = old_objects & new_objects   # Objects in both

            # Detect modifications: same name but different geometry
            modified_names = set()
            for name in common_names:
                old_shape = old_shapes.get(name)
                new_shape = new_shapes.get(name)
                if not self._shapes_equal(old_shape, new_shape):
                    modified_names.add(name)

            # Store for later access
            self._modified_names = list(modified_names)

            FreeCAD.Console.PrintMessage(
                f"AIAssistant: Diff - {len(deleted_names)} deleted ({list(deleted_names)}), "
                f"{len(created_names)} created ({list(created_names)}), "
                f"{len(modified_names)} modified ({list(modified_names)})\n"
            )

            # Show deleted objects as red highlight in main doc
            for obj_name in deleted_names:
                obj = main_doc.getObject(obj_name)
                if obj and hasattr(obj, 'ViewObject') and obj.ViewObject:
                    vo = obj.ViewObject
                    # Store original appearance
                    self._deletion_originals[obj_name] = {
                        'color': vo.ShapeColor if hasattr(vo, 'ShapeColor') else None,
                        'transparency': vo.Transparency if hasattr(vo, 'Transparency') else None,
                        'line_color': vo.LineColor if hasattr(vo, 'LineColor') else None,
                    }
                    # Apply red highlight
                    if hasattr(vo, 'ShapeColor'):
                        vo.ShapeColor = DELETION_COLOR
                    if hasattr(vo, 'Transparency'):
                        vo.Transparency = DELETION_TRANSPARENCY
                    if hasattr(vo, 'LineColor'):
                        vo.LineColor = (0.7, 0.1, 0.1)
                    self._deletion_targets.append(obj_name)

            # Show created objects as green preview
            for obj_name in created_names:
                if obj_name in new_shapes:
                    shape = new_shapes[obj_name]
                    if shape and not shape.isNull():
                        self._add_preview_shape_direct(main_doc, obj_name, shape)

            # Show modified objects: red highlight on old (in main doc) + green preview of new
            for obj_name in modified_names:
                # Highlight old shape in red (will be replaced)
                obj = main_doc.getObject(obj_name)
                if obj and hasattr(obj, 'ViewObject') and obj.ViewObject:
                    vo = obj.ViewObject
                    # Store original appearance
                    self._deletion_originals[obj_name] = {
                        'color': vo.ShapeColor if hasattr(vo, 'ShapeColor') else None,
                        'transparency': vo.Transparency if hasattr(vo, 'Transparency') else None,
                        'line_color': vo.LineColor if hasattr(vo, 'LineColor') else None,
                    }
                    # Apply red highlight (being replaced)
                    if hasattr(vo, 'ShapeColor'):
                        vo.ShapeColor = DELETION_COLOR
                    if hasattr(vo, 'Transparency'):
                        vo.Transparency = DELETION_TRANSPARENCY
                    if hasattr(vo, 'LineColor'):
                        vo.LineColor = (0.7, 0.1, 0.1)
                    self._deletion_targets.append(obj_name)

                # Show new shape as green preview
                if obj_name in new_shapes:
                    new_shape = new_shapes[obj_name]
                    if new_shape and not new_shape.isNull():
                        self._add_preview_shape_direct(main_doc, obj_name, new_shape)

            self._is_deletion = len(deleted_names) > 0 or len(modified_names) > 0

            main_doc.recompute()

            # Fit view
            try:
                if FreeCADGui.ActiveDocument and FreeCADGui.ActiveDocument.ActiveView:
                    FreeCADGui.ActiveDocument.ActiveView.fitAll()
            except Exception:
                pass

            total_changes = len(deleted_names) + len(created_names) + len(modified_names)
            if total_changes > 0:
                FreeCAD.Console.PrintMessage(
                    f"AIAssistant: Created diff preview ({len(deleted_names)} deleted, "
                    f"{len(created_names)} created, {len(modified_names)} modified)\n"
                )
                return (True, "")
            else:
                return (False, "No changes detected between old and new source.py")

        except Exception as e:
            import traceback
            error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            FreeCAD.Console.PrintError(f"AIAssistant: Diff preview failed: {e}\n")
            self.clear_preview()
            return (False, error_msg)

    def _execute_source_in_sandbox(self, source_code: str) -> Tuple[set, Dict, str, List[str]]:
        """Execute source code in temp doc, return object names and shapes.

        Args:
            source_code: Python source code to execute

        Returns:
            Tuple of (object_names: set, shapes: dict mapping name -> Shape, error: str, warnings: list)
            If execution fails, error contains the full traceback.
            warnings contains any deprecation or other warnings captured during execution.
        """
        import traceback
        from .executor import WarningCapture

        temp_doc = None
        try:
            temp_doc = FreeCAD.newDocument("__AIDiffSandbox__", hidden=True)
        except TypeError:
            temp_doc = FreeCAD.newDocument("__AIDiffSandbox__")

        try:
            # Build execution environment
            exec_globals = _build_sandbox_globals(temp_doc)

            # Execute source with warning capture
            FreeCAD.setActiveDocument(temp_doc.Name)
            warnings = []
            try:
                with WarningCapture() as capture:
                    exec(source_code, exec_globals)
                    temp_doc.recompute()
                warnings = capture.warnings
            except Exception as exec_error:
                error_msg = f"{type(exec_error).__name__}: {exec_error}\n{traceback.format_exc()}"
                FreeCAD.Console.PrintError(
                    f"AIAssistant: Sandbox exec failed: {exec_error}\n"
                )
                # Return empty set with error message
                return set(), {}, error_msg, []
            finally:
                if self._main_doc_name and FreeCAD.getDocument(self._main_doc_name):
                    FreeCAD.setActiveDocument(self._main_doc_name)

            # Validate geometry - catch "silent" failures where objects are created
            # but have invalid shapes (common with Arch module)
            validation_errors = []
            for obj in temp_doc.Objects:
                if obj.TypeId in ("App::Origin", "App::Plane", "App::Line"):
                    continue
                # Check for objects that need recompute (State contains "Touched")
                if hasattr(obj, 'State') and 'Touched' in obj.State:
                    validation_errors.append(
                        f"Object '{obj.Label}' ({obj.Name}) failed to compute (still Touched after recompute)"
                    )
                # Check for invalid shapes
                if hasattr(obj, 'Shape'):
                    shape = obj.Shape
                    if shape is None or shape.isNull():
                        validation_errors.append(
                            f"Object '{obj.Label}' ({obj.Name}) has null shape"
                        )
                    elif not shape.isValid():
                        validation_errors.append(
                            f"Object '{obj.Label}' ({obj.Name}) has invalid geometry (Shape.isValid() = False)"
                        )
                    elif shape.Volume == 0 and obj.TypeId not in (
                        "Part::Part2DObject", "Sketcher::SketchObject",
                        "Part::Part2DObjectPython", "Draft::Wire"
                    ):
                        # Zero volume for 3D objects is suspicious (might be a failed operation)
                        # But 2D objects like wires/sketches legitimately have zero volume
                        pass  # Don't report - some valid objects have zero volume

            if validation_errors:
                error_msg = "Geometry validation failed:\n" + "\n".join(validation_errors)
                FreeCAD.Console.PrintError(f"AIAssistant: {error_msg}\n")
                return set(), {}, error_msg, warnings

            # Collect object names and shapes
            object_names = set()
            shapes = {}
            for obj in temp_doc.Objects:
                if obj.TypeId in ("App::Origin", "App::Plane", "App::Line"):
                    continue
                object_names.add(obj.Name)
                if hasattr(obj, 'Shape') and obj.Shape and not obj.Shape.isNull():
                    shapes[obj.Name] = obj.Shape.copy()

            return object_names, shapes, "", warnings

        finally:
            # Close temp doc
            if temp_doc:
                try:
                    FreeCAD.closeDocument(temp_doc.Name)
                except Exception:
                    pass

    def _add_preview_shape_direct(self, doc, name: str, shape):
        """Add a preview shape directly from a Shape object.

        Args:
            doc: Target document (main doc)
            name: Object name for the preview
            shape: Part.Shape to preview
        """
        try:
            preview_name = f"__preview_{name}"
            preview = doc.addObject("Part::Feature", preview_name)
            preview.Shape = shape
            preview.Label = f"[Preview] {name}"

            # Style as green transparent
            if hasattr(preview, 'ViewObject') and preview.ViewObject:
                preview.ViewObject.ShapeColor = PREVIEW_COLOR
                preview.ViewObject.Transparency = PREVIEW_TRANSPARENCY
                preview.ViewObject.DisplayMode = "Shaded"
                preview.ViewObject.LineColor = (0.0, 0.7, 0.2)

            self._preview_objects.append(preview_name)

        except Exception as e:
            FreeCAD.Console.PrintWarning(
                f"AIAssistant: Failed to add preview for {name}: {e}\n"
            )

    def has_preview(self) -> bool:
        """Check if there's an active preview (creation or deletion)."""
        return len(self._preview_objects) > 0 or len(self._deletion_targets) > 0

    def is_deletion_preview(self) -> bool:
        """Check if current preview is a deletion preview."""
        return self._is_deletion

    def is_modification_preview(self) -> bool:
        """Check if current preview includes modifications (same name, different geometry)."""
        return len(self._modified_names) > 0

    def get_modified_names(self) -> List[str]:
        """Get list of object names being modified."""
        return self._modified_names.copy()

    def get_pending_code(self) -> str:
        """Get the pending code for the current preview."""
        return self._pending_code

    # =========================================================================
    # Sandbox Self-Review Methods
    # =========================================================================

    def create_sandbox_for_review(self, new_source: str) -> Tuple[bool, str, Optional[SandboxReviewSession]]:
        """Create a persistent sandbox for self-review iterations.

        Unlike create_diff_preview(), this keeps the sandbox document alive
        so Claude can iterate and fix issues before the user sees the preview.

        Args:
            new_source: The new source.py content to execute

        Returns:
            Tuple of (success, error_message, session)
            - success: True if sandbox was created and code executed
            - error_message: Error details if failed (EXECUTION_ERROR: prefix for code errors)
            - session: SandboxReviewSession object if successful, None otherwise
        """
        import traceback
        from .executor import WarningCapture

        main_doc = FreeCAD.ActiveDocument
        if not main_doc:
            return (False, "No active document", None)

        self._main_doc_name = main_doc.Name
        self._pending_code = new_source

        # Create session
        session = SandboxReviewSession(
            main_doc_name=main_doc.Name,
            source_content=new_source,
            is_active=True,
        )

        # Create sandbox document (NOT hidden - we need GUI view for screenshots)
        # The sandbox will be visible briefly during self-review, but that's necessary
        # for capturing screenshots that Claude can review
        sandbox_doc = FreeCAD.newDocument("__AISelfReviewSandbox__")

        session.sandbox_doc_name = sandbox_doc.Name

        # Execute source in sandbox
        try:
            exec_globals = _build_sandbox_globals(sandbox_doc)

            # Execute with warning capture
            FreeCAD.setActiveDocument(sandbox_doc.Name)
            try:
                with WarningCapture() as capture:
                    exec(new_source, exec_globals)
                    sandbox_doc.recompute()
                self._last_sandbox_warnings = capture.warnings
            except Exception as exec_error:
                error_msg = f"EXECUTION_ERROR:{type(exec_error).__name__}: {exec_error}\n{traceback.format_exc()}"
                FreeCAD.Console.PrintError(f"AIAssistant: Sandbox exec failed: {exec_error}\n")
                self.close_sandbox(session)
                return (False, error_msg, None)
            finally:
                if self._main_doc_name and FreeCAD.getDocument(self._main_doc_name):
                    FreeCAD.setActiveDocument(self._main_doc_name)

            # Validate geometry - catch "silent" failures
            validation_errors = []
            for obj in sandbox_doc.Objects:
                if obj.TypeId in ("App::Origin", "App::Plane", "App::Line"):
                    continue
                if hasattr(obj, 'State') and 'Touched' in obj.State:
                    validation_errors.append(
                        f"Object '{obj.Label}' ({obj.Name}) failed to compute"
                    )
                if hasattr(obj, 'Shape'):
                    shape = obj.Shape
                    if shape is None or shape.isNull():
                        validation_errors.append(
                            f"Object '{obj.Label}' ({obj.Name}) has null shape"
                        )
                    elif not shape.isValid():
                        validation_errors.append(
                            f"Object '{obj.Label}' ({obj.Name}) has invalid geometry"
                        )

            if validation_errors:
                error_msg = f"EXECUTION_ERROR:Geometry validation failed:\n" + "\n".join(validation_errors)
                FreeCAD.Console.PrintError(f"AIAssistant: {error_msg}\n")
                self.close_sandbox(session)
                return (False, error_msg, None)

            # Collect shapes from sandbox
            for obj in sandbox_doc.Objects:
                if obj.TypeId in ("App::Origin", "App::Plane", "App::Line"):
                    continue
                if hasattr(obj, 'Shape') and obj.Shape and not obj.Shape.isNull():
                    session.object_shapes[obj.Name] = {
                        'shape': obj.Shape.copy(),
                        'label': obj.Label,
                    }

            FreeCAD.Console.PrintMessage(
                f"AIAssistant: Sandbox created with {len(session.object_shapes)} objects\n"
            )

            return (True, "", session)

        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
            FreeCAD.Console.PrintError(f"AIAssistant: Failed to create sandbox: {e}\n")
            self.close_sandbox(session)
            return (False, error_msg, None)

    def re_execute_in_sandbox(self, session: SandboxReviewSession, new_source: str) -> Tuple[bool, str]:
        """Re-execute source in existing sandbox after Claude made edits.

        Clears all objects in the sandbox and re-executes with new source.

        Args:
            session: Active sandbox session
            new_source: Updated source.py content

        Returns:
            Tuple of (success, error_message)
        """
        import traceback
        from .executor import WarningCapture

        if not session or not session.is_active:
            return (False, "No active sandbox session")

        sandbox_doc = FreeCAD.getDocument(session.sandbox_doc_name)
        if not sandbox_doc:
            return (False, f"Sandbox document {session.sandbox_doc_name} not found")

        # Clear existing objects
        objects_to_remove = [
            obj.Name for obj in sandbox_doc.Objects
            if obj.TypeId not in ("App::Origin", "App::Plane", "App::Line")
        ]
        for obj_name in objects_to_remove:
            try:
                sandbox_doc.removeObject(obj_name)
            except Exception:
                pass

        session.object_shapes.clear()
        session.source_content = new_source
        session.iteration += 1

        # Re-execute
        try:
            exec_globals = _build_sandbox_globals(sandbox_doc)

            FreeCAD.setActiveDocument(sandbox_doc.Name)
            try:
                with WarningCapture() as capture:
                    exec(new_source, exec_globals)
                    sandbox_doc.recompute()
                self._last_sandbox_warnings = capture.warnings
            except Exception as exec_error:
                error_msg = f"EXECUTION_ERROR:{type(exec_error).__name__}: {exec_error}\n{traceback.format_exc()}"
                return (False, error_msg)
            finally:
                if self._main_doc_name and FreeCAD.getDocument(self._main_doc_name):
                    FreeCAD.setActiveDocument(self._main_doc_name)

            # Validate geometry - catch "silent" failures
            validation_errors = []
            for obj in sandbox_doc.Objects:
                if obj.TypeId in ("App::Origin", "App::Plane", "App::Line"):
                    continue
                if hasattr(obj, 'State') and 'Touched' in obj.State:
                    validation_errors.append(
                        f"Object '{obj.Label}' ({obj.Name}) failed to compute"
                    )
                if hasattr(obj, 'Shape'):
                    shape = obj.Shape
                    if shape is None or shape.isNull():
                        validation_errors.append(
                            f"Object '{obj.Label}' ({obj.Name}) has null shape"
                        )
                    elif not shape.isValid():
                        validation_errors.append(
                            f"Object '{obj.Label}' ({obj.Name}) has invalid geometry"
                        )

            if validation_errors:
                error_msg = f"EXECUTION_ERROR:Geometry validation failed:\n" + "\n".join(validation_errors)
                FreeCAD.Console.PrintError(f"AIAssistant: {error_msg}\n")
                return (False, error_msg)

            # Collect shapes
            for obj in sandbox_doc.Objects:
                if obj.TypeId in ("App::Origin", "App::Plane", "App::Line"):
                    continue
                if hasattr(obj, 'Shape') and obj.Shape and not obj.Shape.isNull():
                    session.object_shapes[obj.Name] = {
                        'shape': obj.Shape.copy(),
                        'label': obj.Label,
                    }

            FreeCAD.Console.PrintMessage(
                f"AIAssistant: Re-executed sandbox (iteration {session.iteration}), "
                f"{len(session.object_shapes)} objects\n"
            )

            return (True, "")

        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
            return (False, error_msg)

    def commit_sandbox_to_preview(self, session: SandboxReviewSession) -> bool:
        """Create green preview shapes in main doc from sandbox objects.

        Called after self-review is complete to show the final result to user.

        Args:
            session: Sandbox session with collected shapes

        Returns:
            True if preview was created successfully
        """
        if not session or not session.object_shapes:
            return False

        main_doc = FreeCAD.getDocument(session.main_doc_name)
        if not main_doc:
            return False

        # Clear any existing preview
        self.clear_preview()

        # Store pending code for approval handler
        self._pending_code = session.source_content
        self._main_doc_name = session.main_doc_name

        # Create preview shapes
        preview_count = 0
        for name, data in session.object_shapes.items():
            try:
                preview_name = f"__preview_{name}"
                preview = main_doc.addObject("Part::Feature", preview_name)
                preview.Shape = data['shape']
                preview.Label = f"[Preview] {data['label']}"

                if hasattr(preview, 'ViewObject') and preview.ViewObject:
                    preview.ViewObject.ShapeColor = PREVIEW_COLOR
                    preview.ViewObject.Transparency = PREVIEW_TRANSPARENCY
                    preview.ViewObject.DisplayMode = "Shaded"
                    preview.ViewObject.LineColor = (0.0, 0.7, 0.2)

                self._preview_objects.append(preview_name)
                preview_count += 1
            except Exception as e:
                FreeCAD.Console.PrintWarning(
                    f"AIAssistant: Failed to create preview for {name}: {e}\n"
                )

        main_doc.recompute()

        # Fit view
        try:
            if FreeCADGui.ActiveDocument and FreeCADGui.ActiveDocument.ActiveView:
                FreeCADGui.ActiveDocument.ActiveView.fitAll()
        except Exception:
            pass

        FreeCAD.Console.PrintMessage(
            f"AIAssistant: Created preview with {preview_count} objects from sandbox\n"
        )

        return preview_count > 0

    def close_sandbox(self, session: Optional[SandboxReviewSession]) -> None:
        """Close sandbox document and clean up session.

        Args:
            session: Sandbox session to close
        """
        if not session:
            return

        session.is_active = False

        if session.sandbox_doc_name:
            try:
                sandbox_doc = FreeCAD.getDocument(session.sandbox_doc_name)
                if sandbox_doc:
                    FreeCAD.closeDocument(session.sandbox_doc_name)
                    FreeCAD.Console.PrintMessage(
                        f"AIAssistant: Closed sandbox {session.sandbox_doc_name}\n"
                    )
            except Exception as e:
                FreeCAD.Console.PrintWarning(
                    f"AIAssistant: Failed to close sandbox: {e}\n"
                )

        session.object_shapes.clear()
        session.preview_objects.clear()

    def get_sandbox_doc(self, session: SandboxReviewSession) -> Optional[Any]:
        """Get the sandbox document for screenshot capture.

        Args:
            session: Active sandbox session

        Returns:
            FreeCAD.Document or None
        """
        if not session or not session.is_active:
            return None
        return FreeCAD.getDocument(session.sandbox_doc_name)
