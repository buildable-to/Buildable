# FreeCAD Project

This project has two source files. Edit only the one relevant to the current request.

## source.py — 3D Modeling (AI Assistant)
Edit source.py for 3D geometry: Part, PartDesign, Arch, BIM solids.
Coordinate system: X = right, Y = forward, Z = up (right-handed).

## drawing.py — 2D Drawings (Drawing Assistant)
Edit drawing.py for 2D structural drawings: Draft wires, dimensions, TechDraw pages, Spreadsheets.
Coordinate system: X = right, Y = up (2D plan view). Z is ignored.

## Conventions
- All dimensions in millimeters
- End scripts with `doc.recompute()`
- Use descriptive Labels for objects
- Rebar notation: "Ø12 A500c ბიჯი 200" (diameter, grade, spacing)
- Grid axes: A, B, C... for columns; 1, 2, 3... for rows

## Drawing Tools (drawing.py only)
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
