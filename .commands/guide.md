# Guide (Framework Onboarding) — v2

## 1. Identity

**Command Type:** Type A — Chat-Only

You are generating an **operational guide** for the rho-aias development framework.
This command reads from the `rho-aias` skill and presents workflow profiles, artifact catalogs, command mappings, status lifecycles, and Structured Prompt examples in an actionable format.

**Skills referenced:** `rho-aias`.

---

## 2. Invocation / Usage

Invocation:
- `/guide` — main menu (overview of profiles, commands, and how to get started)
- `/guide --help` or `/guide -h` — same as no arguments
- `/guide feature` — step-by-step workflow for the `feature` profile
- `/guide bugfix` — step-by-step workflow for the `bugfix` profile
- `/guide refactor` — step-by-step workflow for the `refactor` profile
- `/guide enrichment` — step-by-step workflow for the `enrichment` profile
- `/guide delivery` — step-by-step workflow for the `delivery` profile
- `/guide commands` — table of all commands with recommended mode and profile association
- `/guide prompt` — Structured Prompt format with artifact reference fields and 3–4 practical examples
- `/guide status` — the 6 states of `status.md`, valid transitions, and lifecycle
- `/guide artifacts` — closed catalog of 12 artifact types + `status.md`
- `/guide classification` — Plan Classification (A/B/C) criteria, gates, and closure rules
- `/guide aias` — overview of the `/aias` command and CLI for artifact creation and project setup

Usage notes:
- Usable in any mode. Designed for onboarding and quick reference.
- All content is read dynamically from the `rho-aias` skill files (`SKILL.md`, `reference.md`, `examples.md`). Never hardcode framework details — if the skill changes, the guide reflects those changes automatically.

---

## 3. Inputs

This command may use **only** the following inputs:
- The subcommand from `$ARGUMENTS` (e.g., `feature`, `commands`, `prompt`)
- The `rho-aias` skill files:
  - `aias/.skills/rho-aias/SKILL.md`
  - `aias/.skills/rho-aias/reference.md`
  - `aias/.skills/rho-aias/examples.md`

Rules:
- Read the skill files at execution time. Do NOT rely on memorized content.
- If the skill files are not found, report the error and stop.
- If `$ARGUMENTS` does not match a known subcommand, show the main menu and suggest valid subcommands.

---

## 4. Output Contract (Format)

- The response MUST be rendered as **plain Markdown** in chat.
- No files are created. Output is chat-only.
- Use tables, bullet lists, and code blocks for readability.
- Keep output concise and actionable — this is a reference, not a tutorial.

---

## 5. Content Rules (Semantics)

- Output MUST be in **Spanish** for explanations and **English** for technical terms, artifact names, command names, and status values.
- Present information in execution order (what to do first, second, etc.).
- For profile subcommands (`feature`, `bugfix`, `refactor`, `enrichment`, `delivery`): present the step table from `reference.md` (with Mode/Chat columns) with practical guidance on when and how to invoke each command.
- For `commands`: build the table dynamically from the skill's command references.
- For `prompt`: show the Structured Prompt template (including artifact reference fields `ISSUE:`, `FIX:`, `ASSESSMENT:`, `TRACE:`) and 3–4 real-world examples covering different profiles.
- For `status`: show the 6 states, the transition diagram, and which command triggers each transition.
- For `artifacts`: show the closed catalog table (12 types) from `SKILL.md`.
- For `classification`: show the Plan Classification criteria (A/B/C), assignment/escalation rules, and closure requirements from `SKILL.md`.

---

## 6. Output Structure (Template)

### Subcommand: (none) / `--help` / `-h`

```
# Agentic-Driven Framework — Quick Reference

## Profiles
<table: profile name | description | typical commands in order>

## Getting Started
<3-step quick start: set TASK_DIR → choose profile → run first command>

## Available Subcommands
<table: subcommand | description>

Tip: Run `/guide <profile>` for step-by-step instructions.
```

### Subcommand: `feature` / `bugfix` / `refactor` / `enrichment` / `delivery`

```
# Profile: <name>

## Workflow Steps
<table from reference.md: step | chat | mode | command | artifacts produced | Tracker transition>

## How to Start
<Structured Prompt example for this profile, using artifact reference fields when applicable>

## Recommendations
<2-3 practical tips specific to this profile>
```

### Subcommand: `commands`

```
# Command Reference

<table: command | type (A/B) | recommended mode | profile(s) | what it does>
```

### Subcommand: `prompt`

```
# Structured Prompt Format

## Template
MODE: <mode>
REPO: <repoName>
TASK ID: <TrackerId>
TASK DIR: <taskId>
PROFILE: <feature|bugfix|refactor|enrichment|delivery>
PLAN: <planName>
ISSUE: <filename>
FIX: <filename>
ASSESSMENT: <filename>
TRACE: <filename>
FIGMA: <url>
CONTEXT: <background, current situation, what was requested>
TASK: <what to do, commands to chain>

## Artifact Reference Fields
<table from reference.md: field | artifact referenced | use case>

## Examples
<3-4 examples covering feature, bugfix (with ISSUE:/FIX:/ASSESSMENT:), enrichment, and a minimal invocation>
```

### Subcommand: `status`

```
# Status Lifecycle

## States
<table: status | meaning | entered when>

## Transitions
<transition diagram or list from reference.md>

## Tracker Mapping
<table: framework status | tracker status | triggered by>
```

### Subcommand: `artifacts`

```
# Artifact Catalog

<table from SKILL.md: # | file name | suffix | producer | description>

## Directory Structure
<tree diagram from SKILL.md>

## Discovery
<glob rules>
```

### Subcommand: `classification`

```
# Plan Classification (A / B / C)

## Criteria
<table from SKILL.md: type | scope | examples>

## Assignment and Escalation
- Assigned by: `/blueprint` in `status.md`
- Validated by: `/validate-plan`
- Escalated by: `/charter` (A→B, B→C — never downgrade)

## Closure Rules
<table: type | publication | approval | closure command>
```

---

## 7. Non-Goals / Forbidden Actions

This command MUST **NOT**:
- Create, modify, or delete any files
- Execute commands on behalf of the user
- Provide deep technical explanations (use `/explain` for that)
- Hardcode framework details — always read from the skill files
- Speculate about features not defined in the skill

---

## Notes

- `/guide` is designed for onboarding new team members and as a quick reference during active work.
- Pair with `/explain` when the user needs conceptual depth beyond operational guidance.
- The main menu intentionally fits in one screen to reduce cognitive load.
