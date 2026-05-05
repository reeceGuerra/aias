---
name: technical-writing
description: Standardize the quality of written content in technical artifacts (plans, issues, fixes, reports, charters, PRs, enriched tickets). Use when a command produces a prose artifact that benefits from consistent problem framing, acceptance criteria, root cause descriptions, risk articulation, or increment goal definitions.
category: knowledge
version: 1.0.0
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

---

## REFERENCES

- `reference.md` — Detailed rules, anti-patterns, and checklists for each pattern
- `examples.md` — Before/after examples for each pattern
