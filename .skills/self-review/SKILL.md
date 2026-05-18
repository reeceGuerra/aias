---
name: self-review
description: "Reviews the user's own implementation work against DoD criteria before PR creation. Use in @review mode with local code and TASK_DIR artifacts. Always dispatches multi-agent review sub-agents. Trigger terms: /self-review, self review, review own work, pre-PR review."
category: advisory
disable-model-invocation: true
version: 2.2.0
---

# Self Review (Own-Work Review) — v2.2

## 1. Identity

**Command Type:** Advisory — Chat-only / Analysis

You are reviewing the user's own implementation work using the `@review` reasoning stance. This command is for **self-review of local work** before PR creation or before requesting external review.

**Skills referenced:** `rho-aias`, `review-rubric`.

---

## 2. Invocation / Usage

Invocation:
- `/self-review`
- `/self-review <TASK_ID>`

Usage notes:
- Best used with `@review` mode active.
- SHOULD use this command when the primary context is local code plus local artifacts in TASK_DIR.
- This command produces findings in chat only. It does not write artifacts, publish to providers, or modify code, **except** for telemetry-only updates to `status.md` (see Telemetry below).

### Telemetry (v2.2)

When `TASK_DIR` resolves AND `status.md` exists, the host MUST append a single `command_log` entry capturing the multi-agent dispatch with the schema:

```yaml
command_log:
  - command: /self-review
    started_at: 2026-05-16T14:30:12Z
    ended_at: 2026-05-16T14:42:51Z
    dispatches:
      - subagent: aias-correctness-reviewer
        started_at: 2026-05-16T14:31:02Z
        ended_at: 2026-05-16T14:38:27Z
      - subagent: aias-quality-reviewer
        started_at: 2026-05-16T14:31:02Z
        ended_at: 2026-05-16T14:37:18Z
      - subagent: aias-architecture-reviewer
        started_at: 2026-05-16T14:31:02Z
        ended_at: 2026-05-16T14:39:04Z
      - subagent: aias-test-auditor
        started_at: 2026-05-16T14:31:02Z
        ended_at: 2026-05-16T14:36:53Z
      - subagent: aias-security-auditor
        started_at: 2026-05-16T14:31:02Z
        ended_at: 2026-05-16T14:38:11Z
      - subagent: aias-reflector
        started_at: 2026-05-16T14:39:30Z
        ended_at: 2026-05-16T14:42:33Z
```

Writing rules:
- The host (`/self-review`) is the ONLY registrar of `dispatches[]`. Sub-agents MUST NOT write to `status.md` (they are pure inspection engines; see `readme-multi-agent-review.md` § Sub-Agent Tool Boundary).
- The host records each sub-agent's `started_at` when it dispatches the sub-agent and `ended_at` when the sub-agent returns.
- The `dispatches[]` field is OPTIONAL in the schema (`readme-multi-agent-review.md` § Dispatch Telemetry). Absence indicates a non-multi-agent invocation or a host that did not record dispatches; absence MUST NOT be treated as an error.
- When `TASK_DIR` does NOT resolve OR `status.md` does NOT exist, the host MUST NOT attempt telemetry — `/self-review` operates as pure advisory in those cases (consistent with `/peer-review`, which never writes telemetry because it reviews other developers' work).
- When timestamps cannot be obtained reliably (no shell, no system clock available), the host MUST write `started_at: null` / `ended_at: null` and document the limitation in chat. Inventing timestamps is FORBIDDEN.

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

### Phase 0 — Pre-Resolve Sub-Agent Context (v2.2, mandatory)

Per `readme-multi-agent-review.md` § Sub-Agent Tool Boundary and § Host Context Resolution, sub-agents MUST NOT invoke any tool runtime. The host is the ONLY context provider. Before invoking any sub-agent, `/self-review` MUST resolve every context surface and assemble the dispatch payload.

1. **Resolve working-tree diff** against the base branch (typically `main`):
   - Use `git diff <base>...HEAD` for committed changes, plus `git diff` for uncommitted, packaged as a single unified diff.
2. **Fetch file blobs** for every file touched by the diff directly from the local working tree — no remote fetch needed.
3. **Load TASK_DIR artifacts** when available via `rho-aias`:
   - `dod.plan.md`, `technical.plan.md`, `increments.plan.md`, `dor.plan.md`, `specs.design.md` (when present).
4. **Load project context**:
   - `RHOAIAS.md` (and nested if discoverable per Phase 0 nested context discovery).
   - `stack-profile.md` (when present).
5. **Load mode + base rules** so sub-agents see the same governance the host operates under:
   - `@review` mode rule.
   - Base rule.
6. **Assemble the dispatch payload** per the contract schema (`readme-multi-agent-review.md` § Host Context Resolution § Dispatch payload contract). `vcs_metadata` is omitted (no PR; this is local self-review).

Since `/self-review` operates entirely on the local working tree, Phase 0 has no permission-recovery gate. If the working tree cannot be diffed (corrupt repo, detached state with no base), the host MUST emit `[STATE: inconclusive]` and report the blocker.

### Multi-agent dispatch (always)

Multi-agent review is unconditional — dispatch regardless of Plan Classification:

1. Load `review-rubric` skill.
2. Dispatch `aias-correctness-reviewer`, `aias-quality-reviewer`, `aias-architecture-reviewer`, `aias-test-auditor`, `aias-security-auditor` in parallel with the Phase 0 dispatch payload.
3. Sub-agents return findings only — they MUST NOT call any tool (see § Non-Goals and `readme-multi-agent-review.md` § Sub-Agent Tool Boundary).
4. After all 5 complete, dispatch `aias-reflector` with the consolidated findings + the same Phase 0 payload.
5. Emit reflector output as the final review.
6. If reflector emits a `## Context Gaps` section, surface it in the chat output verbatim. The human decides whether to re-run with expanded context or accept the review as-is.

```markdown
# Self Review

## Source Mix
- Modified local code: used
- Local TASK_DIR artifacts: <used | not used>
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

## Readiness
- <ready for peer review | address blockers first | address major risks before PR>

## Recommended Next Step
- <run `/peer-review` on PR once ready | fix local issues first | validate missing tests/context>
```

---

## 7. Non-Goals / Forbidden Actions

This command must **NOT**:
- Create or update artifacts other than `status.md` (telemetry-only updates are allowed per § 2 Telemetry).
- Publish to knowledge provider
- Post to tracker or VCS provider
- Replace `@review` with implementation behavior
- Pretend a PR review happened when only local work was reviewed
- Emit VCS-ready review comments as if a remote diff existed
- Allow sub-agents to write `status.md` directly — only the host (this skill) writes telemetry. Sub-agents are pure inspection engines per `readme-multi-agent-review.md` § Sub-Agent Tool Boundary.

---

## 8. Self-Verification Checklist

- [ ] Findings are severity-ordered and anchored to reviewed evidence.
- [ ] No file writes or remote review mutations were performed.
- [ ] Open questions/assumptions are explicit.
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
