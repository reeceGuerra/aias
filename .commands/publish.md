# Publish (Task Closure + Knowledge Archive) — v4

## 1. Identity

**Command Type:** Type B — Procedural / Execution

You are **closing a task** by performing a safety-net sync of all artifacts to the configured knowledge provider, generating a Plan Delta artifact/page, marking the task as completed, and posting a closure comment through the configured tracker provider when available. This is a **closure-only** command — progressive publishing happens automatically during command execution for Type B/C tasks (Phase 5c of the **rho-aias** skill loading protocol, classification-gated). `/publish` exists as the final step to ensure everything is archived and the task is formally closed. **`/publish` bypasses the classification gate** — it always executes full knowledge sync regardless of classification, making it the explicit override for Type A tasks that the user wants to archive.

**Skills referenced:** `rho-aias`.

---

## 2. Invocation / Usage

Invocation:
- `/publish`
- `/publish <TASK_ID>`

Usage notes:
- This command is **mode-agnostic** — it can be invoked from any mode or chat session.
- It is intended to be used **after** implementation, PR creation, and any review cycles are complete.
- It is the standard closure step for Type B and Type C plans. Type A plans typically use `/report` or `/brief` instead, but `/publish` can be used to force knowledge archiving for any classification.
- Safe to run multiple times — all operations are idempotent.
- Does NOT transition tracker status to DONE (that is Product's responsibility).

---

## 3. Inputs

This command may use **only** the following inputs:
- All artifacts from TASK_DIR loaded via **rho-aias** skill (Phases 0–3)
- `status.md` for artifact sync map, task_id, and current state
- Plan artifacts (`*.plan.md`) and implementation state (`git diff` if available) for Plan Delta generation
- Service configs:
  - `aias-providers/knowledge-config.md`
  - `aias-providers/tracker-config.md`
- Chat context explicitly provided by the user

Rules:
- TASK_DIR must be resolvable. If not, ask the user for the task ID.
- All artifacts in TASK_DIR are candidates for publishing.

---

## 4. Output Contract (Format)

### Gate: Publish Confirmation

**Type:** Confirmation
**Fires:** Before executing the publish pipeline (Step 1).
**Skippable:** No.

**Context output:**
Present publish summary in chat:
- Task ID and current status
- Artifact count to sync (artifacts with status `created` or `modified`)
- Target knowledge provider and namespace
- Whether Plan Delta will be generated
- Whether tracker closure comment will be posted

**AskQuestion:**
- **Prompt:** "Publish <count> artifacts for <TASK_ID> to knowledge provider and close task?"
- **Options:**
  - `publish`: "Publish artifacts and close task"
  - `cancel`: "Cancel — do not publish"
- **allow_multiple:** false

**On response:**
- `publish` → Proceed to Step 1 (Safety Net Sync)
- `cancel` → Abort. Report current state without changes

**Anti-bypass:** Inherits Gate Invocation Protocol. No additional rules.

This command executes four sequential steps:

### Step 1: Safety Net Sync (classification gate bypassed)

This step always executes full knowledge sync **regardless of classification** — `/publish` is the explicit override that ensures all artifacts reach the knowledge provider even for Type A tasks.

Resolve the knowledge provider from `aias-providers/knowledge-config.md`:
- If config exists and is valid, use `active_provider` + `skill_binding` + provider parameters.
- If config is missing, invalid, or unresolvable, abort and request provider configuration.

Apply generic knowledge sync algorithm:
- Resolve target hierarchy/namespace for `<TASK_ID>` using provider parameters.
- For each artifact marked `created` or `modified`, perform provider-specific upsert.
- Mark artifact as `synced` on success.
- Keep artifact state unchanged on failure and continue (non-blocking).

Read `status.md` artifacts map. For each artifact with sync status `created` or `modified`:
- For `created` artifacts: create or locate target artifact/page and publish the **full Markdown content** of the artifact file.
- For `modified` artifacts: locate existing artifact/page and update with the **full Markdown content** of the artifact file.
- Never summarize, truncate, or abbreviate artifact content.
- Set artifact sync status to `synced` on success.
- **Idempotent:** safe to run multiple times. Updates existing artifacts/pages, never duplicates.

Provider adapter is determined exclusively by resolved `knowledge-config`.

### Step 2: Plan Delta

Generate `delta.publish.md` comparing planned artifacts vs actual implementation:
- **Planned and implemented:** Increments completed as planned.
- **Modified during implementation:** Increments that diverged from the plan.
- **Unplanned additions:** Work done that was not in the original plan.
- **Deferred or dropped:** Planned work not completed.

Write `delta.publish.md` to TASK_DIR and publish it as a child artifact/page in the resolved knowledge provider.

### Step 3: Closure

- Set all artifacts to `synced` in `status.md`.
- Update the knowledge parent page/dashboard with a completion summary.
- Set `status: completed` and `completed: <today's date>` and `published: <today's date>` in `status.md`.
- Set `current_step: null`.

### Step 4: Tracker Comment

Resolve tracker provider from `aias-providers/tracker-config.md`.
If tracker config is missing, invalid, or unresolvable, abort tracker comment and request provider configuration.

Post a closure comment on the ticket only when the resolved tracker provider supports comments and `task_id` is valid for that provider:
"Task archived. All artifacts published to knowledge provider: `<parent_page_link>`"

### End-of-Response Confirmation

```
PUBLISH COMPLETE:
  Task: <TASK_ID>
  Artifacts synced: <count>
  Plan Delta: generated
  Knowledge target: <parent_page_link>
  Tracker comment: posted | skipped (no ticket)
  Status: completed
```

SERVICE RESOLUTION PSEUDOFLOW:

```
resolveService(category):
  if service config exists and is valid:
    return active_provider, skill_binding, parameters
  abort and request provider configuration
```

KNOWLEDGE PROVIDER EXECUTION PSEUDOFLOW:

```
knowledge = resolve(knowledge-config) or abort(missing/invalid knowledge config)
for artifact in status.artifacts where sync in {created, modified}:
  upsertArtifact(knowledge, task_id, artifact)
  if success:
    markSynced(artifact)
```

---

## 5. Content Rules (Semantics)

- Output must be in **English**.
- Do **NOT** invent information for the Plan Delta — compare only what exists in plan artifacts vs available git history.
- If no git diff is available, generate a simplified Plan Delta based on artifact presence.
- Apply the **technical-writing** skill patterns: Conciseness.

---

## 6. Internal Execution Model

### Phase 0–3: Standard Loading

Follow the **rho-aias** skill loading protocol to resolve TASK_DIR and load all artifacts.

### Phase 4: Execution

1. **Safety net sync** (Step 1 above).
2. **Plan Delta generation** (Step 2 above).
3. **Closure** (Step 3 above).
4. **Tracker comment** (Step 4 above).

### Phase 5: Final Status Update

- All artifacts marked `synced`.
- `status.md` set to `completed`.
- No further Phase 5c sync needed (already done in Step 1).

### Phase 6: No Tracker Transition

`/publish` does NOT trigger a tracker status transition. It only posts an optional closure comment through the resolved tracker provider. Final transition to `DONE` remains Product's responsibility.

---

## 7. Non-Goals / Forbidden Actions

This command must **NOT**:
- Transition tracker to `DONE` or any other status
- Modify implementation code or repository files
- Create new artifacts beyond `delta.publish.md`
- Execute git commands beyond reading diff for Plan Delta
- Proceed without a resolvable TASK_DIR
- Delete or remove any artifacts
- Overwrite artifact content (only publish and update sync status)
