# Self Review (Own-Work Review) — v2

## 1. Identity

**Command Type:** Advisory — Chat-only / Analysis

You are reviewing the user's own implementation work using the `@review` reasoning stance. This command is for **self-review of local work** before PR creation or before requesting external review.

**Skills referenced:** `rho-aias`.

---

## 2. Invocation / Usage

Invocation:
- `/self-review`
- `/self-review <TASK_ID>`

Usage notes:
- Best used with `@review` mode active.
- Prefer this command when the primary context is local code plus local artifacts in TASK_DIR.
- This command produces findings in chat only. It does not write artifacts, publish to providers, or modify code.

---

## 3. Inputs

This command may use **only** the following inputs:
- Modified code in the current repository / working tree
- TASK_DIR artifacts loaded via `rho-aias` when available: `dod.plan.md`, `increments.plan.md`, `technical.plan.md`, `dor.plan.md`, `specs.design.md` (when present)
- Chat context explicitly provided by the user

Rules:
- If TASK_DIR is available, load it and prioritize local artifacts as review intent context.
- If TASK_DIR is not available, the command MAY still review the modified code, but MUST state the missing planning context.
- `dod.plan.md` SHOULD be treated as the primary intent/checklist artifact when present.

---

## 4. Output Contract (Format)

- Return rendered Markdown in chat.
- Output MUST follow the same severity-first review structure as `/peer-review`, but this command MUST remain local-work oriented.
- This command MUST NOT emit VCS-ready review snippets because there is no PR diff anchor.
- Each finding SHOULD tie observed code back to one or more of:
  - `dod.plan.md`
  - `increments.plan.md`
  - `technical.plan.md`
  - local coding standards and architecture
- If no findings exist, say so explicitly and state any residual testing or context gaps.

---

## 5. Content Rules (Semantics)

- Output must be in **English**.
- Review modified code only.
- Do **NOT** implement fixes unless the user explicitly asks.
- MUST distinguish blocking issues from optional improvements.
- SHOULD evaluate alignment between actual code, `dod.plan.md`, and increment goals.
- If local artifacts and code conflict, report the drift explicitly.
- MUST conclude whether the work is ready for peer review or what should be addressed first.
- MUST keep recommendations scoped to local review readiness, not PR publication wording.

---

## 6. Output Structure (Template)

```markdown
# Self Review

## Source Mix
- Modified local code: used
- Local TASK_DIR artifacts: <used | not used>

## Findings
### Blocking issues
- <finding or "None">

### Major risks
- <finding or "None">

### Minor improvements
- <finding or "None">

### Open questions / assumptions
- <question or "None">

## Readiness
- <ready for peer review | address blockers first | address major risks before PR>

## Recommended Next Step
- <run `/peer-review` on PR once ready | fix local issues first | validate missing tests/context>
```

---

## 7. Non-Goals / Forbidden Actions

This command must **NOT**:
- Create or update artifacts
- Publish to knowledge provider
- Post to tracker or VCS provider
- Replace `@review` with implementation behavior
- Pretend a PR review happened when only local work was reviewed
- Emit VCS-ready review comments as if a remote diff existed
