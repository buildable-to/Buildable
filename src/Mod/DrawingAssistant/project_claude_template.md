# FreeCAD Drawing Project

## Execution Model
All `*.py` files in `pages/` are executed together as one script.
Execution order: underscore-prefixed files first, then alphabetical.

## Rules for code
- All dimensions in millimeters
- End each script with `doc.recompute()`
- Coordinate system: X = right, Y = up (2D plan view)

## File Organization
One file = one drawing group = one view on the TechDraw sheet.

Each file should:
1. Create geometry, collect in `draft_objects` list
2. Create `App::DocumentObjectGroup`, set `grp.Group = draft_objects`
3. Get or create TechDraw page (idempotent)
4. Add `DrawViewDraft` for this group (idempotent)

ALWAYS edit an existing file when adding to the same drawing group.
Only create a new file for a genuinely new drawing group.

## Drawing Tools
- **Draft**: make_wire, make_circle, make_rectangle, make_text, make_label, make_linear_dimension, make_hatch
- **TechDraw**: DrawPage + DrawSVGTemplate for sheets, DrawViewDraft for placing Draft views
- **Spreadsheet**: Sheet for tables and schedules

## TechDraw Setup
Template path: `FreeCAD.getResourceDir() + "Mod/TechDraw/Templates/ISO/<template>.svg"`
Common templates: A3_Landscape_TD.svg, A4_Landscape_TD.svg, A3_Landscape_blank.svg
Title block fields (A3/A4_Landscape_TD.svg): `doc.recompute()` first, then `tpl.setEditFieldContent("FieldName", "value")`.
Field names: FC-Title, Subtitle, AuthorName, SupervisorName, CreationDate, CheckDate, scale, Weight, drawing_number, SheetNumber, copyright
Adding Draft views: group ALL Draft objects into `App::DocumentObjectGroup`, then create ONE `DrawViewDraft` with the group as Source. Do NOT create one DrawViewDraft per object (causes overlapping bounding-box frames on the sheet).

## Important API Notes
- `Draft.make_circle(radius, placement)` — 2nd arg MUST be `FreeCAD.Placement`, NOT a `Vector`
- `Draft.make_linear_dimension()` ViewObject has NO `ArrowSize` attribute
- Object `.Name` is read-only after creation — set only via `doc.addObject("Type", "Name")`
- Delete objects in reverse order (`reversed(doc.Objects)`) to avoid crashes
- Use your training knowledge for FreeCAD APIs. Do NOT search the source code unless code fails to execute.
