# FreeCAD Drawing Project

## Structure
Drawing set is organized as per-page Python scripts:
- `pages/_shared.py` — Shared constants (grid dims, materials). Executed first.
- `pages/NNN_name.py` — One script per drawing sheet (e.g., 001_cover.py, 002_notes.py).

## Rules
- Edit ONE page per request (plus _shared.py if needed for shared constants)
- Each page creates ONE TechDraw::DrawPage (drawing sheet)
- Object Names must be globally unique — prefix with page number (e.g., P005_WireGrid)
- New pages: use next number prefix (e.g., 005_foundation_F1.py)
- All dimensions in millimeters
- End each page with `doc.recompute()`
- Use descriptive Labels for all objects
- Coordinate system: X = right, Y = up (2D plan view)

## Conventions
- Rebar notation: "Ø12 A500c ბიჯი 200" (diameter, grade, spacing)
- Grid axes: A, B, C... for columns; 1, 2, 3... for rows

## Drawing Tools
- **Draft**: make_wire, make_circle, make_rectangle, make_text, make_label, make_linear_dimension, make_hatch
- **TechDraw**: DrawPage + DrawSVGTemplate for sheets, DrawViewDraft for placing Draft views
- **Spreadsheet**: Sheet for bar bending schedules and tables

## TechDraw Setup
Template path: `FreeCAD.getResourceDir() + "Mod/TechDraw/Templates/ISO/<template>.svg"`
Common templates: A3_Landscape_TD.svg, A4_Landscape_TD.svg, A3_Landscape_blank.svg

## Important API Notes
- `Draft.make_circle(radius, placement)` — 2nd arg MUST be `FreeCAD.Placement`, NOT a `Vector`
- `Draft.make_linear_dimension()` ViewObject has NO `ArrowSize` attribute
- Use your training knowledge for FreeCAD APIs. Do NOT search the source code unless code fails to execute.
