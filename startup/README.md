# Buildable — Startup Docs

Cursor for CAD. A fork of FreeCAD with an AI-native design experience.

---

## Documents

| Doc | What's in it |
|-----|-------------|
| [RESEARCH.md](RESEARCH.md) | Competitive landscape, market sizing, Cursor playbook, FreeCAD platform analysis, strategic questions |
| [TEAM_CRITIQUE.md](TEAM_CRITIQUE.md) | Honest assessment of team gaps, missing roles, counterarguments, and prioritized recommendations |

---

## Quick Facts

- **What**: Fork of FreeCAD + AI assistant that edits Python source code to create 3D designs
- **Positioning**: "Cursor for CAD" — same playbook as Cursor (fork of VS Code)
- **Architecture**: Code-as-source-of-truth — Claude Code reads/edits `source.py`, FreeCAD executes it
- **Team**: Luka (tech), Otar (business), Nikoloz (domain/construction industry)
- **Stage**: Pre-launch, building since Dec 2025
- **Market**: CAD software $12-23B, broader engineering software $48.8B → $126.1B by 2030

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
