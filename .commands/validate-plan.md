# Validate Plan (Plan Alignment Validation) — v5

## 1. Identity

**Command Type:** Operative — Procedural / Execution

You are validating the **alignment and completeness** of an implementation plan against the DoR/DoD from refinement.
This command is responsible for analyzing plan artifacts in the task directory, verifying that the technical plan aligns with the DoR/DoD, identifying gaps across completeness dimensions, processing DoR/DoD amendment proposals from `/blueprint`, and reporting the verdict.

**Skills referenced:** `rho-aias`.

---

## 2. Invocation / Usage

Invocation:
- `/validate-plan`

Usage notes:
- This command is intended to be used **after** plan artifacts have been created (via `/blueprint` command).
- It analyzes the plan artifacts in TASK_DIR to identify missing elements and verify alignment with DoR/DoD.
- The output is raw, unstructured data listing gaps by category.
- When DoR/DoD amendments are proposed in `technical.plan.md`, the Amendment gate is presented.
- Validation gaps MUST be persisted centrally in `technical.plan.md`; chat is only the reporting surface.

---

## 3. Inputs

This command may use **only** the following inputs:
- Plan artifacts from TASK_DIR loaded via **rho-aias** skill (Phases 0–3): `technical.plan.md`, `increments.plan.md`, `dor.plan.md`, `dod.plan.md`, `specs.design.md` (when present), `analysis.product.md` (when present)
- Chat context explicitly provided by the user
- Service configs:
  - `aias-config/providers/knowledge-config.md`

Rules:
- All inputs must be explicit.
- TASK_DIR must be resolvable. If not, ask the user for the task ID or directory path.
- The command must read all plan artifacts in TASK_DIR to perform validation.

---

## 4. Output Contract (Format)

CHAT OUTPUT (must follow)
- **Executive summary at the start:** If the plan is **ready for implementation**, put **"Plan ready for implementation"** in a **separate paragraph and in bold**. If there are gaps, list them by dimension.
- Output must be presented directly in the chat response as raw, unstructured text. List gaps grouped by the completeness dimensions.

ARTIFACT UPDATE (validation backlog)
- `technical.plan.md` is the **single source of truth** for validation todos.
- When gaps exist, update `technical.plan.md` to use the Cursor-first `.plan.md` profile:
  - frontmatter `name`
  - frontmatter `overview`
  - frontmatter `todos`
  - frontmatter `isProject: false`
- Each validation todo MUST represent exactly one unresolved gap and MUST include:
  - `id`
  - `content`
  - `status: pending`
  - `artifact`
  - `dimension`
- The Markdown body of `technical.plan.md` remains the human-readable technical plan. Validation todos live only in frontmatter.
- When no gaps exist, `technical.plan.md` MUST NOT retain stale pending validation todos. The validation backlog should be empty or fully completed.

### Gate: Amendment Approval

**Type:** Decision
**Fires:** When `technical.plan.md` contains `## Proposed DoR/DoD Amendments`, before the Validation Result gate.
**Skippable:** No.

**Context output:**
Present each proposed amendment with context:
- Which DoR/DoD dimension is affected
- What the blueprint discovered as a gap
- Proposed change

**AskQuestion:**
- **Runtime compatibility:** If `AskQuestion` is unavailable, use the Text Gate Protocol from `readme-commands.md` with the same prompt, option ids, labels, and `allow_multiple` semantics.
- **Prompt:** "Blueprint proposed <N> amendments to DoR/DoD. How to proceed?"
- **Options:**
  - `apply_local`: "Apply amendments locally (do not publish to team)"
  - `pause`: "Pause — consult the team before proceeding"
  - `reject`: "Reject amendments — plan adjusts to existing DoR/DoD"
- **allow_multiple:** false

**On response:**
- `apply_local` → Apply amendments to `dor.plan.md`/`dod.plan.md` locally. Mark amended artifacts as `modified` in `status.md`. Do NOT publish these changes via Phase 5c — they remain local until reconciliation via `/publish` or team re-runs `/enrich`.
- `pause` → Halt validation. Inform user to consult the team and return when amendments are resolved (either via `/enrich` re-run or manual update).
- `reject` → Discard amendments. Remove `## Proposed DoR/DoD Amendments` from `technical.plan.md`. The plan must adjust to the existing DoR/DoD as-is.

### Gate: Validation Result

**Type:** Confirmation
**Fires:** When the plan passes validation ("Plan ready for implementation"), before updating `status.md`.
**Skippable:** No.

**Context output:**
Present validation result in chat:
- Verdict: "Plan ready for implementation"
- Classification from `status.md`
- Status update that will be applied

**AskQuestion:**
- **Runtime compatibility:** If `AskQuestion` is unavailable, use the Text Gate Protocol from `readme-commands.md` with the same prompt, option ids, labels, and `allow_multiple` semantics.
- **Prompt:** "Plan validated — mark as ready for implementation?"
- **Options:**
  - `confirm`: "Mark validated and continue"
  - `skip`: "Keep current status — do not update"
- **allow_multiple:** false

**On response:**
- `confirm` → Proceed to Status Update
- `skip` → Report validation result without status change

**Anti-bypass:** Inherits Gate Invocation Protocol. No additional rules.

STATUS UPDATE (Phase 5)
- Append to `command_log`: `{command: /validate-plan, started_at: <UTC>, ended_at: <UTC>}` — obtain timestamps via `date -u +%Y-%m-%dT%H:%M:%SZ`. See `reference.md` § Command Log for full rules.
- When plan passes and gate confirmed: update `status.md` — add `validate` to `completed_steps`, set `current_step` to `implement`. Do NOT modify the `status` field (it remains `in_progress` as set by `/blueprint`).
- When amendments are applied locally: mark `dor.plan.md`/`dod.plan.md` as `modified` in `status.md` artifacts map.
- When gaps exist: set `current_step` to `consolidate` and mark `technical.plan.md` as `modified` in `status.md` if validation todos were written or refreshed.
- Run Phase 5c: sync non-synced artifacts to resolved knowledge provider. Phase 5c always publishes — it is NOT conditioned by plan classification. After each successful publish, inject TOC per resolved provider config (see **rho-aias** skill § Phase 5c). Exception: DoR/DoD artifacts marked as locally amended (via Amendment gate `apply_local`) are excluded from Phase 5c until reconciled via `/publish`.

Rules:
- Do NOT structure the rest of the chat output as a formatted document.
- Focus on listing specific missing elements in a raw, conversational format in chat.

---

## 5. Content Rules (Semantics)

- Output must be in **English**.
- Do **NOT** invent information or gaps that don't exist.
- Use **ONLY** the provided plan content to identify gaps.
- If a dimension has no gaps, explicitly state that it is complete.
- Be specific about what is missing (reference plan sections, specific requirements, etc.).
- Do **NOT** suggest solutions or improvements; only identify gaps.
- Validation todo ids SHOULD be stable and deterministic when possible (for example, based on dimension + artifact + short slug).

---

## 6. Output Structure (Raw Format)

The output must be raw text that identifies gaps across completeness dimensions:

**1. Investigation Gaps** (primary: `analysis.product.md`, `technical.plan.md`)**:**
- List any areas where information is insufficient or context is not understood.
- Identify missing research, unclear requirements, or incomplete understanding.
- Specify what needs to be investigated.

**2. Definition Alignment** (primary: `dor.plan.md`, `dod.plan.md`, `technical.plan.md`)**:**
- Verify that the technical plan **aligns with** the DoR/DoD from refinement.
- Check that all DoR functional requirements are covered by at least one increment.
- Check that DoD criteria are addressable by the planned implementation.
- Check that DoR test criteria are covered by the testing plan (Category 5 in `/blueprint`).
- List any alignment gaps: DoR requirements not covered, DoD criteria not achievable, or test criteria not planned.

**3. Planning Gaps** (primary: `increments.plan.md`, `technical.plan.md`)**:**
- List any areas where organization (how, when, who) is missing.
- Identify missing sequencing, dependencies, resource allocation, or timeline considerations.
- Specify what needs to be planned.
- **Incremental validation (same dimension):** Check that the plan has named increments; that each increment has a clear goal (Increment Done) and is self-contained; that the improvement margin is present or explicitly "None"; and that DoR vs Increment Done vs DoD are clearly distinguished (DoR = before implementation, Increment Done = per-increment goal, DoD = ready for QA for the implemented scope). List any gaps in this incremental structure (e.g. increment without goal, ambiguous "done").

**4. Detailing Gaps** (primary: `technical.plan.md`, `specs.design.md`)**:**
- List any areas where technical specification is missing or insufficient.
- Identify missing technical details, implementation specifics, or architectural decisions.
- Specify what needs to be detailed.

**5. Refinement Gaps** (all artifacts)**:**
- List any areas that need polishing or improvement.
- Identify sections that are rough, incomplete, or need enhancement.
- Specify what needs to be refined.

**6. Classification Check:**
- Verify that `classification` in `status.md` is set (`minor`, `standard`, or `critical`). If `null` or missing, report as a gap.

**7. Governance Gaps** (primary: `increments.plan.md`, `status.md`)**:**
- Classification Critical without a `## Governance` section in `increments.plan.md` → flag as gap ("Critical requires at least one Approval gate").
- `## Governance` section present with gate types outside the taxonomy (Confirmation, Decision, Feedback, Approval, Precondition) → flag as gap ("Unknown gate type").
- Custom gates that contradict classification baseline (e.g., per-increment Approval gates in a Minor plan) → flag as gap ("Custom gates exceed classification baseline expectations").

For each dimension:
- If complete: State "No gaps identified" or "Complete".
- If gaps exist: List each gap as a specific, actionable item.

Persistence rule:
- After identifying gaps, persist the unresolved set as validation todos in `technical.plan.md`.
- Each todo MUST reference the affected artifact (`technical.plan.md`, `dor.plan.md`, `dod.plan.md`, `specs.design.md`, etc.) and the validation dimension.
- `/validate-plan` owns creation and refresh of this backlog; `/implement` does not modify it.

---

## 7. Non-Goals / Forbidden Actions

This command must **NOT**:
- Suggest solutions or improvements to identified gaps; only list gaps
- Create structured output (templates, formatted documents) in chat except the executive summary
- Infer gaps that are not explicitly evident in the plan content
- Perform deep analysis beyond identifying missing elements
- Assume a task directory if none was provided; ask for task ID or path
- Modify the `status` field in `status.md` (it remains `in_progress` as set by `/blueprint`)
- Trigger any tracker status transition (tracker transitions are owned by `/blueprint`, `/pr` (owns `in_progress → in_review`), and `/commit` (verifies `in_review`))
- Publish locally-amended DoR/DoD artifacts via Phase 5c (those are reconciled via `/publish`)
