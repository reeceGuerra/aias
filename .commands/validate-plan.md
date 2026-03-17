# Validate Plan (Plan Completeness Validation) — v4

## 1. Identity

**Command Type:** Type B — Procedural / Execution

You are validating the **completeness** of an implementation plan.
This command is responsible for analyzing plan artifacts in the task directory, identifying gaps across five completeness dimensions (investigation, definition, planning, detailing, refinement), and reporting the verdict. When the plan passes validation, this command triggers the canonical tracker transition `pending_dor` -> `ready` through the resolved tracker provider mapping.

**Skills referenced:** `rho-aias`.

---

## 2. Invocation / Usage

Invocation:
- `/validate-plan`

Usage notes:
- This command is intended to be used **after** plan artifacts have been created (via `/blueprint` command).
- It analyzes the plan artifacts in TASK_DIR to identify missing elements.
- The output is raw, unstructured data listing gaps by category.
- When the plan is complete ("Plan ready for implementation"), triggers canonical tracker transition `pending_dor` -> `ready`.

---

## 3. Inputs

This command may use **only** the following inputs:
- Plan artifacts from TASK_DIR loaded via **rho-aias** skill (Phases 0–3): `technical.plan.md`, `increments.plan.md`, `dor.plan.md`, `dod.plan.md`, `specs.design.md` (when present), `analysis.product.md` (when present)
- Chat context explicitly provided by the user
- Service configs:
  - `aias-providers/tracker-config.md`
  - `aias-providers/knowledge-config.md`

Rules:
- All inputs must be explicit.
- TASK_DIR must be resolvable. If not, ask the user for the task ID or directory path.
- The command must read all plan artifacts in TASK_DIR to perform validation.

---

## 4. Output Contract (Format)

CHAT OUTPUT (must follow)
- **Executive summary at the start:** If the plan is **ready for implementation**, put **"Plan ready for implementation"** in a **separate paragraph and in bold**. If there are gaps, list them by dimension.
- Output must be presented directly in the chat response as raw, unstructured text. List gaps grouped by the five completeness dimensions.

TRACKER SYNC (Phase 6 — when plan is ready)
- When verdict = "Plan ready for implementation" AND `task_id` in `status.md` is valid for the resolved tracker provider:
  - Resolve tracker provider from `aias-providers/tracker-config.md`.
  - Transition canonical tracker status from `pending_dor` -> `ready` using provider mapping.
  - If config is missing, invalid, or unresolvable: abort sync and request provider configuration.
  - Report transition result in chat.
- When gaps exist: no tracker transition.

### Gate: Validation Result

**Type:** Confirmation
**Fires:** When the plan passes validation ("Plan ready for implementation"), before updating `status.md` and triggering tracker sync.
**Skippable:** No.

**Context output:**
Present validation result in chat:
- Verdict: "Plan ready for implementation"
- Classification from `status.md`
- Tracker transition that will fire (`pending_dor` → `ready`)
- Status update that will be applied

**AskQuestion:**
- **Prompt:** "Plan validated — mark as ready and transition tracker to `ready`?"
- **Options:**
  - `confirm`: "Mark ready and sync tracker"
  - `skip`: "Keep current status — do not transition"
- **allow_multiple:** false

**On response:**
- `confirm` → Proceed to Status Update and Tracker Sync
- `skip` → Report validation result without status change or tracker transition

**Anti-bypass:** Inherits Gate Invocation Protocol. No additional rules.

STATUS UPDATE (Phase 5)
- When plan passes and gate confirmed: update `status.md` — set `status: ready`, add `validate` to `completed_steps`, set `current_step` to `implement`.
- When gaps exist: no status change.
- Run Phase 5c (classification-gated): sync non-synced artifacts to resolved knowledge provider only if classification in `status.md` is B or C. Skip if A (see **rho-aias** skill § Phase 5c).

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

---

## 6. Output Structure (Raw Format)

The output must be raw text that identifies gaps across five completeness dimensions:

**1. Investigation Gaps** (primary: `analysis.product.md`, `technical.plan.md`)**:**
- List any areas where information is insufficient or context is not understood.
- Identify missing research, unclear requirements, or incomplete understanding.
- Specify what needs to be investigated.

**2. Definition Gaps** (primary: `dor.plan.md`, `dod.plan.md`)**:**
- List any areas where what will be done to complete the requirement is not established.
- Identify missing functional definitions, unclear scope, or undefined outcomes.
- Specify what needs to be defined.

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
- Verify that `classification` in `status.md` is set (`A`, `B`, or `C`). If `null` or missing, report as a gap.

**7. Governance Gaps** (primary: `increments.plan.md`, `status.md`)**:**
- Classification C without a `## Governance` section in `increments.plan.md` → flag as gap ("Type C requires at least one Approval gate").
- `## Governance` section present with gate types outside the taxonomy (Confirmation, Decision, Feedback, Approval, Precondition) → flag as gap ("Unknown gate type").
- Custom gates that contradict classification baseline (e.g., per-increment Approval gates in a Type A plan) → flag as gap ("Custom gates exceed classification baseline expectations").

For each dimension:
- If complete: State "No gaps identified" or "Complete".
- If gaps exist: List each gap as a specific, actionable item.

---

## 7. Non-Goals / Forbidden Actions

This command must **NOT**:
- Suggest solutions or improvements to identified gaps; only list gaps
- Create structured output (templates, formatted documents) in chat except the executive summary
- Infer gaps that are not explicitly evident in the plan content
- Perform deep analysis beyond identifying missing elements
- Assume a task directory if none was provided; ask for task ID or path
- Transition tracker to any status other than `ready`
- Transition tracker when gaps exist
