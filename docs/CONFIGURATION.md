# Configuration Guide

This guide covers everything you need to configure Rho AIAS for your project. The fastest path is `aias init`, which walks you through all steps interactively:

```bash
python3 aias/.canonical/generation/aias_cli.py init
```

If you prefer to understand each piece before running anything, read on.

---

## Overview

Rho AIAS configuration is composed of a small set of artifacts, each with a specific role:

| Artifact | Location | Purpose |
|---|---|---|
| `RHOAIAS.md` | Project root | Project context (single source of truth) |
| `stack-profile.md` | Project root | Technology stack declaration for generation |
| `stack-fragment.md` | Project root | Build system integration content |
| Service configs | `aias-config/providers/` | External provider bindings |
| Context symlinks | Project root | Tool-specific symlinks → `RHOAIAS.md` |
| Editor settings | `vscode/` (optional) | VSCode/Cursor workspace settings |
| Project docs | `docs/` (optional) | Style guides, conventions |

The first three are required. Services are needed only if your workflow involves external providers (tracker, wiki, design tool, VCS). The rest is optional. See [Progressive Adoption](PROGRESSIVE-ADOPTION.md) for which configuration is needed at each adoption level.

---

## Project Context (RHOAIAS.md)

`RHOAIAS.md` is the single source of truth for project context. Every AI coding tool reads this file to understand what the project is, how it is structured, and what conventions apply.

**Location:** repository root (fixed name).

**Tool-specific context files** (`AGENTS.md`, `CLAUDE.md`, `codex.md`, `GEMINI.md`) are symlinks to `RHOAIAS.md`. Each tool reads the full project context directly via filesystem resolution — no content duplication.

### How to create

```bash
python3 aias/.canonical/generation/aias_cli.py new --context
```

### What to fill in

| Section | Content |
|---|---|
| Project Overview | Name, platform, description, role in the ecosystem |
| Project Structure | Main directories and their purpose (tree format) |
| Conventions | Architecture pattern, UI framework, DI approach, code style, testing strategy |
| Key Technologies | Language, version, frameworks, build tools, key libraries |
| Build and Test | Build commands, test commands, CI/CD notes, environment details |
| Related Documentation | Links to style guides, external docs (optional) |
| Rho AIAS Integration | Pre-filled; references canonical artifact locations (do not modify) |

### Contract reference

`aias/contracts/readme-project-context.md`

---

## Stack Profile (stack-profile.md)

The stack profile declares the technology stack and capabilities consumed by the generator. It drives deterministic generation of modes, rules, and shortcuts.

**Location:** repository root (fixed name).

### How to create

```bash
python3 aias/.canonical/generation/aias_cli.py new --stack-profile
```

### Key sections

| Section | Declares |
|---|---|
| Core stack | Language, UI framework, build tool |
| Architecture | Patterns, layers, module boundaries |
| Tooling | Linters, formatters, static analysis |
| Testing | Frameworks, coverage strategy, snapshot tools |
| Design system | Token source, component library, mapping approach |
| MCP capabilities | Which MCP servers are available (Xcode, Figma, Atlassian, GitHub) |
| Globs | File patterns for mode-specific focus |
| Generation bindings | Rule and mode bindings consumed during generation |

### Contract reference

`aias/contracts/readme-stack-profile.md`

---

## Stack Fragment (stack-fragment.md)

The stack fragment provides build system integration content that is too large or structured to fit inside the stack profile. The generator injects it into the output contract rule.

**Location:** repository root (fixed name).

### Fragment types

| Type | Scope | When to use |
|---|---|---|
| A | Embedded rules only | Simple integration (e.g., header format, naming conventions) |
| B | Embedded + external file rules | Medium complexity (e.g., project file references, target configuration) |
| C | Full multi-file procedures | Complex integration (e.g., multi-target builds, code generation pipelines) |

### How to create

```bash
python3 aias/.canonical/generation/aias_cli.py new --stack-fragment
```

### Contract reference

`aias/contracts/readme-output-contract.md` -- Build System Integration Fragments

---

## Service Configuration

Rho AIAS resolves external providers by category, not by vendor name. Each category has a dedicated config file in `aias-config/providers/`:

| Category | Config file | Purpose | Example provider |
|---|---|---|---|
| `tracker` | `aias-config/providers/tracker-config.md` | Task/issue tracking | Jira, Linear |
| `knowledge` | `aias-config/providers/knowledge-config.md` | Publishing and archive | Confluence, Notion |
| `design` | `aias-config/providers/design-config.md` | Design context retrieval | Figma |
| `vcs` | `aias-config/providers/vcs-config.md` | Version control operations | GitHub, GitLab |

### Config structure

Every service config declares:

- **`active_provider`** -- Which provider is currently active for this category
- **`skill_binding`** -- Which skill implements the provider integration (skill name + capabilities)
- **Provider-specific parameters** -- Under `providers.<provider_name>` (URLs, project keys, space keys, etc.)

The framework resolves by category at runtime. If a config is missing, invalid, or unresolvable, the dependent operation aborts immediately (fail-fast). There is no silent fallback behavior.

### How to create

```bash
python3 aias/.canonical/generation/aias_cli.py new --provider <category>
```

Where `<category>` is one of: `tracker`, `knowledge`, `design`, `vcs`.

### Contract reference

`aias/contracts/readme-provider-config.md`

---

## Setting Up for Your Stack

This section walks through the complete onboarding sequence.

### 1. Clone or copy `aias/` into your project

Copy the `aias/` directory into your repository root. This brings in all commands, canonical sources, contracts, skills, and generation infrastructure.

### 2. Run `aias init`

```bash
python3 aias/.canonical/generation/aias_cli.py init
```

The interactive flow creates the following artifacts:

1. `RHOAIAS.md` -- project context (fills in based on your answers)
2. `stack-profile.md` -- technology stack declaration (includes target tool selection via `binding.generation.tools` and tasks directory via `binding.generation.tasks_dir`)
3. `stack-fragment.md` -- build system integration content
4. Context symlinks -- `AGENTS.md`, `CLAUDE.md`, `codex.md`, `GEMINI.md` → `RHOAIAS.md`
5. Generated outputs -- runs `generate --shortcuts` to produce modes, rules, and tool shortcuts (scoped to selected tools)

If some files already exist, the CLI detects them and asks before overwriting.

### 3. Configure services (optional)

Set up external provider bindings in `aias-config/providers/` for any categories your workflow uses.

#### Recommended: AI-assisted discovery (`/aias configure-providers`)

In your AI coding tool, run `/aias configure-providers`. The agent:

1. Detects existing `*-config.md` files in `aias-config/providers/`.
2. Connects to the MCP server for the selected provider.
3. Discovers field schemas, statuses, spaces, and hierarchies from live data.
4. Generates complete configuration files in `aias-config/providers/<provider_id>/` (e.g., `aias-config/providers/atlassian/jira-field-mapping.md`).
5. Updates `resource_files` and `*_source` paths in the provider config.

If MCP is unavailable, the agent falls back to generating contractual skeletons for manual completion.

#### Alternative: CLI skeleton (`aias new --provider`)

Create basic provider config skeletons via the CLI:

```bash
# Create a tracker config (e.g., Jira)
python3 aias/.canonical/generation/aias_cli.py new --provider tracker

# Create a knowledge config (e.g., Confluence)
python3 aias/.canonical/generation/aias_cli.py new --provider knowledge

# Create a design config (e.g., Figma)
python3 aias/.canonical/generation/aias_cli.py new --provider design

# Create a VCS config (e.g., GitHub)
python3 aias/.canonical/generation/aias_cli.py new --provider vcs
```

For `tracker` and `knowledge` categories, the generated config includes an empty `resource_files: []`. Run `/aias configure-providers` afterward to populate the referenced files, or create them manually following the governing contracts (`readme-tracker-field-mapping.md`, `readme-knowledge-publishing-config.md`, `readme-tracker-status-mapping.md`).

### 4. Verify setup

```bash
python3 aias/.canonical/generation/aias_cli.py health
```

This runs 11 checks covering file existence, directory structure, contract presence, generator availability, shortcut freshness, context symlinks, and provider referenced files. Any failures include specific remediation guidance. Legacy configuration locations are reported as warnings (see [CLI.md](CLI.md) § Legacy detection).

### 5. Start working

Open your AI coding tool (Cursor, Claude Code, Windsurf, GitHub Copilot, Codex, Gemini) and use the Structured Prompt format:

```
MODE: @planning
REPO: my-project
TASK ID: PROJ-100
TASK DIR: PROJ-100
PROFILE: feature
CONTEXT: <describe the problem or requirement>
TASK: <what to do>
```

> This is a subset. See [QUICKSTART.md § Structured Prompt](QUICKSTART.md#structured-prompt-primary-workflow) for the complete field reference including PROFILE, PLAN, FIGMA, CONTEXT, artifact reference fields (ISSUE, FIX, ASSESSMENT, TRACE), and aliases (DIR, TICKET).

---

## Editor Settings (Optional)

VSCode/Cursor workspace settings can be stored in a `vscode/` directory at the project root for shared team configuration (e.g., recommended extensions, formatting settings).

`.code-workspace` files are user-local and not versioned.

Neither is required for the framework to function. Rho AIAS operates entirely through its own artifact system.

---

## Project-Level Documentation (Optional)

Project-specific documentation (style guides, design documentation, architecture decisions, conventions) lives in a `docs/` directory at the project root.

This is separate from framework documentation:

| Directory | Contains |
|---|---|
| `aias/docs/` | Framework documentation (this guide, CLI reference, workflows) |
| `docs/` | Project-specific documentation (style guides, conventions, ADRs) |

---

## Regeneration

Regeneration is needed after modifying generation inputs:

- `stack-profile.md` -- changes to stack declaration, bindings, or globs
- `stack-fragment.md` -- changes to build system integration content
- Canonical sources in `aias/.canonical/` -- mode templates, base rule, output contract

### Command

```bash
python3 aias/.canonical/generation/aias_cli.py generate --shortcuts
```

This produces canonical modes, rules, and tool shortcuts scoped to the tools listed in `binding.generation.tools` (stack profile). The operation is idempotent: running it twice on unchanged inputs produces zero diffs.

To temporarily override tool selection without modifying the stack profile:

```bash
python3 aias/.canonical/generation/aias_cli.py generate --shortcuts --tools cursor,claude
```

---

## Related Documentation

- [Quick Start](QUICKSTART.md) -- Getting started guide and structured prompt format
- [CLI Reference](CLI.md) -- `aias` subcommands, flags, and examples
- [Workflows](WORKFLOWS.md) -- End-to-end workflow documentation (feature, bugfix, enrichment, CI/CD)
- [Service Abstraction](SERVICE-ABSTRACTION.md) -- Service layer architecture and provider switching
