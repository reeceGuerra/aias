---
name: rho-aias
description: Canonical protocol for artifact-driven development workflows. Use when the user works on a task that produces or consumes artifacts under <resolved_tasks_dir>/<TASK_ID>/ (default ~/.cursor/plans/) — including planning, implementation, enrichment, publishing, or any command that reads/writes task artifacts.
---

# Agentic-Driven Development

## PURPOSE

Teach the agent the canonical protocol for managing task artifacts across the full development lifecycle. This skill defines what artifacts exist, where they live, how they are discovered and loaded, and how the agent must track progress, sync to the resolved knowledge provider, and coordinate with the resolved tracker provider.

This is a **system skill** — it is referenced by every mode and every artifact-producing or artifact-consuming command. It provides the shared foundation that keeps all workflows consistent.

---

## WHEN TO USE

Use this skill when:
- **Creating artifacts** — `/blueprint`, `/enrich`, `/issue`, `/fix`, `/charter`, `/trace`, `/assessment`
- **Consuming artifacts** — `/implement`, `/validate-plan`, `/pr`, `/commit`, `/consolidate-plan`, `/brief`, `/report`, `/assessment`
- **Reviewing with artifact context** — `/self-review`, `/peer-review`, `/handoff`
- **Publishing artifacts** — `/publish`, or any command that triggers progressive knowledge sync (Phase 5)
- **Syncing with tracker** — `/enrich`, `/blueprint`, `/pr`, `/commit` (Phase 6)
- **Reasoning about task state** — any mode that loads from `<resolved_tasks_dir>/<TASK_ID>/` (default: `~/.cursor/plans/`)

Commands that reference this skill: `/aias`, `/blueprint`, `/brief`, `/charter`, `/commit`, `/consolidate-plan`, `/enrich`, `/fix`, `/guide`, `/handoff`, `/implement`, `/issue`, `/peer-review`, `/pr`, `/publish`, `/report`, `/self-review`, `/trace`, `/validate-plan`.

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
| A (Local/Low-Risk) | Bug fixes, small refactors, config | No knowledge publishing required | Not required | `/report` or `/brief` to tracker |
| B (Medium-Impact) | Features, UX/UI, internal tools | Knowledge publish via `/publish` | Not required (unless objection) | `/publish` |
| C (Critical/Strategic) | Arch redesigns, cross-team, launches | Knowledge publish via `/publish` | Required before `/implement` | `/publish` |

- Assigned by `/blueprint` in `status.md` (`classification: A | B | C`).
- Validated by `/validate-plan` (gap if missing).
- `/charter` can **escalate** (A→B, B→C) but **never downgrade**.

Important terminology:
- **Command Type A** refers to chat-only command behavior in `readme-commands.md`.
- **Plan Classification A** refers to the low-risk lifecycle class in this skill.

### Governance in Artifacts

The `## Governance` section is an optional section inside `increments.plan.md` that defines **per-increment custom gates**. It follows the Governance-in-Artifact Schema defined in `readme-commands.md`.

| Classification | `## Governance` section | Behavior |
|----------------|------------------------|----------|
| Type A | MUST NOT be generated | No custom gates; baseline feedback after each increment |
| Type B | MAY be generated | Custom gates only when risk or cross-team dependencies warrant them |
| Type C | MUST be generated | At least one Approval gate before the first increment |

**Producer/consumer model:**
- `/blueprint` is the **governance producer** — it writes the `## Governance` section during Phase 3 based on classification and risk assessment.
- `/implement` is the **governance consumer** — it reads classification from `status.md` and custom gates from `increments.plan.md`, resolving which gates to fire at each trigger point.

**Precedence:** Custom gates in `## Governance` take precedence over classification baselines at their specific trigger points.

**`/charter` escalation:** When `/charter` escalates classification (A→B, B→C), subsequent `/implement` runs automatically inherit the higher governance baseline. If a Type C plan lacks a `## Governance` section, `/validate-plan` flags it as a gap.

---

## LOADING PROTOCOL (Summary)

Every command that interacts with artifacts MUST follow this 7-phase protocol:

```
Phase 0 — DIRECTORY RESOLUTION
  Resolve TASK_DIR from context (Structured Prompt, user input, or directory listing).
  If TASK_DIR does not exist and command is a producer: create it.
  If TASK_DIR does not exist and command is a consumer: abort.

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
  5c. UNCONDITIONAL KNOWLEDGE SYNC
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
  5d. Completion check

Phase 6 — TRACKER SYNC
  Triggered only by: /enrich, /blueprint, /pr, /commit
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
