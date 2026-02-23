# FreeCAD AI Drawings - Warehouse
# Structural engineering drawings for the warehouse model
#
# Run warehouse.py first, then run this file.
# exec(open("/home/luka/buildable/FreeCAD/warehouse.py").read())
# exec(open("/home/luka/buildable/FreeCAD/tech_draw.py").read())

import FreeCAD
import TechDraw
import os

doc = FreeCAD.ActiveDocument

# === Collect model objects for projection ===
all_objects = [obj for obj in doc.Objects if obj.TypeId == "Part::Feature"]
if not all_objects:
    raise RuntimeError("No Part::Feature objects found. Run warehouse.py first.")

FreeCAD.Console.PrintMessage(f"Found {len(all_objects)} objects for projection\n")

# === Find TechDraw template ===
template_dir = os.path.join(FreeCAD.getResourceDir(), "Mod", "TechDraw", "Templates")
template_a3 = None

# Search for any usable template
for candidate in ["A3_Landscape_blank.svg", "A3_LandscapeTD.svg"]:
    p = os.path.join(template_dir, candidate)
    if os.path.exists(p):
        template_a3 = p
        break

if not template_a3 and os.path.isdir(template_dir):
    for root, dirs, files in os.walk(template_dir):
        for f in files:
            if f.endswith(".svg"):
                template_a3 = os.path.join(root, f)
                break
        if template_a3:
            break

if not template_a3:
    raise RuntimeError("No TechDraw SVG template found")

FreeCAD.Console.PrintMessage(f"Template: {template_a3}\n")

# === Warehouse dimensions (from warehouse.py) ===
# LENGTH=20000, WIDTH=12000, WALL_HEIGHT=5000, RIDGE_HEIGHT=7000


# ============================================================
# Sheet 1: General Arrangement — Plan + Elevations
# A3 landscape = 420 x 297 mm
# Scale 1:100 → warehouse = 200 x 120 mm on paper
# ============================================================

page1 = doc.addObject("TechDraw::DrawPage", "Sheet1_GA")
page1.Label = "General Arrangement"
tmpl1 = doc.addObject("TechDraw::DrawSVGTemplate", "Template_GA")
tmpl1.Template = template_a3
page1.Template = tmpl1

SCALE_GA = 1.0 / 100.0  # 1:100

# --- Plan view (top-down) ---
# At 1:100: 200mm wide x 120mm tall
plan_view = doc.addObject("TechDraw::DrawViewPart", "GA_Plan")
page1.addView(plan_view)
plan_view.Source = all_objects
plan_view.Direction = FreeCAD.Vector(0, 0, -1)   # look down
plan_view.XDirection = FreeCAD.Vector(1, 0, 0)    # X goes right
plan_view.Scale = SCALE_GA
plan_view.X = 140   # center of plan view on page
plan_view.Y = 205    # upper half of page
plan_view.Label = "Plan View 1:100"
doc.recompute()

# --- Front elevation (looking along -Y, south face) ---
# At 1:100: 200mm wide x 70mm tall
front_view = doc.addObject("TechDraw::DrawViewPart", "GA_Front")
page1.addView(front_view)
front_view.Source = all_objects
front_view.Direction = FreeCAD.Vector(0, -1, 0)    # look from south
front_view.XDirection = FreeCAD.Vector(1, 0, 0)    # X goes right
front_view.Scale = SCALE_GA
front_view.X = 140
front_view.Y = 75     # lower half of page
front_view.Label = "Front Elevation 1:100"
doc.recompute()

# --- Right side elevation (looking along -X, east face) ---
# At 1:100: 120mm wide x 70mm tall
side_view = doc.addObject("TechDraw::DrawViewPart", "GA_Side")
page1.addView(side_view)
side_view.Source = all_objects
side_view.Direction = FreeCAD.Vector(-1, 0, 0)     # look from east
side_view.XDirection = FreeCAD.Vector(0, 1, 0)     # Y goes right
side_view.Scale = SCALE_GA
side_view.X = 330
side_view.Y = 205
side_view.Label = "Side Elevation 1:100"
doc.recompute()

# --- Overall dimension annotations ---
dim_note = doc.addObject("TechDraw::DrawViewAnnotation", "GA_Dims")
page1.addView(dim_note)
dim_note.Text = [
    "GENERAL ARRANGEMENT",
    "Scale 1:100",
    "",
    "Overall: 20000 x 12000 mm",
    "Wall height: 5000 mm",
    "Ridge height: 7000 mm",
]
dim_note.X = 330
dim_note.Y = 75
dim_note.TextSize = 4.0
doc.recompute()

FreeCAD.Console.PrintMessage("Sheet 1 (GA) done\n")


# ============================================================
# Sheet 2: Cross Sections
# Section A-A: Transverse (cut at X=10000, looking along -X)
# Section B-B: Longitudinal (cut at Y=6000, looking along -Y)
# ============================================================

page2 = doc.addObject("TechDraw::DrawPage", "Sheet2_Sections")
page2.Label = "Cross Sections"
tmpl2 = doc.addObject("TechDraw::DrawSVGTemplate", "Template_Sections")
tmpl2.Template = template_a3
page2.Template = tmpl2

SCALE_SECTION = 1.0 / 75.0  # 1:75 for more detail

# Base view (needed as reference for sections, small in corner)
base_view = doc.addObject("TechDraw::DrawViewPart", "Sections_BaseRef")
page2.addView(base_view)
base_view.Source = all_objects
base_view.Direction = FreeCAD.Vector(0, 0, -1)
base_view.XDirection = FreeCAD.Vector(1, 0, 0)
base_view.Scale = 1.0 / 200.0  # tiny reference
base_view.X = 40
base_view.Y = 270
doc.recompute()

# --- Section A-A: Transverse at midspan (X=10000) ---
# Cut normal to X, look from east side → shows Y-Z profile
# At 1:75: width=160mm (12000/75), height=93mm (7000/75)
section_a = doc.addObject("TechDraw::DrawViewSection", "Section_A_A")
page2.addView(section_a)
section_a.Source = all_objects
section_a.BaseView = base_view
section_a.SectionNormal = FreeCAD.Vector(1, 0, 0)
section_a.SectionOrigin = FreeCAD.Vector(10000, 6000, 0)
section_a.Direction = FreeCAD.Vector(-1, 0, 0)     # look along -X (from east)
section_a.XDirection = FreeCAD.Vector(0, -1, 0)     # Y goes left→right on paper
section_a.Scale = SCALE_SECTION
section_a.X = 140
section_a.Y = 200
section_a.Label = "Section A-A  1:75"
doc.recompute()

# --- Section B-B: Longitudinal at mid-width (Y=6000) ---
# Cut normal to Y, look from south → shows X-Z profile
# At 1:75: width=267mm (20000/75), height=93mm (7000/75)
section_b = doc.addObject("TechDraw::DrawViewSection", "Section_B_B")
page2.addView(section_b)
section_b.Source = all_objects
section_b.BaseView = base_view
section_b.SectionNormal = FreeCAD.Vector(0, 1, 0)
section_b.SectionOrigin = FreeCAD.Vector(10000, 6000, 0)
section_b.Direction = FreeCAD.Vector(0, -1, 0)      # look along -Y (from south)
section_b.XDirection = FreeCAD.Vector(1, 0, 0)      # X goes right
section_b.Scale = 1.0 / 100.0  # 1:100 to fit width
section_b.X = 200
section_b.Y = 60
section_b.Label = "Section B-B  1:100"
doc.recompute()

# Section labels
sec_note = doc.addObject("TechDraw::DrawViewAnnotation", "Sec_Labels")
page2.addView(sec_note)
sec_note.Text = [
    "CROSS SECTIONS",
    "",
    "A-A: Transverse at midspan (1:75)",
    "B-B: Longitudinal at center (1:100)",
]
sec_note.X = 340
sec_note.Y = 270
sec_note.TextSize = 4.0
doc.recompute()

FreeCAD.Console.PrintMessage("Sheet 2 (Sections) done\n")


# ============================================================
# Sheet 3: Isometric + Details
# ============================================================

page3 = doc.addObject("TechDraw::DrawPage", "Sheet3_Iso")
page3.Label = "Isometric View"
tmpl3 = doc.addObject("TechDraw::DrawSVGTemplate", "Template_Iso")
tmpl3.Template = template_a3
page3.Template = tmpl3

# --- Isometric view ---
# At 1:75: bounding box ~320mm diagonal → fits A3
iso_view = doc.addObject("TechDraw::DrawViewPart", "Iso_View")
page3.addView(iso_view)
iso_view.Source = all_objects
iso_view.Direction = FreeCAD.Vector(1, -1, -0.7)    # standard iso-ish
iso_view.XDirection = FreeCAD.Vector(-1, -1, 0)
iso_view.Scale = 1.0 / 100.0
iso_view.X = 180
iso_view.Y = 170
iso_view.Label = "Isometric View 1:100"
doc.recompute()

# --- Project info annotation ---
info_note = doc.addObject("TechDraw::DrawViewAnnotation", "Project_Info")
page3.addView(info_note)
info_note.Text = [
    "WAREHOUSE - STRUCTURAL OVERVIEW",
    "",
    "Building dimensions:",
    "  Length: 20 000 mm",
    "  Width:  12 000 mm",
    "  Wall height: 5 000 mm",
    "  Ridge height: 7 000 mm",
    "",
    "Structure:",
    "  Walls: 200 mm concrete/masonry",
    "  Columns: 200x200 mm steel (10 pcs)",
    "  Tie beams: 150x300 mm (5 pcs)",
    "  Ridge beam: 150x300 mm",
    "  Roof: 100 mm panels, gabled",
    "  Floor slab: 150 mm RC",
    "",
    "Concrete: C30/37",
    "Steel: S355",
]
info_note.X = 350
info_note.Y = 170
info_note.TextSize = 3.5
doc.recompute()

FreeCAD.Console.PrintMessage("Sheet 3 (Isometric) done\n")


# ============================================================
# Sheet 4: Spreadsheet — Material Takeoff
# ============================================================

sheet = doc.addObject("Spreadsheet::Sheet", "MaterialTakeoff")
sheet.Label = "Material Takeoff"

# Headers (row 1)
for col, header in [
    ("A1", "No."),
    ("B1", "Element"),
    ("C1", "Qty"),
    ("D1", "Dimensions (mm)"),
    ("E1", "Volume (m3)"),
    ("F1", "Weight (kg)"),
]:
    sheet.set(col, header)

# Data
data = [
    ("1", "Floor slab",     "1",  "20000x12000x150",   "36.0",  "86400"),
    ("2", "Front wall",     "1",  "20000x200x5000",    "20.0",  "48000"),
    ("3", "Back wall",      "1",  "20000x200x5000",    "20.0",  "48000"),
    ("4", "Side walls",     "2",  "200x12000x5000",    "24.0",  "57600"),
    ("5", "Gable panels",   "2",  "200x12000x2000 tri","4.8",   "11520"),
    ("6", "Roof panels",    "2",  "21000x6500x100",    "27.3",  "5460"),
    ("7", "Steel columns",  "10", "200x200x5000",      "2.0",   "15700"),
    ("8", "Tie beams",      "5",  "150x12000x300",     "2.7",   "10598"),
    ("9", "Ridge beam",     "1",  "20000x150x300",     "0.9",   "7065"),
]

for i, (no, elem, qty, dims, vol, wt) in enumerate(data, start=2):
    sheet.set(f"A{i}", no)
    sheet.set(f"B{i}", elem)
    sheet.set(f"C{i}", qty)
    sheet.set(f"D{i}", dims)
    sheet.set(f"E{i}", vol)
    sheet.set(f"F{i}", wt)

doc.recompute()

FreeCAD.Console.PrintMessage("Sheet 4 (Material Takeoff) done\n")


# ============================================================
# Done
# ============================================================
doc.recompute()

FreeCAD.Console.PrintMessage("\n=== TechDraw sheets generated ===\n")
FreeCAD.Console.PrintMessage("  Sheet1_GA:       Plan + Front + Side elevations (1:100)\n")
FreeCAD.Console.PrintMessage("  Sheet2_Sections: Transverse A-A (1:75) + Longitudinal B-B (1:100)\n")
FreeCAD.Console.PrintMessage("  Sheet3_Iso:      Isometric view + project info\n")
FreeCAD.Console.PrintMessage("  MaterialTakeoff: Spreadsheet quantities\n")
FreeCAD.Console.PrintMessage("\nTo test: delete all TechDraw/Spreadsheet objects, then re-run this.\n")
