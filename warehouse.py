"""
FreeCAD Warehouse Generator
Builds a parametric warehouse with walls, roof, floor, doors, and windows.
"""

import FreeCAD
import Part
import math

# --- Parameters ---
LENGTH = 20000    # mm (20m)
WIDTH = 12000     # mm (12m)
WALL_HEIGHT = 5000  # mm (5m) wall height
RIDGE_HEIGHT = 7000 # mm (7m) roof peak
WALL_THICK = 200    # mm
FLOOR_THICK = 150   # mm

# Door parameters
DOOR_W = 3000       # mm (3m wide rolling door)
DOOR_H = 4000       # mm (4m tall)
SMALL_DOOR_W = 1200 # mm personnel door
SMALL_DOOR_H = 2200 # mm

# Window parameters
WIN_W = 1500
WIN_H = 1200
WIN_SILL = 2500     # sill height from floor

doc = FreeCAD.newDocument("Warehouse")

# ─── Floor slab ───
floor_slab = Part.makeBox(LENGTH, WIDTH, FLOOR_THICK)
floor_slab.translate(FreeCAD.Vector(0, 0, -FLOOR_THICK))
Part.show(floor_slab, "Floor")
doc.getObject("Floor").ViewObject.ShapeColor = (0.7, 0.7, 0.7)

# ─── Helper: make a wall with cutouts ───
def make_wall(lx, ly, lz, pos, cutouts=None):
    """Create a wall box at pos, subtract cutout boxes."""
    wall = Part.makeBox(lx, ly, lz)
    wall.translate(pos)
    if cutouts:
        for (cx, cy, cz, cpos) in cutouts:
            hole = Part.makeBox(cx, cy, cz)
            hole.translate(cpos)
            wall = wall.cut(hole)
    return wall

# ─── Front wall (Y=0) with large rolling door + personnel door ───
front_cutouts = [
    # Rolling door centered
    (DOOR_W, WALL_THICK + 2, DOOR_H,
     FreeCAD.Vector(LENGTH / 2 - DOOR_W / 2, -1, 0)),
    # Personnel door on the right
    (SMALL_DOOR_W, WALL_THICK + 2, SMALL_DOOR_H,
     FreeCAD.Vector(LENGTH - 2000 - SMALL_DOOR_W, -1, 0)),
]
front_wall = make_wall(LENGTH, WALL_THICK, WALL_HEIGHT,
                       FreeCAD.Vector(0, 0, 0), front_cutouts)
Part.show(front_wall, "FrontWall")

# ─── Back wall (Y=WIDTH) with rolling door ───
back_cutouts = [
    (DOOR_W, WALL_THICK + 2, DOOR_H,
     FreeCAD.Vector(LENGTH / 2 - DOOR_W / 2, WIDTH - 1, 0)),
]
back_wall = make_wall(LENGTH, WALL_THICK, WALL_HEIGHT,
                      FreeCAD.Vector(0, WIDTH - WALL_THICK, 0), back_cutouts)
Part.show(back_wall, "BackWall")

# ─── Left wall (X=0) with windows ───
left_win_cutouts = []
for i in range(3):
    wx = -1
    wy = 2500 + i * 3000
    left_win_cutouts.append(
        (WALL_THICK + 2, WIN_W, WIN_H,
         FreeCAD.Vector(wx, wy, WIN_SILL))
    )
left_wall = make_wall(WALL_THICK, WIDTH, WALL_HEIGHT,
                       FreeCAD.Vector(0, 0, 0), left_win_cutouts)
Part.show(left_wall, "LeftWall")

# ─── Right wall (X=LENGTH) with windows ───
right_win_cutouts = []
for i in range(3):
    wx = LENGTH - WALL_THICK - 1
    wy = 2500 + i * 3000
    right_win_cutouts.append(
        (WALL_THICK + 2, WIN_W, WIN_H,
         FreeCAD.Vector(wx, wy, WIN_SILL))
    )
right_wall = make_wall(WALL_THICK, WIDTH, WALL_HEIGHT,
                        FreeCAD.Vector(LENGTH - WALL_THICK, 0, 0), right_win_cutouts)
Part.show(right_wall, "RightWall")

# ─── Color walls ───
for name in ["FrontWall", "BackWall", "LeftWall", "RightWall"]:
    doc.getObject(name).ViewObject.ShapeColor = (0.85, 0.82, 0.75)

# ─── Gable triangles (front and back) ───
half_w = WIDTH / 2.0
gable_height = RIDGE_HEIGHT - WALL_HEIGHT

# Front gable
gp1 = FreeCAD.Vector(0, 0, WALL_HEIGHT)
gp2 = FreeCAD.Vector(0, WIDTH, WALL_HEIGHT)
gp3 = FreeCAD.Vector(0, half_w, RIDGE_HEIGHT)
front_gable_wire = Part.makePolygon([gp1, gp2, gp3, gp1])
front_gable_face = Part.Face(front_gable_wire)
front_gable = front_gable_face.extrude(FreeCAD.Vector(WALL_THICK, 0, 0))
Part.show(front_gable, "FrontGable")

# Back gable
bg1 = FreeCAD.Vector(LENGTH - WALL_THICK, 0, WALL_HEIGHT)
bg2 = FreeCAD.Vector(LENGTH - WALL_THICK, WIDTH, WALL_HEIGHT)
bg3 = FreeCAD.Vector(LENGTH - WALL_THICK, half_w, RIDGE_HEIGHT)
back_gable_wire = Part.makePolygon([bg1, bg2, bg3, bg1])
back_gable_face = Part.Face(back_gable_wire)
back_gable = back_gable_face.extrude(FreeCAD.Vector(WALL_THICK, 0, 0))
Part.show(back_gable, "BackGable")

for name in ["FrontGable", "BackGable"]:
    doc.getObject(name).ViewObject.ShapeColor = (0.85, 0.82, 0.75)

# ─── Roof panels (two slopes) ───
ROOF_THICK = 100
ROOF_OVERHANG = 500  # overhang on each side

# Calculate roof panel dimensions
roof_slope_len = math.sqrt((half_w + ROOF_OVERHANG) ** 2 + gable_height ** 2)
roof_angle = math.atan2(gable_height, half_w)

# Left roof panel
lrp1 = FreeCAD.Vector(-ROOF_OVERHANG, -ROOF_OVERHANG, WALL_HEIGHT)
lrp2 = FreeCAD.Vector(-ROOF_OVERHANG, half_w, RIDGE_HEIGHT)
lrp3 = FreeCAD.Vector(-ROOF_OVERHANG, half_w, RIDGE_HEIGHT + ROOF_THICK / math.cos(roof_angle))
lrp4 = FreeCAD.Vector(-ROOF_OVERHANG, -ROOF_OVERHANG, WALL_HEIGHT + ROOF_THICK / math.cos(roof_angle))
left_roof_wire = Part.makePolygon([lrp1, lrp2, lrp3, lrp4, lrp1])
left_roof_face = Part.Face(left_roof_wire)
left_roof = left_roof_face.extrude(FreeCAD.Vector(LENGTH + 2 * ROOF_OVERHANG, 0, 0))
Part.show(left_roof, "LeftRoof")

# Right roof panel
rrp1 = FreeCAD.Vector(-ROOF_OVERHANG, WIDTH + ROOF_OVERHANG, WALL_HEIGHT)
rrp2 = FreeCAD.Vector(-ROOF_OVERHANG, half_w, RIDGE_HEIGHT)
rrp3 = FreeCAD.Vector(-ROOF_OVERHANG, half_w, RIDGE_HEIGHT + ROOF_THICK / math.cos(roof_angle))
rrp4 = FreeCAD.Vector(-ROOF_OVERHANG, WIDTH + ROOF_OVERHANG, WALL_HEIGHT + ROOF_THICK / math.cos(roof_angle))
right_roof_wire = Part.makePolygon([rrp1, rrp2, rrp3, rrp4, rrp1])
right_roof_face = Part.Face(right_roof_wire)
right_roof = right_roof_face.extrude(FreeCAD.Vector(LENGTH + 2 * ROOF_OVERHANG, 0, 0))
Part.show(right_roof, "RightRoof")

for name in ["LeftRoof", "RightRoof"]:
    doc.getObject(name).ViewObject.ShapeColor = (0.55, 0.27, 0.07)

# ─── Steel columns (8 columns along the walls) ───
COL_SIZE = 200  # 200x200mm steel columns
col_positions = []
for i in range(5):
    x = i * (LENGTH / 4.0)
    col_positions.append((x, 0))                    # left side
    col_positions.append((x, WIDTH - COL_SIZE))      # right side

for idx, (cx, cy) in enumerate(col_positions):
    col = Part.makeBox(COL_SIZE, COL_SIZE, WALL_HEIGHT)
    col.translate(FreeCAD.Vector(cx, cy, 0))
    name = f"Column{idx:02d}"
    Part.show(col, name)
    doc.getObject(name).ViewObject.ShapeColor = (0.4, 0.4, 0.45)

# ─── Roof trusses (simplified as rectangular beams along the ridge) ───
BEAM_W = 150
BEAM_H = 300
for i in range(5):
    x = i * (LENGTH / 4.0)
    # Horizontal tie beam
    tie = Part.makeBox(BEAM_W, WIDTH, BEAM_H)
    tie.translate(FreeCAD.Vector(x, 0, WALL_HEIGHT - BEAM_H))
    name = f"TieBeam{i:02d}"
    Part.show(tie, name)
    doc.getObject(name).ViewObject.ShapeColor = (0.4, 0.4, 0.45)

# ─── Ridge beam ───
ridge = Part.makeBox(LENGTH, BEAM_W, BEAM_H)
ridge.translate(FreeCAD.Vector(0, half_w - BEAM_W / 2, RIDGE_HEIGHT - BEAM_H))
Part.show(ridge, "RidgeBeam")
doc.getObject("RidgeBeam").ViewObject.ShapeColor = (0.4, 0.4, 0.45)

# ─── Recompute and fit view ───
doc.recompute()

# Set isometric view
if FreeCAD.GuiUp:
    import FreeCADGui
    FreeCADGui.activeDocument().activeView().viewIsometric()
    FreeCADGui.SendMsgToActiveView("ViewFit")

print("Warehouse model created successfully!")
print(f"  Dimensions: {LENGTH/1000}m x {WIDTH/1000}m")
print(f"  Wall height: {WALL_HEIGHT/1000}m, Ridge: {RIDGE_HEIGHT/1000}m")
