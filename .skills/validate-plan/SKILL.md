---
name: validate-plan
description: "Validates an existing plan artifact for completeness, governance compliance, and Plan Classification correctness. Use before /implement to catch planning gaps. Trigger terms: /validate-plan, validate plan, plan validation, check plan."
category: operative
disable-model-invocation: true
version: 2.1.0
---

# Validate Plan (Plan Alignment Validation) — v6.1

## 1. Identity

**Command Type:** Operative — Procedural / Execution

You are validating the **alignment and completeness** of an implementation plan against the DoR/DoD from refinement.
This command is responsible for analyzing plan artifacts in the task directory, verifying that the technical plan aligns with the DoR/DoD, identifying gaps across completeness dimensions, and registering DoR/DoD amendment proposals from `/blueprint` as `kind: amendment_dor` / `kind: amendment_dod` TODOs in `technical.plan.md` for `/consolidate-plan` to resolve. **v9.5+**: there is no Amendment Approval gate; `/validate-plan` does NOT decide or apply amendments — it only registers them as TODOs.

**Skills referenced:** `rho-aias`.

---

## 2. Invocation / Usage

Invocation:
- `/validate-plan`

Usage notes:
- This command is intended to be used **after** plan artifacts have been created (via `/blueprint` command).
- It analyzes the plan artifacts in TASK_DIR to identify missing elements and verify alignment with DoR/DoD.
- The output is raw, unstructured data listing gaps by category.
- **v9.5+ Amendment processing**: when `technical.plan.md` contains `## Proposed DoR Amendments` and/or `## Proposed DoD Amendments`, each entry is registered as a TODO in the `technical.plan.md` frontmatter with `kind: amendment_dor` or `kind: amendment_dod` (see § Phase: Process Proposed Amendments). NO Amendment Approval gate is presented — `/validate-plan` does not decide or apply amendments. `/consolidate-plan` v2.1.0+ is the resolver.
- **v9.6+ Multi-line bullet parsing**: bullets now follow a multi-line shape with optional `**Proposed resolution**:` and `**Inline confirmation**:` sub-fields. The TODO `content` captures only the parent line; sub-fields stay in the body for `/consolidate-plan` to read (see § Register amendments as TODOs).
- **v9.5+ Legacy hard-fail**: if `technical.plan.md` contains the legacy combined section `## Proposed DoR/DoD Amendments`, `/validate-plan` MUST hard-fail with explicit manual-split instructions (see § Phase: Process Proposed Amendments).
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
- Each todo MUST represent exactly one unresolved item (validation gap OR amendment) and MUST include:
  - `id`
  - `content`
  - `status: pending`
  - `kind` — one of the closed enum `validation | amendment_dor | amendment_dod` (v9.5+, see `aias/.skills/rho-aias/reference.md` § Todo `kind` enum). When `kind` is absent, treat as `validation` for backward compatibility.
  - `artifact` — the target artifact the todo resolves against (`technical.plan.md` for `validation`; `dor.plan.md` for `amendment_dor`; `dod.plan.md` for `amendment_dod`).
  - `dimension` — for `validation`: the validation dimension (Investigation, Definition Alignment, Planning, Detailing, Refinement, Classification, Governance); for `amendment_dor` / `amendment_dod`: the DoR/DoD dimension name (e.g., "Functional", "Non-Functional", "Test criteria").
- The Markdown body of `technical.plan.md` remains the human-readable technical plan. Validation todos and amendment todos live only in frontmatter.
- When no gaps and no amendments exist, `technical.plan.md` MUST NOT retain stale pending todos. The backlog should be empty or fully completed.

### Phase: Process Proposed Amendments (v9.5+)

Run this phase BEFORE the Validation Result gate.

#### Hard fail — legacy single-block

If `technical.plan.md` contains the legacy combined section heading `## Proposed DoR/DoD Amendments`, MUST abort immediately and emit the following message verbatim:

```
Legacy single-block detected: ## Proposed DoR/DoD Amendments

The amendments model changed in v9.5. Single-block sections are no
longer supported. Before continuing:
  1. Open technical.plan.md
  2. Manually split the existing block into:
       ## Proposed DoR Amendments
       ## Proposed DoD Amendments
     classifying each item by its target artifact.
  3. Re-run /validate-plan.

See aias/docs/QUICKSTART.md § Upgrading from v9.4 to v9.5 for examples.
```

Terminal state on hard-fail: `[STATE: blocked]` with summary `legacy single-block detected; manual split required before continuing`. MUST NOT auto-split. MUST NOT continue validation.

#### Register amendments as TODOs

When the canonical split sections are present in `technical.plan.md` (`## Proposed DoR Amendments` and/or `## Proposed DoD Amendments`):

1. **Bullet parsing (v9.6+ multi-line shape, v9.5 backward compatible):** Each bullet is a parent line followed by zero or more two-space-indented sub-bullets. The parent line has shape `- **<Dimension>**: <gap description>.` (terminating period optional). Sub-bullets MAY include:
   - `- **Proposed resolution**: <value>` (v9.5+, optional in v9.6+)
   - `- **Inline confirmation**: <value> (YYYY-MM-DD)` (v9.6+, optional — see `aias/contracts/readme-artifact.md` v2.3 § Refinement Artifact Mutation Invariant for canonical format and regex)
   - Other free-form sub-bullets (treated as descriptive context; preserved in body, not parsed)
2. For each bullet:
   - **Extract `dimension`** from the parent line's `**<Dimension>**:` header (exact-string capture, case sensitive).
   - **Extract `content`** as the parent line text only (dimension + gap description, normalized to a single-line string for the TODO `content` field). Sub-bullets MUST NOT be appended to `content` — they remain in the body for `/consolidate-plan` to read.
   - If the item is in `## Proposed DoR Amendments`: append a TODO to `technical.plan.md` frontmatter with `kind: amendment_dor`, `artifact: dor.plan.md`, `dimension: <captured>`, `content: <parent line only>`, `status: pending`.
   - If the item is in `## Proposed DoD Amendments`: append a TODO with `kind: amendment_dod`, `artifact: dod.plan.md`, otherwise identical.
3. **Backward compatibility (v9.5 single-line bullets):** When a bullet has no sub-bullets and its parent line includes inline `**Proposed resolution**:` text (the v9.5 shape), the entire parent line is captured into `content` verbatim. The TODO `dimension` is still extracted from the leading `**<Dimension>**:` header. No upgrade migration is required — `/validate-plan` v2.1.0+ parses both shapes.
4. Mark `technical.plan.md` as `modified` in `status.md` artifacts map.
5. Continue with normal gap detection (§ 6 Output Structure). Amendment TODOs and validation TODOs may coexist in the same frontmatter.

`/validate-plan` MUST NOT apply amendments. MUST NOT remove the Proposed sections from the body. MUST NOT remove or modify the `**Inline confirmation**:` sub-field. MUST NOT decide which amendments to accept. Resolution is owned exclusively by `/consolidate-plan` v2.1.0+.

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
- When plan passes and gate confirmed AND no pending amendments remain: update `status.md` — add `validate` to `completed_steps`, set `current_step` to `implement`. Do NOT modify the `status` field (it remains `in_progress` as set by `/blueprint`).
- When validation gaps OR amendment TODOs exist: set `current_step` to `consolidate` and mark `technical.plan.md` as `modified` in `status.md`.
- Run Phase 5c: sync non-synced artifacts to resolved knowledge provider. Phase 5c fires only when a valid tracker ticket exists for TASK_ID (P1–P3 preconditions; see **rho-aias** skill § Phase 5c). If preconditions are not met, skip silently — artifacts remain in created/modified state for `/publish` to reconcile. After each successful publish, inject TOC per resolved provider config. **v9.5+**: `dor.plan.md` and `dod.plan.md` are NOT excluded from Phase 5c by `/validate-plan` — that exclusion belonged to the retired `apply_local` flow. `/validate-plan` v2.0.0+ never mutates DoR/DoD; `/consolidate-plan` is the only command that applies amendments and marks them as `modified`.

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
- Classification Critical without a `## Governance` section in `increments.plan.md` → flag as gap ("Critical requires a Governance section with ≥1 Approval gate").
- `## Governance` section present with gate types outside the taxonomy (Confirmation, Decision, Feedback, Approval) → flag as gap ("Unknown gate type").
- Classification Critical with `## Governance` but zero Approval gates → flag as gap ("Critical Governance requires ≥1 Approval gate").
- Classification Minor with any `## Governance` section present → flag as gap ("Minor MUST NOT have a Governance section. Escalate classification or remove.").

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
- Apply, decide, or remove DoR/DoD amendments (v9.5+ — `/validate-plan` only registers them as TODOs; `/consolidate-plan` is the resolver)
- Auto-split the legacy combined `## Proposed DoR/DoD Amendments` section into the canonical split sections (v9.5+ — this is a hard-fail condition; manual split is the only supported migration path)
- Mutate `dor.plan.md` or `dod.plan.md`

---

## 8. Self-Verification Checklist

- [ ] Validation output/gaps reflect current TASK_DIR artifact state.
- [ ] Any `status.md` / `command_log` update was applied when state changed.
- [ ] No out-of-scope file modifications were introduced.
- [ ] Terminal state line was emitted with canonical state token.

## 9. Halt Discipline

- Pause only at declared gates/preconditions/blockers.
- Avoid ad-hoc pauses between deterministic validation phases.
- If blocked, report blocker and required resume input.

## Terminal State Emission

`[STATE: completed | partial | blocked | failed]` + one-line summary is mandatory.

## Invocation Mode Detection

- Standalone default.
- Pipeline mode MAY be inferred from `--from-pipeline`, `--invoked-by`, or predecessor evidence in `status.md`.
- Detection MAY skip duplicate already-resolved chain prompts without changing validation semantics.
