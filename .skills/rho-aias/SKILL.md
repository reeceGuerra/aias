---
name: rho-aias
description: Canonical skill protocol for artifact-driven development workflows. Use when the user works on a task that produces or consumes artifacts under <resolved_tasks_dir>/<TASK_ID>/ (default ~/.cursor/plans/) — including planning, implementation, enrichment, publishing, or any command that reads/writes task artifacts.
category: knowledge
disable-model-invocation: false
version: 9.6.0
---

# Agentic-Driven Development

## PURPOSE

Teach the agent the canonical skill protocol for managing task artifacts across the full development lifecycle. This skill defines what artifacts exist, where they live, how they are discovered and loaded, and how the agent must track progress, sync to the resolved knowledge provider, and coordinate with the resolved tracker provider.

This is a **system skill** — it is referenced by every mode and every artifact-producing or artifact-consuming command. It provides the shared foundation that keeps all workflows consistent.

---

## WHEN TO USE

Use this skill when:
- **Creating artifacts** — `/blueprint`, `/enrich`, `/issue`, `/fix`, `/charter`, `/trace`, `/assessment`
- **Consuming artifacts** — `/implement`, `/validate-plan`, `/pr`, `/commit`, `/consolidate-plan`, `/report`, `/assessment`
- **Reviewing with artifact context** — `/self-review`, `/peer-review`, `/handoff`
- **Publishing artifacts** — `/publish`, or any command that triggers progressive knowledge sync (Phase 5)
- **Syncing with tracker** — `/blueprint`, `/pr`, `/commit` (Phase 6)
- **Reasoning about task state** — any mode that loads from `<resolved_tasks_dir>/<TASK_ID>/` (default: `~/.cursor/plans/`)

Commands that reference this skill: `/aias`, `/assessment`, `/blueprint`, `/charter`, `/commit`, `/consolidate-plan`, `/copyedit`, `/enrich`, `/explain`, `/fix`, `/guide`, `/handoff`, `/implement`, `/issue`, `/peer-review`, `/pr`, `/publish`, `/report`, `/self-review`, `/trace`, `/validate-plan`.

---

## ARTIFACT CATALOG

12 artifact types + 1 system file. This is a **closed catalog** — no other artifact types are allowed.

| # | File name | Suffix | Producer | Description |
|---|-----------|--------|----------|-------------|
| 1 | `technical.plan.md` | `.plan.md` | `/blueprint` | Technical approach, architecture decisions |
| 2 | `increments.plan.md` | `.plan.md` | `/blueprint` | Increment breakdown with goals and ordering |
| 3 | `dor.plan.md` | `.plan.md` | `/enrich` | Definition of Ready checklist |
| 4 | `dod.plan.md` | `.plan.md` | `/enrich` | Definition of Done checklist |
| 5 | `specs.design.md` | `.design.md` | `/blueprint` | Design specifications (UI, resolved design-provider context) |
| 6 | `analysis.product.md` | `.product.md` | `/enrich` | Product analysis (JTBD, 5 Whys, MoSCoW) |
| 7 | `report.issue.md` | `.issue.md` | `/issue` | Issue investigation report |
| 8 | `analysis.fix.md` | `.fix.md` | `/fix` | Root cause analysis and fix strategy |
| 9 | `feasibility.assessment.md` | `.assessment.md` | `/assessment` | Fix feasibility evaluation and approach |
| 10 | `delivery.charter.md` | `.charter.md` | `/charter` | Delivery charter with estimates |
| 11 | `instrumentation.trace.md` | `.trace.md` | `/trace` | Instrumentation and observability plan |
| 12 | `delta.publish.md` | `.publish.md` | `/publish` | Plan Delta (planned vs actual comparison) |
| S | `status.md` | — | system | Progress tracking, tracker sync, artifact sync |

### Naming convention

All artifacts follow the pattern `<name>.<suffix>.md`. The suffix determines the artifact type and enables glob-based discovery. `status.md` is the only exception — it has no suffix because it is a system file, not a content artifact.

### Directory structure

```
<resolved_tasks_dir>/<TASK_ID>/
├── status.md
├── technical.plan.md
├── increments.plan.md
├── dor.plan.md
├── dod.plan.md
├── specs.design.md
├── analysis.product.md
├── report.issue.md
├── analysis.fix.md
├── feasibility.assessment.md
├── delivery.charter.md
├── instrumentation.trace.md
└── delta.publish.md
```

Not all artifacts are present in every task. The profile determines which artifacts are expected (see reference.md).

### Discovery rules

Discover artifacts by globbing the suffix: `*.plan.md`, `*.design.md`, `*.product.md`, `*.issue.md`, `*.fix.md`, `*.assessment.md`, `*.charter.md`, `*.trace.md`, `*.publish.md`. Never hardcode file names — always glob by suffix.

### Path deprecation

Old artifact paths (`~/.cursor/issues/`, `~/.cursor/fixes/`, `~/.cursor/charters/`) are deprecated. All artifacts now live under `<resolved_tasks_dir>/<TASK_ID>/`. Base directory defaults to `~/.cursor/plans/` but is configurable via `stack-profile.md` `binding.generation.tasks_dir` (see `reference.md` § Tasks Base Directory).

---

## CORE RULES

### One mode per chat

Each chat is a single specialized agent: one mode per chat, plus the base rules that always apply. Modes are **never** mixed in the same chat. Handoffs between modes happen across chats — one chat produces an artifact (via a command), and that file is used as input in another chat where a different mode runs. If consecutive steps use the same mode, they stay in the same chat.

Artifacts are the **durable handoff layer**. The `/handoff` command may emit an **operational handoff snippet** to help open the next chat, but that snippet is advisory and never replaces TASK_DIR artifacts or `status.md` as the source of truth.

### Plan Classification

Every plan is classified to determine its publication and approval requirements:

| Type | Scope | Publication | Approval | Closure |
|------|-------|-------------|----------|---------|
| Minor (Local/Low-Risk) | Bug fixes, small refactors, config | Conditional (Phase 5c — tracker-gated) | Not required | `/publish` (reconciliation + closure). `/report` available as lightweight alternative |
| Standard (Medium-Impact) | Features, UX/UI, internal tools | Conditional (Phase 5c — tracker-gated) | Not required (unless objection) | `/publish` |
| Critical (Critical/Strategic) | Arch redesigns, cross-team, launches | Conditional (Phase 5c — tracker-gated) | Required before `/implement` | `/publish` |

Classification determines governance gates, not publication. Phase 5c fires only when a valid tracker ticket exists for the TASK_ID — see Phase 5c preconditions below.

- Assigned by `/blueprint` in `status.md` (`classification: minor | standard | critical`).
- Validated by `/validate-plan` (gap if missing).
- `/charter` can **escalate** (minor→standard, standard→critical) but **never downgrade**.

### Refinement and Amendment (v9.6+)

- **Refinement Artifact Mutation Invariant (v9.6+)**: `dor.plan.md` and `dod.plan.md` are **created** by `/enrich` (refinement flow, primary path) or by `/blueprint` (bug exception only — when `profile: bugfix` and bug-flow artifacts exist without DoR/DoD from `/enrich`). Once they exist, they are **modified** ONLY by `/enrich --refresh` (re-read tracker + comments) or by `/consolidate-plan` (amendment TODO resolution). No other command may mutate them — not even with user confirmation in chat. Inline user answers during `/blueprint` are captured as a `**Inline confirmation**: <text> (YYYY-MM-DD)` sub-field marker inside the corresponding `## Proposed Do{R,D} Amendments` bullet (full contract in `aias/contracts/readme-artifact.md` v2.3 § Refinement Artifact Mutation Invariant).
- **Refinement validated**: `/enrich --brief` sets `refinement_validated: true` in `status.md` when brief comment is posted AND knowledge publish succeeds (team has context for refinement). Without `--brief`, `refinement_validated` is `false`. `/enrich --refresh` does NOT modify this flag (semantically it is a historical indicator of brief+publish success, not of tracker-sync state). This flag informs context quality only; it MUST NOT relax classification-derived governance gates.
- **DoR Readiness Check**: `/enrich` includes a DoR Readiness Check gate (blocking/non-blocking classification) before writing DoR/DoD artifacts.
- **`/enrich --refresh` flow (v9.6+)**: re-reads tracker fields + comment thread, diffs against on-disk DoR/DoD, fires `Gate: Refresh Approval` for the merge, and fires `Sub-Gate: Amendment Reconciliation` (per bullet, iterated) when `## Proposed Do{R,D} Amendments` sections have content. Sets `status.md last_refreshed_at` UTC on successful apply. See `aias/.skills/enrich/SKILL.md` for full Phase ordering.
- **Staged amendments (all gaps, inline-confirmed or unresolved)**: `/blueprint` stages every detected gap in two separate sections in `technical.plan.md` body:
  - `## Proposed DoR Amendments` (canonical heading, no `Category` prefix)
  - `## Proposed DoD Amendments` (canonical heading, no `Category` prefix)
- **Amendment bullet shape (v9.6+, multi-line)**:
  ```
  - **<Dimension>**: <gap description>.
    - **Proposed resolution**: <agent value or "needs <X> from <role>">
    - **Inline confirmation** (optional): <user value> (YYYY-MM-DD)
  ```
- **Amendment routing invariant**:
  - DoR-targeted amendments live ONLY in `dor.plan.md` (or staged in `technical.plan.md § Proposed DoR Amendments` before resolution).
  - DoD-targeted amendments live ONLY in `dod.plan.md` (or staged in `technical.plan.md § Proposed DoD Amendments`).
  - Mixing DoR and DoD changes in a single Proposed section is FORBIDDEN.
  - The legacy combined section `## Proposed DoR/DoD Amendments` is FORBIDDEN since v9.5.
  - Inline-confirmed items MUST appear in the Proposed section with the `**Inline confirmation**:` sub-field marker (v9.6+, reverses v9.5 Path A behavior).
- **Amendment resolution flow (unified TODO model)**:
  - `/validate-plan` v2.1.0+ parses multi-line bullets, reads both Proposed sections, and registers each entry as a TODO in `technical.plan.md` frontmatter with `kind: amendment_dor` or `kind: amendment_dod`. The TODO `content` field captures ONLY the parent line (dimension + gap description); sub-bullets stay in the body. It does NOT decide, apply, or remove Proposed entries. There is NO Amendment Approval gate.
  - `/consolidate-plan` v2.1.0+ iterates TODOs (any `kind`: `validation`, `amendment_dor`, `amendment_dod`) with `status: pending`. For amendment TODOs, it reads the corresponding bullet from the body (matched by exact-string on dimension/criterion). If the bullet contains an `**Inline confirmation**:` sub-field, that value is the default proposed during the Update Approval gate. On apply, the entire bullet (parent + sub-bullets) is removed from the Proposed section.
- **Todo lifecycle (v9.6+)**: `pending → completed` (consolidate-plan applies) or **deleted from frontmatter** (when `/enrich --refresh` Amendment Reconciliation sub-gate Case A `remove` or Case B `tracker` supersedes the amendment). No `cancelled` terminal state. Audit trail lives in `status.md command_log` + artifact git history + knowledge provider version history.
- **Legacy hard-fail**: `/validate-plan` v2.0.0+ hard-fails when it detects the legacy combined `## Proposed DoR/DoD Amendments` heading. No auto-split heuristic is provided. Manual split is the only supported migration path. See `aias/docs/QUICKSTART.md § Upgrading from v9.4 to v9.5`.
- **Phase 5c**: publishes all `modified` artifacts (`dor.plan.md`, `dod.plan.md`, `technical.plan.md`) without special gating. The old `apply_local` / `apply_and_publish` dichotomy is removed since v9.5.

### Governance in Artifacts

The `## Governance` section is an optional section inside `increments.plan.md` that defines **per-increment custom gates**. It follows the Governance-in-Artifact Schema defined in `readme-commands.md`.

| Classification | `## Governance` section | Behavior |
|----------------|------------------------|----------|
| Minor | MUST NOT be generated | No custom gates; baseline feedback after each increment |
| Standard | MAY be generated | Custom gates only when risk or cross-team dependencies warrant them |
| Critical | MUST be generated | At least one Approval gate before the first increment |

**Producer/consumer model:**
- `/blueprint` is the **governance producer** — it writes the `## Governance` section during Phase 3 based on classification and risk assessment.
- `/implement` is the **governance consumer** — it reads classification from `status.md` and custom gates from `increments.plan.md`, resolving which gates to fire at each trigger point.

**Precedence:** Custom gates in `## Governance` take precedence over classification baselines at their specific trigger points.

**`/charter` escalation:** When `/charter` escalates classification (minor→standard, standard→critical), subsequent `/implement` runs automatically inherit the higher governance baseline. If a Critical plan lacks a `## Governance` section, `/validate-plan` flags it as a gap.

---

## LOADING PROTOCOL (Summary)

Every command that interacts with artifacts MUST follow this 7-phase skill protocol:

```
Phase 0 — DIRECTORY RESOLUTION
  Resolve TASK_DIR from context (Structured Prompt, user input, or directory listing).
  Resolve project context via walk-up (`cwd` -> root) to discover nearest
  `RHOAIAS.md`; merge with root context when nested context files exist.
  If TASK_DIR does not exist and command is a producer: create it.
  If TASK_DIR does not exist and command is a consumer: abort.

Phase 0b — CONVERSATION CACHE CHECK (optimization, not correctness)
  Before Phases 1–3 execute below — and before re-loading
  RHOAIAS.md, base-rule, mode-rule, output-contract, or any
  referenced skill — inspect the current conversation context.
  If a Read tool call earlier in the same agent session covered
  the same path with content that matches the current file, SKIP
  the re-Read and reference the already-loaded content.

  The cache check is an OPTIMIZATION HEURISTIC, never a correctness
  contract. When in doubt, re-Read.

  MUST re-Read triggers (override the cache):
    (i)   Any Write tool call against the same path occurred
          earlier in the same conversation (cached content is
          stale by definition).
    (ii)  Any user message indicates a manual edit to the file
          (e.g., "I just edited X").
    (iii) Predecessor command in the current chain updated
          status.md (status.md is high-volatility — always
          re-Read; signal: a Write tool call against the
          status.md path earlier in the session).
    (iv)  RHOAIAS.md staleness gates fire per the freshness
          lifecycle in readme-project-context.md — freshness
          wins over cache regardless of cache state.

  Forbidden:
    - Optimistic skip without freshness re-check on RHOAIAS.md
      when staleness gates apply.
    - Cross-agent cache sharing (each agent's context is
      independent).
    - Caching agent memory across sessions (the cache IS the
      current chat context, ephemeral by design — agent-fresh
      invariant).

  Future hook: cost-report aggregation MAY include a "cache-hit
  ratio" metric once cost reconciliation tooling ships,
  providing measured savings per task and per sprint.
  Instrumentation deferred until that tooling lands.

Phase 1 — ARTIFACT DISCOVERY
  Glob by suffix inside TASK_DIR.
  Build inventory of present artifacts.

Phase 2 — RELEVANCE FILTERING
  Filter inventory against per-mode required/optional artifact lists.
  Warn if required artifacts are missing; note optional ones.

Phase 3 — LOADING + ACKNOWLEDGMENT
  Read relevant artifacts into context.
  Acknowledge loaded artifacts to the user.

Phase 4 — EXECUTION
  Run the command-specific logic.
  Write output artifacts to TASK_DIR.

Phase 5 — STATUS UPDATE + ARTIFACT TRACKING + KNOWLEDGE SYNC
  5a. Update completed_steps / current_step in status.md
  5b. Set artifact sync status (created/modified) for written artifacts
  5c. CONDITIONAL KNOWLEDGE SYNC (tracker-gated)
      Preconditions — ALL THREE are evaluated in order:
        P1. task_id in status.md is present and non-empty.
        P2. Tracker provider resolves successfully from aias-config/providers/tracker-config.md
            (service_category, active_provider, provider enabled, skill binding valid).
        P3. The tracker ticket identified by task_id is reachable and exists in the
            resolved tracker provider (verified via tracker MCP read call).
      Precondition handling:
        - P1 failure: skip Phase 5c silently and leave artifacts in created/modified state
          (reconciled later by /publish).
        - P2 failure: abort the dependent sync operation and request provider configuration
          correction (fail-fast).
        - P3 failure: skip Phase 5c silently and leave artifacts in created/modified state
          (reconciled later by /publish).
      If preconditions are met, publish all non-synced artifacts:
      Publish the full publishable content of all non-synced artifacts to resolved knowledge provider.
      Read each artifact file and publish its complete publishable Markdown body — never summarize.
      For Cursor-first `*.plan.md` artifacts, strip only the initial YAML frontmatter block before publishing.
      For non-plan artifacts, publish the full file content.
      Resolve provider from aias-config/providers/knowledge-config.md.
      Validate service_category, active_provider, provider enabled flag,
      skill binding, and capability compatibility.
      If config is missing/invalid/unresolvable: abort dependent sync
      operation and request provider configuration correction.
      Use provider navigation/update algorithm without duplicates.
      Idempotent: re-publishing updates existing pages, never duplicates.
      If provider is unavailable at runtime: abort dependent sync operation
      and report provider unavailability.
      After each successful artifact publish, check the resolved knowledge
      provider config for a Table of Contents section. If present, inject
      a provider-native TOC element per the algorithm defined in that
      config (read page in native format, insert TOC node, update page).
      This is a MANDATORY post-publish step when the config section exists
      — not optional. TOC injection failure is non-blocking.
  5d. Completion check

Phase 6 — TRACKER SYNC
  Triggered only by: /blueprint, /pr, /commit
  Resolve provider from aias-config/providers/tracker-config.md.
  Validate service_category, active_provider, provider enabled flag,
  skill binding, and capability compatibility.
  Require providers.<active_provider>.status_mapping_source and load mapping.
  If config is missing/invalid/unresolvable: abort dependent tracker sync
  operation and request provider configuration correction.
  If status mapping is missing/invalid/unresolvable: abort dependent tracker
  sync operation and request mapping correction.
  If provider is unavailable at runtime: abort dependent tracker sync
  operation and report provider unavailability.
  Resolve canonical transition via provider status mapping.
  Ownership rule:
    - pending_dor -> ready is a manual transition (team responsibility during refinement)
    - /blueprint owns canonical transition ready -> in_progress
    - /blueprint (bug exception) owns canonical transition pending_dor -> in_progress
    - /pr owns canonical transition in_progress -> in_review
    - /commit only verifies in_review; never owns primary transition
  Boundary: NEVER transition to DONE, NEVER transition to CANCELLED.
  Idempotent: if already at target status, no-op.
```

Canonical service resolution pseudoflow:

```text
resolveServiceOrAbort(category):
  load aias-config/providers/<category>-config.md
  validate schema + active_provider + skill_binding + capability
  if valid:
    return resolved provider binding
  abort dependent operation and request provider configuration
```

---

## REFERENCES

- `reference.md` — Detailed per-mode requirements, loading order, writing rules, workflow profiles, step definitions, status.md format and lifecycle, artifact sync status catalog, knowledge sync details
- `examples.md` — Directory states at each flow stage for feature/bugfix/refactor, status.md evolution, artifact sync progression
- `aias-config/providers/knowledge-config.md` — Knowledge provider category config (active provider, skill binding, failure behavior)
- `aias-config/providers/tracker-config.md` — Tracker provider category config (active provider, skill binding, failure behavior)
- `aias-config/providers/<provider_id>/` — Referenced document directory containing project-specific config files (field mappings, status mappings, publishing configs), generated by `/aias configure-providers`
- `aias/contracts/readme-provider-config.md` — Canonical fail-fast service resolution contract
- `aias/contracts/readme-tracker-field-mapping.md` — Contract for tracker field mapping artifacts
- `aias/contracts/readme-knowledge-publishing-config.md` — Contract for knowledge publishing config artifacts
