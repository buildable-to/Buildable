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

### Beam Section (Cross-section)
**MANDATORY:**
- Main rebar geometry (bottom + top bars, double-line + hooks)
- Shear reinforcement (stirrups d8/d10/d12 at specified spacing)
- Cover dimensions (top and bottom, AND side cover)
- Overall dimensions (depth, width)
- Section cut markers (A-A, B-B showing where this section is taken from)
- **⚠️ NOTE**: A cross-section alone is NOT complete. Must include a companion longitudinal elevation.

### Beam Elevation (Longitudinal section)
**MANDATORY:**
- Longitudinal concrete outline (full span shown)
- Main rebar shown along full span (bottom + top bars, double lines with hooks)
- Stirrups shown as vertical pairs at each stirrup position along span
- Stirrup spacing changes annotated (e.g., d8@100 at supports, d8@150 in mid-span)
- **Span dimension** (overall length — REQUIRED, no calculation possible without it)
- **Anchorage at both supports** — bar extensions into columns/walls with Ld dimension and label (e.g., "Ld = 800mm = 40d")
- Section cut markers (A-A, B-B showing where cross-sections are taken)
- Bar bending schedule (shared with cross-section sheet)
- Material specification (shared with cross-section sheet)
- **Bar shape diagrams** — schematic shape for each bar position (Pos 1, 2, 3...) with bend profile and key dimensions
- **General notes** — standard construction notes block (5-7 items: dimensions in mm, cutting/bending per EN, lap lengths, cover spacers, etc.)
- Title block (shared with cross-section sheet)

**⚠️ COMPLETE BEAM = BOTH VIEWS REQUIRED:**
A structurally complete beam drawing ALWAYS has two companion views:
1. **Cross-section** (perpendicular to span) — shows bar arrangement and stirrup layout
2. **Longitudinal elevation** (along span) — shows bar distribution, stirrup spacing zones, anchorage
Place both on the same TechDraw sheet if they fit, offset by ≥15000mm in X within the page file.

### Slab Section (One Direction)
**MANDATORY:**
- Bottom main reinforcement (running along section) as double lines
- Top reinforcement if cantilevered or two-way
- Transverse reinforcement (the other direction) shown as dots
- Cover dimensions (top, bottom, AND side cover)
- **Span dimension** (overall length — REQUIRED, no bar lengths can be calculated without it)
- Overall dimensions (thickness)
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

## CRITICAL MANDATORY RULES

### 1. BAR SCHEDULE: ALL POSITIONS REQUIRED

The bar bending schedule MUST include EVERY position declared in the drawing geometry.

**WRONG:** Schedule with only Pos 1 when geometry has Pos 1, 2, 3
```
| Pos | Ø (mm) | Shape | Length (mm) | Qty | Total Wt (kg) |
|-----|--------|-------|-------------|-----|---------------|
| 1   | 20     | Hook  | 3000        | 4   | 75.4          |
```

**CORRECT:** All positions listed
```
| Pos | Ø (mm) | Shape      | Length (mm) | Qty | Total Wt (kg) |
|-----|--------|------------|-------------|-----|---------------|
| 1   | 20     | Hook       | 3000        | 4   | 75.4          |
| 2   | 12     | Straight   | 2800        | 2   | 20.1          |
| 3   | 8      | Hook (135) | 500         | 12  | 18.8          |
```

**Impact of missing positions:** Contractor cannot order all bars, site confusion, incomplete steel delivery, work stoppage.

### 2. SPAN DIMENSION: REQUIRED FOR BEAMS AND SLABS

Without the overall span (or length), bar cut lengths CANNOT be calculated.

For beams and slabs, ALWAYS dimension the span:
- **Beams**: dimension along longitudinal elevation from support face to support face (or CL to CL)
- **Slabs**: dimension each direction of main reinforcement

This is the primary dimension — without it, the drawing is incomplete.

### 3. STIRRUP HOOK: 135° per EN 1992-1-1 §8.5

All stirrups and links MUST have a 135° hook bend, NOT a 90° closed corner.

**In geometry:**
- Show a small angled extension at one corner of the stirrup rectangular frame
- The hook angle should be approximately 135° (not sharp 90°)

**In labels:**
Always annotate stirrup spacing with the hook angle:
- ✗ WRONG: `Pos 3  d8@150`
- ✓ CORRECT: `Pos 3  d8@150 (135°)` or `Pos 3  d8@150 (135° hook)`

**Why:** EC2 hook is a ductility/pullout prevention requirement. A 90° corner can slip; 135° provides mechanical anchorage.

---

## Quick Reference: Code Snippets

### Bar Bending Schedule (Spreadsheet with CellEnd)
```python
sht = doc.addObject("Spreadsheet::Sheet", "BarSchedule")
headers = ["Pos", "Ø (mm)", "Shape", "Total Length (mm)", "Qty", "Unit Weight (kg/m)", "Total Weight (kg)"]
for col, h in enumerate(headers):
    cell = chr(65 + col) + "1"
    sht.set(cell, h)

# Add data rows with bar info
bars = [
    {"pos": "1", "dia": 20, "shape": "Straight", "length_mm": 3000, "qty": 4},
    {"pos": "2", "dia": 12, "shape": "Straight", "length_mm": 2800, "qty": 2},
    {"pos": "3", "dia": 8, "shape": "Hook", "length_mm": 500, "qty": 12},
]
# Fill spreadsheet with bar rows (omitted for brevity)

# Embed in TechDraw sheet
sched_view = doc.addObject("TechDraw::DrawViewSpreadsheet", "ScheduleView")
sched_view.Source = sht
page.addView(sched_view)
sched_view.CellStart = "A1"
sched_view.CellEnd = f"G{len(bars) + 1}"  # CRITICAL: must be explicit, default shows only 1 row
sched_view.X = 280
sched_view.Y = 80
```

**CRITICAL:** Without explicit `CellEnd`, TechDraw defaults to showing only the header row + 1 data row, regardless of how many data rows exist in the spreadsheet. Always set `CellEnd` to the last column letter and last row number, e.g., `"G7"` for 6 bar positions + 1 header row.

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
- [ ] Cover dimensions dimensioned on at least TWO edges (top/bottom AND side)
- [ ] **Anchorage shown and dimensioned at support ends** (Ld = Xmm = Xd)
- [ ] **Anchorage strategy consistent** (hooks-within-span OR straight-extensions, not both)
- [ ] Overall width/height/span dimensions present
- [ ] Bar bending schedule visible in sheet (DrawViewSpreadsheet embedded)
- [ ] **Bar schedule shows ALL positions** (Pos 1, 2, 3...) — CellEnd must be set explicitly
- [ ] **Bar shape diagrams present** for each position — small bent-shape sketch with dimensions
- [ ] **Stirrup hook dimensions labeled** on shape diagrams (e.g., "5d = 40mm")
- [ ] Material spec text block readable (concrete grade, steel grade, cover, exposure visible)
- [ ] **General notes block present** (at least 5 standard notes: dims in mm, bending per EN, lap length, spacers, etc.)
- [ ] Section titles present (e.g., "SECTION A-A, Scale 1:20")
- [ ] **Views positioned above Y=55mm** on sheet (no overlap with title block zone)
- [ ] All views fit horizontally (total extent < 380mm)
- [ ] Title block template used (_TD.svg, not blank)
- [ ] Title block fields populated (title, drawing number, scale, date)
- [ ] All text readable, no overlapping dimensions or labels
- [ ] Scale math shown in code comment (geometry extent ÷ scale = sheet fit)

If ANY of these are missing or incomplete, this drawing is NOT construction-ready. Edit the page file to add the missing elements.
