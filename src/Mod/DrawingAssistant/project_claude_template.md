# FreeCAD Drawing Project

## Execution Model
All `*.py` files in `pages/` are executed together as one script.
Execution order: underscore-prefixed files first, then alphabetical.

## Rules for code
- All dimensions in millimeters
- End each script with `doc.recompute()`
- Coordinate system: X = right, Y = up (2D plan view)

## Drawing Tools
- **Draft**: make_wire, make_circle, make_rectangle, make_text, make_label, make_linear_dimension, make_hatch
- **TechDraw**: DrawPage + DrawSVGTemplate for sheets, DrawViewDraft for placing Draft views
- **Spreadsheet**: Sheet for tables and schedules

## TechDraw Setup
Template path: `FreeCAD.getResourceDir() + "Mod/TechDraw/Templates/ISO/<template>.svg"`
Common templates: A3_Landscape_TD.svg, A4_Landscape_TD.svg, A3_Landscape_blank.svg

## Important API Notes
- `Draft.make_circle(radius, placement)` — 2nd arg MUST be `FreeCAD.Placement`, NOT a `Vector`
- `Draft.make_linear_dimension()` ViewObject has NO `ArrowSize` attribute
- Object `.Name` is read-only after creation — set only via `doc.addObject("Type", "Name")`
- Delete objects in reverse order (`reversed(doc.Objects)`) to avoid crashes
- Use your training knowledge for FreeCAD APIs. Do NOT search the source code unless code fails to execute.
