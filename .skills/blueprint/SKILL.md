---
name: blueprint
description: "Collects and structures all data required for an implementation plan into TASK_DIR artifacts. Use after @planning reasoning to produce technical.plan.md, increments.plan.md, dod.plan.md, and dor.plan.md. Trigger terms: /blueprint, blueprint plan, create plan, structure plan."
category: operative
disable-model-invocation: true
version: 5.4.0
---

# Blueprint (Plan Data Collection + Structuring) — v5.4

## 1. Identity

**Command Type:** Operative — Procedural / Execution

You are guiding the **systematic collection and structuring** of all data required for an implementation plan. This command consumes DoR/DoD artifacts from refinement (`/enrich`), collects raw planning data from codebase analysis and context, structures it into artifacts, and writes them to the task directory. On the first execution for a task, it triggers the canonical tracker transition `ready` -> `in_progress`.

**Skills referenced:** `rho-aias`, `technical-writing`, `incremental-decomposition`.

---

## 2. Invocation / Usage

Invocation:
- `/blueprint`
- `/blueprint TASK-ID` — enrich with tracker data when the task id maps to a tracker ticket (also sets TASK_DIR)
- `/blueprint DESIGN-URL` — enrich with design context
- `/blueprint TASK-ID DESIGN-URL` — enrich with both
- `/blueprint --fast` — skip Comprehension and Checkpoint gates (combinable with other arguments)

Usage notes:
- Best used with `@planning` mode active for reasoning quality.
- Can be invoked standalone when required service configs are available and resolvable.
- Output is written directly to the task directory as separate artifact files.
- `--fast` suppresses the Comprehension and Checkpoint gates (Phase 0). The Preview gate always fires. All 7 categories are still collected. Use for trivial or well-understood tasks where validation gates add friction without value.
- If TASK_DIR is set (via Structured Prompt or task id), writes to that directory. If not, creates a new directory from the task id or an agent-chosen name.
- In the Structured Prompt, SHOULD prefer `TASK ID` / `TASK DIR` (or `DIR`) over legacy `TICKET`.
- **Strict mode:** DoR/DoD artifacts (`dor.plan.md`, `dod.plan.md`) must exist in TASK_DIR before planning can proceed, except when the bug exception applies (see Phase 0).

---

## 3. Inputs

This command may use **only** the following inputs:
- Chat context explicitly provided by the user
- Output from `@planning` mode reasoning (if active)
- Tracker data (via resolved tracker provider, if a task id / tracker ticket URL is provided)
- Design context (via resolved design provider, if design URL provided)
- Codebase analysis results (files, patterns, dependencies found during analysis)
- **Upstream artifacts** detected in TASK_DIR:
  - `dor.plan.md` — Definition of Ready (REQUIRED, except bug exception)
  - `dod.plan.md` — Definition of Done (REQUIRED, except bug exception)
  - `analysis.product.md` — product analysis
  - `*.fix.md`, `*.issue.md`, `*.assessment.md` — bug flow artifacts (for bug exception)
- Service configs:
  - `aias-config/providers/tracker-config.md`
  - `aias-config/providers/design-config.md`
  - `aias-config/providers/knowledge-config.md`

Context enrichment requirements:
- If tracker data is not already in context and a task id or tracker URL was provided, resolve tracker provider from `aias-config/providers/tracker-config.md`; if missing/invalid/unresolvable, abort and request provider configuration.
- If design context is not already available and a design URL was provided, resolve design provider from `aias-config/providers/design-config.md`; if missing/invalid/unresolvable, abort and request provider configuration.
- If knowledge provider config is missing/invalid/unresolvable, abort before Phase 5c.

Rules:
- All inputs must be explicit.
- If critical information is missing, fire an AskQuestion gate before proceeding (see `@planning` INTERACTIVE QUESTIONING for priority rules). When `AskQuestion` is unavailable, use the Text Gate Protocol from `readme-commands.md`.

---

## 4. Output Contract (Format)

### Directory Resolution

Follow the **rho-aias** skill loading protocol Phase 0:
- If TASK_DIR exists → use it.
- If TASK_DIR does not exist → create <resolved_tasks_dir>/<TASK_ID>/ where TASK_ID is the canonical task identifier (often equal to the tracker ticket key, when one exists) or an agent-chosen kebab-case name. (Default: `~/.cursor/plans/`)
- Create `status.md` if it does not exist using the canonical format from `aias/.skills/rho-aias/reference.md` § `status.md` Format. Initialize `profile` from context (default: `feature`), `task_id: <TASK_ID>`, `started: <YYYY-MM-DD>`, `status: pending_dor`, and `current_step: blueprint`; keep all remaining fields at canonical defaults (`classification: null`, `refinement_validated: null`, `rhoaias_update: null`, `published: null`, `completed: null`, `tracker_status: null`, `completed_steps: []`, `artifacts: {}`, `command_log: []`).

### Gate: Preview

**Type:** Confirmation
**Fires:** Phase 3, before writing artifacts to TASK_DIR.
**Skippable:** No (always fires, including with `--fast`).

**Context output:**
Present a compact summary in chat:
- Task ID and profile
- One-line overview of the plan
- Increment count and names
- List of artifacts to be written
- Target directory path
- Assigned classification (Minor/Standard/Critical)
- Proposed DoR/DoD amendments (if any)

**AskQuestion:**
- **Runtime compatibility:** If `AskQuestion` is unavailable, use the Text Gate Protocol from `readme-commands.md` with the same prompt, option ids, labels, and `allow_multiple` semantics.
- **Prompt:** "Plan ready. <count> increments, classification <minor|standard|critical>. Write artifacts to <TASK_DIR>?"
- **Options:**
  - `write`: "Write artifacts to TASK_DIR and continue"
  - `adjust`: "Adjust the plan before writing"
- **allow_multiple:** false

**On response:**
- `write` → Write artifacts to TASK_DIR, proceed to End-of-Response Confirmation
- `adjust` → Apply corrections, return to context output and re-present gate

**Anti-bypass:** Inherits Gate Invocation Protocol. No additional rules.

### File Output

Write the following artifacts to TASK_DIR:

| Artifact | Content |
|----------|---------|
| `technical.plan.md` | Problem framing, architectural approach, file structure, visualization, `## Proposed DoR Amendments` (only when DoR gaps exist, inline-confirmed or unresolved), `## Proposed DoD Amendments` (only when DoD gaps exist, inline-confirmed or unresolved). Legacy combined section `## Proposed DoR/DoD Amendments` is FORBIDDEN since v9.5. |
| `increments.plan.md` | Cursor-first `.plan.md` artifact with frontmatter `name`, `overview`, `todos`, `isProject`, plus body content for increments, goals, steps, improvement margin, self-review, testing |
| `specs.design.md` | Design specification. Generated when **either** a design URL is provided (full extraction via resolved design provider) **or** the DoR declares `orientation: user_facing` even without a design URL (minimal specs derived from DoR + chat context; see Category 6 conditions). |
| `dor.plan.md` | **Bug exception only:** Generated when bug flow artifacts exist but no DoR/DoD from `/enrich` |
| `dod.plan.md` | **Bug exception only:** Generated when bug flow artifacts exist but no DoR/DoD from `/enrich` |

### End-of-Response Confirmation

After writing all artifacts, print:
```
Artifacts written to: <absolute_path_to_TASK_DIR>/
  - technical.plan.md
  - increments.plan.md
  [- specs.design.md]
  [- dor.plan.md (bug exception)]
  [- dod.plan.md (bug exception)]
RHOAIAS.md impact: <detected (reason) | none | skipped (placeholders/missing)>
```

### Status Update (Phase 5)

After writing artifacts:
1. Update `status.md`: add each artifact to the `artifacts` map with status `created` (new) or `modified` (overwrite).
2. **Assign Plan Classification**: set `classification` in `status.md` to `minor`, `standard`, or `critical` based on scope, impact, and complexity. See `SKILL.md` Plan Classification for criteria.
3. **RHOAIAS Impact Analysis**: evaluate whether the planned work will require a `RHOAIAS.md` update. See § RHOAIAS Impact Analysis below.
4. Add `blueprint` to `completed_steps`, set `current_step` to `validate`.
5. Append to `command_log`: `{command: /blueprint, started_at: <UTC>, ended_at: <UTC>}` — obtain timestamps via `date -u +%Y-%m-%dT%H:%M:%SZ`. See `reference.md` § Command Log for full rules.
6. Run Phase 5c: sync non-synced artifacts to resolved knowledge provider. Phase 5c fires only when a valid tracker ticket exists for TASK_ID (P1–P3 preconditions; see **rho-aias** skill § Phase 5c). If preconditions are not met, skip silently — artifacts remain in created/modified state for `/publish` to reconcile. When the bug exception generated `dor.plan.md` and `dod.plan.md`, Phase 5c publishes them automatically alongside `technical.plan.md` and `increments.plan.md` when preconditions are met. After each successful publish, inject TOC per resolved provider config.

### TRACKER SYNC (Phase 6 — on start)

- When `task_id` in `status.md` is valid for the resolved tracker provider AND DoR/DoD are verified (exist or bug exception applies):
  1. Resolve tracker provider from `aias-config/providers/tracker-config.md`.
  2. Determine source state and transition:
     - If DoR/DoD existed prior to this command (normal path): transition `ready` -> `in_progress`.
     - If bug exception applied (DoR/DoD generated by this command): transition `pending_dor` -> `in_progress`.
  3. Update `status: in_progress` in `status.md`.
  4. If config is missing, invalid, or unresolvable: abort sync and request provider configuration.
  5. Report transition result in chat (include which transition path was used).
- If tracker transition fails, report the error but do not block planning (planning data is still valuable).

### RHOAIAS Impact Analysis

After assigning classification, determine whether the task will affect `RHOAIAS.md` sections:

1. If `RHOAIAS.md` does not exist in the project root → set `rhoaias_update: null` in `status.md`, skip analysis.
2. If `RHOAIAS.md` contains unfilled placeholders (`< ... >` pattern from `aias init` / `new --context`) → fire **Gate: RHOAIAS Onboarding Incomplete**, then set `rhoaias_update: null`, skip impact analysis.
3. Read `RHOAIAS.md` sections. Compare against the 7 categories collected during planning:
   - **Project Structure** — does the plan create new top-level directories or modules not documented in `RHOAIAS.md`?
   - **Key Technologies** — does the plan introduce new dependencies, frameworks, or language version changes?
   - **Conventions** — does the plan change architecture patterns, DI approach, or testing strategy?
   - **Build and Test** — does the plan add new test targets or modify build/CI configuration?
4. If structural impact is detected in any section → set `rhoaias_update: required`.
5. If no impact detected → set `rhoaias_update: null`.

Report the result in the End-of-Response Confirmation.

#### Advisory Notice: RHOAIAS Onboarding Incomplete

**Fires:** When `RHOAIAS.md` exists but contains unfilled placeholders.
**Skippable:** Yes (informational only, does not block planning).

**Context output:**
"RHOAIAS.md contains unfilled placeholder sections from initial generation. Project context is incomplete — agent context quality will be degraded across all modes and commands. Use an agent conversation to fill `RHOAIAS.md` by reading the project's skills, contracts, and codebase structure."

**No AskQuestion required** — this is an advisory message appended to the End-of-Response Confirmation. It does not block or require user input.

Classification is used **only for governance** (gates in `/implement`), not for publishing decisions:
- **Minor:** Feedback gate after each increment in `/implement`.
- **Standard:** MAY generate `## Governance` in `increments.plan.md` if risk warrants it.
- **Critical:** MUST generate `## Governance` with at least one Approval gate.

When `refinement_validated: true` in `status.md` (set by `/enrich --brief` when brief comment is posted and knowledge publish succeeds), it improves context quality only. It MUST NOT relax classification-derived governance gates.

---

## 5. Content Rules (Semantics)

- Output must be in **English**.
- Apply the **technical-writing** skill patterns: Problem Framing, Acceptance Criteria, Risk Articulation, Conciseness.
- Apply the **incremental-decomposition** skill for all increment decisions.
- Do **NOT** invent information.
- Use **ONLY** the provided inputs and codebase analysis.
- If information is missing for a category, state what is missing and why it matters.
- Collect data for ALL 7 categories. If a category does not apply, state "N/A" with a brief reason.
- The implementation plan must be structured as **named increments** (category 3).
- **Design Specification** (category 6) is only collected when a design URL is provided and design context is available.
- DoR Test criteria (from `dor.plan.md`) define **what** must be tested. Category 5 (Testing) defines **how** to implement those tests: input is the DoR Test criteria; output is a test implementation strategy.

### Canonical Section Titles (v9.4+)

Per `aias/contracts/readme-artifact.md` § Canonical Section Titles, artifact section headings MUST use the canonical heading name, not the producer-side data-collection category label.

- The agent MUST NOT emit `## Category N: <title>` (or `### Category N: <title>`) into any written artifact. Producer-side `Category N:` headings live in this skill body only; the artifact-side heading drops the `Category N:` prefix.
- Canonical artifact heading mapping (transversal, summarized; full map in `readme-artifact.md`):

| Producer category | Target artifact | Canonical artifact heading |
|---|---|---|
| Category 1: Problem Framing | `technical.plan.md` | `## Problem Framing` |
| Category 2: Architecture & Approach | `technical.plan.md` | `## Architecture and Approach` |
| Category 3: Increments | `increments.plan.md` | `## Increments` with `### <Increment Name>` per increment |
| Category 4: Self Code Review | `increments.plan.md` | `## Self Code Review` |
| Category 5: Testing | `increments.plan.md` | `## Testing` |
| Category 6: Design Specification | `specs.design.md` | `## Design Specification` |
| Category 7: File Structure + Visualization | `technical.plan.md` | `## File Structure and Visualization` |

- Governance section (when emitted) uses `## Governance` in `increments.plan.md`, no `Category` prefix.
- Amendment blocks (when emitted) use `## Proposed DoR Amendments` and `## Proposed DoD Amendments` in `technical.plan.md`, no `Category` prefix.

---

## 6. Collection Protocol

### Phase 0: COMPREHENSION + DoR/DoD VERIFICATION

Before collecting any data, verify DoR/DoD precondition and confirm understanding of the requirement.

**Step 1 — DoR/DoD Precondition:**

1. If `dor.plan.md` AND `dod.plan.md` exist in TASK_DIR → consume as context, continue.
2. If they do NOT exist locally → attempt knowledge provider fallback:
   a. Resolve knowledge provider from `aias-config/providers/knowledge-config.md`. If not configured or resolution fails, fall through silently.
   b. Navigate the Confluence hierarchy: `<TECH>/<YEAR>/<QUARTER>/<TASK_ID>/`.
   c. Search descendants for pages titled `<TASK_ID>: dor.plan.md` and `<TASK_ID>: dod.plan.md`.
   d. If BOTH found: read page content, write to TASK_DIR (create TASK_DIR if needed), set artifact sync status to `synced` in `status.md`, continue.
   e. If only one found or none → fall through.
   - This fallback only searches for `dor.plan.md` and `dod.plan.md` — it does not download other artifacts.
3. If still not found BUT `feasibility.assessment.md` exists AND `profile: bugfix` in `status.md` → **bug exception**: generate DoR/DoD bugfix artifacts derived from `report.issue.md` + `analysis.fix.md` + `feasibility.assessment.md`, then continue. **Bug exception is the ONLY create path for `/blueprint`** — it applies exclusively to `profile: bugfix` flows (v9.6+).
4. **Non-bugfix profile precondition (v9.6+):** If still not found AND profile is NOT `bugfix` (i.e., `feature | refactor | enrichment | delivery | spike` per `aias/.skills/rho-aias/reference.md` § Workflow Profiles), abort with `[STATE: blocked]` and message: "Refinement artifacts missing for non-bugfix profile. Run `/enrich <TASK_ID>` first to create `dor.plan.md` and `dod.plan.md`, then re-run `/blueprint`."
5. If still not found AND no assessment exists → **STOP**: "DoR/DoD not found in TASK_DIR or knowledge provider. Run `/enrich <TASK_ID>` to define scope and criteria before planning."

**Step 2 — DoR/DoD Context Loading:**

Summarize the loaded DoR/DoD for the Comprehension gate:
- DoR dimensions (key functional requirements, test criteria, constraints, out of scope)
- DoD criteria (completeness checklist)
- "Assumptions from DoR" as subsection

**Step 3 — Tracker Transition:**

Execute TRACKER SYNC (section 4) to transition `ready` -> `in_progress`.

**Step 4 — Comprehension Summary:**

1. Summarize in 2–3 lines what you understand the user wants to build or fix.
2. State the source context: task id / tracker reference, design URL, chat description, or combination.
3. Include DoR/DoD summary from Step 2.
4. List any assumptions you're making.
5. Fire the Comprehension gate.

#### Gate: Comprehension

**Type:** Confirmation
**Fires:** Phase 0, before any data collection.
**Skippable:** MUST fire UNLESS `--fast` is specified.

**Context output:**
Present comprehension summary in chat:
- Requirement (2–3 line summary)
- Sources (task id / tracker reference / design URL / chat context)
- DoR summary (dimensions loaded, key requirements)
- DoD summary (criteria count, key items)
- Upstream artifacts loaded from TASK_DIR (or "none")
- Assumptions (or "none")
- Tracker transition result (`ready → in_progress` or error)

**AskQuestion:**
- **Runtime compatibility:** If `AskQuestion` is unavailable, use the Text Gate Protocol from `readme-commands.md` with the same prompt, option ids, labels, and `allow_multiple` semantics.
- **Prompt:** "Comprehension check — is this understanding correct?"
- **Options:**
  - `confirm`: "Confirm understanding and begin data collection"
  - `adjust`: "Adjust understanding before proceeding"
- **allow_multiple:** false

**On response:**
- `confirm` → Proceed to Phase 1 (COLLECT)
- `adjust` → Apply corrections, return to context output and re-present gate

**Anti-bypass:** Inherits Gate Invocation Protocol. No additional rules.

#### Gate: Checkpoint

**Type:** Confirmation
**Fires:** Phase 0, immediately after Comprehension (or as the first gate when Comprehension is skipped via `--fast`).
**Skippable:** MUST fire UNLESS `--fast` is specified.

**Context output:**
Present a planning checkpoint summary:
- Ready-to-collect signal (DoR/DoD verified or bug exception path)
- Source coverage (tracker/design/chat inputs)
- Any blockers that would invalidate collection

**AskQuestion:**
- **Runtime compatibility:** If `AskQuestion` is unavailable, use the Text Gate Protocol from `readme-commands.md` with the same prompt, option ids, labels, and `allow_multiple` semantics.
- **Prompt:** "Checkpoint before collection — continue with plan data collection?"
- **Options:**
  - `continue`: "Continue with plan data collection"
  - `adjust`: "Adjust assumptions before collecting"
- **allow_multiple:** false

**On response:**
- `continue` → Proceed to Phase 1 (COLLECT)
- `adjust` → Apply corrections, return to context output and re-present gate

**Anti-bypass:** Inherits Gate Invocation Protocol. No additional rules.

### Phase 1: COLLECT (Categories 1–7)

Collect all 7 categories. DoR/DoD are consumed as context — they are NOT re-collected.

**DoR alignment check (v9.6+ TODO model, single-path):** While collecting categories, verify that the proposed plan covers the functional requirements from the DoR. **Any gap detected between DoR/DoD and the technical plan MUST be staged as a proposed amendment** in the corresponding split section (`## Proposed DoR Amendments` or `## Proposed DoD Amendments`) in `technical.plan.md`. Blueprint **MUST NOT modify** `dor.plan.md` or `dod.plan.md` even when the user resolves a gap inline in chat — inline answers are captured as a `**Inline confirmation**:` sub-field marker within the Proposed bullet, and `/consolidate-plan` applies them via the standard Update Approval gate. The legacy combined section `## Proposed DoR/DoD Amendments` is FORBIDDEN since v9.5.

#### Staged amendments (all gaps, inline-confirmed or unresolved)

Every gap detected during Phase 1 is staged as a proposed amendment in `technical.plan.md`. Split routing is mandatory:

- **DoR-targeted gaps** → `## Proposed DoR Amendments` (section in `technical.plan.md`). Items here describe gaps in `dor.plan.md` to be applied by `/consolidate-plan` to `dor.plan.md`.
- **DoD-targeted gaps** → `## Proposed DoD Amendments` (section in `technical.plan.md`). Items here describe gaps in `dod.plan.md` to be applied by `/consolidate-plan` to `dod.plan.md`.

Each amendment entry uses a uniform multi-line shape (per `readme-artifact.md` v2.3 § Refinement Artifact Mutation Invariant):

```markdown
## Proposed DoR Amendments

- **<Dimension>**: <gap description>.
  - **Proposed resolution**: <agent's proposed value or "needs <X> from <role>">
  - **Inline confirmation** (optional, only when user resolved in chat): <user value> (YYYY-MM-DD)

## Proposed DoD Amendments

- **<Criterion>**: <gap description>.
  - **Proposed resolution**: <agent's proposed value or "needs <X> from <role>">
  - **Inline confirmation** (optional, only when user resolved in chat): <user value> (YYYY-MM-DD)
```

The `**Inline confirmation**:` sub-field is **optional**. Include it only when the user answers a DoR/DoD gap directly in the same `/blueprint` chat. The value is captured verbatim with the resolution date in `YYYY-MM-DD` UTC. `/consolidate-plan` v2.1.0+ parses this marker and uses it as the default proposed value during its Update Approval gate.

**Routing invariant (FORBIDDEN patterns):**

- Mixing DoR and DoD items in a single Proposed section is FORBIDDEN.
- Emitting a legacy single-block `## Proposed DoR/DoD Amendments` is FORBIDDEN (since v9.5). `/validate-plan` v2.1.0 hard-fails on detection of this legacy heading.
- Inline-confirmed items MUST appear in the Proposed section with the `**Inline confirmation**:` sub-field marker — they are applied by `/consolidate-plan` like any other amendment (the marker provides the default value).
- Direct modification of `dor.plan.md` or `dod.plan.md` from `/blueprint` is FORBIDDEN under any circumstance (v9.6+). Bug exception in § Phase 0 applies to **create** only, not modify.

If neither `## Proposed DoR Amendments` nor `## Proposed DoD Amendments` has content after Phase 1, OMIT the heading entirely (do NOT emit empty sections).

### Phase 2: ANALYZE

Structure the collected data:
- "DoR alignment" — verify that the increments proposed cover the functional requirements of the DoR.
- "DoD reference" — ensure the DoD is considered in self-review and testing categories.

### Phase 3: STRUCTURE + WRITE

Structure the collected data into the artifact files and fire the Preview gate (section 4). Write to TASK_DIR only after gate confirmation.

#### Governance Output

After structuring increments and before the Preview gate, determine whether `increments.plan.md` requires a `## Governance` section:

- **Minor:** MUST NOT generate a `## Governance` section.
- **Standard:** MAY generate a `## Governance` section when risk assessment or cross-team dependencies warrant per-increment custom gates. If no custom gates are needed, omit the section.
- **Critical:** MUST generate a `## Governance` section with at least one Approval gate before the first increment.

The `## Governance` section follows the Governance-in-Artifact Schema defined in `readme-commands.md`. Classification is assigned in Phase 5 (Status Update) and written to `status.md`, not to the governance section itself.

---

## 7. Output Structure (Data Categories)

Collect data for each of the following categories. Each category maps to a specific artifact file.

> **Canonical heading invariant (v9.4+, see `readme-artifact.md` § Canonical Section Titles):** The `### Category N: <Title>` shape below is the **producer-side** structure used during data collection. The canonical heading in the **produced artifact** drops the `Category N:` prefix. Each category lists its canonical artifact heading explicitly. Emitting `## Category N:` into `technical.plan.md`, `increments.plan.md`, or `specs.design.md` is FORBIDDEN — it bleeds internal scaffolding into the knowledge provider.

### Category 1: Problem Framing → `technical.plan.md`

**Canonical artifact heading:** `## Problem Framing`

- What we are building or fixing (1–2 lines)
- Why it matters (user impact, bug impact, or technical motivation)
- Current behavior vs desired behavior (if known)

### Category 2: Architecture & Approach → `technical.plan.md`

**Canonical artifact heading:** `## Architecture and Approach`

- Architectural approach aligned with project guidelines
- Use Cases involved (high level)
- DI implications (if any)
- Constraints from existing patterns or legacy code

### Category 3: Increments (required) → `increments.plan.md`

**Canonical artifact heading:** `## Increments`, with each increment under `### <Increment Name>` (no `Category` or numeric prefix on the artifact side; the producer-side `Category 3:` label is internal to this skill only).

Structure the implementation as **named increments**. Apply the **incremental-decomposition** skill.

`increments.plan.md` MUST use the Cursor-first `.plan.md` profile:

- frontmatter `name` = concise plan label for the increment set
- frontmatter `overview` = 1–2 sentence summary of the execution strategy
- frontmatter `todos` = exactly one item per increment, in execution order
- frontmatter `isProject` = `false`
- each todo item MUST include:
  - `id`
  - `content`
  - `status: pending`

The Markdown body remains the human-readable plan. Frontmatter tracks execution state; it does not replace the increment sections below.

**Per increment, provide:**
- **Increment name** (short, descriptive)
- **Goal:** What "done" looks like for this increment (one or two lines)
- **Steps:** Ordered steps where each step includes: what changes, what could go wrong, how to verify quickly
- Where relevant: scope control, concurrency (async/await), error handling, performance/security

**Improvement margin:** Optional improvements listed separately. Must NOT block "done" for any increment.

### Category 4: Self Code Review → `increments.plan.md`

**Canonical artifact heading:** `## Self Review` (no `Category` prefix). Lives inside `increments.plan.md` alongside `## Increments` and `## Testing`.

- How implementation will be validated before sending to QA
- Compliance with project standards
- Alignment with DoR Technical constraints (from `dor.plan.md`)

### Category 5: Testing → `increments.plan.md`

**Canonical artifact heading:** `## Testing` (no `Category` prefix).

**Input:** Test criteria from `dor.plan.md` (what must be tested — scenarios, happy path, edge cases, failure scenarios).
**Output:** Test implementation strategy — how to cover the DoR test criteria.

- Tests to create/update (unit, integration, UI) mapped to DoR test criteria
- Manual verification steps per increment
- Fixtures/mocks needed
- How to execute the tests
- Edge cases and failure paths to validate

Category 5 does NOT re-define the test scenarios (those are in the DoR). It defines the implementation plan: "for these N DoR scenarios, we will create X unit tests in Y file, Z integration tests, and W manual verification steps."

### Category 6: Design Specification (conditional) → `specs.design.md`

**Canonical artifact heading:** `## Design Specification` (with sub-sections for component hierarchy, visual states, interaction map, accessibility, and design system mapping as `### <Sub-Section>`, no `Category` prefix).

**Trigger conditions (v9.4+):** Collect this category when **either** condition is true:

- **(a)** A design URL is provided AND the design provider is resolvable from `aias-config/providers/design-config.md`.
- **(b)** The DoR declares `orientation: user_facing` in `dor.plan.md`, regardless of design URL availability.

**Behavior by condition:**

| Condition | Behavior |
|---|---|
| (a) only — design URL with resolvable provider | Full extraction via the resolved design provider. Extract component hierarchy, layout/visual properties, typography, interactive states, and token references. |
| (b) only — `user_facing` DoR with no design URL | Generate a **minimal `specs.design.md`** derived from DoR Functional + DoR Technical constraints + chat context. The artifact MUST include the explicit note: `> **Design provider was not consulted** — this specification is derived from DoR and context only and SHOULD be revisited with a design reference before implementation.` Do NOT invent visual states, colors, typography, or token mappings the DoR does not declare. |
| (a) AND (b) — design URL and `user_facing` DoR | Full extraction via the design provider PLUS a DoR alignment commentary section that highlights any divergence between the design and the DoR's declared functional intent. |
| Neither — no design URL and orientation is not `user_facing` | Omit `specs.design.md`. |

For condition (a) and (a) AND (b): if the design provider config is missing, invalid, or unresolvable while a design URL was provided, abort and request configuration (Phase 3 fail-fast).

For condition (b) only: design provider unavailability is NOT a blocker. The minimal `specs.design.md` MUST be generated using DoR + chat context.

If the active mode defines a **DESIGN SYSTEM MAPPING** section, apply it: map raw design values (colors, typography, spacing) to the project's design tokens. Present both the raw value and the mapped token for each property so the developer can verify the match. Under condition (b) only (no design provider), design system mapping is omitted because there are no raw design values to map; the note above must declare that absence.

### Category 7: File Structure + Visualization → `technical.plan.md`

**Canonical artifact heading:** `## File Structure and Visualization` (no `Category` prefix).

- Files to create (with suggested paths)
- Files to modify
- Dependencies to verify/add
- Architecture and flow diagrams using Mermaid

---

## 7. Non-Goals / Forbidden Actions

This command must **NOT**:
- Write implementation code or full file contents
- Skip categories without stating why
- Invent information not present in inputs or codebase analysis
- Push to git or publish to external services without explicit user instruction
- Write artifacts outside TASK_DIR
- Create artifact types not in the closed catalog
- **Modify `dor.plan.md` or `dod.plan.md` directly under ANY circumstance (v9.6+).** Blueprint MAY only **create** `dor.plan.md` / `dod.plan.md` under the bug exception (§ Phase 0, Step 1, item 3 — `profile: bugfix` with `feasibility.assessment.md` present). Any change to existing DoR/DoD content — inline-confirmed or otherwise — MUST be staged as a proposed amendment in `## Proposed DoR Amendments` or `## Proposed DoD Amendments` (with the `**Inline confirmation**:` sub-field marker when the user resolved inline) and resolved by `/consolidate-plan`. The legacy combined section `## Proposed DoR/DoD Amendments` remains FORBIDDEN since v9.5.
- Proceed without DoR/DoD (except bug exception with assessment artifacts)

SERVICE RESOLUTION PSEUDOFLOW:

```
tracker = resolve(tracker-config) or abort(missing/invalid tracker config)
design = resolve(design-config) or abort(missing/invalid design config)
knowledge = resolve(knowledge-config) or abort(missing/invalid knowledge config)
```

---

## 8. Self-Verification Checklist

- [ ] Required planning artifacts were written to TASK_DIR (or abort path documented).
- [ ] `status.md` was updated with classification/progress data and `command_log` entry.
- [ ] Expected tracker/knowledge side effects were executed or explicitly reported as blocked.
- [ ] Terminal state line was emitted with canonical state token.

## 9. Halt Discipline

- Pause only at declared gates, preconditions, or blocking failures.
- Avoid ad-hoc confirmation pauses between mandatory phases.
- If blocked, report blocker + exact required input.

## Terminal State Emission

`[STATE: completed | partial | blocked | failed]` + one-line summary is mandatory.

## Invocation Mode Detection

- Standalone is default.
- Pipeline mode MAY be inferred via `--from-pipeline`, `--invoked-by`, or predecessor evidence in `status.md`.
- Detection MAY skip duplicate interactive checks already resolved in same chain, without changing artifact semantics.
