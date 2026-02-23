# FreeCAD Drawing Project

## Project Context
- `project.md` contains engineer-provided project notes (naming conventions, materials, rules). Follow these when creating drawings.

## Execution Model
All `*.py` files in `pages/` are executed together.
Execution order: underscore-prefixed files first, then alphabetical.
The system clears all objects before re-executing a file — do NOT use
idempotent patterns. Just create objects directly.

## Rules for code
- All dimensions in millimeters
- End each script with `doc.recompute()`
- Coordinate system: X = right, Y = up (2D plan view)
- The system provides `SHEET_Y_OFFSET` — use it as the base Y for all geometry so different sheets don't overlap in Draft space. Offset groups along X by ≥15000mm within a file. E.g. plan at (0, SHEET_Y_OFFSET), section at (20000, SHEET_Y_OFFSET).

## File Organization
One file = one complete drawing sheet.

Each file creates ALL geometry, groups, AND views for one sheet:
1. Constants and dimensions at the top
2. Drawing groups (each with unique origin offset ≥15000mm)
3. TechDraw page + template
4. ALL views with coordinated positions and scales
5. `doc.recompute()` at the end

ALWAYS edit the existing file when modifying anything on that sheet.
Only create a new file for a genuinely NEW SHEET.

Use `_helpers.py` for shared utility functions across sheets.
NEVER put TechDraw page/view code in underscore-prefixed files.

## Drawing Tools
- **Draft**: make_wire, make_circle, make_rectangle, make_text, make_label, make_linear_dimension, make_hatch
- **TechDraw**: DrawPage + DrawSVGTemplate for sheets, DrawViewDraft for placing Draft views
- **Spreadsheet**: Sheet for tables and schedules

## TechDraw Setup
Template path: `FreeCAD.getResourceDir() + "Mod/TechDraw/Templates/ISO/<template>.svg"`
DEFAULT template: A3_Landscape_blank.svg (no title block). Use this unless the user requests a title block.
Title block fields (A3/A4_Landscape_TD.svg): `doc.recompute()` first, then `tpl.setEditFieldContent("FieldName", "value")`.
Field names: FC-Title, Subtitle, AuthorName, SupervisorName, CreationDate, CheckDate, scale, Weight, drawing_number, SheetNumber, copyright
Adding Draft views: group ALL Draft objects into `App::DocumentObjectGroup`, then create ONE `DrawViewDraft` with the group as Source. Do NOT create one DrawViewDraft per object (causes overlapping bounding-box frames on the sheet).
IMPORTANT: `page.addView(view)` resets X/Y to page center. ALWAYS set `view.X` and `view.Y` AFTER calling `page.addView(view)`, never before.
Page dimensions available via `page.PageWidth` and `page.PageHeight` (read-only, after recompute).
Page coordinates: origin (0,0) at BOTTOM-LEFT, Y increases UP. Y=0 is the BOTTOM. Title block is at low Y. Safe area for views: X 20–400, Y 50–260 (A3).
Scale to fit: BEFORE setting view.Scale, compute geometry extent and write a comment showing the math. Usable area: A3 ≈ 380×250mm. Standard scales: 1:20, 1:50, 1:100, 1:200, 1:500. Pick the largest that fits.
Text size: `view.FontSize` on DrawViewDraft controls ALL text (Draft FontSizes are IGNORED). Formula: `FontSize = desired_mm / Scale`. Example: 3mm text at 1:20 → FontSize=60. FontSize defines text height in model space — leave enough room for annotations.
Line spacing: ALWAYS set `view.LineSpacing = view.FontSize * 0.7` alongside FontSize. Default LineSpacing=1.0 causes multi-line text overlap.

## Important API Notes
- `Draft.make_circle(radius, placement)` — 2nd arg MUST be `FreeCAD.Placement`, NOT a `Vector`
- `Draft.make_linear_dimension()` ViewObject has NO `ArrowSize` attribute
- Object `.Name` is read-only after creation — set only via `doc.addObject("Type", "Name")`
- Delete objects in reverse order (`reversed(doc.Objects)`) to avoid crashes
- Use your training knowledge for FreeCAD APIs. Do NOT search the source code unless code fails to execute.
