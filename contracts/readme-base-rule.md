# Base Rule Contract — Cursor Rules System (v1.0)

> **Keyword convention**: This contract uses RFC-2119 keywords (MUST, MUST NOT, SHOULD, MAY).
> See [readme-commands.md](readme-commands.md) § RFC-2119 Keyword Policy for definitions.

This document defines the **canonical contract** for base rules (`.cursor/rules/base.mdc`) in the Cursor configuration system.

It exists to:
- Establish standards for base rule structure and content
- Ensure consistency across all base rules
- Provide clear guidance for creating and maintaining base rules
- Prevent rule drift and ambiguity

This document is written **for maintainers** of the Cursor configuration system.

---

## What is a Base Rule?

A **base rule** is a Cursor rule file (`.mdc` format) with `alwaysApply: true` that defines the **foundational behavior** of the AI assistant for a specific context (repository or workspace).

### Characteristics

- **Always active** — Applied to every interaction when the context is open
- **Context-specific** — Defines behavior for a particular repository or workspace
- **Foundational** — Establishes the base role, constraints, and principles
- **Composable** — Works alongside mode-specific rules (`@planning`, `@qa`, etc.)

### Location

- **Canonical location:** `aias-config/rules/base.mdc` — the generated source of truth
- **Tool-specific locations** (shortcuts only — see `readme-tool-adapter.md`):
  - Cursor: `.cursor/rules/base.mdc`
  - Claude Code: `.claude/rules/base.md`
  - Windsurf: `.windsurf/rules/base.md`
  - GitHub Copilot: referenced in `.github/copilot-instructions.md`

---

## Rule Types in Cursor

Cursor supports four types of rules based on when and how they are applied. Base rules use the first type:

### Always Apply (`alwaysApply: true`) — Used by Base Rules

**Description:** Apply to every chat session.

**Use when:**
- Defining foundational behavior that SHOULD always be active
- Setting base constraints, language preferences, or core principles
- Creating base rules (this contract)

**Example:**
```yaml
---
description: Core behavior for this iOS project
alwaysApply: true
---
```

**Note:** Base rules **MUST** use `alwaysApply: true`. Mode rules use `alwaysApply: false` (see `readme-mode-rule.md` for mode rule types).

---

## Contract Structure

All base rules **MUST follow this structure and order**.

### 1. Frontmatter (Required)

```yaml
---
description: <brief description of the rule's purpose>
alwaysApply: true
---
```

**Required fields:**
- `description`: One-line description of what this rule defines
- `alwaysApply: true`: MUST be explicitly set to `true`

**Optional fields:**
- `globs`: Array of file patterns where this rule applies (rarely used for base rules)

---

### 2. Content Sections (Required Order)

#### ROLE or MODEL ROLE (Required)

Define the AI's role and expertise.

**MUST include:**
- Primary role (e.g., "senior iOS architect", "Cursor System Architect")
- Key areas of expertise
- Thinking style or approach

**Example:**
```
ROLE
You are a senior iOS mobile app architect and technical lead. You prioritize production-grade engineering, maintainability, and correctness.
```

---

#### MAIN OBJECTIVES (Optional but Recommended)

List the primary objectives or capabilities the AI MUST have.

**Structure:**
- Numbered list of main objectives
- Each objective can have sub-bullets for clarity

**When to include:**
- When the role has multiple distinct responsibilities
- When you need to explicitly enumerate capabilities
- For complex or specialized contexts

**When to omit:**
- Simple, single-purpose roles
- When objectives are obvious from ROLE section

---

#### CONSTRAINTS (Required, but can be distributed)

Define what the AI **MUST NOT** do or **MUST** consider.

**Options:**
1. **Explicit CONSTRAINTS section** — All constraints in one place
2. **Distributed constraints** — Constraints in relevant sections (ASSUMPTIONS & AMBIGUITY, LIMITATIONS & TRUTHFULNESS, CODE PRESERVATION, etc.)

**MUST include (somewhere in the rule):**
- Technical limitations or boundaries
- Behavioral restrictions
- Explicit "do not" statements

**When to use explicit section:**
- Simple rules with few constraints
- When constraints don't fit naturally in other sections

**When to distribute:**
- Complex rules with many constraint categories
- When constraints are better organized by topic (security, performance, code preservation, etc.)

**Example (Explicit):**
```
CONSTRAINTS

- Be technically accurate at all times.
- Do not claim capabilities that are not supported by the current toolchain.
- Do not assume missing requirements. State assumptions explicitly.
```

**Example (Distributed):**
```
ASSUMPTIONS & AMBIGUITY
- Do not assume missing requirements. State assumptions explicitly.

LIMITATIONS & TRUTHFULNESS
- Do not claim capabilities that are not supported by the current toolchain.

CODE PRESERVATION
- Do not remove, rename, or refactor unrelated code or functionality.
```

---

#### COMMANDS AND SKILLS (Recommended)

Instructs the agent on how to work with the agentic architecture's commands and skills.

**MUST include:**
- That slash commands (`/X`) are loaded from `aias/.commands/` (framework) or `aias-config/commands/` (project) and MUST be followed strictly
- That commands are NOT rules — the agent MUST NOT search rule directories for commands
- That skills referenced by modes/commands are loaded from `aias/.skills/` (framework) or `aias-config/skills/` (project)
- That the agent MUST NOT execute a command or skill from memory

**Example:**
```
COMMANDS AND SKILLS
- When the user invokes a slash command (e.g., `/commit`, `/brief`, `/pr`), follow the command definition strictly. Commands are loaded from `aias/.commands/` or `aias-config/commands/` — they are NOT rules. Do not search rule directories for commands.
- When a mode or command references a skill by name (e.g., "use the **atlassian-mcp** skill"), follow the skill definition. Skills are loaded from `aias/.skills/` or `aias-config/skills/`.
- Never execute a command or skill from memory. Always follow the loaded definition.
```

**When to include:**
- Always, for any workspace that uses the agentic architecture (commands, modes, skills)

**When to omit:**
- Workspaces that do not use the agentic architecture

---

#### Additional Sections (Context-Dependent)

Add sections as needed for your specific context:

- **LANGUAGE** — Language preferences for conversation vs code
- **ENGINEERING PRINCIPLES** — Core engineering values
- **CODE PRESERVATION** — Rules about refactoring and code changes
- **SECURITY** — Security considerations
- **PERFORMANCE** — Performance guidelines
- **ASSUMPTIONS & AMBIGUITY** — How to handle unclear requirements
- **LIMITATIONS & TRUTHFULNESS** — Honesty about capabilities
- **CONFLICT HANDLING** — What to do when instructions conflict
- **STYLE** — Code style and conventions
- **INPUTS YOU MAY RECEIVE** — What inputs are expected
- **QUALITY CRITERIA** — Definition of done
- **OUTPUT FORMAT** — Formatting expectations
- **FAILURE MODES TO AVOID** — Common mistakes to prevent
- **OPERATING PRINCIPLE** — Core philosophy

---

## Content Guidelines

### What to Include

✅ **Do include:**
- Role definition and expertise
- Core constraints and boundaries
- Language preferences (if non-English)
- Engineering principles specific to the context
- Behavioral rules that apply to all interactions
- Explicit "do not" statements for common mistakes

### What to Exclude

❌ **Do not include:**
- Project context or purpose (belongs in `RHOAIAS.md` — see `readme-project-context.md` contract)
- Mode-specific behavior (belongs in mode rules like `planning.mdc`, `qa.mdc`)
- Command-specific behavior (belongs in command definitions)
- Task-specific instructions (belongs in the user's prompt)
- Examples or tutorials (belongs in documentation)
- Detailed technical specifications (belongs in project docs)
- Workflow steps (belongs in workflow documentation)

---

## Quality Criteria

A good base rule is:

### 1. **Focused**
- Defines behavior for **one context** (one repo or one workspace)
- Does not try to cover multiple unrelated contexts
- Clear scope boundaries

### 2. **Concise**
- Typically 30–150 lines (excluding frontmatter)
- No redundant statements
- Every section adds value

### 3. **Deterministic**
- Clear, unambiguous statements
- No vague or subjective language
- Explicit "do" and "do not" statements

### 4. **Composable**
- Works well with mode-specific rules
- Does not conflict with other rules
- Can be overridden by more specific rules when needed

### 5. **Maintainable**
- Well-organized sections
- Clear section headers (UPPERCASE)
- Easy to update without breaking behavior

### 6. **Context-Appropriate**
- Reflects the actual needs of the context
- Not overly generic or overly specific
- Balances detail with readability

---

## Formatting Standards

### Section Headers
- Use **UPPERCASE** for major sections
- Use `---` separator between major sections
- Keep headers concise (1–3 words when possible)

### Content Style
- Use bullet points for lists
- Use numbered lists for ordered items
- Use **bold** for emphasis on key terms
- Use code backticks for technical terms, file names, or commands

### Structure
- One concept per section
- Sections flow logically (context → role → constraints → specifics)
- No nested sections more than 2 levels deep

---

## Examples

### Example 1: Repository Base Rule (iOS Project)

```markdown
---
description: Core behavior for this iOS project (Spanish chat, rigorous engineering)
alwaysApply: true
---

ROLE
You are a senior iOS mobile app architect and technical lead. You prioritize production-grade engineering, maintainability, and correctness.

LANGUAGE
- Conversation and explanations: Spanish.
- Code, identifiers, filenames, docstrings, and commit messages: English.

COMMANDS AND SKILLS
- When the user invokes a slash command (e.g., `/commit`, `/brief`, `/pr`), follow the command definition strictly. Commands are loaded from `aias/.commands/` or `aias-config/commands/` — they are NOT rules. Do not search rule directories for commands.
- When a mode or command references a skill by name (e.g., "use the **atlassian-mcp** skill"), follow the skill definition. Skills are loaded from `aias/.skills/` or `aias-config/skills/`.
- Never execute a command or skill from memory. Always follow the loaded definition.

ENGINEERING PRINCIPLES
- Prefer correctness, clarity, and maintainability over speed.
- Follow SOLID and the existing project structure and conventions.
- Prefer modular, composable designs over monolithic implementations.

CONSTRAINTS
- Do not remove, rename, or refactor unrelated code or functionality.
- Do not assume missing requirements. State assumptions explicitly.
- Do not claim capabilities that are not supported by the current toolchain.
```

### Example 2: Workspace Base Rule (Configuration System)

```markdown
---
description: Cursor System Architect role and behavior for configuration workspace
alwaysApply: true
---

MODEL ROLE

You are an **Expert in**:
- Cursor command design and contract definition
- Cursor rules architecture and best practices
- Contract-driven development for AI systems

You think like a **senior systems architect + AI configuration specialist**, not a marketer.

CONSTRAINTS

- Be technically accurate at all times.
- Always reference and comply with existing contracts.
- Do not create artifacts that violate established contracts.
- Do not modify contracts without explicit user approval.
```

**Note:** Project context for this workspace would be defined in `RHOAIAS.md` (see `readme-project-context.md` contract).

---

## Common Anti-Patterns

### ❌ Too Generic
```markdown
ROLE
You are a helpful assistant.
```
**Problem:** No specific context or expertise.

### ❌ Too Specific
```markdown
ROLE
You are a senior iOS developer working on the login screen of the mobilemax app, specifically the authentication flow that uses OAuth2 with the backend API endpoint /api/v1/auth/login.
```
**Problem:** Too narrow, belongs in a task-specific prompt.

### ❌ Mode-Specific Content
```markdown
PLANNING BEHAVIOR
When in planning mode, create a detailed plan with 5 sections...
```
**Problem:** Belongs in `planning.mdc`, not `base.mdc`.

### ❌ Command-Specific Content
```markdown
COMMIT MESSAGE FORMAT
When using /commit, format messages as...
```
**Problem:** Belongs in command definition, not base rule.

### ❌ Redundant Constraints
```markdown
CONSTRAINTS
- Be helpful.
- Be accurate.
- Be clear.
```
**Problem:** Too generic, adds no value.

---

## Versioning

Base rules SHOULD be versioned when:
- Behavioral changes are made
- New constraints are added that change AI behavior
- Role definition changes significantly

**Versioning approach:**
- Update the `description` field to include version if needed
- Document changes in commit messages
- Consider backward compatibility

---

## Testing a Base Rule

After creating or updating a base rule, verify:

1. **Clarity:** Can a new maintainer understand the rule's purpose?
2. **Completeness:** Does it cover all necessary base behavior?
3. **Conciseness:** Can any section be removed without losing value?
4. **Composability:** Does it work with existing mode rules?
5. **Determinism:** Are all statements clear and unambiguous?

---

## Summary

A good base rule:
- Defines **foundational behavior** for a specific context
- Is **always active** (`alwaysApply: true`)
- Is **focused, concise, and deterministic**
- **Complements** `AGENTS.md` (which provides project context) and mode-specific rules
- **Excludes** project context (belongs in `AGENTS.md`), task-specific, mode-specific, or command-specific content

When in doubt, ask: "Does this apply to **every** interaction in this context?" If yes, it belongs in the base rule. If no, it belongs elsewhere.

## Invariant vs Parametrizable Sections

Base rules contain both **invariant** sections (shared across all focused workspaces) and **parametrizable** sections (driven by the workspace's stack profile bindings).

### Invariant Sections

These sections MUST be present in every focused workspace `base.mdc` and share the same content:

| Section | Notes |
|---|---|
| LANGUAGE | Conversation vs code language rules. **MUST be category-driven** (see below). |
| COMMANDS AND SKILLS | Agentic architecture instructions. Identical across workspaces. |
| ENGINEERING PRINCIPLES (shared subset) | Core principles (correctness, SOLID, modularity, no unauthorized libs). |
| CODE PRESERVATION | Do not remove/rename/refactor unrelated code. |
| SECURITY | Security implications and secure defaults. |
| ASSUMPTIONS & AMBIGUITY | Explicit assumptions, clarifying questions. |
| CONFLICT HANDLING | Stop, explain, options with trade-offs. |

### Parametrizable Sections

These sections vary per workspace and are driven by stack profile bindings (`binding.rule.base.*`):

| Section | Binding source | Notes |
|---|---|---|
| ROLE | `binding.rule.base.role_specialty` | Workspace-specific role and expertise. |
| `description` (frontmatter) | `binding.rule.base.description` | One-line workspace-specific description. |
| ENGINEERING PRINCIPLES (extra) | `binding.rule.base.engineering_extra` | One additional principle per workspace (optional). |
| Domain-specific constraints | `binding.rule.base.domain_constraints_section` | e.g., DESIGN SYSTEM CONSTRAINTS, NETWORKING CONSTRAINTS, MACRO CONSTRAINTS. Optional; only when the workspace has domain-specific behavioral rules. |
| PERFORMANCE | `binding.rule.base.performance_focus` | Domain-specific focus areas (UI rendering vs networking vs generated code). |
| LIMITATIONS & TRUTHFULNESS | `binding.rule.base.platform_limitations` | Platform/toolchain-specific limitations (Swift Macros/Xcode vs Kotlin/AGP/Compose). |
| STYLE | `binding.rule.base.styleguide_paths` | Paths to project-specific style guides. |

---

## Category-Driven Language Mandate

The LANGUAGE section in every `base.mdc` **MUST use category-driven references** for external service providers. Hardcoding provider names (e.g., "Jira", "Confluence", "GitHub") in the LANGUAGE section violates the service abstraction established in Phase 3.

**Correct (category-driven):**
```
- Tracker tickets (titles, descriptions, comments)
- Pull request titles, descriptions, and branch names
```

**Incorrect (provider-hardcoded):**
```
- Jira tickets (titles, descriptions, comments)
```

This mandate applies to all sections of `base.mdc` that reference external service categories.

---

## Canonical Rule Profiles

Base rules for focused workspaces are generated from the canonical source (`aias/.canonical/base-rule.md`) using stack profile bindings (`binding.rule.base.*`). This ensures:

- Invariant sections remain consistent across workspaces
- Parametrizable sections are driven by explicit, traceable bindings
- Updates propagate deterministically: update template → regenerate workspace rules

See `readme-stack-profile.md` for the binding definitions and `readme-output-contract.md` for the complementary output contract.

---

## v5 Conventions

### COMMANDS AND SKILLS Section Updates

The COMMANDS AND SKILLS section in every `base.mdc` MUST include:
- Reference to the **rho-aias** skill for artifact management
- The TASK_DIR convention for task directory resolution
- The `/publish` command for task closure and resolved knowledge-provider archival

---

## v7 Conventions (Tool Portability)

### Canonical Location

The canonical location for generated base rules is `aias-config/rules/base.mdc`. Tool-specific directories (`.cursor/rules/`, `.claude/rules/`, `.windsurf/rules/`, `.github/`) contain **shortcut files** that reference the canonical source. See `readme-tool-adapter.md` for shortcut format per tool.

### Command and Skill Paths

The COMMANDS AND SKILLS section MUST reference `aias/.commands/` (framework) and `aias-config/commands/` (project) for commands, and `aias/.skills/` (framework) and `aias-config/skills/` (project) for skills. These are the canonical locations; tool-specific paths (e.g., `~/.cursor/commands/`) are resolved by each tool's shortcut layer.

---

**Related contracts:**
- `readme-project-context.md` — Contract for `RHOAIAS.md` (project context)
- `readme-tool-adapter.md` — Contract for shortcut files
- `readme-artifact.md` — Contract for task artifacts

---

This document is the **source of truth** for base rule structure and content.
