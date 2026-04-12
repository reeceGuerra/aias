# Quick Start Guide

Quick reference for getting started with the Rho AIAS configuration system.

---

## Setup

### Prerequisites (Bootstrapping)

The framework ships the `/aias` chat command at `aias/.commands/aias.md`, but your IDE doesn't know about it until you make it available. Before running `/aias init` in a chat agent, choose one of these paths:

| Path | When to use | Steps |
|---|---|---|
| **A. Copy the command** | Your IDE supports custom commands (e.g., Cursor) | Copy `aias/.commands/aias.md` → `.cursor/commands/aias.md` (or equivalent path for your tool). After `aias init` generates shortcuts, this manual copy is no longer needed for future commands. |
| **B. Use the CLI directly** | Your IDE does not support custom commands, or you prefer the terminal | Run `python3 aias/.canonical/generation/aias_cli.py init` — no command registration required. |
| **C. Follow instructions manually** | You want full control | Open `aias/.commands/aias.md`, read the command definition, and follow its steps in a chat agent conversation. |

> **Why is this necessary?** The `/aias` command bootstraps the entire workspace — but it cannot register itself. Once `aias init` completes and generates shortcuts (step 6–7), all other commands, modes, rules, and skills are available automatically via symlinks.

### Running Init

The fastest way to set up a new project is with the `aias` CLI:

```bash
python3 aias/.canonical/generation/aias_cli.py init
```

Or, if you copied the command (Path A):

```
/aias init
```

This guides you through creating `RHOAIAS.md`, `stack-profile.md`, `stack-fragment.md`, provider configs, context symlinks, and runs the generator. For individual artifacts, use `aias new` (see [CLI Reference](CLI.md)).

If the project is already set up, skip to **Core Concepts** below.

### Upgrading from v7.5

If your project was set up with v7.5 or earlier, update the `aias/` submodule and then:

1. Run `python3 aias/.canonical/generation/aias_cli.py generate --shortcuts` — regenerates rules and modes into `aias-config/` and updates shortcuts.
2. Run `python3 aias/.canonical/generation/aias_cli.py health` — detects legacy locations.
3. If legacy warnings appear, run `/aias health` in your AI assistant for interactive migration.

Key changes in v7.6: `aias/` is now read-only. Generated rules/modes moved from `aias/.rules/` and `aias/.modes/` to `aias-config/rules/` and `aias-config/modes/`. Provider configs moved from `aias-providers/` to `aias-config/providers/`. Custom commands and skills go to `aias-config/commands/` and `aias-config/skills/`.

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
- `/brief` — Generate feature brief
- `/report` — Generate validated bug RCA report and publish RCA fields when requested
- `/pr` — Generate PR description
- `/enrich` — Analyze and refine a tracker ticket; produces `analysis.product.md`, `dor.plan.md`, `dod.plan.md`; publishes to knowledge provider; transitions `pending_dor → ready` (use with `@product` or standalone)
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
| `/brief` | Feature brief | Planning context | Markdown brief |
| `/report` | Bug RCA report | Debug context | Markdown RCA summary |
| `/self-review` | Review your own local work | `@review` + local code / TASK_DIR | Findings + readiness verdict in chat |
| `/peer-review` | Review a PR or third-party change | `@review` + PR URL/number | Findings + VCS-ready snippets + general review comment |
| `/handoff` | Prepare the next chat with explicit context | Current chat context + optional TASK_DIR | Single Markdown handoff snippet |
| `/pr` | PR description | Implementation context | PR template |
| `/enrich` | Refine task: product analysis + DoR/DoD + publish | Task ID + `@product` context | Task directory + `pending_dor → ready` |
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
- **Contracts:** `aias/contracts/readme-commands.md` (commands), `readme-mode-rule.md` (modes), `readme-skill.md` (skills)
