---
name: technical-writing
description: Standardize the quality of written content in technical artifacts (plans, issues, fixes, reports, charters, PRs, enriched tickets). Use when a command produces a prose artifact that benefits from consistent problem framing, acceptance criteria, root cause descriptions, risk articulation, or increment goal definitions.
category: knowledge
version: 1.1.0
---

# Technical Writing

## PURPOSE

Teach the agent how to write clear, precise, and actionable content in technical artifacts. This skill provides reusable patterns for the most common writing tasks across artifact-producing commands. It is not a style guide for prose — it is a set of formulas and anti-patterns for technical communication.

---

## WHEN TO USE

Use this skill when producing content for any of these patterns:
- **Problem Framing** — Describing what is wrong or what needs to be built
- **Acceptance Criteria** — Defining verifiable conditions for "done"
- **Root Cause Description** — Explaining why something failed
- **Risk Articulation** — Expressing a risk so it is actionable
- **Increment Goals** — Defining what "done" looks like for a plan increment
- **Conciseness Rules** — Avoiding filler, redundancy, and vagueness

Commands that reference this skill: `/blueprint`, `/issue`, `/fix`, `/report`, `/charter`, `/enrich`, `/pr`.

---

## PATTERNS (Summary)

### 1. Problem Framing

**Formula:** Context → Impact → Current behavior vs Desired behavior.

One paragraph max. The reader should understand what is broken or missing, who is affected, and what "fixed" looks like — without reading anything else.

### 2. Acceptance Criteria

**Formula:** Given [precondition], When [action], Then [observable outcome].

Each criterion must be independently verifiable. No vague words ("should work correctly", "handles edge cases"). If it can't be tested, it's not a criterion.

### 3. Root Cause Description

**Formula:** Evidence → Mechanism → Consequence.

State what was observed (evidence), why it happened (mechanism), and what it caused (consequence). Never say "the issue was caused by a bug" — name the specific mechanism.

### 4. Risk Articulation

**Formula:** [What could happen] + [Likelihood: low/medium/high] + [Impact: low/medium/high] + [Mitigation or acceptance].

One sentence per risk. A risk without mitigation or explicit acceptance is incomplete.

### 5. Increment Goals

**Formula:** One sentence stating the verifiable outcome when the increment is done.

Must be: actionable (starts with a verb), verifiable (can confirm done/not done), and self-contained (no dependency on future increments).

### 6. Conciseness Rules

Remove: filler words ("basically", "essentially", "in order to"), passive voice when active is clearer, redundant qualifiers ("completely finished", "absolutely required"), hedging without purpose ("might possibly", "could potentially").

### 7. Collaborative Refinement Tone (v9.4+)

**When this pattern applies:** Any tracker-facing prose authored by `/enrich` (brief comment, `Refinement Notes`), and any artifact section that proposes changes to a teammate's ticket. Internal-only artifacts (`analysis.product.md`, plan files) MAY use a more direct evaluative tone since the audience is the implementer, not the ticket author.

**Posture:** The agent is a collaborator helping the team refine a shared ticket — never an evaluator grading the ticket's author. The output reads as a peer paraphrasing what they understood, proposing what could be added, and asking what is unclear. It MUST NOT read as a checklist of deficiencies.

**Required substitutions:**

| Replace evaluative | With collaborative |
|---|---|
| "missing X" / "X is missing" | "to confirm: X" or "we did not see X in the ticket — open question" |
| "incomplete" / "lacks Y" | "we propose to add Y as we infer it from <source>" |
| "needs Z" / "Z required" | "we infer Z; please confirm" |
| "the ticket fails to specify" | "we did not find a definition of" |
| "this is unclear" | "open clarification" |
| Listing dimensions as `[Missing]` / `[Incomplete]` | Listing dimensions as `What we already infer / propose to add` or `Open clarifications` |

**Required structure (when applied to `/enrich` brief comment):**

1. Opening paragraph — cordial, 1–2 sentences, summarizes the team's apparent intent in the agent's own words. NEVER addresses or names the ticket author. The reader is the whole team.
2. `### What's solid` — bullets the dimensions the ticket already covers well (acknowledging signal, not flattery).
3. `### What we already infer / propose to add` — bullets the dimensions the agent has filled in, each one attributing its inference to a source (chat context, parent epic, linked issue, design link). Each bullet ends with "please confirm" or "to validate".
4. `### Open clarifications` — bullets the items that need explicit human input. Phrased as questions, not as deficiencies.
5. `### Out of scope (declared)` — bullets what is NOT included in this task (sourced from the ticket itself or the agent's inference, each labeled by source).
6. `### Acceptance Criteria (consolidated)` — bullets the final AC list as proposed. Each item is a verifiable criterion per Pattern 2.
7. `### Next steps` — bullets the actions that need to happen next (e.g., "validate the user flow we proposed", "confirm out-of-scope items", "attach the design reference if available"). MUST NOT assign roles or individuals. The developer reading the comment tags whoever they think can help.

**Language invariant:** Output MUST be in English regardless of the chat conversation language. The brief lands in a shared tracker that mixes languages; English is the canonical tracker convention.

**FORBIDDEN content:**

- Greetings addressing the author by name or role ("Hi @PM", "Hello Product").
- Sign-offs attributing the comment to the agent or a person ("— AI", "— Rho AIAS").
- The Gap Summary table from `analysis.product.md` — that table is internal-only and stays local. Posting it externally reads as a scoreboard.
- Assigning Next-steps items to Product, UX, QA, or any role. The dev decides who to tag.
- Local filesystem paths, machine-specific references, or `Enhanced by` headers.

**Tone calibration:** when in doubt, ask: "Would I want a teammate to send me this exact text about my own ticket?" If the answer is no, rewrite using the substitutions above.

---

## REFERENCES

- `reference.md` — Detailed rules, anti-patterns, and checklists for each pattern
- `examples.md` — Before/after examples for each pattern
