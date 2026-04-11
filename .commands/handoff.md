# Handoff (Operational Cross-Chat Transfer) — v1

## 1. Identity

**Command Type:** Type A — Chat-only / Operational formatting

You are generating an operational handoff snippet that transfers context from the current chat to another chat or agent without mutating files, status, or remote systems. This command complements the durable artifact handoff model by producing a transient Markdown snippet that makes the next step explicit.

**Skills referenced:** `rho-aias`.

---

## 2. Invocation / Usage

Invocation:
- `/handoff -m <mode> -c <command>`
- `/handoff --mode <mode> --command <command>`
- `/handoff -m <mode>`
- `/handoff -c <command>`
- `/handoff`

Optional flags:
- `-t, --task-id <TASK_ID>`
- `-r, --repo <repo>`

Usage notes:
- Canonical invocation is `/handoff -m <mode> -c <command>`.
- If only `-m` is provided, respect the mode and leave the command open when necessary.
- If only `-c` is provided, MAY resolve the destination mode from workflow evidence.
- If no flags are provided, MAY propose the next handoff only when the workflow evidence is clear enough to support a controlled resolution.

---

## 3. Inputs

This command may use **only** the following inputs:
- Explicit mode / command / task / repo flags provided by the user
- Chat context explicitly provided by the user
- Current workflow context already present in the conversation
- Local TASK_DIR artifacts when available through `rho-aias`
- `status.md` when available through TASK_DIR
- `stack-profile.md` (`binding.generation.tools`) for shortcut path resolution

Rules:
- The command MAY resolve a destination only after the user explicitly invokes `/handoff`.
- Resolution must be based on explicit workflow evidence already available in chat or TASK_DIR.
- If evidence is insufficient, the command MUST preserve uncertainty explicitly instead of inventing continuity.
- This command MUST NOT require external provider calls.

---

## 4. Output Contract (Format)

- Return exactly one fenced `markdown` code block.
- Do NOT include prose before or after the block.
- The block MUST be directly reusable as the opening payload for another chat / agent.
- The block MUST always include the required base sections defined in Section 6.

---

## 5. Content Rules (Semantics)

- The snippet content MUST be in **English**.
- The command MUST prefer explicit user-provided destination over inferred destination.
- Controlled resolution is allowed only for `/handoff` and only because the user explicitly requested a handoff artifact.
- Any assumption or inferred destination MUST be declared inside the snippet.
- This command MUST distinguish operational handoff from durable artifact handoff: it summarizes the next-step context, but does not replace TASK_DIR artifacts as the source of truth.
- Extra sections beyond the required base MUST come only from the closed contextual mappings defined in Section 6.
- **Path resolution:** Before emitting the snippet, resolve the shortcut path for MODE and COMMAND based on the primary tool (first entry) in `binding.generation.tools` from `stack-profile.md`. Use the tool adapter mapping:
  - `cursor`: `.cursor/rules/<mode>.mdc`, `.cursor/commands/<command>.md`
  - `claude`: `.claude/rules/<mode>.md`, command not supported (emit canonical: `aias/.commands/<command>.md`)
  - `copilot`: `.github/instructions/<mode>.instructions.md`, `.github/agents/<command>.md`
  - `codex`: mode not supported (emit canonical: `aias-config/modes/<mode>.mdc`), `.codex/commands/<command>.md`
  - If tool is unknown or `binding.generation.tools` is missing, emit the canonical path as fallback (`aias-config/modes/<mode>.mdc`, `aias/.commands/<command>.md`).
  - Always verify the resolved path exists before emitting. If missing, fall back to canonical.
  - Path resolution applies only to framework commands (`aias/.commands/`). Project-specific commands in `aias-config/commands/` are out of scope for handoff resolution.

---

## 6. Output Structure (Template)

````markdown
```markdown
MODE: <resolved mode shortcut path or "Unspecified">
COMMAND: <resolved command shortcut path or "Open">
REPO: <repo or "Unspecified">
TASK ID: <task id or "Unspecified">
DIR: <task dir or "Unspecified">

Context:
- <what the next chat needs to know>

Goal:
- <what the next chat should achieve>

Constraints:
- <relevant boundaries, assumptions, or risks>

Expected output:
- <what the next chat should produce>

Assumptions:
- <explicit assumptions or "None">

[Optional contextual block for `@debug` + `/fix`]
Known validated bug:
- <bug statement>
Observed reproduction context:
- <context>
Environment:
- <environment>
Instructions:
- <debug-specific instructions>

[Optional contextual block for `@dev` + `/assessment`]
Assessment focus:
- <focus>
Behavioral reference:
- <artifact / evidence / contract to honor>

[Optional contextual block for `@planning` + `/blueprint`]
Planning objective:
- <objective>
Assessment outcome to honor:
- <assessment takeaway>
Behavioral reference:
- <artifact / constraint / reference>
Requested output:
- <expected planning artifact/output>

[Optional contextual block for review follow-up]
What was verified:
- <reviewed surface>
Findings:
- <carry-forward findings>
Assumptions / unknowns:
- <unknowns>
Bottom line for next agent:
- <actionable summary>
```
````

---

## 7. Non-Goals / Forbidden Actions

This command must **NOT**:
- Write or update artifacts
- Update `status.md`
- Publish to tracker, knowledge provider, or VCS provider
- Hide uncertainty behind confident wording
- Infer a destination command when the user explicitly supplied only a mode and the command remains open
- Replace TASK_DIR artifacts as the durable handoff layer between chats
