# Stack Profile Contract — Cursor Configuration System (v1.2)

This document defines the **canonical contract** for platform stack profiles used by the Phase 2 platform abstraction flow.

It exists to:
- Standardize how platform capabilities are declared
- Enable deterministic mode generation from canonical templates
- Prevent technology hardcoding in canonical mode templates
- Keep profile evolution explicit and backward-compatible

This document is written **for maintainers** of the Cursor configuration system.

---

## What is a Stack Profile?

A **stack profile** is a platform-scoped configuration artifact that declares technology and capability variables consumed by canonical mode templates.

### Characteristics

- **Platform-scoped** — One profile per platform (e.g., iOS, Android)
- **Human-editable** — Markdown, readable without generators
- **Template-consumable** — Keys are designed for deterministic substitution/conditional rendering
- **Extensible** — Supports future platforms (Web/Backend) without changing generator logic
- **Traceable** — Declares where each key is consumed or reserved

### What a Stack Profile is NOT

A stack profile is **not** a mode, a command, a skill, or a task artifact.

| Artifact | Defines |
|---|---|
| **Mode** | Behavior and thinking model for a task type |
| **Command** | Execution procedure and output structure |
| **Skill** | How to operate with tools/services |
| **Stack profile** | Platform variables/capabilities for generation |

---

## File Location and Naming

- `<repo_root>/stack-profile.md` — one file per repo, at the repository root (fixed name, analogous to `Podfile` or `Package.swift`)

Build system integration content is provided by `<repo_root>/stack-fragment.md` (see `readme-output-contract.md` § Build System Integration Fragments).

---

## Mandatory Structure

All stack profiles **must** include the following sections in this order:

1. `Schema`
2. `Metadata`
3. `Core stack`
4. `Architecture`
5. `Tooling`
6. `Testing`
7. `Design system`
8. `MCP capabilities`
9. `Globs`
10. `Generation bindings`
11. `Reserved keys`

---

## Minimum Variable Coverage

Each profile must define, at minimum:

- **Language** (name + version)
- **UI framework**
- **Build tool**
- **Dependency injection model**
- **Async/concurrency model**
- **Networking stack**
- **Testing stack** (unit + UI)
- **Design system/token policy**
- **MCP capability declarations**
- **Relevant globs for generated modes**
- **Generation routing** (stack identity + output directory + tasks directory)
- **Mode frontmatter bindings** (`description`, `model`, `color`, `globs`) for all 7 modes

---

## Generation Bindings Contract

`Generation bindings` is mandatory and must use one binding per line with this format:

- ``- `binding.<key>`: `<value>` ``

Required binding groups:

1. **Routing**
   - `binding.generation.stack_id`
   - `binding.generation.mode_output_dir` — must be `aias-config/modes` (canonical-only generation target)
   - `binding.generation.tools` — comma-separated list of target tools for shortcut generation. Valid values: `cursor`, `claude`, `windsurf`, `copilot`, `codex`. Only tools listed here will have shortcuts generated.
   - `binding.generation.tasks_dir` — base directory for task artifact directories (`<tasks_dir>/<TASK_ID>/`). Must be an absolute path or `~/`-prefixed. Default: `~/.cursor/plans/`.
   - `binding.generation.canonical_mode_output_dir` — canonical flat output for modes (e.g., `aias-config/modes`)
   - `binding.generation.canonical_rule_output_dir` — canonical flat output for rules (e.g., `aias-config/rules`)
2. **Shared template keys** (minimum)
   - `binding.platform_role_label`
   - `binding.language`
   - `binding.ui.framework`
   - `binding.build.tool`
   - `binding.architecture.pattern`
   - `binding.architecture.business_logic_location`
   - `binding.architecture.async_model`
   - `binding.architecture.di_policy`
   - `binding.networking.stack`
   - `binding.design_system.system`
   - `binding.testing.unit`
   - `binding.testing.ui`
   - `binding.platform_environment_label`
   - `binding.integration.dependency_graph`
3. **Capability flags** (booleans as `true|false`)
   - Minimum required keys:
     - `binding.capabilities.design_system_mapping_section`
     - `binding.capabilities.xcode_mcp`
     - `binding.capabilities.preview_required`
     - `binding.capabilities.platform_logging_hint`
     - `binding.capabilities.github_mcp`
     - `binding.capabilities.generated_code_dependency`
4. **Per-mode frontmatter**
   - `binding.mode.<mode>.description`
   - `binding.mode.<mode>.model`
   - `binding.mode.<mode>.color`
   - `binding.mode.<mode>.globs`
   - where `<mode>` is one of: `planning`, `dev`, `qa`, `debug`, `review`, `product`, `integration`

`binding.mode.<mode>.globs` format rule:

- Input in stack profile: comma-separated list (CSV) for readability.
- Output in generated `.mdc`: must be normalized as YAML array under `globs:`.
- Contractual output target:
  - `globs:`
  - `  - "*.pattern1"`
  - `  - "*.pattern2"`

`binding.mode.<mode>.globs` content rule:

- Globs MUST use **file-type patterns** (e.g., `*.swift`, `*.plan.md`, `*.kt`), NOT repository-specific paths (e.g., `my-repo/**/*.swift`).
- Repository directory names, project names, or workspace-specific prefixes MUST NOT appear in glob patterns. Globs are consumed by the generated mode frontmatter and must remain portable across any repository that uses the same stack.
- Acceptable: `*.swift`, `**/*.swift`, `*.plan.md`, `*.xml`, `*.kt`
- Not acceptable: `my-app/**/*.swift`, `src/main/java/**/*.kt`, `ProjectName.xcodeproj/**`

`binding.generation.tools` content rule:

- Value MUST be a comma-separated list of tool identifiers.
- Valid identifiers: `cursor`, `claude`, `windsurf`, `copilot`, `codex`.
- At least one tool MUST be specified.
- The generator only produces shortcuts for the listed tools. G6 post-flight validation is scoped to listed tools only.
- Override: the generator accepts `--tools <csv>` as a CLI flag to temporarily override the binding without modifying the profile.

`binding.generation.tasks_dir` content rule:

- Value MUST be an absolute path or start with `~/` (tilde-prefixed). Relative paths are not allowed.
- Default value: `~/.cursor/plans/` (backward compatible with Cursor).
- This is the base directory where task artifact directories are stored. Each task creates a subdirectory: `<tasks_dir>/<TASK_ID>/`.
- The generator validates presence of this binding in G1 (profile discovery). Missing = blocking error.
- At runtime, the rho-aias skill resolves this binding to locate and write task artifacts (see `aias/.skills/rho-aias/reference.md` § Tasks Base Directory).

Binding keys are the source of truth for generation. Hardcoding these values in the generator is not contract-compliant.

---

## Rule Bindings

Stack profiles must declare bindings for workspace rule generation (`base.mdc` and `output-contract.mdc`). These bindings complement the existing mode generation bindings.

### Base Rule Bindings (`binding.rule.base.*`)

| Key | Required | Description |
|---|---|---|
| `binding.rule.base.description` | Yes | Frontmatter `description` for the workspace's `base.mdc` |
| `binding.rule.base.role_specialty` | Yes | ROLE section content (expertise, focus, thinking style) |
| `binding.rule.base.engineering_domain_principle` | Yes | Domain-specific engineering principle for ENGINEERING PRINCIPLES section |
| `binding.rule.base.security_line` | Yes | Security focus text for SECURITY section |
| `binding.rule.base.performance_line` | Yes | Performance focus text for PERFORMANCE section |
| `binding.rule.base.assumptions_domain` | Yes | Domain-specific triggers for clarifying questions in ASSUMPTIONS section |
| `binding.rule.base.limitations_truthfulness_line` | Yes | Truthfulness constraint for LIMITATIONS section |
| `binding.rule.base.platform_limitations` | Yes | Toolchain-specific limitations text (e.g., "Swift Macros, SwiftSyntax" or "experimental APIs, KSP edge cases") |
| `binding.rule.base.styleguide_paths` | Yes | STYLE section content with project-specific styleguide references |
| `binding.rule.base.domain_constraints_section` | No | Full domain-specific constraints section (header + content), e.g., DESIGN SYSTEM CONSTRAINTS, NETWORKING CONSTRAINTS, MACRO CONSTRAINTS |

### Output Contract Bindings (`binding.rule.output_contract.*`)

| Key | Required | Description |
|---|---|---|
| `binding.rule.output_contract.profile` | Yes | Canonical output contract profile ID (`ios-app`, `ios-spm-package`, `ios-spm-package-with-demo`, `ios-xcode-template`, `android-app`) |
| `binding.rule.output_contract.environment` | Yes | ENVIRONMENT section content (IDE, versions, targets) |
| `binding.rule.output_contract.documentation_tool` | Yes | Documentation convention (e.g., "Xcode Quick Help docstrings" or "KDoc for public APIs") |
| `binding.rule.output_contract.linter` | Yes | Linter/formatter/comment convention (e.g., "No inline comments. Use MARK sections" or "Avoid inline comments. Prefer self-explanatory names") |
| `binding.rule.output_contract.testing` | Yes | Testing conventions specific to the workspace |
| `binding.rule.output_contract.file_header_project_name` | No | Project name for Swift file header (iOS only; absent when platform has no file header convention) |
| `binding.rule.output_contract.file_header_author` | No | Author line for Swift file header (iOS only) |
| `binding.rule.output_contract.deliverables_extra` | No | Additional deliverable item (e.g., macro impact analysis) |
| `binding.rule.output_contract.documentation_extra` | No | Additional documentation rule beyond the base convention |
| `binding.rule.output_contract.domain_considerations` | No | Domain-specific output considerations section (header + content) |

**Build system integration** is resolved via the **fragment file** at `<repo_root>/stack-fragment.md`, not via an inline binding. See `aias/contracts/readme-output-contract.md` § Build System Integration Fragments.

### Per-Workspace Rule Bindings

When a platform has multiple focused workspaces (e.g., iOS has 5), each workspace requires its own set of rule bindings. Use this naming convention:

```
binding.rule.base.<workspace_id>.<key>
binding.rule.output_contract.<workspace_id>.<key>
```

Where `<workspace_id>` matches the focused workspace directory name (e.g., `mobilemax-dev`, `rdsui-dev`).

### Shared Bindings

When bindings are identical across all workspaces in a platform, declare them once with a shared prefix (e.g., `ios_shared`) and the generator resolves with fallback: workspace-specific → shared → platform-level.

```
binding.rule.base.<shared_prefix>.<key>
binding.rule.output_contract.<shared_prefix>.<key>
```

The shared prefix is auto-detected by the generator from keys matching `rule.base.*_shared.*`.

---

## Consumption Rules

- Every declared key must be either:
  - **Consumed** by at least one canonical template section, or
  - Declared in `Reserved keys` with a clear future intent.
- Canonical templates must not hardcode platform technology outside profile-driven values or documented conditionals.
- Profile keys should be stable; when renamed, update templates and generation docs in the same change.
- Every required binding key must be present; missing required bindings are blocking.

---

## Change Discipline

When modifying a stack profile contract or profile schema:

- Record the design decision (what changed, why, expected impact)
- Keep changes scoped (avoid unrelated refactors)
- Validate generation idempotency after changes
- Do not close the phase with unresolved blocking feedback

---

## Quality Criteria

A valid stack profile is:

1. **Complete** — covers all variables needed by all 7 generated platform modes
2. **Deterministic** — keys are unambiguous for generator/template consumption
3. **Traceable** — key usage is documented (consumed vs reserved)
4. **Extensible** — supports adding platforms without generator redesign
5. **Stable** — minimizes churn in key names and schema
6. **Portable** — same contract supports future stacks by changing only profile bindings

---

## Validation Checklist

Before approving profile changes:

1. Required sections exist and are ordered
2. Minimum variable coverage is complete
3. Every key is consumed or reserved
4. No platform hardcoding leaked into canonical templates
5. Generated outputs remain contract-compliant and idempotent
6. `Generation bindings` covers routing + all 7 mode frontmatter bindings

---

## Phase 2 Implementation Checklist

Use this checklist to validate that platform abstraction was implemented correctly end-to-end (not only profile syntax):

- [ ] `stack-profile.md` exists at the repo root and complies with mandatory structure.
- [ ] `aias/.canonical/` contains exactly 7 templates (`planning`, `dev`, `qa`, `debug`, `review`, `product`, `integration`).
- [ ] Generator artifacts exist in `aias/.canonical/generation/` (`README.md` + generation mechanism).
- [ ] Generated outputs exist in canonical directories and include `GENERATED — DO NOT EDIT`.
- [ ] Generation is idempotent (second run produces no output diffs).
- [ ] Mode equivalence is guaranteed by design (canonical templates + stack profile capabilities).
- [ ] Transversal modes (`delivery`, `devops`) are out-of-scope for template-based generation (they are copied verbatim to `.modes/` and included in shortcut distribution). The `continuous-improvement` rule follows the same copy pattern but targets `.rules/`.
- [ ] No blocking feedback remains open in contracts, templates, or generation axes.

---

## Related Contracts

- `aias/contracts/readme-mode-rule.md`
- `aias/contracts/readme-base-rule.md`
- `aias/contracts/readme-output-contract.md`
- `aias/contracts/readme-commands.md`
- `aias/contracts/readme-artifact.md`

---

This document is the **source of truth** for stack profile structure and lifecycle.
