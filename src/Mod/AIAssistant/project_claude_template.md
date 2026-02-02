# FreeCAD AI Assistant

## Workflow

**source.py** is the single source of truth. Edit it directly to make design changes.

- CREATE: Add code to source.py
- DELETE: Remove code from source.py
- MODIFY: Edit existing code in source.py
- ANSWER: Return text explanation (don't edit)

## Rules

- Units: millimeters
- Always end with `doc.recompute()`
- Use Names (not Labels) when referencing objects in code

## Positioning Objects (CRITICAL)

**Single Body = auto-positioning.** Features in one Body stack automatically via the feature chain.

**Multiple Bodies need explicit Placement:**
```python
roof_body.Placement = FreeCAD.Placement(
    FreeCAD.Vector(0, 0, wall_height),  # Position at top of walls
    FreeCAD.Rotation(0, 0, 0, 1)
)
```

**Attach sketches to existing geometry** for relative positioning:
```python
wall_sketch.AttachmentSupport = [(floor_pad, "Face6")]  # Top face of floor
wall_sketch.MapMode = "FlatFace"
doc.recompute()  # Required after setting attachment
```

**Part module shapes** also need explicit positioning:
```python
roof = Part.makeBox(length, width, height)
roof.translate(FreeCAD.Vector(0, 0, wall_height))
Part.show(roof, "Roof")
```

## API Discovery

When unsure about FreeCAD APIs, **search the source code**:

```
# Find usage examples
Grep pattern="makeHelix" path="{{FREECAD_SOURCE}}/Mod/Part"
Grep pattern="PartDesign::Pad" path="{{FREECAD_SOURCE}}/Mod/PartDesign"

# Check test files for working examples
Glob pattern="**/test*.py" path="{{FREECAD_SOURCE}}/Mod/Part"
```

Key modules:
- Part: `{{FREECAD_SOURCE}}/Mod/Part/`
- PartDesign: `{{FREECAD_SOURCE}}/Mod/PartDesign/`
- Sketcher: `{{FREECAD_SOURCE}}/Mod/Sketcher/`
- Draft: `{{FREECAD_SOURCE}}/Mod/Draft/`

## Known Gotchas

- Use `pad.SideType = "Symmetric"` not `pad.Midplane = True` (deprecated)
- Call `doc.recompute()` after setting `AttachmentSupport`
- Circular edges have 1 vertex, not 2
- Face numbering changes after boolean ops
