# Tool Adapter Contract — Rho AIAS Configuration System

This document defines the **canonical contract** for tool adapters (shortcut files) in the Rho AIAS configuration system.

It exists to:
- Define what a shortcut file is and how it works
- Establish format requirements per supported AI coding tool
- Ensure zero content duplication between canonical sources and tool-specific directories
- Provide clear guidance for generating and maintaining shortcuts

This document is written **for maintainers** of the Rho AIAS configuration system.

---

## What is a Shortcut File?

A **shortcut** is a tool-specific artifact that points to a canonical source in `aias/`. It enables each AI coding tool to discover and load Rho AIAS configuration through its native mechanisms — without duplicating any canonical content.

Shortcuts use one of two strategies:

| Strategy | Mechanism | LLM dependency | When used |
|---|---|---|---|
| **Symlink** | Filesystem symlink (`link → canonical`) | None — the filesystem resolves the reference | Tool reads the canonical format natively (Cursor `.mdc`, any tool for plain `.md`) |
| **Enriched text** | Text file with `[name] description` prefix + path instruction | Low — behavioral nudge increases compliance | Tool requires format transformation (Claude `paths:`, Windsurf plain, Copilot `applyTo:`) |

### Characteristics

- **Zero duplication** — Neither strategy copies canonical content into the shortcut
- **Tool-native format** — Each shortcut matches the format the target tool expects
- **Same name** — The shortcut file uses the same base name as the canonical source
- **Generated** — Shortcuts are produced by the generator (`generate_modes_and_rules.py`), not maintained manually
- **Disposable** — Deleting a shortcut directory removes tool support; the canonical source is unaffected
- **Symlinks use relative paths** — Computed via `os.path.relpath(target, link.parent)` for portability

### What a Shortcut is NOT

| Is | Is NOT |
|---|---|
| A symlink or enriched path reference | A copy of canonical content |
| Tool-specific format | Universal format |
| Generated artifact | Manually maintained file |
| Disposable | Source of truth |

---

## Canonical Source Locations

All canonical content lives exclusively in `aias/`:

| Artifact type | Canonical location |
|---|---|
| Rules (always-apply) | `aias/.rules/*.mdc` |
| Modes (conditional) | `aias/.modes/*.mdc` |
| Commands | `aias/.commands/*.md` |
| Skills | `aias/.skills/*/` |
| Context | `RHOAIAS.md` (project root) |

---

## Supported Tools and Shortcut Directories

### Cursor

| Artifact | Shortcut location | Strategy | Format |
|---|---|---|---|
| Rules | `.cursor/rules/<name>.mdc` | Symlink | Symlink → `aias/.rules/<name>.mdc` |
| Modes | `.cursor/rules/<name>.mdc` | Symlink | Symlink → `aias/.modes/<name>.mdc` (inherits `globs` for auto-activation) |
| Commands | `.cursor/commands/<name>.md` | Symlink | Symlink → `aias/.commands/<name>.md` |
| Skills | `.cursor/skills/<name>/SKILL.md` | Symlink | Symlink → `aias/.skills/<name>/SKILL.md` |
| Context | `AGENTS.md` | Symlink | Symlink → `RHOAIAS.md` |

### Claude Code

| Artifact | Shortcut location | Strategy | Format |
|---|---|---|---|
| Rules | `.claude/rules/<name>.md` | Enriched text | `[name] description` + path instruction |
| Modes | `.claude/rules/<name>.md` | Enriched text | Optional `paths:` frontmatter + `[name] description` + path instruction |
| Commands | Not supported | — | — |
| Skills | `.claude/skills/<name>/SKILL.md` | Symlink | Symlink → `aias/.skills/<name>/SKILL.md` |
| Context | `CLAUDE.md` | Symlink | Symlink → `RHOAIAS.md` |

### Windsurf

| Artifact | Shortcut location | Strategy | Format |
|---|---|---|---|
| Rules | `.windsurf/rules/<name>.md` | Enriched text | `[name] description` + path instruction, no frontmatter |
| Modes | Not supported | — | All rules are always-apply; no conditional activation |
| Commands | Not supported | — | — |
| Skills | Not supported | — | — |
| Context | `AGENTS.md` | Symlink | Symlink → `RHOAIAS.md` (shared with Cursor/Copilot) |

**Constraint:** 12,000 character limit per rule file in Windsurf.

### GitHub Copilot

| Artifact | Shortcut location | Strategy | Format |
|---|---|---|---|
| Rules | `.github/copilot-instructions.md` | Enriched text | Single file aggregating `[name] description` per rule |
| Modes | `.github/instructions/<name>.instructions.md` | Enriched text | Optional `applyTo:` frontmatter + `[name] description` + path instruction |
| Commands | `.github/agents/<name>.md` | Symlink | Symlink → `aias/.commands/<name>.md` |
| Skills | Not supported | — | — |
| Context | `AGENTS.md` | Symlink | Symlink → `RHOAIAS.md` (shared with Cursor/Windsurf) |

### Codex

| Artifact | Shortcut location | Strategy | Format |
|---|---|---|---|
| Rules | Not supported | — | `.codex/rules/` in Codex is for sandbox/permissions, not behavioral instructions |
| Modes | Not supported | — | — |
| Commands | `.codex/commands/<name>.md` | Symlink | Symlink → `aias/.commands/<name>.md` |
| Skills | `.agents/skills/<name>/SKILL.md` | Symlink | Symlink → `aias/.skills/<name>/SKILL.md` |
| Context | `codex.md` | Symlink | Symlink → `RHOAIAS.md` |

### Gemini

| Artifact | Shortcut location | Strategy | Format |
|---|---|---|---|
| Rules | Not supported | — | — |
| Modes | Not supported | — | — |
| Commands | Not supported | — | — |
| Skills | Not supported | — | — |
| Context | `GEMINI.md` | Symlink | Symlink → `RHOAIAS.md` |

---

## Shortcut Content Format

### Symlink Shortcuts

Symlink shortcuts are filesystem symlinks from the tool-specific path to the canonical source. The tool reads canonical content directly — no LLM interpretation required.

**Rules and Modes (Cursor):**

```
.cursor/rules/base.mdc → aias/.rules/base.mdc          (symlink)
.cursor/rules/planning.mdc → aias/.modes/planning.mdc   (symlink)
```

Note: Cursor mode symlinks inherit `globs` from the canonical `.mdc` file, enabling auto-activation by file pattern. This is a behavioral improvement over the previous text shortcut pattern which omitted `globs`.

**Commands (Cursor):**

```
.cursor/commands/implement.md → aias/.commands/implement.md   (symlink)
```

**Commands (GitHub Copilot — Agents):**

```
.github/agents/implement.md → aias/.commands/implement.md   (symlink)
```

**Commands and Skills (Codex):**

```
.codex/commands/implement.md → aias/.commands/implement.md      (symlink)
.agents/skills/rho-aias/SKILL.md → aias/.skills/rho-aias/SKILL.md   (symlink)
```

**Skills (Cursor and Claude Code):**

```
.cursor/skills/rho-aias/SKILL.md → aias/.skills/rho-aias/SKILL.md   (symlink)
.claude/skills/rho-aias/SKILL.md → aias/.skills/rho-aias/SKILL.md   (symlink)
```

### Enriched Text Shortcuts

Enriched text shortcuts are text files containing a `[name] description` behavioral nudge followed by a "Read and follow" instruction. Used where the tool requires format transformation incompatible with symlinks.

**Rules (Claude Code):**

```
[base] Core behavior for RDSUI design system development
Read and follow the canonical rule at: aias/.rules/base.mdc
```

**Modes (Claude Code) — with `paths:` frontmatter:**

```
---
paths:
  - "*.plan.md"
---
[planning] Planning mode: senior technical lead focused on turning vague requests into clear, actionable planning data
Read and follow the canonical mode at: aias/.modes/planning.mdc
```

**Rules (Windsurf):**

```
[base] Core behavior for RDSUI design system development
Read and follow the canonical rule at: aias/.rules/base.mdc
```

**Rules (GitHub Copilot) — aggregated:**

```
Read and follow these canonical rules:
- [base] Core behavior for RDSUI design system development — aias/.rules/base.mdc
- [output-contract] Output contract: complete file contents + reasoning — aias/.rules/output-contract.mdc
- [continuous-improvement] Continuous improvement — learn from user feedback — aias/.rules/continuous-improvement.mdc
```

**Modes (GitHub Copilot) — with `applyTo:` frontmatter:**

```
---
applyTo: "*.plan.md,*.product.md"
---
[planning] Planning mode: senior technical lead focused on turning vague requests into clear, actionable planning data
Read and follow the canonical mode at: aias/.modes/planning.mdc
```

### Context Symlinks

Context shortcuts are **symlinks** to `RHOAIAS.md` (generated by `aias_cli.py`, not the generator script), scoped by `binding.generation.tools`:

| Context file | Created when tools include |
|---|---|
| `AGENTS.md` | `cursor`, `windsurf`, or `copilot` |
| `CLAUDE.md` | `claude` |
| `codex.md` | `codex` |

Each tool reads `RHOAIAS.md` content directly via filesystem resolution — no LLM interpretation required. Tools that read `AGENTS.md` (Cursor, Windsurf, Copilot) share the same symlink.

---

## Naming Convention

- The shortcut file must have the **same base name** as the canonical source
- Extension matches the tool's expectation (`.mdc` for Cursor, `.md` for all others)
- For GitHub Copilot modes: `<name>.instructions.md` (tool requirement)
- For GitHub Copilot commands: `<name>.md` in `.github/agents/`

---

## Generation

Shortcuts are generated by `generate_modes_and_rules.py` as part of the standard generation pipeline. The generator:

1. Produces canonical files in `aias/.rules/` and `aias/.modes/`
2. Reads `binding.generation.tools` from `stack-profile.md` to determine target tools
3. Generates tool-specific shortcuts only for the listed tools
4. Treats `aias/.commands/*.md` canonically by directory discovery, so new commands such as `/handoff` flow into supported command shortcut targets without a hardcoded command registry
5. Validates shortcuts via post-flight gates G6–G7 (scoped to listed tools)

### Pre-flight Validation Gates

| Gate | Name | Validates |
|---|---|---|
| G5 | Output Directory | `aias/.rules/` and `aias/.modes/` exist or can be created |
| G6 | Shortcut Consistency | Every canonical file has corresponding shortcuts for supported tools. Symlinks are validated for existence AND target resolution (broken symlinks produce a specific error distinct from "missing"). |
| G7 | No Content Duplication | Symlinks are **exempt** (they point to full canonical content by design). Enriched text shortcuts must not exceed 500 bytes. Aggregated files (`copilot-instructions.md`) must not exceed 1500 bytes. |

---

## Maintenance

| Event | Action |
|---|---|
| Canonical content updated | Re-run generator; shortcuts auto-updated if format changes |
| New tool added | Extend generator's adapter table; re-run |
| Tool removed | Delete its shortcut directory |
| New rule/mode added | Re-run generator; new shortcuts created automatically |

---

## Quality Criteria

### Symlink shortcuts

1. Is a **relative symlink** (not absolute) pointing to the canonical source
2. Target **resolves to an existing file** (no broken symlinks)
3. Has the **same base name** as the canonical source
4. Is **generated** by the generator, not manually maintained
5. Is **idempotent** — re-running the generator produces an identical symlink

### Enriched text shortcuts

1. Starts with `[name] description` line (behavioral nudge extracted from canonical frontmatter)
2. Contains a "Read and follow the canonical ..." instruction as the action line
3. Uses the **correct format** for the target tool (including any required frontmatter)
4. Has the **same base name** as the canonical source
5. Does **not exceed** 500 bytes
6. Is **generated** by the generator, not manually maintained

---

## Fidelity Summary

| Tool | Rules | Modes | Commands | Skills | Context |
|---|---|---|---|---|---|
| Cursor | Full (symlink) | Full (symlink, globs inherited) | Full (symlink) | Full (symlink) | Full (symlink → RHOAIAS.md) |
| Claude Code | Full (enriched text) | Partial (enriched text, paths: scoping) | None | Full (symlink) | Full (symlink → RHOAIAS.md) |
| Windsurf | Partial (enriched text, always-apply only) | None | None | None | Full (symlink → RHOAIAS.md) |
| GitHub Copilot | Full (enriched text) | Partial (enriched text, applyTo: scoping) | Full (symlink) | None | Full (symlink → RHOAIAS.md) |
| Codex | None | None | Full (symlink) | Full (symlink) | Full (symlink → RHOAIAS.md) |
| Gemini | None | None | None | None | Full (symlink → RHOAIAS.md) |

---

## Related Contracts

- `readme-base-rule.md` — Contract for base rules (canonical content)
- `readme-mode-rule.md` — Contract for mode rules (canonical content)
- `readme-output-contract.md` — Contract for output contract rules (canonical content)
- `readme-project-context.md` — Contract for `RHOAIAS.md` (canonical context)
- `readme-stack-profile.md` — Contract for stack profiles (generation bindings)

---

This document is the **source of truth** for tool adapter (shortcut) structure and behavior.
