# Buildable — Deep Research Report

*Last updated: 2026-02-10*

## What is Buildable?

Buildable is an AI-native parametric 3D modeler for structural engineering. Engineers describe designs in natural language and Claude Code edits a Python `source.py` that defines the design. Built on FreeCAD and the OpenCASCADE geometry kernel.

- **GitHub**: github.com/buildable-to/Buildable
- **Website**: buildable.to
- **Created**: December 2025, active development since January 2026

### Founding Team

- **Luka Lortkipanidze** — Technical lead. ML/Data Engineering background. Ex-Tether. Co-founded Bitpulse (BitpulseAI). Builds the AI layer and core platform.
- **Otar Donadze** — Business lead. Business major. Worked with Luka at Bitpulse for 1.5 years. Handles strategy, go-to-market, and operations.
- **Nikoloz Lortkipanidze** — Domain expert. Civil Engineering major. Works as a constructor. CTO of the Georgian Precast Association (umbrella org combining multiple precast companies in Georgia). Brings real-world construction/engineering workflows and industry connections.

The team covers the three critical bases: **AI/engineering** (Luka), **business** (Otar), and **domain expertise with industry access** (Nikoloz). Nikoloz's position at the Georgian Precast Association provides a direct channel to commercial customers — a built-in distribution advantage that Ondsel never had.

Fun fact: Cursor's founders originally spent almost a year building AI autocomplete for mechanical engineering CAD software before pivoting to code editing because the market was "stagnant." Three years later, CAD is one of the hottest "Cursor for X" domains.

---

## Competitive Landscape

### Direct Competitors — AI-First CAD Startups

| Company | Funding | Approach | Differentiation |
|---------|---------|----------|-----------------|
| **Zoo.dev** (ex-KittyCAD) | $10.1M (Sequoia) | New CAD from scratch, custom language (KCL), custom engine | 300K users, open app layer, proprietary engine |
| **Adam** (YC W25) | $4.1M | Text-to-parametric-CAD, standalone tool | Viral (10M+ impressions), starting Onshape integration |
| **MecAgent** | ~$3M | AI copilot plugin for SolidWorks/CATIA/Fusion/Creo | 10K users in 5 months, interest from Ford/Tesla/Audi |
| **Leo AI** | $9.7M (Flint, a16z scout) | "Large Mechanical Model" — engineering knowledge copilot | 50K+ users, HP/Siemens/Mobileye clients |
| **Backflip AI** | $30M (NEA, a16z) | Scan-to-parametric-CAD (reverse engineering) | Founded by Markforged CEO, Transformer co-inventor as angel |
| **Hestus** (YC S24) | $1.5M | AI copilot for CAD sketching (Fusion 360 plugin) | Narrow focus, 12x sketch optimization |
| **DraftAid** (YC) | $500K+ | AI 2D drawing automation from 3D models | "GitHub Copilot for CAD drawings" |
| **Aurorin CAD** | Unknown | New AI-native CAD with custom kernel | Early stage |

**Total VC in AI-CAD startups: ~$58M+** (excluding incumbents' internal R&D)

### Incumbents Adding AI

| Vendor | AI Features | Status |
|--------|-----------|--------|
| **Autodesk** (Fusion/AutoCAD) | Neural CAD — generates editable B-Rep from text, AI Assistant, AutoConstrain | Shipping 2025 |
| **Dassault** (SolidWorks/CATIA) | AURA AI companion, 3 virtual companions, auto drawing generation | Announced Feb 2026 |
| **Siemens** (NX/Solid Edge) | Design Copilot, CAM AI copilot, auto drawings (80% coverage) | Shipping |
| **PTC** (Onshape/Creo) | AI Advisor, FeatureScript code generation, agent workflows | Shipping |

### FreeCAD-Specific AI Projects

- **neka-nat/freecad-mcp** (343+ stars) — MCP server connecting Claude to FreeCAD
- **Artifex** — Macro translating natural language to FreeCAD models via LLM APIs
- **GPT4FreeCAD** — GPT-4 integration for FreeCAD scripting
- Multiple academic papers on LLMs for CadQuery/build123d code generation

---

## The "Cursor for X" Playbook

### Cursor's Numbers

| Metric | Value |
|--------|-------|
| Valuation | $29.3B (Nov 2025) |
| Total funding | ~$3.5B |
| ARR | $1B+ (fastest SaaS ever — 17 months) |
| DAU | 1M+ |
| Paid conversion | 40% |
| Marketing spend | $0 to $100M ARR |

### Why Cursor Forked VS Code (Not a Plugin)

1. Extension API was too shallow — couldn't do repo-wide context, multi-file edits, terminal interaction
2. Full UX control — redesigned the entire experience around AI collaboration
3. Proprietary models — built custom models (Composer, Tab) that need deep integration
4. Speed — 62.9s avg task completion vs 89.9s for Copilot

### Successful Fork Precedents

- **Cursor** / VS Code → $29.3B
- **Brave** / Chromium → 93.8M MAU, $980M valuation
- **Windsurf** / VS Code → Acquired by Google for ~$2.4B

### Other "Cursor for X" Startups

- **Shortcut** — "Cursor for Excel" — $44.5M (a16z), scores >80% on Excel World Championship
- **Sourcetable** — "Cursor for Spreadsheets" — $4.3M seed
- **Leo AI** — "Cursor for Mechanical Engineering" — $9.7M
- **Adam** — "Cursor for CAD" — $4.1M (YC)
- **Vesence** — "Cursor for Lawyers" (YC)
- **Den** — "Cursor for Knowledge Workers" (YC)
- Video editing agents (Eddie AI, Descript, Overlap) — a16z thesis piece

---

## FreeCAD as a Platform

### Strengths for AI

- **Python-first**: Almost everything is scriptable — perfect for LLM code generation
- **Open source (LGPL)**: No licensing barriers to commercial redistribution
- **OpenCASCADE kernel**: Same professional-grade geometry engine as SolidWorks/CATIA
- **850K–1.25M users**, growing 30%+ after Autodesk pricing increases
- **75% of users willing to pay** for improvements
- **Headless execution**: Can generate and validate models server-side
- **FreeCAD 1.0** (Nov 2024) fixed the notorious Topological Naming Problem

### Weaknesses

- UX is the Achilles' heel — "quirks all the way down, no unified mental model between modules"
- Performance degrades on complex models
- 0.01% market share of tracked commercial CAD deployments
- Documentation gaps in the Python API
- Volunteer-dependent development (FPA spending ~EUR 250K/yr)

### The Ondsel Cautionary Tale

Ondsel was a VC-backed startup that tried to commercialize FreeCAD. They **shut down Nov 2024** after ~2 years despite:
- VC funding and a full team
- Building the assembly solver (now in FreeCAD 1.0)
- ~100 interviews with engineers
- Strong community support

**Why they failed**: Could not convert commercial customers. Closed-source CAD is taught in schools and deeply entrenched. Hobbyists loved it but couldn't sustain a business.

**Their legacy**: Assembly workbench, VarSets, 145+ PRs merged, EUR 40K "Ondsel Onwards Fund" to FPA.

---

## CAD Market Opportunity

- CAD software market: **$12–23B** (growing 6.2% CAGR)
- Broader engineering software: **$48.8B**, projected **$126.1B by 2030**
- 43% of SMEs cite learning curve as the #1 barrier to CAD adoption
- Average engineering team uses 5+ disconnected tools
- Generative design subsegment growing at ~18% CAGR

---

## What Makes Buildable Unique

| Approach | Who | Buildable's Advantage |
|----------|-----|----------------------|
| New CAD from scratch | Zoo, Aurorin | Leverages mature FreeCAD + OpenCASCADE, no need to rebuild entire CAD |
| Text-to-CAD standalone | Adam | Iterative editing of complex existing designs, not just generation from scratch |
| Plugin for commercial CAD | MecAgent, Hestus, Leo | No vendor lock-in, no $4K/yr base software cost, open source |
| AI features in commercial CAD | Autodesk, Siemens, Dassault | Code-as-source-of-truth — git-friendly, reproducible, full AI context |
| MCP plugins for FreeCAD | Various open source | Deep fork integration vs shallow RPC bridge |

### The Core Thesis

> FreeCAD's biggest weakness (UX complexity) is exactly what AI can solve. If an AI assistant can shield users from FreeCAD's complexity by translating natural language into correct Python scripts, it bypasses the very limitations that have held FreeCAD back — and does so on a free, open-source, professional-grade geometry kernel.

---

## Key Strategic Questions

1. **Ondsel's ghost**: How does Buildable avoid the same fate? (Ondsel had more resources and still couldn't convert commercial customers)
2. **Adam is claiming "Cursor for CAD"**: They have $4.1M, YC backing, and viral traction. How do you differentiate?
3. **Fork maintenance burden**: FreeCAD has 45K+ commits. Keeping up with upstream while diverging is costly.
4. **Go-to-market**: FreeCAD's user base is 45% hobbyists. Where are the paying customers?
5. **Why Claude Code specifically**: Tight coupling to one LLM vendor vs. model-agnostic approach?

---

## Sources

### Buildable
- https://buildable.to
- https://github.com/buildable-to/Buildable

### Competitors
- https://zoo.dev — Zoo (ex-KittyCAD)
- https://adam.new — Adam CAD
- https://mecagent.com — MecAgent
- https://www.getleo.ai — Leo AI
- https://backflip.ai — Backflip AI
- https://www.hestus.co — Hestus
- https://draftaid.io — DraftAid
- https://www.aurorincad.com — Aurorin CAD

### Incumbents
- https://www.autodesk.com/products/fusion-360/ai-automation
- https://www.autodesk.com/solutions/autodesk-ai/neural-technology
- https://plm.sw.siemens.com/en-US/nx/cad-online/ai/
- https://www.onshape.com/en/features/ai-advisor

### FreeCAD AI Projects
- https://github.com/neka-nat/freecad-mcp
- https://github.com/contextform/freecad-mcp
- https://github.com/islamnurdin/Artifex
- https://github.com/revhappy/GPT4FreeCAD

### Cursor / Fork Model
- https://research.contrary.com/company/anysphere
- https://cursor.com/blog/series-d
- https://x.com/lennysan/status/1917964591029719277 (Cursor's CAD origins)

### FreeCAD Ecosystem
- https://blog.freecad.org/2024/11/19/freecad-version-1-0-released/
- https://www.ondsel.com/blog/goodbye/
- https://fpa.freecad.org/annualreports/2025.html

### Market Data
- https://www.futuremarketinsights.com/reports/computer-aided-design-cad-market
- https://www.mordorintelligence.com/industry-reports/engineering-software-market
- https://techcrunch.com/2025/10/31/yc-alum-adam-raises-4-1m-to-turn-viral-text-to-3d-tool-into-ai-copilot/
