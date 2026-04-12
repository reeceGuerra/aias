# PR Draft (VCS Provider) — v3

## 1. Identity

**Command Type:** Operative — Procedural / Execution

You are generating a **pull request description** for this repository using the configured VCS provider.
This command is responsible for formatting validated implementation context into a review-ready PR description, including a Plan Delta section that compares planned artifacts against actual implementation. After PR creation, it triggers the configured tracker transition to review state.

**Skills referenced:** `rho-aias`, `technical-writing`.

---

## 2. Invocation / Usage

Invocation:
- `/pr` — create the PR (resolves base branch via gate if not provided)
- `/pr <branch>` — create the PR against `<branch>` as base; the **current local branch** is the head.
- `/pr --dry` — generate the PR description in chat without creating (dry-run)
- `/pr --update` — update an existing PR description with the latest context.

Usage notes:
- This command is intended to be used **after** implementation is complete (post-dev, MAY be post-review).
- By default, `/pr` creates the PR via the resolved VCS provider. Use `--dry` to only preview the description in chat.
- Reads plan artifacts from TASK_DIR to generate the Plan Delta section.
- After PR creation, this command is the canonical owner of tracker transition `in_progress` -> `in_review`.
- If unpublished artifacts exist, shows a `/publish` nudge.

---

## 3. Inputs

This command may use **only** the following inputs:
- Plan artifacts from TASK_DIR loaded via **rho-aias** skill (Phases 0–3)
- Chat context explicitly provided by the user
- Output from a prior reasoning step (e.g. `@planning`, `@dev`, `@review`)
- Diffs or file lists explicitly provided by the user
- `git diff` against the base branch for Plan Delta generation
- Service configs:
  - `aias-config/providers/knowledge-config.md`
  - `aias-config/providers/vcs-config.md`
  - `aias-config/providers/tracker-config.md`

Rules:
- Inputs must be explicit.
- Do **NOT** infer changes that are not present in the provided context.
- If TASK_DIR is available, load artifacts and generate Plan Delta.

---

## 4. Output Contract (Format)

- The response **MUST** be returned as **a single Markdown code block** using ```markdown.
- **NO text** is allowed outside the code block (except the /publish nudge and tracker sync report after the code block).
- The code block **MUST start** with a Markdown heading (`#` or `##`).
- Only one code block is allowed.

### Gate: Base Branch Resolution (conditional)

**Type:** Input
**Fires:** When `/pr` is invoked without a base branch AND the base cannot be inferred from the repository default branch via the VCS provider.
**Skippable:** No.

**Resolution logic:**
1. If the user provided `<branch>`, use it as base — skip this gate.
2. If not, attempt to infer the default branch from the repository via the resolved VCS provider.
3. If inference fails, fire this gate.

**AskQuestion:**
- **Runtime compatibility:** If `AskQuestion` is unavailable, use the Text Gate Protocol from `readme-commands.md` asking the user to provide the base branch name as free text.
- **Prompt:** "Base branch not specified and could not be inferred. Which branch should this PR target?"
- **Options:** Free-text input (the user writes the branch name).

**On response:**
- Use the provided branch name as the base and proceed to the PR Confirmation gate.

**Anti-bypass:** Inherits Gate Invocation Protocol. No additional rules.

### Gate: PR Confirmation

**Type:** Confirmation
**Fires:** Before creating or updating a PR. Does NOT fire in `--dry` mode.
**Skippable:** No.

**Context output:**
Present PR summary in chat:
- PR title (draft)
- Base branch and head branch
- Increment count and plan delta highlights (if TASK_DIR available)
- Action: create vs update

**AskQuestion:**
- **Runtime compatibility:** If `AskQuestion` is unavailable, use the Text Gate Protocol from `readme-commands.md` with the same prompt, option ids, labels, and `allow_multiple` semantics.
- **Prompt:** "Create PR against <base-branch> with the description above?"
- **Options:**
  - `create`: "Create the pull request"
  - `adjust`: "Adjust the description before creating"
- **allow_multiple:** false

**On response:**
- `create` → Proceed with PR creation via resolved VCS provider
- `adjust` → Apply corrections, return to context output and re-present gate

**Anti-bypass:** Inherits Gate Invocation Protocol. No additional rules.

PLAN DELTA (when TASK_DIR is available):
- Compare plan artifacts (`increments.plan.md`, `technical.plan.md`) against `git diff` to identify:
  - Planned work that was implemented as described
  - Planned work that was modified during implementation
  - Unplanned work that was added
  - Planned work that was deferred or dropped
- Include the Plan Delta as a section in the PR body (see template).

TRACKER SYNC (Phase 6 — after PR creation):
- After PR is created AND `task_id` in `status.md` is valid for the resolved tracker provider:
  - Resolve tracker provider from `aias-config/providers/tracker-config.md`.
  - Transition canonical tracker status from `in_progress` -> `in_review` using provider mapping.
  - If tracker config is missing, invalid, or unresolvable: abort tracker sync and request provider configuration.
  - Report transition result after the code block.

STATUS UPDATE (Phase 5):
- Update `status.md`: set `status: in_review`, add `pr` to `completed_steps`, set `current_step` to `closure`.
- Run Phase 5c: sync non-synced artifacts to resolved knowledge provider. Phase 5c always publishes — it is NOT conditioned by plan classification (see **rho-aias** skill § Phase 5c).

PUBLISH NUDGE:
- If any artifacts in `status.md` have sync status `created` or `modified`, append after the code block:
  "Unpublished artifacts detected. Run `/publish` to archive all artifacts."

SERVICE RESOLUTION PSEUDOFLOW:

```
vcs = resolve(vcs-config) or abort(missing/invalid vcs config)
tracker = resolve(tracker-config) or abort(missing/invalid tracker config)
knowledge = resolve(knowledge-config) or abort(missing/invalid knowledge config)
```

---

## 5. Content Rules (Semantics)

- Output must be in **English**.
- Apply the **technical-writing** skill patterns: Problem Framing, Conciseness.
- Use **exactly** the template defined below.
- Do **NOT** invent changes or scope.
- If information is missing, leave the section empty or add a short placeholder comment.
- Keep the content concise and review-friendly.
- **Evidence attachments:** GitHub does not provide a public API for uploading images to PR descriptions. The `Screenshots` section in the template supports manual attachment via the web UI after PR creation. If evidence files (images, GIFs) exist in TASK_DIR or are referenced in chat, note their local paths in the Screenshots section so the user can attach them manually.

---

## 6. Output Structure (Template)

```markdown
# Pull Request

## Title
<!-- Use a concise, descriptive title. Example: [FEAT] Add async search to product list -->

## Purpose
Select one:
- [ ] Feature
- [ ] Bug Fix
- [ ] Hotfix
- [ ] Release
- [ ] Other

## Associated Tickets
<!-- Link tracker tickets -->
[<TASK_ID>](<TRACKER-TICKET-URL>)

## Summary
<!-- High-level summary of what changed (2–4 bullets max) -->
- 
- 

## Implementation Details
<!-- Explain how the change was implemented and why -->
<!-- Mention relevant Use Cases, DI changes, networking, UI components, etc. -->

## Testing Performed

### Automated Testing
- [ ] Swift Testing
- [ ] Other (explain)

### Manual Testing
<!-- Steps to manually verify the change -->
1.
2.

## Screenshots (if applicable)
| Before | After |
| ------ | ----- |
|        |       |

## Impact / Risk Assessment
<!-- Potential impacts on performance, security, DI graph, networking, UI, etc. -->
- Risk level: Low / Medium / High
- Notes:

## Plan Delta
<!-- Compare planned increments vs actual implementation -->
| Increment | Status | Notes |
|-----------|--------|-------|
| <Increment 1> | Implemented as planned / Modified / Deferred | <brief notes> |

**Unplanned changes:** <list or "none">

## Checklist
- [ ] I have performed a self-review of my own code
- [ ] Code follows the project style and architecture guidelines
- [ ] My changes generate no new warnings
- [ ] I have added or updated tests where appropriate
- [ ] New and existing tests pass locally
```

---

## 7. Non-Goals / Forbidden Actions

This command must **NOT**:
- Invent changes or scope
- Create a PR without confirming via the PR Confirmation gate
- Perform `git push` (if creating the PR, assume the user has already pushed the current branch or guide them to do so)
- Perform implementation or reasoning
- Modify code or files (except status.md)
- Execute commands (except git diff and resolved VCS/tracker calls)
- Suggest alternative approaches
- Transition tracker to any status other than IN REVIEW

