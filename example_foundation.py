# Buildable AI Source - ALTA Small Warehouse
# Foundation F-1 (16 pieces)
#
# Run this inside FreeCAD: Macro > Execute Macro > select this file

import FreeCAD
import Part
import Arch
import Sketcher
import os

doc = FreeCAD.ActiveDocument or FreeCAD.newDocument("ALTA_Warehouse")

# ============================================================
# 1. CONCRETE GEOMETRY (BIM/Arch)
# ============================================================

# Footing: 3200 x 4200 x 500mm
footing = Arch.makeStructure(length=3200, width=4200, height=500, name="F1_Footing")
footing.IfcType = "Footing"
footing.Placement.Base = FreeCAD.Vector(0, 0, 0)

# Pedestal: 750 x 750 x 1850mm, centered on footing
pedestal = Arch.makeStructure(length=750, width=750, height=1850, name="F1_Pedestal")
pedestal.IfcType = "Column"
pedestal.Placement.Base = FreeCAD.Vector(
    (3200 - 750) / 2,
    (4200 - 750) / 2,
    500
)

doc.recompute()

# ============================================================
# 2. REINFORCEMENT (Rebar)
# ============================================================

# --- Bottom mesh: Ø12@200 A500c (X direction) ---
bottom_x_sketch = doc.addObject("Sketcher::SketchObject", "F1_BottomX_Path")
bottom_x_sketch.addGeometry(
    Part.LineSegment(
        FreeCAD.Vector(40, 40, 40),
        FreeCAD.Vector(3160, 40, 40)
    ), False
)
doc.recompute()

bottom_x_rebar = Arch.makeRebar(
    baseobj=footing,
    sketch=bottom_x_sketch,
    diameter=12,
    amount=21,
    offset=40,
    name="pos_1_bottom_X"
)
bottom_x_rebar.Mark = "1"
doc.recompute()

# --- Bottom mesh: Ø12@200 A500c (Y direction) ---
bottom_y_sketch = doc.addObject("Sketcher::SketchObject", "F1_BottomY_Path")
bottom_y_sketch.addGeometry(
    Part.LineSegment(
        FreeCAD.Vector(40, 40, 52),
        FreeCAD.Vector(40, 4160, 52)
    ), False
)
doc.recompute()

bottom_y_rebar = Arch.makeRebar(
    baseobj=footing,
    sketch=bottom_y_sketch,
    diameter=12,
    amount=16,
    offset=40,
    name="pos_2_bottom_Y"
)
bottom_y_rebar.Mark = "2"
doc.recompute()

# --- Pedestal stirrups: Ø12@200 A500c ---
stirrup_sketch = doc.addObject("Sketcher::SketchObject", "F1_Stirrup_Path")
cx = (3200 - 750) / 2
cy = (4200 - 750) / 2
cover = 40
stirrup_sketch.addGeometry(Part.LineSegment(
    FreeCAD.Vector(cx + cover, cy + cover, 540),
    FreeCAD.Vector(cx + 750 - cover, cy + cover, 540)
), False)
stirrup_sketch.addGeometry(Part.LineSegment(
    FreeCAD.Vector(cx + 750 - cover, cy + cover, 540),
    FreeCAD.Vector(cx + 750 - cover, cy + 750 - cover, 540)
), False)
stirrup_sketch.addGeometry(Part.LineSegment(
    FreeCAD.Vector(cx + 750 - cover, cy + 750 - cover, 540),
    FreeCAD.Vector(cx + cover, cy + 750 - cover, 540)
), False)
stirrup_sketch.addGeometry(Part.LineSegment(
    FreeCAD.Vector(cx + cover, cy + 750 - cover, 540),
    FreeCAD.Vector(cx + cover, cy + cover, 540)
), False)
doc.recompute()

stirrups = Arch.makeRebar(
    baseobj=pedestal,
    sketch=stirrup_sketch,
    diameter=12,
    amount=10,
    offset=40,
    name="pos_3_stirrups"
)
stirrups.Mark = "3"
doc.recompute()

# ============================================================
# 3. TECHDRAW SHEETS
# ============================================================

# Find a template that exists on this system
template_path = ""
search_paths = [
    os.path.join(FreeCAD.getResourceDir(), "Mod", "TechDraw", "Templates", "A3_Landscape_blank.svg"),
    os.path.join(FreeCAD.getResourceDir(), "Mod", "TechDraw", "Templates", "A3_LandscapeTD.svg"),
]
for p in search_paths:
    if os.path.exists(p):
        template_path = p
        break

if not template_path:
    # Fallback: search for any SVG template
    td_template_dir = os.path.join(FreeCAD.getResourceDir(), "Mod", "TechDraw", "Templates")
    if os.path.isdir(td_template_dir):
        for f in os.listdir(td_template_dir):
            if f.endswith(".svg") and "A3" in f:
                template_path = os.path.join(td_template_dir, f)
                break
        if not template_path:
            for f in os.listdir(td_template_dir):
                if f.endswith(".svg"):
                    template_path = os.path.join(td_template_dir, f)
                    break

if not template_path:
    FreeCAD.Console.PrintWarning("No TechDraw template found, skipping drawings\n")
else:
    # --- Sheet 1: Plan + Sections ---
    page1 = doc.addObject("TechDraw::DrawPage", "F1_Sheet1")
    tmpl1 = doc.addObject("TechDraw::DrawSVGTemplate", "F1_Template1")
    tmpl1.Template = template_path
    page1.Template = tmpl1

    all_objects = [footing, pedestal, bottom_x_rebar, bottom_y_rebar, stirrups]

    # Plan view (top-down)
    plan_view = doc.addObject("TechDraw::DrawViewPart", "F1_Plan")
    page1.addView(plan_view)
    plan_view.Source = all_objects
    plan_view.Direction = FreeCAD.Vector(0, 0, 1)
    plan_view.X = 120
    plan_view.Y = 200
    plan_view.Scale = 0.05
    doc.recompute()

    # Section 1-1 (cut through center, looking along Y)
    section_1 = doc.addObject("TechDraw::DrawViewSection", "F1_Section_1_1")
    page1.addView(section_1)
    section_1.Source = all_objects
    section_1.BaseView = plan_view
    section_1.SectionNormal = FreeCAD.Vector(0, 1, 0)
    section_1.SectionOrigin = FreeCAD.Vector(1600, 2100, 1175)
    section_1.Direction = FreeCAD.Vector(0, 0, 1)
    section_1.X = 300
    section_1.Y = 200
    section_1.Scale = 0.05
    doc.recompute()

    # Section 2-2 (cut through center, looking along X)
    section_2 = doc.addObject("TechDraw::DrawViewSection", "F1_Section_2_2")
    page1.addView(section_2)
    section_2.Source = all_objects
    section_2.BaseView = plan_view
    section_2.SectionNormal = FreeCAD.Vector(1, 0, 0)
    section_2.SectionOrigin = FreeCAD.Vector(1600, 2100, 1175)
    section_2.Direction = FreeCAD.Vector(0, 0, 1)
    section_2.X = 120
    section_2.Y = 70
    section_2.Scale = 0.05
    doc.recompute()

    # --- Sheet 2: BBS Table ---
    page2 = doc.addObject("TechDraw::DrawPage", "F1_Sheet2_BBS")
    tmpl2 = doc.addObject("TechDraw::DrawSVGTemplate", "F1_Template2")
    tmpl2.Template = template_path
    page2.Template = tmpl2

    bbs = doc.addObject("TechDraw::DrawViewAnnotation", "F1_BBS")
    page2.addView(bbs)
    bbs.Text = [
        "BAR BENDING SCHEDULE - Foundation F-1 (16 pcs)",
        "",
        "Pos   Dia    Grade    Shape       Length    Qty    Total(m)   Weight(kg)",
        "---   ---    -----    -----       ------    ---    --------   ----------",
        " 1    12     A500c    Straight    3120mm     21      65.5        58.2",
        " 2    12     A500c    Straight    4120mm     16      65.9        58.6",
        " 3    12     A500c    Rect.       2540mm     10      25.4        22.6",
        "",
        "Total steel per element:  139.4 kg",
        "Total steel (16 pcs):    2230.4 kg",
        "Steel ratio:              56.2 kg/m3",
        "",
        "Concrete volume per element:  2.48 m3",
        "Total concrete (16 pcs):     39.7 m3",
        "Concrete class:              C30/37",
    ]
    bbs.X = 200
    bbs.Y = 150
    bbs.TextSize = 5.0
    doc.recompute()

FreeCAD.Console.PrintMessage("\n=== Foundation F-1 generated successfully ===\n")
FreeCAD.Console.PrintMessage("Objects: F1_Footing, F1_Pedestal, 3 rebar groups\n")
FreeCAD.Console.PrintMessage("Sheets: F1_Sheet1 (plan + sections), F1_Sheet2_BBS\n")
