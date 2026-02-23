# Drawing Sizes and Proportions

Standard sizes for structural engineering technical drawings on A3 Landscape.
Based on ISO 3098, ISO 128, ISO 129-1, ISO 5457, ISO 7200, ISO 5455.

---

## 1. Text Heights (on printed paper, scale-independent)

Text height does NOT change with drawing scale. These are final printed sizes.

| Element | Height (mm) | ISO Standard |
|---------|-------------|--------------|
| Dimension text | 2.5 | ISO 3098 (A3 minimum) |
| Annotations / notes | 2.5 | ISO 3098 |
| Bar marks (rebar callouts) | 3.5 | ISO 3098 + industry practice |
| View titles | 3.5 | ISO 3098 |
| Drawing title (title block) | 5.0 | ISO 3098 |

Standard ISO lettering heights: 1.8, 2.5, 3.5, 5.0, 7.0, 10, 14, 20 mm.
Always use one of these values.

### Calculating model-space text height for DrawViewDraft
Since `view.FontSize` controls text size in Draft model space and the view is scaled:
```
model_text_height = paper_text_height × scale_denominator
```
Example: 2.5mm dimension text at 1:50 → FontSize needs to produce 2.5mm on paper.

---

## 2. Line Weights (on printed paper, scale-independent)

ISO 128 standard widths: 0.13, 0.18, 0.25, 0.35, 0.50, 0.70, 1.00, 1.40, 2.00 mm.
Use the **0.25 / 0.35 / 0.50 / 1.00** group for A3 structural drawings.

| Element | Width (mm) | Line Type | Notes |
|---------|-----------|-----------|-------|
| **Reinforcement bars** | **0.70** | Continuous | Must be visually dominant |
| Concrete outline (visible) | 0.50 | Continuous | Wide |
| Concrete hidden edges | 0.35 | Dashed | Behind-view edges |
| Section cut line | 0.70 | Continuous | Matches rebar weight |
| Dimension lines | 0.25 | Continuous | Narrow |
| Extension lines | 0.25 | Continuous | Narrow |
| Center / axis lines | 0.25 | Chain (long-short-long) | Narrow |
| Hatching lines | 0.18–0.25 | Continuous | Narrow |
| Drawing border frame | 0.70 | Continuous | Extra-wide |

**Visual hierarchy rule:** Reinforcement > Concrete outline > Hidden edges > Dimensions/annotations.
Use no more than **4 distinct line weights** per drawing.

---

## 3. Dimension Annotations

### Terminator style
**Structural drawings use oblique tick marks (45°)**, not arrows.
- Tick mark: short line at 45° through the intersection of dimension and extension lines
- Tick length: ~2.5 mm on paper
- Drawn from lower-left to upper-right

### Proportions (all values in mm on paper)

| Parameter | Value | Notes |
|-----------|-------|-------|
| Extension line overshoot | 2.0 | Past the dimension line |
| Gap (object to extension line) | 1.5–2.0 | Keeps drawing clean |
| Text offset above dimension line | 1.0 | Centered on line |
| Minimum gap between dimension lines | 7.0 | Stacked dimensions |
| First dimension line from object | 10.0 | Prevents crowding |

### Dimension text placement
- Text placed **above** and **centered on** the dimension line
- Text reads left-to-right (horizontal dimensions) or bottom-to-top (vertical dimensions)
- When space is tight, text may be placed outside with a leader

---

## 4. A3 Landscape Sheet Layout (420 × 297 mm)

### Margins (ISO 5457)

| Edge | Margin (mm) | Notes |
|------|------------|-------|
| Left (binding/filing) | 20 | Wider for hole punching |
| Right | 10 | |
| Top | 10 | |
| Bottom | 10 | |

### Drawing space
- Total: **390 × 277 mm** (420−20−10 × 297−10−10)
- Title block: **180 mm wide**, bottom-right corner
- Title block height: typically 36–56 mm (template dependent)
- Usable area above title block: approximately **390 × 230 mm**

### View spacing
- Minimum **20–30 mm** between adjacent views
- Allow **8–10 mm** below/above each view for title/label
- Scale indicator text placed near each view title

### Border frame
- 0.70 mm continuous line around the drawing space
- Centering marks at midpoint of each edge (optional)

---

## 5. Standard Scales (ISO 5455)

| Scale | Typical Use in Structural |
|-------|--------------------------|
| 1:5 | Connection details, rebar bend details |
| 1:10 | Section details, joint details |
| 1:20 | Element cross-sections, local reinforcement details |
| 1:25 | Medium detail views |
| 1:50 | Structural plans, element elevations, typical sections |
| 1:100 | Floor plans, general arrangement |
| 1:200 | Site plans, overall building layouts |
| 1:500 | Site context plans |

### Scale selection rule
Pick the **largest scale that fits** the view within the available sheet area with margins for dimensions and labels. Always use a standard scale from this list.

### What changes with scale

| Property | Changes with scale? | Notes |
|----------|-------------------|-------|
| Text height on paper | NO | Always 2.5mm for dims, 3.5mm for titles |
| Line weight on paper | NO | Always per the table above |
| Level of detail | YES | Smaller scales → fewer details shown |
| Rebar representation | YES | 1:20 double-line, 1:50 single thick line, 1:100 single line |
| Hatching density | YES | May be adjusted for readability |

---

## 6. FreeCAD Implementation Notes

### Text sizing with DrawViewDraft
FreeCAD's `DrawViewDraft.FontSize` works in model space units, scaled by the view's `Scale` property. The relationship:
```
paper_text_size ≈ (FontSize / Scale) / 2    (FreeCAD's SVG formula)
```

To get **2.5mm** dimension text on paper:
- At Scale=0.01 (1:100): FontSize = 2.5 × 2 × 0.01 × 100 = **5.0**
- At Scale=0.02 (1:50): FontSize = 2.5 × 2 × 0.02 × 50 = **5.0**
- At Scale=0.05 (1:20): FontSize = 2.5 × 2 × 0.05 × 20 = **5.0**

In practice, FontSize ≈ 5.0 produces ~2.5mm text across common scales. For 3.5mm text (titles, bar marks), use FontSize ≈ 7.0.

### Line weight limitations
FreeCAD Draft objects have limited line weight control in TechDraw rendering. The `DrawViewDraft` renders all objects with the same line weight. To create visual hierarchy:
- Use separate groups for different line weight categories
- Create separate `DrawViewDraft` views with different `LineWidth` properties if supported
- Or accept uniform line weight and rely on line style (solid vs dashed) for distinction
