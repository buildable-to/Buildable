# Demo Video Plan

*Last updated: 2026-02-10*

## Video Strategy

Three videos, in order of priority. Each builds on the previous — same footage can be reused.

---

## Video 1: "The Change Request" (30 sec)

**Purpose**: Social media, shareable, maximum impact
**Audience**: Structural engineers, precast company owners, tech/startup community
**Where to post**: LinkedIn, X/Twitter, YouTube Shorts, Reddit r/engineering

### Storyboard

```
[0-3s]   WIDE SHOT: Screen showing a complete set of precast drawings
          (15+ pages of real-looking TechDraw output in Buildable)
          Text overlay: "You just finished the structural drawings."

[3-8s]   NOTIFICATION POPUP (animated, phone-style):
          "Structural engineer: Change all foundation rebar
           from Ø12 to Ø16. Increase footing depth by 200mm.
           Client needs updated drawings by tomorrow."

[8-12s]  Text overlay: "In AutoCAD, this takes 3 days."
          QUICK CUTS (0.5s each):
          - Hand moving mouse tediously in AutoCAD
          - Editing a dimension annotation
          - Scrolling through a long drawing
          - Recalculating numbers in a table manually
          - Frustrated face / head in hands (optional, keep it subtle)

[12-22s] Text overlay: "In Buildable:"
          SCREEN RECORDING of Buildable:
          - Chat panel visible on left
          - Engineer types: "Update all foundations: bottom rebar Ø16,
            increase footing depth to 2550."
          - AI responds: "Updating 2 foundation types..."
          - 3D model updates in viewport (footing gets deeper, rebar changes)
          - Cut to TechDraw sheet — dimensions updating
          - Cut to BBS table — quantities recalculating
          - Cut to PDF export completing

[22-27s] Text overlay: "Every drawing. Every table. 30 seconds."
          Show final output: clean PDF drawing set

[27-30s] END CARD:
          "Buildable"
          "AI-powered structural detailing"
          buildable.to
```

### What to build before recording

- [ ] One foundation type (F-1) with 3D model + rebar in Buildable
- [ ] TechDraw sheet with plan view, 2 sections, BBS table
- [ ] AI edit working: change rebar diameter → everything regenerates
- [ ] Clean dark theme UI (already have Cursor-inspired theme)

### Production notes

- Screen record at 4K, export at 1080p
- Use smooth scrolling and cursor movements (no jerky mouse)
- Music: minimal electronic, low-energy (like Linear or Stripe promos)
- Text overlays: clean sans-serif font, white on dark, no animations
- No voiceover for this version — pure visual impact
- Keep the Georgian title block text — authenticity matters

---

## Video 2: "The Foundation" (60 sec)

**Purpose**: Website hero video, landing page
**Audience**: Anyone visiting buildable.to

### Storyboard

```
[0-5s]   OPENING:
          Slow flip through pages of a real structural drawing set
          (use the ALTA warehouse PDF or similar)
          Text overlay: "Designing these drawings takes 2 months.
                         Building the actual structure? 15 days."

[5-10s]  Text overlay: "What if the drawings took 10 minutes?"
          TRANSITION: Fade to Buildable interface, empty project

[10-15s] CHAT PANEL — engineer types:
          "Create foundation F-1. Rectangular footing 3200x4200,
           pedestal 750x750, depth 2350mm. Concrete C30/37.
           Bottom mesh Ø12@200 A500c. Stirrups Ø12/10@90/200."

[15-20s] AI THINKING:
          Show the AI response streaming in the chat
          (like Claude/ChatGPT typing animation)
          "Creating foundation F-1... Generating geometry..."

[20-35s] THE MONEY SHOT — 3D viewport:
          - Concrete footing geometry appears (solid, grey)
          - Camera slowly rotates around it
          - Concrete becomes semi-transparent / x-ray view
          - Bottom rebar mesh fades in (steel-colored bars)
          - Top rebar mesh appears
          - Stirrups populate inside the pedestal
          - Camera pulls back to show complete element
          TAKE YOUR TIME HERE — this is the visual wow moment
          Engineers will pause and stare at this

[35-45s] TECHDRAW GENERATION:
          Cut to TechDraw workbench
          - Plan view renders with dimension lines appearing
          - Section 1-1 draws with rebar marks (Ø12 A500c, etc.)
          - Section 2-2 appears alongside
          - Bar shape details populate (pos. 1, 2, 3...)
          - BBS table fills in: diameter, length, quantity, weight
          - Total steel weight calculates at bottom
          Speed this up slightly — the visual of a professional
          drawing assembling itself is satisfying

[45-52s] THE CHANGE:
          Chat: "Change bottom rebar to Ø16. Add 2 extra bars in X direction."
          - All sheets update simultaneously
          - Quick cuts between updating views
          Text overlay: "One change. Every drawing updates."

[52-57s] EXPORT:
          Show PDF/DWG export
          Quick flip through the generated drawing set
          It looks professional. It looks real.

[57-60s] END CARD:
          "Buildable"
          "From parameters to drawings in minutes"
          buildable.to
          [Try it free] button mockup
```

### What to build (on top of Video 1 requirements)

- [ ] Smooth 3D viewport camera animation / orbit
- [ ] Semi-transparent concrete view showing rebar inside
- [ ] Bar shape detail drawings on TechDraw
- [ ] PDF export flow
- [ ] Polish the AI chat response animation

### Production notes

- This video lives on the website — it auto-plays muted in the hero section
- Must look polished, not scrappy
- Consider adding subtle sound design (keyboard clicks, soft "generation" sounds)
- Optional: very brief voiceover version for YouTube

---

## Video 3: "The Full Project" (2-3 min)

**Purpose**: Detailed walkthrough for interested leads, YouTube
**Audience**: Engineers evaluating the tool, VCs doing due diligence

### Storyboard

```
[0-15s]  INTRO:
          Show the ALTA warehouse 3D render (from PDF cover page)
          Text: "This is a real precast warehouse project.
                 84m x 48m. Steel frame with precast elements.
                 The structural drawings took 2 months.
                 Actual construction? 15 days."
          Text: "Let's rebuild the drawings in Buildable."

[15-45s] PROJECT SETUP:
          - Create new project in Buildable
          - Chat: "Create a precast warehouse project. 8-bay portal frame,
            84m long, 48m wide. Column grid at 6m spacing."
          - Show grid layout generating (plan view matching ALTA page 4)
          - Column positions appear on grid

[45-90s] FOUNDATIONS:
          - "Add foundation type F-1 at all perimeter columns.
            3200x4200 footing, 750x750 pedestal..."
          - 3D foundations appear at grid points
          - Show one foundation in detail (3D rebar view)
          - Show generated TechDraw sheet
          - "Foundation F-2 at interior columns. Same but 4700 wide..."
          - Second type appears

[90-120s] COLUMNS:
          - "Facade columns: 600x600, height 8.5m, concrete C40/50..."
          - Columns rise from foundations in 3D view
          - Show column cross-section with rebar detail
          - Show column TechDraw sheet with splice zones, stirrup spacing

[120-150s] BEAMS AND ROOF:
           - "Roof beams spanning between column rows..."
           - Beams appear connecting columns
           - "TT roof slabs at 6m span..."
           - Roof assembles — building takes shape
           - Camera pulls back: full 3D model of the warehouse

[150-180s] THE COMPARISON:
           Split screen:
           LEFT: Generated drawing set from Buildable (flip through pages)
           RIGHT: Original ALTA PDF (flip through pages)
           They match. Same layout. Same level of detail.
           Same BBS tables. Same section details.
           Text: "15 minutes vs 2 months.
                  Now construction is the bottleneck, not paper."

[180-210s] THE CHANGE DEMO:
           - "The client just increased the building by 2 bays.
             Update the grid to 10 bays, add foundations and columns."
           - Watch the entire project update
           - New foundations appear, new columns, new beams
           - ALL drawings regenerate
           - Text: "A change that would take a week. Done in 60 seconds."

[210-240s] OUTRO:
           Show the final deliverable:
           - 3D BIM model (rotatable)
           - Complete drawing set (PDF)
           - DWG files (for AutoCAD compatibility)
           - Material takeoff (concrete volumes, steel weights)
           Text: "Buildable — AI-powered structural detailing"
           "Try it free at buildable.to"
```

### What to build (on top of Video 1+2 requirements)

- [ ] Column element type with rebar
- [ ] Beam element type
- [ ] Slab/roof element type (at least visually)
- [ ] Grid/layout plan generation
- [ ] Multi-element project in single source.py
- [ ] Material takeoff summary

### Production notes

- This video can have voiceover (Luka or Otar narrating)
- Or: text overlays only, with music — cleaner, no accent concerns
- Include a "subscribe" or "join waitlist" CTA at the end
- Post on YouTube with SEO title: "AI Generates Precast Structural Drawings in Minutes"

---

## Visual Style Guide

### Screen layout during recording

```
┌─────────────────────────────────────────────────────┐
│  Buildable (dark theme)                         ─ □ x│
├──────────────┬──────────────────────────────────────┤
│              │                                      │
│   AI Chat    │         3D Viewport                  │
│   Panel      │         or                           │
│              │         TechDraw Sheet               │
│  [user msg]  │                                      │
│  [ai reply]  │                                      │
│              │                                      │
│  [input___]  │                                      │
│              │                                      │
├──────────────┴──────────────────────────────────────┤
│  Status bar                                         │
└─────────────────────────────────────────────────────┘
```

### Color palette

- **Background**: Dark (#1e1e2e) — Cursor-inspired
- **Chat panel**: Slightly lighter dark (#252535)
- **Concrete**: Light grey (#b0b0b0) with subtle texture
- **Rebar**: Steel blue-grey (#708090) or construction orange (#e87d2f)
- **Dimensions**: White (#ffffff) on dark background
- **Accent**: Blue (#4a9eff) for selections and highlights

### Typography for overlays

- **Headlines**: Inter or SF Pro, Bold, 48-64px
- **Body text**: Inter or SF Pro, Regular, 24-32px
- **Code/specs**: JetBrains Mono or SF Mono, 20-28px
- **Color**: White with subtle drop shadow on dark backgrounds

### Music references

- Linear app promo style: minimal, electronic, subtle
- Stripe developer docs style: calm, confident
- NOT: dramatic startup pitch music, dubstep, or corporate
- Suggestion: Artlist or Epidemic Sound, search "minimal tech" or "product demo"

---

## Recording Checklist

### Before recording

- [ ] Clean desktop — hide all other apps, notifications off
- [ ] Set screen resolution to 2560x1440 or 3840x2160
- [ ] Buildable dark theme active, font size readable at 1080p
- [ ] Pre-load the project so there's no cold-start delay
- [ ] Practice the chat inputs — know exactly what to type
- [ ] Test that all generations work without errors
- [ ] Clear chat history for a fresh look

### During recording

- [ ] Record at native resolution (4K preferred)
- [ ] Use OBS Studio or similar (free, good quality)
- [ ] Smooth, deliberate mouse movements
- [ ] Type at a natural pace in chat (not too fast)
- [ ] Pause briefly after each generation to let viewer absorb
- [ ] Record multiple takes — pick the cleanest one

### After recording

- [ ] Edit in DaVinci Resolve (free) or Premiere
- [ ] Add text overlays and transitions
- [ ] Add music track
- [ ] Export: 1080p for social media, 4K for website
- [ ] Create thumbnail: split-screen of Buildable + drawing output
- [ ] Write post copy for LinkedIn/X

---

## Distribution Plan

### Video 1 (30 sec — "The Change Request")

| Platform | Format | Notes |
|----------|--------|-------|
| LinkedIn | Native video, square 1:1 | Tag #precast #structuralengineering #CAD #AI |
| X/Twitter | Native video, 16:9 | Short punchy caption: "2 months of work. Updated in 30 seconds." |
| YouTube Shorts | Vertical 9:16 crop | Add captions/subtitles |
| Reddit | r/engineering, r/civilengineering, r/structuralengineering | "We built a tool that auto-generates precast structural drawings" |
| Instagram Reels | Vertical 9:16 crop | Same as YouTube Shorts |

### Video 2 (60 sec — "The Foundation")

| Platform | Format | Notes |
|----------|--------|-------|
| buildable.to | Hero section, autoplay muted, loop | Primary placement |
| YouTube | Standard upload | SEO: "AI generates structural drawings from text" |
| LinkedIn | Long-form post with video | Founder story + demo |

### Video 3 (2-3 min — "The Full Project")

| Platform | Format | Notes |
|----------|--------|-------|
| YouTube | Full video | SEO: "AI-powered precast structural detailing — full project demo" |
| buildable.to/demo | Dedicated demo page | With CTA to try or join waitlist |
| Email to precast companies | Direct link | Nikoloz sends to association members |

---

## Timeline

| Week | Milestone |
|------|-----------|
| 1-4 | Build: Foundation F-1 end-to-end (3D + rebar + TechDraw + BBS) |
| 5 | Build: AI edit/change propagation working |
| 6 | Record Video 1 (30 sec). Post to social media. |
| 7 | Record Video 2 (60 sec). Put on website. |
| 8-12 | Build: More element types (columns, beams) |
| 13 | Record Video 3 (2-3 min). Post to YouTube. |

**The 30-second video is the forcing function.** It defines exactly what you need to build first and gives you a hard deadline. Everything else follows from that.
