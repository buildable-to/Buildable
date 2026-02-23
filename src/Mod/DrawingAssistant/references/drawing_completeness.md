# Structural Drawing Completeness Checklist

## MANDATORY: Every structural drawing MUST contain ALL of these elements

A structurally complete drawing is construction-ready. Incomplete drawings cause site confusion, rework, and safety hazards.

### 1. Main Reinforcement Geometry
- All primary bars shown with correct representation (double lines for parallel, filled dots for perpendicular)
- Correct layer stacking: Bottom layer 1 center = cover + d/2, Layer 2 = cover + d_layer1 + d/2, Top = thickness - cover - d/2
- Bar mark labels: "Pos N  [count]d[diameter]/[spacing]" with leader lines

### 2. Shear Reinforcement (REQUIRED for beams and columns)
- **Beams**: stirrups/links shown with diameter and spacing (e.g., d8@150)
- **Columns**: ties/links shown (rectangular around main bars)
- **Slabs**: transverse reinforcement shown as dots (perpendicular to main direction)
- Exception: slabs with one-way spanning may omit transverse bars if noted

### 3. Cover Dimensions
- Concrete cover dimensioned on at least one vertical edge
- Standard cover values by exposure class (EN 1992-1-1 Table 4.2):
  - XC1 (dry): 25mm
  - XC2/XC3 (wet/humid): 35mm
  - XC4 (cyclic): 40mm
  - XD/XS (marine/chemical): 45–50mm

### 4. Overall Dimensions
- Element width + height/thickness shown with dimension lines
- Any critical dimensions contractor needs to set formwork (e.g., wall openings, beam offsets)

### 5. Bar Bending Schedule (REQUIRED)
- Spreadsheet with columns: Pos | Ø (mm) | Shape | Total Length (mm) | Qty | Unit Weight (kg/m) | Total Weight (kg)
- Embedded in TechDraw sheet via DrawViewSpreadsheet (visible on printed drawing)
- All bars listed with correct counts and lengths

### 6. Material Specification Box
- Concrete grade: e.g., "C30/37 per EN 206"
- Reinforcing steel grade: e.g., "B500B per EN 10080"
- Nominal cover (with design deviation): e.g., "Nom. cover 35mm (cdev 10mm)"
- Exposure class: e.g., "Exposure class XC3"
- Design standard: e.g., "Design standard: EN 1992-1-1"
- Placed as Draft text block, typically bottom-left or spare area of sheet

### 7. Section Reference Marks
- Section cut markers (A-A, B-B) on plan/elevation views showing where sections are taken
- Section titles below each section: "SECTION A-A, Scale 1:20"
- Ensures contractor can correlate sections to locations

### 8. Title Block
- Use `A3_Landscape_TD.svg` template (title block version) for production drawings
- Populate:
  - **FC-Title**: Element name/description (e.g., "Slab on Ground Reinforcement")
  - **Subtitle**: Project name (e.g., "Office Building")
  - **drawing_number**: Unique identifier (e.g., "STR-101")
  - **SheetNumber**: Page numbering if multi-sheet set
  - **scale**: Drawing scale (e.g., "1:20")
  - **CreationDate**: Date drawn
  - **AuthorName**: Engineer/designer (recommended)

---

## Per Element Type: Mandatory Elements

### Beam Section (Longitudinal)
**MANDATORY:**
- Main rebar geometry (bottom + top bars, double-line + hooks)
- Shear reinforcement (stirrups d8/d10/d12 at specified spacing)
- Cross-section view showing stirrup arrangement
- Cover dimensions (top and bottom)
- Overall dimensions (span, depth)
- Bar bending schedule
- Material specification
- Title block

### Beam Elevation View
**MANDATORY:**
- Main rebar showing full span (double-line bars with hooks)
- Stirrup distribution along span (shown as vertical pairs at each stirrup position)
- Section cut markers (A-A, B-B where sections are taken)
- Overall dimensions (span, supports)
- Bar bending schedule
- Material specification
- Title block

### Slab Section (One Direction)
**MANDATORY:**
- Bottom main reinforcement (running along section) as double lines
- Top reinforcement if cantilevered or two-way
- Transverse reinforcement (the other direction) shown as dots
- Cover dimensions (top and bottom)
- Overall dimensions (span, thickness)
- Bar bending schedule (both directions)
- Material specification
- Title block

### Slab Plan View (Two-Way Slab)
**MANDATORY:**
- Main reinforcement X-direction (bars parallel to plan)
- Main reinforcement Y-direction (bars parallel to plan)
- Bending dimension labels for each direction
- Overall dimensions
- Bar bending schedule
- Material specification
- Title block

### Column Section
**MANDATORY:**
- Main vertical bars shown (double lines if parallel to cut, dots if perpendicular)
- Ties/links shown (typically rectangular stirrups)
- Spacing of ties specified (e.g., d10@150 mm)
- Cross-section view showing tie arrangement
- Cover dimensions
- Overall dimensions (height, width)
- Bar bending schedule
- Material specification
- Title block

### Foundation / Pad Footing
**MANDATORY:**
- Plan view showing both reinforcement directions (X and Y bars)
- Bottom mesh reinforcement all directions
- Top reinforcement if applicable
- Section views showing layer stacking and cover
- Cover dimensions (top and bottom)
- Overall dimensions (length, width, thickness)
- Bar bending schedule
- Material specification
- Title block

### Formwork / Shuttering (No Rebar)
**MANDATORY:**
- Concrete outline/structure geometry
- Overall dimensions
- Finish specifications (concrete class, surface treatment)
- Title block
- Material specification (concrete grade only, no rebar)

---

## Quick Reference: Code Snippets

### Bar Bending Schedule (Spreadsheet)
```python
sht = doc.addObject("Spreadsheet::Sheet", "BarSchedule")
headers = ["Pos", "Ø (mm)", "Shape", "Total Length (mm)", "Qty", "Unit Weight (kg/m)", "Total Weight (kg)"]
for col, h in enumerate(headers):
    cell = chr(65 + col) + "1"
    sht.set(cell, h)

# Add data rows with bar info
sht.set("A2", "1")      # Pos
sht.set("B2", "20")     # Diameter
sht.set("C2", "Straight")
sht.set("D2", "3000")   # Length in mm
sht.set("E2", "4")      # Quantity
# Unit weight and total weight calculated

# Embed in TechDraw sheet
view_ssheet = doc.addObject("TechDraw::DrawViewSpreadsheet", "ScheduleView")
view_ssheet.Source = sht
page.addView(view_ssheet)
view_ssheet.X = 20
view_ssheet.Y = 50
```

### Material Specification Text Block
```python
mat_text = Draft.make_text([
    "MATERIAL SPECIFICATION",
    "Concrete: C30/37 per EN 206",
    "Reinforcement: B500B per EN 10080",
    "Nominal cover: 35mm (design dev = 10mm)",
    "Exposure class: XC3",
    "Design standard: EN 1992-1-1",
], FreeCAD.Vector(ox, oy, 0))
mat_text.Label = "MaterialSpec"
draft_objects.append(mat_text)
```

### Stirrups in Cross-Section (Double-Line Rectangle)
```python
# Stirrup as rectangular closed wire (outer + inner profiles)
r = 4  # 8mm bar → 4mm radius
# Outer profile
outer = Draft.make_wire([
    V(cx - width/2 + cover + r, cy - height/2 + cover + r, 0),
    V(cx + width/2 - cover - r, cy - height/2 + cover + r, 0),
    V(cx + width/2 - cover - r, cy + height/2 - cover - r, 0),
    V(cx - width/2 + cover + r, cy + height/2 - cover - r, 0),
], closed=True)
# Inner profile (same with offset)
inner = Draft.make_wire([
    V(cx - width/2 + cover + 3*r, cy - height/2 + cover + 3*r, 0),
    V(cx + width/2 - cover - 3*r, cy - height/2 + cover + 3*r, 0),
    V(cx + width/2 - cover - 3*r, cy + height/2 - cover - 3*r, 0),
    V(cx - width/2 + cover + 3*r, cy + height/2 - cover - 3*r, 0),
], closed=True)
outer.Label = "Stirrup_Outer"
inner.Label = "Stirrup_Inner"
```

### Embedding Title Block (A3_Landscape_TD.svg)
```python
page = doc.addObject("TechDraw::DrawPage", "Sheet1")
tpl = doc.addObject("TechDraw::DrawSVGTemplate", "Template")
tpl.Template = FreeCAD.getResourceDir() + "Mod/TechDraw/Templates/ISO/A3_Landscape_TD.svg"
page.Template = tpl
doc.recompute()

# Populate title block fields
tpl.setEditFieldContent("FC-Title", "Reinforcement Section A-A")
tpl.setEditFieldContent("drawing_number", "STR-101")
tpl.setEditFieldContent("scale", "1:20")
tpl.setEditFieldContent("CreationDate", "2026-02-23")
tpl.setEditFieldContent("AuthorName", "Structural Engineer")
```

---

## Common Omissions (RED FLAGS)

❌ **Stirrups missing** — most dangerous, structural failure mode
❌ **No bar schedule** — contractor cannot order bars or verify quantities
❌ **No material spec** — concrete/steel grade undefined, may use wrong materials
❌ **No cover dimension** — durability compromised, structure may corrode
❌ **No cross-section** — contractor doesn't understand rebar arrangement
❌ **Blank title block** — drawing cannot be tracked or referenced
❌ **Individual line segments for rebar** — should use continuous polylines, cleaner rendering

---

## Verification Checklist for Self-Review

Before responding "LOOKS_GOOD" in drawing review, verify:

- [ ] Main reinforcement present with correct bar counts
- [ ] Stirrups/links clearly shown (for beams/columns)
- [ ] Cover dimensions dimensioned on drawing
- [ ] Overall width/height dimensions present
- [ ] Bar bending schedule visible in sheet (DrawViewSpreadsheet embedded)
- [ ] Material spec text block readable (concrete grade, steel grade, cover, exposure visible)
- [ ] Section titles present (e.g., "SECTION A-A, Scale 1:20")
- [ ] Title block template used (_TD.svg, not blank)
- [ ] Title block fields populated (title, drawing number, scale, date)
- [ ] All text readable, no overlapping dimensions or labels
- [ ] Scale math shown in code comment (geometry extent ÷ scale = sheet fit)

If ANY of these are missing or incomplete, this drawing is NOT construction-ready. Edit the page file to add the missing elements.
