# Mode, Rule, and Shortcut Generation (Phase 2 + Phase 4 + Phase 5)

This directory contains the maintenance-time generation flow for platform modes, workspace rules, and multi-tool shortcuts.

## Goal

Generate committed mode and rule files for:

**Canonical outputs**:
- `aias-config/modes/*.mdc` — Generated platform modes
- `aias-config/rules/base.mdc` — Generated base rule (flat)
- `aias-config/rules/output-contract.mdc` — Generated output contract (flat)

**Shortcuts** (Phase 5, with `--shortcuts` flag):
- `.cursor/rules/*.mdc` — Rules + modes for Cursor
- `.cursor/commands/*.md` — Commands for Cursor
- `.cursor/skills/<name>/SKILL.md` — Skills for Cursor
- `.claude/rules/*.md` — Rules + modes for Claude Code (with `paths:` for modes)
- `.claude/skills/<name>/SKILL.md` — Skills for Claude Code
- `.windsurf/rules/*.md` — Always-apply rules for Windsurf
- `.github/copilot-instructions.md` — Aggregated rules for GitHub Copilot
- `.github/instructions/*.instructions.md` — Modes for GitHub Copilot (with `applyTo:`)
- `.github/agents/*.md` — Commands for GitHub Copilot
- `.codex/commands/*.md` — Commands for Codex
- `.agents/skills/<name>/SKILL.md` — Skills for Codex

from:

- `aias/.canonical/*.mdc` (mode templates)
- `aias/.canonical/base-rule.md` (canonical base rule)
- `aias/.canonical/output-contract.md` (canonical output contract)
- `<repo_root>/stack-fragment.md` (build system integration — one per repo, fixed name)
- `<repo_root>/stack-profile.md` (one per repo, fixed name)

## Deterministic inputs

- **Mode templates** provide shared mode logic with `{{#if capability}}` conditionals.
- **Rule templates** provide shared rule structure with `{{#section}}...{{/section}}` Mustache-style conditionals.
- **Stack fragment** (`<repo_root>/stack-fragment.md`) stores build system integration content (too large for stack profile bindings). One per repo.
- **Stack profile** (`<repo_root>/stack-profile.md`) provides `binding.*` values: mode frontmatter, capability flags, base rule bindings (`binding.rule.base.*`), and output contract bindings (`binding.rule.output_contract.*`). One per repo.

## Pre-flight Validation Protocol

Before any file is generated, the script runs 6 sequential validation gates that accumulate all errors and abort without modifying files if any gate fails.

| Gate | Name | What it checks |
|---|---|---|
| **G0** | Infrastructure | Canonical sources (`base-rule.md`, `output-contract.md`) exist and contain a `` ```markdown `` code block. Fragment file exists. All 9 canonical mode templates exist. |
| **G1** | Profile Discovery | `stack-profile.md` exists at repo root. Profile is readable and parses into non-empty bindings. `generation.stack_id` is present and `generation.mode_output_dir` is set to `aias-config/modes`. |
| **G2** | Mode Binding Completeness | For every profile × mode, the 4 frontmatter keys (`description`, `model`, `color`, `globs`) are present and non-empty. |
| **G3** | Rule Binding Completeness | For every discovered workspace: all required base rule keys (10) and output contract keys (4) resolve (workspace → shared → platform fallback). `profile` binding is present. |
| **G4** | Fragment Validation | `stack-fragment.md` exists at repo root, is non-empty, and contains at least one UPPERCASE section header. |
| **G5** | Output Directory | `aias-config/rules/` and `aias-config/modes/` exist or can be created. |

### Post-flight Validation (only with `--shortcuts`)

Post-flight gates are **fatal**: if any G6/G7 check fails, the generator exits with code 1 (generation output is preserved but the process signals failure).

| Gate | Name | What it checks |
|---|---|---|
| **G6** | Shortcut Consistency | Every canonical rule and mode has corresponding shortcuts for all supported tools (Cursor, Claude Code, Windsurf, GitHub Copilot, Codex). Commands validated for Cursor, Copilot, and Codex. Skills validated for Cursor, Claude Code, and Codex. |
| **G7** | No Content Duplication | No enriched text shortcut exceeds 500 bytes (symlinks are exempt). Aggregated files (`copilot-instructions.md`) must not exceed 1500 bytes. Checked across all shortcut directories including `.codex/commands`, `.agents/skills`, `.cursor/skills`, `.claude/skills`. |

## Generator behavior

`generate_modes_and_rules.py` performs:

### Mode generation

All 9 modes (`planning`, `dev`, `qa`, `debug`, `review`, `product`, `integration`, `delivery`, `devops`) are template-based. Transversal modes (`delivery`, `devops`) have built-in default bindings — stack-profile overrides are optional.

1. Reads `binding.*` keys from stack profiles.
2. Resolves stack identity.
3. Loads canonical mode templates (all from `aias/.canonical/*.mdc`).
4. Resolves per-mode frontmatter: explicit bindings take priority, then built-in defaults for transversal modes.
5. Renders conditional blocks (`{{#if ...}}...{{/if}}`).
6. Replaces placeholders (`{{key}}`).
7. Removes template-only comments.
8. Injects header `GENERATED — DO NOT EDIT` after frontmatter.
9. Writes to canonical path (`aias-config/modes/`).

### Rule generation

1. Discovers workspace IDs from `binding.rule.base.<ws_id>.description` keys.
2. Skips manual-maintenance exceptions (currently: `xctemplates-dev`).
3. Resolves bindings with fallback: workspace-specific → shared (`*_shared`) → platform-level.
4. Extracts template content from markdown code blocks in canonical templates.
5. Renders Mustache-style sections (`{{#key}}...{{/key}}`) with standalone tag line handling.
6. Replaces placeholders (`{{key}}`).
7. For `output-contract.mdc`: loads build system integration from fragment files and generates file header section from project name + author bindings.
8. Writes to canonical path (`aias-config/rules/`, flat).

**Multi-workspace behavior:** When multiple workspace IDs are discovered, rules are generated sequentially but written to the same flat files (`base.mdc`, `output-contract.mdc`). Only the last workspace (alphabetically sorted) is preserved (last-wins). A warning is emitted when this occurs. For most setups a single workspace is expected.

### Shortcut generation (with `--shortcuts`)

1. Collects mode globs from all processed profiles.
2. For each supported tool, generates shortcut files referencing canonical sources:
   - **Cursor**: `.mdc` with frontmatter → path reference (rules, modes, commands, skills)
   - **Claude Code**: `.md` with optional `paths:` frontmatter → path reference (rules, modes, skills)
   - **Windsurf**: plain `.md` → path reference (always-apply rules only)
   - **GitHub Copilot**: aggregated `copilot-instructions.md`, `.instructions.md` with `applyTo:`, agents
   - **Codex**: `.md` → path reference (commands in `.codex/commands/`, skills in `.agents/skills/`)

Shortcut content is always a path reference to the canonical source — never duplicated content.

## Prerequisites

- **Python 3.10+** (stdlib only, no third-party dependencies). The CLI validates the version at startup and exits with a clear error if the requirement is not met.

## Run instructions

**Preferred:** Use the `aias` CLI wrapper (see `docs/CLI.md`):

```bash
# Canonical + tool shortcuts
python3 aias/.canonical/generation/aias_cli.py generate --shortcuts

# Canonical only
python3 aias/.canonical/generation/aias_cli.py generate
```

**Direct invocation** (equivalent, for scripting or CI):

```bash
# Meta-workspace (canonical, no shortcuts)
python3 aias/.canonical/generation/generate_modes_and_rules.py

# Adopter project (canonical + tool shortcuts)
python3 aias/.canonical/generation/generate_modes_and_rules.py --shortcuts
```

**Important:** Do NOT use `--shortcuts` in the meta-workspace. It would overwrite manually maintained rules in `.cursor/rules/`.

## Idempotency check

Run generation twice and diff all outputs:

```bash
BACKUP="/tmp/rho-aias-idempotency"
rm -rf "$BACKUP" && mkdir -p "$BACKUP"
for f in aias-config/modes/*.mdc aias-config/rules/*.mdc; do
  [ -f "$f" ] || continue
  mkdir -p "$BACKUP/$(dirname "$f")"
  cp "$f" "$BACKUP/$f"
done
python3 aias/.canonical/generation/generate_modes_and_rules.py
for f in $(find "$BACKUP" -name "*.mdc"); do
  rel="${f#$BACKUP/}"
  diff -q "$f" "$rel" || echo "DIFF: $rel"
done
rm -rf "$BACKUP"
```

If no "DIFF:" lines appear, generation is idempotent.

## Stack fragment

Build system integration content lives in an external fragment file because it can be very large (100+ lines for Xcode pbxproj procedures) and varies significantly per workspace.

| Aspect | Value |
|---|---|
| **Location** | `<repo_root>/stack-fragment.md` (one per repo, fixed name) |
| **Contract** | `aias/contracts/readme-output-contract.md` § Build System Integration Fragments (includes Fragment Structure Options) |

When onboarding a new repo:

1. Follow the Fragment Structure Options in `aias/contracts/readme-output-contract.md` to create `stack-fragment.md` at repo root
2. Fill applicable sections, delete the rest
3. Add `binding.rule.output_contract.<ws>.profile` and other output contract bindings to `stack-profile.md` at repo root
4. Run the generator — pre-flight G4 validates the fragment before generation

## Exceptions

| Workspace | Rule | Reason |
|---|---|---|
| `xctemplates-dev` | Both | Highly specialized template, significant structural deviation from canonical templates (no SECURITY/PERFORMANCE, custom DELIVERABLES). Documented as EX-001 in `validation/rule-validation-matrix.md`. |

## Validation checklist

### Modes
- [x] Generated files include `GENERATED — DO NOT EDIT`.
- [x] Frontmatter includes `description`, `alwaysApply`, `model`, `color`, `globs` (array YAML).
- [x] All 9 mode files exist in `aias-config/modes/`.
- [x] Product modes include `SCOPE`.
- [x] No generated mode includes `GENERATION NOTES`.

### Rules
- [x] All 5 standard workspaces generate `base.mdc` and `output-contract.mdc`.
- [x] `aias-config/rules/` contains flat `base.mdc` and `output-contract.mdc` (no subdirectories).
- [x] Generated rules match pre-existing files (verified via backup-diff test).
- [x] Binding value unescaping handles `\n` → newline and `` \` `` → `` ` ``.
- [x] Conditional sections produce no spurious blank lines.
- [x] Idempotency: second generation run produces zero diffs.
- [x] `xctemplates-dev` rules are untouched by the generator.

### Shortcuts (with `--shortcuts`)
- [x] Cursor: rules, modes, commands, skills shortcuts generated.
- [x] Claude Code: rules, modes, skills shortcuts generated (with `paths:` for modes).
- [x] Windsurf: always-apply rules only (no modes).
- [x] GitHub Copilot: aggregated rules, modes with `applyTo:`, agents for commands.
- [x] Codex: commands, skills shortcuts generated.
- [x] No enriched text shortcut exceeds 500 bytes; aggregated files do not exceed 1500 bytes (symlinks are exempt).
- [x] Gemini: no shortcuts (context only via `GEMINI.md`).
