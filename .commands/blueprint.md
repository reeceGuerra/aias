# Blueprint (Plan Data Collection + Structuring) — v4

## 1. Identity

**Command Type:** Type B — Procedural / Execution

You are guiding the **systematic collection and structuring** of all data required for an implementation plan. This command collects raw planning data, structures it into artifacts, and writes them to the task directory.

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
- `--fast` suppresses the Comprehension gate (Phase 0) and the Checkpoint gate (Phase 1). The Preview gate always fires. All 13 categories are still collected. Use for trivial or well-understood tasks where validation gates add friction without value.
- If TASK_DIR is set (via Structured Prompt or task id), writes to that directory. If not, creates a new directory from the task id or an agent-chosen name.
- In the Structured Prompt, prefer `TASK ID` / `TASK DIR` (or `DIR`) over legacy `TICKET`.

---

## 3. Inputs

This command may use **only** the following inputs:
- Chat context explicitly provided by the user
- Output from `@planning` mode reasoning (if active)
- Tracker data (via resolved tracker provider, if a task id / tracker ticket URL is provided)
- Design context (via resolved design provider, if design URL provided)
- Codebase analysis results (files, patterns, dependencies found during analysis)
- **Upstream artifacts** detected in TASK_DIR: `*.product.md`, `*.fix.md`, `*.issue.md`, `*.assessment.md` — if present, load and incorporate as additional context
- Service configs:
  - `aias-providers/tracker-config.md`
  - `aias-providers/design-config.md`
  - `aias-providers/knowledge-config.md`

Context enrichment requirements:
- If tracker data is not already in context and a task id or tracker URL was provided, resolve tracker provider from `aias-providers/tracker-config.md`; if missing/invalid/unresolvable, abort and request provider configuration.
- If design context is not already available and a design URL was provided, resolve design provider from `aias-providers/design-config.md`; if missing/invalid/unresolvable, abort and request provider configuration.
- If classification is B or C and knowledge provider config is missing/invalid/unresolvable, abort before Phase 5c.

Rules:
- All inputs must be explicit.
- If critical information is missing, ask before proceeding (see `@planning` INTERACTIVE QUESTIONING for priority rules).

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
- Assigned classification (A/B/C)

**AskQuestion:**
- **Runtime compatibility:** If `AskQuestion` is unavailable, use the Text Gate Protocol from `readme-commands.md` with the same prompt, option ids, labels, and `allow_multiple` semantics.
- **Prompt:** "Plan ready. <count> increments, classification <A|B|C>. Write artifacts to <TASK_DIR>?"
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
| `technical.plan.md` | Problem framing, architectural approach, file structure, visualization |
| `increments.plan.md` | Cursor-first `.plan.md` artifact with frontmatter `name`, `overview`, `todos`, `isProject`, plus body content for increments, goals, steps, improvement margin, self-review, testing, and DoD alignment |
| `dor.plan.md` | Definition of Ready (functional, non-functional, technical, test cases, commitment) |
| `dod.plan.md` | Definition of Done checklist |
| `specs.design.md` | Design specification from resolved design provider (only when design context exists) |

### End-of-Response Confirmation

After writing all artifacts, print:
```
Artifacts written to: <absolute_path_to_TASK_DIR>/
  - technical.plan.md
  - increments.plan.md
  - dor.plan.md
  - dod.plan.md
  [- specs.design.md]
```

### Status Update (Phase 5)

After writing artifacts:
1. Update `status.md`: add each artifact to the `artifacts` map with status `created` (new) or `modified` (overwrite).
2. **Assign Plan Classification**: set `classification` in `status.md` to `A`, `B`, or `C` based on scope, impact, and complexity. See `SKILL.md` Plan Classification for criteria.
3. Add `blueprint` to `completed_steps`, set `current_step` to `validate`.
4. Run Phase 5c (classification-gated): sync non-synced artifacts to resolved knowledge provider only if classification is B or C. Skip if A (see **rho-aias** skill § Phase 5c). Note: classification was just assigned in step 2 — the gate reads the value set in this same execution.

---

## 5. Content Rules (Semantics)

- Output must be in **English**.
- Apply the **technical-writing** skill patterns: Problem Framing, Acceptance Criteria, Risk Articulation, Conciseness.
- Apply the **incremental-decomposition** skill for all increment decisions.
- Do **NOT** invent information.
- Use **ONLY** the provided inputs and codebase analysis.
- If information is missing for a category, state what is missing and why it matters.
- Collect data for ALL 13 categories. If a category does not apply, state "N/A" with a brief reason.
- The implementation plan must be structured as **named increments** (category 7).
- **Design Specification** (category 12) is only collected when a design URL is provided and design context is available.

---

## 6. Collection Protocol

### Phase 0: COMPREHENSION

Before collecting any data, confirm understanding of the requirement.

1. Summarize in 2–3 lines what you understand the user wants to build or fix.
2. State the source context: task id / tracker reference, design URL, chat description, or combination.
3. List any assumptions you're making.
4. Fire the Comprehension gate.

#### Gate: Comprehension

**Type:** Confirmation
**Fires:** Phase 0, before any data collection.
**Skippable:** MUST fire UNLESS `--fast` is specified.

**Context output:**
Present comprehension summary in chat:
- Requirement (2–3 line summary)
- Sources (task id / tracker reference / design URL / chat context)
- Upstream artifacts loaded from TASK_DIR (or "none")
- Assumptions (or "none")

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

### Phase 1: COLLECT (Categories 1–6)

Collect: Problem Framing, DoR (Functional, Non-Functional, Technical, Test Cases), and Commitment.

After completing these 6 categories, fire the Checkpoint gate.

#### Gate: Checkpoint

**Type:** Confirmation
**Fires:** Phase 1, after categories 1–6 are collected.
**Skippable:** MUST fire UNLESS `--fast` is specified.

**Context output:**
Present checkpoint summary in chat:
- Problem (one-line summary)
- Happy path (core behavior)
- Key constraints (top 2–3 technical/non-functional)
- Dependencies (blocking items or "none")
- Increments preview (estimated count based on scope so far)

**AskQuestion:**
- **Runtime compatibility:** If `AskQuestion` is unavailable, use the Text Gate Protocol from `readme-commands.md` with the same prompt, option ids, labels, and `allow_multiple` semantics.
- **Prompt:** "Categories 1–6 collected. Continue to increments and remaining categories?"
- **Options:**
  - `continue`: "Continue to remaining categories (7–13)"
  - `adjust`: "Adjust categories 1–6 before continuing"
- **allow_multiple:** false

**On response:**
- `continue` → Proceed to Phase 2 (categories 7–13)
- `adjust` → Apply corrections, return to context output and re-present gate

**Anti-bypass:** Inherits Gate Invocation Protocol. No additional rules.

### Phase 2: COLLECT (Categories 7–13)

Collect: Increments, Self Code Review, Testing, DoD, File Structure, Design Specification (if applicable), and Visualization.

### Phase 3: STRUCTURE + WRITE

Structure the collected data into the artifact files and fire the Preview gate (section 4). Write to TASK_DIR only after gate confirmation.

#### Governance Output

After structuring increments and before the Preview gate, determine whether `increments.plan.md` requires a `## Governance` section:

- **Type A:** MUST NOT generate a `## Governance` section.
- **Type B:** MAY generate a `## Governance` section when risk assessment or cross-team dependencies warrant per-increment custom gates. If no custom gates are needed, omit the section.
- **Type C:** MUST generate a `## Governance` section with at least one Approval gate before the first increment.

The `## Governance` section follows the Governance-in-Artifact Schema defined in `readme-commands.md`. Classification is assigned in Phase 5 (Status Update) and written to `status.md`, not to the governance section itself.

---

## 7. Output Structure (Data Categories)

Collect data for each of the following categories. Each category maps to a specific artifact file.

### Category 1: Problem Framing → `technical.plan.md`

- What we are building or fixing (1–2 lines)
- Why it matters (user impact, bug impact, or technical motivation)
- Current behavior vs desired behavior (if known)

### Category 2: DoR Functional → `dor.plan.md`

- Intended behavior (happy path)
- User experience expectations
- Visible states or outcomes

### Category 3: DoR Non-Functional → `dor.plan.md`

- Performance considerations
- Security or data sensitivity concerns
- Accessibility or UX constraints (if applicable)

### Category 4: DoR Technical → `dor.plan.md`

- Architectural approach aligned with project guidelines
- Use Cases involved (high level)
- DI implications (if any)
- Constraints from existing patterns or legacy code

### Category 5: DoR Test Cases → `dor.plan.md`

- What needs to be verified to consider the requirement correct
- Happy path test cases
- Key edge cases (max 5)
- Failure scenarios worth validating
- Missing DoR elements
- Targeted questions required to proceed (only those that materially affect the plan)

### Category 6: Commitment → `dor.plan.md`

- Whether the requirement has been analyzed
- Related ticket (if applicable)
- Task list (high level)
- Dependency analysis
- Suggested implementation order
- Blocking analysis
- Working branch status

### Category 7: Increments (required) → `increments.plan.md`

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

### Category 8: Self Code Review → `increments.plan.md`

- How implementation will be validated before sending to QA
- Compliance with project standards
- Alignment with DoR Technical

### Category 9: Testing → `increments.plan.md`

- Tests to be implemented or updated
- Manual verification steps
- Edge cases and failure paths to validate

### Category 10: DoD (Definition of Done) → `dod.plan.md`

All criteria that determine when the implemented scope is ready for QA.

### Category 11: File Structure → `technical.plan.md`

- Files to create (with suggested paths)
- Files to modify
- Dependencies to verify/add

### Category 12: Design Specification (conditional) → `specs.design.md`

**Only collect when a design URL is provided.** Resolve design provider from `aias-providers/design-config.md`. If config/provider is unavailable, abort and request configuration. Extract component hierarchy, layout/visual properties, typography, interactive states, and token references.

If the active mode defines a **DESIGN SYSTEM MAPPING** section, apply it: map raw design values (colors, typography, spacing) to the project's design tokens. Present both the raw value and the mapped token for each property so the developer can verify the match.

### Category 13: Visualization → `technical.plan.md`

Architecture and flow diagrams using Mermaid.

---

## 8. Non-Goals / Forbidden Actions

This command must **NOT**:
- Write implementation code or full file contents
- Skip categories without stating why
- Invent information not present in inputs or codebase analysis
- Push to git or publish to external services without explicit user instruction
- Write artifacts outside TASK_DIR
- Create artifact types not in the closed catalog

SERVICE RESOLUTION PSEUDOFLOW:

```
tracker = resolve(tracker-config) or abort(missing/invalid tracker config)
design = resolve(design-config) or abort(missing/invalid design config)
knowledge = resolve(knowledge-config) or abort(missing/invalid knowledge config)
```
