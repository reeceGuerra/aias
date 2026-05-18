# Quick Start Guide

Quick reference for getting started with the Rho AIAS configuration system.

---

## Setup

### Prerequisites (Bootstrapping)

The framework ships the `/aias` skill at `aias/.skills/aias/SKILL.md`, but your IDE doesn't know about it until you make it available. Before running `/aias init` in a chat agent, choose one of these paths:

| Option | When to use | Steps |
|---|---|---|
| **A. Copy the skill** | Your IDE supports custom skills or commands (e.g., Cursor) | Copy `aias/.skills/aias/SKILL.md` → `.cursor/skills/aias/SKILL.md` (or equivalent path for your tool). After `aias init` generates shortcuts, this manual copy is no longer needed for future skills. |
| **B. Use the CLI directly** | Your IDE does not support custom skills, or you prefer the terminal | Run `python3 aias/.canonical/generation/aias_cli.py init` — no skill registration required. |
| **C. Follow instructions manually** | You want full control | Open `aias/.skills/aias/SKILL.md`, read the skill definition, and follow its steps in a chat agent conversation. |

> **Why is this necessary?** The `/aias` skill bootstraps the entire workspace — but it cannot register itself. Once `aias init` completes and generates shortcuts (step 6–7), all other commands (as advisory/operative skills), modes, rules, and skills are available automatically via symlinks.

### Running Init

The fastest way to set up a new project is with the `aias` CLI:

```bash
python3 aias/.canonical/generation/aias_cli.py init
```

Or, if you copied the command (Option A):

```
/aias init
```

This guides you through creating `RHOAIAS.md`, `stack-profile.md`, `stack-fragment.md`, provider configs, context symlinks, and runs the generator. For individual artifacts, use `aias new` (see [CLI Reference](CLI.md)).

If the project is already set up, skip to **Core Concepts** below.

### Upgrading from v8.x

If your project was set up with v8.x, update the `aias/` submodule and then:

1. Run `python3 aias/.canonical/generation/aias_cli.py generate --shortcuts` — regenerates shortcuts including new `.cursor/skills/` paths.
2. Run `python3 aias/.canonical/generation/aias_cli.py health` — detects legacy command shortcuts and `aias-config/commands/` entries.
3. Run `/aias health` in your AI assistant for interactive migration of any legacy shortcut targets.

Key changes in v9.0: Custom commands migrated to command-shaped skills — new custom work must use `aias-config/skills/<name>/SKILL.md` (not `aias-config/commands/`). Multi-agent review added: run `aias init` or `aias health` to create sub-agent symlinks under `.cursor/agents/`. If upgrading from v8.0–v8.9, migrate historical Plan Classification labels to current values: `minor|standard|critical` in all `status.md` `classification` fields.

**Upgrading to v9.2:** Canonical sources reorganized into `aias/.canonical/rules/`, `aias/.canonical/modes/`, and `aias/.canonical/subagents/`. Sub-agents are now a project-owned generated surface at `aias-config/subagents/`. Run `aias generate --shortcuts` to regenerate sub-agent copies and refresh `.cursor/agents/` symlinks. Review `git diff aias-config/subagents/` before committing.

**Upgrading to v9.3:** Three additive hardening items, no migration required for in-flight tasks. `/handoff` now uses lstat-based path resolution (no symlink-follow); fallbacks to `aias-config/` are explicitly annotated with `[fallback reason: …]`. `readme-knowledge-publishing-config.md` v1.1 adds a Title Canonicity invariant — Confluence artifact titles MUST stay as `<TASK_ID>: <filename>` (e.g., `ABC-12345: dod.plan.md`); humanized titles (`ABC-12345: Definition of Done`) are now FORBIDDEN. Existing Confluence pages with humanized titles are not auto-rewritten; the next publish creates the canonical title and may produce a duplicate that must be manually deduplicated. `review-rubric` v1.1 makes Scope discipline always-on (diff-only findings; legacy posture applied automatically); no flag changes.

**Upgrading to v9.4:** Six items shipped as a cohort; no schema-breaking migration. Key changes: (1) `/self-review` now writes `dispatches[]` telemetry into `status.md` `command_log` when multi-agent review fires — legacy `command_log` entries without `dispatches[]` remain valid (backward compatible). (2) Sub-Agent Tool Boundary: sub-agents MUST NOT invoke any tool runtime (MCP, shell, git, file writes, etc.). If you maintain custom sub-agents under `aias-config/subagents/`, ensure they do not include tool-call instructions; run `aias generate --shortcuts` to refresh canonical sub-agents (review `git diff aias-config/subagents/` before committing). (3) `/peer-review` gains Phase 0 — Pre-Resolve Sub-Agent Context with a Gate: VCS Permission Recovery for tool-permission failures during PR diff retrieval. (4) `/enrich` and `/report` now use exhaustive tracker read (`fields=['*all']` + `expand=['renderedFields', 'names', 'schema']`); custom fields you previously missed will now surface. (5) `/enrich --brief` posts in English (regardless of chat language) as a collaborative refinement note (`## Refinement Notes — <TASK_ID>`) — re-run `/enrich --brief` if you want existing brief comments updated. (6) Producer skills emit canonical heading shapes — no `## Category N: <Title>` bleed-through into Confluence. (7) `/blueprint` Category 6 now fires when DoR declares `orientation: user_facing` even without a design URL, producing a minimal `specs.design.md` with a "Design provider was not consulted" disclosure note.

**Upgrading from v9.4 to v9.5:** One architectural redesign — the DoR/DoD amendment flow moves to a unified TODO model. **Schema-breaking for in-flight tasks that contain a legacy `## Proposed DoR/DoD Amendments` combined block in `technical.plan.md`** (no auto-split is performed; `/validate-plan` v2.0.0 will hard-fail with `[STATE: blocked]`).

What changed in v9.5 (no action required for tasks that have not yet passed `/blueprint`):

1. `/blueprint` v5.3.0 — Phase 1 stages DoR/DoD gaps into two separate sections (`## Proposed DoR Amendments` and `## Proposed DoD Amendments`); the combined `## Proposed DoR/DoD Amendments` section is FORBIDDEN.
2. `/validate-plan` v2.0.0 (**MAJOR**) eliminates the Amendment Approval gate and registers each Proposed entry as a TODO in `technical.plan.md` frontmatter with `kind: amendment_dor` or `kind: amendment_dod` (`kind: validation` remains for plan-gap TODOs). The `## Proposed` sections stay in the body as documentation until resolution.
3. `/consolidate-plan` v2.0.0 (**MAJOR**) becomes the sole resolver across all `kind` values. A single "Update Approval" gate fires per todo; on approval, `validation` writes to the named artifact, `amendment_dor` writes to `dor.plan.md` and removes the bullet from `## Proposed DoR Amendments`, `amendment_dod` writes to `dod.plan.md` and removes the bullet from `## Proposed DoD Amendments`. When a Proposed section becomes empty, the heading is removed.
4. The legacy `apply_local` Phase 5c exclusion is retired; `dor.plan.md` / `dod.plan.md` modifications participate in Phase 5c as normal `modified` artifacts.

> Historical note (v9.5 only): `/blueprint` v5.3.0 originally shipped with a "Path A" that applied inline answers directly to `dor.plan.md` / `dod.plan.md` and logged them in `## Resolution Log`. v9.6 removed Path A as an architectural regression (see "Upgrading from v9.5 to v9.6" below). Tasks that wrote a `## Resolution Log` under v9.5 MAY keep it; new emissions are FORBIDDEN.

Migration steps for in-flight tasks that already wrote `## Proposed DoR/DoD Amendments` under `/validate-plan` v1.x:

1. Open `technical.plan.md` and rename `## Proposed DoR/DoD Amendments` to two separate headings: `## Proposed DoR Amendments` and `## Proposed DoD Amendments`.
2. Move each bullet to whichever section matches its target artifact (DoR-vs-DoD is usually unambiguous from the bullet text). When in doubt, ask the planner; do NOT guess.
3. Save the file and re-run `/validate-plan` — it will register the moved bullets as TODOs (`kind: amendment_dor` / `kind: amendment_dod`) and continue normally.
4. Run `/consolidate-plan` to resolve the registered TODOs one by one. There is no Amendment Approval gate to acknowledge.

If `/validate-plan` reports `[STATE: blocked] legacy '## Proposed DoR/DoD Amendments' block detected`, the manual split above is required before progress can resume; the hard-fail is intentional — auto-split was rejected to avoid silent mis-routing of DoR-vs-DoD intent. See `aias/CHANGELOG.md` § v9.5 and `BACKLOG.md` § Wave 3 (BL-S79) for the full architectural rationale.

**Upgrading from v9.5 to v9.6:** Refinement Contract Hardening — repairs the v9.5 architectural regression where `/blueprint`'s Path A allowed direct modification of `dor.plan.md` / `dod.plan.md` with a fragmented audit trail. **No schema migration required for in-flight tasks** — v9.6 changes are behavioral, additive on `status.md`, and backward compatible on bullet shape.

What changed in v9.6 (in-flight tasks continue to work without manual intervention):

1. **Refinement Artifact Mutation Invariant** (`aias/contracts/readme-artifact.md` v2.3) — CREATE for `dor.plan.md` / `dod.plan.md` is restricted to `/enrich` (primary) and `/blueprint` (bug exception only: `profile: bugfix` + `feasibility.assessment.md` + DoR/DoD missing). MODIFY is restricted to `/enrich --refresh` and `/consolidate-plan`. All other commands are FORBIDDEN to mutate DoR/DoD, even with explicit user confirmation in chat.
2. **`/blueprint` v5.4.0** — Path A removed. When the user answers a DoR/DoD gap inline, the answer is captured as a `**Inline confirmation**: <value> (YYYY-MM-DD)` sub-field marker inside the Proposed Amendment bullet — never applied directly to the source artifact. The marker becomes the default value for `/consolidate-plan`'s Update Approval gate. A new precondition gate aborts non-bugfix profiles when `dor.plan.md` / `dod.plan.md` are missing.
3. **`/enrich` v1.3.0 — `--refresh` flag** — re-reads the tracker exhaustively (description + custom fields + comment thread), re-derives DoR/DoD, diffs against on-disk artifacts, and fires `Gate: Refresh Approval` + `Sub-Gate: Amendment Reconciliation` per bullet. Use whenever PM/QA/design update the ticket after the original refinement. Sets `status.md last_refreshed_at: <UTC>` on success; does NOT modify `refinement_validated`. Incompatible with `--brief` / `--fields`.
4. **`/validate-plan` v2.1.0** — multi-line bullet parsing (parent line + sub-fields including `**Inline confirmation**:`); backward compatible with v9.5 single-line bullets via parent-line fallback. Does NOT remove or modify the `**Inline confirmation**:` sub-field.
5. **`/consolidate-plan` v2.1.0** — parses the `**Inline confirmation**:` marker and uses its value as the Update Approval gate default; on apply, removes the entire multi-line bullet (parent + sub-bullets). Explicit clarifications added: team notification is dev discretion, tracker freshness is dev discretion, automatic tracker writes are FORBIDDEN.
6. **`status.md last_refreshed_at`** — new optional field (absent ≡ `null`); set by `/enrich --refresh` on successful apply.
7. **TODO lifecycle** — clarified as `pending → completed | deleted-from-frontmatter` (no `cancelled` terminal state). Deletion occurs when `/enrich --refresh` Amendment Reconciliation supersedes a TODO; audit lives in `command_log` + git history + knowledge provider page versions.
8. **`## Resolution Log` deprecated** — pre-existing logs in legacy artifacts MAY remain; new emissions are FORBIDDEN. Audit trail now lives entirely in `command_log` + git + knowledge provider page versions.
9. **`expand` parameter fix (BL-S83)** — pre-existing bug since v9.4: `getJiraIssue` `expand` parameter is a comma-separated string, not an array. Fixed in `enrich`, `report`, and `atlassian-mcp` skills. If you maintain custom skills that call `getJiraIssue` with `expand=[…]`, switch to `expand='…,…'`.

No migration steps required. If your in-flight task contains a v9.5 `## Resolution Log`, leave it as-is — historical artifacts are preserved.

---

### Upgrading from v7.5

If your project was set up with v7.5 or earlier, update the `aias/` submodule and then:

1. Run `python3 aias/.canonical/generation/aias_cli.py generate --shortcuts` — regenerates rules and modes into `aias-config/` and updates shortcuts.
2. Run `python3 aias/.canonical/generation/aias_cli.py health` — detects legacy locations.
3. If legacy warnings appear, run `/aias health` in your AI assistant for interactive migration.

Key changes in v7.6: `aias/` is now read-only. Generated rules/modes moved from `aias/.rules/` (retired, v7.6) and `aias/.modes/` (retired, v7.6) to `aias-config/rules/` and `aias-config/modes/`. Provider configs moved from `aias-providers/` (retired, v7.5) to `aias-config/providers/`. Historical note: custom commands and skills went to `aias-config/commands/` and `aias-config/skills/` in v7.6; `aias-config/commands/` is deprecated since v9.0 and new custom work must use `aias-config/skills/<name>/SKILL.md`.

---

## Core Concepts

> **New to the framework?** You don't need to learn everything at once. See [Progressive Adoption](PROGRESSIVE-ADOPTION.md) for a 3-level path from minimal setup to full governance.

### Modes (How to Think)

Modes define **how to think** about a task. They generate raw, unstructured data.

**Available Modes:**
- `@planning` — Planning and requirements analysis
- `@delivery` — Delivery assessment (readiness, effort, viability, impact, risks)
- `@qa` — QA bug reporting and testing
- `@debug` — Debugging and root cause analysis
- `@review` — Code review
- `@dev` — Developer (production-ready code). Use `/implement` for plan-driven execution.
- `@product` — Product analysis and conceptual exploration
- `@devops` — CI/CD pipelines, private dependency resolution, build orchestration
- `@integration` — Integration testing, API contract validation, end-to-end flows

**Usage:**
```
@planning

TASK: <describe what you want to plan>
```

---

### Commands (How to Execute)

Commands define **how to execute** and format output. They structure data from modes.

**Available Commands:**
- `/blueprint` — Collect and structure plan data into directory artifacts (use with `@planning`)
- `/charter` — Structure delivery data into delivery charter (writes to task directory)
- `/issue` — Structure QA data into bug report (writes to task directory)
- `/fix` — Structure debug data into fix analysis (writes to task directory)
- `/report` — Generate validated bug RCA report and publish RCA fields when requested
- `/pr` — Generate PR description
- `/enrich` — Analyze and refine a tracker ticket; produces `analysis.product.md`, `dor.plan.md`, `dod.plan.md`; publishes to knowledge provider. Optional flags: `--brief` (post enrichment brief as Jira comment), `--fields` (write structured fields to tracker), `--refresh` (v9.6+: re-read tracker drift and reconcile into local DoR/DoD via `Refresh Approval` + per-bullet `Amendment Reconciliation` gates; incompatible with `--brief` / `--fields`)
- `/explain` — Concept-focused learning response (use in any mode, natural in `@product`)
- `/trace` — Generate log instrumentation plan; writes to task directory (use with `@qa` or `@debug`)
- `/assessment` — Evaluate fix feasibility; bridges `/fix` to `/blueprint` in bugfix flows (use with `@dev`)
- `/validate-plan` — Validate plan alignment with DoR/DoD; process DoR/DoD amendments
- `/consolidate-plan` — Work through plan gaps one by one
- `/implement` — Execute plan increment by increment with governance gates (use with `@dev`)
- `/publish` — Reconcile remaining artifacts, generate Plan Delta, and formally close the task
- `/guide` — Operational reference for the rho-aias framework (profiles, commands, prompt format, status lifecycle, artifacts)
- `/self-review` — Review your own local work (use with `@review`)
- `/peer-review` — Review a PR or third-party change (use with `@review`)
- `/handoff` — Generate an operational Markdown handoff snippet for the next chat or agent
- `/commit` — Stage and commit files
- `/aias` — Framework management (health checks, configuration, scaffolding)
- `/copyedit` — Technical writing review and refinement

**Usage:**
```
/blueprint

INPUT:
<paste raw data from @planning>
```

---

## Structured Prompt (Primary Workflow)

The most efficient way to interact with the system. One message with structured context and command chaining.

### Format

```
MODE: <mode>                 (required)
REPO: <repo>                 (when working in a specific repo)
TASK ID: <task-id>            (enables tracker-provider enrichment via service config)
TASK DIR: <task-id>           (artifact dir: <resolved_tasks_dir>/<task-id>/ — default: ~/.cursor/plans/)
PROFILE: <profile>           (feature|bugfix|refactor|enrichment|delivery — sets workflow profile)
PLAN: <plan-name>            (when continuing from an existing plan)
ISSUE: <filename>            (loads report.issue.md for context or update)
FIX: <filename>              (loads analysis.fix.md for context)
ASSESSMENT: <filename>       (loads feasibility.assessment.md for planning)
TRACE: <filename>            (loads instrumentation.trace.md for implementation)
FIGMA: <url>                 (triggers figma-mcp enrichment)
CONTEXT: <background>        (problem description, current state, what was requested)
TASK: <instruction>          (what to do + optional command chaining)
```

All fields except MODE and TASK are optional — use only what the task needs. When `TASK ID` is provided and `TASK DIR` is not, the task directory defaults to the task identifier. `DIR` is an allowed alias for `TASK DIR`. `TICKET` remains a legacy alias for `TASK ID` for compatibility.

### Fail-Fast Guardrails (Service-Dependent Steps)

For commands that depend on tracker/knowledge/design/VCS providers:

- Resolve provider by category from `aias-config/providers/<category>-config.md`.
- Validate active provider, skill binding, and required mapping/config sources.
- If config or mapping is missing/invalid/unresolvable, abort the dependent operation and request correction.
- Do not continue with silent fallback behavior.

### Examples

**Planning a new feature:**
```
MODE: @planning
REPO: mobilemax-dev
TASK ID: MAX-12761
TASK DIR: MAX-12761
PROFILE: feature
FIGMA: https://figma.com/design/abc123/...
CONTEXT: Product requested a new candidate search feature with filters
         by location, work mode, and availability.
TASK: Analyze the requirement. When done, execute /blueprint.
```

**Debugging a crash:**
```
MODE: @debug
REPO: mobilemax-dev
TASK ID: MAX-12850
TASK DIR: MAX-12850
PROFILE: bugfix
CONTEXT: The candidate list crashes when filtering by "Remote only".
         The API returns null for the candidates array instead of an
         empty array. QA confirmed on all devices.
TASK: Analyze the root cause. When done, execute /fix.
```

**Implementing from a plan:**
```
MODE: @dev
REPO: mobilemax-dev
TASK DIR: MAX-12761
TASK: Execute /implement for this plan.
```

**Enriching a vague ticket:**
```
MODE: @product
TASK ID: MAX-13001
TASK DIR: MAX-13001
PROFILE: enrichment
CONTEXT: Ticket only says "Add export button to reports".
         No acceptance criteria, no design, no scope definition.
TASK: Analyze with product frameworks. When done, execute /enrich.
```

**Refactoring with a plan:**
```
MODE: @planning
TASK ID: MAX-13200
TASK DIR: MAX-13200
PROFILE: refactor
CONTEXT: Extracting the authentication layer into a standalone module.
TASK: Analyze the refactor scope. When done, execute /blueprint.
```

**Delivery assessment:**
```
MODE: @delivery
TASK ID: MAX-13300
TASK DIR: MAX-13300
PROFILE: delivery
CONTEXT: Evaluating readiness for the Q2 search feature release.
TASK: Assess the plan and produce a charter.
```

**Quick code review:**
```
MODE: @review
REPO: mobilemax-dev
TASK DIR: MAX-12850
TASK: Review the changes on the current branch. When done, /self-review.
```

**Operational handoff to the next chat:**
```
/handoff -m @planning -c /blueprint
```

---

## Quick Reference

### Modes

| Mode | Purpose | Output |
|------|---------|--------|
| `@planning` | Plan features/requirements (use with `/blueprint` for full data collection) | Raw planning data |
| `@delivery` | Assess readiness, effort, viability, risks | Raw delivery data |
| `@qa` | Report bugs | Raw QA data |
| `@debug` | Analyze bugs | Raw debug data |
| `@review` | Review code | Structured review |
| `@dev` | Write code (use `/implement` for plans) | Production code |
| `@product` | Product analysis, conceptual exploration | Conceptual ideas, enriched requirements |
| `@integration` | Coordinate cross-repo changes | Coordination guidance |
| `@devops` | CI/CD pipelines, private deps, build orchestration | Pipeline configs, scripts |

### Commands

| Command | Purpose | Input | Output |
|---------|---------|-------|--------|
| `/blueprint` | Collect and structure plan data into directory artifacts | `@planning` context | `<resolved_tasks_dir>/<TASK_ID>/` |
| `/charter` | Structure delivery charter | `@delivery` data | Task directory |
| `/implement` | Execute plan increment by increment | Plan in task directory | Code changes |
| `/issue` | Structure bug report | `@qa` data | Task directory |
| `/fix` | Structure fix analysis | `@debug` data | Task directory |
| `/report` | Bug RCA report | Debug context | Markdown RCA summary |
| `/self-review` | Review your own local work | `@review` + local code / TASK_DIR | Findings + readiness verdict in chat |
| `/peer-review` | Review a PR or third-party change | `@review` + PR URL/number | Findings + VCS-ready snippets + general review comment |
| `/handoff` | Prepare the next chat with explicit context | Current chat context + optional TASK_DIR | Single Markdown handoff snippet |
| `/pr` | PR description | Implementation context | PR template |
| `/enrich` | Refine task: product analysis + DoR/DoD + publish | Task ID + `@product` context + optional `--brief`/`--fields` | Task directory (+ brief comment if `--brief`) |
| `/explain` | Concept learning | Topic or question | Structured explanation (chat) |
| `/trace` | Log instrumentation plan | `@qa` or `@debug` context | Task directory |
| `/assessment` | Evaluate fix feasibility | `@dev` + fix + issue | Task directory |
| `/validate-plan` | Validate plan alignment with DoR/DoD | Plan in task directory | Alignment verdict + amendment resolution |
| `/consolidate-plan` | Work through plan gaps | Plan in task directory | Updated plan artifacts |
| `/publish` | Reconcile + close task (all classifications) | Task directory | Resolved knowledge provider archive + delta + closure data. Mode-agnostic. |
| `/commit` | Commit changes | Git status (automatic) | Git commit |
| `/aias` | Framework management | Subcommand + flags | Health, config, scaffolding |
| `/copyedit` | Technical writing review | Document content | Refined text |
| `/guide` | Operational reference | Topic or subcommand | Framework reference (chat) |

---

## Recommended Models per Mode

Each mode performs best with a specific model type. Cursor does not auto-select models per mode — use this table as a reference when choosing manually.

| Mode | Recommended Model | Why |
|---|---|---|
| `@planning` | opus-4.6 | Deep reasoning for architecture decisions and requirement analysis |
| `@delivery` | opus-4.6 | Complex evaluation of readiness, viability, and risk |
| `@debug` | opus-4.6 | Multi-hypothesis root cause analysis requires deep reasoning |
| `@dev` | gpt-5.3-codex | Fast, accurate code generation optimized for implementation |
| `@review` | sonnet-4.6 | Balanced analysis speed with thorough code inspection |
| `@qa` | sonnet-4.6 | Systematic test coverage with efficient execution |
| `@product` | sonnet-4.6 | Broad conceptual exploration with good product analysis |
| `@integration` | sonnet-4.6 | Cross-repo coordination requires balanced reasoning |
| `@devops` | sonnet-4.6 | Pipeline configuration with practical accuracy |

**General guidance:**
- **opus** — Use for tasks requiring deep reasoning, multi-step analysis, or architectural decisions
- **codex** — Use for tasks requiring fast, accurate code generation
- **sonnet** — Use for tasks requiring balanced analysis and execution speed

---

## Workspace Setup

Each workspace has:
- `base.mdc` — Always-applied behavior rules (governed by `aias/contracts/readme-base-rule.md`, generated from canonical source with stack profile bindings)
- `RHOAIAS.md` (via `AGENTS.md` symlink) — Project context
- `output-contract.mdc` — Output format and build system integration rules (governed by `aias/contracts/readme-output-contract.md`, generated from canonical source with stack profile bindings)

To create or regenerate workspace artifacts, use `aias init` or individual `aias new` subcommands (see [CLI Reference](CLI.md)).

---

## Example: Your First Feature

> This tutorial corresponds to **Level 1** of the [Progressive Adoption](PROGRESSIVE-ADOPTION.md) model — only `@planning`, `@dev`, `/blueprint`, `/implement`, and `/commit` are needed.

**Step 1: Refine** (product analysis + DoR/DoD)
```
MODE: @product
REPO: mobilemax-dev
TASK ID: MAX-14000
CONTEXT: Product wants a user profile screen where users can view and
         edit their name, email, and phone number.
TASK: Analyze with product frameworks. When done, /enrich MAX-14000.
```

**Step 2: Plan** (new chat)
```
MODE: @planning
REPO: mobilemax-dev
TASK ID: MAX-14000
TASK DIR: MAX-14000
FIGMA: https://figma.com/design/abc123/user-profile
CONTEXT: Requirement refined — DoR/DoD in TASK_DIR.
TASK: Analyze the requirement. When done, /blueprint.
```

**Step 3: Validate** (same chat or new)
```
/validate-plan
```

**Step 4: Implement** (new chat)
```
MODE: @dev
REPO: mobilemax-dev
TASK DIR: MAX-14000
TASK: /implement
```

**Step 5: Commit, PR & Close**
```
/commit
```
```
/pr
```
```
/publish
```

---

## Further Reading

- **Detailed workflows:** [WORKFLOWS.md](WORKFLOWS.md) — Feature development, bug fix, enrichment, CI/CD, integration, and all other end-to-end flows
- **Artifact catalog and skill loading protocol:** `aias/.skills/rho-aias/SKILL.md` — Artifact types, skill loading protocol, Plan Classification, one-mode-per-chat rule
- **CLI reference:** [CLI.md](CLI.md) — `aias` subcommands, flags, and examples
- **Framework guide:** Run `/guide` for operational reference (profiles, commands, status lifecycle, artifacts)
- **Contracts:** `aias/contracts/readme-commands.md` (behavioral contract for advisory/operative skills), `readme-mode-rule.md` (modes), `readme-skill.md` (all five skill categories), `readme-multi-agent-review.md` (multi-agent review protocol)
