# Project Context Contract — Rho AIAS Configuration System (v1.0)

> **Keyword convention**: This contract uses RFC-2119 keywords (MUST, MUST NOT, SHOULD, MAY).
> See [readme-commands.md](readme-commands.md) § RFC-2119 Keyword Policy for definitions.

This document defines the **canonical contract** for `RHOAIAS.md` — the single source of truth for project context in any repository that adopts Rho AIAS.

It exists to:
- Define the structure and purpose of `RHOAIAS.md`
- Establish the relationship between `RHOAIAS.md` and tool-specific context wrappers
- Ensure consistency across adopter projects
- Prevent context duplication across tools

This document is written **for maintainers** of the Rho AIAS configuration system.

---

## What is RHOAIAS.md?

`RHOAIAS.md` is a **project context file** placed at the root of any repository that adopts Rho AIAS. It is the single source of truth for project context — all tool-specific context files (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `codex.md`) are shortcuts that point to this file.

### Characteristics

- **Single source of truth** — All project context lives here; tool-specific files are shortcuts
- **Template-driven** — Adopters fill in a template with their project-specific information
- **Tool-agnostic** — Written in plain Markdown, readable by any tool
- **Root location** — MUST be in the repository root
- **Comprehensive** — Covers all aspects a tool needs to understand the project

### What RHOAIAS.md is NOT

| Is | Is NOT |
|---|---|
| Project context for adopter repositories | Context for the Rho AIAS meta-workspace |
| A template with placeholders | A pre-filled document |
| The single source of truth | One of many context files |
| Tool-agnostic Markdown | Tool-specific format |

---

## Relationship with Tool-Specific Context Files

Each AI coding tool has its own context file at the repository root. These are **symlinks** to `RHOAIAS.md` — each tool reads the full project context directly via filesystem resolution:

| Tool | Context file | Mechanism |
|---|---|---|
| Cursor | `AGENTS.md` | Symlink → `RHOAIAS.md` |
| Claude Code | `CLAUDE.md` | Symlink → `RHOAIAS.md` |
| Windsurf | `AGENTS.md` | Symlink → `RHOAIAS.md` (shared with Cursor/Copilot) |
| GitHub Copilot | `AGENTS.md` | Symlink → `RHOAIAS.md` (shared with Cursor/Windsurf) |
| Codex CLI | `codex.md` | Symlink → `RHOAIAS.md` |
| Gemini | `GEMINI.md` | Symlink → `RHOAIAS.md` |

**Zero duplication principle:** No tool-specific context file may contain project context. They are symlinks to `RHOAIAS.md` — no content duplication, no LLM interpretation required.

---

## Relationship with the Meta-Workspace

The Rho AIAS meta-workspace (this repository) has its own `AGENTS.md` that describes the framework itself. This file is **not** replaced or renamed by `RHOAIAS.md`.

- `AGENTS.md` (meta-workspace root) → Describes the Rho AIAS framework
- `RHOAIAS.md` (adopter project root) → Template for adopter projects

These serve different purposes and coexist independently.

---

## Mandatory Structure

`RHOAIAS.md` MUST include the following sections in this order:

### 1. Project Overview (Required)

Describe what the project is, its role in the ecosystem, and target platform(s).

### 2. Project Structure (Required)

List the main directories and their purpose, using tree format.

### 3. Conventions (Required)

Document architecture pattern, UI framework, DI approach, code style, and testing strategy.

### 4. Key Technologies (Required)

List language, version, frameworks, build tools, and key libraries.

### 5. Build and Test (Required)

Document build commands, test commands, CI/CD notes, and environment details.

### 6. Related Documentation (Optional)

Links to style guides, READMEs, external docs, and contract references.

### 7. Rho AIAS Integration (Required — Fixed Content)

This section is pre-filled and references the canonical artifact locations:

```markdown
## Rho AIAS Integration

This project uses [Rho AIAS](https://github.com/rho-aias/aias) for AI-assisted development.

- **Rules**: `aias-config/rules/` — Generated behavioral rules (always-apply and output contracts)
- **Modes**: `aias-config/modes/` — Generated task-specific modes (planning, dev, QA, debug, review, product, integration)
- **Commands**: `aias/.commands/` (framework) + `aias-config/commands/` (project) — Command definitions
- **Skills**: `aias/.skills/` (framework) + `aias-config/skills/` (project) — Reusable operational skills
- **Providers**: `aias-config/providers/` — Provider configuration files

> This file is the single source of truth for project context. All tool-specific config files (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `codex.md`) are shortcuts to this file.
```

---

## Quality Criteria

A valid `RHOAIAS.md`:

1. Contains all required sections with project-specific content
2. Has a pre-filled `Rho AIAS Integration` section (not modified by adopters)
3. Is placed at the repository root
4. Provides enough context for any AI tool to understand the project
5. Does not contain behavioral rules (those belong in `base.mdc`)
6. Does not contain mode-specific instructions (those belong in mode rules)

---

## Generation vs Filled

The `RHOAIAS.md` file exists in two states:

| State | How it's created | Content |
|---|---|---|
| **Generated** | `aias init` (CLI) or `/aias new --context` (chat) | Sections with placeholder instructions based on user inputs |
| **Filled** | Adopter project root | Sections with actual project content |

The generated file uses the format `< instruction text >` for each placeholder to guide adopters. The contract above (§ Mandatory Structure) is the single source of truth for the expected structure — there are no intermediate template files on disk.

---

## Freshness Lifecycle

`RHOAIAS.md` is not a static artifact. As a project evolves — new modules, changed dependencies, restructured directories — the file MUST be kept current to preserve agent context quality across all modes and commands.

### Three-layer freshness model

| Layer | Mechanism | Trigger | Action |
|-------|-----------|---------|--------|
| **In-workflow** (proactive) | `/blueprint` impact analysis | Every task that goes through `/blueprint` | Sets `rhoaias_update` field in `status.md`; gates in `/commit` and `/pr` remind the user |
| **Passive detection** | `aias health` staleness check | On-demand health check | Reports WARN when `RHOAIAS.md` is stale (age + commit activity) or contains unfilled placeholders |
| **Manual catch-up** | `/aias refresh-context` | User invocation | Delta-first: searches published `delta.publish.md` for deferred/skipped context sync; falls back to filesystem/git log. Proposes section-level diffs with approval gate |

### Drift signals

The following signals indicate that `RHOAIAS.md` MAY need updating:

- **Project Structure** — new top-level directories or modules not documented
- **Key Technologies** — dependency manifest changes (new frameworks, language upgrades)
- **Conventions** — architecture pattern changes, new DI approach, testing strategy shift
- **Build and Test** — new test targets, CI/CD pipeline changes

### Update governance

- `RHOAIAS.md` MUST NOT be modified without human approval. All automated flows (blueprint detection, health warnings, refresh-context proposals) operate through gates — the framework informs and proposes, the human decides.
- The `rhoaias_update` field in `status.md` tracks freshness state per task. See `reference.md` § `status.md` Format for the field definition and valid states.
- Tasks that bypass `/blueprint` (ad-hoc `/implement`) do not activate the in-workflow freshness flow. This is a known limitation — ad-hoc work is outside the governed workflow.
- `/publish` records the `rhoaias_update` outcome in `delta.publish.md` as a `RHOAIAS.md Context Sync` section. This makes deltas the **primary explicit source** for `/aias refresh-context` when a knowledge provider is available — the command searches deltas with `deferred` or `skipped` status to identify tasks that impacted project context but did not update `RHOAIAS.md`. Deltas published before this feature (without the section) are ignored by `refresh-context`.

---

## Related Contracts

- `readme-tool-adapter.md` — Contract for shortcut files (context symlinks → `RHOAIAS.md`)
- `readme-base-rule.md` — Contract for base rules (behavioral rules, not project context)

---

This document is the **source of truth** for project context structure, the `RHOAIAS.md` lifecycle, and the freshness governance model.
