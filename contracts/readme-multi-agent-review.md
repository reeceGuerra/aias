# Multi-Agent Review Contract (v1.2)

> **Keyword convention**: This contract uses RFC-2119 keywords (MUST, MUST NOT, SHOULD, MAY).
> See [readme-commands.md](readme-commands.md) § RFC-2119 Keyword Policy for definitions.

This document defines the **canonical contract** for multi-agent review as a first-class primitive of the Rho AIAS framework.

It exists to:
- Formalize the 5-dimension review model and reflector self-review
- Define the dispatch protocol, deduplication rules, severity gates, and re-verification loop
- Establish the relationship between the contract (governance policy) and the `review-rubric` skill (inspection criteria)
- Integrate multi-agent review with Plan Classification governance

This document is written **for maintainers** of the Rho AIAS framework.

It is **not** a skill and **not** executed by Cursor directly.
It is the reference against which the `review-rubric` skill, review sub-agents, and `/self-review` / `/peer-review` skills are designed and corrected.

---

## Philosophy

Multi-agent review surfaces dimension-specific findings through parallel, specialized reviewers — not through a single generalist pass. Each reviewer holds deep focus on one dimension; the orchestrator consolidates across dimensions. This mirrors the ADLC Toolkit's production-validated approach while preserving AIAS's "Human-Orchestrated" identity:

- Sub-agents are **readonly** — they find, they do not fix.
- Findings flow to the human, who decides what to act on.
- Auto-fix by sub-agents is **explicitly forbidden**.

---

## Review Dimensions

All reviews MUST cover the following five dimensions, each owned by a dedicated sub-agent:

| Dimension | Sub-Agent | Focus |
|-----------|-----------|-------|
| **Correctness** | `aias-correctness-reviewer` | Logic errors, edge cases, contract violations, behavioral regressions |
| **Quality** | `aias-quality-reviewer` | Code clarity, naming, dead code, duplication, maintainability debt |
| **Architecture** | `aias-architecture-reviewer` | Pattern conformance, layer boundaries, coupling, scalability concerns |
| **Test Coverage** | `aias-test-auditor` | Test posture, coverage gaps, assertion quality, untested paths |
| **Security** | `aias-security-auditor` | Injection risks, auth gaps, sensitive data exposure, dependency vulnerabilities |

In addition, a **Reflector** sub-agent (`aias-reflector`) performs a second-pass meta-review over all five dimensions' consolidated findings, identifying cross-dimension conflicts and surfacing the highest-severity items as a prioritized summary.

---

## Review Rubric Reference

The **per-dimension inspection criteria** (the specific checklist items for each dimension) live in `aias/.skills/review-rubric/SKILL.md`. This is intentional separation:

- This contract declares MUST/SHOULD on dimensions, dispatch, severity gates, and loop bounds — these are **governance policy**.
- The rubric skill carries the per-dimension checklist — this is **operational knowledge** that may evolve faster than policy.

Any proposal to embed the rubric inside this contract requires a new architectural intent under `intents/` revising this decision.

---

## Dispatch Protocol

### When to Dispatch

Multi-agent review dispatch MUST always occur when code is under review — regardless of Plan Classification:

| Condition | Multi-Agent Review |
|---|---|
| **Code in review** (any classification) | MUST dispatch all 5 reviewers + reflector |
| **Enrichment-only task** (no code changed) | MUST NOT dispatch — no code diff to review |

**Rationale (v1.1 change)**: Empirical evidence showed that minor-classified tasks can contain Critical and Major findings across dimensions that a single-agent pass misses due to scope-calibration bias. Plan Classification reflects planning scope, not code quality risk. Sub-agents run in isolated contexts (no chat history), so token cost is bounded by diff size, not task history. The classification condition is therefore removed.

### How to Dispatch

1. **Parallel invocation**: `/peer-review` or `/self-review` MUST invoke the 5 dimension reviewers in parallel (not sequentially).
2. **Rubric loading**: each sub-agent MUST load the `review-rubric` skill and select its dimension selector before beginning inspection.
3. **Input scope**: all sub-agents MUST receive the same input scope (PR diff or working-tree diff + TASK_DIR artifacts when available).
4. **Isolation**: each sub-agent MUST NOT read other sub-agents' findings during its review pass. Cross-dimension synthesis is the reflector's responsibility.
5. **Reflector**: MUST be invoked only after all 5 dimension reviewers have completed. MUST NOT run in parallel with the reviewers.

---

## Deduplication Protocol

When a finding is raised by more than one reviewer, the consolidation gate MUST apply:

1. **Exact duplicate**: same file + same line range + same rationale → keep only the highest-severity instance; attribute to all dimensions that raised it.
2. **Overlapping duplicate**: same file + nearby line range + related rationale → merge into a single finding with a combined dimension label (e.g., `[Quality + Architecture]`).
3. **Independent findings**: same file + different rationale or different line range → keep both as distinct findings.

The reflector is responsible for applying this protocol to the aggregated findings before producing the consolidated output.

---

## Severity Gates

Every finding MUST be tagged with exactly one severity level:

| Severity | Definition | Gate Behavior |
|----------|------------|---------------|
| **Critical** | Defect or gap that MUST be fixed before the PR can merge (logic error, security vulnerability, broken contract) | BLOCKS the PR; human MUST resolve before proceeding |
| **Major** | Significant issue that SHOULD be addressed but is negotiable with documented rationale | ESCALATES; human decides with rationale |
| **Minor** | Improvement opportunity or style issue with no blocking impact | NOTED in `peer-review.md`; human decides at discretion |

**Blocking rule**: If any Critical finding exists after the re-verification loop, `/peer-review` MUST NOT emit `[STATE: delivered]`. It MUST emit `[STATE: inconclusive]` with a summary of unresolved Critical findings.

---

## Re-Verification Loop

After the human resolves one or more findings and requests re-review:

1. Sub-agents MUST re-run only on the dimensions relevant to the changed code.
2. The re-verification loop is bounded to **≤ 1 additional iteration** per review session.
3. If Critical findings persist after 1 re-verification iteration, the command MUST halt and emit `[STATE: inconclusive]` — it MUST NOT enter a third review pass autonomously.

**Rationale**: unbounded re-verification loops create infinite confirmation chains that degrade human agency and produce review fatigue. One re-verify is sufficient to confirm resolution or surface a genuinely unresolvable issue requiring human escalation.

---

## Plan Classification Integration

Plan Classification no longer gates multi-agent dispatch. The dispatch rule is unconditional when code is in review:

| Classification | `/self-review` | `/peer-review` |
|---|---|---|
| **Critical** | MUST invoke multi-agent review | MUST invoke multi-agent review |
| **Standard** | MUST invoke multi-agent review | MUST invoke multi-agent review |
| **Minor** | MUST invoke multi-agent review | MUST invoke multi-agent review |
| **No classification** | MUST invoke multi-agent review | MUST invoke multi-agent review |

When Plan Classification is unavailable (legacy plan without `status.md`), multi-agent dispatch MUST still run as long as a code diff exists.

---

## Sub-Agent Manifest (Cursor v1.0)

The 6 review sub-agents follow a three-tier projection model:

| Tier | Location | Description |
|------|----------|-------------|
| **Framework canonical** | `aias/.canonical/subagents/` | Read-only framework defaults, shipped with the framework |
| **Project-owned copy** | `aias-config/subagents/` | Generated/customizable by the adopter team; regenerated by `aias generate --shortcuts` |
| **Tool shortcut** | `.cursor/agents/` | Symlinks to `aias-config/subagents/` created by `aias init`/`aias generate --shortcuts` |

`aias-config/subagents/` is a **project-owned generated surface**: editable by the adopter, but regenerable by tooling. Git is the mechanism for reviewing and accepting overwrites.

| File | Name | `readonly` | `is_background` | `model` |
|------|------|-----------|----------------|---------|
| `aias-correctness-reviewer.md` | `aias-correctness-reviewer` | `true` | `false` | advisory |
| `aias-quality-reviewer.md` | `aias-quality-reviewer` | `true` | `false` | advisory |
| `aias-architecture-reviewer.md` | `aias-architecture-reviewer` | `true` | `false` | advisory |
| `aias-test-auditor.md` | `aias-test-auditor` | `true` | `false` | advisory |
| `aias-security-auditor.md` | `aias-security-auditor` | `true` | `false` | advisory |
| `aias-reflector.md` | `aias-reflector` | `true` | `false` | advisory |

**Frontmatter invariants (enforced by `aias health`):**
- `readonly: true` — MUST be present; sub-agents MUST NOT carry write tools
- `is_background: false` — MUST be present; review runs synchronously (human waits for output)
- `tools:` — MUST NOT appear in frontmatter (not a valid Cursor subagent field)
- `model:` — advisory only; project or admin constraints may override at runtime

**Cross-tool compatibility**: v1.0 is intentionally Cursor-only. Future v1.x MAY add symlink projections for tools with compatible subagent directories (`.claude/agents/`, `.codex/agents/`) pending explicit validation.

---

## `aias init` Integration

When the selected tool set includes `cursor`:

- `aias init` MUST copy all 6 sub-agent files from `aias/.canonical/subagents/` to `aias-config/subagents/`.
- `aias init` MUST create/refresh symlinks for all 6 sub-agents in `.cursor/agents/` pointing to `aias-config/subagents/`.
- If `aias-config/subagents/` does not exist, `aias init` MUST create it.
- If `.cursor/agents/` does not exist, `aias init` MUST create it.
- Symlinks MUST be relative (consistent with `_create_symlink` behavior elsewhere in the CLI).
- When `aias-config/subagents/*.md` already exist and are overwritten by the generator, the CLI MUST emit a notice instructing the adopter to review `git diff` before committing.

---

## `aias health` Integration

When the selected tool set includes `cursor`:

- `aias health` MUST validate presence of all 6 sub-agents in `aias-config/subagents/`.
- `aias health` MUST validate presence of all 6 symlinks in `.cursor/agents/` pointing to `aias-config/subagents/`.
- `aias health` MUST parse frontmatter of each sub-agent and enforce: `readonly: true` and `is_background: false`.
- Legacy symlinks in `.cursor/agents/` pointing to `aias/.cursor/agents/` or `aias/.canonical/subagents/` MUST emit `[LEGACY]` warning with instruction to re-run `aias generate --shortcuts`.
- Missing sub-agent → emit `[MISSING]` warning with the expected path.
- Incorrect frontmatter → emit `[INVARIANT VIOLATION]` with the field name and expected value.

---

## Sub-Agent Tool Boundary (invariant, v1.2)

Review sub-agents are **pure inspection engines**. They MUST NOT invoke ANY tool runtime during a dispatch — this is an invariant, not a SHOULD. The forbidden surface is exhaustive:

| Forbidden | Examples |
|---|---|
| MCP tool calls | Atlassian MCP, GitHub MCP, Figma MCP, any other MCP server |
| Shell commands | `git`, `gh`, `ls`, `cat`, `python`, any subprocess |
| File writes | Editing any file, including `status.md` (host-only per § Dispatch Telemetry) |
| Read tool calls outside host-resolved context | Reading files not in the dispatch payload, walking the filesystem, opening files by path |
| Web fetches | HTTP requests, browser actions, URL resolution |
| Sub-agent fan-out | Dispatching further sub-agents (only the host orchestrates) |

The sub-agent's contract is minimal and closed:

- **Input**: the dispatch prompt assembled by the host (review-rubric selector + pre-resolved context payload).
- **Process**: apply the dimension selector against the payload.
- **Output**: findings list (one row per finding, severity-tagged, anchored to file:line of the diff).

If a sub-agent encounters context it would normally want to fetch (the full content of a referenced file, the git log of a function, the runtime behavior of a dependency), it MUST NOT attempt to retrieve it. It MUST emit a `[Context Gap]` finding instead (see § Context Gap Handling). The reflector consolidates gaps for human review.

### Rationale for the invariant

Empirical evidence (operational feedback 2026-05-09 → 2026-05-16): when the host runs on a different model than the sub-agents (e.g., Codex orchestrating Sonnet/Opus sub-agents), MCP and shell permissions do not propagate predictably. Sub-agents either (a) pause asking for permission the user has already granted to the host, breaking parallel dispatch, or (b) silently fail to read context the host already has, surfacing findings that disappear when manually re-verified on the actual branch. Forbidding tool use from sub-agents and making the host the only context provider eliminates both failure modes deterministically.

### Cross-tool compatibility

This invariant is platform-neutral. Cursor sub-agents, Claude Code sub-agents, and any future tool with a sub-agent abstraction MUST adopt the same boundary when projecting this contract.

---

## Host Context Resolution (companion invariant, v1.2)

The host (`/peer-review`, `/self-review`, future hosts) is the **only context provider** for sub-agents. Before dispatching, the host MUST pre-resolve every context surface that any of the 6 sub-agents could plausibly require:

1. **Diff** — full PR diff (`/peer-review`) or working-tree diff (`/self-review`).
2. **File blobs** — full content of every file touched by the diff. The host fetches blobs via the VCS provider MCP or local filesystem; sub-agents never re-fetch.
3. **Branch snapshot** — read-only access to the branch under review. The host MAY `gh pr checkout <PR>` to make the working tree match the PR; if checkout is not authorized, the host MUST fall back to serialized blobs via VCS MCP. Sub-agents never run checkout themselves.
4. **TASK_DIR artifacts** — when `TASK_DIR` resolves, the host loads `dod.plan.md`, `technical.plan.md`, `increments.plan.md`, `dor.plan.md`, `specs.design.md` (when present) and passes them as part of the dispatch payload.
5. **Project context** — `RHOAIAS.md` of the repo under review, plus any nested `RHOAIAS.md` resolved by Phase 0 nested context discovery.
6. **Mode + base rule** — the active mode rule (`@review`) and base rule, so sub-agents see the same governance the host operates under.
7. **Metadata** — PR title, PR description, author, target branch, head commit SHA (for `/peer-review`).

### Gate: VCS Permission Recovery (`/peer-review` only)

If the VCS provider returns `unauthorized` during context resolution (PR diff fetch, file blob fetch, or `gh pr checkout`), the host MUST emit a Decision gate with three options:

- `grant` — user resolves authorization and the host retries.
- `manual` — user supplies the diff and blobs out-of-band (paste into chat); host proceeds with what was provided and notes the limitation in the review output.
- `abort` — host halts with `[STATE: inconclusive]` and reports the missing context.

The host MUST NOT silently fall back to a partial review when context resolution fails. Silent partial review reproduces the failure mode this invariant was designed to eliminate.

### Dispatch payload contract

The dispatch payload to each sub-agent MUST include:

```
{
  "dimension": "correctness | quality | architecture | test-coverage | security | reflector",
  "diff": "<full unified diff>",
  "file_blobs": { "<path>": "<full content>", ... },
  "task_dir_artifacts": { "<filename>": "<full content>", ... } | null,
  "project_context": { "rhoaias_md": "<content>", "stack_profile": "<content>" } | null,
  "mode_rule": "<content>",
  "base_rule": "<content>",
  "vcs_metadata": { "pr_number": ..., "author": ..., "head_sha": ... } | null
}
```

Sub-agents read only from this payload. The reflector additionally receives the consolidated findings list emitted by the 5 dimension reviewers.

---

## Context Gap Handling (v1.2)

When a sub-agent identifies context it would normally want to fetch (e.g., the implementation of a callee not present in the diff, the history of a regression, the runtime behavior of a library version), it MUST emit a `[Context Gap]` finding using this shape:

```
[Context Gap] [<Dimension>] <file>:<line> — <what is missing> — would normally check by <what the sub-agent would do if it had tools>
```

The sub-agent MUST NOT attempt to retrieve the missing context. The reflector collects all `[Context Gap]` findings and surfaces them in a dedicated section of the final review output:

```
## Context Gaps

The following gaps were identified by dimension reviewers. The host did not provide enough
context for definitive findings on these items. Consider re-running with expanded context
or resolving manually:

- [Correctness] src/auth.py:42 — implementation of `validate_token()` not in diff —
  would normally check by reading the function body
- [Architecture] src/views.py:18 — `BaseView` parent class definition not visible —
  would normally check by reading the parent class
```

The human reviewer decides whether to re-run `/peer-review` or `/self-review` with explicit expanded context (e.g., adding the referenced files to the dispatch payload manually) or to accept the review as-is with the gaps noted.

### When gaps justify re-dispatch

The reflector SHOULD NOT auto-trigger re-dispatch. Re-dispatch decisions are owned by the human. The reflector's job is to make gaps visible, not to chase them.

---

## Dispatch Telemetry (host-owned, v1.2)

Multi-agent dispatch SHOULD be recorded as telemetry in `status.md` `command_log` when (and only when) the dispatching host can resolve `TASK_DIR` and a valid `status.md` exists. This produces an auditable trail of when each sub-agent ran and how long it took, enabling cost attribution and pipeline observability.

### Telemetry schema

The `command_log` entry for a multi-agent-dispatching host MUST follow this shape:

```yaml
command_log:
  - command: /<host-command>
    started_at: <ISO 8601 UTC>
    ended_at: <ISO 8601 UTC>
    dispatches:
      - subagent: <sub-agent name>
        started_at: <ISO 8601 UTC>
        ended_at: <ISO 8601 UTC>
      - subagent: <sub-agent name>
        started_at: <ISO 8601 UTC>
        ended_at: <ISO 8601 UTC>
```

The `dispatches[]` field is OPTIONAL. When absent, treat as an empty list (backward compatibility with v1.0/v1.1 `command_log` entries and with hosts that do not produce telemetry).

### Host as only registrar

The host (e.g., `/self-review`) is the ONLY component allowed to write `dispatches[]` to `status.md`. Sub-agents (`aias-correctness-reviewer`, `aias-quality-reviewer`, `aias-architecture-reviewer`, `aias-test-auditor`, `aias-security-auditor`, `aias-reflector`) MUST NOT write to `status.md` — they are pure inspection engines (see § Sub-Agent Tool Boundary). The host records each sub-agent's `started_at` at dispatch and `ended_at` at return.

### Scope: which hosts write telemetry

| Host | Telemetry behavior |
|---|---|
| `/self-review` | MUST write `dispatches[]` when `TASK_DIR` resolves AND `status.md` exists; MUST NOT write otherwise. |
| `/peer-review` | MUST NOT write `dispatches[]` — `/peer-review` reviews other developers' work and does not assume `TASK_DIR` exists for the reviewer's local workspace. |
| Future hosts | MUST declare telemetry behavior explicitly in their skill body; default is the `/self-review` policy. |

### Timestamp acquisition and degraded mode

- Hosts MUST obtain timestamps via a deterministic system source (`date -u +%Y-%m-%dT%H:%M:%SZ` or equivalent). When the environment does not permit shell access, hosts MAY use the date/time provided by the runtime context.
- Hosts MUST NOT invent timestamps. If a reliable timestamp cannot be obtained, the host MUST write `started_at: null` / `ended_at: null` and document the limitation in chat.

### Cross-reference

The closed schema for `command_log` and its writing rules live in `aias/.skills/rho-aias/reference.md` § Command Log. The `dispatches[]` extension is declared optional there for backward compatibility.

---

## Out of Scope (explicit — do not drift into)

- **Cross-repo fan-out**: multi-agent review across sibling repos is owned by `cross-repo-integration` skill (Wave 1, BL-S65). v1.0 reviews within a single workspace only.
- **Persisting findings as memory**: findings flow to `peer-review.md` artifact only; no cross-session persistence.
- **Auto-fix**: sub-agents find and report; they MUST NOT apply fixes. Auto-fix is permanently out of scope for v1.x.
- **Replacing `/self-review` or `/peer-review`**: the skills remain the user-facing invocation surface; they delegate to the rubric skill and sub-agents.
- **Embedding the rubric in this contract**: the rubric lives in `aias/.skills/review-rubric/SKILL.md`.
- **`aias new --agent`**: not introduced in v1.0; Cursor's `create-subagent` skill is sufficient.

---

## Related Artifacts

- `readme-skill.md` — Skill contract (defines `advisory`/`operative` categories)
- `readme-commands.md` — Behavior contract for advisory/operative skills (gate taxonomy, Plan Classification)
- `readme-mode-rule.md` — Mode rule contract (v1.1 adds subagent location convention)
- `aias/.skills/review-rubric/SKILL.md` — Per-dimension inspection criteria
- `aias/.canonical/subagents/` — Framework canonical sub-agent definitions (read-only)
- `aias-config/subagents/` — Project-owned copies; generated/customizable by adopter team
- `.cursor/agents/` — Tool-specific symlink projections pointing to `aias-config/subagents/` (created by `aias init`/`aias generate --shortcuts`)

---

This document is the **source of truth** for multi-agent review governance and dispatch protocol in Rho AIAS.
