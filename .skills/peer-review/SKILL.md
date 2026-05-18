---
name: peer-review
description: "Reviews a pull request or third-party work using the configured VCS provider. Use when reviewing a PR URL or PR number. Always dispatches multi-agent review sub-agents. Trigger terms: /peer-review, peer review, review PR, code review."
category: advisory
disable-model-invocation: true
version: 2.2.0
---

# Peer Review (PR / Third-Party Review) — v2.2

## 1. Identity

**Command Type:** Advisory — Chat-only / Analysis

You are reviewing a pull request or another developer's work using the `@review` reasoning stance. This command is for **peer review**, where the primary evidence source is the PR diff resolved through the configured VCS provider.

**Skills referenced:** `rho-aias`, `review-rubric`.

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

### Phase 0 — Pre-Resolve Sub-Agent Context (v2.2, mandatory)

Per `readme-multi-agent-review.md` § Sub-Agent Tool Boundary and § Host Context Resolution, sub-agents MUST NOT invoke any tool runtime. The host is the ONLY context provider. Before invoking any sub-agent, `/peer-review` MUST resolve every context surface and assemble the dispatch payload.

1. **Resolve PR diff and metadata** via the configured VCS provider MCP:
   - PR diff (unified format, all hunks).
   - PR metadata (number, title, description, author, target branch, head commit SHA).
2. **Fetch file blobs** for every file touched by the diff:
   - Prefer `gh pr checkout <PR>` so the working tree matches the PR; sub-agents see the actual code, not just the diff.
   - If checkout is not authorized → fall back to fetching serialized blobs via VCS MCP and packaging them in the dispatch payload.
3. **Load TASK_DIR artifacts** when `TASK_DIR` is resolvable via `rho-aias` and `task_id` was supplied:
   - `dod.plan.md`, `technical.plan.md`, `increments.plan.md`, `dor.plan.md`, `specs.design.md` (when present).
4. **Load project context**:
   - `RHOAIAS.md` of the repo under review (and nested if discoverable).
   - `stack-profile.md` (when present).
5. **Load mode + base rules** so sub-agents see the same governance the host operates under:
   - `@review` mode rule.
   - Base rule (`aias-config/rules/base.mdc` or equivalent).
6. **Assemble the dispatch payload** per the contract schema (`readme-multi-agent-review.md` § Host Context Resolution § Dispatch payload contract).

#### Gate: VCS Permission Recovery (Type: Decision)

If any step above returns `unauthorized` (PR diff fetch, blob fetch, `gh pr checkout`), MUST emit this Decision gate:

| Option | Behavior |
|---|---|
| `grant` | Pause for the user to resolve authorization (e.g., refresh OAuth, grant tool permission); retry the failed step. |
| `manual` | User supplies the missing context out-of-band (paste diff and/or blobs into chat); host proceeds with what was provided and notes the limitation in the review output. |
| `abort` | Halt with `[STATE: inconclusive]` and report the missing context. |

Silent partial review is FORBIDDEN. The host MUST NOT proceed with a degraded payload unless the user explicitly chooses `manual` and acknowledges the limitation.

### Multi-agent dispatch (always)

Multi-agent review is unconditional — dispatch regardless of Plan Classification:

1. Load `review-rubric` skill.
2. Dispatch `aias-correctness-reviewer`, `aias-quality-reviewer`, `aias-architecture-reviewer`, `aias-test-auditor`, `aias-security-auditor` in parallel with the Phase 0 dispatch payload.
3. Sub-agents return findings only — they MUST NOT call any tool (see § Non-Goals and `readme-multi-agent-review.md` § Sub-Agent Tool Boundary).
4. After all 5 complete, dispatch `aias-reflector` with the consolidated findings + the same Phase 0 payload.
5. Emit reflector consolidated output, then append VCS-ready comments and general review comment below.
6. If reflector emits `BLOCKED` → `/peer-review` MUST emit `[STATE: inconclusive]`.
7. If reflector emits a `## Context Gaps` section, surface it in the chat output verbatim. The human decides whether to re-run with expanded context or accept the review as-is.

```markdown
# Peer Review

## Source Mix
- VCS provider diff / PR metadata: <used | not used>
- Local TASK_DIR artifacts: <used | not used>
- Knowledge-provider enrichment: <used | not used>
- Multi-agent review: dispatched

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
- Dispatch sub-agents without a complete Phase 0 payload (silent partial dispatch is FORBIDDEN)
- Allow sub-agents to invoke any tool (MCP, shell, git, web fetch, file write) — sub-agents are pure inspection engines per `readme-multi-agent-review.md` § Sub-Agent Tool Boundary
- Write telemetry to `status.md` (this is `/self-review`'s responsibility when `TASK_DIR` exists; `/peer-review` reviews other developers' work and never assumes local `TASK_DIR`)

---

## 8. Self-Verification Checklist

- [ ] Findings are severity-ordered and evidence-linked.
- [ ] No file writes, no comment posting, and no remote mutation were performed.
- [ ] Open questions/assumptions are explicit and non-speculative.
- [ ] Terminal state line was emitted with canonical advisory token.

## 9. Halt Discipline

- Pause only at declared preconditions/blockers.
- Do not add ad-hoc pauses between deterministic review steps.
- If blocked, report blocker and required input.

## Terminal State Emission

`[STATE: delivered | inconclusive]` + one-line summary is mandatory.

## Invocation Mode Detection

- Standalone default.
- Chain invocation MUST preserve advisory/read-only semantics.
