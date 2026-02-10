# Buildable — Vertical Strategy & YC Lessons

*Last updated: 2026-02-10*

This document synthesizes deep research on Y Combinator startup lessons, vertical SaaS strategy, the "Cursor for X" playbook, and construction/precast market dynamics — all applied to Buildable's strategic positioning.

> **Key insight from customer discovery:** One of Georgia's biggest precast companies told us their design/drawing phase takes **2 months** while actual physical construction takes only **15 days**. They spend **4x longer on paper than on concrete.** The bottleneck in precast isn't building — it's the paperwork before building. This is the problem Buildable solves.

---

## Table of Contents

1. [YC's Core Startup Lessons](#1-ycs-core-startup-lessons)
2. [The Vertical SaaS Thesis](#2-the-vertical-saas-thesis)
3. [The Wedge Strategy](#3-the-wedge-strategy)
4. [Vertical AI — The 2025-2026 Playbook](#4-vertical-ai--the-20252026-playbook)
5. [The Cursor Playbook — Lessons for Buildable](#5-the-cursor-playbook--lessons-for-buildable)
6. [Why Ondsel Failed & How to Avoid It](#6-why-ondsel-failed--how-to-avoid-it)
7. [Construction/Precast Market Deep Dive](#7-constructionprecast-market-deep-dive)
8. [Georgia as a Launchpad](#8-georgia-as-a-launchpad)
9. [Go-to-Market & Pricing](#9-go-to-market--pricing)
10. [The Buildable Playbook — Putting It All Together](#10-the-buildable-playbook--putting-it-all-together)

---

## 1. YC's Core Startup Lessons

### The Four Commandments

YC's essential startup advice boils down to four things, repeated endlessly by every partner:

1. **Launch something fast**
2. **Talk to users**
3. **Build what they want**
4. **Don't die**

Everything else is commentary.

### Launch Fast

YC doesn't mean "announce on Product Hunt." They mean: **get your product in front of real users who can give you real feedback.** A mediocre product in users' hands today beats a perfect product in six months.

> "If you are not embarrassed by the first version of your product, you've launched too late." — Reid Hoffman (often quoted at YC)

**What "launch" means for Buildable:** A working demo where one real precast engineer describes a foundation element and gets back a TechDraw sheet with rebar details and BBS table. That's the MVP launch. Not a marketing website. Not a polished UI. The drawing output.

### Talk to Users (The Mom Test)

YC is obsessed with customer discovery, but specifically the *right kind*. Don't pitch. Don't ask "would you use this?" Don't ask about the future. Instead:

- **Ask about their life, not your idea.** "Walk me through what happens when you get a new order."
- **Ask about the past, not the future.** "How much did you spend on design software last year?"
- **Look for pain they're already spending money/time to solve.** If they're not already trying to fix it, it's not real.

**10 customers who love you is better than 1,000 who kind of like you.** YC emphasizes finding a small group with a burning problem over a large group with passing interest.

### Growth Metrics

| Growth Rate | YC Assessment |
|-------------|---------------|
| 5-7% per week | Good (standard during YC batch) |
| 10% per week | Exceptional ("you're doing great") |
| <5% per week | Concerning — something is wrong |

**But:** Growth only makes sense after product-market fit. Before PMF, the metric is **retention** — are users coming back? Are they telling others?

### Common Mistakes (From Dalton Caldwell & Michael Seibel)

**1. Tarpit Ideas**
Ideas that seem appealing, get initial positive feedback, but become long-term traps. They attract many founders, generate early validation, but never quite work. Signs: lots of competitors trying the same thing, everyone says "great idea!" but nobody pays.

**2. Building Without Talking to Users**
Spending months building without validating whether anyone wants the product. The most dangerous form: "I know the industry, I don't need to ask."

**3. Over-Delegation Too Early**
Hiring senior people before achieving PMF causes founders to lose control and understanding of fundamentals.

**4. Insufficient Resilience**
The most common reason startups fail: founders give up. Dalton Caldwell's primary advice — **"Just don't die."** The defining trait of successful founders is profound self-belief and refusal to accept failure.

**5. Market Size Blindness**
Insufficient addressable markets limit startup potential regardless of execution quality. You need to be able to tell a credible story about how this becomes a $100M+ ARR business.

### Founder Mode (Paul Graham, September 2024)

PG's most viral recent essay. Key insights:

- Conventional wisdom says: "Hire good people and give them space." PG says this is wrong for founders.
- **Founder mode** means staying deeply involved in product, engineering, and customer decisions — even as you scale.
- Skip-level meetings become the norm. Founders shouldn't just talk to their direct reports.
- Brian Chesky (Airbnb) exemplified this: he went from delegating everything (company declined) to being deeply hands-on (company recovered).

**Applied to Buildable:** With a 3-person team, this isn't a choice — it's automatic. But as you grow, resist the urge to hire managers. Stay in the details.

### AI-Specific YC Advice (2025-2026)

- **Over 50% of YC's Spring 2025 batch** (70+ companies out of 144) were building agentic AI
- **"If your product can be replaced by a system prompt, you lack a moat."** Your product should be so deeply embedded in a user's workflow that switching costs are prohibitively high.
- **Workflow integration > chat interface.** Defensibility in 2026 is in the "last mile" of execution, not the "first mile" of generation.
- **Process power:** The unsexy engineering work — building thousands of edge cases, automation pipelines, safety checks — creates the real moat. Like CaseText's legal AI that took years of refining to work reliably.
- **Enterprises want vertical AI** — smaller, domain-specific models with deep context, privacy protections, and guaranteed accuracy.
- **The gold rush mentality of 2024 has given way to rigorous ROI scrutiny.** Investors now prioritize startups that deliver measurable business outcomes over experimental AI tools.

### "Do Things That Don't Scale"

The most important YC essay for your stage. The main goal: **learn as much as possible.**

**Specific examples from YC startups:**

| Startup | Unscalable Action | Result |
|---------|-------------------|--------|
| **Airbnb** | Founders rented a $500 camera and went door-to-door photographing listings | 2-3x more bookings for upgraded listings |
| **Stripe** | "Collison installation" — when anyone agreed to try Stripe, they'd say "give me your laptop" and set them up on the spot | Legendary adoption speed |
| **Brex** | Bought 300 bottles of Veuve Clicquot ($50 each), hand-delivered with handwritten notes from CEO to recently-funded startups | Massive early customer acquisition |

**What "doing things that don't scale" means for Buildable:**
- Physically sit with precast engineers as they use the tool. Watch where they get stuck.
- Manually generate drawings for your first 5 customers (even if the AI can't do it perfectly yet). Deliver the output, get feedback, iterate.
- Go to precast factories in person. Bring a laptop. Show the tool on their actual project.
- Nikoloz should introduce you to every precast company founder he knows — not via email, but in person over coffee.

---

## 2. The Vertical SaaS Thesis

### Why VCs Love Vertical SaaS

Every major VC firm (Bessemer, a16z, Sequoia, Point Nine) has published strong endorsements of the vertical strategy. The economics are consistently better than horizontal SaaS:

| Metric | Horizontal SaaS | Vertical SaaS |
|--------|-----------------|---------------|
| CAC Payback | 12-24 months | 6-12 months |
| Net Revenue Retention | 100-120% | 110-140%+ |
| Gross Margins | 70-80% | 75-85% |
| Market Share Achievable | 2-5% | 20-50%+ |
| Competitive Moat | Weak (many competitors) | Strong (niche dominance) |

### The "Layer Cake" Strategy

What separates good vertical software from great: continuously building additional products to sell into the core vertical. This is Bessemer's key lesson from a decade of vertical investing.

**Veeva** — the biggest vertical SaaS success story:
- Started with CRM for pharma sales reps (narrow wedge)
- Before CRM saturated, launched Veeva Vault (content management for pharma)
- Now approaching $2.4B revenue with 30%+ annual growth
- Each new product layer was sold to the same customer base

**Toast** — the restaurant revolution:
- Started with restaurant POS (point of sale)
- Added payments (now 50% of revenue), payroll, marketing tools, online ordering
- $4B+ market cap from a "just a restaurant tool" wedge
- Pioneered "SaaS + fintech" — free or cheap software subsidized by payment processing fees

**Procore** — construction's operating system:
- Started with project management for general contractors
- Expanded to: financials, quality/safety, preconstruction, workforce management
- $1B+ ARR. Made the software free for subcontractors and owners (network effect)
- Key insight: whoever controls the collaboration platform controls the ecosystem

**ServiceTitan** — HVAC to everything home services:
- Started with dispatching software for HVAC companies
- Expanded to plumbing, electrical, garage doors, pest control
- IPO'd December 2024 at $650M+ ARR
- Ara Mahdessian's rule: **"Never expand until the core has >8/10 NPS."**

### The Counter-Arguments — When Vertical Fails

**1. The TAM Trap** — If total addressable market is <$500M with no expansion path, you build a lifestyle business, not a venture-scale company. But VCs consistently underestimate vertical TAMs: Veeva was told "pharma CRM is a $200M market" — they turned it into $2.4B.

**2. Single Industry Cyclicality** — If your vertical is cyclical (construction, oil & gas), downturns can devastate revenue. Procore nearly ran out of money during 2008-2012.

**3. Customization Spiral** — Every customer wants something different. If you customize for each, you build a consulting business, not a product business. The fix: be opinionated. "This is best practice" rather than customizing for every customer.

**4. Growth Ceiling** — After capturing 30-50% of a vertical, growth slows. This is why the expansion strategy matters from Day 1. The wedge is not the business — it's the entry point.

---

## 3. The Wedge Strategy

### Picking the Right Wedge

A "wedge" is a strategy that involves solving the biggest bottleneck for a specific customer segment. What looks like a small market is actually a key that unlocks a much larger opportunity.

**Five characteristics of a good wedge:**

1. **You can be #1 fast** — small enough to dominate in 12-18 months
2. **Whole product exists** — you can deliver a complete solution (not a feature)
3. **No entrenched competition** — greenfield or only legacy solutions
4. **References propagate** — success stories travel to adjacent segments
5. **Partners available** — consultants, integrators, or resellers who serve this niche

### The TAM Wedge Sizing Method

A common mistake: sizing TAM of the wedge alone. The right way is to size the expansion path.

```
Buildable's TAM Expansion:

Wedge:      Precast structural detailing automation          ~$500M-1B
Adjacent 1: Full precast fabrication management (BIM→production)  ~$1-2B
Adjacent 2: Structural steel fabrication software            ~$1-2B
Adjacent 3: All specialty subcontractor fabrication          ~$5B
Adjacent 4: General structural engineering AI                ~$5-10B
Platform:   Construction industry AI/CAD platform            ~$50B+
```

**VC-investable sizing:** Most VCs want a wedge TAM of at least $1-2B AND a credible path to $10B+. The precast wedge works because the expansion path is clear and each adjacent market has similar workflows.

### The "Earn the Right" Expansion (ServiceTitan's Playbook)

1. **Become indispensable** for one workflow (for Buildable: drawing generation from parameters)
2. **Customers pull you** into adjacent workflows (they'll ask for production planning, then material takeoffs, then BIM export)
3. **Never expand until the core has >8/10 NPS** — premature expansion kills vertical companies
4. **Each expansion should increase NRR by 5-10%** — if it doesn't, it's the wrong expansion

### The Bowling Pin Strategy (Geoffrey Moore)

Each market segment you dominate makes the next one easier:

```
Pin 1: Georgian precast companies (Nikoloz's direct connections)
Pin 2: Turkish precast companies (similar standards, geographic proximity)
Pin 3: Middle East precast (massive construction boom, Eurocode-based)
Pin 4: European precast (largest precast market globally)
Pin 5: Cast-in-place concrete detailing (adjacent workflow)
Pin 6: Steel structure detailing (similar BIM→fabrication flow)
Pin 7: General structural engineering AI
```

---

## 4. Vertical AI — The 2025-2026 Playbook

### Bessemer's Framework: Why Vertical AI > Vertical SaaS

Traditional vertical SaaS digitized workflows. Vertical AI **performs** them. This is a 10x larger market:

- Traditional SaaS competes for **IT budgets** (~$500B globally)
- Vertical AI competes for **labor budgets** (~$4 trillion in US wages alone)

The opportunity: automate high-complexity tasks previously impossible for software, in markets worth ~13% of US GDP.

### Bessemer's "Good, Better, Best" Framework

| Level | What You Build | Competitors | Moat |
|-------|----------------|-------------|------|
| **Good** | New features that demo well, some productivity boost | SaaS incumbents | Execution speed |
| **Better** | Features with measurable ROI in core workflows | Adjacent players | Complex product + early data |
| **Best** | End-to-end workflows "not previously possible without LLMs" | Nobody | Data + multimodal superiority |

**Buildable should aim for "Best":** Generating complete structural drawings from natural language descriptions is not possible without LLMs. No existing tool does this. That's the sweet spot.

### Contrary Research: The Vertical AI Playbook

Key finding: **42% of enterprise AI initiatives were discontinued in 2024.** The problem isn't technology — it's implementation. Winners will redesign workflows, not just add AI to existing ones.

Three deployment paths:

1. **Sell Software to Operators** (fastest, most scalable) — This is Buildable's path
2. **Buy & Modernize Operators** (acquire businesses, embed AI) — Capital-intensive
3. **Build Full-Stack AI Companies** (become the operator) — Maximum control

### Notable Vertical AI Companies Setting the Standard

| Company | Vertical | Funding | Key Metric |
|---------|----------|---------|------------|
| **Harvey** | Legal | $100M+ Series C, ~$1.5B val | $100M+ ARR, 300+ clients |
| **Abridge** | Healthcare (clinical docs) | $212M Series C, $850M+ val | Partners with Epic |
| **EvenUp** | Personal injury law | $135M+ raised | ~$50M+ ARR |
| **Ramp** | Corporate finance | $7.65B valuation | $300M+ ARR |
| **Tractable** | Insurance claims | $2B+ valuation | Photo-based damage assessment |

**Pattern:** The best vertical AI companies target workflows where: (a) the work is repetitive but requires domain expertise, (b) the output format is well-defined, (c) there's a clear feedback loop (accepted/rejected by human expert).

**This maps perfectly to precast detailing:** repetitive but requires structural engineering knowledge, output is standardized drawings, and the engineer reviews and approves.

### 10 Principles for Defensible Vertical AI (Bessemer)

1. Align automation with customer needs, not technical possibility
2. Prioritize differentiated workflows over easily replicated features
3. Leverage AI for superhuman tasks (processing at inhuman scales)
4. Demonstrate quantifiable ROI
5. Innovate on business models (not just technology)
6. **Target niche markets first** — initial advantages in overlooked, high-ROI sectors
7. Customize for nuanced compliance/regulatory requirements
8. Build technical moats from multimodality (combine data types + workflow integration)
9. Build modular systems that can swap underlying models
10. Prioritize data quality over quantity

### The Moat Question for AI Startups

Sam Altman's advice: **Focus on being the only one doing what you do. Figure out the moat later.**

But investors in 2026 want specific defensibility:

- **Data Flywheel** — Product generates unique, non-public data that improves the model over time. For Buildable: every precast element generated, every engineer correction, every Eurocode validation creates proprietary training data.
- **Workflow Integration** — Your product is so embedded in daily operations (CRM, billing, production) that switching costs are prohibitive. For Buildable: once source.py contains a company's entire element library, switching costs are enormous.
- **Process Power** — The unsexy edge-case engineering (thousands of rebar detailing rules, Georgian title block formats, BBS table standards) that takes years to accumulate.

---

## 5. The Cursor Playbook — Lessons for Buildable

### Cursor's Origin Story

Anysphere was founded in 2022 by four MIT friends: Michael Truell, Sualeh Asif, Arvid Lunnemark, and Aman Sanger.

**The CAD chapter:** Before Cursor existed, the team spent ~4-8 months building AI for mechanical engineering/CAD. They were building "GitHub Copilot for CAD" — predicting the next changes engineers would make to 3D models.

**Why they abandoned CAD:**
1. **Feedback loop speed.** In code, you test output in seconds. In CAD, validating correctness requires simulation, physical testing, or expert review.
2. **Training data scarcity.** Code has GitHub. CAD models are scarce, proprietary, and harder to learn from.
3. **Text vs. spatial.** Code is text (LLMs are text machines). CAD geometry is spatial/visual.
4. **Market timing.** GPT-3.5/4 made AI-for-code about to break out. CAD was further away.

**The critical insight for Buildable:** The Cursor founders didn't abandon CAD because it was a bad market — they abandoned it because the technology wasn't ready. Your `source.py` architecture bridges this gap: **you convert the CAD problem into a code problem**, which is exactly where LLMs excel. This is a fundamentally different approach than what they tried in 2022.

### Cursor's Key Decisions

| Decision | Why It Mattered |
|----------|-----------------|
| **Fork VS Code** (not a plugin) | Full control over UX — Tab completion, inline diffs, file indexing couldn't be done as an extension |
| **Tab completion as killer feature** | Predicted multi-line edits and refactors, felt "magical" |
| **Proprietary model fine-tuning** | Built cursor-small for low-latency completions, not just API wrappers |
| **Speed over raw capability** | Made AI interactions feel instant — UX investment mattered more than model capability |
| **$0 marketing to $300M ARR** | Pure product-led growth, developer word-of-mouth |

### Cursor's Growth

| Date | Milestone |
|------|-----------|
| 2022 | Founded, YC W23 |
| Early 2024 | ~$1M ARR, fast growth among early adopters |
| Mid 2024 | Explosive viral growth, GPT-4 integration |
| Late 2024 | $100M+ ARR, $2.5B valuation (a16z, Thrive) |
| Early 2025 | ~$300M+ ARR, fastest-growing SaaS in history |
| Late 2025 | $1B+ ARR, $29.3B valuation |

### The Fork vs. Plugin Decision

**Fork when:**
- AI needs to change the **core interaction model** (editing, rendering, navigation)
- The upstream extension API is **too limited**
- You need to control **performance** end-to-end
- You're building a **product**, not a feature

**Plugin when:**
- AI is **additive** (chatbot, suggestion panel, linting)
- You're **testing demand** before committing
- **Distribution** matters more than UX depth

**For Buildable:** FreeCAD's addon system is far less mature than VS Code's extension API. The FreeCAD UI has significant UX gaps. AI-CAD integration needs to touch geometry creation, constraint solving, and 3D visualization deeply. **This strongly favors forking.** Your current approach is strategically sound.

### "Cursor for X" — What's Working

| Startup | Fork/Base | Outcome |
|---------|-----------|---------|
| **Cursor** | VS Code | $29.3B valuation |
| **Windsurf** | VS Code (different approach) | Acquired by Google ~$2.4B |
| **Brave** | Chromium | 93.8M MAU, $980M valuation |
| **Bolt.new / Lovable** | AI app builders | $25M+ ARR quickly |

**The pattern that works:** Fork a beloved open-source tool with a large user base but poor UX or missing AI capabilities. Add AI deeply (not superficially). Target power users first.

---

## 6. Why Ondsel Failed & How to Avoid It

### What Ondsel Was

Ondsel (founded ~2022, shut down November 2024) tried to commercialize FreeCAD. Founded by Brad Collette (longtime FreeCAD contributor), they raised a seed round and hired FreeCAD developers.

### Why They Failed

In their own words: *"Failed to find commercial adoption to justify a venture-capitalized startup"* and *"could not find product-market fit and ran out of runway."*

| Failure Mode | Detail |
|--------------|--------|
| **No differentiation from upstream** | Improvements were incremental — better defaults, polished UI. Users waited for upstream merges. |
| **Wrong business model** | Slightly-better-FreeCAD caught between "free" (FreeCAD) and "enterprise" (commercial CAD) |
| **Wrong target buyer** | FreeCAD users chose it *because* it's free. Converting them to paid was nearly impossible. |
| **Cloud collaboration wasn't enough** | Ondsel Lens competed with Onshape, GrabCAD — crowded space |
| **Gave everything upstream** | 145 PRs merged into FreeCAD, noble but undermined their business |

### Five Lessons for Buildable

**1. Don't just polish FreeCAD — fundamentally transform it.**
Ondsel's mistake was incremental improvement. Buildable's AI-first approach is a much stronger differentiator. You're not selling "better FreeCAD" — you're selling "natural language structural detailing."

**2. Target a different buyer.**
Ondsel tried to sell to existing FreeCAD users. Buildable should target people who **currently use AutoCAD** for precast detailing (and hate it), or who can't afford Tekla ($10K-20K/seat/year). You're expanding the market, not converting it.

**3. AI is the moat, not the distribution.**
Ondsel had no technical moat. Buildable's AI integration, precast element library, Eurocode knowledge, and source.py architecture are much harder to replicate.

**4. Keep your AI layer proprietary.**
Contribute bug fixes and UX improvements upstream (be a good citizen). But the AI assistant, precast library, and vertical-specific features are your competitive advantage. Don't give those away.

**5. Revenue must come from value-add, not the base CAD.**
Nobody will pay for "FreeCAD but slightly better." They will pay for "I described my foundation and got complete construction drawings in 10 minutes." The AI workflow is the product. FreeCAD is the engine.

---

## 7. Construction/Precast Market Deep Dive

### Why Construction Is Notoriously Hard to Sell To

| Challenge | Why It Matters |
|-----------|----------------|
| **Fragmentation** | 750K+ firms in the US alone, 90% have <20 employees. No single buyer controls the market. |
| **Low margins** | Typical 2-5% net margins. Every $500/month SaaS fee is scrutinized. |
| **Tech resistance** | "We've been doing it this way for 40 years." Change management is harder than almost any industry. |
| **Project-based** | Every project is one-off. Companies think in projects, not subscriptions. |
| **Connectivity** | Job sites lack reliable internet. Factories are better but still limited. |
| **Multi-party** | Owner, architect, GC, 20+ subcontractors, inspectors. No one party controls technology decisions. |

**61% of North American contractors** cite field worker acceptance as a top-three obstacle to new technology. More than half spend <2% of revenue on IT.

### What Works in Construction Tech Sales

**From Procore (gold standard, $1B+ ARR):**
- Made software **free for subcontractors and owners** (network effect: GC pays, subs get hooked)
- Invested ~30% of revenue in training and customer success
- Built for mobile from day one (field workers use iPads/phones)
- Became the "system of record" — once docs live in Procore, switching costs are enormous

**From PlanGrid (acquired by Autodesk for $875M):**
- Simple, specific use case: digital blueprints on iPad
- Founders went to job sites and **handed iPads to workers**
- So simple that training was almost unnecessary
- Viral: workers showed it to workers on other projects

**Key sales strategies:**
1. **Sell through pain, not features.** "How much does rework cost you per project?"
2. **Prove ROI on a single project.** Pilot on one element set. Show measurable time savings.
3. **Industry events are essential.** World of Concrete, Precast Show, BetonTage. Relationships form and deals start here.
4. **Referrals are king.** One peer recommendation > 100 cold emails.
5. **White-glove onboarding.** Construction companies won't read documentation. Hold their hand.

### The Precast Concrete Market

**Global market:** $143-155B in 2025, projected $178-261B by 2030-2035 (CAGR 4.5-5.7%)

**Digital adoption:**
- 58% of global precast manufacturers have adopted automation/robotics in production (2023)
- 67%+ now use BIM
- But the **design-to-production** workflow remains severely under-digitized

**The gap:** There is no dominant "Procore for precast" — no single platform connecting design/BIM, production, quality, logistics, and erection. Existing solutions are:
- Very expensive (Tekla at $10K-20K/seat/year, Allplan)
- Narrowly focused (only design OR only production planning)
- Tied to specific machinery vendors (Elematic)
- Generic and not precast-optimized (Revit, generic ERP)

### Key Characteristics Favoring Buildable

| Characteristic | Why It's Good for You |
|----------------|----------------------|
| **Countable buyer base** | ~300-500 PCI-certified plants in North America, similar in Europe. You can literally list every potential customer. |
| **Manufacturing-like retention** | Unlike project-based construction (churn when projects end), precast plants operate continuously. ~95%+ annual retention. |
| **Industry associations as channels** | PCI (US), BIBM (Europe), Georgian Precast Association (Nikoloz). Powerful distribution channels. |
| **BIM mandate tailwind** | Governments forcing digital adoption. Companies that avoided software now MUST adopt it. |
| **Repetitive, rules-based work** | Template-driven drawings, standardized detailing rules. Perfect for AI automation. |
| **High switching costs** | Once a company's element library is in Buildable, migration is extremely painful. |

---

## 8. Georgia as a Launchpad

### The Structural Advantage

| Factor | Georgia | San Francisco | Ratio |
|--------|---------|---------------|-------|
| Engineer salary | $1,500-3,000/mo | $15,000-25,000/mo | 5-10x cheaper |
| Office/living | ~$500-1,000/mo | $4,000-8,000/mo | 5-8x cheaper |
| $100K runway lasts | 12-18 months | 2-3 months | 5-6x longer |
| Monthly burn (3-person team) | $5,000-10,000 | $50,000-80,000 | 5-10x lower |

YC's $500K for 7% gives a Georgian team **2-4 years of runway** vs. 6-12 months for a US team. This is a massive structural advantage.

### Emerging Market Startups That Went Global

| Company | Origin | Outcome | Key Lesson |
|---------|--------|---------|------------|
| **GitLab** | Ukraine | IPO at ~$11B | Remote-first made origin irrelevant |
| **Grammarly** | Ukraine | 30M+ DAU, $13B val | Product so good geography doesn't matter |
| **UiPath** | Romania | IPO at $35B+ | Engineering in Romania, sales in the US |
| **JetBrains** | Czech/Russia | $500M+ revenue, bootstrapped | Build for developers globally, no VC needed |
| **dLocal** | Uruguay (3.4M pop!) | IPO at $9B | Almost exactly Georgia's population |
| **Pipedrive** | Estonia | Acquired for $1.5B | CRM built in Tallinn, sold globally |
| **Bolt** | Estonia | $8B+ valuation | Ride-hailing, started in tiny market |

### How They Overcame Geographic Disadvantage

1. **Dual structure** — Engineering in low-cost country, sales in target market
2. **Remote-first** — Made origin irrelevant (GitLab had no offices)
3. **Product-led growth** — Products that spread through adoption/word-of-mouth don't need expensive sales teams
4. **US/EU incorporation** — Solve legal/investor concerns from day one
5. **Solved a universal problem** — Not just a local issue

### The Beachhead Strategy for Buildable

**Phase 1 — Home Market as Lab (6-18 months):**
Georgia as testing ground. Local customers are accessible (visit their factory in 30 minutes). Iterate fast. Get case studies.

**Phase 2 — Adjacent Markets (12-24 months):**
Turkey is the key: 85M people, massive precast industry, geographic/cultural proximity, similar price sensitivity. Also: Azerbaijan, Central Asia.

**Phase 3 — Larger Markets (18-36 months):**
Middle East (Saudi Arabia's NEOM/Vision 2030, UAE), Eastern Europe. Use regional traction for credibility.

**Phase 4 — Global (36+ months):**
Western Europe (largest precast market), then US. May need local sales presence.

---

## 9. Go-to-Market & Pricing

### GTM Playbook

**Product-led growth is the right model** for an AI engineering tool:

1. **Free tier** — Let anyone download and use Buildable with limited AI interactions per day
2. **Viral demos** — 30-second video of "change all foundation rebar to Ø16" → everything regenerates. That video is worth more than any sales call.
3. **Design partners first** — First 3-5 customers get it free in exchange for feedback and case studies. Frame it as a partnership, not a discount.
4. **Industry events** — Precast Show, BetonTage, World of Concrete, local Georgian/Turkish construction events. One trade show booth > a year of cold emails.
5. **Move upmarket over time** — Makers/hobbyists → professional engineers → enterprises

### Pricing Strategy

**The core tension:** Georgian precast companies budget $500-5,000/year for software. US/European companies budget $20,000-100,000+. You can't anchor to either extreme.

**Two tiers, two buyers** (see [BUSINESS_MODEL.md](BUSINESS_MODEL.md) for full details):

- **Pro** — $400/month per company (up to 5 users). The engineer's tool. AI detailing, unlimited exports, full element library.
- **Enterprise** — $2,000-3,000/month per factory. The owner/CTO's platform. Includes the Buildable Portal (element library, templates, project dashboard, standards config, analytics).

**Why per company/per factory (not per seat):** Per-seat pricing discourages adoption — companies minimize licenses to save money. Per-factory pricing encourages everyone at a plant to use it, and correlates with value (more factories = more projects = more value).

**Phase 1 (0-10 customers, Georgia):**
Design partner approach. First 3-5 free, next 5-10 pay $200-300/month (regional pricing). You're learning, not optimizing revenue.

**Phase 2 (10-50 customers, regional expansion):**
Published Pro tier at $400/month. Regional discounts for Georgia/Turkey through direct sales (never published). First Enterprise pilots at $1,000-1,500/factory.

**Phase 3 (50+ customers, global):**
Full published pricing. Enterprise at $2,500-3,000+/factory. Annual contracts with 2-month discount for prepayment.

**Geographic pricing:** One public price (Western/US). Regional customers get non-public "partner discounts." Georgia $200-300/mo Pro, Turkey $300-400, Middle East $500-700, Europe/US $500-800. See [BUSINESS_MODEL.md](BUSINESS_MODEL.md) for full breakdown.

**Pricing Principles:**

1. **Never publicly anchor to a low price.** Raising prices later is nearly impossible.
2. **Price on value, not cost.** If you save $100K/year, charging $12K/year is a bargain.
3. **The 10x rule:** Product should deliver 10x its cost in savings.
4. **Don't compete on price.** Don't be "cheap Tekla." Be "purpose-built AI structural detailing."
5. **Annual contracts.** Construction companies plan in project cycles. Aligns with their planning.

### The ROI Story

**Current cost of drawing production in Georgia:**
- 2 engineers × 2 months × $1,500/month = **$6,000 per project**
- 5 projects/year = **$30,000/year on drawings**

**With Buildable (70% time savings):**
- Saves ~$21,000/year
- Charge $300-500/month ($3,600-6,000/year)
- **ROI: 3.5-5.8x** — easy sell

**For international markets:**
- Engineering salaries 3-5x higher ($4,000-8,000/month)
- Same time savings → $100K+ annual savings
- Charge $1,000-2,000/month → obvious ROI

---

## 10. The Buildable Playbook — Putting It All Together

### The Thesis (One Sentence)

**Precast structural detailing is a $150B industry where 60% of project time goes to repetitive, template-driven drawing work that AI can automate — and Buildable is the only company combining a mature open-source CAD kernel with deep AI integration to do it.**

### Why This Vertical, Why Now

| Factor | Evidence |
|--------|----------|
| **The work is AI-automatable** | Template-driven, rules-based, repetitive but requires domain expertise |
| **Pain is quantified** | 2 months design vs. 15 days construction — validated by one of Georgia's biggest precast companies |
| **Buyers exist and are reachable** | Countable buyer base (~300-500 plants per region), industry associations as channels |
| **Budget exists** | $30K/year on drawing production in Georgia, $100K+ internationally |
| **Technology is ready** | Claude/GPT-4+ era models handle code generation well, source.py architecture bridges CAD→code gap |
| **No incumbent owns this** | Tekla is expensive and doesn't automate; no dominant "precast AI" exists |
| **Expansion path is clear** | Precast → structural steel → general structural → "Cursor for CAD" |

### The Anti-Ondsel Strategy

| Ondsel's Mistake | Buildable's Approach |
|------------------|---------------------|
| Incremental FreeCAD improvement | AI-first transformation — fundamentally new capability |
| Targeted existing FreeCAD users | Target AutoCAD users in precast who hate manual work |
| No technical moat | AI integration, precast element library, Eurocode knowledge |
| Gave everything upstream | Keep AI layer proprietary, contribute base improvements |
| Cloud collaboration (crowded) | Drawing automation (uncontested) |
| General purpose | Vertical-specific (precast structural detailing) |

### The 12-Month Execution Plan

**Months 1-3: Prove the Wedge**
- Build Foundation F-1 end-to-end (3D + rebar + TechDraw + BBS)
- Record the 30-second demo video
- Demo to 5 precast company founders through Nikoloz
- Complete 10 customer discovery interviews
- Validate: "Would you use this on your next project?"

**Months 4-6: First Revenue**
- Expand element library (columns, beams, walls)
- Sign 3-5 design partners in Georgia (free or $100-300/month)
- Build change propagation (the killer feature: one parameter change → all drawings update)
- First case study with time savings data

**Months 7-9: Validate PMF**
- 10+ active users, at least 5 paying
- One company uses Buildable output on a real project
- Begin Turkey outreach (through construction industry contacts)
- Apply to YC or raise pre-seed ($200-500K)

**Months 10-12: Scale Signal**
- $2K-5K MRR
- DWG/PDF export (so output opens in AutoCAD)
- Regional pricing for Turkey/Azerbaijan
- Full 3-minute demo video for YouTube
- Industry event attendance (local, then regional)

### What Not To Do

1. **Don't build the general "Cursor for CAD" first.** The horizontal AI-CAD market is contested (Zoo, Adam, incumbents). Win the vertical first.
2. **Don't spend 6 months polishing the UI** before getting output in front of real engineers. The drawing quality matters more than the button layout.
3. **Don't try to replace AutoCAD.** Position as complementary: "Generate in Buildable, refine in AutoCAD if needed, export DWG."
4. **Don't fundraise before having paying customers.** Georgia's low burn rate is your superpower. Use it.
5. **Don't build a model-agnostic AI layer yet.** Claude Code works. Ship with it. Abstract later when you have revenue.
6. **Don't give talks about AI-CAD at conferences.** Give talks about precast detailing efficiency. Be the precast expert, not the AI expert.

### The Success Metrics

| Metric | 3 Months | 6 Months | 12 Months |
|--------|----------|----------|-----------|
| Customer conversations | 10+ | 20+ | 50+ |
| Active users | 3-5 | 10+ | 30+ |
| Paying customers | 0 | 3-5 | 10+ |
| MRR | $0 | $500-1,500 | $2,000-5,000 |
| Element types supported | 1 (foundations) | 4-5 | 7+ |
| Accuracy (drawings needing 0 corrections) | 60% | 80% | 90% |
| Countries with users | 1 | 1-2 | 3-4 |

### The Fundraising Narrative (When Ready)

> "One of Georgia's biggest precast companies told us something that stopped us in our tracks: their design and drawing phase takes **2 months**. Actual construction? **15 days.** They spend 4x longer on paper than on concrete — and the drawings are the same templates filled in with different parameters every single time.
>
> We built AI that generates those drawings in minutes. Describe your element — dimensions, rebar, concrete class — and Buildable produces complete construction drawings with correct Eurocode detailing, bar bending schedules, and material summaries. One parameter change? Everything regenerates in seconds, not days.
>
> We already have [X] paying customers in [Y] countries, saving them [Z] hours per project. We're raising to expand our element library and enter the Turkish and Middle Eastern markets, where precast is booming and construction companies are desperate for efficiency tools."

Lead with the **2 months vs. 15 days** — it's a visceral, unforgettable data point. Lead with Nikoloz's precast association as proof of commercial demand. Lead with the demo video.

Don't lead with "Cursor for CAD." Don't lead with the technology. Don't lead with TAM slide decks. Lead with the pain, the proof, and the product.

---

## Sources

### YC Startup Advice
- [YC's Essential Startup Advice](https://www.ycombinator.com/library/4D-yc-s-essential-startup-advice)
- [Lessons from 1,000+ YC Startups — Dalton Caldwell (Lenny's Newsletter)](https://www.lennysnewsletter.com/p/lessons-from-1000-yc-startups)
- [Co-founder Mistakes That Kill Companies — YC Library](https://www.ycombinator.com/library/DZ-co-founder-mistakes-that-kill-companies-and-how-to-avoid-them)
- [Do Things That Don't Scale — Paul Graham](https://paulgraham.com/ds.html)
- [Founder Mode — Paul Graham](https://www.paulgraham.com/foundermode.html)
- [Startup Playbook — Sam Altman](https://playbook.samaltman.com/)
- [What I Learned Going Through YC — Matthew Gunton (2026)](https://medium.com/@mgunton7/what-i-learned-going-through-y-combinator-614c76c24550)

### Vertical SaaS & AI Strategy
- [Ten Lessons from a Decade of Vertical Software Investing — Bessemer](https://www.bvp.com/atlas/ten-lessons-from-a-decade-of-vertical-software-investing)
- [Building Vertical AI: Playbook for Founders — Bessemer](https://www.bvp.com/atlas/building-vertical-ai-an-early-stage-playbook-for-founders)
- [Bessemer Vertical AI Book (Jan 2026 PDF)](https://www.bvp.com/assets/uploads/2026/01/BUILDING-VERTICAL-AI_PDF_BESSEMER_VENTURE_PARTNERS_BOOK_JANUARY_2026.pdf)
- [Roadmap: Built World AI — Bessemer](https://www.bvp.com/atlas/roadmap-built-world-ai)
- [The Vertical AI Playbook — Contrary Research](https://research.contrary.com/report/the-vertical-ai-playbook)
- [Vertical SaaS: Flipping the Playbook](https://medium.com/@cristina.castellan/vertical-saas-flipping-the-playbook-1bfbfbfaf108)
- [How to Build a Verticalized SaaS Business — Accion](https://www.accion.org/how-to-build-a-verticalized-saas-business-for-lasting-success/)
- [Go-To-Market: Find the Wedge — Nine Four Ventures](https://ninefour.vc/2019/08/07/go-to-market-find-the-wedge/)

### Cursor / AI-CAD
- [The Rise of Cursor — Michael Truell (Lenny's Newsletter)](https://www.lennysnewsletter.com/p/the-rise-of-cursor-michael-truell)
- [How Four MIT Students Built the Fastest-Growing Software Company Ever](https://aakashgupta.medium.com/how-four-mit-students-built-the-fastest-growing-software-company-ever-ca19441702a8)
- [How Cursor Grows — Aakash Gupta](https://www.news.aakashg.com/p/how-cursor-grows)
- [Anysphere Business Breakdown — Contrary Research](https://research.contrary.com/company/anysphere)
- [Paul Graham's Playbook for AI Startup Founders](https://charlesandsystems.substack.com/p/paul-grahams-playbook-for-ai-startup)

### Ondsel & FreeCAD
- [We Are Shutting Down Ondsel](https://www.ondsel.com/blog/goodbye/)
- [The End of Ondsel — Hackaday](https://hackaday.com/2024/11/12/the-end-of-ondsel-and-reflecting-on-the-commercial-prospects-for-freecad/)

### Construction Tech
- [Getting Ahead of Construction Tech Adoption — Procore](https://www.procore.com/jobsite/getting-ahead-of-construction-tech-adoption-challenges)
- [Precast Concrete Market Report — Grand View Research](https://www.grandviewresearch.com/industry-analysis/precast-concrete-market)
- [Precast Concrete Market Forecast — Mordor Intelligence](https://www.mordorintelligence.com/industry-reports/precast-concrete-market)
- [Precast Concrete Market — Future Market Insights](https://www.futuremarketinsights.com/reports/precast-concrete-market)

### AI Investment Trends
- [YC 2025 Agentic Landscape](https://artemerritt.medium.com/yc-2025-agentic-landscape-de5af758bd19)
- [The Moats of the Agentic AI Economy](https://medium.com/@sand.mayur/the-moats-of-the-agentic-ai-economy-609d2171a749)
- [The 3 AI Investment Trends VCs Are Chasing in 2026](https://analyticsweek.com/the-3-ai-investment-trends-vcs-are-chasing-in-2026-and-where-to-pitch-your-product/)
