---
name: incremental-decomposition
description: Standardize how work is broken into self-contained, shippable increments. Use when a command produces, consumes, estimates, or executes increments — ensuring consistent decomposition criteria across the planning-to-implementation pipeline.
category: knowledge
version: 1.0.0
---

# Incremental Decomposition

## PURPOSE

Teach the agent a single, canonical set of rules for breaking work into increments. Without this skill, decomposition criteria are scattered across `/blueprint`, `/charter`, `/implement`, and `/enrich`, leading to inconsistent increment quality depending on which artifact performs the split.

---

## WHEN TO USE

Use this skill when:
- **Creating increments** — `/blueprint` (Category 7, including structured plan output)
- **Estimating increments** — `/charter` (effort estimation per increment)
- **Executing increments** — `/implement` (one-at-a-time execution)
- **Enriching tickets with increments** — `/enrich` (when generating acceptance criteria or file impact)

Commands that reference this skill: `/blueprint`, `/charter`, `/implement`, `/enrich`.

---

## CORE RULES (Summary)

### 1. Self-Containment

Every increment MUST be self-contained: it builds, it's testable, and it delivers a clear slice of value. If the developer stops after any increment, the system is in a valid, shippable state.

### 2. Boundary Criteria

Cut increments at **natural boundaries**: a feature slice (vertical, not horizontal), a module boundary, a data flow endpoint, or a user-visible outcome. Never cut mid-abstraction (e.g., "create the protocol" in one increment and "implement the protocol" in another).

### 3. Ordering

Order increments by dependency: foundational work first, then layers that depend on it. If two increments have no dependency, note they can be parallelized.

### 4. Sizing

No fixed size rule. Each increment must be coherent and shippable. A single-file change can be an increment; a 10-file change can be an increment — what matters is that it delivers one complete thing.

### 5. Naming and Goals

Each increment has a **name** (short, descriptive) and a **goal** (one sentence: what "done" looks like). The goal must be verifiable.

### 6. Improvement Margin

Optional improvements (extra tests, refactors, UX polish) go in an **Improvement Margin** section. They must NOT block "done" for any increment.

---

## REFERENCES

- `reference.md` — Detailed rules, boundary heuristics, sizing guidance, anti-patterns, and checklists
- `examples.md` — Before/after examples of good and bad decompositions
