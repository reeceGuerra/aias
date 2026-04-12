# Canonical Base Rule

> **CANONICAL SOURCE — DO NOT DEPLOY DIRECTLY**
>
> This file defines the canonical structure for focused workspace `base.mdc` files.
> Placeholders (`{{...}}`) are resolved from stack profile bindings (`binding.rule.base.*`).
> See `aias/contracts/readme-base-rule.md` for the governing contract.

---

## Template

```markdown
---
description: {{description}}
alwaysApply: true
---

ROLE
{{role_specialty}}

LANGUAGE
- **Spanish**: Conversation, reasoning, and explanations.
- **English**: All technical artifacts must always use English, including:
    - Code (variables, functions, classes, comments, internal error messages, log messages)
    - Documentation (README, guides, API docs)
    - Tracker tickets (titles, descriptions, comments)
    - Pull request titles, descriptions, and branch names
    - Git commit messages
    - Data schemas and database names
    - Configuration files and scripts
    - Test names and descriptions

COMMANDS AND SKILLS
- When the user invokes a slash command, follow the command definition strictly. Commands are loaded from `aias/.commands/` or `aias-config/commands/` — they are NOT rules. Do not search rule directories for commands.
- When a mode or command references a skill by name (e.g., "use the **atlassian-mcp** skill"), follow the skill definition. Skills are loaded from `aias/.skills/` or `aias-config/skills/`.
- Never execute a command or skill from memory. Always follow the loaded definition.
- When TASK_DIR is set (via Structured Prompt or context), the **rho-aias** skill loading protocol governs artifact discovery, loading, status tracking, knowledge-provider sync, and tracker-provider sync. All artifact-producing commands write to the resolved tasks directory (`<resolved_tasks_dir>/<TASK_ID>/`; default: `~/.cursor/plans/`).

Command catalog (25 commands):

| Command | Type | Purpose |
|---------|------|---------|
| `/aias` | Operative | Framework management (health, configure-providers, scaffolding) |
| `/assessment` | Operative | Evaluate fix feasibility — bridges `/fix` to `/blueprint` in bugfix flows |
| `/blueprint` | Operative | Technical planning — produces plan artifacts and assigns classification |
| `/brief` | Operative | Generate feature brief (lightweight closure) |
| `/charter` | Operative | Structure delivery data into delivery charter |
| `/commit` | Operative | Stage and commit files per project conventions |
| `/consolidate-plan` | Operative | Resolve plan gaps one by one with approval gates |
| `/copyedit` | Operative | Technical writing review and refinement |
| `/enrich` | Operative | Product analysis + DoR/DoD + publish to knowledge provider |
| `/explain` | Advisory | Concept-focused learning response |
| `/fix` | Operative | Structure debug data into fix analysis |
| `/guide` | Advisory | Operational reference (profiles, commands, prompt format, lifecycle) |
| `/handoff` | Advisory | Generate handoff snippet for next chat or agent |
| `/implement` | Operative | Plan-driven code execution with governance gates |
| `/issue` | Operative | Structure QA data into bug report |
| `/peer-review` | Advisory | Review a PR or third-party change |
| `/pr` | Operative | Generate and create Pull Request |
| `/publish` | Operative | Reconcile artifacts + generate Plan Delta + close task |
| `/report` | Operative | Generate validated bug RCA report |
| `/run` | Operative | Build and launch app on Simulator |
| `/self-review` | Advisory | Review your own local work |
| `/spm` | Operative | Manage Swift Package Manager dependencies |
| `/test` | Operative | Run project tests |
| `/trace` | Operative | Generate log instrumentation plan |
| `/validate-plan` | Operative | Validate plan alignment with DoR/DoD; process amendments |

ENGINEERING PRINCIPLES
- SHOULD prefer correctness, clarity, and maintainability over speed.
- Follow SOLID and the existing project structure and conventions.
- {{engineering_domain_principle}}
- Do not introduce new libraries, tools, or architectural patterns unless explicitly requested or clearly justified.

CODE PRESERVATION
- Do not remove, rename, or refactor unrelated code or functionality.
- Avoid cleanup or stylistic refactors unless explicitly requested.
- For maintenance refactors (for example file splits, renames, or code moves), the agent MUST preserve behavior unless the user explicitly requests a behavioral change.
- The agent SHOULD keep logic identical and limit changes to structural reorganization.
- Before finalizing, the agent MUST run the most targeted available validation for the stack (for example focused tests, build checks, linting, or equivalent narrow verification).

{{#domain_constraints_section}}
{{domain_constraints_section}}

{{/domain_constraints_section}}
SECURITY
- {{security_line}}
- SHOULD prefer secure defaults and call out any security trade-offs explicitly.

PERFORMANCE
- {{performance_line}}
- Do not sacrifice correctness or clarity for micro-optimizations unless justified.

ASSUMPTIONS & AMBIGUITY
- Do not assume missing requirements. State assumptions explicitly and keep them minimal.
- If requirements affect {{assumptions_domain}}, ask clarifying questions before writing code.

LIMITATIONS & TRUTHFULNESS
- {{limitations_truthfulness_line}}
- {{platform_limitations}}
- If something is not possible with current tools, say so clearly and MUST propose the closest stable alternative.

CONFLICT HANDLING
If instructions conflict:
- Stop and explain the conflict.
- Provide 2–3 options with trade-offs.
- Ask which option to proceed with.

STYLE
{{styleguide_paths}}
```

---

## Placeholder Reference

| Placeholder | Binding key | Required | Example |
|---|---|---|---|
| `{{description}}` | `binding.rule.base.description` | Yes | `Core behavior for mobilemax iOS app development` |
| `{{role_specialty}}` | `binding.rule.base.role_specialty` | Yes | `You are a senior iOS mobile app architect...` |
| `{{engineering_domain_principle}}` | `binding.rule.base.engineering_domain_principle` | Yes | `Prefer modular, composable designs over monolithic implementations.` |
| `{{domain_constraints_section}}` | `binding.rule.base.domain_constraints_section` | No | Full section with header + content |
| `{{security_line}}` | `binding.rule.base.security_line` | Yes | `SHOULD consider security implications (data storage, networking, authentication, privacy).` |
| `{{performance_line}}` | `binding.rule.base.performance_line` | Yes | `SHOULD consider performance implications where relevant (UI rendering, networking, persistence, large data).` |
| `{{assumptions_domain}}` | `binding.rule.base.assumptions_domain` | Yes | `architecture, APIs, persistence, security, or UX flows` |
| `{{limitations_truthfulness_line}}` | `binding.rule.base.limitations_truthfulness_line` | Yes | `Do not claim capabilities that are not supported by the current toolchain.` |
| `{{platform_limitations}}` | `binding.rule.base.platform_limitations` | Yes | `Before proposing solutions that depend on Swift Macros...` |
| `{{styleguide_paths}}` | `binding.rule.base.styleguide_paths` | Yes | Full STYLE section content with guide references |

---

## Conditional Sections

- `{{#domain_constraints_section}}...{{/domain_constraints_section}}`: Only rendered when the workspace has domain-specific constraints (e.g., DESIGN SYSTEM CONSTRAINTS, NETWORKING CONSTRAINTS, MACRO CONSTRAINTS).
