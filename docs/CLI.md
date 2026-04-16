# Rho AIAS CLI Reference

The `aias` CLI is a Python script for interactive scaffolding, generation, and health checks of Rho AIAS artifacts.

**Location:** `aias/.canonical/generation/aias_cli.py`

**Requirements:** Python 3.10+ (standard library only)

**Run:**
```bash
python3 aias/.canonical/generation/aias_cli.py <subcommand> [options]
```

---

## Subcommands

### `init` — Project Onboarding

Full interactive onboarding in 6 steps:

1. **Detection** — checks for existing `RHOAIAS.md`, `stack-profile.md`, `stack-fragment.md`
2. **Context** — creates `RHOAIAS.md` (project name, platform, description, architecture, technologies)
3. **Stack profile** — creates `stack-profile.md` (language, build system, UI framework, testing, target tools, tasks directory)
4. **Stack fragment** — creates `stack-fragment.md` (build system integration: automatic discovery, manual project file, or hybrid)
5. **Context symlinks** — creates context symlinks → `RHOAIAS.md`, scoped by tool selection (`AGENTS.md` for cursor/windsurf/copilot, `CLAUDE.md` for claude, `codex.md` for codex)
6. **Generation** — runs `generate --shortcuts`

> **Provider configuration** is handled separately. Use `new --provider <category>` for skeleton configs, or `/aias configure-providers` in the AI assistant for MCP-assisted discovery.

```bash
python3 aias/.canonical/generation/aias_cli.py init
```

If all files exist, the CLI asks before overwriting. If some are missing, it creates only the missing ones.

---

### `new` — Create Artifacts

```bash
python3 aias/.canonical/generation/aias_cli.py new <flag> [name]
```

| Flag | Artifact | Name required | Output location |
|---|---|---|---|
| `-m`, `--mode` | Mode rule | Yes (kebab-case) | `aias-config/modes/<name>.mdc` |
| `-r`, `--rule` | Always-apply rule | Yes (kebab-case) | `aias-config/rules/<name>.mdc` |
| `-c`, `--command` | Command definition | Yes (kebab-case) | `aias/.commands/<name>.md` |
| `-s`, `--skill` | Skill | Yes (kebab-case) | `aias/.skills/<name>/SKILL.md` |
| `-P`, `--provider` | Provider config | Yes (category) | `aias-config/providers/<category>-config.md` |
| `-C`, `--context` | RHOAIAS.md | No | `RHOAIAS.md` |
| `-p`, `--stack-profile` | Stack profile | No | `stack-profile.md` |
| `-f`, `--stack-fragment` | Stack fragment | No | `stack-fragment.md` |

**Naming:** All artifact names must be kebab-case (`^[a-z][a-z0-9]*(-[a-z0-9]+)*$`).

**Collision detection:** If the target file already exists, the CLI asks before overwriting.

**Post-action:** All `new` types except `--provider` auto-run `generate --shortcuts` after creating the artifact. The generator reads `binding.generation.tools` from the stack profile to scope shortcut generation.

#### Examples

```bash
# Create a new mode
python3 aias/.canonical/generation/aias_cli.py new --mode code-review

# Create a new rule
python3 aias/.canonical/generation/aias_cli.py new --rule security-policy

# Create a new command
python3 aias/.canonical/generation/aias_cli.py new -c deploy

# Create the canonical handoff command
python3 aias/.canonical/generation/aias_cli.py new -c handoff

# Create a new skill
python3 aias/.canonical/generation/aias_cli.py new -s slack-mcp

# Create a provider config
python3 aias/.canonical/generation/aias_cli.py new -P tracker

# Create project context
python3 aias/.canonical/generation/aias_cli.py new --context

# Create stack profile
python3 aias/.canonical/generation/aias_cli.py new --stack-profile

# Create stack fragment
python3 aias/.canonical/generation/aias_cli.py new --stack-fragment
```

---

### `generate` — Run Generator

Invokes `generate_modes_and_rules.py` to produce canonical modes and rules.

```bash
# Canonical outputs only (modes + rules)
python3 aias/.canonical/generation/aias_cli.py generate

# Canonical + shortcuts for tools listed in stack profile
python3 aias/.canonical/generation/aias_cli.py generate --shortcuts

# Override: shortcuts for specific tools only (does not modify stack profile)
python3 aias/.canonical/generation/aias_cli.py generate --shortcuts --tools cursor,claude
```

With `--shortcuts`, the generator reads `binding.generation.tools` from `stack-profile.md` to determine which tools to produce shortcuts for. The optional `--tools <csv>` flag overrides the binding for that run without modifying the profile.

**Aliases:** `gen` for `generate`, `gen -s` for `generate --shortcuts`.

---

### `health` — Setup Verification

Runs setup verification checks and reports status.

```bash
python3 aias/.canonical/generation/aias_cli.py health
```

| # | Check | OK | WARN | FAIL |
|---|---|---|---|---|
| 1 | `RHOAIAS.md` exists | Exists | — | Not found |
| 1b | `RHOAIAS.md` freshness | Modified N days ago (N commits since) | Unfilled placeholders / stale (>60 days, >30 commits) | — |
| 2 | `stack-profile.md` exists | Exists | — | Not found |
| 3 | `stack-fragment.md` exists | Exists | — | Not found |
| 4 | `aias/` structure | Framework directories present | Some missing | `aias/` not found |
| 4b | `aias-config/` structure | All subdirectories present | Not found or some missing | — |
| 5 | Contracts exist | >= 10 files | — | Not found |
| 6 | Generator exists | Present | — | Not found |
| 7 | Shortcuts up to date | Counts match canonical (scoped to selected tools) | Divergence / no tools binding | — |
| 7b | Shortcut integrity | G6/G7 passed | Cannot import generator module | Issues found |
| 8 | Context symlinks | Expected symlinks → `RHOAIAS.md` (scoped to selected tools) | Missing, broken, or no tools binding | — |
| 9 | Provider configs | Config(s) present in `aias-config/providers/` | Missing or empty | — |
| 9b | Legacy providers | — | `aias-providers/` exists at root | — |
| 9c | Legacy rules/modes | — | `.mdc` files in `aias/.rules/` or `aias/.modes/` | — |
| 9d | Legacy shortcuts | — | Symlinks point to `aias/.rules/` or `aias/.modes/` | — |
| 9e | Legacy canonical bindings | — | `canonical_mode_output_dir` or `canonical_rule_output_dir` points to legacy location | — |
| 9f | Deprecated binding | — | `binding.generation.mode_output_dir` still present | — |
| 10 | Referenced files | All `resource_files` paths exist | Legacy paths (`aias-providers/`) | Missing `resource_files` key or missing files |
| 10b | Sections (`<type>`) | All mandatory sections present | TOC cross-reference inconsistency | Missing mandatory sections |
| 11 | Tasks directory | `binding.generation.tasks_dir` present and directory exists | Directory does not exist yet | Binding missing |

Each check reports a specific corrective action message (not a generic "Run aias init").

#### Legacy detection and repair

Legacy checks (9b, 9c, 9d, 9e, 9f, and legacy paths in check 10) detect pre-v7.6 file locations and deprecated bindings. Section validation (10b) detects missing mandatory sections in referenced provider files. These produce `[WARN]` or `[FAIL]`. When the AI agent runs `/aias health` and detects these issues, it offers interactive migration and repair gates (see `/aias` command § 9):

| Scenario | Detection | Action |
|---|---|---|
| `aias-providers/` at root | Check 9b | Copy to `aias-config/providers/`, update paths in configs |
| `.mdc` files in `aias/.rules/` or `aias/.modes/` | Check 9c | Re-run `aias generate --shortcuts` |
| Shortcuts pointing to `aias/.rules/` or `aias/.modes/` | Check 9d | Re-run `aias generate --shortcuts` |
| `resource_files` with `aias-providers/` prefix | Check 10 | Copy files to `aias-config/providers/<provider>/`, update configs |
| Missing mandatory sections in referenced files | Check 10b | Agent reads governing contract and patches missing sections (Scenario F) |

#### Post-submodule update flow

After updating the `aias/` submodule to a new version:

1. Run `generate --shortcuts` to regenerate modes, rules, and shortcuts into `aias-config/`.
2. Run `health` to detect any new checks or legacy warnings.
3. If legacy warnings are reported, run `/aias health` in the AI assistant to trigger assisted migration.

---

## Implicit Help

Any subcommand without required arguments shows its own help:

- `aias` or `aias --help` → general help
- `aias new` → artifact type flags

---

## Relationship with `/aias` Command

Both the CLI and the `/aias` chat command produce identical artifacts. The difference:

| Aspect | CLI (`aias_cli.py`) | Command (`/aias`) |
|---|---|---|
| Interface | Terminal via `input()` | Chat conversation |
| Validation | Deterministic (regex, length, non-empty) | Semantic (contract-aware smart suggestions) |
| Smart suggestions | No | Yes (explains, offers alternatives) |
| Bootstrapping | None — runs directly | Requires manual copy to IDE command path (see [QUICKSTART § Prerequisites](QUICKSTART.md#prerequisites-bootstrapping)) |
| Best for | Scripted/batch setup, CI | Interactive artifact creation with guidance |

Note: the CLI flag `-c` means `--command` for `aias new`. It is unrelated to command-specific invocation flags such as `/handoff -c <command>`.

---

## Related

- [QUICKSTART](QUICKSTART.md) — Getting started guide
- [Contracts](../contracts/) — Canonical artifact contracts
- [Generator README](../.canonical/generation/README.md) — Generator internals
- [WORKFLOWS](WORKFLOWS.md) — End-to-end workflow documentation
