# Multi-Agent Review Contract (v1.1)

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

The 6 review sub-agents are defined as Cursor sub-agent files under `aias/.cursor/agents/`:

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

- `aias init` MUST create/refresh symlinks for all 6 BL-S53 sub-agents in `.cursor/agents/` pointing to canonical sources in `aias/.cursor/agents/`.
- If `.cursor/agents/` does not exist, `aias init` MUST create it.
- Symlinks MUST be relative (consistent with `_create_symlink` behavior elsewhere in the CLI).

---

## `aias health` Integration

When the selected tool set includes `cursor`:

- `aias health` MUST validate presence of all 6 sub-agents in `.cursor/agents/`.
- `aias health` MUST parse frontmatter of each sub-agent and enforce: `readonly: true` and `is_background: false`.
- Missing sub-agent → emit `[MISSING]` warning with the expected path.
- Incorrect frontmatter → emit `[INVARIANT VIOLATION]` with the field name and expected value.

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
- `aias/.cursor/agents/` — Canonical sub-agent definitions
- `.cursor/agents/` — Tool-specific symlink projections (created by `aias init`)

---

This document is the **source of truth** for multi-agent review governance and dispatch protocol in Rho AIAS.
