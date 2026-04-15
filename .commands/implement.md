# Implement (Plan-Driven Execution) — v4

## 1. Identity

**Command Type:** Operative — Procedural / Execution

You are executing an implementation plan increment by increment, reading plan artifacts from the task directory. This command orchestrates a mandatory protocol: **read → analyze → understand → execute → feedback gate → next**. It ensures the developer has full visibility and control at every step.

**Skills referenced:** `rho-aias`, `incremental-decomposition`, `xcode-mcp` (conditional — iOS projects).

---

## 2. Invocation / Usage

Invocation:
- `/implement`
- `/implement` (with a self-review handoff in the chat opening context)

Usage notes:
- This command is intended to be used within `@dev` mode.
- It requires plan artifacts in TASK_DIR (`technical.plan.md`, `increments.plan.md`, `dor.plan.md`, `dod.plan.md`, and `specs.design.md` when present). MAY load `analysis.product.md` for product context.
- The command does NOT execute the entire plan autonomously. It executes **one increment at a time** and waits for user feedback before proceeding.
- `increments.plan.md` is the only plan artifact this command may update. It MUST NOT modify validation todos in `technical.plan.md`.
- **Review Resolution mode:** When the chat opening message contains a handoff snippet from `/self-review` (with findings such as blocking issues, major risks, or minor improvements), the command enters Review Resolution mode instead of plan-driven execution. See Phase 1-R in Section 6.

---

## 3. Inputs

This command may use **only** the following inputs:
- Plan artifacts from TASK_DIR loaded via **rho-aias** skill (Phases 0–3): `technical.plan.md`, `increments.plan.md`, `dor.plan.md`, `dod.plan.md`, `specs.design.md` (when present), `analysis.product.md` (when present)
- Self-review handoff snippet (from the chat opening context) — activates Review Resolution mode
- Chat context explicitly provided by the user
- Codebase state (files, dependencies, existing code)
- Service configs:
  - `aias-config/providers/knowledge-config.md`

Rules:
- All inputs must be explicit.
- TASK_DIR must be resolvable. If not, ask the user for the task ID.
- If plan artifacts cannot be found, ask the user to run `/blueprint` first.
- Do NOT invent plan content. Work only with what the plan provides.

---

## 4. Output Contract (Format)

This command produces **code changes** directly in the codebase (not a file artifact).

STATUS UPDATE (Phase 5 — after each increment)
- Update `status.md`: update `current_step` to `implement` (if not already set). Do NOT modify the `status` field — it remains `in_progress` as set by `/blueprint`.
- Append to `command_log`: `{command: /implement, started_at: <UTC>, ended_at: <UTC>}` — obtain timestamps via `date -u +%Y-%m-%dT%H:%M:%SZ`. See `reference.md` § Command Log for full rules.
- Run Phase 5c: sync non-synced artifacts to resolved knowledge provider. Phase 5c always publishes — it is NOT conditioned by plan classification. After each successful publish, inject TOC per resolved provider config (see **rho-aias** skill § Phase 5c).

Output is delivered in **phases**, each clearly communicated in chat:
- Phase 1 (Read): Confirmation of plan loaded
- Phase 2 (Analyze): Structured analysis summary
- Phase 3 (Understand): Comprehension confirmation with user gate
- Phase 4+ (Execute): Code changes per increment with feedback gates

---

## 5. Content Rules (Semantics)

- Output must be in **English**.
- Do **NOT** invent information or steps not in the plan.
- Do **NOT** skip increments or change their order.
- Do **NOT** proceed to the next increment without explicit user approval.
- Do **NOT** combine multiple increments into one execution.
- Apply the **incremental-decomposition** skill execution checklist when consuming increments (order, one-at-a-time, verify goal, update status).
- If the plan has ambiguities or gaps, raise them during the Analyze or Understand phase — do not guess.
- Follow all `@dev` mode rules (quality bar, feasibility checks, safeguards).
- **Review Resolution:** When the chat opening message contains a self-review handoff, convert findings into fix items ordered by severity (blocking → major → minor). Each fix item is executed as a mini-increment with the same gate protocol. Open questions / assumptions from the review MUST NOT be auto-executed — present them to the user for decision.
- **Full test suite mandatory:** Verification MUST use `RunAllTests`. Using `RunSomeTests` or any subset is **forbidden** during `/implement` verification. The full test suite MUST run after every increment to detect collateral impact on tests outside the modified scope.

---

## 6. Execution Protocol (Mandatory Order)

### Phase 1: READ

Follow the **rho-aias** skill loading protocol (Phases 0–3) to resolve TASK_DIR and load plan artifacts. Confirm to the user:
- Task ID and profile
- Number of increments found (from `increments.plan.md`)
- Current status (from `status.md`)

```
✓ Artifacts loaded from: <resolved_tasks_dir>/<TASK_ID>/
  Profile: <profile>
  Increments: <count>
  Classification: <minor|standard|critical|unset>
  Governance: <custom gates present | no custom gates | no governance section>
  Status: <status from status.md>
  Artifacts: <list of loaded artifacts>
```

Do NOT proceed to Phase 2 without completing Phase 1.

---

### Phase 1-R: REVIEW RESOLUTION (conditional)

**Activation:** The chat opening message contains a handoff snippet whose `COMMAND` resolves to `/implement` and whose `Context` or `Findings` block contains self-review findings (blocking issues, major risks, minor improvements).

When activated, this phase **replaces** Phases 2–4 with a review-driven execution loop. If the handoff also references plan artifacts in TASK_DIR (`increments.plan.md`), review findings take precedence — resolve all findings first, then resume plan-driven execution at Phase 2.

**Protocol:**

1. **Parse** findings from the handoff by severity.
2. **Present** summary to the user:
   ```
   REVIEW RESOLUTION:
     Source: self-review handoff
     Blocking: <N> items
     Major: <N> items
     Minor: <N> items
     Questions: <N> items (require user decision)
   ```
3. **Map** each finding to a concrete fix item (target file, expected change, rationale from the finding).
4. **Present questions** — If the review includes open questions or assumptions, present them to the user and wait for a decision before proceeding. Do NOT auto-resolve questions.
5. **Execute** each fix item as a mini-increment following the same protocol as Phase 4:
   - Announce → Implement fix → Report → Verify (build + `RunAllTests`) → Feedback gate.
   - Fix items execute in severity order: blocking first, then major, then minor.
6. **Completion** — After all fixes are applied:
   ```
   REVIEW RESOLUTION COMPLETE:
     Fixed: <N> items
     Skipped: <N> items (user decision)
     Verification: <last build + test result>

     Recommended next step:
     - @review + /self-review to validate fixes
   ```

Do NOT proceed to Phase 2 without completing Phase 1-R (when activated).

---

### Phase 2: ANALYZE

Analyze the plan structure and the current codebase state. Report:

1. **Increment summary** — List all increments with their names and goals (one line each).
2. **Dependency check** — Are the technical dependencies (SPM packages, modules, APIs) available?
3. **Codebase alignment** — Do the files to create/modify match the current codebase structure? Any conflicts?
4. **Design Specification** — If the plan includes a Design Specification section (design provider data), acknowledge it and note which increments will use it.
5. **Risk flags** — Any concerns, gaps, or ambiguities in the plan that could block execution.

6. **Governance resolution** — Read `classification` from `status.md` and `## Governance` section from `increments.plan.md`. Determine effective governance per the resolution flowchart:
   1. If `increments.plan.md` contains a `## Governance` section with a custom gate at a trigger point → custom gate takes **precedence** at that trigger point.
   2. Else, apply the classification baseline from `readme-commands.md`:
      - **Minor:** Feedback after each increment.
      - **Standard:** Feedback after each increment.
      - **Critical:** Approval gate before Increment 1; Feedback after each.
   3. Else (legacy — `status.md` has no `classification` field): Feedback after each increment.

```
ANALYSIS:
  Increments:
    1. <name> — <goal>
    2. <name> — <goal>
    ...
  Dependencies: <all available / missing: X, Y>
  Codebase: <aligned / conflicts: X>
  Design Spec: <present for N components / not present>
  Governance: <classification X, N custom gates / baseline only / legacy>
  Risks: <none / list>
```

Do NOT proceed to Phase 3 without completing Phase 2.

---

### Phase 3: UNDERSTAND

Confirm comprehension to the user. Present:

1. **Execution order** — The exact order in which increments will be executed.
2. **First increment preview** — What the first increment will do (goal, key changes, files affected).
3. **Assumptions** — Any assumptions made based on the plan or codebase analysis.
4. **Governance summary** — Effective governance resolved in Phase 2 (classification baseline, custom gates, or legacy).

Then fire the Ready gate.

#### Gate: Ready

**Type:** Confirmation
**Fires:** Phase 3, before executing any increment.
**Skippable:** No.

**Context output:**
Present execution readiness in chat:
- Increment 1 name, goal, and files
- Assumptions (or "none")
- Effective governance for this execution (baseline / custom / legacy)

**AskQuestion:**
- **Runtime compatibility:** If `AskQuestion` is unavailable, use the Text Gate Protocol from `readme-commands.md` with the same prompt, option ids, labels, and `allow_multiple` semantics.
- **Prompt:** "Ready to start with Increment 1: <name>. Proceed?"
- **Options:**
  - `proceed`: "Begin execution with Increment 1"
  - `adjust`: "Adjust the plan before starting"
  - `stop`: "Stop — do not execute"
- **allow_multiple:** false

**On response:**
- `proceed` → Check for pre-execution governance gates (see below), then proceed to Phase 4
- `adjust` → Apply corrections, return to context output and re-present gate
- `stop` → Report current state and halt

**Anti-bypass:** Inherits Gate Invocation Protocol. No additional rules.

#### Gate: Pre-Implementation Approval (conditional)

**Type:** Approval
**Fires:** After the Ready gate, before Increment 1, when governance requires it.
**Skippable:** No (when applicable).

**Trigger conditions (in precedence order):**
1. Custom gate at trigger "before Increment 1" in `## Governance` → fire the custom gate via AskQuestion (takes precedence).
2. Classification Critical baseline → fire this Approval gate.
3. Classification Minor/Standard baseline or legacy → skip (no approval needed).

**AskQuestion (baseline Critical):**
- **Prompt:** "Classification Critical — pre-implementation approval required. Approve execution of <count> increments?"
- **Options:**
  - `approve`: "Approve and begin execution"
  - `reject`: "Reject — return to planning"
- **allow_multiple:** false

**On response:**
- `approve` → Proceed to Phase 4 (Increment 1)
- `reject` → Report current state, suggest `/blueprint` for replanning

**Anti-bypass:** Inherits Gate Invocation Protocol. No additional rules.

---

### Phase 4: EXECUTE (per increment)

For each increment:

1. **Announce** the increment being executed:
   ```
   ▶ Executing Increment <N>: <name>
   ```

2. **Implement** the increment following:
   - The plan's steps in order
   - `@dev` mode quality bar (edge cases, error handling, named constants, Swift Testing)
   - Architecture alignment from the plan's DoR Technical
   - Design Specification data if available for this increment's UI components

3. **Report** completion:
   ```
   ✓ Increment <N> complete: <name>
     Changes: <summary of what was done>
     Files modified: <list>
     Files created: <list>
     Verification: <how to verify — from the plan's step verification>
   ```

4. **Update** the plan's frontmatter todo status from `pending` to `completed` for this increment (if the plan file is writable).
   - Update only the matching increment todo in `increments.plan.md`.
   - Do NOT create, remove, or modify validation todos in `technical.plan.md`.
   - Do NOT mutate `dod.plan.md`, `dor.plan.md`, or `technical.plan.md` as part of execution tracking.

5. **Verify** (conditional — requires `xcode-mcp`):
   - Resolve `tabIdentifier` via `XcodeListWindows` (once per execution session; reuse for subsequent increments).
   - Run `BuildProject(tabIdentifier)`.
   - If build succeeds, MUST call `RunAllTests(tabIdentifier)` — running a subset via `RunSomeTests` is **forbidden**. Changes in one increment may break tests outside the modified scope; only a full suite run catches this.
   - **Result interpretation:** Use `counts.failed` as the authoritative success signal. The `errors` field in individual test results is only present when errors exist — its absence means the test passed, not that it was skipped. If `counts.total > 0` and `counts.failed == 0`, the test suite passed.
   - Report result:
     ```
     ✓ Verification passed:
       Build: SUCCESS (<elapsed>)
       Tests: <passed> passed, 0 failed (<elapsed>)
     ```
   - If build or tests fail, fire the Verification Failure gate (see below).
   - If `xcode-mcp` is not available (non-iOS project), skip silently.
   - If `XcodeListWindows` fails (Xcode not open), warn and skip verification for this increment.

6. **Governance gate** — Resolve and fire the appropriate gate before proceeding to the next increment.

#### Gate: Inter-Increment Feedback

**Type:** Feedback
**Fires:** After each increment completion, before proceeding to the next.
**Skippable:** No.

**Resolution flowchart:**
1. Check `increments.plan.md` `## Governance` for custom gate at trigger "after Increment N" → fire custom gate via AskQuestion (takes precedence at this trigger point).
2. Else, apply classification baseline:
   - **Minor / Standard:** Fire this Feedback gate.
   - **Critical:** Fire this Feedback gate (Critical pre-implementation approval already handled in Phase 3).
3. Else (legacy — no `classification` in `status.md`): Fire this Feedback gate.

**Context output:**
Report increment completion (changes, files, verification).

**AskQuestion:**
- **Runtime compatibility:** If `AskQuestion` is unavailable, use the Text Gate Protocol from `readme-commands.md` with the same prompt, option ids, labels, and `allow_multiple` semantics.
- **Prompt:** "Increment <N> done. Next: Increment <N+1>: <name>. Continue?"
- **Options:**
  - `continue`: "Continue to next increment"
  - `adjust`: "Apply corrections before continuing"
  - `stop`: "Stop execution"
- **allow_multiple:** false

**On response:**
- `continue` → Proceed to next increment
- `adjust` → User provides corrections; apply them before continuing (see Feedback Handling below)
- `stop` → Report current state (completed increments, remaining increments, any in-progress work)

**Anti-bypass:** Inherits Gate Invocation Protocol. No additional rules.

#### Gate: Verification Failure (conditional)

**Type:** Decision
**Fires:** After step 5 (Verify), only when build or tests fail.
**Skippable:** No (when fired).

**Context output:**
Report verification result:
- Build status (success/failure + error count)
- Test status (passed/failed counts)
- Error details (file, line, message — from build log or test results)

**AskQuestion:**
- **Runtime compatibility:** If `AskQuestion` is unavailable, use the Text Gate Protocol from `readme-commands.md` with the same prompt, option ids, labels, and `allow_multiple` semantics.
- **Prompt:** "Verification failed after Increment <N>. <error summary>."
- **Options:**
  - `fix`: "Fix the issues" (agent applies corrections, then re-runs verification)
  - `retry`: "Re-run verification" (after manual user fixes outside the agent)
  - `skip`: "Skip verification and proceed to feedback"
  - `stop`: "Stop execution"
- **allow_multiple:** false

**On response:**
- `fix` → Agent attempts to fix reported errors, then re-runs build + tests. If still failing, re-fires this gate.
- `retry` → Re-runs build + tests without changes. If still failing, re-fires this gate.
- `skip` → Proceed to Inter-Increment Feedback gate (user accepts risk).
- `stop` → Report current state and halt.

**Anti-bypass:** Inherits Gate Invocation Protocol. No additional rules.

### Feedback Handling

When receiving corrections or feedback between or during increments:

**Operational adjustments** (fits within current increment scope):
- Acknowledge and integrate into the current increment.
- Note the adjustment in the increment completion summary.

**New scope** (work not covered by any existing increment):
- Pause execution and fire the New Scope gate.

#### Gate: New Scope

**Type:** Decision
**Fires:** During feedback handling, when the user's feedback introduces work not covered by any existing increment.
**Skippable:** No.

**Context output:**
Describe the new scope detected and explain why it falls outside the current plan.

**AskQuestion:**
- **Runtime compatibility:** If `AskQuestion` is unavailable, use the Text Gate Protocol from `readme-commands.md` with the same prompt, option ids, labels, and `allow_multiple` semantics.
- **Prompt:** "New scope detected outside current plan. How should this be handled?"
- **Options:**
  - `inline_now`: "Implement within current increment (small, self-contained additions only)"
  - `defer`: "Log for separate task and return to planning"
- **allow_multiple:** false

**On response:**
- `inline_now` → Execute immediately within the current increment. Use for small, self-contained additions that do not require formal planning.
- `defer` → Do not mutate other plan artifacts. Stop or pause execution and instruct the user to take the new scope back to planning (`/blueprint`, `/validate-plan`, or `/consolidate-plan`) so it can be captured outside `/implement`.

**Anti-bypass:** Inherits Gate Invocation Protocol. No additional rules.

**Systemic feedback** (reveals a pattern that should persist beyond this plan):
- Flag it: "This feedback may warrant a rule update — continuous-improvement will handle it."

---

### Plan Completion

When all increments are executed (or the user stops):

```
IMPLEMENTATION SUMMARY:
  Plan: <plan-name>
  Completed: <N> of <total> increments
  Remaining: <list or "none">
  Improvement margin: <list of optional items from plan, if any>

  Next steps:
  - /commit to commit changes (align messages with increment names)
  - @review + /self-review for local review
  - @review + /peer-review when reviewing a PR / third-party change
  - /pr for pull request description
  - /publish to archive artifacts via knowledge provider (when ready)
```

SERVICE RESOLUTION PSEUDOFLOW:

```
knowledge = resolve(knowledge-config) or abort(missing/invalid knowledge config)
```

---

## 7. Non-Goals / Forbidden Actions

This command must **NOT**:
- Execute the entire plan without feedback gates
- Skip or reorder increments
- Invent steps not in the plan
- Combine multiple increments into one
- Run `git push` or publish to any external service
- Modify files outside the scope defined by the plan
- Proceed past any phase without completing the previous one
- Continue after a feedback gate without user confirmation
- Run only a subset of tests during verification (always run the full suite via `RunAllTests`)
