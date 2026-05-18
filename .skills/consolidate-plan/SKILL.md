---
name: consolidate-plan
description: "Merges multiple increment notes or partial plan artifacts into a single coherent plan artifact. Use when planning has produced fragmented or redundant plan files. Trigger terms: /consolidate-plan, merge plan, consolidate increments."
category: operative
disable-model-invocation: true
version: 2.1.0
---

# Consolidate Plan (Gap-by-Gap Plan Strengthening) — v5.1

## 1. Identity

**Command Type:** Operative — Procedural / Execution

You are **consolidating** an implementation plan by working through todos persisted by `/validate-plan` in `technical.plan.md` frontmatter, one at a time, using the plan artifacts in the task directory.
This command is responsible for guiding a strict workflow: one persisted todo → one proposal → refinement until the user agrees → update the relevant artifact(s) in TASK_DIR only when explicitly instructed. **v9.5+**: todos carry an explicit `kind` field (`validation | amendment_dor | amendment_dod`); `/consolidate-plan` is the SOLE resolver for all three kinds. Validation todos resolve in `technical.plan.md`; `amendment_dor` todos resolve by applying to `dor.plan.md` and removing the entry from `## Proposed DoR Amendments`; `amendment_dod` todos resolve analogously against `dod.plan.md` and `## Proposed DoD Amendments`. There is no separate Amendment gate — the Update Approval gate covers all kinds; routing-by-kind happens deterministically in Step 4.

**Skills referenced:** `rho-aias`.

---

## 2. Invocation / Usage

Invocation:
- `/consolidate-plan`
- `/consolidate-plan <TASK_ID>`

Usage notes:
- Use **after** plan artifacts exist in TASK_DIR and `/validate-plan` has identified gaps and/or registered amendment TODOs.
- This command processes todos persisted in `technical.plan.md` frontmatter one at a time, regardless of `kind` (`validation | amendment_dor | amendment_dod`).
- Plan artifacts are loaded from TASK_DIR via the **rho-aias** skill loading protocol.
- If TASK_DIR is not set, ask the user for the task ID.
- `technical.plan.md` is the single source of truth for the todo backlog. Chat summaries are not an operational substitute.
- **v9.5+ Amendment routing invariant**: `amendment_dor` todos MUST be applied only to `dor.plan.md`; `amendment_dod` todos MUST be applied only to `dod.plan.md`; mixing is FORBIDDEN. After applying an amendment, the corresponding entry in `## Proposed DoR Amendments` or `## Proposed DoD Amendments` in `technical.plan.md` body MUST be removed; once a Proposed section is empty, the heading itself MUST be removed.

---

## 3. Inputs

This command may use **only** the following inputs:
- Plan artifacts from TASK_DIR loaded via **rho-aias** skill (Phases 0–3): `technical.plan.md`, `increments.plan.md`, `dor.plan.md`, `dod.plan.md`, `specs.design.md` (when present), `analysis.product.md` (when present)
- Pending todos from `technical.plan.md` frontmatter (each with `kind`, `artifact`, `dimension`, `content`)
- Chat context: the user's replies during the refinement cycle

Rules:
- All inputs must be explicit.
- If `technical.plan.md` has no pending todos, stop with a precondition message telling the user to run `/validate-plan` first.
- The command must **not** reconstruct gaps from chat history when `technical.plan.md` lacks them.
- The command must **not** assume which todo to start with unless the user specifies one; by default, take the first pending todo (any `kind`).
- Each proposal must identify the **specific artifact file(s)** that will be modified (e.g., "update `dor.plan.md`", not just "update the plan"), derived deterministically from the todo's `kind` + `artifact` fields.

---

## 4. Output Contract (Format)

- **Proposals** must be presented in the chat as plain Markdown. Structure: a clear heading for the todo (showing `kind`, `artifact`, `dimension`), then the concrete changes (what to add, change, or remove in which artifact), then a short summary.
- **Refinement:** Replies in chat; no fixed template. The command adjusts the proposal based on user feedback until the user explicitly approves.
- **After artifact update:** Confirm in chat: which todo was resolved (including `kind`), which artifact(s) were updated, and list remaining pending todos.
- **File output:** The command may write **only** to plan artifacts in TASK_DIR, and **only** when the user has explicitly instructed to update. After updating, run Phase 5 to mark artifacts as `modified` and sync to resolved knowledge provider (Phase 5c fires only when a valid tracker ticket exists for TASK_ID — P1–P3 preconditions; see **rho-aias** skill § Phase 5c; after each successful publish, inject TOC per resolved provider config). **v9.5+**: there is no `apply_local` exclusion — DoR/DoD artifacts resolved via amendment TODOs participate in Phase 5c as normal `modified` artifacts.

---

## 5. Content Rules (Semantics)

- Output must be in **English**.
- Do **not** invent gaps or changes; only work with persisted todos and the user's feedback.
- Proposals must be **concrete**: specify which artifact(s) (e.g. `dor.plan.md`, `increments.plan.md`) and what text or structure to add or change, deterministically derived from the todo's `kind` + `artifact` fields.
- Do **not** update artifacts until the user explicitly instructs to do so.
- When a proposal is applied, mark only the corresponding todo in `technical.plan.md` as `completed`.

### Amendment routing invariant (v9.5+)

- `kind: validation` → resolve in the `artifact` named on the todo (typically `technical.plan.md`; MAY be `increments.plan.md`, `specs.design.md`, etc.).
- `kind: amendment_dor` → resolve in `dor.plan.md` at the dimension named on the todo. After applying, MUST remove the **entire multi-line bullet** (parent line + all sub-bullets) from `## Proposed DoR Amendments` in `technical.plan.md`. Applying to `dod.plan.md` is FORBIDDEN regardless of user intent.
- `kind: amendment_dod` → resolve in `dod.plan.md` at the criterion named on the todo. After applying, MUST remove the entire multi-line bullet from `## Proposed DoD Amendments` in `technical.plan.md`. Applying to `dor.plan.md` is FORBIDDEN regardless of user intent.
- After both Proposed sections are empty, the section headings MUST be removed from `technical.plan.md`.
- Backward compatibility: when a todo has no `kind` field, treat as `kind: validation` (matches v9.4 and earlier behavior). v9.5 single-line Proposed bullets (without sub-bullets) are parsed as a single-line shape; everything works identically.

### Inline confirmation marker (v9.6+)

When proposing changes for an `amendment_dor` or `amendment_dod` todo (Step 2), `/consolidate-plan` MUST:

1. Locate the corresponding bullet in `technical.plan.md` body (matched by exact-string on the dimension/criterion captured in the todo's `dimension` field).
2. Parse sub-bullets under the parent bullet line. Each sub-bullet is detected by exactly two leading spaces followed by `- `. Recognized sub-fields (case sensitive):
   - `**Proposed resolution**: <value>` — agent's proposed value (always optional but typical in v9.5+ artifacts).
   - `**Inline confirmation**: <value> (YYYY-MM-DD)` — user's inline answer captured during `/blueprint` (v9.6+). Canonical regex: `^\s\s-\s+\*\*Inline confirmation\*\*:\s+(?P<value>.+?)\s+\((?P<date>\d{4}-\d{2}-\d{2})\)\s*$` (per `aias/contracts/readme-artifact.md` v2.3 § Refinement Artifact Mutation Invariant).
3. Resolve the **default proposed value** for the Update Approval gate by precedence:
   - If `**Inline confirmation**:` exists, use its captured value as the default (the user already answered this gap inline during `/blueprint`; honor that decision unless the user overrides at the gate).
   - Else if `**Proposed resolution**:` exists, use its value as the default.
   - Else (legacy bullets, no sub-fields), fall back to the todo's `content` field and let the user provide the resolution at the gate.
4. The dev MAY override the default during refinement (Step 3); the marker provides a default, not a binding decision.
5. If the bullet uses non-canonical inline confirmation phrasing (e.g., parentheses inverted, missing date, wrong delimiters), the parser MUST treat the sub-bullet as descriptive context (not as a marker) and fall through to the `**Proposed resolution**:` default. Emit an advisory in chat: `Inline confirmation marker for <dimension> did not match canonical regex; falling back to proposed resolution. See readme-artifact.md v2.3 § Inline confirmation marker for canonical format.`

### Discretion clarifications (v9.6+)

- **Team notification is dev discretion.** `/consolidate-plan` does NOT automatically post tracker comments, mentions, or notifications when amendments are applied. The dev decides whether to share the resolution (e.g., add a Jira comment after `/consolidate-plan` finishes). The skill's responsibility ends at the artifact mutation + `command_log` audit; cross-team coordination is out of scope.
- **Tracker freshness is dev discretion.** `/consolidate-plan` does NOT re-read the tracker before applying amendments. If the dev suspects tracker drift since the last `/enrich`, the recommended workflow is to run `/enrich --refresh` first (v9.6+) to reconcile then run `/consolidate-plan`. Combining drift detection with amendment resolution in a single command was explicitly rejected during v9.6 design — they serve different governance surfaces (drift vs. resolution) and merging them would couple the two gates.
- **Automatic tracker writes are FORBIDDEN.** Even when an `amendment_dor` resolves a tracker-derived gap (e.g., NFR added in the description after `/enrich`), `/consolidate-plan` MUST NOT write back to the tracker. The dev decides whether to push the resolution via `/enrich --fields` or a manual edit.

---

## 6. Output Structure (Procedure)

The command follows this **procedure**. Do not skip steps or update artifacts before the user instructs.

### Step 1 — Select current todo

- Follow **rho-aias** skill loading protocol (Phases 0–3) to load TASK_DIR artifacts.
- Read pending todos from `technical.plan.md` frontmatter.
- If no pending todos exist, stop and ask the user to run `/validate-plan` first.
- Select **one** todo: the first pending item, or the one the user specified.
- Announce which todo is being worked on, including its `kind`, `artifact`, and `dimension` when available.

### Step 2 — Propose

- Produce a **proposal**: concrete changes to the relevant artifact(s) that address this todo.
- Present the proposal in chat. Do **not** modify artifacts yet.
- The target artifact is derived deterministically from the todo's `kind` + `artifact` fields (no artifact-type branching in the proposal phase):
  - `kind: validation` → target is the `artifact` named on the todo.
  - `kind: amendment_dor` → target is `dor.plan.md` (plus `technical.plan.md` body bullet removal in Step 4).
  - `kind: amendment_dod` → target is `dod.plan.md` (plus `technical.plan.md` body bullet removal in Step 4).

### Step 3 — Refinement cycle

- MUST wait for the user's response before proceeding.
- If the user requests changes: revise the proposal. Repeat until the user indicates agreement.
- If the user cancels or switches todo: acknowledge and select another todo.
- When the user indicates agreement with the proposal, fire the Update Approval gate (single gate for all `kind` values; routing-by-kind happens in Step 4).

#### Gate: Update Approval

**Type:** Confirmation
**Fires:** Step 3, when the user agrees with a proposal (any `kind`).
**Skippable:** No.

**Context output:**
Present the approved proposal summary:
- Todo being resolved (`kind`, `artifact`, `dimension`)
- Artifact file(s) to update
- Summary of changes to apply
- For `amendment_dor` / `amendment_dod`: explicit note that the corresponding entry in `## Proposed DoR Amendments` or `## Proposed DoD Amendments` will be removed from `technical.plan.md`; if this is the last entry in the section, the heading itself will be removed.

**AskQuestion:**
- **Runtime compatibility:** If `AskQuestion` is unavailable, use the Text Gate Protocol from `readme-commands.md` with the same prompt, option ids, labels, and `allow_multiple` semantics.
- **Prompt:** "Apply this proposal to <artifact-file(s)>?"
- **Options:**
  - `apply`: "Apply changes to artifact(s)"
  - `revise`: "Revise the proposal further"
- **allow_multiple:** false

**On response:**
- `apply` → Proceed to Step 4
- `revise` → Return to refinement cycle

**Anti-bypass:** Inherits Gate Invocation Protocol. No additional rules.

### Step 4 — Update artifacts (routing by `kind`)

For **all** todos, apply the approved proposal and update `status.md`. Routing by `kind` (v9.5+):

- `kind: validation`:
  1. Apply the proposal to the artifact named on the todo (`technical.plan.md`, `increments.plan.md`, `specs.design.md`, etc.).
  2. Mark the affected artifact as `modified` in `status.md` artifacts map.
- `kind: amendment_dor`:
  1. Apply the proposal to `dor.plan.md` at the dimension named on the todo.
  2. Remove the **entire multi-line bullet** (parent line + ALL sub-bullets, including `**Proposed resolution**:` and `**Inline confirmation**:` markers) from `## Proposed DoR Amendments` in `technical.plan.md` body.
  3. If `## Proposed DoR Amendments` is now empty, remove the heading from `technical.plan.md`.
  4. Mark `dor.plan.md` AND `technical.plan.md` as `modified` in `status.md` artifacts map.
- `kind: amendment_dod`:
  1. Apply the proposal to `dod.plan.md` at the criterion named on the todo.
  2. Remove the **entire multi-line bullet** (parent line + ALL sub-bullets) from `## Proposed DoD Amendments` in `technical.plan.md` body.
  3. If `## Proposed DoD Amendments` is now empty, remove the heading from `technical.plan.md`.
  4. Mark `dod.plan.md` AND `technical.plan.md` as `modified` in `status.md` artifacts map.

Then, for any `kind`:

- Mark the corresponding todo in `technical.plan.md` frontmatter as `completed`.
- Run Phase 5: mark updated artifacts as `modified` in `status.md`, sync to resolved knowledge provider (Phase 5c fires only when a valid tracker ticket exists for TASK_ID — P1–P3 preconditions; after each successful publish, inject TOC per resolved provider config). **v9.5+**: DoR/DoD modifications via amendment TODOs participate in Phase 5c as normal `modified` artifacts (no `apply_local` exclusion).
- Add `consolidate` to `completed_steps`. Set `current_step` to `validate`.
- Append to `command_log`: `{command: /consolidate-plan, started_at: <UTC>, ended_at: <UTC>}` — obtain timestamps via `date -u +%Y-%m-%dT%H:%M:%SZ`. See `reference.md` § Command Log for full rules.
- Confirm in chat: "Artifact updated. Todo resolved (`kind: <kind>`)." and list remaining pending todos.

### Step 5 — Next todo (optional)

- If there are more pending todos (any `kind`) and the user wants to continue, repeat from Step 1. Otherwise, the command run is complete.

---

## 7. Non-Goals / Forbidden Actions

This command must **NOT**:
- Update artifacts without the user's explicit instruction to do so.
- Work on more than one todo at a time.
- Invent gaps or add new content beyond what the todo requires.
- Apply an `amendment_dor` todo to `dod.plan.md`, or an `amendment_dod` todo to `dor.plan.md` (routing invariant, v9.5+).
- Leave a Proposed Amendment bullet in `technical.plan.md` body after a corresponding amendment todo has been completed.
- Re-introduce the legacy combined section `## Proposed DoR/DoD Amendments` (FORBIDDEN since v9.5).
- Execute external commands or scripts (except reading/writing artifacts in TASK_DIR).
- Perform deep reasoning beyond proposing and refining artifact text.
- Write artifacts outside TASK_DIR.

---

## 8. Self-Verification Checklist

- [ ] Consolidation updates were written only to intended plan artifacts.
- [ ] `status.md` / `command_log` updates were applied when state changed.
- [ ] No out-of-scope files were modified.
- [ ] Terminal state line was emitted with canonical state token.

## 9. Halt Discipline

- Pause only at declared gates/preconditions/blockers.
- Avoid ad-hoc "continue?" pauses between deterministic steps.
- If blocked, report blocker and required resume input.

## Terminal State Emission

`[STATE: completed | partial | blocked | failed]` + one-line summary is mandatory.

## Invocation Mode Detection

- Standalone default.
- Pipeline mode MAY be inferred from `--from-pipeline`, `--invoked-by`, or predecessor evidence in `status.md`.
- Detection MUST NOT change semantic consolidation output.
