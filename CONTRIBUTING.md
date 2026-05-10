# Contributing to Rho AIAS

Rho AIAS is a contract-driven framework. Every artifact type — modes, commands, skills, rules, tool adapters — follows an explicit contract that governs its structure, behavior, and quality criteria. This guide explains how to create or modify each artifact type while maintaining system integrity.

---

## The Contract System

Contracts are the canonical standards that govern every artifact type in Rho AIAS. They define structure, required fields, behavioral constraints, and quality criteria. If there is a conflict between an implementation and its governing contract, **the contract wins**.

All contracts live in `aias/contracts/` (15 contracts):

| Contract | Purpose |
|---|---|
| `readme-commands.md` | Command structure and categories (Advisory / Operative) |
| `readme-base-rule.md` | Base rule structure, invariant/parametrizable taxonomy |
| `readme-output-contract.md` | Output contract rules and fragment system |
| `readme-mode-rule.md` | Mode rule structure and design principles |
| `readme-skill.md` | Skill structure and separation of concerns |
| `readme-multi-agent-review.md` | Multi-agent review protocol (dimensions, dispatch, severity gates, sub-agent manifest) |
| `readme-provider-config.md` | Service provider configuration and fail-fast resolution |
| `readme-tracker-status-mapping.md` | Tracker status mapping and trigger naming |
| `readme-tracker-field-mapping.md` | Tracker field mapping (traceability, catalogs, format resolution) |
| `readme-knowledge-publishing-config.md` | Knowledge publishing configuration (hierarchy, navigation) |
| `readme-artifact.md` | Task artifact lifecycle and directory structure |
| `readme-stack-profile.md` | Stack profile structure and rule bindings |
| `readme-tool-adapter.md` | Tool adapter shortcut format and fidelity matrix |
| `readme-project-context.md` | Project context (`RHOAIAS.md`) single source of truth |
| `readme-versioning-policy.md` | Contract versioning scheme, deprecation policy, version registry |

Before creating or modifying any artifact, read the governing contract first.

---

## Version Management

Release metadata is versioned documentation, not runtime agent context.

- `aias/CHANGELOG.md` is the source of truth for the current framework version, versioning scheme, and release history.
- `AGENTS.md` MUST NOT keep the detailed release history; it SHOULD only point to `aias/CHANGELOG.md`.
- When bumping the framework version, update `aias/CHANGELOG.md` first.
- If a release changes architecture, workflows, or maintainer expectations, review references in `aias/README.md` and `aias/docs/ARCHITECTURE.md` as part of the same change.

### Contract Versioning

Individual contracts follow a **Major.Minor** versioning scheme independent of the framework version. See `aias/contracts/readme-versioning-policy.md` for:
- When to bump contract versions (major vs minor)
- Deprecation policy (minimum one major framework version coexistence)
- Backward compatibility rules

When modifying a contract, include the version bump in the same change. When submitting a PR that modifies a contract, reference it as: *"Complies with `readme-<name>.md` v<X.Y>"*.

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

## Creating a New Command (Advisory or Operative Skill)

Commands are now implemented as directory-form skills with `category: advisory` or `category: operative` and `disable-model-invocation: true`. The `aias new --command` flag is deprecated — use `aias new --skill` instead.

1. Read the contracts:
   - `aias/contracts/readme-skill.md` — Skill structure and category rules.
   - `aias/contracts/readme-commands.md` — Behavioral contract governing structure, quality criteria, and self-verification for advisory and operative skills.
2. Determine the category:
   - **Advisory** — Chat-only. Produces output in the conversation (analysis, reports, explanations). No side effects, no file writes.
   - **Operative** — Procedural/execution. Performs side effects (file writes, API calls, artifact creation).
3. Create the skill using the CLI:

```bash
python3 aias/.canonical/generation/aias_cli.py new --skill <name>
# → select "advisory" or "operative" when prompted for category
```

This creates `aias/.skills/<name>/SKILL.md` (framework) or `aias-config/skills/<name>/SKILL.md` (project) with the correct frontmatter, including `disable-model-invocation: true`.

4. Follow these rules:
   - Commands are **deterministic** — same input produces same behavior.
   - Commands are **procedural** — they execute steps, they do not perform deep reasoning (that is the mode's job).
   - Commands **do not infer missing intent** — if required input is absent, they halt and ask.
   - Each command must include a **self-verification checklist** of observable, mechanically verifiable side-effects.

5. Run the generator to produce shortcuts for all configured tools:

```bash
python3 aias/.canonical/generation/aias_cli.py generate --shortcuts
```

> **Migrating existing project custom commands?** Run `aias new --migrate-commands` for an interactive migration from `aias-config/commands/` to `aias-config/skills/` (`aias-config/commands/` is deprecated since v9.0; all new custom work must use `aias-config/skills/`).

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

## Creating or Extending a Sub-agent (Cursor only)

Sub-agents are specialized Cursor agents that operate as autonomous reviewers or auditors. They are distinct from skills — they run as separate agent instances **always dispatched** by `/peer-review` and `/self-review` (unconditionally, regardless of Plan Classification), and they have their own YAML frontmatter lifecycle.

**Canonical sub-agents** (maintained in `aias/.cursor/agents/`) are framework-level and should not be modified for project-specific needs. To extend or customize, add a sub-agent at the project level in `.cursor/agents/` (not symlinked from the framework).

### Frontmatter invariants

Every sub-agent `.md` file must include:

```yaml
---
name: <kebab-case-name>
description: <one-line purpose>
model: <model-slug>          # advisory; the user may override
readonly: true               # sub-agents must not write files
is_background: false         # must be false (reviewed inline, not backgrounded)
---
```

**`readonly: true`** is mandatory — sub-agents perform analysis, not implementation. **`is_background: false`** is mandatory — their output must be readable inline before the review continues. `model` is advisory; Cursor allows the user to override it.

> Do **not** add a `tools:` field — this is not a valid Cursor sub-agent frontmatter field.

### Review contract reference

`aias/contracts/readme-multi-agent-review.md` governs dispatch, severity gates, and the sub-agent manifest (which sub-agents exist and what each reviews). Consult this contract before adding or changing a sub-agent's scope.

### Registering a new sub-agent

1. Create `aias/.cursor/agents/<name>.md` (framework) or `.cursor/agents/<name>.md` (project-level).
2. Add the mandatory frontmatter (see above).
3. If it is a framework-level sub-agent, register it in the manifest section of `readme-multi-agent-review.md` and update `_ensure_review_subagent_symlinks()` in `aias_cli.py` to include the new file in `aias init` / `generate --shortcuts`.
4. Update `_check_review_subagent_integrity()` in `aias_cli.py` to validate the new sub-agent in `aias health`.
5. Run `aias health` to verify integrity.

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
| `aias init` | Full project onboarding (includes sub-agent symlinks for Cursor) |
| `aias new --mode <name>` | Create a new mode from the canonical template |
| `aias new --skill <name>` | Create a new skill directory and `SKILL.md` |
| `aias new --migrate-commands` | Migrate project custom commands to skills |
| `aias new --provider <category>` | Create a provider configuration |
| `aias generate --shortcuts` | Regenerate all artifacts, shortcuts, and sub-agent symlinks |
| `aias health` | Verify setup integrity (contracts, bindings, shortcuts, sub-agents) |

> `aias new --command` is deprecated. Use `aias new --skill` and select `advisory` or `operative` as the category.

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
- **If modifying a contract**, explain the downstream impact on existing artifacts (modes, commands, skills, rules, shortcuts) and confirm all affected artifacts have been updated. Bump the contract version per `readme-versioning-policy.md`.

---

## Related Documentation

- [CLI Reference](docs/CLI.md)
- [Generator README](.canonical/generation/README.md)
- [Quickstart](docs/QUICKSTART.md)
- [Workflows](docs/WORKFLOWS.md)
- [Service Abstraction](docs/SERVICE-ABSTRACTION.md)
