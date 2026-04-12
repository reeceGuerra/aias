# Blueprint (Plan Data Collection + Structuring) — v5

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
- `/blueprint --fast` — skip Comprehension gate (combinable with other arguments)

Usage notes:
- Best used with `@planning` mode active for reasoning quality.
- Can be invoked standalone when required service configs are available and resolvable.
- Output is written directly to the task directory as separate artifact files.
- `--fast` suppresses the Comprehension gate (Phase 0). The Preview gate always fires. All 7 categories are still collected. Use for trivial or well-understood tasks where validation gates add friction without value.
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
- Create `status.md` if it does not exist, with profile inferred from context (default: `feature`).

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
| `technical.plan.md` | Problem framing, architectural approach, file structure, visualization, proposed DoR/DoD amendments (if any) |
| `increments.plan.md` | Cursor-first `.plan.md` artifact with frontmatter `name`, `overview`, `todos`, `isProject`, plus body content for increments, goals, steps, improvement margin, self-review, testing |
| `specs.design.md` | Design specification from resolved design provider (only when design context exists) |
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

### Status Update (Phase 5)

After writing artifacts:
1. Update `status.md`: add each artifact to the `artifacts` map with status `created` (new) or `modified` (overwrite).
2. **Assign Plan Classification**: set `classification` in `status.md` to `minor`, `standard`, or `critical` based on scope, impact, and complexity. See `SKILL.md` Plan Classification for criteria.
3. **RHOAIAS Impact Analysis**: evaluate whether the planned work will require a `RHOAIAS.md` update. See § RHOAIAS Impact Analysis below.
4. Add `blueprint` to `completed_steps`, set `current_step` to `validate`.
5. Run Phase 5c: sync non-synced artifacts to resolved knowledge provider. Phase 5c always publishes — it is NOT conditioned by plan classification. When the bug exception generated `dor.plan.md` and `dod.plan.md`, Phase 5c publishes them automatically alongside `technical.plan.md` and `increments.plan.md`.

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

#### Gate: RHOAIAS Onboarding Incomplete

**Type:** Advisory
**Fires:** When `RHOAIAS.md` exists but contains unfilled placeholders.
**Skippable:** Yes (informational only, does not block planning).

**Context output:**
"RHOAIAS.md contains unfilled placeholder sections from initial generation. Project context is incomplete — agent context quality will be degraded across all modes and commands. Use an agent conversation to fill `RHOAIAS.md` by reading the project's skills, contracts, and codebase structure."

**No AskQuestion required** — this is an advisory message appended to the End-of-Response Confirmation. It does not block or require user input.

Classification is used **only for governance** (gates in `/implement`), not for publishing decisions:
- **Minor:** No additional governance gates in `/implement`.
- **Standard:** MAY generate `## Governance` in `increments.plan.md` if risk warrants it.
- **Critical:** MUST generate `## Governance` with at least one Approval gate.

When `refinement_validated: true` in `status.md` (set by `/enrich` after team refinement), classification-derived governance gates are relaxed (e.g., Critical does not require Pre-Implementation Approval in `/implement` if team refinement already validated the scope).

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

---

## 6. Collection Protocol

### Phase 0: COMPREHENSION + DoR/DoD VERIFICATION

Before collecting any data, verify DoR/DoD precondition and confirm understanding of the requirement.

**Step 1 — DoR/DoD Precondition:**

- If `dor.plan.md` AND `dod.plan.md` exist in TASK_DIR → consume as context, continue.
- If they do NOT exist BUT `feasibility.assessment.md` exists → **bug exception**: generate DoR/DoD bugfix artifacts derived from `report.issue.md` + `analysis.fix.md` + `feasibility.assessment.md`, then continue.
- If they do NOT exist AND no assessment exists → **STOP**: "DoR/DoD not found in TASK_DIR. Run `/enrich <TASK_ID>` to define scope and criteria before planning."

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

### Phase 1: COLLECT (Categories 1–7)

Collect all 7 categories. DoR/DoD are consumed as context — they are NOT re-collected.

**DoR alignment check:** While collecting categories, verify that the proposed plan covers the functional requirements from the DoR. If gaps are detected between the DoR/DoD and the technical plan:
- Do NOT modify `dor.plan.md` or `dod.plan.md`.
- Register gaps as `## Proposed DoR/DoD Amendments` in `technical.plan.md`.
- These amendments are resolved by `/validate-plan` via the Amendment gate.

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

### Category 1: Problem Framing → `technical.plan.md`

- What we are building or fixing (1–2 lines)
- Why it matters (user impact, bug impact, or technical motivation)
- Current behavior vs desired behavior (if known)

### Category 2: Architecture & Approach → `technical.plan.md`

- Architectural approach aligned with project guidelines
- Use Cases involved (high level)
- DI implications (if any)
- Constraints from existing patterns or legacy code

### Category 3: Increments (required) → `increments.plan.md`

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

- How implementation will be validated before sending to QA
- Compliance with project standards
- Alignment with DoR Technical constraints (from `dor.plan.md`)

### Category 5: Testing → `increments.plan.md`

**Input:** Test criteria from `dor.plan.md` (what must be tested — scenarios, happy path, edge cases, failure scenarios).
**Output:** Test implementation strategy — how to cover the DoR test criteria.

- Tests to create/update (unit, integration, UI) mapped to DoR test criteria
- Manual verification steps per increment
- Fixtures/mocks needed
- How to execute the tests
- Edge cases and failure paths to validate

Category 5 does NOT re-define the test scenarios (those are in the DoR). It defines the implementation plan: "for these N DoR scenarios, we will create X unit tests in Y file, Z integration tests, and W manual verification steps."

### Category 6: Design Specification (conditional) → `specs.design.md`

**Only collect when a design URL is provided.** Resolve design provider from `aias-config/providers/design-config.md`. If config/provider is unavailable, abort and request configuration. Extract component hierarchy, layout/visual properties, typography, interactive states, and token references.

If the active mode defines a **DESIGN SYSTEM MAPPING** section, apply it: map raw design values (colors, typography, spacing) to the project's design tokens. Present both the raw value and the mapped token for each property so the developer can verify the match.

### Category 7: File Structure + Visualization → `technical.plan.md`

- Files to create (with suggested paths)
- Files to modify
- Dependencies to verify/add
- Architecture and flow diagrams using Mermaid

---

## 8. Non-Goals / Forbidden Actions

This command must **NOT**:
- Write implementation code or full file contents
- Skip categories without stating why
- Invent information not present in inputs or codebase analysis
- Push to git or publish to external services without explicit user instruction
- Write artifacts outside TASK_DIR
- Create artifact types not in the closed catalog
- Modify `dor.plan.md` or `dod.plan.md` directly (propose amendments in `technical.plan.md` instead)
- Proceed without DoR/DoD (except bug exception with assessment artifacts)

SERVICE RESOLUTION PSEUDOFLOW:

```
tracker = resolve(tracker-config) or abort(missing/invalid tracker config)
design = resolve(design-config) or abort(missing/invalid design config)
knowledge = resolve(knowledge-config) or abort(missing/invalid knowledge config)
```
