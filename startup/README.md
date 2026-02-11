# Buildable — Startup Docs

AI-powered structural detailing for precast concrete. Built on open-source CAD with an AI-native design experience.

---

## Documents

| Doc | What's in it |
|-----|-------------|
| [RESEARCH.md](RESEARCH.md) | Competitive landscape, market sizing, Cursor playbook, FreeCAD platform analysis, strategic questions |
| [TEAM_CRITIQUE.md](TEAM_CRITIQUE.md) | Honest assessment of team gaps, missing roles, counterarguments, and prioritized recommendations |
| [CUSTOMER_DISCOVERY.md](CUSTOMER_DISCOVERY.md) | Interview guide for precast company founders — questions, what to listen for, call template |
| [PRECAST_PLAN.md](PRECAST_PLAN.md) | Product plan — precast vertical focus, phased roadmap, technical architecture, GTM, pricing |
| [DEMO_VIDEO.md](DEMO_VIDEO.md) | Demo video plan — 3 concepts (30s/60s/3min), storyboards, visual style, recording checklist, distribution |
| [STRATEGY.md](STRATEGY.md) | Comprehensive strategy — YC lessons, vertical SaaS thesis, wedge strategy, Cursor playbook, Ondsel lessons, precast market, pricing, 12-month plan |
| [BUSINESS_MODEL.md](BUSINESS_MODEL.md) | Business model — B2B SaaS pricing (Free/Pro/Enterprise), enterprise portal design, revenue layer cake, projections, geographic pricing |

---

## Quick Facts

- **What**: AI-powered CAD that generates complete precast structural drawings from natural language (built on FreeCAD + OpenCASCADE)
- **Positioning**: AI-powered structural detailing for precast concrete — vertical-first, not generic CAD
- **Playbook**: Same approach as Cursor (fork open-source, add deep AI) but targeting a specific vertical
- **Architecture**: Code-as-source-of-truth — Claude Code reads/edits `model.py`, FreeCAD executes it
- **Team**: Luka (tech), Otar (business), Nikoloz (domain/CTO of Georgian Precast Association)
- **Stage**: Pre-launch, building since Dec 2025
- **Key insight**: One of Georgia's biggest precast companies: design/drawings take **2 months**, actual construction takes **15 days** — 4x longer on paper than on concrete
- **Market**: Precast concrete $143-155B globally; CAD software $12-23B; broader engineering software $48.8B → $126.1B by 2030

## Key Competitors

- **Zoo.dev** — $10.1M, new CAD from scratch with custom language
- **Adam** — $4.1M (YC), text-to-CAD standalone, claims "Cursor for CAD"
- **Leo AI** — $9.7M, engineering knowledge copilot
- **Backflip** — $30M, scan-to-CAD
- **MecAgent** — ~$3M, AI plugin for commercial CAD
- Incumbents (Autodesk, Siemens, Dassault, PTC) all adding AI features

## Our Edge

1. Code-as-source-of-truth (git-friendly, reproducible, full AI context)
2. Built on mature open-source CAD with professional geometry kernel (OpenCASCADE)
3. Free — no $4K/yr base software cost
4. Domain co-founder with industry association access (built-in first customers)
5. Iterative editing of complex designs, not just text-to-CAD generation
