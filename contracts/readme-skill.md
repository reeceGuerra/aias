# Skill Contract — Cursor Configuration System (v1.1)

This document defines the **canonical contract** for skills used in this rho-aias development architecture.

It exists to:
- Establish what a skill is (and what it is not)
- Ensure separation of concerns between skills, modes, and commands
- Provide a single, stable reference for skill structure and quality
- Prevent knowledge duplication and scope creep across artifacts

This document is written **for maintainers** of the Cursor configuration system.

It is **not** a skill.
It is **not** executed by Cursor directly.
It is the reference against which skills are designed, reviewed, and corrected.

---

## What is a Skill?

A **skill** is a reusable unit of **operational knowledge** that teaches the agent how to interact with a specific external resource, service, or tool. Skills are consumed by modes and commands when context requires them.

### Characteristics

- **Operational** — Defines *how to operate* with a resource (API calls, parameter extraction, sequencing, error handling)
- **Reusable** — Any mode or command can consume it; not tied to a single workflow
- **Transversal** — Platform-agnostic by nature; not iOS-specific or Android-specific
- **Single-domain** — One skill = one external resource or service (e.g., Atlassian, Figma, GitHub)
- **Discoverable** — The agent finds and applies it based on the `description` in the frontmatter when context matches

### What a Skill is NOT

A skill is **not** a mode, a command, a base rule, or an agent definition.

| Artifact | Defines | Example |
|----------|---------|---------|
| **Mode** | How to think; role, principles, mental model for a task type | @planning: "think as a senior tech lead" |
| **Command** | How to execute; template, procedure, output format | /blueprint: "collect and structure planning data into artifacts" |
| **Skill** | How to operate with an external resource or service | atlassian-mcp: "this is how you read a Jira ticket via MCP" |
| **Base rule** | Always-on behavior; language, constraints, conventions | base.mdc: "respond in Spanish, code in English" |
| **Agent (AGENTS.md)** | Project context; structure, technologies, conventions | "This is an iOS app using MVVM + Clean Architecture" |

**Key distinction:** A mode decides *when* to use a resource (e.g., "if the user provides a Jira URL, enrich with ticket data"). A skill provides the *how* (e.g., "call `getAccessibleAtlassianResources` first to get `cloudId`, then `getJiraIssue`"). The skill never decides workflow; the mode or command that consumes it does.

---

## Philosophy

Skills in this system are:
- **Focused on a single domain** — one external service or resource per skill
- **Read-only by default** — write operations only when the user explicitly requests them
- **Fail-safe** — if the service does not respond or is not configured, abort and inform the user; never invent data or continue with degraded flow
- **Concise** — only include knowledge the agent does not already have; the agent is smart, the skill adds domain-specific operational details
- **Stateless** — a skill does not maintain state between invocations; it provides instructions for the current operation

Skills **do not**:
- Define when to use themselves (that is the mode's or command's decision)
- Include mode logic (role, principles, mental models)
- Include command logic (templates, output formats, procedures)
- Contain project-specific context (that belongs in AGENTS.md)
- Contain base behavior (that belongs in base.mdc)

---

## Separation of Concerns

### What belongs in a Skill

✅ **Operational knowledge for a specific resource:**
- How to authenticate or obtain required identifiers (e.g., `cloudId` for Atlassian)
- How to extract parameters from user input (e.g., `fileKey` and `nodeId` from a Figma URL)
- Call sequences and dependencies between API calls
- Required and optional parameters for each operation
- Error handling: what to do when the service fails or is unavailable
- Read vs write boundaries and safety rules

### What does NOT belong in a Skill

❌ **Do not include:**
- When to use this skill in a workflow (belongs in the consuming mode)
- Role or mental model ("think as a…") (belongs in a mode)
- Output templates or formatting (belongs in a command)
- Project-specific details (belongs in AGENTS.md)
- Generic constraints (belongs in base.mdc)
- Multiple unrelated services in a single skill

---

## Skill Categories

All skills belong to **exactly one** category.

### MCP Skills

Skills that teach the agent how to interact with a Model Context Protocol server.

Characteristics:
- Map to a specific MCP server (e.g., Atlassian, Figma, GitHub)
- Document the tool call sequence, required parameters, and error handling
- Enforce read-only by default; write only on explicit user request
- Include abort-on-failure behavior
- For tracker-sync capabilities, declare and validate provider status mapping source

Examples:
- `atlassian-mcp` — Read Jira issues, Confluence pages
- `figma-mcp` — Read design context, screenshots
- `github-mcp` — Read PRs, create PRs

### Tool Skills (future)

Skills that teach the agent how to use a specific CLI tool, script, or local utility.

Characteristics:
- Map to a specific tool or script
- Document invocation, parameters, expected output
- May include validation or error handling steps

Examples (hypothetical):
- `xcodebuild-skill` — How to build and test with xcodebuild
- `gradle-skill` — How to build and test with Gradle

---

## Canonical Skill Definition Structure

All skills **must follow this structure**.

### 1. Directory and File Layout

```
skill-name/
├── SKILL.md              # Required — main instructions
├── reference.md          # Optional — detailed API/parameter reference
└── examples.md           # Optional — usage examples
```

### 2. Storage Location

| Type | Path | Scope |
|------|------|-------|
| Personal | `~/.cursor/skills/skill-name/` | Available across all projects for this user |
| Project | `.cursor/skills/skill-name/` | Shared with anyone using the repository |
| Framework | `aias/.skills/skill-name/` | Core skills shipped with the framework (read-only) |
| Project | `aias-config/skills/skill-name/` | Custom skills created per-project via `aias new --skill` |

**Note:** Never create skills in `~/.cursor/skills-cursor/`. That directory is reserved for Cursor's internal built-in skills.

### 3. Frontmatter (Required)

```yaml
---
name: skill-name
description: Brief description of what this skill does and when the agent should use it. Include trigger terms.
---
```

**Required fields:**

| Field | Rules | Purpose |
|-------|-------|---------|
| `name` | Max 64 chars, lowercase letters/numbers/hyphens only | Unique identifier |
| `description` | Max 1024 chars, non-empty, third person, includes WHAT and WHEN | Agent uses this to decide when to apply the skill |

**Description rules:**
- Write in **third person** (the description is injected into the system prompt)
- Be **specific** and include trigger terms (e.g., "Jira ticket", "Figma URL", "pull request")
- Include both **WHAT** (capabilities) and **WHEN** (trigger scenarios)

### 4. Content Sections (Required Order)

#### PURPOSE (Required)

One or two sentences: what this skill enables and what resource it operates on.

---

#### OPERATIONS (Required)

List the operations the skill supports. For each operation:

- **Operation name** (e.g., "Read Jira issue", "Create pull request")
- **When to use** — brief trigger condition
- **Prerequisites** — what must be obtained first (e.g., `cloudId`)
- **Call sequence** — step-by-step: which tool/API to call, with which parameters, in which order
- **Parameter extraction** — how to get required parameters from user input (URLs, keys, etc.)
- **Output** — what the call returns and how the consuming mode/command should use it

---

#### SAFETY RULES (Required)

- **Read/write boundary:** What is read-only by default; what requires explicit user request to write
- **Abort on failure:** What to do when the service does not respond or is not configured (must include: abort, do not invent data, inform the user)
- **Data integrity:** Do not fabricate, infer, or assume data that the service did not return
- **Tracker mapping integrity (when capability = `tracker-sync`):** Require a valid `status_mapping_source` with canonical trigger keys in `slash + kebab-case`; if missing/invalid/unresolvable, abort dependent tracker operation and inform the user

---

#### REFERENCE (Optional)

If the skill needs detailed parameter documentation beyond what fits in OPERATIONS, put it in a separate `reference.md` file and link to it:

```markdown
For complete parameter details, see [reference.md](reference.md).
```

Keep references **one level deep** (SKILL.md → reference.md, not deeper).

---

## Design Principles

### Single Responsibility
- One skill = one external resource or service
- Do not combine Atlassian + GitHub in one skill
- If a service has clearly distinct sub-domains (e.g., Jira vs Confluence), they may share a skill if they share the same MCP server and authentication flow; otherwise, split

### Conciseness
- Target: **SKILL.md under 500 lines** (excluding frontmatter)
- Only include knowledge the agent does not already have
- The agent knows how to make API calls; the skill tells it *which* calls, *in what order*, *with what parameters*
- Use progressive disclosure: essential info in SKILL.md, detailed reference in separate files

### Read-Only by Default
- Every operation must state whether it is read or write
- Write operations must require **explicit user instruction** (e.g., "publish to Jira", "create the PR")
- If the user does not ask for a write operation, the skill must not perform one

### Abort on Failure
- If the MCP/service does not respond, is not configured, or returns an error: **abort the operation that depends on this skill**
- Do **not** continue with invented data or degraded flow
- Inform the user explicitly: "Could not connect to [service]. Aborting. Please check that the MCP is configured and available."
- This rule applies to every operation in every skill

### Stability
- Skills should change only when the underlying service API or MCP changes
- Operational details (call sequences, parameters) belong here; workflow decisions (when to call) belong in modes
- A stable skill reduces maintenance across all modes and commands that consume it

### Service-Skill Immutability Policy
- MCP service skills are provider-specific by design (e.g., `atlassian-mcp`, `figma-mcp`, `github-mcp`) and must not be refactored into provider-agnostic workflow abstractions.
- Service-skill changes are allowed only when at least one of these triggers is true:
  - The provider API/MCP contract changed and the skill needs refresh.
  - A validated bug exists in call sequencing, parameters, or safety handling.
  - A security/compliance change requires behavior updates.
- Service-skill changes are not allowed for:
  - "generalizing" provider-specific expertise into cross-provider behavior
  - moving workflow logic from commands/modes into skills
  - stylistic rewrites without operational justification
- Generic non-provider skills (e.g., `technical-writing`, `incremental-decomposition`) are exempt from this immutability rule and can evolve through normal contract updates.

---

## Quality Criteria

A good skill is:

### 1. **Focused**
- Addresses **one** external resource or service
- Does not mix domains
- Clear, single purpose

### 2. **Discoverable**
- Description is specific and includes trigger terms
- The agent can determine from the description whether this skill is relevant to the current context
- Name is descriptive and unambiguous (e.g., `atlassian-mcp`, not `jira-helper`)

### 3. **Correct**
- Call sequences match the actual MCP/API behavior
- Parameters are accurate and complete
- Prerequisites are documented (e.g., "obtain `cloudId` before calling `getJiraIssue`")

### 4. **Safe**
- Read-only by default; write only on explicit user request
- Abort on failure; never invent data
- Data integrity rules are explicit

### 5. **Concise**
- Under 500 lines
- No redundant explanations
- Progressive disclosure for detailed reference

### 6. **Composable**
- Any mode or command can consume it without conflict
- Does not assume which mode or command is calling it
- Does not include workflow logic

### 7. **Maintainable**
- Well-organized sections
- Clear section headers
- Easy to update when the underlying service changes

---

## Common Anti-Patterns

### Mixing Domains
```markdown
# Bad: two services in one skill
PURPOSE
Read Jira issues and fetch Figma designs.
```
**Problem:** Two unrelated services with different authentication and parameters. Split into two skills.

### Including Mode Logic
```markdown
# Bad: skill decides workflow
OPERATIONS
If the user is in @planning mode, read the Jira ticket to enrich the DoR.
```
**Problem:** The skill should not know about modes. It provides "how to read a Jira ticket"; the mode decides "when to read it".

### Including Command Logic
```markdown
# Bad: skill defines output format
OPERATIONS
Format the Jira ticket data as a markdown table with columns: Key, Summary, Status.
```
**Problem:** Output formatting belongs in the command. The skill returns raw data; the command structures it.

### Inventing Data on Failure
```markdown
# Bad: fallback with invented data
If the MCP does not respond, use the ticket key as the title and assume status is "Open".
```
**Problem:** Violates abort-on-failure and data integrity. Must abort and inform the user.

### Too Verbose
```markdown
# Bad: explaining what an API is
An API (Application Programming Interface) is a way for software to communicate...
```
**Problem:** The agent already knows this. Only include operational specifics.

---

## Choosing the Right Artifact

| Question | Answer → Artifact |
|----------|-------------------|
| "How should I think about this task?" | → **Mode** |
| "How do I format or structure this output?" | → **Command** |
| "How do I interact with this external service?" | → **Skill** |
| "What is always true in every interaction?" | → **Base rule** |
| "What is this project and how is it structured?" | → **AGENTS.md** |

If a piece of knowledge fits in more than one category, it probably needs to be split. Do not put mode logic in a skill or skill logic in a mode.

---

## Versioning

Skills should be versioned when:
- The underlying MCP or API changes (new parameters, deprecated operations, changed sequences)
- Operations are added or removed
- Safety rules change

**Versioning approach:**
- Update the `description` field to include version if needed
- Document changes in commit messages
- Consider backward compatibility for modes and commands that consume the skill

---

## Testing a Skill

After creating or updating a skill, verify:

1. **Discovery:** Does the agent find and apply this skill when the context matches (e.g., user provides a Jira URL)?
2. **Correctness:** Do the call sequences and parameters match the actual MCP/API behavior?
3. **Safety:** Does the skill abort on failure? Does it refuse to write without explicit user request?
4. **Composability:** Can multiple modes consume this skill without conflict?
5. **Conciseness:** Is the SKILL.md under 500 lines? Is there redundant content?
6. **Separation:** Does the skill avoid mode logic, command logic, and project context?

---

## Summary

A good skill:
- Provides **operational knowledge** for **one** external resource or service
- Is **transversal** (platform-agnostic) and **reusable** across modes and commands
- Is **read-only by default**; writes only on explicit user request
- **Aborts on failure**; never invents data
- Is **concise, focused, and composable**
- **Excludes** mode logic, command logic, base behavior, and project context

When in doubt, ask: "Does this teach the agent how to operate with a specific external resource?" If yes, it belongs in a skill. If it teaches "how to think", it belongs in a mode. If it teaches "how to format output", it belongs in a command.

---

## v5 Conventions

### System Skill Type

The `rho-aias` skill is a **system skill** — it is referenced by every mode and every artifact-producing or artifact-consuming command. Unlike MCP skills (which interact with external APIs) or tool skills (which provide domain knowledge), a system skill defines the **shared protocol** that all other artifacts follow.

System skills are characterized by:
- **Universal reference** — every mode and command references them
- **Protocol definition** — they define sequencing, state management, and coordination rules
- **Cross-cutting concerns** — they handle artifact lifecycle, sync tracking, and status management

The `rho-aias` skill is the canonical example of this type.

---

**Related contracts:**
- `readme-commands.md` — Contract for command definitions
- `readme-mode-rule.md` — Contract for mode rule definitions
- `readme-base-rule.md` — Contract for `base.mdc` files (always active)
- `readme-project-context.md` — Contract for `RHOAIAS.md` (project context)
- `readme-artifact.md` — Contract for task artifacts
- `readme-tracker-status-mapping.md` — Contract for provider tracker-state mappings

---

This document is the **source of truth** for skill structure and content.
