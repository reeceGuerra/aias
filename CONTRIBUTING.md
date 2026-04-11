# Contributing to Rho AIAS

Rho AIAS is a contract-driven framework. Every artifact type — modes, commands, skills, rules, tool adapters — follows an explicit contract that governs its structure, behavior, and quality criteria. This guide explains how to create or modify each artifact type while maintaining system integrity.

---

## The Contract System

Contracts are the canonical standards that govern every artifact type in Rho AIAS. They define structure, required fields, behavioral constraints, and quality criteria. If there is a conflict between an implementation and its governing contract, **the contract wins**.

All contracts live in `aias/contracts/` (13 contracts):

| Contract | Purpose |
|---|---|
| `readme-commands.md` | Command structure and categories (Type A / Type B) |
| `readme-base-rule.md` | Base rule structure, invariant/parametrizable taxonomy |
| `readme-output-contract.md` | Output contract rules and fragment system |
| `readme-mode-rule.md` | Mode rule structure and design principles |
| `readme-skill.md` | Skill structure and separation of concerns |
| `readme-provider-config.md` | Service provider configuration and fail-fast resolution |
| `readme-tracker-status-mapping.md` | Tracker status mapping and trigger naming |
| `readme-tracker-field-mapping.md` | Tracker field mapping (traceability, catalogs, format resolution) |
| `readme-knowledge-publishing-config.md` | Knowledge publishing configuration (hierarchy, navigation) |
| `readme-artifact.md` | Task artifact lifecycle and directory structure |
| `readme-stack-profile.md` | Stack profile structure and rule bindings |
| `readme-tool-adapter.md` | Tool adapter shortcut format and fidelity matrix |
| `readme-project-context.md` | Project context (`RHOAIAS.md`) single source of truth |

Before creating or modifying any artifact, read the governing contract first.

---

## Version Management

Release metadata is versioned documentation, not runtime agent context.

- `aias/CHANGELOG.md` is the source of truth for the current framework version, versioning scheme, and release history.
- `AGENTS.md` must not keep the detailed release history; it should only point to `aias/CHANGELOG.md`.
- When bumping the framework version, update `aias/CHANGELOG.md` first.
- If a release changes architecture, workflows, or maintainer expectations, review references in `aias/README.md` and `aias/docs/ARCHITECTURE.md` as part of the same change.

---

## Creating a New Mode

1. Read the contract: `aias/contracts/readme-mode-rule.md`.
2. Create the canonical template in `aias/.canonical/<mode-name>.mdc`, or use the CLI:

```bash
python3 aias/.canonical/generation/aias_cli.py new --mode <name>
```

3. Follow these design principles:
   - **Brevity** — 30-80 lines. Modes are concise behavioral directives, not documentation.
   - **Conceptual Focus** — Define *what to think about*, not step-by-step procedures (that is the command's job).
   - **Stability** — Avoid embedding frequently changing details. Delegate volatile content to skills or commands.
   - **One mode per chat** — Each mode defines a single cognitive posture. Modes do not overlap.

4. Add generation bindings in the target repository's `stack-profile.md` so the generator knows which repos use this mode.
5. Run the generator to produce shortcuts for all configured tools:

```bash
python3 aias/.canonical/generation/aias_cli.py generate --shortcuts
```

---

## Creating a New Command

1. Read the contract: `aias/contracts/readme-commands.md`.
2. Determine the category:
   - **Type A** — Chat-only. Produces output in the conversation (analysis, reports, explanations).
   - **Type B** — Procedural/execution. Performs side effects (file writes, API calls, artifact creation).
3. Create the command definition in `aias/.commands/<name>.md` (framework) or `aias-config/commands/<name>.md` (project), or use the CLI:

```bash
python3 aias/.canonical/generation/aias_cli.py new --command <name>
```

4. Follow these rules:
   - Commands are **deterministic** — same input produces same behavior.
   - Commands are **procedural** — they execute steps, they do not perform deep reasoning (that is the mode's job).
   - Commands **do not infer missing intent** — if required input is absent, they halt and ask.

5. Run the generator to produce shortcuts for all configured tools:

```bash
python3 aias/.canonical/generation/aias_cli.py generate --shortcuts
```

---

## Creating a New Skill

1. Read the contract: `aias/contracts/readme-skill.md`.
2. Create the skill directory and entry point at `aias/.skills/<name>/SKILL.md` (framework) or `aias-config/skills/<name>/SKILL.md` (project), or use the CLI:

```bash
python3 aias/.canonical/generation/aias_cli.py new --skill <name>
```

3. Follow these rules:
   - **Single-domain** — One external service or knowledge area per skill.
   - **Operational** — Skills describe *how* to interact with a service, not *when*.
   - **Stateless** — No persistent state between invocations.
   - **Read-only by default** — Write operations require explicit opt-in.
   - A skill never decides *when* to be used. That decision belongs to the consuming mode or command.

4. Run the generator to produce shortcuts for all configured tools:

```bash
python3 aias/.canonical/generation/aias_cli.py generate --shortcuts
```

---

## Adding Tool Support

1. Read the contract: `aias/contracts/readme-tool-adapter.md`.
2. Understand the shortcut model: shortcuts are **path references** to canonical sources. They contain zero duplicated content. The canonical source in `aias/` is always authoritative.
3. Add the new tool's shortcut format to the generator (`generate_modes_and_rules.py`):
   - Define how the tool discovers modes, commands, skills, and rules.
   - Implement the shortcut file format the tool expects.
4. Implement validation:
   - **Pre-flight (G5)** — Verify the tool's output directories exist and are writable.
   - **Post-flight (G6-G7)** — Verify all generated shortcuts resolve to valid canonical sources.
5. Update the fidelity matrix in `aias/contracts/readme-tool-adapter.md` to document what the new tool supports and at what fidelity level.

---

## Using the CLI

The CLI scaffolds new artifacts and validates existing ones:

| Command | Purpose |
|---|---|
| `aias init` | Full project onboarding |
| `aias new --mode <name>` | Create a new mode from the canonical template |
| `aias new --command <name>` | Create a new command definition |
| `aias new --skill <name>` | Create a new skill directory and `SKILL.md` |
| `aias new --provider <category>` | Create a provider configuration |
| `aias generate --shortcuts` | Regenerate all artifacts and shortcuts |
| `aias health` | Verify setup integrity (contracts, bindings, shortcuts) |

See [CLI Reference](docs/CLI.md) for full documentation.

---

## Naming Conventions

All artifact names must be **kebab-case**, matching the pattern:

```
^[a-z][a-z0-9]*(-[a-z0-9]+)*$
```

Examples: `code-review`, `slack-mcp`, `deploy`, `incremental-decomposition`.

This convention applies uniformly to contracts, skills, commands, modes, and generated files. Generated files preserve the canonical name without transformation.

---

## Quality Criteria

Every contribution must satisfy these checks:

1. The new or modified artifact **complies with its governing contract**.
2. `aias health` passes with no errors.
3. The generator is **idempotent**: running it twice in sequence produces zero diffs.
4. No artifact introduces **content duplication** between canonical sources (`aias/`) and shortcut directories (`.cursor/`, `.claude/`, `.codex/`, etc.).

---

## PR Expectations

When submitting a pull request:

- **Reference the governing contract** in the PR description (e.g., "Complies with `readme-skill.md` v1.x").
- **Include evidence of contract compliance** — quote the relevant contract sections or provide a compliance checklist.
- **Verify idempotency** — run the generator before and after your changes; confirm zero diffs on the second run.
- **If modifying a contract**, explain the downstream impact on existing artifacts (modes, commands, skills, rules, shortcuts) and confirm all affected artifacts have been updated.

---

## Related Documentation

- [CLI Reference](docs/CLI.md)
- [Generator README](.canonical/generation/README.md)
- [Quickstart](docs/QUICKSTART.md)
- [Workflows](docs/WORKFLOWS.md)
- [Service Abstraction](docs/SERVICE-ABSTRACTION.md)
