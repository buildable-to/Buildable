# Rebar Drawing Conventions for FreeCAD Draft

## Decision Rules

A reinforcement section ALWAYS shows TWO types of rebar representation:
- **DOUBLE LINES** for bars you see along their length (parallel to the cut)
- **FILLED DOTS** for bars going into/out of the page (perpendicular to the cut)

**YOU MUST USE BOTH.** Never draw all rebar as circles/dots — that is wrong.

### Which bars are parallel vs perpendicular?

In a slab or foundation section:
- The section cuts across the element. You see the slab thickness.
- **Bottom main bars** (the ones with spacing, e.g. d18/200): one direction runs ALONG
  the section plane (show as DOUBLE LINES with hooks), the other runs INTO the page
  (show as DOTS).
- **Rule**: In "Section A-A", show the FIRST-listed bottom rebar as DOUBLE LINES (parallel)
  and the second layer as DOTS (perpendicular). In "Section B-B" (the other cut direction),
  swap them.
- **Top bars**: same logic — show as DOUBLE LINES if they run along the section, DOTS if
  they run into the page.

### Representation details

**DOUBLE LINES** (bars parallel to cut):
- Draw as 2 continuous polylines (outer profile + inner profile) so corners connect properly
- Outer polyline: left hook tip → down corner → along bar bottom → up corner → right hook tip
- Inner polyline: left hook tip → down corner → along bar top → up corner → right hook tip
- Plus 2 short cap lines connecting outer/inner at each hook tip
- Bottom bars: hooks bend **UP**. Top bars: hooks bend **DOWN**.

**FILLED DOTS** (bars perpendicular to cut):
- `Draft.make_circle(diameter/2, placement)`
- Many bars (>10): show REPRESENTATIVE dots only — first 3, middle 3, last 3
- Few bars (≤10): show all dots

### Other rules
- **NO hatching** on reinforcement sections — hatching clutters the rebar detail. Only use
  hatching on formwork/structural sections (without rebar).
- **Labels**: `Pos N  [count]d[diameter]/[spacing]` with leader line from bar to label
- **Layer stacking**: Bottom layer 1 center = cover + d/2. Layer 2 = cover + d_layer1 + d/2.
  Top layer = thickness - cover - d/2.

---

## Complete Working Example

Foundation slab section showing all rebar patterns. Copy and adapt this code.

```python
import FreeCAD
import Draft
import math

doc = FreeCAD.ActiveDocument

# === REINFORCEMENT SECTION EXAMPLE ===
# Slab: 3000mm wide × 400mm thick
# Section cuts through the LONG axis (X direction)
#
# Pos A: d16 bottom, running along X → PARALLEL to cut → DOUBLE LINES with hooks UP
# Pos B: d16 bottom, running along Y → PERPENDICULAR to cut → DOTS
# Pos C: d12 top, running along X → PARALLEL to cut → DOUBLE LINES with hooks DOWN
#
# Layer stacking (from bottom face up):
#   Bottom layer 1 (Pos A): center Y = cover + d/2 = 30 + 8 = 38mm
#   Bottom layer 2 (Pos B): center Y = cover + d_layer1 + d/2 = 30 + 16 + 8 = 54mm
#   Top layer (Pos C):      center Y = thickness - cover - d/2 = 400 - 30 - 6 = 364mm

OX = 0
OY = SHEET_Y_OFFSET

SLAB_W = 3000
SLAB_T = 400
COVER = 30
HOOK = 200       # hook extension length (simplification of 10d)

DA = 16  # Pos A diameter
DB = 16  # Pos B diameter
DC = 12  # Pos C diameter

V = FreeCAD.Vector
draft_objects = []


# ============================================================
# CONCRETE OUTLINE (no hatching on rebar sections — it clutters the rebar detail)
# ============================================================
outline = Draft.make_wire([
    V(OX, OY, 0),
    V(OX + SLAB_W, OY, 0),
    V(OX + SLAB_W, OY + SLAB_T, 0),
    V(OX, OY + SLAB_T, 0),
], closed=True)
outline.Label = "ConcreteOutline"
draft_objects.append(outline)


# ============================================================
# POS A: d16 PARALLEL to cut → DOUBLE LINES + HOOKS UP
# (Bottom layer 1, running along the section plane)
# IMPORTANT: Use continuous polylines so hooks connect to bar body at corners!
# ============================================================
rA = DA / 2  # half-diameter = 8mm
yA = OY + COVER + rA  # bar center Y = 38mm from bottom

xA_start = OX + COVER          # bar starts at cover from left edge
xA_end = OX + SLAB_W - COVER   # bar ends at cover from right edge

# --- Outer profile: single continuous polyline ---
# Left hook top → left hook bottom corner → bar bottom → right hook bottom corner → right hook top
posA_outer = Draft.make_wire([
    V(xA_start - rA, yA + HOOK, 0),  # left hook tip (top)
    V(xA_start - rA, yA - rA, 0),    # corner: left hook meets bar bottom
    V(xA_end + rA, yA - rA, 0),      # bar bottom runs to right side
    V(xA_end + rA, yA + HOOK, 0),    # right hook tip (top)
], closed=False)
posA_outer.Label = "PosA_Outer"
draft_objects.append(posA_outer)

# --- Inner profile: single continuous polyline ---
# Left hook top → left hook top corner → bar top → right hook top corner → right hook top
posA_inner = Draft.make_wire([
    V(xA_start + rA, yA + HOOK, 0),  # left hook tip (top, inner)
    V(xA_start + rA, yA + rA, 0),    # corner: left hook meets bar top
    V(xA_end - rA, yA + rA, 0),      # bar top runs to right side
    V(xA_end - rA, yA + HOOK, 0),    # right hook tip (top, inner)
], closed=False)
posA_inner.Label = "PosA_Inner"
draft_objects.append(posA_inner)

# --- Cap lines at hook tips (connect outer to inner) ---
capA_L = Draft.make_wire([V(xA_start - rA, yA + HOOK, 0), V(xA_start + rA, yA + HOOK, 0)], closed=False)
capA_L.Label = "PosA_CapL"
draft_objects.append(capA_L)

capA_R = Draft.make_wire([V(xA_end - rA, yA + HOOK, 0), V(xA_end + rA, yA + HOOK, 0)], closed=False)
capA_R.Label = "PosA_CapR"
draft_objects.append(capA_R)


# ============================================================
# POS B: d16 PERPENDICULAR to cut → DOTS (representative sampling)
# (Bottom layer 2, running into the page)
# ============================================================
rB = DB / 2
yB = OY + COVER + DA + rB  # layer 2 center, above layer 1

# Calculate total bar count, then show representative subset
n_total = int((SLAB_W - 2 * COVER) / 200) + 1  # e.g. 15 bars at 200mm spacing
mid = n_total // 2
# Show first 3, middle 3, last 3 — avoids cluttering with 15+ dots
rep_indices = [0, 1, 2, mid - 1, mid, mid + 1, n_total - 3, n_total - 2, n_total - 1]

bar_x_start = OX + COVER + rB
spacing_actual = (SLAB_W - 2 * COVER) / (n_total - 1)

for i, idx in enumerate(rep_indices):
    x = bar_x_start + idx * spacing_actual
    dot = Draft.make_circle(rB, FreeCAD.Placement(V(x, yB, 0), FreeCAD.Rotation()))
    dot.Label = f"PosB_Dot{i}"
    draft_objects.append(dot)


# ============================================================
# POS C: d12 PARALLEL to cut → DOUBLE LINES + HOOKS DOWN
# (Top layer, hooks go DOWN into concrete mass)
# Same continuous polyline approach as Pos A, but hooks go DOWN
# ============================================================
rC = DC / 2  # half-diameter = 6mm
yC = OY + SLAB_T - COVER - rC  # top layer center

xC_start = OX + COVER
xC_end = OX + SLAB_W - COVER

# --- Outer profile: single continuous polyline ---
# Left hook bottom → left hook top corner → bar top → right hook top corner → right hook bottom
posC_outer = Draft.make_wire([
    V(xC_start - rC, yC - HOOK, 0),  # left hook tip (bottom)
    V(xC_start - rC, yC + rC, 0),    # corner: left hook meets bar top
    V(xC_end + rC, yC + rC, 0),      # bar top runs to right side
    V(xC_end + rC, yC - HOOK, 0),    # right hook tip (bottom)
], closed=False)
posC_outer.Label = "PosC_Outer"
draft_objects.append(posC_outer)

# --- Inner profile: single continuous polyline ---
posC_inner = Draft.make_wire([
    V(xC_start + rC, yC - HOOK, 0),  # left hook tip (bottom, inner)
    V(xC_start + rC, yC - rC, 0),    # corner: left hook meets bar bottom
    V(xC_end - rC, yC - rC, 0),      # bar bottom runs to right side
    V(xC_end - rC, yC - HOOK, 0),    # right hook tip (bottom, inner)
], closed=False)
posC_inner.Label = "PosC_Inner"
draft_objects.append(posC_inner)

# --- Cap lines at hook tips ---
capC_L = Draft.make_wire([V(xC_start - rC, yC - HOOK, 0), V(xC_start + rC, yC - HOOK, 0)], closed=False)
capC_L.Label = "PosC_CapL"
draft_objects.append(capC_L)

capC_R = Draft.make_wire([V(xC_end - rC, yC - HOOK, 0), V(xC_end + rC, yC - HOOK, 0)], closed=False)
capC_R.Label = "PosC_CapR"
draft_objects.append(capC_R)


# ============================================================
# LABELS WITH LEADERS
# ============================================================
label_x = OX + SLAB_W + 600  # labels to the right of the section

# Pos A label
ldr_a = Draft.make_wire([V(OX + SLAB_W - 200, yA, 0), V(label_x - 80, OY - 200, 0)], closed=False)
ldr_a.Label = "PosA_Leader"
draft_objects.append(ldr_a)
lbl_a = Draft.make_text(["Pos 1  15d16/200"], V(label_x, OY - 200, 0))
lbl_a.Label = "PosA_Label"
draft_objects.append(lbl_a)

# Pos B label
ldr_b = Draft.make_wire([V(OX + SLAB_W - 400, yB, 0), V(label_x - 80, OY - 600, 0)], closed=False)
ldr_b.Label = "PosB_Leader"
draft_objects.append(ldr_b)
lbl_b = Draft.make_text(["Pos 2  15d16/200"], V(label_x, OY - 600, 0))
lbl_b.Label = "PosB_Label"
draft_objects.append(lbl_b)

# Pos C label
ldr_c = Draft.make_wire([V(OX + SLAB_W - 200, yC, 0), V(label_x - 80, OY + SLAB_T + 200, 0)], closed=False)
ldr_c.Label = "PosC_Leader"
draft_objects.append(ldr_c)
lbl_c = Draft.make_text(["Pos 3  6d12"], V(label_x, OY + SLAB_T + 200, 0))
lbl_c.Label = "PosC_Label"
draft_objects.append(lbl_c)


# ============================================================
# COVER DIMENSIONS
# ============================================================
dim_cov_bot = Draft.make_linear_dimension(
    V(OX, OY, 0), V(OX, OY + COVER, 0),
    V(OX - 400, OY + COVER / 2, 0))
dim_cov_bot.Label = "Dim_CoverBot"
draft_objects.append(dim_cov_bot)

dim_cov_top = Draft.make_linear_dimension(
    V(OX, OY + SLAB_T - COVER, 0), V(OX, OY + SLAB_T, 0),
    V(OX - 400, OY + SLAB_T - COVER / 2, 0))
dim_cov_top.Label = "Dim_CoverTop"
draft_objects.append(dim_cov_top)


# ============================================================
# SECTION TITLE
# ============================================================
title = Draft.make_text(
    ["REINFORCEMENT SECTION A-A", "Scale 1:20"],
    V(OX + SLAB_W / 2 - 800, OY - 1500, 0))
title.Label = "SectionTitle"
draft_objects.append(title)

# === Group ===
grp = doc.addObject("App::DocumentObjectGroup", "RebarSectionGroup")
grp.Group = draft_objects

doc.recompute()
```

---

## Stirrups / Shear Reinforcement (MANDATORY for beams and columns)

Stirrups (also called links or ties) carry shear force and hold main bars in position. They are REQUIRED in all beam and column sections. Omitting stirrups makes the drawing incomplete and non-structural.

### Stirrup representation in section view

A stirrup shows as a **closed rectangle** (like a frame around the beam/column core) with double-line representation:
- **Outer wire**: from outer corner to outer corner
- **Inner wire**: set inward by the bar diameter, forming the other side of the rectangular frame

The stirrup should:
- Have its outer face at `cover` distance from the concrete edge
- Use double-line representation (outer + inner profiles)
- Show the hook at one corner (typically 135° bend)

### Stirrup drawing code pattern (in cross-section at position x=100mm)

```python
# Beam: 500mm wide, 600mm deep, d8 stirrups, 40mm cover
r = 4  # d8 → radius = 4mm
cx, cy = 100, 300  # center of stirrup frame
width, height = 500, 600  # concrete dimensions
cover = 40

# Outer profile
outer = Draft.make_wire([
    V(cx - width/2 + cover + r, cy - height/2 + cover + r, 0),
    V(cx + width/2 - cover - r, cy - height/2 + cover + r, 0),
    V(cx + width/2 - cover - r, cy + height/2 - cover - r, 0),
    V(cx - width/2 + cover + r, cy + height/2 - cover - r, 0),
], closed=True)
outer.Label = "Stirrup_Outer"

# Inner profile (offset by 2*r to show bar thickness)
inner = Draft.make_wire([
    V(cx - width/2 + cover + 3*r, cy - height/2 + cover + 3*r, 0),
    V(cx + width/2 - cover - 3*r, cy - height/2 + cover + 3*r, 0),
    V(cx + width/2 - cover - 3*r, cy + height/2 - cover - 3*r, 0),
    V(cx - width/2 + cover + 3*r, cy + height/2 - cover - 3*r, 0),
], closed=True)
inner.Label = "Stirrup_Inner"
```

### Stirrup spacing annotation

Label the stirrups group or section with:
`Pos N  d[diameter]@[spacing]`
Example: `Pos 4  d8@150` means d8 bar diameter, 150mm spacing

### Slabs: Transverse Reinforcement (replaces stirrups)

For slabs, stirrups don't apply. Instead, show the **transverse (perpendicular) main reinforcement** as dots (same as the parallel main bars shown as dots in the cross-section rule):
- Main bars in one direction: double lines
- Transverse bars in other direction: filled dots
- Both must be labeled with their positions and spacing

---

## Anchorage at Supports (MANDATORY for beam longitudinal bars)

Bars cannot just end at the concrete face — they must extend into the support (wall, column, or bearing pad) to develop full tensile capacity. The anchorage length (Ld) depends on concrete strength, steel grade, and bar diameter.

### Anchorage length values (EC2 simplified)

For B500B reinforcing steel in typical concrete grades:

| Concrete | d20 straight | d20 with hook | d16 straight | d16 with hook |
|----------|--------------|---------------|--------------|---------------|
| C25/30   | 880mm (44d) | 616mm (31d)   | 704mm (44d)  | 493mm (31d)   |
| C30/37   | 760mm (38d) | 532mm (27d)   | 608mm (38d)  | 426mm (27d)   |
| C35/45   | 680mm (34d) | 476mm (24d)   | 544mm (34d)  | 381mm (24d)   |

**Rule of thumb:** Ld = 40d (straight), Ld = 28d (with standard hook). The hook reduces required anchorage by ~30%.

### Geometry pattern

Show anchorage on the beam elevation (longitudinal section). The bar extends BEYOND the span face by Ld into the support column or wall:

```python
# Example: bottom bar (Pos 1, d20) anchorage into right support
Ld = 40 * DA  # = 40 * 20 = 800mm for d20 straight bar

# Bar extension past span end (shown as single or dashed line)
anc_line = Draft.make_wire([
    V(OX + SPAN, yA, 0),          # right edge of beam section
    V(OX + SPAN + Ld, yA, 0),     # bar continues Ld into support
], closed=False)
anc_line.Label = "Anc_Pos1_Right"
draft_objects.append(anc_line)

# Dimension the anchorage length
anc_dim = Draft.make_linear_dimension(
    V(OX + SPAN, yA, 0),
    V(OX + SPAN + Ld, yA, 0),
    V(OX + SPAN + Ld/2, yA - 300, 0))  # dimension line below
anc_dim.Label = "Dim_Anc_Right"
draft_objects.append(anc_dim)

# Label: "Ld = 800mm = 40d"
anc_txt = Draft.make_text([f"Ld = {Ld}mm = 40d"],
    V(OX + SPAN + Ld/2, yA - 600, 0))
anc_txt.Label = "AncLabel_Right"
draft_objects.append(anc_txt)

# Repeat for left support (same Ld value)
```

### Where to show anchorage

- **Bottom bars** (Pos 1): show on BOTH ends of the beam elevation
- **Top bars** (Pos 2): show only at continuous supports (where negative bending exists); omit at simple supports
- **Simply supported beam**: bottom bars only, both ends. Top bars don't need anchorage.
- **Continuous or cantilever**: all longitudinal bars need anchorage at every support face

---

## Bar Shape Diagrams (MANDATORY for production drawings)

Every position in the bar bending schedule must have a companion shape diagram — a small schematic showing the bar's bent profile with critical dimensions. Fabricators read these diagrams to understand how to bend each bar.

### Components of a shape diagram

Each shape diagram shows:
1. **Bar outline** — polyline showing the bent shape
2. **Total length** — labeled on the straight section
3. **Hook extensions** — labeled with length (Lh = 10d typically)
4. **Position number** — e.g. "Pos 1", "Pos 3"
5. **Shape code** (optional) — ISO/EN standard shape code (e.g. "Type 11")

### Common shape patterns

#### Type 11 — Straight bar with 180° hooks (bottom bars with hooks)

```python
# Shape diagram for Pos 1: d20 hook bars, total length 6400mm
ox, oy = 1000, 500  # position in Draft space
DA = 20
bar_len = 6400
hook = 200  # 10*DA = 10*20 = 200mm (standard)

# Outline: left hook (up) → straight section → right hook (up)
shp = Draft.make_wire([
    V(ox, oy + hook, 0),           # left hook tip
    V(ox, oy, 0),                  # left corner (where straight begins)
    V(ox + bar_len, oy, 0),        # straight section centerline
    V(ox + bar_len, oy + hook, 0), # right hook tip
], closed=False)
shp.Label = "Shape_Pos1_Outline"
draft_objects.append(shp)

# Dimension: total bar length
dim_total = Draft.make_linear_dimension(
    V(ox, oy - 100, 0), V(ox + bar_len, oy - 100, 0),
    V(ox + bar_len/2, oy - 400, 0))
dim_total.Label = "Shape_Pos1_Length"
draft_objects.append(dim_total)

# Label: "Pos 1  6400mm" or "Pos 1  d20 Hook"
lbl = Draft.make_text(["Pos 1", "d20", f"{bar_len}mm"], V(ox + bar_len/2 - 200, oy + hook + 200, 0))
lbl.Label = "Shape_Pos1_Label"
draft_objects.append(lbl)
```

#### Type 51 — Stirrup/link with 135° hook

```python
# Shape diagram for Pos 3: d8 stirrups, inner dimensions (b-2r)×(h-2r)
ox, oy = 1000, 1200  # below the Type 11 diagram
DS = 8
r = DS / 2
inner_w = 280  # calculated from concrete width - 2*cover - DS
inner_h = 450  # calculated from concrete depth - 2*cover - DS
hook_ext = 100  # 10*DS = 80mm, draw a bit more for visibility

# Outer rectangle (outer face of stirrup bar)
shp_outer = Draft.make_wire([
    V(ox, oy, 0),
    V(ox + inner_w + 2*r, oy, 0),
    V(ox + inner_w + 2*r, oy + inner_h + 2*r, 0),
    V(ox, oy + inner_h + 2*r, 0),
], closed=True)
shp_outer.Label = "Shape_Stirrup_Outer"
draft_objects.append(shp_outer)

# Inner rectangle (inner face of stirrup bar)
shp_inner = Draft.make_wire([
    V(ox + r, oy + r, 0),
    V(ox + inner_w + r, oy + r, 0),
    V(ox + inner_w + r, oy + inner_h + r, 0),
    V(ox + r, oy + inner_h + r, 0),
], closed=True)
shp_inner.Label = "Shape_Stirrup_Inner"
draft_objects.append(shp_inner)

# 135° hook at one corner (upper-left, drawn at 45° angle)
import math
hx = hook_ext * math.cos(math.radians(45))  # 70.7mm
hy = hook_ext * math.sin(math.radians(45))
hook_line = Draft.make_wire([
    V(ox, oy + inner_h + 2*r, 0),  # corner start
    V(ox - hx, oy + inner_h + 2*r + hy, 0),  # 135° extension (upper-left)
], closed=False)
hook_line.Label = "Shape_Stirrup_Hook"
draft_objects.append(hook_line)

# Dimension: inner width × height
dim_w = Draft.make_linear_dimension(
    V(ox, oy - 100, 0), V(ox + inner_w + 2*r, oy - 100, 0),
    V(ox + (inner_w + 2*r)/2, oy - 300, 0))
dim_h = Draft.make_linear_dimension(
    V(ox + inner_w + 3*r, oy, 0), V(ox + inner_w + 3*r, oy + inner_h + 2*r, 0),
    V(ox + inner_w + 5*r, oy + (inner_h + 2*r)/2, 0))
dim_w.Label = "Shape_Stirrup_W"
dim_h.Label = "Shape_Stirrup_H"
draft_objects.append(dim_w)
draft_objects.append(dim_h)

# Label: "Pos 3  d8@150 (135°)"
lbl = Draft.make_text(["Pos 3", "d8 Stirrup", "(135° hook)"],
    V(ox + (inner_w + 2*r)/2 - 100, oy + inner_h + 3*r + 200, 0))
lbl.Label = "Shape_Stirrup_Label"
draft_objects.append(lbl)
```

### Grouping and placement

Group all shape diagrams together and create a separate DrawViewDraft view at smaller scale (1:5 or 1:10) placed beside or below the bar bending schedule on the TechDraw sheet:

```python
shapes_objects = [...]  # all shape wires, dimensions, labels
shapes_grp = doc.addObject("App::DocumentObjectGroup", "BarShapes_Group")
shapes_grp.Group = shapes_objects

# In TechDraw page setup:
shapes_view = doc.addObject("TechDraw::DrawViewDraft", "ShapesView")
shapes_view.Source = shapes_grp
shapes_view.Scale = 0.1  # 1:10
page.addView(shapes_view)
shapes_view.X = 20   # right side of schedule
shapes_view.Y = 80
```

---

## Quick Reference

| Bar d (mm) | Half-d (r) | Hook length (10d) | Bend radius |
|------------|-----------|-------------------|-------------|
| 12 | 6 | 120 | 24mm (2d, d≤16) |
| 16 | 8 | 160 | 32mm (2d, d≤16) |
| 18 | 9 | 180 | 63mm (3.5d, d>16) |
| 20 | 10 | 200 | 70mm (3.5d, d>16) |
| 25 | 12.5 | 250 | 87.5mm (3.5d, d>16) |

Bar label format: `Pos N  [count]d[diameter]/[spacing]`
Hook direction: bottom bars → UP, top bars → DOWN
