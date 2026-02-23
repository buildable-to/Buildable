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
