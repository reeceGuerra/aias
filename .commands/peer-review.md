# Peer Review (PR / Third-Party Review) — v1

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
  - `aias-providers/vcs-config.md`
  - `aias-providers/knowledge-config.md`

Rules:
- VCS provider context is **mandatory** for PR review. If PR diff or metadata cannot be resolved, stop and request a valid PR identifier or provider configuration.
- Local TASK_DIR context is **optional** and non-blocking.
- Knowledge-provider enrichment is **optional**, best-effort, and non-blocking.
- If both diff evidence and artifact intent exist, the diff remains the primary source of truth for what changed.

---

## 4. Output Contract (Format)

Return findings directly in chat, prioritized by severity:

1. Blocking issues
2. Major risks
3. Minor improvements
4. Open questions / assumptions
5. Overall recommendation

When auxiliary context was used, state the source mix explicitly:

- VCS provider diff / PR metadata
- Local TASK_DIR artifacts
- Knowledge-provider enrichment

If no findings exist, say so explicitly and state any residual context gaps.

---

## 5. Content Rules (Semantics)

- Output must be in **English**.
- Review only the code and metadata that belong to the requested PR / change set.
- Do **NOT** implement fixes, approve the PR, or merge changes.
- MUST distinguish blocking issues from optional improvements.
- MUST report drift when PR changes conflict with local or remote planning artifacts.
- MUST use provider-agnostic language in the command contract: say **VCS provider** and **knowledge provider**, not brand names.

---

## 6. Review Procedure

1. Resolve the PR diff and metadata through the configured VCS provider.
2. If TASK_DIR is available locally, load `dod.plan.md`, `increments.plan.md`, and `technical.plan.md` as secondary context.
3. If `task_id` is available, MAY attempt knowledge-provider enrichment for published artifacts. Failure here MUST NOT block the review.
4. Review the PR diff first; auxiliary artifacts only enrich intent and history.
5. If diff evidence conflicts with local or remote artifacts, report the drift and prioritize the current diff as the source of changed behavior.
6. Return findings with evidence and impact.

---

## 7. Non-Goals / Forbidden Actions

This command must **NOT**:
- Proceed as a PR review without resolvable PR diff context
- Treat knowledge-provider enrichment as mandatory
- Replace diff evidence with artifact summaries
- Create or update artifacts
- Publish to knowledge provider
- Post comments or approvals unless the user explicitly requests a separate action
