# Buildable — Business Model & Pricing

*Last updated: 2026-02-10*

---

## The One-Line Business Model

**B2B SaaS subscription selling AI-powered structural detailing to precast concrete companies, priced per factory/location.**

---

## Two Products, Two Buyers

Buildable is not one product — it's two, serving different people at the same company:

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│   BUILDABLE DESKTOP                    BUILDABLE PORTAL          │
│   ─────────────────                    ────────────────          │
│                                                                  │
│   WHO: The engineer                    WHO: The owner/CTO        │
│   WHAT: AI-powered CAD tool            WHAT: Web-based platform  │
│   WHY: "I generate drawings faster"    WHY: "I control my        │
│                                         company's design IP"     │
│                                                                  │
│   ┌─────────────────────┐              ┌─────────────────────┐  │
│   │  FreeCAD + AI Chat  │              │  Element Library     │  │
│   │  3D Model + Rebar   │   ◄─sync─►  │  Template Library    │  │
│   │  TechDraw Sheets    │              │  Project Dashboard   │  │
│   │  BBS Tables         │              │  Standards Config    │  │
│   │  DWG/PDF Export     │              │  Analytics           │  │
│   └─────────────────────┘              └─────────────────────┘  │
│                                                                  │
│   Sold as: Pro plan                    Sold as: Enterprise plan  │
│   Decision: Engineer says "I need      Decision: Owner says      │
│   this tool"                           "the company needs this   │
│                                         platform"                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Pricing Tiers

### Free

**Price:** $0
**Purpose:** Try it, fall in love, tell your colleagues

| What's Included |
|-----------------|
| 1 user |
| 3 AI element generations per month |
| Standard element library (foundations, columns, beams) |
| Watermarked PDF export |
| Community support |

**Why free matters:** Engineers are skeptical. They won't pay before seeing it work on their own element. Free removes the "let me check with my boss" barrier. And watermarked exports mean their output becomes marketing — every drawing that gets shared has "Made with Buildable" on it.

---

### Pro — $400/month ($4,800/year)

**Price:** $400/month per company (up to 5 users)
**Purpose:** Small-to-mid precast company running real projects

| What's Included |
|-----------------|
| Up to 5 users |
| Unlimited AI generations |
| Unlimited exports (DWG, PDF, IFC) |
| Full element library (foundations, columns, beams, walls, slabs, stairs) |
| Eurocode 2 standard library |
| Standard title block templates |
| BBS table generation |
| Material summaries |
| Email support |

**Who buys this:** A Georgian precast company with 2-5 engineers, doing 5-10 projects/year. The engineer tries the free tier, generates a few elements, shows the output to the boss. Boss sees it works. $400/month vs. $6,000/project in manual drawing labor. Easy yes.

**The ROI pitch:**

```
Manual drawing cost:     $6,000/project × 5 projects = $30,000/year
Buildable Pro:           $400/month × 12              =  $4,800/year
                                                        ──────────
Savings:                                                $25,200/year
ROI:                                                    5.25x
```

---

### Enterprise — $2,000+/month per factory

**Price:** $2,000-3,000/month per factory location
**Purpose:** Multi-factory, multi-country operations with custom standards

| What's Included (everything in Pro, plus) |
|------------------------------------------|
| **Buildable Portal** (web-based platform) |
| Unlimited users per factory |
| Custom element library — company's own parametric types |
| Custom title blocks & BBS formats per country/client |
| Multiple code standards (Eurocode + Turkish code + ACI + etc.) |
| Tekla / Revit / IFC import-export integration |
| Drawing approval workflows |
| Revision tracking & drawing archive |
| Project dashboard with analytics |
| Standards configuration (cover, spacing, materials) |
| API access |
| Dedicated onboarding & training |
| Priority support with SLA |

**Who buys this:** A company with 2-5 factories, 10-30 engineers, operating across multiple countries. The decision-maker is the owner or CTO, not the individual engineer.

**The ROI pitch:**

```
Company: 3 factories, 20 engineers, 30 projects/year

Manual drawing cost:     20 engineers × 50% time on drawings × $3,000/mo salary
                         = $30,000/month = $360,000/year in drawing labor

Buildable Enterprise:    3 factories × $2,500/month = $7,500/month = $90,000/year

Even saving only 50% of drawing time:
Savings:                 $180,000/year
ROI:                     2x

Saving 70% (realistic once element library is built):
Savings:                 $252,000/year
ROI:                     2.8x
```

---

## Why Price Per Factory (Not Per Seat)

| Per Seat | Per Factory |
|----------|-------------|
| Companies minimize seat count to save money | Companies want ALL engineers using it |
| Discourages adoption | Encourages adoption |
| Doesn't correlate with value | More factories = more projects = more value |
| Creates awkward "who gets a license" politics | "Everyone at this plant can use it" |
| Revenue: 5 seats × $200 = $1,000 | Revenue: 1 factory × $2,500 = $2,500 |

Precast companies think about their business in factories, not headcount. "We have 3 plants" is how they describe their scale. Pricing per factory matches how they think.

---

## The Enterprise Portal

The portal is the web-based platform where the company manages its design IP. This is the lock-in layer.

### Element Library

```
┌─────────────────────────────────────────────────────────────┐
│  My Company > Element Library                    + New Type  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  📁 Foundations                                              │
│  ├── F-1 Standard Pad                    [used 47 times]    │
│  │   3200×4200, C30/37, bottom Ø12@200                      │
│  │   Tags: warehouse, standard                               │
│  │                                                           │
│  ├── F-2 Wide Pad                        [used 23 times]    │
│  │   3200×4700, C30/37, bottom Ø12@200                      │
│  │   Tags: warehouse, wide-span                              │
│  │                                                           │
│  └── F-3 Deep Pad (soft soil)            [used 8 times]     │
│      3600×5000, C35/45, bottom Ø16@150                      │
│      Tags: residential, soft-ground                          │
│                                                              │
│  📁 Columns                                                  │
│  ├── COL-600 Standard                    [used 112 times]   │
│  ├── COL-600 Seismic                     [used 34 times]    │
│  └── COL-800 Heavy Load                  [used 31 times]    │
│                                                              │
│  📁 Beams                                                    │
│  ├── BM-R400 Rectangular                 [used 67 times]    │
│  ├── BM-T600 T-Section                   [used 45 times]    │
│  └── BM-L500 L-Section                   [used 19 times]    │
│                                                              │
│  📁 Walls                                                    │
│  📁 Slabs                                                    │
│  📁 Connections                                              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

Each element type is a parametric template:
- Default dimensions (overridable per project)
- Standard rebar arrangements
- Company-specific detailing rules
- Preferred materials and grades
- Drawing layout and annotation style

When an engineer in Buildable Desktop says "create Foundation F-1 for the new warehouse," the AI already knows the company's F-1 template. It just asks for the project-specific dimensions. This is what makes Buildable faster than any generic AI tool — it has the company's institutional knowledge built in.

**Switching cost:** A company with 50+ validated element types built over 2 years will never recreate that in another tool. This is the moat.

### Template Library

```
┌─────────────────────────────────────────────────────────────┐
│  My Company > Templates                        + New Template│
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  📄 Title Blocks                                             │
│  ├── Georgian Standard (A3)              [default]          │
│  ├── Turkish Standard (A3)                                   │
│  ├── Client: ALTA Group                                      │
│  └── Client: Batumi Development                              │
│                                                              │
│  📄 BBS Formats                                              │
│  ├── Georgian Standard                   [default]          │
│  ├── Eurocode General                                        │
│  └── Turkish Standard                                        │
│                                                              │
│  📄 Drawing Layouts                                          │
│  ├── Foundation: Plan + 2 Sections + BBS                     │
│  ├── Column: Elevation + 3 Sections + BBS                    │
│  └── Beam: Side + 2 Sections + BBS                           │
│                                                              │
│  📄 Standard Notes                                           │
│  ├── General structural notes (Georgian)                     │
│  ├── Concrete specification notes                            │
│  └── Rebar specification notes                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Project Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│  My Company > Projects                        + New Project  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  🏗️ ALTA Small Warehouse (Tbilisi)            ██████░░ 73%  │
│  84×48m | 84 elements | Started: Jan 15 | Due: Mar 1        │
│  Concrete: 342 m³ | Steel: 28.4 tons | Drawings: 62/84     │
│  Last activity: 2 hours ago by Giorgi                        │
│                                                              │
│  🏗️ Batumi Residential Complex               ██░░░░░░ 12%  │
│  126 elements | Started: Feb 1 | Due: Apr 15                │
│  Concrete: est. 890 m³ | Steel: est. 71 tons                │
│  Last activity: yesterday by Nino                            │
│                                                              │
│  🏗️ Ankara Shopping Mall                      ░░░░░░░░  0%  │
│  45 elements (estimated) | Not started | Due: May 1          │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  📊 This Month                                               │
│  Elements generated: 34    Drawings exported: 28             │
│  Est. hours saved: 156     Est. cost saved: $7,800           │
└─────────────────────────────────────────────────────────────┘
```

### Standards Configuration

```
┌─────────────────────────────────────────────────────────────┐
│  My Company > Standards                                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Design Code                                                 │
│  ├── Primary: Eurocode 2 (EN 1992-1-1)                      │
│  ├── National Annex: Georgia                                 │
│  └── Secondary: Turkish Seismic Code (TBDY 2018)            │
│                                                              │
│  Concrete                                                    │
│  ├── Approved classes: C20/25, C25/30, C30/37, C40/50       │
│  ├── Default: C30/37                                         │
│  └── Aggregate size: 20mm                                    │
│                                                              │
│  Reinforcement                                               │
│  ├── Main bars: A500c                                        │
│  ├── Stirrups: A240c                                         │
│  ├── Welded mesh: B500B                                      │
│  ├── Available diameters: Ø8, Ø10, Ø12, Ø14, Ø16, Ø20, Ø25│
│  └── Preferred diameters: Ø12, Ø16, Ø20 (minimize variety)  │
│                                                              │
│  Cover Requirements (company minimums)                       │
│  ├── Interior elements: 30mm                                 │
│  ├── Exterior elements: 40mm + 5mm company safety margin     │
│  ├── Ground contact: 50mm                                    │
│  └── Fire rating R60: 35mm                                   │
│                                                              │
│  Drawing Standards                                           │
│  ├── Scale: 1:50 (plans), 1:20 (sections), 1:10 (details)  │
│  ├── Dimension style: Eurocode standard                      │
│  ├── Rebar mark format: Ø[diameter] [grade] pos.[number]    │
│  └── Language: Georgian (ქართული) + English                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Analytics

```
┌─────────────────────────────────────────────────────────────┐
│  My Company > Analytics                     Jan 2027         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Usage                                                       │
│  ├── Elements generated:        142                          │
│  ├── Drawing sets exported:     118                          │
│  ├── AI conversations:          267                          │
│  └── Change propagations:       89                           │
│                                                              │
│  Efficiency                                                  │
│  ├── Est. hours saved:          640 hrs                      │
│  ├── Est. cost saved:           $32,000                      │
│  ├── Avg time per element:      12 min (vs ~4 hrs manual)    │
│  └── Accuracy (0 corrections):  87%                          │
│                                                              │
│  Most Used Elements                                          │
│  1. COL-600 Standard        (34 generations)                 │
│  2. F-1 Standard Pad        (28 generations)                 │
│  3. BM-R400 Rectangular     (22 generations)                 │
│                                                              │
│  By Factory                                                  │
│  ├── Tbilisi Plant:    68 elements (48%)                     │
│  ├── Kutaisi Plant:    45 elements (32%)                     │
│  └── Batumi Plant:     29 elements (20%)                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

The analytics serve two purposes:
1. **For the customer:** Justify the subscription to management. "We saved $32K this month."
2. **For you:** Understand usage patterns, identify expansion opportunities, reduce churn.

---

## Revenue Model Over Time — The Layer Cake

```
Year 1:  Layer 1 — AI Structural Detailing (SaaS subscription)
         Revenue: Pro subscriptions + first Enterprise pilots
         $2K-5K MRR

Year 2:  Layer 2 — Enterprise Portal + Element Library
         Revenue: Enterprise subscriptions at $2K+/factory
         + Material Takeoff (concrete volumes, steel weights, costs)
         $20K-50K MRR

Year 3:  Layer 3 — Procurement Integration
         "Your BBS says you need 2.4 tons of Ø12 A500c rebar.
          Order from 3 suppliers — best price: $X from Supplier Y."
         Revenue: Referral fee or % of material orders
         This is the Toast playbook — fintech layered on SaaS

Year 4+: Layer 4 — Project Financing
         "Finance this $50K steel order. Pay in 90 days."
         Revenue: Interest margin on material financing
         This is where Toast makes 50% of revenue

         Layer 5 — Production Planning
         "Optimal mold schedule for next 2 weeks:
          Day 1: F-1 (molds 1-4), COL-600 (mold 5)..."
         Revenue: Premium module on Enterprise plan
```

Each layer sells to the **same customer**. You don't need new customers to grow revenue — you grow by going deeper with existing ones. This is the vertical SaaS magic.

---

## Revenue Projections

### Conservative Scenario

| Month | Pro Customers | Enterprise Factories | MRR | ARR |
|-------|--------------|---------------------|-----|-----|
| 6 | 3 | 0 | $1,200 | $14,400 |
| 12 | 8 | 1 | $5,700 | $68,400 |
| 18 | 15 | 3 | $12,500 | $150,000 |
| 24 | 25 | 8 | $26,000 | $312,000 |
| 36 | 40 | 20 | $56,000 | $672,000 |

Assumes: $400/mo Pro, $2,500/mo per Enterprise factory, 5% monthly churn on Pro, 2% on Enterprise.

### Aggressive Scenario (with Turkey + Middle East expansion)

| Month | Pro | Enterprise Factories | MRR | ARR |
|-------|-----|---------------------|-----|-----|
| 12 | 12 | 2 | $9,800 | $117,600 |
| 18 | 30 | 8 | $32,000 | $384,000 |
| 24 | 50 | 15 | $57,500 | $690,000 |
| 36 | 80 | 40 | $132,000 | $1,584,000 |

---

## Pricing by Geography

Don't publish different prices. Use one price list, with non-public regional adjustments.

| Market | Pro | Enterprise (per factory) | Justification |
|--------|-----|-------------------------|---------------|
| Georgia | $200-300/mo | $1,000-1,500/mo | Design partner pricing, low salaries |
| Turkey | $300-400/mo | $1,500-2,000/mo | Large market, mid-range salaries |
| Middle East (UAE, Saudi) | $500-700/mo | $2,500-3,500/mo | High salaries, massive projects |
| Europe | $500-700/mo | $3,000-4,000/mo | Highest willingness to pay |
| US | $500-800/mo | $3,000-5,000/mo | Highest salaries, largest savings |

**Rule:** List price is the Western/US price on the website. Regional customers get "partner discounts" through direct sales. This avoids anchoring to a low price that you can't raise later.

---

## What Customers Pay For vs. What They Get

| They Pay For | What Actually Creates the Lock-in |
|-------------|----------------------------------|
| AI element generation | Their element library (50+ validated types built over months) |
| Drawing export | Their template library (title blocks, BBS formats per client) |
| Monthly subscription | Their project history and institutional knowledge |
| Enterprise portal access | Their standards configuration (company-specific rules) |

The tool is the hook. The data is the moat.

---

## Competitive Pricing Context

| Product | Price | What You Get |
|---------|-------|-------------|
| **Tekla Structures** | $10,000-20,000/seat/year | Full BIM detailing, no AI automation |
| **Allplan Precast** | $5,000-15,000/seat/year | Precast-specific BIM, no AI |
| **AutoCAD** | $2,000-4,000/seat/year | General 2D drafting, fully manual |
| **Revit** | $3,000-5,000/seat/year | General BIM, not precast-specific |
| **Buildable Pro** | $4,800/year (whole company) | AI detailing, precast-specific, automated |
| **Buildable Enterprise** | $24,000-36,000/factory/year | AI + portal + custom library + integrations |

**Key differentiator:** Every competitor charges per seat and gives you a tool. Buildable charges per company/factory and gives you **automation**. The engineer still has to draw in Tekla. In Buildable, the AI draws for them.

---

## Pricing Principles

1. **Simple.** Two numbers: Pro monthly price, Enterprise monthly price. No tiers within tiers, no feature matrices, no "contact sales" on Pro.

2. **Price on value, not cost.** If Buildable saves $25K/year, charging $5K/year is a bargain. Don't price based on your server costs or AI API bills.

3. **Never anchor low.** Georgian partners get private discounts. The public price is the Western price. You can always discount down, you can never raise up.

4. **Annual discount.** Offer 2 months free for annual prepayment (effectively 17% discount). Improves cash flow and reduces churn.

5. **The 10x rule.** Product should deliver 10x its cost in savings. $400/month should save $4,000+/month. If it doesn't, the product isn't ready — fix the product, don't drop the price.

6. **Don't compete on price.** You're not "cheap Tekla." You're "AI structural detailing that didn't exist before." Different category, different value.

---

## Build Sequence

What to build and when — business model features only:

```
NOW (Month 1-3):
├── Desktop app: Foundation F-1 end-to-end
├── Free tier: watermarked PDF export
└── Pricing page on buildable.to (Pro + Enterprise, "coming soon")

NEXT (Month 4-6):
├── Pro tier: payment integration (Stripe)
├── Unlimited AI + export for Pro customers
├── Basic licensing / activation system
└── More element types (columns, beams)

LATER (Month 7-12):
├── Enterprise portal MVP
│   ├── Element library (custom types)
│   ├── Template library (custom title blocks)
│   └── Basic project dashboard
├── Multi-user support
└── DWG/IFC export

FUTURE (Year 2):
├── Full portal: analytics, standards config, approval workflows
├── Material takeoff + procurement integration
├── Tekla/Revit import
└── API for third-party integrations
```

**Critical rule:** Do NOT build the portal before having 5+ paying Pro customers. The portal is an Enterprise upsell, and Enterprise customers only come after you've proven the core product works.

---

## Key Metrics to Track

| Metric | What It Tells You | Target |
|--------|-------------------|--------|
| **MRR** | Revenue health | Growing 15-20% monthly |
| **Pro → Enterprise conversion** | Portal value | 20%+ of Pro customers upgrade within 12 months |
| **Net Revenue Retention** | Are customers expanding? | >110% (they pay more over time, not less) |
| **Time to first export** | Onboarding quality | <30 minutes from signup to first drawing |
| **Elements per customer per month** | Product stickiness | Growing month over month |
| **Churn** | Product-market fit | <5% monthly (Pro), <2% monthly (Enterprise) |
| **Customer Acquisition Cost** | GTM efficiency | <3 months of subscription revenue |
| **Element library size (Enterprise)** | Lock-in depth | Growing = they're investing in the platform |
