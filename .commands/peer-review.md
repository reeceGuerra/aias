# Peer Review (PR / Third-Party Review) — v2

## 1. Identity

**Command Type:** Type A — Chat-only / Analysis

You are reviewing a pull request or another developer's work using the `@review` reasoning stance. This command is for **peer review**, where the primary evidence source is the PR diff resolved through the configured VCS provider.

**Skills referenced:** `rho-aias`.

---

## 2. Invocation / Usage

Invocation:
- `/peer-review <PR-URL>`
- `/peer-review <PR-NUMBER>`
- `/peer-review <PR-URL> <TASK_ID>`
- `/peer-review <PR-NUMBER> <TASK_ID>`

Usage notes:
- Best used with `@review` mode active.
- The PR identifier is the primary trigger for this command.
- This command produces findings in chat only. It does not approve, merge, or modify the PR.

---

## 3. Inputs

This command may use **only** the following inputs:
- PR URL or PR number supplied by the user
- Diff, metadata, and review context resolved through the configured VCS provider
- Optional TASK_DIR artifacts when local task context exists
- Optional knowledge-provider artifacts resolved by `task_id`
- Chat context explicitly provided by the user
- Service configs:
  - `aias-config/providers/vcs-config.md`
  - `aias-config/providers/knowledge-config.md`

Rules:
- VCS provider context is **mandatory** for PR review. If PR diff or metadata cannot be resolved, stop and request a valid PR identifier or provider configuration.
- Local TASK_DIR context is **optional** and non-blocking.
- Knowledge-provider enrichment is **optional**, best-effort, and non-blocking.
- If both diff evidence and artifact intent exist, the diff remains the primary source of truth for what changed.

---

## 4. Output Contract (Format)

- Return rendered Markdown in chat.
- Output MUST contain three layers in this order:
  1. findings prioritized by severity
  2. VCS-ready review comment snippets
  3. one general review comment for the PR as a whole
- For each VCS-ready snippet:
  - `File` and `Applies to diff` MUST be rendered as normal text
  - only `Suggested review comment` MUST be wrapped in a fenced code block
- When auxiliary context was used, state the source mix explicitly:
  - VCS provider diff / PR metadata
  - Local TASK_DIR artifacts
  - Knowledge-provider enrichment
- If no findings exist, say so explicitly, keep the general review comment, and omit per-finding VCS snippets.

---

## 5. Content Rules (Semantics)

- Output must be in **English**.
- Review only the code and metadata that belong to the requested PR / change set.
- Do **NOT** implement fixes, approve the PR, or merge changes.
- MUST distinguish blocking issues from optional improvements.
- MUST report drift when PR changes conflict with local or remote planning artifacts.
- MUST use provider-agnostic language in the command contract: say **VCS provider** and **knowledge provider**, not brand names.
- VCS-ready comments MUST be professional, impact-first, and safe for third-party developer review.
- VCS-ready comments MUST NOT be sarcastic, aggressive, or condescending.
- The general review comment MUST summarize the PR-level posture, not repeat every finding verbatim.

---

## 6. Output Structure (Template)

```markdown
# Peer Review

## Source Mix
- VCS provider diff / PR metadata: <used | not used>
- Local TASK_DIR artifacts: <used | not used>
- Knowledge-provider enrichment: <used | not used>

## Findings
### Blocking issues
- <finding or "None">

### Major risks
- <finding or "None">

### Minor improvements
- <finding or "None">

### Open questions / assumptions
- <question or "None">

## VCS-Ready Review Comments
### Comment <n>
File: `<path>`
Applies to diff: `<hunk / changed lines / contextual anchor>`

```text
<Suggested review comment in English>
```

## General Review Comment

```text
<PR-level review comment in English>
```

## Overall Recommendation
- <request changes | address majors then re-review | looks good with minor follow-ups>
```

---

## 7. Non-Goals / Forbidden Actions

This command must **NOT**:
- Proceed as a PR review without resolvable PR diff context
- Treat knowledge-provider enrichment as mandatory
- Replace diff evidence with artifact summaries
- Create or update artifacts
- Publish to knowledge provider
- Post comments or approvals unless the user explicitly requests a separate action
- Pretend that a VCS-ready snippet was anchored when no diff context exists
