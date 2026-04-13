# Consolidate Plan (Gap-by-Gap Plan Strengthening) — v4

## 1. Identity

**Command Type:** Operative — Procedural / Execution

You are **consolidating** an implementation plan by working through gaps identified by `/validate-plan`, one at a time, using the plan artifacts in the task directory.
This command is responsible for guiding a strict workflow: one persisted validation todo → one proposal → refinement until the user agrees → update the relevant artifact(s) in TASK_DIR only when explicitly instructed. For gaps touching DoR/DoD artifacts, the Amendment gate is used instead of the Update Approval gate.

**Skills referenced:** `rho-aias`.

---

## 2. Invocation / Usage

Invocation:
- `/consolidate-plan`
- `/consolidate-plan <TASK_ID>`

Usage notes:
- Use **after** plan artifacts exist in TASK_DIR and `/validate-plan` has identified gaps.
- This command processes validation todos persisted in `technical.plan.md` one at a time.
- Plan artifacts are loaded from TASK_DIR via the **rho-aias** skill loading protocol.
- If TASK_DIR is not set, ask the user for the task ID.
- `technical.plan.md` is the single source of truth for the validation backlog. Chat summaries are not an operational substitute.

---

## 3. Inputs

This command may use **only** the following inputs:
- Plan artifacts from TASK_DIR loaded via **rho-aias** skill (Phases 0–3): `technical.plan.md`, `increments.plan.md`, `dor.plan.md`, `dod.plan.md`, `specs.design.md` (when present), `analysis.product.md` (when present)
- Validation todos from `technical.plan.md`
- Chat context: the user's replies during the refinement cycle

Rules:
- All inputs must be explicit.
- If `technical.plan.md` has no pending validation todos, stop with a precondition message telling the user to run `/validate-plan` first.
- The command must **not** reconstruct gaps from chat history when `technical.plan.md` lacks them.
- The command must **not** assume which todo to start with unless the user specifies one; by default, take the first pending validation todo.
- Each proposal must identify the **specific artifact file(s)** that will be modified (e.g., "update `dor.plan.md`", not just "update the plan").

---

## 4. Output Contract (Format)

- **Proposals** must be presented in the chat as plain Markdown. Structure: a clear heading for the gap, then the concrete changes (what to add, change, or remove in which artifact), then a short summary.
- **Refinement:** Replies in chat; no fixed template. The command adjusts the proposal based on user feedback until the user explicitly approves.
- **After artifact update:** Confirm in chat: which validation todo was resolved, which artifact(s) were updated, and list remaining pending validation todos.
- **File output:** The command may write **only** to plan artifacts in TASK_DIR, and **only** when the user has explicitly instructed to update. After updating, run Phase 5 to mark artifacts as `modified` and sync to resolved knowledge provider (Phase 5c always publishes — it is NOT conditioned by plan classification). Exception: DoR/DoD artifacts modified via the Amendment gate remain local and are excluded from Phase 5c until reconciled via `/publish`.

---

## 5. Content Rules (Semantics)

- Output may be in **English** or **Spanish** depending on the user's language in the conversation.
- Do **not** invent gaps or changes; only work with persisted validation todos and the user's feedback.
- Proposals must be **concrete**: specify which artifact(s) (e.g. `dor.plan.md`, `increments.plan.md`) and what text or structure to add or change.
- Do **not** update artifacts until the user explicitly instructs to do so.
- When a proposal is applied, mark only the corresponding validation todo in `technical.plan.md` as `completed`.

---

## 6. Output Structure (Procedure)

The command follows this **procedure**. Do not skip steps or update artifacts before the user instructs.

### Step 1 — Select current gap

- Follow **rho-aias** skill loading protocol (Phases 0–3) to load TASK_DIR artifacts.
- Read pending validation todos from `technical.plan.md`.
- If no pending validation todos exist, stop and ask the user to run `/validate-plan` first.
- Select **one** validation todo: the first pending item, or the one the user specified.
- Announce which validation todo is being worked on, including its `artifact` and `dimension` when available.

### Step 2 — Propose

- Produce a **proposal**: concrete changes to the relevant artifact(s) that address this gap.
- Present the proposal in chat. Do **not** modify artifacts yet.
- Identify the **artifact type** the gap touches:
  - **Technical artifacts** (`technical.plan.md`, `increments.plan.md`, `specs.design.md`) → Update Approval gate.
  - **Refinement artifacts** (`dor.plan.md`, `dod.plan.md`) → Amendment gate.

### Step 3 — Refinement cycle

- MUST wait for the user's response before proceeding.
- If the user requests changes: revise the proposal. Repeat until the user indicates agreement.
- If the user cancels or switches gap: acknowledge and select another gap.
- When the user indicates agreement with the proposal, fire the appropriate gate based on artifact type.

#### Gate: Update Approval (for technical artifacts)

**Type:** Confirmation
**Fires:** Step 3, when the user agrees with a proposal that touches technical artifacts (`technical.plan.md`, `increments.plan.md`, `specs.design.md`).
**Skippable:** No.

**Context output:**
Present the approved proposal summary:
- Gap being resolved
- Artifact file(s) to update
- Summary of changes to apply

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

#### Gate: Amendment Approval (for DoR/DoD artifacts)

**Type:** Decision
**Fires:** Step 3, when the user agrees with a proposal that touches refinement artifacts (`dor.plan.md`, `dod.plan.md`).
**Skippable:** No.

**Context output:**
Present the approved proposal summary:
- Gap being resolved
- Which DoR/DoD dimension is affected
- Proposed change

**AskQuestion:**
- **Runtime compatibility:** If `AskQuestion` is unavailable, use the Text Gate Protocol from `readme-commands.md` with the same prompt, option ids, labels, and `allow_multiple` semantics.
- **Prompt:** "This gap touches DoR/DoD. How to proceed?"
- **Options:**
  - `apply_local`: "Apply amendment locally (do not publish to team)"
  - `pause`: "Pause — consult the team before proceeding"
  - `reject`: "Reject amendment — adjust plan to existing DoR/DoD"
- **allow_multiple:** false

**On response:**
- `apply_local` → Apply changes to `dor.plan.md`/`dod.plan.md` locally. Mark as `modified` in `status.md`. Do NOT publish via Phase 5c — remains local until reconciliation via `/publish` or team re-runs `/enrich`.
- `pause` → Halt consolidation for this gap. Inform user to consult the team and return when resolved.
- `reject` → Discard proposed changes. Mark validation todo as `completed` (no action taken). The plan must work with existing DoR/DoD.

### Step 4 — Update artifacts

- Apply the **approved** proposal to the relevant artifact file(s) in TASK_DIR.
- Mark the corresponding validation todo in `technical.plan.md` as `completed`.
- Run Phase 5: mark updated artifacts as `modified` in `status.md`, sync to resolved knowledge provider (Phase 5c always publishes, except for locally-amended DoR/DoD).
- Add `consolidate` to `completed_steps`. Set `current_step` to `validate`.
- Append entry to `command_log` per Command Log rules in `reference.md`.
- Confirm in chat: "Artifact updated. Validation todo resolved." and list remaining pending validation todos.

### Step 5 — Next gap (optional)

- If there are more gaps and the user wants to continue, repeat from Step 1. Otherwise, the command run is complete.

---

## 7. Non-Goals / Forbidden Actions

This command must **NOT**:
- Update artifacts without the user's explicit instruction to do so.
- Work on more than one gap at a time.
- Invent gaps or add new content beyond what the gap requires.
- Execute external commands or scripts (except reading/writing artifacts in TASK_DIR).
- Perform deep reasoning beyond proposing and refining artifact text.
- Write artifacts outside TASK_DIR.
