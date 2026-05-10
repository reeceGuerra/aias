# Incremental Decomposition — Pattern Reference

Detailed rules, boundary heuristics, sizing guidance, anti-patterns, and checklists.

---

## 1. Self-Containment

### Rules

- After completing any single increment, the project MUST build without errors.
- After completing any single increment, the feature delivered by that increment MUST be testable (manual or automated).
- No increment may leave the codebase in a "half-wired" state (e.g., a protocol declared but not implemented, a route registered but pointing to an empty screen).
- If an increment introduces a new dependency (SPM package, module), that same increment must include the minimal integration (import, DI registration) needed for the dependency to be usable.

### Verification Question

> "If this increment is the last one the developer completes, is the system in a valid state?"

If the answer is no, the increment is not self-contained. Merge it with the next one or restructure.

---

## 2. Boundary Criteria

### Where to Cut

| Boundary type | Description | Example |
|---|---|---|
| **Vertical feature slice** | A thin end-to-end path through the stack (data → logic → UI) for one user action | "User can search positions by keyword" (API call + ViewModel + UI) |
| **Module boundary** | A self-contained module or package that can be built independently | "Add `RDSAnalytics` package with event tracking protocol" |
| **Data flow endpoint** | A complete data path from source to consumption | "Fetch and cache candidate list from API" |
| **User-visible outcome** | A change the user can see or interact with | "Display empty state when no results match the filter" |

### Where NOT to Cut

| Anti-pattern | Why it's wrong | Fix |
|---|---|---|
| **Horizontal layer split** — "Create the protocol" then "Implement the protocol" | Protocol without implementation is dead code; violates self-containment | Merge into one increment: "Create and implement X protocol" |
| **Setup increment** — "Configure DI and add imports" | Setup without usage delivers no value | Merge setup into the first increment that uses it |
| **Scaffold increment** — "Create empty files and folder structure" | Scaffolding alone is not testable or valuable | Include scaffolding in the first increment that populates it |
| **Mid-flow split** — "Add the API call" then "Handle the response" | An API call without response handling is incomplete | One increment: "Fetch and handle X from API" |

### Heuristic

Ask: "Can I demo this increment to someone?" If yes, it's a good boundary. If you need to say "well, it doesn't do anything visible yet, but..." — merge it.

---

## 3. Ordering

### Rules

- Order by dependency: if Increment B uses something created in Increment A, A comes first.
- If two increments are independent (no shared dependency), note they can be **parallelized**.
- Foundation first: data models, protocols, and service interfaces before UI that consumes them — but always as a vertical slice, not as a layer.
- Never order by file type (e.g., "all models first, then all views"). Order by feature slice.

### Dependency Notation

When listing increments, mark dependencies explicitly:

```
Increment 1: Create candidate search API service (standalone)
Increment 2: Add search UI with ViewModel (depends on: 1)
Increment 3: Add filter persistence (depends on: 2)
Increment 4: Add analytics tracking (independent, parallelizable with 2–3)
```

---

## 4. Sizing

### Rules

- No fixed size rule (no "40–60%" or "max N files" formula).
- Size is driven by **coherence**: one increment = one complete thing.
- A 1-file increment is valid if it delivers a complete, verifiable change (e.g., a bug fix, a configuration change).
- A 15-file increment is valid if all files serve the same coherent goal and removing any file would break the increment.

### Sizing Signals

| Signal | Interpretation |
|---|---|
| Increment touches 3+ unrelated modules | Too big — likely multiple increments bundled |
| Increment goal needs "and" to describe | Too big — split at the "and" |
| Increment has 1 step | Possibly too small — check if it's self-contained and valuable |
| Increment takes >1 sentence to explain the goal | Too complex — SHOULD split |

### When in Doubt

Prefer slightly larger increments over artificially small ones. A self-contained increment with 8 files is better than 3 increments of 2-3 files where none works alone.

---

## 5. Naming and Goals

### Naming

- Short, descriptive, action-oriented: "Add candidate search", "Refactor token refresh", "Fix filter reset on back navigation."
- Avoid generic names: "Phase 1", "Initial setup", "Miscellaneous changes."
- The name should tell the developer what the codebase looks like AFTER the increment.

### Goals

- One sentence stating the verifiable outcome.
- Starts with a verb (Add, Implement, Replace, Refactor, Remove, Migrate, Fix).
- Includes how to verify: "verified by unit test passing" or "verified by X screen rendering correctly."

### Formula

**[Verb] [what changes] [where]; verified by [how to confirm done].**

---

## 6. Improvement Margin

### Rules

- Optional items that enhance quality but do not block "done" for any increment.
- Typical items: extra test coverage, minor refactors, UX polish, documentation updates, accessibility improvements.
- Listed separately from core increments (in a dedicated section or subsection).
- If there are no optional improvements, state "None" explicitly.

### Anti-Pattern

Mixing optional items into core increment steps. This inflates scope and makes it unclear what's required vs nice-to-have.

---

## 7. Estimation Alignment (for `/charter`)

When estimating increments in a delivery charter:

- Estimate each increment independently.
- Use relative sizing: S / M / L / XL.
- Assess complexity (Low / Med / High) based on unknowns, integration points, and edge cases — not file count.
- Confidence (High / Med / Low) reflects how well-understood the increment is. Low confidence = the increment may need re-scoping after discovery.
- If one increment has Low confidence and High complexity, flag it as a risk.

---

## Checklists

### Decomposition Checklist (when creating increments)

- [ ] Every increment is self-contained (builds, testable, delivers value)?
- [ ] No increment cuts mid-abstraction (protocol without implementation, API call without handler)?
- [ ] Increments are ordered by dependency?
- [ ] Parallelizable increments are noted?
- [ ] Each increment has a descriptive name and a one-sentence verifiable goal?
- [ ] No "setup only" or "scaffold only" increments?
- [ ] Improvement margin items are separated from core increments?

### Execution Checklist (when consuming increments)

- [ ] Executing increments in the defined order?
- [ ] Not combining multiple increments into one execution step?
- [ ] Verifying each increment's goal before proceeding?
- [ ] Updating plan status after each increment?
