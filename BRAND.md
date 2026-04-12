# Brand Identity

> **Rho AIAS** — *Rule-governed Human-Orchestrated* **A**gentic **I**nfrastructure for **A**rchitectural **S**tandards
>
> *The seven-layered shield of agentic development.*

**Rho AIAS** is the name of the rho-aias development architecture defined and maintained in this workspace. Use **AIAS** as the short form for paths, references, and everyday use.

The name draws from two sources:

1. **Rho Aias** (ῥώ αἴας) — the legendary seven-layered shield, a symbol of layered defense and structural integrity.
2. **The framework's own seven layers** — each one protecting the development process from ambiguity and context loss:

| Layer | Component | Purpose |
|---|---|---|
| 1 | **AGENTS.md** | Explicit project context |
| 2 | **Base Rules** | Universal agent behavior |
| 3 | **Modes** | Specialized reasoning stances |
| 4 | **Commands** | Deterministic execution |
| 5 | **Skills** | Reusable operational knowledge |
| 6 | **Contracts** | Architectural standards and governance |
| 7 | **Artifacts** | Verified, traceable outputs |

**Guiding principle**: *Architecture, not better prompts, is the solution.*

**Core identity**: Human-Governed · Context-Driven · Deterministic Workflows

> **Mission, Vision, Target Audience, and Value Proposition** have been extracted to [README.md](README.md) as the framework's public-facing front door. This file retains the brand identity, values, origin story, differentiators, tone, and visual identity.

# Values

Rho AIAS values are non-negotiable because each one is enforced by architecture, not slogans. The seven layers define the framework's structural defense; these five values define its operating posture in day-to-day execution.

1. **Context**  
   *Without context, there is no useful power.*  
   Context turns generic model capability into useful system behavior. Without explicit context, outputs may look strong but remain unreliable in real workflows.  
   Behavioral trace: AGENTS.md, structured prompts, artifact skill loading protocol, and task directories.

2. **Determinism**  
   *What does not repeat does not scale.*  
   Determinism removes ambiguity through explicit contracts, repeatable command behavior, and traceable artifacts. The objective is not rigidity for its own sake, but predictable quality under change.  
   Behavioral trace: contracts for commands, modes, rules, and skills; layered design with explicit boundaries.

3. **Governance**  
   *Without boundaries, there is no control.*  
   Governance defines when humans decide, approve, or redirect. It prevents silent autonomy drift and keeps responsibility clear at every handoff.  
   Behavioral trace: one mode per chat, explicit command contracts, and human-controlled handoffs.

4. **Transversality**  
   *One standard, any environment.*  
   Transversality keeps the framework portable across platforms, IDEs, and external services. The architecture must survive tool changes without losing operational consistency.  
   Behavioral trace: stack profiles, service abstraction layer, multi-tool shortcut generation, and portability contracts.

5. **Pragmatism**  
   *Less talk, more traceable delivery.*  
   Pragmatism prioritizes outcomes that teams can execute today while preserving traceability for tomorrow. It favors usable increments over framework theater.  
   Behavioral trace: artifact lifecycle, `status.md` tracking, and commands optimized for usable outputs.

Together, these values keep the framework honest: if a behavior cannot be traced to architecture through these principles, it is not considered part of the system.

# Origin Story

Rho AIAS started from friction, not from an ambition to create a framework. Early work with ChatGPT delivered useful ideas but unreliable execution loops: copy-paste overhead, context drift between sessions, and long conversations that still required manual reconstruction of intent. The model could help, but the surrounding workflow was unstable.

The turning point came with adopting Cursor in day-to-day engineering work. Local context and coding ergonomics improved, but a deeper issue remained: without explicit structure, even stronger tooling still produced inconsistent outcomes across tasks and chats. Good results depended too heavily on memory and prompting style.

That led to a practical decision: standardize behavior. Instead of writing "better prompts" every time, define reusable modes, command contracts, and artifact outputs that enforce consistency. Over roughly 2.5 months, this evolved organically from personal operating rules into a layered architecture with clear responsibilities and handoff mechanisms.

As the system matured, OpenSpec emerged as an important validation point. It confirmed that specification-first and artifact-driven approaches were not isolated ideas; they represented a broader direction in reliable AI-assisted software work. That external signal did not replace Rho AIAS identity, but it did validate the core thesis that disciplined structure outperforms improvisation.

Rho AIAS then took shape as its own product identity: Rule-governed Human-Orchestrated Agentic Infrastructure for Architectural Standards, symbolized by the seven-layer shield. The name reflects both technical intent and cultural grounding. The result is not a generic "AI productivity method" but a practitioner-built architecture for teams that need reliability, governance, and continuity.

# Differentiators

Rho AIAS is not positioned as "better than" other frameworks in absolute terms. It is differentiated by design choices that align with deterministic engineering workflows.

**Compared with OpenSpec**
- OpenSpec strongly validates spec-first thinking and structured development.
- Rho AIAS extends this posture with mode-specialized reasoning, explicit command contracts, and a seven-layer operational model spanning context, execution, and artifact governance.
- Rho AIAS also emphasizes workflow continuity across planning, implementation, PR, and closure with status tracking and synchronization behavior.

**Compared with BMAD**
- BMAD-style approaches can be effective for rapid agent orchestration and broad multi-agent collaboration.
- Rho AIAS is more opinionated about deterministic boundaries: one mode per chat, contract-defined commands, and strict artifact naming conventions plus skill loading protocols.
- The tradeoff is intentional: less free-form flexibility in exchange for lower ambiguity and higher repeatability.

**Compared with Kiro**
- Kiro-like systems often optimize for coding acceleration and interactive assistance in implementation loops.
- Rho AIAS gives stronger weight to governance and lifecycle integrity: plan classification, readiness gates, traceable artifacts, and explicit closure mechanics.
- This makes Rho AIAS especially useful where compliance, process consistency, or cross-team handoffs matter.

**Compared with Spec Kit and similar templates**
- Spec templates provide valuable structure at planning time.
- Rho AIAS treats structure as end-to-end operations, not only as documentation scaffolding: from analysis to execution to publication state.
- It combines reusable contracts with workflow state management so outputs remain actionable beyond initial planning.

In practice, these frameworks are complementary influences. Rho AIAS differentiates itself by integrating planning discipline, execution determinism, and operational traceability into one coherent architecture.

# Tone and Voice

Rho AIAS communicates like a senior engineer explaining a system tested in real work, not like a brand campaign.

**Tone principles**
- **Technically precise**: use concrete terms (contracts, artifacts, transitions, failure modes) instead of broad claims.
- **Honest about limitations**: state tradeoffs clearly (e.g., structure adds overhead but improves reliability).
- **Practical and implementation-first**: favor workflows, examples, and operational guidance over abstract theory.
- **Respectful and factual**: compare alternatives without dismissive language.
- **Human and grounded**: retain the practitioner voice and cultural context of the name without reducing either to decoration.

**Writing guidance for consistent outputs**
- For README intros: lead with the problem (AI inconsistency), then the thesis (architecture over prompts), then the concrete mechanism (layers, contracts, artifacts).
- For docs: prioritize "how it works" and "when to use it," with explicit inputs/outputs and failure boundaries.
- For talk abstracts: frame the journey from ad hoc AI usage to deterministic workflows, with measurable operational benefits.

**Style guardrails**
- Avoid startup superlatives ("revolutionary," "game-changing") unless backed by evidence.
- Avoid generic productivity language detached from architecture.
- SHOULD use short, declarative statements that map directly to observable framework behavior.

If a statement cannot be tied to an implemented behavior in the system, rewrite it or remove it. Consistency of voice follows from consistency of truth.

# Visual Identity

## Design Intent

The visual identity of Rho AIAS translates the framework's verbal identity — seven architectural layers, structural defense, practitioner-first precision — into a coherent visual system.

- The **seven-petaled rosette** (shield + bloom) is derived from Rho Aias as depicted in Fate/Stay Night: a luminous, geometric, layered barrier that radiates outward from a center point.
- The **color palette** draws from jacaranda blooms — vivid violets and blues that are structural, not decorative — the way Mexico's jacaranda canopies filter light through layered petals.
- The **typographic discipline** carries the weight and precision of Tite Kubo's aphoristic style in Bleach: bold, clean, high-contrast, with generous negative space. Text functions as architecture, not ornament.
- Every visual decision maps to a brand value or architectural layer. If a visual element is purely decorative, it does not belong.
- The system is designed for documentation, IDE themes, terminal-adjacent contexts, and engineering presentations — not marketing collateral.
- All specifications are directly applicable by developers without design expertise.

## Visual Identity Principles

1. **Structure over decoration** — Every visual element maps to an architectural concept. Ornament without structural meaning is excluded. *(Values: Determinism, Pragmatism)*
2. **Layered by design** — The seven-layer shield is the organizing principle for visual hierarchy, color depth, and logo construction. *(Values: Context, Governance)*
3. **Luminous precision** — Colors and forms evoke light filtered through structure: translucent, clean, geometrically constrained — not soft or ambient. *(Reference: Fate/Stay Night Rho Aias barrier aesthetic)*
4. **Text as architecture** — Typography carries structural weight. Headings stand alone as statements. Negative space is intentional, not residual. *(Reference: Bleach chapter title pages, value motto style)*
5. **Environment adaptability** — Every color, mark, and type choice must function in both light and dark modes without loss of legibility or identity. *(Value: Transversality)*
6. **Practitioner-first simplicity** — Specs are directly applicable by engineers in markdown, code, and presentations. No interpretation layer required. *(Value: Pragmatism)*

## Logo System

### Primary Logo (Symbol + Wordmark)

**Symbol**: A seven-petaled radial rosette. Each petal is an elongated, pointed oval (vesica-piscis derived), evenly spaced around a central point at approximately 51.4° intervals, radiating outward to form a symmetrical structure that reads simultaneously as a shield and a bloom. Each petal carries a subtle internal gradient suggesting translucency — lighter at the outer edges, deeper violet at the core. The overall silhouette inscribes a circle.

**Wordmark**: "Rho AIAS" set in Inter (or equivalent geometric sans-serif). "Rho" in mixed case, "AIAS" in all-caps. Letter-spacing is generous (+2–4% tracking) to carry the negative-space discipline of the typographic system.

**Composition**: Symbol to the left, wordmark to the right, vertically centered. Minimum clear space: 1× the symbol radius on all sides. Overall aspect ratio (symbol + wordmark): approximately 3:1 horizontal.

### Symbol-Only Variant

For favicons, badges, social profile images, and constrained contexts:

- Use the seven-petaled rosette alone.
- Minimum legible size: 24×24px.
- At sizes below 32px, collapse inner petal gradients to solid fills to preserve readability.

### Monochrome Variants

| Context | Symbol + Wordmark Color | Background |
|---|---|---|
| Dark-on-light | `rho-violet-900` (#2D1B4E) | White or light surfaces |
| Light-on-dark | `rho-violet-100` (#EDE5F4) | Dark surfaces |
| Single-color fallback | Pure white or pure black | When color reproduction is unavailable |

### AI Generation / Designer Brief

> A geometric seven-petaled rosette mark. Each petal is an elongated, pointed oval shape (vesica piscis), evenly spaced around a central point at approximately 51.4° intervals, radiating outward to form a symmetrical flower-shield pattern. The overall silhouette is circular. Petals have a subtle internal gradient suggesting translucency — lighter at the edges, deeper violet (#6B3FA0) at the core. The style is minimal, precise, and architectural — not organic or hand-drawn. Lines are clean and uniform in weight. The aesthetic references a luminous energy barrier rendered as a botanical rosette. No text in the symbol. Background: transparent. Color palette: deep violet to blue-violet gradient within petals. Flat design, no shadows, no 3D effects.

### Rationale Mapping

| Logo Feature | Origin Reference | Architectural Layer |
|---|---|---|
| Seven petals | Fate/Stay Night Rho Aias (seven-layer barrier) | All 7 layers (AGENTS.md through Artifacts) |
| Radial symmetry | Shield geometry — defense radiates from center | Core architecture radiating to outputs |
| Pointed oval petals | Vesica piscis — intersection of two circles | Overlap: human governance and agent execution |
| Violet-blue palette | Jacaranda blooms filtering light | Structural color — vivid, not decorative |
| Translucency gradient | Rho Aias energy barrier luminosity | Layered transparency — each layer visible through the next |
| Clean geometry | Engineering precision | Determinism and repeatability values |

## Color System

### Core Palette

| Token | Role | Hex | RGB | Usage Context | Light Mode | Dark Mode | Accessibility |
|---|---|---|---|---|---|---|---|
| `rho-violet-900` | Primary (deepest) | `#2D1B4E` | 45, 27, 78 | Headings, primary text on light | Primary text color | — | AA on white (14.5:1) |
| `rho-violet-700` | Primary (standard) | `#5B2D8E` | 91, 45, 142 | Brand accents, active states | Links, emphasis | — | AA on white (7.2:1) |
| `rho-violet-500` | Primary (vivid) | `#6B3FA0` | 107, 63, 160 | Logo fill, key UI accents | Interactive elements | Primary accent | AA-large on white (4.8:1); AA on dark-950 (5.1:1) |
| `rho-violet-300` | Secondary (light) | `#B088D4` | 176, 136, 212 | Highlights, borders | Decorative only | Secondary text, borders | Not for text on light backgrounds |
| `rho-violet-100` | Secondary (lightest) | `#EDE5F4` | 237, 229, 244 | Backgrounds, cards | Card/section backgrounds | Text on dark (13.8:1 on dark-950) | AA on dark backgrounds |
| `rho-blue-600` | Accent | `#3A6BC5` | 58, 107, 197 | Secondary actions, links | Accent interactive | Accent interactive | AA on white (4.6:1); AA-large compliant |
| `rho-blue-400` | Accent (light) | `#7BA3E0` | 123, 163, 224 | Hover states, secondary | — | Secondary accent | Decorative use only on light |
| `rho-dark-950` | Neutral (darkest) | `#1A1A2E` | 26, 26, 46 | Dark mode backgrounds | — | Primary background | Base dark surface |
| `rho-dark-800` | Neutral (dark) | `#2A2A40` | 42, 42, 64 | Dark mode cards/sections | — | Elevated surfaces | — |
| `rho-light-50` | Neutral (lightest) | `#FAFAFA` | 250, 250, 250 | Light mode backgrounds | Primary background | — | Base light surface |
| `rho-light-200` | Neutral (light) | `#E8E8EC` | 232, 232, 236 | Borders, dividers | Subtle dividers | — | — |

### Semantic Palette

| Token | Role | Hex | RGB | Light Mode | Dark Mode Adjustment |
|---|---|---|---|---|---|
| `rho-success` | Success | `#2E7D4F` | 46, 125, 79 | On white | Lighten to `#4CAF7A` |
| `rho-warning` | Warning | `#C47F17` | 196, 127, 23 | On white | Lighten to `#E0A33C` |
| `rho-error` | Error | `#B33A3A` | 179, 58, 58 | On white | Lighten to `#D46A6A` |
| `rho-info` | Info | `#3A6BC5` | 58, 107, 197 | Shared with `rho-blue-600` | Shared with `rho-blue-600` |

### Contrast Guidance

- **Body text**: `rho-violet-900` on `rho-light-50` (14.5:1) or `rho-violet-100` on `rho-dark-950` (13.8:1).
- **Headings**: `rho-violet-900` or `rho-violet-700` on light surfaces; `rho-violet-100` on dark surfaces.
- **Interactive elements**: `rho-violet-500` or `rho-blue-600` — verify AA or AA-large compliance against the target surface.
- **Never** place `rho-violet-300` or `rho-blue-400` as text on light backgrounds (insufficient contrast).

## Typography System

### Typeface Selection

| Role | Typeface | License | Rationale |
|---|---|---|---|
| Primary (sans-serif) | **Inter** | Open-source (SIL OFL) | Geometric sans-serif optimized for screen readability; excellent at small sizes; widely available |
| Secondary (monospace) | **JetBrains Mono** | Open-source (SIL OFL) | Designed for code; ligature-supported; complements Inter's x-height and rhythm |

### Fallback Stacks

- **Sans-serif**: `'Inter', 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif`
- **Monospace**: `'JetBrains Mono', 'SF Mono', 'Fira Code', 'Cascadia Code', monospace`

### Typography Scale

| Text Role | Typeface | Weight | Size Range | Line Height | Use Case |
|---|---|---|---|---|---|
| Display / Hero | Inter | 700 (Bold) | 32–48px | 1.1–1.2 | Brand statements, value mottos, landing hero |
| H1 | Inter | 700 (Bold) | 24–32px | 1.2–1.3 | Page titles, section headings |
| H2 | Inter | 600 (SemiBold) | 20–24px | 1.25–1.35 | Subsection headings |
| H3 | Inter | 600 (SemiBold) | 16–20px | 1.3–1.4 | Minor headings, card titles |
| Body | Inter | 400 (Regular) | 14–16px | 1.5–1.6 | Paragraph text, documentation |
| Body emphasis | Inter | 500 (Medium) | 14–16px | 1.5–1.6 | Inline emphasis, key terms |
| Caption | Inter | 400 (Regular) | 12–13px | 1.4–1.5 | Metadata, footnotes, table labels |
| Code inline | JetBrains Mono | 400 (Regular) | 13–14px | 1.4–1.5 | Inline code references |
| Code block | JetBrains Mono | 400 (Regular) | 13–14px | 1.5–1.6 | Code snippets, terminal output |
| Value motto | Inter | 700 (Bold) | 18–24px | 1.2–1.3 | Brand value statements (aphoristic style) |

### Weight Rules

- **Bold (700)**: Headings, brand statements, and value mottos only. Weight signals hierarchy.
- **SemiBold (600)**: Secondary headings.
- **Medium (500)**: Inline emphasis within body text.
- **Regular (400)**: All body content and code.
- **Light/Thin (300/100)**: Never used. These compromise readability in technical contexts and violate the high-contrast discipline.

### Code-Adjacent Compatibility

- JetBrains Mono and Inter share compatible x-height and rhythm at equivalent sizes.
- Both are open-source and available via Google Fonts, system packages, or direct download.
- For slides and print: substitute Inter with SF Pro Display (Apple) or Segoe UI (Microsoft) as system fallbacks.

## Usage Guidelines

### Logo

**Do**:
- Use the primary logo (symbol + wordmark) in README headers and documentation landing pages.
- Use the symbol-only variant for favicons, badges, and social profile images.
- Maintain minimum clear space (1× symbol radius) around the logo.
- Use monochrome variants when color reproduction is unavailable.

**Don't**:
- Stretch, rotate, or skew the logo.
- Place the logo on busy or low-contrast backgrounds without a solid container.
- Recreate the logo with alternative typefaces or petal counts.
- Add shadows, glows, or 3D effects.

### Color

**Do**:
- Use the violet palette as the dominant brand color across all surfaces.
- Use the blue accent sparingly — for interactive elements and secondary emphasis only.
- Verify contrast ratios (minimum WCAG AA) for all text-on-background combinations.
- Use semantic colors exclusively for status and feedback states.

**Don't**:
- Use `rho-violet-300` or `rho-blue-400` as text color on light backgrounds.
- Introduce colors outside the defined palette without extending the token system.
- Use gradients as background fills in documentation — reserve gradients for the logo mark only.

### Typography

**Do**:
- Use Inter for all non-code text in documentation, slides, and web.
- Use JetBrains Mono for all code blocks, inline code, and terminal references.
- Apply the weight hierarchy consistently: Bold for headings, Regular for body.
- Give value mottos the display treatment — they stand alone with generous whitespace.

**Don't**:
- Mix more than two typeface families in a single context.
- Use decorative or serif typefaces — they conflict with the architectural tone.
- Set body text below 14px or code text below 13px.
- Apply all-caps to body text — reserve for short labels and the "AIAS" portion of the wordmark.
