# FreeCAD Python API Quick Reference

## Module Selection Guide

| Task | Module | Why |
|------|--------|-----|
| **Buildings** (walls, roof, windows) | `Arch` | Designed for architecture, hollow walls, auto-cut openings |
| **Mechanical parts** | `PartDesign` | Parametric features, single solid body |
| **Simple shapes + booleans** | `Part` | Quick prototypes, flexible combinations |

---

## Arch Module (Buildings & Architecture)

**ALWAYS use for buildings, warehouses, houses.**

```python
import Arch
import Draft
import FreeCAD

doc = FreeCAD.ActiveDocument or FreeCAD.newDocument("Building")

# === WALLS ===
# Simple wall (standalone)
wall = Arch.makeWall(None, length=5000, width=200, height=3000, name="Wall")

# Wall from baseline (for precise placement)
line = Draft.make_line(FreeCAD.Vector(0,0,0), FreeCAD.Vector(5000,0,0))
wall = Arch.makeWall(line, width=200, height=3000)

# Position a wall
wall.Placement.Base = FreeCAD.Vector(0, 5000, 0)
wall.Placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(0,0,1), 90)  # Rotate 90°

# === DOORS & WINDOWS (auto-cut through walls) ===
# Preset window types: "Fixed", "Open 1-pane", "Open 2-pane", "Sash 2-pane",
#                      "Sliding 2-pane", "Simple door", "Glass door"
door = Arch.makeWindowPreset("Simple door", width=1000, height=2100,
                              h1=100, h2=100, w1=0, w2=0, sill=0)
door.Hosts = [wall]  # Attaches to wall and cuts opening
door.Placement.Base = FreeCAD.Vector(1000, 0, 0)  # Position along wall

window = Arch.makeWindowPreset("Fixed", width=1200, height=1000)
window.Hosts = [wall]
window.Placement.Base = FreeCAD.Vector(3000, 0, 1000)  # 1m from floor

# === ROOF ===
# IMPORTANT: Set Angles AND Runs AFTER creation
# For Draft.make_rectangle(length, width), edges: 0=South, 1=East, 2=North, 3=West
roof_base = Draft.make_rectangle(10000, 8000)
roof_base.Placement.Base = FreeCAD.Vector(0, 0, 3000)  # At wall top
roof = Arch.makeRoof(roof_base)
doc.recompute()  # Let roof initialize

# Hip roof (all 4 sides sloped):
roof.Angles = [15, 15, 15, 15]  # 15° pitch all sides
roof.Runs = [4000, 5000, 4000, 5000]  # Run = distance to ridge, height = run * tan(angle)
doc.recompute()

# Gable roof (2 sloped sides, 2 vertical gable ends):
# 90° = vertical gable end (run auto-set to 0)
roof.Angles = [30, 90, 30, 90]  # Sloped on S/N, gable on E/W
roof.Runs = [4000, 0, 4000, 0]  # Run for sloped sides = half of building width
doc.recompute()

# === FLOOR/SLAB ===
floor = Arch.makeStructure(length=10000, width=8000, height=200, name="Floor")

# === COLUMNS/BEAMS ===
column = Arch.makeStructure(length=300, width=300, height=3000, name="Column")
column.Placement.Base = FreeCAD.Vector(0, 0, 0)

beam = Arch.makeStructure(length=5000, width=200, height=300, name="Beam")
beam.Placement.Base = FreeCAD.Vector(0, 0, 3000)
beam.Placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(1,0,0), 90)  # Horizontal

doc.recompute()
```

---

## Part Module (Creating Primitives)

```python
Part.makeBox(length, width, height, pnt=Vector(0,0,0), dir=Vector(0,0,1))
Part.makeCylinder(radius, height, pnt=Vector(0,0,0), dir=Vector(0,0,1), angle=360)
Part.makeCone(radius1, radius2, height, pnt=Vector(0,0,0), dir=Vector(0,0,1), angle=360)
Part.makeSphere(radius, pnt=Vector(0,0,0), dir=Vector(0,0,1), angle1=-90, angle2=90, angle3=360)
Part.makeTorus(radius1, radius2, pnt=Vector(0,0,0), dir=Vector(0,0,1), angle1=0, angle2=360, angle=360)
```

## Boolean Operations (on shapes)

```python
shape.fuse(other)              # Union - returns new shape
shape.cut(other)               # Subtraction - returns new shape
shape.common(other)            # Intersection - returns new shape
shape.fuse((tool1, tool2))     # Multi-fuse
shape.cut((tool1, tool2))      # Multi-cut
```

## Fillets and Chamfers

```python
# IMPORTANT: These return NEW shapes, don't modify in place
# edgeList must be a list of Edge objects from shape.Edges

shape.makeFillet(radius, edgeList)              # Fillet with single radius
shape.makeFillet(radius1, radius2, edgeList)    # Variable radius fillet
shape.makeChamfer(size, edgeList)               # Chamfer with single size
shape.makeChamfer(size1, size2, edgeList)       # Asymmetric chamfer

# Example - fillet all edges of a box:
box = Part.makeBox(100, 100, 50)
filleted = box.makeFillet(5, box.Edges)  # 5mm radius on all edges
```

## Extrusion and Revolution

```python
shape.extrude(vector)                    # Extrude along vector
shape.revolve(center, axis, angle)       # Revolve around axis (angle in degrees)

# Example:
face.extrude(FreeCAD.Vector(0, 0, 100))  # Extrude face 100mm in Z
```

## Wire and Face Creation

```python
Part.makePolygon([pt1, pt2, pt3, pt1])   # Closed wire from points (repeat first point)
Part.makeLine(pt1, pt2)                   # Line edge
Part.makeCircle(radius, center=Vector(0,0,0), normal=Vector(0,0,1), angle1=0, angle2=360)
Part.Face(wire)                           # Create face from closed wire
```

## Document Objects (Parametric)

```python
# These create parametric objects in the document
doc.addObject("Part::Box", "Name")        # Has .Length, .Width, .Height
doc.addObject("Part::Cylinder", "Name")   # Has .Radius, .Height
doc.addObject("Part::Sphere", "Name")     # Has .Radius
doc.addObject("Part::Cone", "Name")       # Has .Radius1, .Radius2, .Height
doc.addObject("Part::Torus", "Name")      # Has .Radius1, .Radius2

# Boolean operations (parametric)
doc.addObject("Part::Cut", "Name")        # Set .Base and .Tool
doc.addObject("Part::Fuse", "Name")       # Set .Base and .Tool
doc.addObject("Part::Common", "Name")     # Set .Base and .Tool
doc.addObject("Part::MultiFuse", "Name")  # Set .Shapes = [obj1, obj2, ...]
doc.addObject("Part::MultiCommon", "Name")

# Generic Part (for computed shapes)
doc.addObject("Part::Feature", "Name")    # Set .Shape = computed_shape
```

## Placement

```python
obj.Placement.Base = FreeCAD.Vector(x, y, z)
obj.Placement.Rotation = FreeCAD.Rotation(axis, angle_degrees)
obj.Placement.Rotation = FreeCAD.Rotation(yaw, pitch, roll)  # Euler angles in degrees
```

## Common Patterns

```python
# Fillet a parametric box (must use Part::Feature for result)
box = doc.addObject("Part::Box", "Box")
box.Length, box.Width, box.Height = 100, 80, 50
doc.recompute()

filleted_shape = box.Shape.makeFillet(5, box.Shape.Edges)
result = doc.addObject("Part::Feature", "FilletedBox")
result.Shape = filleted_shape

# Boolean cut with door opening
wall = doc.addObject("Part::Box", "Wall")
door = doc.addObject("Part::Box", "DoorCutout")
wall_with_door = doc.addObject("Part::Cut", "WallWithDoor")
wall_with_door.Base = wall
wall_with_door.Tool = door
```

---

## Complete Example: Simple Warehouse (Arch Module)

```python
import FreeCAD
import Arch
import Draft

doc = FreeCAD.ActiveDocument or FreeCAD.newDocument("Warehouse")

# Dimensions (mm)
length = 20000  # 20m
width = 12000   # 12m
wall_height = 6000  # 6m
wall_thickness = 250

# Floor slab
floor = Arch.makeStructure(length=length, width=width, height=200, name="Floor")
floor.Placement.Base = FreeCAD.Vector(0, 0, -200)

# Walls - create baselines, then walls
south_line = Draft.make_line(FreeCAD.Vector(0,0,0), FreeCAD.Vector(length,0,0))
north_line = Draft.make_line(FreeCAD.Vector(0,width,0), FreeCAD.Vector(length,width,0))
west_line = Draft.make_line(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,width,0))
east_line = Draft.make_line(FreeCAD.Vector(length,0,0), FreeCAD.Vector(length,width,0))

wall_south = Arch.makeWall(south_line, width=wall_thickness, height=wall_height, name="SouthWall")
wall_north = Arch.makeWall(north_line, width=wall_thickness, height=wall_height, name="NorthWall")
wall_west = Arch.makeWall(west_line, width=wall_thickness, height=wall_height, name="WestWall")
wall_east = Arch.makeWall(east_line, width=wall_thickness, height=wall_height, name="EastWall")

# Large truck door (south wall)
truck_door = Arch.makeWindowPreset("Simple door", width=4000, height=4500)
truck_door.Hosts = [wall_south]
truck_door.Placement.Base = FreeCAD.Vector(length/2 - 2000, 0, 0)

# Personnel door (south wall)
pers_door = Arch.makeWindowPreset("Simple door", width=1000, height=2100)
pers_door.Hosts = [wall_south]
pers_door.Placement.Base = FreeCAD.Vector(2000, 0, 0)

# Windows (east and west walls)
for i in range(3):
    win = Arch.makeWindowPreset("Fixed", width=2000, height=1500)
    win.Hosts = [wall_east]
    win.Placement.Base = FreeCAD.Vector(length, 2000 + i*3000, 1500)

# Roof (set Angles AND Runs AFTER creation)
roof_base = Draft.make_rectangle(length + 500, width + 500)  # 500mm overhang
roof_base.Placement.Base = FreeCAD.Vector(-250, -250, wall_height)
roof = Arch.makeRoof(roof_base)
doc.recompute()
# Gable roof: sloped on S/N (along length), gable ends on E/W
# Run = horizontal distance from eave to ridge = half of building width
roof.Angles = [15, 90, 15, 90]
roof.Runs = [(width + 500) / 2, 0, (width + 500) / 2, 0]  # Run for sloped sides
doc.recompute()
```

---

## Coordinate System Reference

```
        Z (up)
        |
        |
        +------ X (right/East)
       /
      /
     Y (forward/North)
```

| Plane | Normal | Sketch X | Sketch Y |
|-------|--------|----------|----------|
| XY_Plane | +Z | X | Y |
| XZ_Plane | +Y | X | Z |
| YZ_Plane | +X | Y | Z |
