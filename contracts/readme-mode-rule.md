# Mode Rule Contract — Cursor Rules System (v1.0)

> **Keyword convention**: This contract uses RFC-2119 keywords (MUST, MUST NOT, SHOULD, MAY).
> See [readme-commands.md](readme-commands.md) § RFC-2119 Keyword Policy for definitions.

This document defines the **canonical contract** for mode rules (`.cursor/rules/*.mdc` files with `alwaysApply: false`) in the Cursor configuration system.

It exists to:
- Establish standards for mode rule structure and content
- Clarify the four types of rules in Cursor and when to use each
- Ensure consistency across all mode rules
- Provide clear guidance for creating and maintaining mode rules

This document is written **for maintainers** of the Cursor configuration system.

---

## What is a Mode Rule?

A **mode rule** is a Cursor rule file (`.mdc` format) that defines **task-specific behavior** for the AI assistant. Unlike base rules, mode rules are **not always active** — they are activated when needed.

### Characteristics

- **Task-specific** — Defines behavior for a specific type of work (planning, debugging, QA, etc.)
- **Activated on demand** — Not always active (typically `alwaysApply: false`)
- **Focused** — Addresses one specific workflow or task type
- **Composable** — Works alongside base rules (never alongside other mode rules in the same chat)
- **Behavior-focused** — Defines *how to think* and *what to do*, not output structure (that's handled by workspace `output-contract.mdc`)
- **One mode per chat** — Each chat session uses exactly one mode. Modes are never mixed in the same chat. Handoffs between modes happen across chats via artifact files

### Output Format Responsibility

**Important:** Output format and structure are defined by the workspace's `output-contract.mdc` file (always applied). Mode rules focus on **behavior and thinking**, not output formatting. Only define output format in a mode if it needs to specify raw data collection for commands (e.g., unstructured data that commands will later structure).

### Location

- **Canonical location:** `aias-config/modes/` — the generated source of truth
- **Tool-specific directories** (shortcuts only — see `readme-tool-adapter.md`):
  - Repository-level: `.cursor/rules/<mode-name>.mdc` in the repository root
  - Workspace-level: `.cursor/rules/<mode-name>.mdc` in the workspace directory

---

### Design Principles

Mode rules SHOULD follow these design principles:

**Brevedad (Brevity)**
- Target length: **30–80 lines** (excluding frontmatter)
- Every line MUST add value
- Remove redundant or obvious statements
- If a mode exceeds 80 lines, SHOULD split it or move detailed procedures to commands

**Conceptual Focus**
- Focus on **"what to think"** and **principles**, not detailed steps
- Define the mental model and approach for the task
- Avoid step-by-step procedures (those belong in commands)
- Emphasize decision-making criteria and principles

**Stability**
- Avoid details that change frequently (tool versions, specific APIs, implementation details)
- Focus on principles that remain constant over time
- Leave procedural details, templates, and specific workflows to commands
- Mode rules SHOULD change rarely; commands can evolve more frequently

**Separation of Concerns**
- **Modes:** Define *how to think* and *what principles to apply*
- **Commands:** Define *how to execute* with templates, procedures, and detailed steps

---

## Modes vs Commands: Separation of Concerns

Understanding when to use a mode rule vs a command is critical for maintaining a clean, stable configuration system.

### Mode Rules Define

✅ **What to think about:**
- Mental models and approaches
- Decision-making principles
- Quality criteria and standards
- What questions to ask
- What to consider or avoid

✅ **Conceptual guidance:**
- "Focus on edge cases"
- "Consider security implications"
- "Validate assumptions explicitly"

### Commands Define

✅ **How to execute:**
- Step-by-step procedures
- Templates and formats
- Specific workflows
- Output structures
- Data transformations

✅ **Procedural details:**
- "Generate a plan with these 7 sections"
- "Format the output as Markdown with this structure"
- "Execute this script with these parameters"

### Example: Planning Workflow

**Mode (`planning.mdc`):**
- "Think about requirements, risks, and edge cases"
- "Consider technical and functional aspects"
- "Question assumptions explicitly"

**Command (`/enrich`):**
- "Analyze task completeness, generate artifacts, optionally post enrichment brief (`--brief`)"
- "Use the output contract template"
- "Structure the output as JSON for processing"

This separation ensures modes remain **stable** (principles don't change) while commands can **evolve** (templates and procedures can improve).

---

## Rule Types in Cursor

Cursor supports three types of rules for mode rules (all use `alwaysApply: false`):

### 1. Apply Intelligently (`alwaysApply: false` + descriptive `description`)

**Description:** When Agent decides it's relevant based on description.

**Use when:**
- The rule SHOULD activate automatically when the context matches
- The description clearly indicates when the rule is relevant
- You want Cursor to intelligently apply the rule based on conversation context

**Example:**
```yaml
---
description: Swift concurrency patterns and async/await best practices
alwaysApply: false
---
```

**How it works:** Cursor analyzes the conversation and applies the rule when the description matches the current context.

---

### 2. Apply to Specific Files (`alwaysApply: false` + `globs`)

**Description:** When file matches a specified pattern.

**Use when:**
- The rule SHOULD only apply when working with specific file types or paths
- You want file-type-specific behavior (e.g., different rules for `.swift` vs `.md` files)

**Example:**
```yaml
---
description: Swift file formatting and style rules
alwaysApply: false
globs: ["**/*.swift"]
---
```

**How it works:** Cursor applies the rule only when files matching the glob patterns are in context.

---

### 3. Apply Manually (`alwaysApply: false` + no `globs` + clear mode name)

**Description:** When @-mentioned in chat (e.g., `@planning`, `@qa`, `@debug`).

**Use when:**
- Creating mode rules that users explicitly activate
- Defining workflows that SHOULD be invoked intentionally
- Most common type for mode rules

**Example:**
```yaml
---
description: Planning mode: derive DoR, produce an actionable plan, and define a DoD ready for QA (no code)
alwaysApply: false
---
```

**How it works:** User activates with `@planning`, `@qa`, `@debug`, etc. The filename (without `.mdc`) becomes the activation keyword.

---

## Contract Structure for Mode Rules

All mode rules **MUST follow this structure and order**.

### 1. Frontmatter (Required)

```yaml
---
description: <clear description of when and why this mode applies>
alwaysApply: false
---
```

**Required fields:**
- `description`: Clear description that helps Cursor understand when to apply (for intelligent application) or helps users understand the mode's purpose
- `alwaysApply: false`: MUST be explicitly set to `false` for mode rules

**Optional fields:**
- `globs`: Array of file patterns where this rule applies (for file-specific rules)

**Naming convention:**
- Filename becomes the activation keyword (e.g., `planning.mdc` → `@planning`)
- Use lowercase, kebab-case for multi-word modes (e.g., `code-review.mdc` → `@code-review`)

---

### 2. Content Sections (Required Order)

#### MODE ROLE or ROLE (Required)

Define the AI's role when this mode is active.

**MUST include:**
- Primary role for this specific mode
- Key focus areas or expertise for this task type
- What perspective the AI SHOULD take

**Example:**
```
PLANNING ROLE
Act as a senior iOS technical lead. Your job is to turn vague or incomplete requests into a clear plan that can be implemented, validated, and delivered to QA with confidence.
```

---

#### SCOPE (Required)

Define what this mode does and does not do.

**MUST include:**
- What the mode is responsible for
- Explicit "do not" statements for out-of-scope behavior
- Boundaries and limitations

**Example:**
```
SCOPE
- Planning only: do not write implementation code or full file contents.
- Do not assume missing requirements silently.
- If requirements are vague, drive alignment by proposing structure, options, and asking targeted questions.
```

---

#### WORKFLOW or PROCESS (Optional but Recommended)

Define the step-by-step process for this mode.

**Structure:**
- Numbered or ordered list of steps
- Clear sequence of actions
- Decision points or branching logic if needed

**When to include:**
- When the mode has a specific workflow (e.g., planning, debugging)
- When there are clear sequential steps
- When the process is non-obvious

**When to omit:**
- Simple, single-purpose modes
- When the workflow is obvious from the role and scope

---

#### OUTPUT FORMAT (Optional)

**Note:** Output format is typically defined by the workspace's `output-contract.mdc` file (always applied). Only include this section if the mode requires a specific output format that differs from or supplements the workspace contract.

**When to include:**
- The mode needs a unique output structure not covered by the workspace contract
- The mode generates structured data that will be consumed by commands (e.g., raw data for `/enrich`, `/report`, `/pr`)

**When to omit:**
- The workspace's `output-contract.mdc` already defines the output format (most common case)
- The mode focuses on behavior/thinking rather than output structure
- The mode produces unstructured or conversational output

**Example (only if needed):**
```
OUTPUT FORMAT
- Provide raw, unstructured information
- Focus on data collection, not formatting
- Commands will structure this data later
```

---

#### Additional Sections (Context-Dependent)

Add sections as needed for your specific mode:

- **INPUTS TO REQUEST** — What information the mode needs
- **FIRST PRINCIPLES** — Core principles for this mode
- **QUALITY BAR** — Standards for output quality
- **CHANGE DISCIPLINE** — Rules about what the mode should/shouldn't change
- **CONSTRAINTS** — Mode-specific constraints
- **EXAMPLES** — Usage examples or output examples
- **OUTPUT** — Only if the mode needs to specify raw data format for commands (not structure)

**Note:** File output contracts belong in the workspace's `output-contract.mdc`, not in mode rules.

---

## Content Guidelines

### What to Include

✅ **Do include:**
- Clear role definition for this specific mode
- Explicit scope boundaries (what it does and doesn't do)
- **Principles and mental models** (how to think about the task)
- **Decision-making criteria** (what to consider)
- Workflow or process steps (if applicable, but keep them high-level)
- Mode-specific constraints or principles
- Output format (only if it differs from workspace `output-contract.mdc`)

### What to Exclude

❌ **Do not include:**
- Base behavior (belongs in `base.mdc`)
- Project context (belongs in `AGENTS.md` / `RHOAIAS.md`)
- **Detailed procedures or step-by-step workflows** (belongs in commands)
- **Templates or specific output formats** (belongs in commands)
- **Tool-specific details or versions** (belongs in commands or documentation)
- Command-specific behavior (belongs in command definitions)
- Generic constraints that apply to all modes (belongs in `base.mdc`)

---

## Quality Criteria

A good mode rule is:

### 1. **Focused**
- Addresses **one specific task type** or workflow
- Does not try to cover multiple unrelated tasks
- Clear, single purpose

### 2. **Activation-Clear**
- Users understand when to use it
- Description clearly indicates purpose
- Activation method is obvious (`@mode-name`)

### 3. **Deterministic**
- Clear, unambiguous instructions
- Explicit "do" and "do not" statements
- Predictable behavior and approach

### 4. **Composable (across chats, not within)**
- Works well with base rules in the same chat
- Does not conflict with other mode rules
- Handoffs between modes happen across chats — one mode produces an artifact, another consumes it in a different chat
- **Never combine multiple modes in a single chat session**

### 5. **Complete**
- Defines role and scope clearly
- Includes necessary workflow steps (if applicable)
- Covers edge cases relevant to the mode

### 6. **Maintainable**
- Well-organized sections
- Clear section headers (UPPERCASE)
- Easy to update without breaking behavior

### 7. **Stable**
- Avoids details that change frequently (tool versions, API specifics, implementation details)
- Focuses on principles and mental models that remain constant
- Changes rarely; when it does change, it's because the fundamental approach changed
- Leaves procedural details, templates, and specific workflows to commands

**Why stability matters:**
- Mode rules define "how to think" — thinking principles don't change often
- Commands define "how to execute" — execution details can evolve
- Stable modes reduce maintenance burden and configuration drift

---

## Formatting Standards

### Section Headers
- Use **UPPERCASE** for major sections
- Use `---` separator between major sections
- Keep headers concise (1–3 words when possible)

### Content Style
- Use bullet points for lists
- Use numbered lists for ordered steps
- Use **bold** for emphasis on key terms
- Use code backticks for technical terms, file names, or commands

### Structure
- One concept per section
- Sections flow logically (role → scope → workflow → additional sections)
- No nested sections more than 2 levels deep

---

## Examples

### Example 1: Planning Mode (Apply Manually)

```markdown
---
description: Planning mode: derive DoR, produce an actionable plan, and define a DoD ready for QA (no code)
alwaysApply: false
---

PLANNING ROLE
Act as a senior iOS technical lead. Your job is to turn vague or incomplete requests into a clear plan that can be implemented, validated, and delivered to QA with confidence.

SCOPE
- Planning only: do not write implementation code or full file contents.
- Do not assume missing requirements silently.
- If requirements are vague, drive alignment by proposing structure, options, and asking targeted questions.

WORKFLOW
1) Establish a minimal but sufficient Definition of Ready (DoR).
2) Derive the technical and functional plan from that DoR.
3) Explicitly define the Definition of Done (DoD) that determines when the work is ready for QA.

OUTPUT
- Provide raw, unstructured information about the plan
- Focus on collecting all relevant data points
- Commands (e.g., `/enrich`) will structure this information later
```

### Example 2: File-Specific Rule (Apply to Specific Files)

```markdown
---
description: Swift test file patterns and best practices
alwaysApply: false
globs: ["**/*Tests.swift", "**/*Test.swift"]
---

ROLE
You are a senior iOS testing specialist focused on writing clear, maintainable, and effective tests.

SCOPE
- Test files only: apply these patterns when working with test files.
- Focus on test clarity, coverage, and maintainability.

TESTING PRINCIPLES
- Use Swift Testing framework.
- One test per behavior or scenario.
- Clear test names that describe what is being tested.
```

---

## Common Anti-Patterns

### ❌ Too Generic
```markdown
ROLE
You are a helpful assistant.
```
**Problem:** No specific role or focus for the mode.

### ❌ Too Broad
```markdown
ROLE
You are a senior iOS developer who can plan, code, debug, review, and test.
```
**Problem:** Tries to cover too many tasks. SHOULD be split into multiple focused modes.

### ❌ Missing Scope
```markdown
ROLE
You are a debugger.
```
**Problem:** No clear boundaries on what the mode does and doesn't do.

### ❌ Defining Output Format When Workspace Already Does
```markdown
OUTPUT FORMAT
1) Problem statement
2) Solution
```
**Problem:** The workspace's `output-contract.mdc` already defines output format. Modes SHOULD focus on behavior, not structure.

### ❌ Base Rule Content
```markdown
LANGUAGE
- Conversation: Spanish
- Code: English
```
**Problem:** Belongs in `base.mdc`, not in a mode rule.

---

## Choosing the Right Rule Type

**Note:** Mode rules always use `alwaysApply: false`. For `alwaysApply: true` rules, see `readme-base-rule.md`.

### Use Apply Intelligently (`alwaysApply: false` + descriptive `description`)
- Rules that SHOULD activate automatically when context matches
- Domain-specific knowledge that's relevant in certain conversations
- Best practices that apply situationally

### Use Apply to Specific Files (`alwaysApply: false` + `globs`)
- File-type-specific rules (e.g., `.swift`, `.md`, `.json`)
- Language-specific formatting or conventions
- File-type-specific best practices

### Use Apply Manually (`alwaysApply: false` + no `globs`)
- **Most common for mode rules**
- Workflow-specific modes (`@planning`, `@qa`, `@debug`, `@review`)
- Task-specific behaviors that users explicitly invoke
- Modes that define complete workflows

---

## Versioning

Mode rules SHOULD be versioned when:
- Behavioral changes are made
- Workflow steps change significantly
- Scope or role definition changes
- Output format changes (only if the mode defines its own output format)

**Versioning approach:**
- Update the `description` field to include version if needed
- Document changes in commit messages
- SHOULD consider backward compatibility

---

## Testing a Mode Rule

After creating or updating a mode rule, verify:

1. **Clarity:** Can a user understand when and how to use this mode?
2. **Completeness:** Does it cover all necessary aspects of the mode?
3. **Focus:** Does it address one specific task type?
4. **Composability:** Does it work with existing base rules and other modes?
5. **Determinism:** Are all instructions clear and unambiguous?
6. **Activation:** Is it clear how to activate the mode (`@mode-name`)?

---

## Summary

A good mode rule:
- Defines **task-specific behavior** for a specific workflow
- Is **not always active** (`alwaysApply: false`)
- Is **focused, deterministic, and composable**
- Has a **clear activation method** (typically `@mode-name`)
- **Excludes** base behavior, project context, or command-specific content

When in doubt, ask: "Does this apply to **one specific type of task or workflow**?" If yes, it belongs in a mode rule. If it applies to all interactions, it belongs in `base.mdc`.

---

## v5 Conventions

### Mandatory `rho-aias` Skill Reference

All modes that interact with task artifacts MUST include an ARTIFACT LOADING section that references the **rho-aias** skill loading protocol (Phases 0–3). This section specifies which artifacts the mode requires and which are optional.

### `globs` Frontmatter Convention

Modes SHOULD declare relevant file globs in the `globs` frontmatter field. This enables Cursor to suggest the mode when the user opens matching files. Globs SHOULD include both artifact suffixes (e.g., `*.plan.md`, `*.issue.md`) and technology file extensions (e.g., `*.swift`, `*.kt`).

### Workflow Profile Awareness

Modes that load artifacts SHOULD be aware of the current workflow profile (`feature`, `bugfix`, `refactor`, `enrichment`) to set appropriate expectations about which artifacts exist.

---

**Related contracts:**
- `readme-base-rule.md` — Contract for `base.mdc` files (always active)
- `readme-project-context.md` — Contract for `RHOAIAS.md` (project context)
- `readme-artifact.md` — Contract for task artifacts

---

This document is the **source of truth** for mode rule structure and content.
