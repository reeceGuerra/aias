---
name: cross-repo-integration
description: Coordinate work that spans multiple repositories using an integration workspace and dependency-aware sequencing. Use when a change requires planning/execution handoff across repos (for example shared package + consuming app).
category: knowledge
version: 1.0.0
---

# Cross-Repo Integration

## PURPOSE

Provide a deterministic, human-orchestrated protocol for coordinating tasks that affect multiple repositories while preserving per-repo ownership and minimizing integration drift.

---

## OPERATIONS

### 1) Build Cross-Repo Dependency Graph

When integration work starts:
1. Identify all impacted repos and dependency direction.
2. Map parent ticket + per-repo subtasks (Jira hierarchy as cross-repo graph).
3. Classify each repo node as producer (creates change), adopter (consumes change), or both.

### 2) Plan in Source Repositories First

Protocol:
1. Create/refresh plan in producer repo.
2. Create/refresh plan in adopter repo with explicit integration gap placeholder.
3. Keep each repo plan authoritative for repo-local implementation details.

### 3) Orchestrate in Integration Workspace

In the integration workspace:
1. Resolve inter-repo sequencing (which repo lands first, compatibility windows).
2. Track required version constraints/contracts.
3. Produce a synchronized execution checklist that references each repo task.

### 4) Execute and Reconcile

1. Execute repo-local changes in their native focused workspace.
2. Return to integration workspace to validate graph-level completeness.
3. Record cross-repo decisions and residual risks for handoff.

---

## SAFETY RULES

- Integration workspace orchestration is coordination-only by default.
- Do not auto-modify repositories outside the currently active repo context.
- Any cross-repo write action must be explicitly requested and confirmed by the user.
- If dependency graph is ambiguous, stop and ask for clarification before sequencing work.

---

## Scoping analysis (v1.0, in scope)

### Problem

In integration workspaces, commands from multiple repos can collide (same command name, different repo context), causing ambiguous execution targeting.

### In-scope evaluation

This skill explicitly evaluates **per-folder command scoping** in v1.0:
- Detect whether current CWD maps to one repo root unambiguously.
- Prefer command resolution from the nearest repo context.
- If command name exists in multiple repos and CWD does not disambiguate, require explicit repo selector.

### v1.0 decision

Adopt **nearest-repo-first resolution** with explicit fallback:
1. Resolve active repo from CWD ancestry.
2. Execute command in resolved repo scope.
3. If unresolved/ambiguous, prompt user to select target repo.

This keeps integration orchestration deterministic while avoiding accidental cross-repo command leakage.

---

## Workspace convention (optional)

Integration workspaces MAY define:

```json
"integration_skill_enabled": true
```

This flag is optional and informational. `@integration` mode remains the primary activation mechanism.

---

## REFERENCE

For execution templates and example sequencing patterns, see [reference.md](reference.md).
