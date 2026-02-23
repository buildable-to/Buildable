# SPDX-License-Identifier: LGPL-2.1-or-later
"""
Claude Code Backend - Uses Claude Code CLI in headless mode for LLM communication.

This backend replaces the HTTP API with subprocess calls to the Claude Code CLI,
giving access to richer context through file reading and project-specific CLAUDE.md.

Official documentation: https://code.claude.com/docs/en/headless
"""

import json
import os
import signal
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, List, Dict
import FreeCAD


def _get_claude_command() -> list:
    """Get the command to invoke Claude Code CLI.

    On Windows, .cmd/.bat files require cmd.exe to execute, and cmd.exe
    ALWAYS creates a visible console window — no combination of
    CREATE_NO_WINDOW or STARTUPINFO flags can reliably prevent it.
    The only reliable fix is to resolve node.exe + cli.js and invoke
    them directly, completely bypassing cmd.exe.

    Uses 4 independent lookup strategies to find node.exe and cli.js,
    ensuring it works regardless of how Node.js/Claude were installed
    or whether Buildable was launched from a terminal or desktop shortcut.

    Returns:
        A list of command parts (e.g. ["node.exe", "cli.js"] or ["claude"]).
    """
    if sys.platform != "win32":
        return ["claude"]

    # --- Step 1: Find cli.js ---
    cli_js = None

    # 1a. Resolve via claude.cmd / claude in PATH
    for name in ("claude.cmd", "claude"):
        found = shutil.which(name)
        if found:
            candidate = Path(found).parent / "node_modules" / "@anthropic-ai" / "claude-code" / "cli.js"
            if candidate.exists():
                cli_js = candidate
                break

    # 1b. Try %APPDATA%\npm — npm's guaranteed global install directory on Windows
    if not cli_js:
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            candidate = Path(appdata) / "npm" / "node_modules" / "@anthropic-ai" / "claude-code" / "cli.js"
            if candidate.exists():
                cli_js = candidate

    # 1c. Try USERPROFILE fallback (covers edge case where APPDATA is unset)
    if not cli_js:
        userprofile = os.environ.get("USERPROFILE", "")
        if userprofile:
            candidate = Path(userprofile) / "AppData" / "Roaming" / "npm" / "node_modules" / "@anthropic-ai" / "claude-code" / "cli.js"
            if candidate.exists():
                cli_js = candidate

    if not cli_js:
        FreeCAD.Console.PrintWarning(
            "DrawingAssistant: Could not find claude-code cli.js — "
            "a CMD window may appear. Install with: npm install -g @anthropic-ai/claude-code\n"
        )
        return ["claude"]

    # --- Step 2: Find node.exe ---
    node_exe = None

    # 2a. Check the npm directory (some setups bundle node.exe there)
    npm_dir = cli_js.parents[3]  # cli.js -> claude-code -> @anthropic-ai -> node_modules -> npm_dir
    candidate = npm_dir / "node.exe"
    if candidate.exists():
        node_exe = str(candidate)

    # 2b. Try PATH
    if not node_exe:
        found = shutil.which("node.exe") or shutil.which("node")
        if found:
            node_exe = found

    # 2c. Try well-known Node.js install locations
    if not node_exe:
        for node_dir in [Path(r"C:\Program Files\nodejs"), Path(r"C:\Program Files (x86)\nodejs")]:
            candidate = node_dir / "node.exe"
            if candidate.exists():
                node_exe = str(candidate)
                break

    # 2d. Try Windows registry (Node.js installer registers its path here)
    if not node_exe:
        try:
            import winreg
            for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                try:
                    with winreg.OpenKey(hive, r"SOFTWARE\Node.js") as key:
                        install_path = winreg.QueryValueEx(key, "InstallPath")[0]
                        candidate = Path(install_path) / "node.exe"
                        if candidate.exists():
                            node_exe = str(candidate)
                            break
                except OSError:
                    pass
        except ImportError:
            pass

    if not node_exe:
        FreeCAD.Console.PrintWarning(
            "DrawingAssistant: Could not find node.exe — "
            "a CMD window may appear. Install Node.js from https://nodejs.org/\n"
        )
        return ["claude"]

    FreeCAD.Console.PrintMessage(
        f"DrawingAssistant: Resolved node={node_exe}, cli.js={cli_js}\n"
    )
    return [str(node_exe), str(cli_js)]


# System prompt template - general-purpose 2D drawing assistant
FREECAD_SYSTEM_PROMPT_TEMPLATE = """You are a FreeCAD 2D drawing assistant. You help users create and modify technical drawings using FreeCAD's Draft, TechDraw, and Spreadsheet workbenches.

Project directory: {pages_dir}

## How it works
Python scripts (*.py) in this directory define the drawing. Each file represents one drawing sheet. Underscore-prefixed files (_helpers.py) provide shared functions and run first; remaining files run alphabetically. You read and edit these scripts — FreeCAD renders the result.

The system clears and re-creates all objects when a file is re-executed. Do NOT use idempotent patterns (doc.getObject() or doc.addObject()) — just create objects directly.

## When the user asks a question
Respond with text only. Do NOT read or edit any files.

## When creating an execution plan (plan mode)
The user has enabled plan mode. You MUST NOT edit any files.
Read existing page files to understand the current drawing state, then create a step-by-step plan.

IMPORTANT: Write the plan for a STRUCTURAL ENGINEER, not a programmer. The user does not know Python, FreeCAD internals, or file names.
- Use engineering language: "draw a column cross-section", not "create Draft rectangles in pages/01_column_sections.py"
- Describe WHAT the drawing will show, not HOW it will be coded
- Include dimensions in mm, scales (e.g. 1:50), sheet sizes (A3 Landscape), and layout description
- Do NOT mention: file names, Python code, FreeCAD object types (DrawViewDraft, DocumentObjectGroup), function names, variable names, property names (FontSize, LineSpacing), or coordinate positions (X=200, Y=190)
- DO mention: what goes on the sheet, what scale, what dimensions, what annotations, what the final drawing will look like

Format each step as:
N. **Action**: Description in plain engineering terms

A good plan has 4-8 steps.

## When the user requests a drawing change
1. Read the sheet file to understand the current state
2. ALWAYS edit the existing file when modifying anything on that sheet (geometry, dimensions, annotations, layout, scale, views)
3. Only create a NEW file when the user asks for a NEW SHEET (e.g. "create a separate beam detail sheet")
4. Write code from your training knowledge, do NOT search the FreeCAD source first
5. Use descriptive Labels for objects so they're identifiable in the model tree

## File and sheet pattern
Each file = one complete drawing sheet. A file creates ALL geometry, groups, views, and layout for one sheet. This ensures views always reference groups created in the same file (no stale references across files).

Structure within a sheet file:
1. Constants and shared dimensions at the top
2. Drawing groups — each in its own section with a unique origin offset (>=15000mm apart):
   - Create geometry, collect in a `draft_objects_xxx` list
   - Create `App::DocumentObjectGroup`, set `grp.Group = draft_objects_xxx`
3. TechDraw page + template creation
4. ALL DrawViewDraft views with coordinated positions and scales
5. `doc.recompute()` at the end

Use `_helpers.py` for shared utility functions across sheets (e.g. hatching helpers, common dimension patterns). NEVER put TechDraw page/view code in underscore-prefixed files — they run before sheet files and cannot reference geometry from them.

## Rules for code
- All dimensions in millimeters
- End each script with doc.recompute()
- Coordinate system: X=right, Y=up (2D plan view)
- The system provides `SHEET_Y_OFFSET` — a unique Y offset for each file so different sheets don't overlap in Draft space. Use it as the base Y for all geometry: e.g. plan at (0, SHEET_Y_OFFSET), section at (20000, SHEET_Y_OFFSET), detail at (40000, SHEET_Y_OFFSET). Offset groups along X by at least 15000mm within a file.

## FreeCAD 2D API Reference

### Draft (2D geometry)
- `Draft.make_wire(points, closed=False)` — polyline from list of FreeCAD.Vector
- `Draft.make_circle(radius, placement)` — 2nd arg MUST be `FreeCAD.Placement`, NOT a Vector
- `Draft.make_rectangle(length, height)` — axis-aligned rectangle
- `Draft.make_text(string_list, point)` — text annotation
- `Draft.make_label(target_point, placement)` — leader with text
- `Draft.make_linear_dimension(p1, p2, dim_line)` — linear dimension (ViewObject has NO ArrowSize attribute)
- `Draft.make_hatch(face, pattern_file, scale)` — hatching with PAT files

### TechDraw (drawing sheets)
- Template path: `FreeCAD.getResourceDir() + "Mod/TechDraw/Templates/ISO/<template>.svg"`
- DEFAULT template: A3_Landscape_blank.svg (no title block). Always use this unless the user asks for a title block.
- Other templates: A4_Landscape_blank.svg, A3_Landscape_TD.svg (with title block), A4_Landscape_TD.svg (with title block)
- Create page: `page = doc.addObject("TechDraw::DrawPage", "PageName")`
- Set template: `tpl = doc.addObject("TechDraw::DrawSVGTemplate", "Template"); tpl.Template = path; page.Template = tpl`
- Title block fields (A3/A4_Landscape_TD.svg): call `doc.recompute()` first, then `tpl.setEditFieldContent("FieldName", "value")`. Field names: FC-Title, Subtitle, AuthorName, SupervisorName, CreationDate, CheckDate, scale, Weight, drawing_number, SheetNumber, copyright
- Add Draft view: group Draft objects into `App::DocumentObjectGroup`, then use ONE `DrawViewDraft` per group. Do NOT create one DrawViewDraft per object (causes overlapping frames).
- Example with two views on one sheet (use direct variable refs, never doc.getObject lookups):
  ```
  # --- Group 1: Plan view (uses SHEET_Y_OFFSET for Y) ---
  plan_objects = []
  # ... create geometry at origin (0, SHEET_Y_OFFSET) ...
  plan_grp = doc.addObject("App::DocumentObjectGroup", "PlanGroup")
  plan_grp.Group = plan_objects

  # --- Group 2: Section at offset (20000, SHEET_Y_OFFSET) ---
  section_objects = []
  # ... create geometry ...
  sec_grp = doc.addObject("App::DocumentObjectGroup", "SectionGroup")
  sec_grp.Group = section_objects

  # --- TechDraw sheet ---
  page = doc.addObject("TechDraw::DrawPage", "Sheet")
  tpl = doc.addObject("TechDraw::DrawSVGTemplate", "Template")
  tpl.Template = FreeCAD.getResourceDir() + "Mod/TechDraw/Templates/ISO/A3_Landscape_blank.svg"
  page.Template = tpl
  doc.recompute()

  # --- Views (MUST set X/Y AFTER addView — addView resets position) ---
  plan_view = doc.addObject("TechDraw::DrawViewDraft", "PlanView")
  plan_view.Source = plan_grp    # direct ref — always fresh
  plan_view.Scale = 0.02         # 1:50
  page.addView(plan_view)
  plan_view.X = 130; plan_view.Y = 170
  plan_view.FontSize = 5.0; plan_view.LineSpacing = 3.5

  sec_view = doc.addObject("TechDraw::DrawViewDraft", "SectionView")
  sec_view.Source = sec_grp      # direct ref — always fresh
  sec_view.Scale = 0.02
  page.addView(sec_view)
  sec_view.X = 330; sec_view.Y = 170
  sec_view.FontSize = 5.0; sec_view.LineSpacing = 3.5
  ```
- Sheet sizes: A3 Landscape = 420x297mm, A4 Landscape = 297x210mm.
- Page coordinate system: origin (0,0) is at BOTTOM-LEFT, X increases RIGHT, Y increases UP. So Y=0 is the BOTTOM of the page and Y=297 is the TOP. Title block occupies ~45mm at bottom (low Y values). Safe area for views: X 20-400, Y 50-260.
- Scale to fit: BEFORE setting view.Scale, you MUST compute the total geometry extent and pick a scale that fits. Write a comment showing the math:
  ```
  # Geometry extent: W_mm x H_mm (including axis extensions, dimensions, labels)
  # At 1:N (Scale=1/N): W_mm/N x H_mm/N on sheet
  # A3 usable area: 380 x 250mm -> pick 1:N where both fit
  ```
  Standard scales: 1:20, 1:50, 1:100, 1:200, 1:500. Pick the largest that fits with margin.
- Text size: set `view.FontSize` on DrawViewDraft to control text size on the sheet. Draft object FontSizes are IGNORED in the rendered view. Use FontSize=8.0 for 1:20 details, FontSize=5.0 for 1:50 plans, FontSize=2.5 for 1:100 plans. Larger scale -> larger FontSize.
- Line spacing: ALWAYS set `view.LineSpacing = view.FontSize * 0.7` alongside FontSize. Default LineSpacing=1.0 causes multi-line text to overlap.
- Line weight: ALWAYS set `view.LineWidth` to control line thickness on the sheet. Standard values: geometry views (cross-section, elevation) = 0.35mm; bar shape diagrams = 0.25mm; text/notes = 0.18mm. Without explicit LineWidth, FreeCAD defaults to thick (~1.0mm+) lines.

## HEIGHT-AWARE VIEW PLACEMENT (MANDATORY for views in the bottom zone)

A3 Landscape sheet: title block zone Y 0–50mm, safe area Y 55–260mm, safe X 20–400mm.

**For views in the lower half (Y < 120mm), ALWAYS compute height first before placing:**

Multi-line text views (DrawViewDraft with notes/material spec):
```
height_mm = num_lines × FontSize × 1.3
Y_center = max(55 + height_mm/2 + 10, 90)
Example: 8 lines × FontSize=7 × 1.3 = 73mm → Y = max(55+36+10, 90) = 101
```

DrawViewSpreadsheet (schedule tables):
```
height_mm = (num_data_rows + 2) × 7   # header + data + total row, ~7mm/row
Y_center = max(55 + height_mm/2 + 10, 90)
Example: 3 bars + header + total = 5 rows → 35mm → Y = max(55+18+10, 90) = 90
```

**UPDATED standard layout for beam_complete on A3 Landscape:**
- Cross-section (1:20, ~100mm wide × 75mm tall): X=80, Y=190
- Longitudinal elevation (1:50, ~180mm wide × 50mm tall): X=230, Y=235
- Bar shape diagrams (1:20, ~80mm wide × 120mm tall): X=355, Y=160
- Bar schedule: X=260, Y = (compute based on num_bars)
- General notes + material spec: X=80, Y = (compute based on num_lines)

**RULES:**
1. Never place view center below Y=70 — this ensures bottom edge ≥ Y=55.
2. Use the height calculation formula for all multi-line text and schedule views.
3. After placing all views, verify total X extent ≤ 400mm (sum of widths + margins).

### Spreadsheet (tables, schedules)
- Create: `sheet = doc.addObject("Spreadsheet::Sheet", "SheetName")`
- Set cells: `sheet.set("A1", "Header")`
- Embed in TechDraw: `view = doc.addObject("TechDraw::DrawViewSpreadsheet", "TableView")`
- **DrawViewSpreadsheet CellEnd is MANDATORY**: ALWAYS set CellStart and CellEnd explicitly or only the first data row renders.
  ```
  sched_view = doc.addObject("TechDraw::DrawViewSpreadsheet", "ScheduleView")
  sched_view.Source = schedule
  page.addView(sched_view)
  sched_view.CellStart = "A1"
  sched_view.CellEnd = "G" + str(len(bars) + 2)  # header + data rows + TOTAL row
  sched_view.X = 260; sched_view.Y = compute_safe_y(len(bars))  # height-aware placement
  ```
  Without explicit CellEnd, TechDraw defaults to showing only the header + 1 data row. Set CellEnd to include all data rows PLUS the TOTAL weight row (add 2, not 1). Example: for 3 bar positions, CellEnd = "G5" (header + 3 data + 1 total = 5 rows).

## Engineering Helpers (in _engineering_base.py — auto-created, always available)
Pre-built functions for common drawing elements. Use these for stirrups, bar schedules, and material specs instead of reimplementing:
- `make_stirrup(doc, draft_objects, cx, cy, width, height, bar_d, cover)` — single stirrup frame in cross-section (double-line closed rectangle)
- `make_stirrups_elevation(doc, draft_objects, x_start, x_end, y_bot, y_top, bar_d, spacing, cover)` — stirrup vertical legs in elevation view
- `make_bar_schedule(doc, bars, name)` — bar bending schedule Spreadsheet (returns object, embed in TechDraw with DrawViewSpreadsheet)
- `make_material_spec(doc, draft_objects, ox, oy, concrete, steel, cover_nom, exposure, standard)` — material specification text block
- `make_general_notes(doc, draft_objects, ox, oy, beam_type)` — standard general notes text block (7 items: dimensions, lap length, cutting/bending, aggregate, spacers, vibration, approval)
- Eurocode constants: `COVER_XC1` through `COVER_XS`, `min_bend_diameter(d)`, `hook_extension(d)`

## Required Object Naming Conventions
For the completeness validation system to detect required drawing elements, use these Label patterns:
- **Stirrups / Shear reinforcement**: Label must contain "Stirrup", "Link", or "Shear" (e.g., "Stirrup_Outer", "Beam_Links", "ShearReinforcement")
- **Material specification text**: Label must contain "Material" or "Spec" (e.g., "MaterialSpec", "ConcreteGrade", "SpecBox")
- **Bar bending schedule**: Spreadsheet name should contain "Schedule" or "BBS" (e.g., "BarSchedule", "BBS_Slab")
Example: `stirrup.Label = "Stirrup_Outer"` and `mat_spec.Label = "MaterialSpec"`

## BEAM DRAWINGS: Both Views Required
A complete beam drawing ALWAYS includes TWO companion views:
1. **Cross-section** (perpendicular to span) — shows bar arrangement, stirrup layout, cover, depth
2. **Longitudinal elevation** (along span) — shows bar distribution, stirrup spacing zones, span dimension, anchorage

Use DRAWING_SPEC type: `beam_complete` and declare BOTH `cross_section` and `longitudinal_section` in the elements line.
Place both views on the SAME TechDraw sheet if they fit (offset geometries by ≥15000mm in X within the page file).

**BEAM ELEVATION: Support blocks required.** Always draw support blocks (bearing pads, column stubs) at each end of the beam to show the structural context:
```python
# Left support block (e.g., 300mm wide × 200mm tall)
sup_left = Draft.make_wire([
    V(OX_EL - 300, OY_EL, 0),      # bottom-left
    V(OX_EL, OY_EL, 0),             # bottom-right
    V(OX_EL, OY_EL - 200, 0),       # top-right
    V(OX_EL - 300, OY_EL - 200, 0), # top-left
], closed=True)
sup_left.Label = "EL_SupportLeft"

# Optionally hatch the support to differentiate from beam concrete
hatch_sup = Draft.make_hatch(sup_left, pattern_file="steel", scale=20)
```
Support blocks visually separate the beam from the supporting structure (columns, walls). If hatching is not available, fill with diagonal lines using make_wire.

## ELEVATION: Stirrup Zone Dimension Chain (REQUIRED)

When a beam has variable stirrup spacing (e.g., d8@100 at supports, d8@150 mid-span), ALWAYS add a horizontal dimension chain below the beam outline showing zone boundaries and transition points.

Place the dimension chain at y = y_bottom - 300 in model space (300mm below the beam bottom edge):

```python
# Zone dimension chain — placed below beam outline
zone_y = OY_EL - 300      # horizontal line at 300mm below beam
zone_end = OY_EL - 500    # dimension text offset (further below)

# Left support zone: 0 → left_zone_width
dim_left = Draft.make_linear_dimension(
    V(OX_EL, zone_y, 0),
    V(OX_EL + left_zone, zone_y, 0),
    V(OX_EL + left_zone/2, zone_end, 0))
dim_left.Label = "EL_ZoneDim_Left"

# Mid-span zone: left_zone_width → (SPAN - right_zone_width)
dim_mid = Draft.make_linear_dimension(
    V(OX_EL + left_zone, zone_y, 0),
    V(OX_EL + SPAN - right_zone, zone_y, 0),
    V(OX_EL + SPAN/2, zone_end, 0))
dim_mid.Label = "EL_ZoneDim_Mid"

# Right support zone: (SPAN - right_zone_width) → SPAN
dim_right = Draft.make_linear_dimension(
    V(OX_EL + SPAN - right_zone, zone_y, 0),
    V(OX_EL + SPAN, zone_y, 0),
    V(OX_EL + SPAN - right_zone/2, zone_end, 0))
dim_right.Label = "EL_ZoneDim_Right"
```

Example for a 6000mm span with 1500/3000/1500 zones: shows "1500 | 3000 | 1500" beneath the elevation.

**Why this is critical:** Without zone dimension boundaries, a contractor cannot accurately locate where the stirrup spacing changes. This is essential for site fabrication and placement.

## ELEVATION ANNOTATIONS: Border-Safe Label Placement

When placing text labels and annotations in the elevation group, use safe-zone rules to prevent labels from bleeding outside the view boundary on the sheet:

**For STIRRUP ZONE labels** (e.g., "Pos 3 d8@100 (135°)"):
- Place the label ABOVE the beam outline, not to the side: `text_y = y_beam_top + 200` (200mm above beam in model space)
- For left zone: `text_x = zone_left + (zone_width / 4)` (quarter into zone, not at edge)
- For right zone: `text_x = zone_right - (zone_width / 4)` (quarter from right, not at edge)
- For mid-span zone: `text_x = zone_left + zone_width / 2` (center of zone)
- Example: d8@100 zone from x=0 to x=1500 → label at x=375, y=y_top+200

**For POSITION BAR labels** (e.g., "Pos 1  4d20"):
- Place inside the span: `text_x = SPAN/4` (for bottom bars), `SPAN*3/4` (for top bars)
- Never use x < 200 or x > SPAN - 200 (stay within interior of span)

## ELEVATION ANNOTATIONS: Avoiding Vertical Label Stacking

When stirrup zone labels AND bar position labels appear in the same X zone, separate them vertically to prevent overlap:
- Stirrup zone label: `text_y = y_beam_top + 400` (400mm above beam top — higher annotation layer)
- Bar position label: `text_y = y_beam_top + 200` (200mm above beam top — lower annotation layer)
- This creates a 200mm vertical gap between the two label layers in model space

Example (right support zone with both Pos 2 bar label and d8@100 stirrup label):
```python
# Stirrup zone label (higher)
stirrup_label_r = Draft.make_text(
    ["d8@100 (135°)"],
    V(SPAN - right_zone/4, y_top + 400, 0))
stirrup_label_r.Label = "EL_StirrupZone_Right"

# Bar position label (lower, slightly left to avoid horizontal overlap)
bar_label_r = Draft.make_text(
    ["Pos 2  2d12"],
    V(SPAN * 0.65, y_top + 200, 0))
bar_label_r.Label = "EL_Pos2_Right"
```

**Result**: all labels stay within the interior of the view bounding box and won't extend past the drawing border.

## SECTION TITLES: Place ABOVE the View, Not Below

Section view titles must be placed ABOVE the cross-section geometry to avoid collision with notes, material spec, and schedule in the lower sheet area:

```python
title = Draft.make_text(
    ["SECTION A-A", "Scale 1:20"],
    V(cx, geometry_top + 100, 0))  # 100mm above top of concrete outline
title.Label = "CS_Title"
```

**NEVER place section titles below the geometry** (below the X axis of the view origin), because the lower sheet area is occupied by notes, material spec, and the schedule table. Placing titles ABOVE the view ensures they don't collide with lower-zone elements.

## BAR SCHEDULE: Every Position Must Appear
The bar bending schedule MUST include EVERY position declared in the drawing geometry.
- If code draws Pos 1 (d20 bars), Pos 2 (d12 bars), Pos 3 (d8 stirrups) — the schedule must have 3 data rows
- A schedule showing only one position when multiple are drawn is INCOMPLETE and INCORRECT
- **CRITICAL: Stirrups/links are ALSO bar positions.** They must appear in the schedule as a row.
- Use `make_bar_schedule(doc, bars, name)` where `bars` = list of ALL bar positions (including stirrups) as dicts with keys: position, dia, shape, length_mm, qty
  - position: string like "1", "2", "3"
  - dia: integer (bar diameter in mm)
  - shape: string like "Hook", "Straight", "Stirrup"
  - length_mm: float (total bar length in mm)
  - qty: integer (quantity of bars)
- Never populate just the "primary" bar; include stirrups/links as Pos N in the schedule
- Count stirrups: approximately span / spacing + 1 (e.g., 6000mm / 150mm ≈ 41 stirrups)
- See _engineering_base.py make_bar_schedule() helper for complete usage

## STIRRUPS: 135° Hook per EN 1992-1-1 §8.5
All stirrups and links MUST have a 135° hook (not 90°) per Eurocode ductility requirement.
- In geometry: show a small angled extension at one corner of the stirrup rectangular frame
- In labels: always annotate with hook angle, e.g., "Pos 3  d8@150 (135°)" or "d8@150 (135° hook)"
- Why: 90° corners slip; 135° provides mechanical anchorage against pullout

**Stirrup shape diagram hook extension dimension (REQUIRED):**
On each stirrup shape diagram, ALWAYS dimension the hook extension length:
  - Hook length = max(10d, 75mm)  (e.g., d8 → max(80mm, 75mm) = 80mm)
  - Use `Draft.make_linear_dimension()` to show the dimension from corner to hook tip
  - Label the dimension with the hook length, e.g., "5d = 40mm" (minimum) or "80mm" (actual)

## BAR LENGTH AND ANCHORAGE: Choose ONE Strategy per Bar

**Strategy A: Hooks within span** (standard for simply supported beams)
- Bar ends at COVER distance from beam face
- Hooks bend UP (bottom bars) or DOWN (top bars) inside the beam
- Cut length = SPAN - 2×COVER + 2×HOOK  (e.g., 6000 - 70 + 400 = 6330mm for d20)
- On elevation: bar stays INSIDE beam body, no extension outside span
- Anchorage provided by the hook itself: "Standard anchorage via end hooks" or "lb,eq ≈ 560mm per EC2 §8.4.4"
- **DO NOT draw** 800mm anchorage extension lines outside the span when using this strategy

**Strategy B: Straight bars into supports** (for large Ld or compact sections)
- Bar extends PAST beam face into the support block by Ld distance
- Ld = 40d (straight) or 28d (with hook) per Eurocode
- Cut length = SPAN + 2×Ld - 2×COVER  (e.g., 6000 + 1600 - 70 = 7530mm for d20 @ 40d)
- On elevation: draw bar body extending 800mm into each support block
- Dimension the extension: "Ld = 800mm = 40d" or similar label
- **DO NOT draw** hooks at bar ends inside the span when using this strategy

**CRITICAL: Do not mix strategies.** If geometry shows hooks inside the beam, do NOT also draw 800mm extension lines outside the span.

For simply supported beams: **Strategy A is standard.** Draw hooks at ends, use hooks for anchorage.

**HOOK DIMENSION REQUIRED ON ELEVATION**: Even with Strategy A, ALWAYS add a linear dimension at the beam ends showing the hook extension length using `Draft.make_linear_dimension`:
```
hook_dim = Draft.make_linear_dimension(
    V(x_end, y_bar, 0), V(x_end, y_bar + HOOK_A, 0),
    V(x_end + 300, y_bar + HOOK_A/2, 0))
hook_dim.Label = "EL_HookDim_Right"
```
This makes the anchorage mechanically legible on the printed drawing — fabricators and inspectors see the hook depth immediately.

See rebar_conventions.md for complete geometry code patterns.

## BAR SHAPE DIAGRAMS: Required for complete drawings

Every position in the bar schedule must have a companion shape diagram:
- Draw small schematic outlines showing the bar's bent profile with critical dimensions
- Include total bar length, hook extensions, position number, and shape code if applicable
- Group all shape diagrams together and display at smaller scale (1:5 or 1:10) beside the bar schedule

**DIMENSION RULES (STRICT):**

**FORBIDDEN**: Any `make_linear_dimension` that measures the diagram's DRAWING WIDTH.
The shape diagram is drawn at a compressed scale (e.g., 6170mm bar drawn as ~2000mm for display).
Never add a dimension showing the display width (e.g., "2000mm") — a fabricator has no use for "2000mm" when the bar is actually 6170mm.

**ONLY ALLOWED dimensions on shape diagrams:**
1. `make_text` label with actual cut length: "L = 6170mm" or "Pos 2  d12  L=6170mm  Hook=120mm"
2. `make_linear_dimension` ONLY for hook extensions: from bar end (inner face) to hook tip
   - Shows the actual hook length (e.g., 120mm), NOT the drawn hook height
3. For stirrups: inner width dimension, inner height dimension, and hook extension dimension
   - All showing ACTUAL internal dimensions, NOT diagram drawing widths

**Examples:**
- ✓ CORRECT: Text "Pos 2  d12  L = 6170mm  Hook = 120mm (10d)" + one dimension line for hook = 120mm
- ✓ CORRECT: Stirrup with dimensions: inner_width=230mm, inner_height=430mm, hook_extension=100mm
- ✗ FORBIDDEN: Dimension showing the drawn bar width (2000mm — the display scale, not real bar length)
- ✗ FORBIDDEN: Dimension showing the drawn hook height (not the actual hook extension)

## BAR SHAPE DIAGRAMS: Include Shape Code Reference

Every bar shape diagram must include the shape code reference for fabricators to cross-reference EN 10221 / BS 8666 bending shape libraries:

**Standard Shape Codes:**
- **Shape Code 11**: Straight bar with equal hooks at both ends (typical for simply-supported main bars)
- **Shape Code 01**: Straight bar, no hooks (for special anchorage arrangements)
- **Shape Code 51**: Rectangular stirrup/link with 135° hook (standard for beam/column ties)
- **Shape Code 60**: Stirrup with varying dimensions (for complex geometries)

**Include shape code in the label text or as a separate annotation:**

Option 1 — Include in main label text:
```python
# Pos 1: straight bar with hooks
bar_label_1 = Draft.make_text(
    ["Pos 1  d20  SC-11  L=6330mm  Hook=200mm"],
    V(diagram_x, diagram_y, 0))

# Pos 3: stirrup with hook
stirrup_label_3 = Draft.make_text(
    ["Pos 3  d8  SC-51  L=1488mm  Hook=80mm"],
    V(diagram_x, diagram_y - 200, 0))
```

Option 2 — Add separate shape code annotation adjacent to diagram:
```python
sc_label = Draft.make_text(["SC-11"], V(shape_diagram_x, shape_diagram_y - 100, 0))
sc_label.Label = f"ShapeCode_Pos1"
```

**Why shape codes matter**: Fabrication shops reference BS 8666 / EN 10221 shape libraries. Including the shape code enables direct lookup and cross-referencing without ambiguity about the bend configuration.

See rebar_conventions.md for complete code patterns

## Important gotchas
- Object `.Name` is read-only after creation — set only via `doc.addObject("Type", "DesiredName")`
- Use `.Label` for human-readable identification (can be changed anytime)
- Draft objects auto-generate Names — collect refs as you create them, don't filter by Name prefix later
- Delete document objects in REVERSE order (`reversed(doc.Objects)`) to avoid crashes from dangling links"""


_ENGINEERING_BASE_TEMPLATE = '''# Engineering base helpers for structural drawings
# Auto-generated by DrawingAssistant — edit freely to customize

import FreeCAD
import Draft
import math

V = FreeCAD.Vector

# ============================================================
# EUROCODE EN 1992-1-1 CONSTANTS
# ============================================================
COVER_XC1 = 25   # mm — dry/permanently wet
COVER_XC2 = 35   # mm — wet, rarely dry
COVER_XC3 = 35   # mm — moderate humidity
COVER_XC4 = 40   # mm — cyclic wet/dry
COVER_XD1 = 45   # mm — chloride, moderate humidity
COVER_XD2 = 50   # mm — chloride, wet
COVER_XS = 50    # mm — marine exposure

def min_bend_diameter(bar_d):
    """Minimum mandrel diameter for bends — EN 1992-1-1 Table 8.1N."""
    if bar_d <= 16:
        return 4 * bar_d   # 4d for d ≤ 16mm
    else:
        return 7 * bar_d   # 7d for d > 16mm

def hook_extension(bar_d):
    """Standard hook straight extension after bend — 10d, minimum 100mm."""
    return max(10 * bar_d, 100)

# ============================================================
# STIRRUP / LINK HELPERS
# ============================================================

def make_stirrup(doc, draft_objects, cx, cy, width, height, bar_d, cover=35):
    """Draw a single stirrup in cross-section view as double-line rectangle.

    Args:
        doc: FreeCAD document
        draft_objects: list to append created objects to
        cx, cy: center of the stirrup frame in Draft model space (mm)
        width: outer concrete dimension (mm)
        height: outer concrete dimension (mm)
        bar_d: stirrup bar diameter (mm)
        cover: concrete cover to stirrup face (mm)
    """
    r = bar_d / 2
    # Inner edge of stirrup = cover from concrete face + half bar diameter
    x0 = cx - width/2 + cover + r
    x1 = cx + width/2 - cover - r
    y0 = cy - height/2 + cover + r
    y1 = cy + height/2 - cover - r

    # Outer wire (closed rectangle)
    outer = Draft.make_wire([
        V(x0 - r, y0 - r, 0),
        V(x1 + r, y0 - r, 0),
        V(x1 + r, y1 + r, 0),
        V(x0 - r, y1 + r, 0),
    ], closed=True)
    outer.Label = "Stirrup_Outer"
    draft_objects.append(outer)

    # Inner wire (closed rectangle, offset by bar diameter)
    inner = Draft.make_wire([
        V(x0 + r, y0 + r, 0),
        V(x1 - r, y0 + r, 0),
        V(x1 - r, y1 - r, 0),
        V(x0 + r, y1 - r, 0),
    ], closed=True)
    inner.Label = "Stirrup_Inner"
    draft_objects.append(inner)

def make_stirrups_elevation(doc, draft_objects, x_start, x_end, y_bot, y_top,
                             bar_d, spacing, cover=35):
    """Draw stirrups in elevation/longitudinal section view.

    Shows stirrup vertical legs as double lines at each stirrup position.
    Typical use: beam elevation showing stirrup distribution along span.
    """
    r = bar_d / 2
    n = int((x_end - x_start) / spacing) + 1
    for i in range(n):
        x = x_start + i * spacing
        # Left leg of stirrup
        left_outer = Draft.make_wire([V(x - r, y_bot, 0), V(x - r, y_top, 0)])
        left_outer.Label = f"Stir_{i}_LeftOuter"
        draft_objects.append(left_outer)
        # Right leg of stirrup
        right_outer = Draft.make_wire([V(x + r, y_bot, 0), V(x + r, y_top, 0)])
        right_outer.Label = f"Stir_{i}_RightOuter"
        draft_objects.append(right_outer)

# ============================================================
# BAR BENDING SCHEDULE
# ============================================================

def make_bar_schedule(doc, bars, name="BarSchedule"):
    """Create a bar bending schedule spreadsheet.

    Args:
        doc: FreeCAD document
        bars: list of dicts, each with keys:
              'pos' (str), 'dia' (int), 'shape' (str), 'length_mm' (float),
              'qty' (int), 'unit_weight_kg_per_m' (optional float)
        name: Name for the Spreadsheet object

    Returns:
        The Spreadsheet object (use DrawViewSpreadsheet to embed in TechDraw)
    """
    sht = doc.addObject("Spreadsheet::Sheet", name)

    # Headers
    headers = ["Pos", "Ø (mm)", "Shape", "Length (mm)", "Qty", "Unit wt (kg/m)", "Total wt (kg)"]
    for col, h in enumerate(headers):
        cell = chr(65 + col) + "1"
        sht.set(cell, h)

    # Data rows
    DENSITY = 7850  # kg/m³ for steel
    total_all_wt = 0.0
    for row, bar in enumerate(bars, start=2):
        dia = bar.get("dia", 0)
        length_mm = bar.get("length_mm", 0)
        qty = bar.get("qty", 1)
        # Unit weight = (π/4) * d² * density / 1e6  (d in mm, result kg/m)
        unit_wt = bar.get("unit_weight_kg_per_m") or (
            math.pi / 4 * (dia**2) * DENSITY / 1e6
        )
        total_wt = unit_wt * (length_mm / 1000) * qty
        total_all_wt += total_wt

        sht.set(f"A{row}", str(bar.get("pos", "")))
        sht.set(f"B{row}", str(dia))
        sht.set(f"C{row}", str(bar.get("shape", "Straight")))
        sht.set(f"D{row}", f"{length_mm:.0f}")
        sht.set(f"E{row}", str(qty))
        sht.set(f"F{row}", f"{unit_wt:.3f}")
        sht.set(f"G{row}", f"{total_wt:.1f}")

    # Total weight row
    total_row = len(bars) + 2
    sht.set(f"A{total_row}", "TOTAL")
    sht.set(f"G{total_row}", f"{total_all_wt:.1f}")

    return sht

# ============================================================
# MATERIAL SPECIFICATION TEXT BLOCK
# ============================================================

def make_material_spec(doc, draft_objects, ox, oy,
                        concrete="C30/37", steel="B500B",
                        cover_nom=35, exposure="XC3",
                        standard="EN 1992-1-1"):
    """Create a material specification text block for the drawing.

    Args:
        doc: FreeCAD document
        draft_objects: list to append to
        ox, oy: bottom-left position in Draft model space (mm)
        concrete: concrete grade string (e.g. "C30/37")
        steel: steel grade string (e.g. "B500B")
        cover_nom: nominal cover in mm
        exposure: exposure class string (e.g. "XC3")
        standard: design standard string (e.g. "EN 1992-1-1")
    """
    lines = [
        "MATERIAL SPECIFICATION",
        f"Concrete: {concrete} per EN 206",
        f"Reinforcement: {steel} per EN 10080",
        f"Nominal cover: {cover_nom}mm (cdev 10mm)",
        f"Exposure class: {exposure}",
        f"Design standard: {standard}",
    ]
    txt = Draft.make_text(lines, V(ox, oy, 0))
    txt.Label = "MaterialSpec"
    draft_objects.append(txt)
    return txt

# ============================================================
# GENERAL NOTES TEXT BLOCK
# ============================================================

def make_general_notes(doc, draft_objects, ox, oy, beam_type="simply_supported"):
    """Create standard general notes text block for construction drawings.

    Args:
        doc: FreeCAD document
        draft_objects: list to append to
        ox, oy: bottom-left position in Draft model space (mm)
        beam_type: "simply_supported" or "continuous" (affects lap length guidance)
    """
    lap_rule = "50d" if beam_type == "simply_supported" else "60d"
    lines = [
        "GENERAL NOTES",
        "1. All dimensions in millimeters unless noted otherwise.",
        f"2. Minimum lap length = {lap_rule} (Exposure class XC2).",
        "3. Reinforcement to be cut and bent per EN 10221.",
        "4. Maximum aggregate size = 20mm.",
        "5. Maintain nominal cover with approved plastic spacers.",
        "6. Concrete vibrated during placing, not re-vibrated.",
        "7. Obtain written approval before departing from drawing.",
    ]
    txt = Draft.make_text(lines, V(ox, oy, 0))
    txt.Label = "GeneralNotes"
    draft_objects.append(txt)
    return txt
'''


class ClaudeCodeBackend:
    """LLM backend using Claude Code CLI in headless mode.

    Benefits over HTTP API:
    - Claude can read FreeCAD source code (.pyi stubs, docstrings)
    - Claude can read project files on-demand (pages/*.py, snapshots/)
    - Project-specific CLAUDE.md for custom instructions
    - Session continuity via --resume
    - Tool access (Glob, Grep, Read) for intelligent context gathering
    """

    def __init__(self, project_dir: str = None):
        """Initialize the Claude Code backend.

        Args:
            project_dir: Project directory for accessing pages/ and snapshots.
                        Note: Claude runs from repo root to access FreeCAD API docs.
        """
        self.project_dir = project_dir
        self._repo_root = self._find_repo_root()
        self._session_id: Optional[str] = None

        # Model identifier (matches LLMBackend interface)
        self.model = "claude-code"
        self.api_url = "claude-code-cli"  # Matches LLMBackend interface

        # Debug info (matches LLMBackend interface)
        self.last_duration_ms = 0
        self.last_cost = 0.0
        self.last_system_prompt = ""
        self.last_context = ""
        self.last_conversation = []
        self.last_tool_calls: List[Dict] = []  # Tool calls made during last request

        # Track which page files were edited (for direct source editing flow)
        self.edited_files: List[str] = []

        # Callback for real-time tool call updates (for progress indicator)
        # Signature: on_tool_call(tool_name: str, tool_input: dict)
        self.on_tool_call = None

        # Active subprocess handle (for cancellation via SIGINT)
        self._process: Optional[subprocess.Popen] = None
        self._cancelled = False  # Set by cancel(), checked after process exits

    def chat(
        self,
        user_message: str,
        context: str = "",
        history: list = None,
        multi_angle_screenshots: list = None,
        read_only: bool = False,
    ) -> str:
        """Send message to Claude Code CLI and get response.

        Args:
            user_message: The user's natural language request
            context: Optional document context string (passed in prompt if no CLAUDE.md)
            history: Optional conversation history (not used - Claude Code manages sessions)
            multi_angle_screenshots: Optional list of file paths to multi-angle screenshots
            read_only: If True, restrict to Read/Glob/Grep tools only (for plan mode)

        Returns:
            Generated response (Python code or text answer)
        """
        # Store for debugging
        self.last_context = context
        self.last_conversation = history[-6:] if history else []

        # Build the prompt
        prompt = self._build_prompt(user_message, context, multi_angle_screenshots)

        # Build command - use stream-json for tool visibility
        # Note: stream-json requires --verbose when used with -p (print mode)
        claude_cmd = _get_claude_command()
        cmd = claude_cmd + ["-p", "--verbose", "--output-format", "stream-json"]

        # Tool access: --tools restricts which tools exist in context,
        # --allowedTools auto-approves tools without prompting.
        # Phase 1 (read_only): --tools removes Edit/Write/ExitPlanMode entirely
        # Phase 2 / normal: --allowedTools auto-approves all needed tools
        if read_only:
            cmd.extend(["--tools", "Read,Glob,Grep"])
        else:
            cmd.extend(["--allowedTools", "Read,Glob,Grep,Edit,Write"])

        # Build system prompt
        pages_dir = self._get_pages_dir()

        system_prompt = FREECAD_SYSTEM_PROMPT_TEMPLATE.format(
            pages_dir=pages_dir or "(no project)",
        )

        # Auto-create _engineering_base.py if not present
        if self.project_dir:
            pages_dir_path = Path(self.project_dir) / "pages"
            eng_base = pages_dir_path / "_engineering_base.py"
            if pages_dir_path.exists() and not eng_base.exists():
                try:
                    eng_base.write_text(_ENGINEERING_BASE_TEMPLATE, encoding="utf-8")
                    FreeCAD.Console.PrintMessage(
                        "DrawingAssistant: Auto-created _engineering_base.py with engineering helpers\n"
                    )
                except Exception as e:
                    FreeCAD.Console.PrintWarning(
                        f"DrawingAssistant: Failed to create _engineering_base.py: {e}\n"
                    )

        # Append engineer's project notes (from project.md)
        if self.project_dir:
            project_md = Path(self.project_dir) / "project.md"
            if project_md.exists():
                try:
                    notes = project_md.read_text(encoding="utf-8").strip()
                    if notes:
                        system_prompt += (
                            f"\n\n## Project Notes (from engineer)\n{notes}"
                        )
                except Exception as e:
                    FreeCAD.Console.PrintWarning(
                        f"DrawingAssistant: Failed to read project.md: {e}\n"
                    )

            # Append reference documents listing
            ref_dir = Path(self.project_dir) / "reference_docs"
            if ref_dir.exists():
                docs = sorted(
                    f for f in ref_dir.iterdir()
                    if f.is_file() and not f.name.startswith(".")
                )
                if docs:
                    listing = "\n".join(
                        f"- {f.name} ({f.stat().st_size / 1024:.0f} KB)"
                        for f in docs
                    )
                    system_prompt += (
                        f"\n\n## Available Reference Documents\n{listing}\n"
                        "Use the Read tool to consult these when relevant "
                        "(in reference_docs/ directory). "
                        "For PDFs, use the pages parameter."
                    )

        # Append module-level reference standards (e.g. rebar conventions)
        refs_dir = Path(__file__).resolve().parent.parent / "references"
        if refs_dir.is_dir():
            # Embed drawing completeness reference inline (high priority, always available)
            completeness_ref = refs_dir / "drawing_completeness.md"
            if completeness_ref.exists():
                try:
                    completeness_content = completeness_ref.read_text(encoding="utf-8")
                    system_prompt += (
                        f"\n\n## Drawing Completeness (MANDATORY)\n{completeness_content}"
                    )
                except Exception:
                    pass

            # List other reference files (rebar_conventions.md, drawing_sizes.md)
            ref_files = sorted(
                f for f in refs_dir.iterdir()
                if f.is_file() and f.suffix == ".md" and f.name != "drawing_completeness.md"
            )
            if ref_files:
                listing = "\n".join(f"- `{f}` — {f.stem.replace('_', ' ').title()}" for f in ref_files)
                system_prompt += (
                    f"\n\n## Additional Drafting Standards\n{listing}\n"
                    "When drawing reinforcement (rebar) in section or plan views, "
                    "refer to the rebar conventions reference file for working code examples "
                    "that show the correct patterns for double-line bars, dots, hooks, and hatching."
                )

        cmd.extend(["--append-system-prompt", system_prompt])
        self.last_system_prompt = system_prompt

        # Resume session if we have one (for multi-turn conversations)
        if self._session_id:
            cmd.extend(["--resume", self._session_id])

        # NOTE: Prompt is passed via stdin, not as command line argument
        # This avoids shell escaping issues with special characters

        # Set working directory to PROJECT directory (so Claude can edit pages/)
        # Claude can still read API docs via absolute paths in the prompt
        cwd = self.project_dir or self._repo_root or os.getcwd()

        FreeCAD.Console.PrintMessage(f"DrawingAssistant: Calling Claude Code in {cwd}\n")

        # Reset state for this request
        self.last_tool_calls = []
        self.edited_files = []
        self._cancelled = False

        start_time = time.time()
        try:
            # Use Popen for streaming NDJSON output
            # Hide console window on Windows
            kwargs = {}
            if sys.platform == "win32":
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                si.wShowWindow = 0  # SW_HIDE
                kwargs["startupinfo"] = si

            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",  # Explicit UTF-8 for Windows compatibility
                cwd=cwd,
                **kwargs
            )
            self._process = process

            # Write prompt to stdin and close
            process.stdin.write(prompt)
            process.stdin.close()

            # Parse NDJSON stream line by line
            result_text = ""
            assistant_text_parts = []  # Fallback: accumulate text from assistant events
            tool_calls = []

            for line in process.stdout:
                line = line.strip()
                if not line:
                    continue

                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                event_type = event.get("type")

                # Extract text and tool_use from assistant messages
                if event_type == "assistant":
                    message = event.get("message", {})
                    for block in message.get("content", []):
                        if block.get("type") == "text":
                            assistant_text_parts.append(block.get("text", ""))
                        elif block.get("type") == "tool_use":
                            tool_name = block.get("name", "")
                            tool_input = block.get("input", {})
                            tool_call = {
                                "tool": tool_name,
                                "input": tool_input
                            }
                            tool_calls.append(tool_call)
                            # Log with details
                            detail = self._format_tool_log(tool_name, tool_input)
                            FreeCAD.Console.PrintMessage(
                                f"DrawingAssistant: Tool call - {detail}\n"
                            )
                            # Fire callback for progress indicator
                            if self.on_tool_call:
                                self.on_tool_call(tool_name, tool_input)

                # Handle final result
                elif event_type == "result":
                    result_text = event.get("result", "")
                    self._session_id = event.get("session_id")

                    # Debug: log result content
                    FreeCAD.Console.PrintMessage(
                        f"DrawingAssistant: Result event - length: {len(result_text)}, "
                        f"preview: {result_text[:100] if result_text else '(empty)'}...\n"
                    )

                    # Track cost
                    self.last_cost = event.get("total_cost_usd", 0)

                    # Check for error
                    if event.get("is_error", False):
                        error_msg = result_text or "Unknown error"
                        FreeCAD.Console.PrintError(
                            f"DrawingAssistant: Claude Code returned error: {error_msg}\n"
                        )
                        self.last_duration_ms = (time.time() - start_time) * 1000
                        return f"# Error: {error_msg}"

            # Wait for process to complete
            # Use shorter timeout if cancelled (SIGINT should exit quickly)
            wait_timeout = 10 if self._cancelled else 180
            try:
                process.wait(timeout=wait_timeout)
            except subprocess.TimeoutExpired:
                # Process didn't exit in time — force kill
                FreeCAD.Console.PrintWarning(
                    "DrawingAssistant: Process didn't exit after "
                    f"{wait_timeout}s, killing\n"
                )
                process.kill()
                process.wait(timeout=5)

            self.last_duration_ms = (time.time() - start_time) * 1000

            # Store tool calls for UI access
            self.last_tool_calls = tool_calls

            # Check if we cancelled this request
            if self._cancelled:
                FreeCAD.Console.PrintMessage(
                    "DrawingAssistant: Claude Code request was cancelled\n"
                )
                return None  # Sentinel: cancelled, not an error

            # Track which page files were edited (for direct source editing flow)
            self.edited_files = []
            for tc in tool_calls:
                tool_name = tc.get("tool")
                if tool_name in ("Edit", "Write"):
                    file_path = tc.get("input", {}).get("file_path", "")
                    if "/pages/" in file_path and file_path.endswith(".py"):
                        filename = Path(file_path).name
                        if filename not in self.edited_files:
                            self.edited_files.append(filename)
                            FreeCAD.Console.PrintMessage(
                                f"DrawingAssistant: Detected page {tool_name.lower()}: {filename}\n"
                            )

            # Check for process errors
            if process.returncode != 0:
                stderr = process.stderr.read()
                FreeCAD.Console.PrintError(f"DrawingAssistant: Claude Code error: {stderr}\n")
                return f"# Error: {stderr}"

            # Fallback: if result is empty, use accumulated assistant text
            if not result_text and assistant_text_parts:
                result_text = "\n".join(assistant_text_parts)
                FreeCAD.Console.PrintMessage(
                    "DrawingAssistant: Result was empty, using assistant text fallback\n"
                )

            FreeCAD.Console.PrintMessage(
                f"DrawingAssistant: Claude Code response received "
                f"({self.last_duration_ms:.0f}ms, ${self.last_cost:.4f}, "
                f"{len(tool_calls)} tool calls)\n"
            )

            return self._clean_response(result_text)

        except json.JSONDecodeError as e:
            FreeCAD.Console.PrintError(f"DrawingAssistant: Failed to parse Claude Code response: {e}\n")
            return f"# Error: Failed to parse response: {e}"

        except FileNotFoundError:
            FreeCAD.Console.PrintError("DrawingAssistant: Claude Code CLI not found. Is it installed?\n")
            return "# Error: Claude Code CLI not found. Install with: npm install -g @anthropic-ai/claude-code"

        except Exception as e:
            FreeCAD.Console.PrintError(f"DrawingAssistant: Claude Code error: {e}\n")
            return f"# Error: {e}"

        finally:
            self._process = None

    def cancel(self):
        """Send SIGINT to the running Claude Code process for graceful interruption.

        Claude Code saves session state on SIGINT, so --resume will continue
        the conversation including the interrupted turn.
        """
        self._cancelled = True
        if self._process and self._process.poll() is None:
            FreeCAD.Console.PrintMessage("DrawingAssistant: Sending SIGINT to Claude Code process\n")
            if sys.platform == "win32":
                self._process.terminate()
            else:
                self._process.send_signal(signal.SIGINT)

    def _build_prompt(self, message: str, context: str,
                       multi_angle_screenshots: list = None) -> str:
        """Build the prompt for Claude Code.

        User message comes FIRST for prominence.
        Pages directory path is in the system prompt — not repeated here to avoid
        tempting Claude to read files for pure questions.
        """
        parts = []

        # User message FIRST — don't bury it under context
        parts.append(message)
        parts.append("")

        # Always include document context
        if context:
            parts.append(f"## Document State\n{context}")
            parts.append("")

        # Screenshots (user-attached + auto-generated)
        if multi_angle_screenshots:
            user_images = [p for p in multi_angle_screenshots if "/user_uploads/" in p]
            auto_images = [p for p in multi_angle_screenshots if "/user_uploads/" not in p]

            if user_images:
                parts.append("### User-attached images:")
                for path in user_images:
                    parts.append(f"- {path}")
                parts.append("")

            if auto_images:
                parts.append("### Current drawing state (use Read tool to view):")
                for path in auto_images:
                    p = Path(path)
                    sheet_stem = p.parent.name
                    if p.stem == "_sheet":
                        # TechDraw page — shows final printed layout with text rendering
                        parts.append(f"- {sheet_stem} / SHEET LAYOUT (final print view): {path}")
                    else:
                        # Draft geometry group — shows raw geometry at full scale
                        group_label = p.stem.replace("_", " ")
                        parts.append(f"- {sheet_stem} / {group_label} (Draft geometry): {path}")
                parts.append("")

        return "\n".join(parts)

    def _clean_response(self, response: str) -> str:
        """Clean up the response - remove markdown code blocks if present."""
        response = response.strip()

        # Remove markdown code fences
        if response.startswith("```python"):
            response = response[9:]
        elif response.startswith("```"):
            response = response[3:]

        if response.endswith("```"):
            response = response[:-3]

        return response.strip()

    def _format_tool_log(self, tool: str, input_data: dict) -> str:
        """Format tool call for console logging with details."""
        if tool == "Glob":
            pattern = input_data.get("pattern", "")
            return f"Glob: {pattern}"
        elif tool == "Read":
            path = input_data.get("file_path", "")
            if len(path) > 60:
                path = "..." + path[-57:]
            return f"Read: {path}"
        elif tool == "Grep":
            pattern = input_data.get("pattern", "")
            path = input_data.get("path", ".")
            if len(path) > 30:
                path = "..." + path[-27:]
            return f"Grep: '{pattern}' in {path}"
        elif tool == "Edit":
            path = input_data.get("file_path", "")
            if len(path) > 50:
                path = "..." + path[-47:]
            return f"Edit: {path}"
        elif tool == "Write":
            path = input_data.get("file_path", "")
            if len(path) > 50:
                path = "..." + path[-47:]
            return f"Write: {path}"
        elif tool == "Bash":
            cmd = input_data.get("command", "")
            if len(cmd) > 50:
                cmd = cmd[:47] + "..."
            return f"Bash: {cmd}"
        elif tool == "Task":
            desc = input_data.get("description", "")
            return f"Task: {desc}"
        else:
            return f"{tool}"

    def _get_pages_dir(self) -> Optional[str]:
        """Get absolute path to pages/ directory for the project."""
        if self.project_dir:
            pages_dir = Path(self.project_dir) / "pages"
            return str(pages_dir.resolve())
        return None

    @property
    def source_was_edited(self) -> bool:
        """Backward compat: True if any page file was edited."""
        return len(self.edited_files) > 0

    def _find_repo_root(self) -> Optional[str]:
        """Find FreeCAD repo root directory.

        Walks up from this file's location to find the directory containing src/Mod/.
        This allows Claude to read FreeCAD API source files (.pyi stubs, docstrings).

        Returns:
            Repo root path, or None if not found
        """
        current = Path(__file__).resolve().parent
        # Walk up to find repo root (contains src/Mod/)
        while current.parent != current:
            if (current / "src" / "Mod").exists():
                return str(current)
            current = current.parent
        return None

    def clear_session(self):
        """Clear the current session (start fresh conversation)."""
        self._session_id = None
        FreeCAD.Console.PrintMessage("DrawingAssistant: Claude Code session cleared\n")

    def get_session_id(self) -> Optional[str]:
        """Get the current session ID for persistence."""
        return self._session_id

    def set_session_id(self, session_id: str):
        """Restore a session ID (for resuming conversations)."""
        self._session_id = session_id
