# Buildable for Precast — Product Plan

*Last updated: 2026-02-06*

## The Problem

Precast concrete companies spend **~60% of total project time** on the design/drawing phase. The structural calculations are done relatively fast, but producing detailed construction drawings is a "robotic" manual process that takes **2 people ~2 months** per project.

The drawings follow **standardized templates** — plan views, cross-sections, rebar details, bar bending schedules — filled in with different parameters for each element. The work is rules-based (follow Eurocode, apply standard detailing), not creative.

Every change cascades: if one rebar diameter changes, the drafter must manually update plan annotations, section views, bar shape drawings, BBS tables, and weight summaries. This is where the real time goes.

## The Insight

Looking at a real precast structural project (ALTA Small Warehouse, 84x48m, Tbilisi 2025):

- **Foundation F-1** (16 pieces): 3 pages of drawings, all from the same template
- **Foundation F-2** (8 pieces): 3 pages, same template, different dimensions
- **Facade columns** (14 + 10 pieces): same template, different rebar specs
- **Every page** follows the same structure: plan + sections + bar shapes + BBS table

The entire document set is the same drawing template filled in with different parameters. An AI that knows the rules can generate these in seconds instead of days.

## The Product

### Positioning

> **Buildable** — AI-powered structural detailing for precast concrete.
> Describe your element, get complete construction drawings in minutes.

Not "Cursor for CAD" (too generic). Not "text-to-CAD" (too vague). **Structural detailing automation for precast** — specific, defensible, and directly mapped to a painful workflow.

### How It Works

```
Structural calculation results (from ETABS, SAP2000, RFEM, etc.)
                    ↓
Engineer describes element in Buildable:
"Foundation F-1, 3200x4200, depth 2350, pedestal 750x750,
 C30/37, bottom Ø12@200 A500c, stirrups Ø12/10@90/200"
                    ↓
AI edits source.py → FreeCAD generates:
├── 3D model with rebar (inspectable, rotatable)
├── TechDraw sheet: plan view + Section 1-1 + Section 2-2
├── Bar shape page: each position with dimensions
├── BBS table: marks, diameters, lengths, quantities, weights
└── Material summary: concrete volume, steel kg/m³
                    ↓
Engineer reviews, adjusts → Export DWG/PDF
```

### The Killer Feature: Change Propagation

**In AutoCAD** (current workflow): Engineer says "change F-1 bottom rebar from Ø12 to Ø16"
- Manually update plan view annotation
- Manually update Section 1-1 rebar marks
- Manually update Section 2-2 rebar marks
- Redraw bar shape for that position
- Recalculate and update BBS table row
- Update total steel weight
- Check if cover/spacing still meets code
- Repeat for every element affected
- **Time: hours to days**

**In Buildable**: "Change F-1 bottom rebar to Ø16"
- AI modifies one parameter in source.py
- Everything regenerates: drawings, sections, bar shapes, BBS, weights
- AI self-reviews against Eurocode minimums
- **Time: seconds**

This is the 2 months → 2 days compression.

---

## What To Build

### Phase 1: Foundation MVP (Weeks 1-6)

**Goal**: Generate Foundation F-1 from that ALTA PDF automatically.

**Deliverables**:
1. `PrecastFoundation` Python class that creates:
   - Parametric 3D geometry (footing + pedestal) using FreeCAD Part/Arch
   - Rebar placement using FreeCAD Rebar addon
   - TechDraw sheet with plan view and 2 cross-sections
   - Dimensioning (auto-placed)
   - Bar shape detail drawings
   - BBS table (matching the Georgian standard format)

2. AI system prompt additions:
   - Precast structural element knowledge
   - Eurocode 2 rebar rules (cover, spacing, bend radii)
   - Standard bar diameters and grades (A500c, A240c, B500B, S235)
   - Concrete classes and properties
   - Georgian title block format

3. TechDraw template:
   - Standard sheet layout matching existing Georgian practice
   - Title block with: მისამართი, შემსრულებელი, შემოწმებული, etc.
   - BBS table format

**Demo**: Recreate Foundation F-1 from the ALTA project. Show to precast company founder. Ask: "This took 10 minutes. How long would this take your team?"

### Phase 2: Full Element Library (Weeks 7-14)

Extend to all common precast element types:

| Element | Variants | Priority |
|---------|----------|----------|
| Pad foundations | Rectangular, square, stepped | Done in Phase 1 |
| Columns | Square, rectangular, with corbels | High |
| Beams | Rectangular, T, inverted-T, L | High |
| Wall panels | Solid, with openings | High |
| Slabs | Solid, hollow-core, TT (double-tee) | Medium |
| Stairs | Precast stair flights | Medium |
| Connections | Column-beam, column-foundation, panel joints | Medium |

For each element type:
- Parametric 3D model
- Standard rebar arrangements
- TechDraw views (plan, sections, details)
- Bar shapes + BBS
- Material takeoff

### Phase 3: Project-Level Features (Weeks 15-20)

- **Layout plans**: Grid-based column/beam layout generation (like page 4 of the PDF)
- **Element schedules**: Summary tables listing all element types, quantities, concrete volumes, steel weights
- **Multi-element projects**: "Create the full warehouse: 16x F-1 foundations, 8x F-2 foundations, 24x columns type 1..."
- **DWG/DXF export**: So output can be opened in AutoCAD by anyone
- **PDF batch export**: Full drawing set ready for government submission
- **IFC export**: For BIM coordination

### Phase 4: Intelligence Layer (Weeks 21+)

- **Code compliance checking**: AI validates rebar against Eurocode 2 / Georgian building code
- **Optimization suggestions**: "You could save 12% steel by using Ø14@150 instead of Ø16@200"
- **Import from structural software**: Parse ETABS/SAP2000/RFEM output → auto-generate elements
- **Revision management**: Track changes between versions, generate revision clouds
- **Quantity takeoff**: Full project BOM with material costs

---

## Technical Architecture

### Precast Element Classes

```
src/Mod/AIAssistant/precast/
├── __init__.py
├── base.py              # PrecastElement base class
├── foundation.py        # PrecastFoundation (pad, strip, pile cap)
├── column.py            # PrecastColumn (with splice zones, corbels)
├── beam.py              # PrecastBeam (rectangular, T, L, inverted-T)
├── slab.py              # PrecastSlab (solid, hollow-core, TT)
├── wall.py              # PrecastWall (solid, with openings)
├── rebar.py             # RebarLayout, RebarMesh, Stirrups helpers
├── bbs.py               # BarBendingSchedule generator
├── standards.py         # Eurocode 2 rules, material properties
└── templates/
    ├── sheet_a3.svg      # TechDraw A3 template with Georgian title block
    ├── bbs_table.svg     # BBS table template
    └── bar_shapes.svg    # Standard bar shape library
```

### How source.py Looks for a Precast Project

```python
# Buildable AI Source - ALTA Small Warehouse
# Created: 2026-02-10

import FreeCAD
from buildable.precast import PrecastFoundation, PrecastColumn, RebarMesh, Stirrups

doc = FreeCAD.ActiveDocument or FreeCAD.newDocument("ALTA_Warehouse")

# === Foundation F-1 (16 pieces) ===
f1 = PrecastFoundation(
    name="F-1",
    footing=(3200, 4200, 500),       # width, length, depth
    pedestal=(750, 750, 1250),        # width, length, height
    concrete="C30/37",
    cover=40,
    bottom_mesh=RebarMesh("Ø12", 200, "A500c"),
    top_mesh=RebarMesh("Ø10", 200, "A500c"),
    stirrups=Stirrups("Ø12/10", [90, 200], "A500c"),
    quantity=16,
    level=-3.25
)
f1.build(doc)  # Creates 3D model + TechDraw sheets + BBS

# === Foundation F-2 (8 pieces) ===
f2 = PrecastFoundation(
    name="F-2",
    footing=(3200, 4700, 500),
    pedestal=(850, 850, 1350),
    concrete="C30/37",
    cover=40,
    bottom_mesh=RebarMesh("Ø12", 200, "A500c"),
    top_mesh=RebarMesh("Ø10", 200, "A500c"),
    stirrups=Stirrups("Ø12/10", [90, 200], "A500c"),
    quantity=8,
    level=-3.25
)
f2.build(doc)

# === Facade Columns Type 1 (14 pieces) ===
# ... AI adds more as engineer describes them
```

### System Prompt Additions

The AI assistant system prompt gets precast-specific knowledge:

```
## Precast Structural Detailing

When working on precast projects:

1. ALWAYS read source.py first to understand existing elements
2. Use the precast library classes (PrecastFoundation, PrecastColumn, etc.)
3. Follow Eurocode 2 for rebar detailing:
   - Minimum cover: 30mm (interior), 40mm (exterior), 50mm (ground contact)
   - Minimum bar spacing: max(bar_diameter, 20mm, aggregate_size + 5mm)
   - Standard bend radii per bar diameter
   - Lap lengths per concrete class and bar grade
4. Standard materials in Georgia:
   - Reinforcement: A500c (main), A240c (stirrups), B500B (welded mesh)
   - Structural steel: S235, S355
   - Concrete: C20/25, C25/30, C30/37, C40/50
5. Generate complete output for each element:
   - 3D model with rebar
   - TechDraw: plan + 2 sections + bar shapes + BBS
   - Material summary
6. When modifying elements, regenerate all affected drawings
7. Validate rebar against code requirements before accepting
```

---

## Go-to-Market

### Phase 1: Georgian Precast Association (Months 1-3)

- **Target**: 3-5 member companies of the association (Nikoloz's direct connections)
- **Offer**: Free pilot — "Let us generate drawings for one element on your next project"
- **Goal**: Prove the time savings, get testimonials, identify gaps
- **Success metric**: One company uses Buildable output on a real project

### Phase 2: Paid Pilots in Georgia (Months 4-6)

- **Target**: 10 precast companies in Georgia
- **Pricing**: $200-500/month (affordable for Georgian market, validates willingness to pay)
- **Offer**: Full precast detailing — foundations, columns, beams, walls
- **Goal**: $2K-5K MRR, 5+ paying customers, case studies with before/after timelines

### Phase 3: Regional Expansion (Months 7-12)

- **Target**: Turkey, Azerbaijan, Kazakhstan, UAE — nearby markets with construction booms, similar standards (Eurocode-based)
- **Pricing**: $500-1000/month
- **Localization**: Title block templates per country, local code variants
- **Goal**: $20K+ MRR

### Phase 4: Global Precast Market (Year 2)

- **Target**: Precast companies worldwide (Europe, Middle East, Southeast Asia)
- **Pricing**: $1000-2000/month (still 5-10x cheaper than hiring a drafter)
- **Expand**: Add ACI 318 (US standard), BS 8110 (UK), IS 456 (India)
- **Goal**: $100K+ MRR → fundraise

### Long-term: Platform Expansion

Precast is the wedge. Once established:
- Expand to cast-in-place concrete detailing
- Steel structure detailing
- General structural engineering
- Eventually: the full "Cursor for CAD" vision, earned through vertical dominance

---

## Pricing Logic

**Current cost of drawing production:**
- 2 engineers × 2 months × ~$1,500/month (Georgian salary) = **$6,000 per project**
- A company doing 5 projects/year spends **$30,000/year** on drawing production

**Buildable target:**
- Save 70% of drawing time → save ~$21,000/year
- Charge $300-500/month ($3,600-6,000/year)
- **ROI: 3.5-5.8x** — easy sell

**For international markets:**
- Engineering salaries are 3-5x higher ($4,000-8,000/month)
- Same time savings → $100K+ annual savings
- Charge $1,000-2,000/month → still obvious ROI

---

## Competitive Moat

| Moat | Description |
|------|-------------|
| **Domain knowledge** | Precast detailing rules, Eurocode compliance, BBS generation — generic AI CAD tools don't have this |
| **Georgian Precast Association** | Built-in distribution to first customers, impossible for competitors to replicate |
| **Precast element library** | Each validated element class is accumulated IP |
| **Template library** | Country-specific title blocks, BBS formats, code variants |
| **Customer lock-in** | Once a company's standard elements are in Buildable, switching cost is high |
| **Open source base** | No CAD license cost → accessible to SMBs that can't afford Tekla/Revit |

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Engineers don't trust AI-generated drawings | Preview + review workflow. Engineer always approves. Start with simple elements. |
| FreeCAD TechDraw output quality not professional enough | Invest in template polish. Export to DWG for final touches if needed. |
| Market too small (Georgian precast) | Georgia is the beachhead, not the market. Precast is $155B globally. |
| Autodesk/Tekla adds AI detailing | They're focused on general CAD, not precast-specific workflows. Vertical focus wins. |
| Rebar detailing errors could cause structural failures | Always require engineer review. Add code compliance checks. Never position as replacing the engineer. |
| Claude Code dependency | Build model-agnostic backend (already have HTTP backend). Precast element library works regardless of LLM. |

---

## Key Metrics to Track

- **Time to generate**: How many minutes to produce a complete element drawing set
- **Accuracy rate**: % of generated drawings that need zero manual corrections
- **Adoption**: Number of element sets generated per customer per month
- **Retention**: Do customers come back for the next project?
- **Revenue**: MRR growth

---

## First Milestone

**Recreate Foundation F-1 from the ALTA project PDF in Buildable.**

- Input: Element parameters (dimensions, rebar, concrete class)
- Output: 3D model + TechDraw sheet matching the PDF format
- Timeline: 4-6 weeks
- Demo to: The precast company founder we just spoke with
- Question to ask: "Would you use this on your next project?"
