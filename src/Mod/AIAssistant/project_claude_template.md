# FreeCAD AI Assistant Context

You are helping design a 3D model in FreeCAD.

## STEP 1: Classify the Task FIRST

**Before writing ANY code, determine the task type:**

| If the user wants... | Use this approach |
|---------------------|-------------------|
| Building/warehouse/house (walls, roof, doors, windows) | **Arch module** |
| Mechanical part (bracket, enclosure, gear, fitting) | **PartDesign** |
| Simple shapes combined together | **Part module** |
| Quick prototype / artistic form | **Part module** |

**WHY THIS MATTERS:**
- **PartDesign** creates ONE solid - features must connect. Bad for buildings with separate walls/roof.
- **Arch** has Wall, Roof, Window designed for architecture. Walls are hollow, windows cut automatically.
- **Part** allows separate shapes combined with booleans. More flexible.

## STEP 2: Workflow - Direct Source Editing

**source.py** is the single source of truth. Edit it directly.

**To make design changes:**
1. Read source.py to understand the current design
2. Use the Edit tool to modify source.py directly
3. CREATE objects: Add code to source.py
4. DELETE objects: Remove the relevant code from source.py
5. MODIFY objects: Edit the relevant code in source.py

## Coordinate System (CRITICAL)

FreeCAD uses **RIGHT-HANDED** coordinates:
```
        Z (up)
        |
        |
        +------ X (right/East)
       /
      /
     Y (forward/North)
```

**Standard Reference Planes:**
| Plane | Orientation | Normal Direction | Pad/Pocket Direction |
|-------|-------------|------------------|---------------------|
| XY_Plane | Horizontal (floor) | +Z (up) | Pad: +Z, Pocket: -Z |
| XZ_Plane | Vertical, faces South | +Y (north) | Pad: +Y, Pocket: -Y |
| YZ_Plane | Vertical, faces West | +X (east) | Pad: +X, Pocket: -X |

## Building Construction (Arch Module)

**For warehouses, houses, any building - USE ARCH MODULE:**

```python
import Arch
import Draft

# --- WALLS ---
# Option 1: Direct wall (simple)
wall_south = Arch.makeWall(None, length=20000, width=250, height=6000, name="SouthWall")

# Option 2: Wall from baseline (more control)
baseline = Draft.make_line(FreeCAD.Vector(0,0,0), FreeCAD.Vector(20000,0,0))
wall = Arch.makeWall(baseline, width=250, height=6000)

# Position walls
wall_north = Arch.makeWall(None, length=20000, width=250, height=6000)
wall_north.Placement.Base = FreeCAD.Vector(0, 12000, 0)

# --- DOORS/WINDOWS (automatically cut through walls) ---
door = Arch.makeWindowPreset("Simple door", width=4000, height=4500)
door.Hosts = [wall_south]  # Cuts opening automatically
door.Placement.Base = FreeCAD.Vector(8000, 0, 0)  # Position along wall

# --- ROOF ---
# CRITICAL: Set BOTH Angles AND Runs AFTER creation
# Runs = horizontal distance from eave to ridge. Height = run * tan(angle)
# For Draft.make_rectangle(length, width), edges: 0=South, 1=East, 2=North, 3=West
roof_base = Draft.make_rectangle(20000, 12000)
roof_base.Placement.Base = FreeCAD.Vector(0, 0, wall_height)
roof = Arch.makeRoof(roof_base)
doc.recompute()
# Gable roof example (2 sloped, 2 gable ends):
roof.Angles = [30, 90, 30, 90]  # 90° = vertical gable end
roof.Runs = [6000, 0, 6000, 0]  # Run = half of building width for centered ridge
doc.recompute()

# --- FLOOR ---
floor = Arch.makeStructure(length=20000, width=12000, height=200, name="Floor")
```

## PartDesign Workflow (Mechanical Parts ONLY)

**Only use PartDesign for mechanical parts - NOT buildings.**

```python
import Part
import Sketcher
import PartDesign

body = doc.addObject("PartDesign::Body", "Body")

# Sketch on XY plane (horizontal)
sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
sketch.AttachmentSupport = [(doc.getObject("XY_Plane"), "")]
sketch.MapMode = "FlatFace"

# Draw rectangle
sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(0,0,0), FreeCAD.Vector(100,0,0)))
sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(100,0,0), FreeCAD.Vector(100,50,0)))
sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(100,50,0), FreeCAD.Vector(0,50,0)))
sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(0,50,0), FreeCAD.Vector(0,0,0)))
# Add coincident constraints to close
sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))
sketch.addConstraint(Sketcher.Constraint("Coincident", 1, 2, 2, 1))
sketch.addConstraint(Sketcher.Constraint("Coincident", 2, 2, 3, 1))
sketch.addConstraint(Sketcher.Constraint("Coincident", 3, 2, 0, 1))

# Pad upward
pad = body.newObject("PartDesign::Pad", "BasePad")
pad.Profile = sketch
pad.Length = 30
doc.recompute()
```

## Opening/Pocket Direction Rules

**CRITICAL: Pocket cuts PERPENDICULAR to the sketch plane.**

For a building with walls:
```
Building orientation:
- Length along X (East-West)
- Width along Y (North-South)
- Height along Z (up)

Wall positions:
- South wall: Y = 0
- North wall: Y = building_width
- West wall: X = 0
- East wall: X = building_length
```

| To cut opening in... | Sketch plane | Pocket direction |
|---------------------|--------------|------------------|
| South wall (Y=0) | XZ_Plane | +Y (into building) |
| North wall (Y=max) | XZ_Plane + offset | -Y (Reversed=True) |
| West wall (X=0) | YZ_Plane | +X (into building) |
| East wall (X=max) | YZ_Plane + offset | -X (Reversed=True) |
| Floor/ceiling | XY_Plane | ±Z |
| Roof (sloped) | **Attach to roof face** | Normal to face |

## Common Pitfalls to AVOID

### ❌ DON'T: Use PartDesign for buildings
```python
# BAD - Creates solid block, not hollow walls
body = doc.addObject("PartDesign::Body", "Building")
# Walls and roof will merge into single solid
```

### ✅ DO: Use Arch for buildings
```python
# GOOD - Creates proper hollow walls
import Arch
wall = Arch.makeWall(None, length=5000, width=250, height=3000)
```

### ❌ DON'T: Use same sketch plane for all walls
```python
# BAD - All doors cut in wrong direction
door_sketch.AttachmentSupport = [(doc.getObject("XZ_Plane"), "")]  # Only works for South wall!
```

### ✅ DO: Use correct plane for each wall
```python
# For South wall (Y=0)
sketch.AttachmentSupport = [(doc.getObject("XZ_Plane"), "")]
pocket.Reversed = False  # Cuts into building (+Y)

# For North wall (Y=max)
sketch.AttachmentSupport = [(doc.getObject("XZ_Plane"), "")]
sketch.AttachmentOffset = FreeCAD.Placement(FreeCAD.Vector(0, building_width, 0), FreeCAD.Rotation())
pocket.Reversed = True  # Cuts into building (-Y)
```

### ❌ DON'T: Cut skylights vertically through sloped roof
```python
# BAD - Creates rectangular holes in sloped surface
skylight_sketch.AttachmentSupport = [(doc.getObject("XY_Plane"), "")]  # Horizontal plane
```

### ✅ DO: Attach to actual roof face or use Arch windows
```python
# GOOD - Use Arch module for roof openings
skylight = Arch.makeWindowPreset("Open 1-pane", width=2000, height=2000)
skylight.Hosts = [roof]
```

## Self-Check Before Generating

Ask yourself:
1. **Is this a building?** → Use Arch module
2. **Is this a mechanical part?** → Use PartDesign
3. **Do I need openings in walls?** → Use correct sketch plane for each wall
4. **Am I creating hollow structures?** → Use Arch.makeWall (hollow by design)
5. **Does my pocket cut through the right surface?** → Check plane orientation

## Code Rules

- Use millimeters for all dimensions
- End code with `doc.recompute()`
- Use descriptive Labels for objects
- Use object Names (not Labels) when referencing in code

## When Unsure About FreeCAD API

Search the codebase:
```
Grep pattern="makeWall" path="{{FREECAD_SOURCE}}/Mod/Arch"
Grep pattern="makeRoof" path="{{FREECAD_SOURCE}}/Mod/Arch"
```

## Context Files

- **source.py** - The design expressed as Python code (edit this directly)
- **activity.ndjson** - Log of all interactions
- **snapshots/** - JSON snapshots of document state
- **screenshots/** - Viewport images sent with each message
