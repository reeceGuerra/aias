# Cursor Commands – System Contract (v6.0)

> **Keyword convention**: This contract defines and uses RFC-2119 keywords (MUST, MUST NOT, SHOULD, MAY). See section "RFC-2119 Keyword Policy" below for definitions.

This document defines the **canonical contract** for all Cursor commands used in this workspace system.

It exists to:
- Reduce ambiguity and drift between commands
- Provide a single, stable reference for command structure
- Improve consistency when Cursor loads commands partially or inconsistently

This document is written **for me** as the system author and maintainer.

It is **not** a command.
It is **not** executed by Cursor directly.
It is the reference against which commands are designed, reviewed, and corrected.

---

## Philosophy

Commands in this system are:
- Deterministic
- Procedural or formatting-oriented
- Designed to work reliably in a **two-message workflow**

Commands **do not**:
- Perform deep reasoning
- Infer missing intent
- Invent information
- Act autonomously without explicit input

When reasoning is required, it happens **before** the command, using a mode (`@planning`, `@qa`, etc.).

### Controlled Resolution Exception

The only allowed exception to "do not infer missing intent" is **controlled resolution** inside `/handoff`.

Controlled resolution is allowed only when all conditions hold:
- The user explicitly invoked `/handoff`
- The destination is resolved from explicit workflow evidence already available in chat or TASK_DIR
- Any inferred mode / command / next step is declared explicitly in the output
- The command preserves uncertainty instead of inventing continuity when evidence is insufficient

This exception does **not** authorize open-ended command autonomy. It exists only to format an operational handoff when the user explicitly asks for one.

---

## Command Categories

All commands belong to **exactly one** category.

### Advisory — Chat-Only Commands

Characteristics:
- Output is presented exclusively in the chat response
- No file writes
- No status mutation
- External system calls are allowed only in **read-only** mode
- External mutation remains forbidden (no tracker writes, no knowledge publishes, no VCS comments/approvals/merges)

Typical usage:
- User asks a question or requests information
- Command reads from skill files, chat context, TASK_DIR context, or read-only provider context and responds in chat

Examples:
- guide
- explain
- self-review
- peer-review
- handoff

---

### Operative — Procedural / Execution Commands

Characteristics:
- May write artifacts to TASK_DIR
- May update `status.md` (state mutation)
- May call external systems (tracker provider, knowledge provider, VCS provider)
- May execute shell commands (git, xcodebuild, etc.)
- Must be deterministic and sequential

Typical usage:
- Message 1: Resolve intent and inputs (optional but recommended)
- Message 2: Execute command

Examples:
- blueprint
- commit
- pr
- issue
- publish

---

## Modes vs Commands: Separation of Concerns

Understanding when to use a mode rule vs a command is critical for maintaining a clean, stable configuration system and enabling the **two-message workflow**.

### Commands Define

✅ **How to execute:**
- Step-by-step procedures and workflows
- Templates and output formats
- Specific data transformations
- Execution of external tools (Operative)
- Structured output generation (Advisory)

✅ **Procedural details:**
- "Generate a brief with these exact sections: Problem, Approach, Risks, DoD"
- "Format the output as rendered Markdown with this structure"
- "Execute this script with these parameters"
- "Stage files matching these patterns and commit with this message format"

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

### Two-Message Workflow

The separation enables a reliable **two-message workflow**:

**Message 1: Reasoning (Mode)**
- User activates a mode (e.g., `@planning`, `@qa`, `@debug`)
- Mode provides raw, unstructured information
- Mode focuses on principles and thinking, not structure

**Message 2: Execution (Command)**
- User invokes a command (e.g., `/brief`, `/report`, `/commit`)
- Command structures the raw data from Message 1
- Command applies templates, formats, and procedures

### Examples by Command Type

#### Advisory Commands (Chat-Only)

**Workflow:**
1. User asks about a workflow profile or framework concept
2. `/guide feature` → Reads from `rho-aias` skill and responds in chat with the profile steps

**Separation:**
- **Mode:** Provides reasoning stance and domain context
- **Command (`/guide`, `/explain`):** Reads reference material and presents information in chat — no files written, no state changed
- **Command (`/peer-review`):** Reads PR context through the configured VCS provider, then returns findings/snippets in chat — no files written, no remote mutation

#### Operative Commands (Procedural / Execution)

**Workflow:**
1. `@planning` → Provides raw planning data (requirements, risks, approach)
2. `/blueprint` → Writes plan artifacts to TASK_DIR, updates `status.md`, syncs through the resolved knowledge provider

**Separation:**
- **Mode (`planning.mdc`):** "Think about requirements, risks, and edge cases"
- **Command (`/blueprint`):** "Write `technical.plan.md`, `increments.plan.md`, etc. to TASK_DIR, update status, sync"

**Alternative Workflow (Operative with direct execution):**
1. Chat context → User provides explicit intent
2. `/commit` → Stages files, generates commit message, executes `git commit`, verifies tracker review state if PR is open

### Why This Separation Matters

**Stability:**
- Commands can evolve (templates, procedures, formats can improve)
- Modes remain stable (principles and thinking don't change often)

**Clarity:**
- Commands are deterministic and procedural
- Modes are conceptual and principle-based

**Reliability:**
- Two-message workflow reduces ambiguity
- Commands receive structured input from modes
- Each component has a single, clear responsibility

---

## Canonical Command Definition Template

All commands **must follow this structure and order**.
The sections below are mandatory.

Only the **Output Structure** section is expected to vary significantly between commands.

---

### 1. Identity

Describe **what this command is** and **what it is responsible for**.

This section **must include** a formal declaration of the command category.

**Required subfield:**
- `Command Type:` `Advisory` | `Operative`

Purpose:
- Anchor the ontological role of the command
- Prevent Cursor from inferring execution authority or scope
- Make allowed behavior explicit before any other rules apply

---

### 2. Invocation / Usage

Describe **how the command is invoked**, if applicable.

May include:
- Arguments
- Flags
- Modes
- Examples

Notes:
- Even if a command takes no arguments, this section must exist.
- This marks the command as **operational**, not conversational.

---

### 3. Inputs

Define **what information the command is allowed to use** and **where it may come from**.

Examples:
- Chat context
- Output from a previous `@planning` / `@qa` step
- Logs
- Diffs
- File contents explicitly provided

Rules:
- Inputs must be explicit
- No hidden assumptions
- This section is **critical** for the two-message workflow

---

### 4. Output Contract (Format)

Define the **output format rules**.

Decisions made here:
- Rendered Markdown vs Markdown in a code block
- Single block vs multiple blocks
- Whether text is allowed outside the block

Rules:
- This section must be **structurally identical** across all commands
- Only the values change, not the shape
- This is where consistency is enforced

---

### 5. Content Rules (Semantics)

Define **what the output may and may not contain**, independent of format.

Examples:
- Language requirements
- No invention of information
- What to do when information is missing
- Level of detail
- Explicit exclusions

Purpose:
- Prevent “filling in the blanks”
- Reduce hallucinations
- Enforce scope discipline

---

### 6. Output Structure (Template)

Define the **exact structure** of the output.

This includes:
- Section headers
- Order of sections
- Placeholders or comments

Notes:
- This is the **primary point of variation** between commands
- The structure should be complete and explicit
- No additional sections may be added by the model

---

### 7. Non-Goals / Forbidden Actions

Explicitly list actions the command **must not perform**.

Examples:
- Do not write code
- Do not modify files
- Do not suggest alternatives
- Do not write files or mutate external systems (for Advisory commands)

Purpose:
- Reduce overreach
- Prevent scope creep
- Make boundaries unambiguous

---

## Governance

This section defines the canonical governance framework for interactive gates across all commands and modes. It is the **single source of truth** for gate behavior, enforcement language, and contextual governance rules.

All gates in commands MUST comply with this section. Individual command definitions reference this section — they do not redefine governance rules.

---

### Gate Taxonomy

Five gate types. The first four use a **structured interactive mechanism**; Precondition is a hard STOP.

| Gate Type | Mechanism | Blocking | Use Case | Options Pattern |
|---|---|---|---|---|
| **Confirmation** | `AskQuestion` when available; otherwise `Text Gate Protocol` | Yes | Validate understanding or approve a write action | 2 options: affirmative action + adjustment |
| **Decision** | `AskQuestion` when available; otherwise `Text Gate Protocol` | Yes | Choose between mutually exclusive paths | 2–5 options describing distinct actions |
| **Feedback** | `AskQuestion` when available; otherwise `Text Gate Protocol` | Yes | Post-execution quality check | 3 options: continue / adjust / stop |
| **Approval** | `AskQuestion` when available; otherwise `Text Gate Protocol` | Yes | Authorize a high-impact or irreversible action | 2 options: approve / reject with reason |
| **Precondition** | Hard STOP (halt + report) | Yes | Missing required input or invalid state | No `AskQuestion` — halt execution and report |

**Binding rules:**
- Confirmation, Decision, Feedback, and Approval MUST use `AskQuestion` when the runtime exposes it.
- If the runtime does not expose `AskQuestion`, Confirmation, Decision, Feedback, and Approval MUST use the `Text Gate Protocol`.
- Precondition MUST NOT use `AskQuestion`. It halts and reports.
- No ad-hoc interactive mechanism is permitted outside these two channels.

---

### Runtime Compatibility for Gates

Rho AIAS supports two runtime-compatible channels for the same interactive gate model:

1. `AskQuestion` — canonical and preferred when available
2. `Text Gate Protocol` — mandatory compatibility path when `AskQuestion` is unavailable in the runtime

This does **not** create a new gate type. It preserves the same gate taxonomy, blocking semantics, option ids, and anti-bypass rules across runtimes.

The absence of `AskQuestion` in the runtime activates `Text Gate Protocol`. Commands MUST NOT invent their own fallback wording or degrade to informal free-form chat choices.

### Text Gate Protocol

When `AskQuestion` is unavailable, the runtime MUST project the same gate through chat text using this exact sequence:

1. Present the normal gate context output.
2. Present the gate prompt and the same option ids and labels that would have been used in `AskQuestion`.
3. Instruct the user to reply with exactly one option id unless the gate explicitly allows multiple selections.
4. Map the user's reply to the same action table defined under `On response`.

Rules:

- The gate remains blocking until a valid mapped response is received.
- If the user reply does not map cleanly to exactly one valid option (or the allowed multi-select set), the gate MUST re-fire.
- Commands MUST NOT continue execution while awaiting a valid textual gate response.

### Gate Invocation Protocol

Every gate in the system (except Precondition) follows this exact 3-step sequence. This is the **single source of truth** for gate behavior.

**Step 1 — Context**
Present a structured summary in chat text that gives the user enough information to make an informed decision. This is informational output only — not a gate.

The context MUST include:
- What was analyzed or produced
- What will happen next if the user approves
- Any assumptions, risks, or notable findings

**Step 2 — Gate**
Invoke the structured interactive mechanism with:
- A clear, specific prompt that restates the decision
- Descriptive, action-oriented options (see Option Design Principles)
- The appropriate `allow_multiple` setting for the gate type

Mechanism resolution:
- If `AskQuestion` is available in the runtime, MUST use `AskQuestion`.
- Otherwise, MUST use `Text Gate Protocol` with the same prompt, option ids, labels, and `allow_multiple` semantics.

The gate MUST block execution until the user responds.

**Step 3 — Action**
Execute the action corresponding to the user's selection:
- If the user selected the affirmative option → proceed
- If the user selected "adjust" or equivalent → apply corrections and return to Step 1
- If the user selected "stop" or "reject" → halt and report current state

#### Anti-Bypass Rules

These rules apply to **all gates in all commands**. They are defined here and referenced (never redefined) by individual gate definitions.

| Rule ID | Rule | Rationale |
|---|---|---|
| AB-01 | MUST NOT skip a gate without an explicit contract exemption (e.g., `--fast`) | Gates exist to protect decision points. |
| AB-02 | MUST NOT infer `--fast` from context, urgency, or task simplicity | `--fast` is an explicit user flag on `/blueprint` only. |
| AB-03 | MUST NOT batch multiple gates into a single structured interaction | Each gate represents a distinct decision point. |
| AB-04 | MUST NOT print unstructured gate options in chat text as a substitute for the canonical mechanism | Chat text is informational unless it follows the exact Text Gate Protocol. |
| AB-05 | MUST NOT self-answer a gate based on prior context or assumptions | Gates require explicit user input. |
| AB-06 | MUST NOT proceed past a gate while a gate response is pending | The gate is blocking. No execution until response. |
| AB-07 | MUST NOT convert a Precondition STOP into an `AskQuestion` gate | Preconditions are not negotiable. |

---

### Option Design Principles

1. **Descriptive labels.** Options MUST describe the action, not generic responses. Good: "Write artifacts to TASK_DIR and continue". Bad: "Yes".
2. **Contextual specificity.** Options MUST reference the concrete entities being acted upon. Good: "Create PR targeting `develop` branch". Bad: "Proceed".
3. **Action-oriented verbs.** Each option MUST start with a verb or verb phrase.
4. **Exhaustive coverage.** The option set MUST cover all valid responses. If the user might want to stop, include a stop option.
5. **No duplicative options.** Each option MUST represent a distinct action path.
6. **Prompt context.** The gate prompt MUST include a 1–2 line summary that frames the decision without requiring the user to re-read the full context output.

---

### Canonical Gate Section Pattern

Every gate defined in a command MUST use this template structure:

```markdown
### Gate: <Name>

**Type:** <Confirmation | Decision | Feedback | Approval>
**Fires:** <when this gate fires — condition or phase>
**Skippable:** <No | MUST ... UNLESS --fast>

**Context output:**
<Description of what information is presented before the gate>

**AskQuestion:**
- **Prompt:** "<specific prompt text>"
- **Options:**
  - `<option-id-1>`: "<Descriptive action label>"
  - `<option-id-2>`: "<Descriptive action label>"
  [- `<option-id-3>`: "<Descriptive action label>"]
- **allow_multiple:** <true | false>

**Runtime compatibility:**
- If `AskQuestion` is unavailable, use the Text Gate Protocol with the same prompt, option ids, labels, and `allow_multiple` semantics.

**On response:**
- `<option-id-1>` → <action>
- `<option-id-2>` → <action>
[- `<option-id-3>` → <action>]

**Anti-bypass:** Inherits Gate Invocation Protocol. No additional rules.
```

**Rules:**
- "Anti-bypass" MUST always reference the Gate Invocation Protocol. Individual gates MUST NOT define their own anti-bypass rules.
- "Skippable" MUST be `No` for all gates except `/blueprint` Comprehension and Checkpoint which use `MUST ... UNLESS --fast`.

---

### Enforcement Language

#### RFC-2119 Keyword Policy

| Keyword | Intended Force | Allowed Use Cases | Prohibited Misuse |
|---|---|---|---|
| **MUST** | Absolute requirement | Gates, `AskQuestion` invocation, preconditions, structural requirements | Preferences or recommendations |
| **MUST NOT** | Absolute prohibition | Anti-bypass rules, forbidden actions, security constraints | Soft discouragement |
| **MUST ... UNLESS** | Conditional requirement with explicit exception | Gates with named skip conditions (`--fast`) | Open-ended or implicit conditions |
| **SHOULD** | Strong recommendation, deviation requires justification | Best practices, architectural alignment, quality expectations | Mandatory behavior (use MUST) |
| **MAY** | Optional, at implementer's discretion | Permitted but not required behavior | Expected behavior (use SHOULD) |

**Application scope:**
- All 25 commands MUST use RFC-2119 keywords for enforcement language.
- All 9 canonical modes MUST use RFC-2119 keywords to replace suggestive language ("prefer", "consider", "propose", "optionally"). Each replacement requires per-instance judgment — not mechanical substitution.

#### Mode Enforcement Mapping

Suggestive language in canonical modes MUST be replaced with RFC-2119 keywords:

| Source Pattern | Replacement Pattern | Judgment Required |
|---|---|---|
| "Prefer X" | `SHOULD X` (strong default with justified deviation) or `MUST X` (if non-optional) | Yes — evaluate if deviation is ever acceptable |
| "consider X" | `MUST consider X` (if mandatory) or `SHOULD consider X` (if recommended) | Yes — evaluate if skipping consideration is acceptable |
| "propose X" | `MUST propose X` (active output requirement) | Usually MUST — proposing is an action, not a preference |
| "optionally" | `MAY` | Direct mapping |

---

### Command Gate Requirements

All 25 commands are categorized by implementation priority for gate standardization.

#### P0 — Core (deep redesign)

| Command | Required Gates | Notes |
|---|---|---|
| `/blueprint` | Comprehension (Confirmation, `MUST ... UNLESS --fast`), Checkpoint (Confirmation, `MUST ... UNLESS --fast`), Preview (Confirmation, always fires). Add governance output logic (producer rules). | Governance producer. Only structural gates. |
| `/implement` | Understand (Confirmation, always). Pre-Implementation Approval (Approval, Critical baseline or custom). Inter-Increment Feedback (Feedback, Standard/Critical baseline or custom). Increment-specific custom gates (per governance schema). | Governance consumer. Plan-driven resolution. |

#### P1 — High-risk, zero gates (new gates)

| Command | Required Gates | Notes |
|---|---|---|
| `/pr` | PR Confirmation (Confirmation) before creating PR — show target branch, title, Plan Delta preview. | External write (VCS + tracker). |
| `/publish` | Publish Confirmation (Confirmation) before publishing — show artifact list, sync status, closure implications. | Irreversible closure action. |

#### P2 — Existing text-based gates (migrate to `AskQuestion`)

| Command | Required Gates | Notes |
|---|---|---|
| `/commit` | Branch Safeguard (Confirmation) — migrate existing text-based warning on main/master/develop. Commit Plan Confirmation (Confirmation) — show files and messages before execution. | Existing text-based gate. |
| `/enrich` | Classification Comprehension (Confirmation) when tracker signals conflict with user declaration or classification is ambiguous. Tracker Write (Confirmation) before remote enrichment write. | Existing text-based tracker write gate plus new classification gate. |
| `/consolidate-plan` | Artifact Update (Confirmation) — migrate existing text-based update instruction. | Existing text-based gate. |
| `/copyedit` | Target Confirmation (Confirmation) — migrate existing implicit path confirmation. | Implicit gate. |

#### P3 — Artifact-writing commands (new Artifact Preview gates)

| Command | Required Gates | Notes |
|---|---|---|
| `/assessment` | Artifact Preview (Confirmation) before writing `feasibility.assessment.md`. | Coexists with END-OF-RESPONSE CONFIRMATION. |
| `/brief` | Tracker Publish (Confirmation) when user requests publish to tracker. Chat-only output needs no gate. | Gate only on external write. |
| `/report` | Evidence Sufficiency (Confirmation) when RCA fields lack enough evidence for publish. Tracker Publish (Confirmation) when user requests publish to tracker. Chat-only output needs no gate. | External write with evidence gate before publish when needed. |
| `/charter` | Artifact Preview (Confirmation) before writing `delivery.charter.md`. | Coexists with END-OF-RESPONSE CONFIRMATION. |
| `/issue` | Artifact Preview (Confirmation) before writing `report.issue.md`. | Coexists with END-OF-RESPONSE CONFIRMATION. |
| `/fix` | Artifact Preview (Confirmation) before writing `analysis.fix.md`. | Coexists with END-OF-RESPONSE CONFIRMATION. |
| `/trace` | Artifact Preview (Confirmation) before writing `instrumentation.trace.md` (when TASK_DIR is set). | File write is conditional. |
| `/validate-plan` | Governance validation gaps check. | No tracker transition (ownership moved to `/enrich`). |

#### Sweep-only — RFC-2119 language standardization (no new gates)

| Command | Action | Notes |
|---|---|---|
| `/run` | Enforcement language sweep only. | Low-risk (local simulator). |
| `/test` | Enforcement language sweep only. | Low-risk (local test execution). |
| `/spm` | Enforcement language sweep only. | Has `--dry-run` safety. |
| `/guide` | Enforcement language sweep only. | Advisory, chat-only. |
| `/explain` | Enforcement language sweep only. | Advisory, chat-only. |
| `/self-review` | Enforcement language sweep only. | Advisory, chat-only local review. |
| `/peer-review` | Enforcement language sweep only. | Advisory, read-only VCS review. |
| `/handoff` | Enforcement language sweep only. | Advisory, operational handoff formatting. |

---

### Contextual Governance

Governance behavior in `/implement` is **contextual to the task** — determined by Plan Classification and optional custom gates in the plan artifact, not hardcoded in the command.

#### Governance-in-Artifact Schema

An optional `## Governance` section within `increments.plan.md` contains **only per-increment custom gates** that go beyond the classification baseline. Classification, task-level gates, and default behavior are derived from `status.md` — never duplicated in this section.

```markdown
## Governance

| Increment | Gate Point | Gate Type | Gate Prompt | Options |
|-----------|-----------|-----------|-------------|---------|
| <name> | before-start | Approval | "<prompt>" | <pipe-separated options> |
| <name> | after-completion | Decision | "<prompt>" | <pipe-separated options> |
```

**Column definitions:**

| Column | Allowed Values | Description |
|---|---|---|
| Increment | Increment name from the plan | Which increment this gate applies to |
| Gate Point | `before-start` \| `after-completion` | When the gate fires relative to increment execution |
| Gate Type | `Confirmation` \| `Decision` \| `Feedback` \| `Approval` | One of the 4 interactive gate types |
| Gate Prompt | Free text | The prompt presented via `AskQuestion` |
| Options | Pipe-separated list | The options for `AskQuestion` |

**Rules:**
- The Governance section MUST NOT restate classification baselines.
- The Governance section MUST NOT include Precondition gates.
- Each row represents exactly one custom gate at one gate point for one increment.
- Custom gates are **additive** — they augment the baseline, never replace it.

#### Classification Baselines

Minimum governance requirements per classification. These are **non-reducible** — no command, mode, or custom governance can remove a baseline gate.

| Classification | Structural Gates (always) | Pre-Implementation Gate | Inter-Increment Gate | Custom Governance |
|---|---|---|---|---|
| **Minor** (Local/Low-Risk) | Understand (Confirmation) | None | None | MUST NOT be present |
| **Standard** (Medium-Impact) | Understand (Confirmation) | None | Feedback after each increment | MAY be present if risk warrants |
| **Critical** (Critical/Strategic) | Understand (Confirmation) | Approval before first increment | Feedback after each increment | MUST be present with ≥1 Approval gate |

**Notes:**
- "Understand" is structural (part of `/implement` Phase 3) and fires for all classifications. It verifies comprehension, not governance.
- "Feedback after each increment" = Feedback-type `AskQuestion` after completing each increment: continue / adjust / stop.
- "Approval before first increment" = Approval-type `AskQuestion` before executing the first increment: approve / reject.

#### Producer Rules (`/blueprint`)

`/blueprint` is the governance **producer**. It writes the `## Governance` section in `increments.plan.md` based on classification.

| Classification | Producer Behavior |
|---|---|
| **Minor** | MUST NOT generate a `## Governance` section. If custom gates are needed, MUST escalate classification to Standard first. |
| **Standard** | MAY generate a `## Governance` section when risk analysis warrants gates beyond the baseline (risk severity, external dependencies, cross-module impact). |
| **Critical** | MUST generate a `## Governance` section with at least 1 Approval gate at the highest-risk increment. |

**`--fast` interaction:** `/blueprint --fast` skips Comprehension and Checkpoint structural gates but does NOT affect classification assignment or governance output.

#### Consumer Resolution (`/implement`)

`/implement` is the governance **consumer**. At runtime, it resolves which gates to fire using this 3-step precedence logic:

```
Step 1: READ classification from status.md
  ├── classification = minor → Baseline Minor (no inter-increment gates)
  ├── classification = standard → Baseline Standard (Feedback after each increment)
  ├── classification = critical → Baseline Critical (Approval before first + Feedback after each)
  └── classification = null (legacy) → GOTO Step 3

Step 2: CHECK for ## Governance section in increments.plan.md
  ├── Section exists → For each gate point in current increment:
  │     ├── Custom gate defined at this point → Fire custom gate (skip baseline at this point)
  │     └── No custom gate at this point → Fire baseline gate (if any)
  └── Section absent → Fire only baseline gates per classification

Step 3: LEGACY FALLBACK (no classification in status.md)
  → Treat as Standard: Feedback gate after each increment
  → Ignore any ## Governance section
  → Log warning: "No classification found. Using legacy fallback (Standard behavior)."
```

#### Precedence Rule

At each gate point for each increment, **exactly one gate fires**:

1. If a custom gate is defined at this point → fire the custom gate.
2. Else if a baseline gate exists at this point → fire the baseline gate.
3. Else → no gate at this point.

MUST NOT fire both custom and baseline at the same point.

#### Escalation Compatibility

Classification changes from `/charter` auto-propagate because `/implement` reads `status.md` at runtime. No additional mechanism needed.

#### Governance Validation (`/validate-plan`)

`/validate-plan` MUST check these governance conditions:

| Check | Condition | Result |
|---|---|---|
| Critical without governance | `classification = critical` AND no `## Governance` section | **Gap**: "Critical requires a Governance section with ≥1 Approval gate." |
| Minor with governance | `classification = minor` AND `## Governance` section exists | **Gap**: "Minor MUST NOT have a Governance section. Escalate classification or remove." |
| Critical without approval | `classification = critical` AND `## Governance` exists but zero Approval gates | **Gap**: "Critical Governance requires ≥1 Approval gate." |
| Missing classification | `classification = null` | **Gap** (existing check): "Classification not assigned." |

---

### Coexistence and Backward Compatibility

#### Artifact Preview vs END-OF-RESPONSE CONFIRMATION

These are distinct patterns that coexist in the same command:

| Pattern | Purpose | Timing | Mechanism | Blocking |
|---|---|---|---|---|
| **Artifact Preview** | User decides whether to write | BEFORE write | `AskQuestion` (Confirmation) | Yes |
| **END-OF-RESPONSE CONFIRMATION** | Inform user what was written | AFTER write | Chat text output | No |

When both are present, the sequence is: Context → Artifact Preview gate → Write → END-OF-RESPONSE CONFIRMATION.

#### Legacy Plan Behavior

When `/implement` encounters a plan without classification (created before governance):
1. Finds `classification: null` in `status.md`.
2. Enters legacy fallback: Standard baseline (Feedback after each increment).
3. Ignores any `## Governance` section.
4. Logs warning in chat.

---

## v5 Conventions

### Task Directory Writing

Commands that produce artifacts MUST write to the task directory (`<resolved_tasks_dir>/<TASK_ID>/`), not to standalone paths. The **rho-aias** skill defines the directory structure, artifact catalog (12 types + `status.md`), and naming conventions. See `aias/contracts/readme-artifact.md` for the full artifact contract.

### TASK_DIR Field

The Structured Prompt convention includes a `TASK_DIR` field that resolves the task directory. In user-facing prompts, `TASK DIR` is preferred and `DIR` is an allowed ergonomic alias. When `TASK_ID` / `TASK ID` is provided and `TASK_DIR` / `TASK DIR` is not, the task directory defaults to the task identifier. `TICKET` may remain as a legacy input alias, but it is not the canonical framework term. Commands MUST respect this field for directory resolution.

### Plan Delta Section

The `/pr` command includes a Plan Delta section comparing planned artifacts vs actual implementation. This is generated by comparing `increments.plan.md` against `git diff`.

### `/publish` Command Type

`/publish` is an Operative command that performs reconciliation and closure operations: reconciliation sync through the resolved knowledge provider, Plan Delta generation, and task completion. It is **mode-agnostic** — invocable from any chat session.

### Tracker Sync Convention

Commands that trigger tracker transitions MUST declare the transition in their Output Contract (Section 4) under a "TRACKER SYNC (Phase 6)" subsection. Only four commands trigger transitions: `/enrich`, `/blueprint`, `/pr`, `/commit`. `/blueprint` has an additional bug exception variant that transitions `pending_dor` -> `in_progress` directly when DoR/DoD are generated via bug exception. Transitions must be expressed in canonical status form and resolved through `status_mapping_source` defined in `aias-config/providers/tracker-config.md`. See `aias/contracts/readme-tracker-status-mapping.md` for mapping rules.

### Skills Reference Convention

Commands that reference skills MUST declare them in the Identity section (Section 1) using the format: `**Skills referenced:** skill-name-1, skill-name-2.`

---

## v5.1 Conventions

### `/assessment` Command

`/assessment` is an Operative command that evaluates fix feasibility. It bridges `/fix` output to `/blueprint` input in bugfix workflows by filtering error mechanisms and solutions against codebase evidence. Produces `feasibility.assessment.md`.

### Plan Classification

`/blueprint` MUST assign a Plan Classification (`minor`, `standard`, or `critical`) in `status.md`. `/validate-plan` MUST verify the classification is present. `/charter` MAY escalate the classification (minor→standard, standard→critical) but MUST NOT downgrade it. Classification determines closure requirements:
- **Minor:** `/report` or `/brief` to the resolved tracker provider
- **Standard/Critical:** `/publish` to the resolved knowledge provider

### Structured Prompt — Artifact Reference Fields

In addition to the standard fields (`MODE`, `REPO`, `TASK ID`, `TASK DIR`, `PROFILE`, `PLAN`, `FIGMA`, `CONTEXT`, `TASK`), the Structured Prompt supports artifact reference fields: `ISSUE:`, `FIX:`, `ASSESSMENT:`, `TRACE:`. `DIR:` is an allowed alias for `TASK DIR`. `TICKET:` may be accepted as a legacy alias for `TASK ID`, but new documentation MUST prefer `TASK ID`. Artifact reference fields resolve relative to TASK_DIR and instruct the agent to load the referenced artifact as primary context.

### One Mode Per Chat

Commands do not enforce mode boundaries, but all documentation and workflow profiles assume the **one mode per chat** rule: each chat session uses exactly one mode, and handoffs between modes happen via artifact files across chats.

Artifacts remain the **durable handoff layer** between chats. The `/handoff` command MAY produce an **operational handoff snippet** in chat, but that snippet is advisory and transient. It MUST NOT replace TASK_DIR artifacts as the source of truth.

---

## v6 Conventions

### Governance Section

The **Governance** section (above) is the canonical source for all gate behavior, enforcement language, and contextual governance rules. Commands MUST comply with the Gate Invocation Protocol, use the Canonical Gate Section Pattern for gate definitions, and follow the Command Gate Requirements for their priority tier.

### Contract Version

This contract is version **v6**. The Governance section is new in v6. All prior conventions (v5, v5.1) remain in effect unless explicitly superseded by the Governance section.

### Backward Compatibility

Commands that predate this version continue to function. The Governance section introduces new requirements that are applied incrementally per the Command Gate Requirements priority tiers (P0 → P1 → P2 → P3 → Sweep).

---

## Consistency Rules

- All commands must follow this template **in order**
- Each command must declare its category in **Identity**
- Output format decisions must be system-wide, not ad-hoc
- When in doubt, prefer explicitness over brevity
- Artifact-producing commands MUST follow the **rho-aias** skill loading protocol
- Commands must declare their skill references in the Identity section

This document is the **source of truth** for command structure.
