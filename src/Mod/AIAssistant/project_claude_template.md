# FreeCAD AI Assistant Context

You are helping design a 3D model in FreeCAD.

## Workflow: Direct Source Editing

**source.py** is the single source of truth for this design. It's a Python script that generates the FreeCAD geometry when executed.

**To make design changes:**
1. Read source.py to understand the current design
2. Use the Edit tool to modify source.py directly
3. CREATE objects: Add code to source.py
4. DELETE objects: Remove the relevant code from source.py
5. MODIFY objects: Edit the relevant code in source.py

**Example - to delete an object named "Roof":**
- DO: Use Edit tool to remove the lines that create "Roof" from source.py
- DON'T: Return `doc.removeObject('Roof')` code

**To answer questions (not modify design):**
Return a clear text explanation.

## Code Rules

- Use millimeters for dimensions
- End code with `doc.recompute()`
- Use descriptive Labels for objects
- Use object Names (not Labels) when referencing in code

## PartDesign Best Practices

### Single Body vs Multiple Bodies

**Prefer a single Body when possible.** Features within one Body are automatically positioned relative to each other through the feature chain.

```python
# GOOD: Single body with stacked features
body = doc.addObject("PartDesign::Body", "Building")

# Floor sketch on XY plane
floor_sketch = body.newObject("Sketcher::SketchObject", "FloorSketch")
floor_sketch.AttachmentSupport = [(doc.getObject("XY_Plane"), "")]
floor_sketch.MapMode = "FlatFace"
# ... draw floor rectangle ...

floor_pad = body.newObject("PartDesign::Pad", "Floor")
floor_pad.Profile = floor_sketch
floor_pad.Length = 150

# Wall sketch attached to TOP of floor
wall_sketch = body.newObject("Sketcher::SketchObject", "WallSketch")
wall_sketch.AttachmentSupport = [(floor_pad, "Face6")]  # Top face
wall_sketch.MapMode = "FlatFace"
# ... draw wall profile ...

walls_pad = body.newObject("PartDesign::Pad", "Walls")
walls_pad.Profile = wall_sketch
walls_pad.Length = 4000
```

### When You Must Use Multiple Bodies

If features cannot be in one Body (e.g., different coordinate systems), **set the Body's Placement** to position it correctly:

```python
# Body 2 needs explicit positioning
roof_body = doc.addObject("PartDesign::Body", "RoofBody")
roof_body.Placement = FreeCAD.Placement(
    FreeCAD.Vector(0, 0, wall_height),  # Position at top of walls
    FreeCAD.Rotation(0, 0, 0, 1)
)
```

### Sketch Coordinate Systems

Understanding sketch planes is critical:

| Plane | Sketch X | Sketch Y | 3D Result |
|-------|----------|----------|-----------|
| XY_Plane | X | Y | X-Y plane at Z=0 |
| XZ_Plane | X | Z | X-Z plane at Y=0 |
| YZ_Plane | Y | Z | Y-Z plane at X=0 |

**For a roof profile on the XZ plane:**
- Sketch X = 3D X (along building length)
- Sketch Y = 3D Z (height)
- Extrude direction = 3D Y (building width)

### Attaching Sketches to Existing Geometry

Attach sketches to faces of existing features for automatic positioning:

```python
# Attach to a specific face of an existing pad
sketch.AttachmentSupport = [(existing_pad, "Face6")]
sketch.MapMode = "FlatFace"
doc.recompute()  # IMPORTANT: recompute after setting attachment
```

Face numbering varies by geometry. When unsure, use:
- `Face1` through `Face6` for box-like shapes (typical)
- Top face is usually the highest-numbered face for upward extrusions

### Pad Properties (IMPORTANT - Avoid Deprecated APIs)

**Use SideType instead of Midplane (deprecated):**

```python
# WRONG - Deprecated
pad.Midplane = True  # Will show warning

# CORRECT - Modern API
pad.SideType = "Symmetric"  # Extrude both directions equally

# SideType values:
# "One side" - Extrude in one direction (default)
# "Symmetric" - Extrude equally both directions (replaces Midplane=True)
# "Two sides" - Extrude different amounts each direction
```

### Part Module (Simple Shapes)

For quick prototyping or non-parametric shapes, Part module is simpler:

```python
import Part

# Simple box
box = Part.makeBox(1000, 500, 200)
Part.show(box, "SimpleBox")

# Position with Placement
obj = doc.getObject("SimpleBox")
obj.Placement.Base = FreeCAD.Vector(100, 200, 300)
```

### Boolean Operations (Part Module)

```python
# Union (fuse)
result = shape1.fuse(shape2)

# Subtraction (cut)
result = shape1.cut(shape2)

# Intersection (common)
result = shape1.common(shape2)
```

## When Unsure About FreeCAD API

You have access to the entire FreeCAD codebase. When unsure about API usage:

1. **Search for examples** using Grep to find how an API is used:
   ```
   Grep pattern="makeHelix" path="{{FREECAD_SOURCE}}"
   Grep pattern="makePipe" path="{{FREECAD_SOURCE}}"
   ```

2. **Look at test files** - they contain working examples:
   ```
   Grep pattern="Part.makeBox" path="{{FREECAD_SOURCE}}" glob="*Test*.py"
   Grep pattern="SideType" path="{{FREECAD_SOURCE}}/Mod/PartDesign"
   ```

3. **Check workbench implementations** for complex operations:
   - Part module: `{{FREECAD_SOURCE}}/Mod/Part/`
   - PartDesign module: `{{FREECAD_SOURCE}}/Mod/PartDesign/`
   - Draft module: `{{FREECAD_SOURCE}}/Mod/Draft/`

4. **Common API gotchas to avoid**:
   - Circular edges have only 1 vertex (don't access `edge.Vertexes[1]`)
   - Edge/face indices change after boolean operations
   - Use `edge.Length` and `edge.BoundBox` instead of vertex indices
   - Always `doc.recompute()` after setting AttachmentSupport
   - Use `SideType` not `Midplane` for pad extrusion direction
   - Multiple Bodies need explicit `Placement` to position them

**Always search for working examples before using unfamiliar API calls.**

## Context Files

- **source.py** - The design expressed as Python code (edit this directly)
- **activity.ndjson** - NDJSON log of all interactions (one JSON object per line)
- **snapshots/** - JSON snapshots of document state (objects, geometry)
- **screenshots/** - Viewport images sent with each message
- **sessions/** - Conversation history and LLM debug data
