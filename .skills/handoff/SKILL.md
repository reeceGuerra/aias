---
name: handoff
description: "Formats an operational handoff summary for transitioning context between modes or sessions. Use at the end of a chat session or before switching to a different mode. Trigger terms: /handoff, handoff, transition context, end of session, switch mode."
category: advisory
disable-model-invocation: true
version: 1.2.0
---

# Handoff (Operational Cross-Chat Transfer) — v1.2

## 1. Identity

**Command Type:** Advisory — Chat-only / Operational formatting

You are generating an operational handoff snippet that transfers **observed context** from the current chat to another chat or agent. The handoff describes where things stand — it does not prescribe what the next agent should do. What to do next is always the user's decision.

This command complements the durable artifact handoff model by producing a transient Markdown snippet. It does not replace TASK_DIR artifacts as the source of truth.

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
- To satisfy the Terminal State Contract while preserving single-block output, the block MUST end with a terminal state line: `[STATE: delivered | inconclusive]` + one-line summary.

---

## 5. Content Rules (Semantics)

- The snippet content MUST be in **English**.
- The command MUST prefer explicit user-provided destination over inferred destination.
- Controlled resolution is allowed only for `/handoff` and only because the user explicitly requested a handoff artifact.
- Any assumption or inferred destination MUST be declared inside the snippet.
- **Context only — no prescription:** Every bullet in the handoff MUST describe observed state (what happened, what is known, what was found). It MUST NOT tell the next agent what to do, what to produce, or what to achieve. Deciding the next action is the user's responsibility.
- **Descriptive step lists are allowed:** A list of steps that describes observed behavior (e.g., reproduction steps for a bug, migration steps already executed) is contextual and permitted. A list of steps that prescribes future agent actions is forbidden.
- Extra sections beyond the required base MUST come only from the closed contextual mappings defined in Section 6.
- **Path resolution:** Before emitting the snippet, resolve the shortcut path for MODE and COMMAND based on the primary tool (first entry) in `binding.generation.tools` from `stack-profile.md`. The resolved path MUST always be the **installed shortcut location** — never a framework internal path (`aias/.skills/`, `aias/.modes/`). Use the tool adapter mapping:
  - `cursor`: `.cursor/rules/<mode>.mdc`, `.cursor/skills/<command>/SKILL.md`
  - `claude`: `.claude/rules/<mode>.md`, skills not supported for commands (fall back to `aias-config/skills/<command>/SKILL.md`)
  - `copilot`: `.github/instructions/<mode>.instructions.md`, `.github/agents/<command>.md`
  - `codex`: modes not supported (fall back to `aias-config/modes/<mode>.mdc`), `.codex/commands/<command>.md`
  - When a tool does not support a given type (per `readme-tool-adapter.md`), fall back directly to `aias-config/modes/<mode>.mdc` for modes or `aias-config/skills/<command>/SKILL.md` for commands — never to `aias/.skills/` or `aias/.modes/`.
  - If `binding.generation.tools` is missing or the tool is unknown, emit `aias-config/modes/<mode>.mdc` for modes and `aias-config/skills/<command>/SKILL.md` for commands.
- **Path resolution — existence check (v1.2):** Path existence MUST be verified using an `lstat`-equivalent check that DOES NOT follow symlinks. The shortcut location (e.g., `.cursor/skills/<command>/SKILL.md`) is frequently a symlink pointing to `aias-config/skills/<command>/SKILL.md`; a follow-the-target check that fails on broken targets is acceptable, but a check that returns "missing" merely because the symlink target lives elsewhere is FORBIDDEN. When in doubt, treat the symlink itself as the canonical existence signal. Only fall back to `aias-config/` when the shortcut path neither exists as a regular file nor as a symlink.
- **Path resolution — input normalization (v1.2):** Before resolving MODE or COMMAND names, apply the minimal normalization pipeline below to user-provided values; nothing more, nothing less:
  1. Strip a single leading `/` if present (`/blueprint` → `blueprint`).
  2. Lower-case the value (`Blueprint` → `blueprint`).
  3. Preserve kebab-case structure intact (`self-review` stays `self-review`; do NOT collapse hyphens or replace them with spaces/underscores).
  4. Trim surrounding whitespace.
  Heavier normalizations (alias expansion, fuzzy matching, semantic substitution) are FORBIDDEN — they create silent misroutes when an unknown name resembles a known one.
- **Path resolution — catalog validation (v1.2):** After normalization, MUST validate the value against the closed catalog of installed skills (the union of `aias-config/skills/` and any tool-specific shortcuts directory). Unknown names MUST NOT be accepted optimistically. When the normalized value is not in the catalog, emit the shortcut path as best-effort and append `[fallback reason: skill not found in installed catalog]` to the COMMAND line per § 6.
- **Path resolution — fallback reporting (v1.2):** When the resolution path falls back to `aias-config/` for any reason (shortcut location does not exist, tool does not support the type, unknown tool, unknown skill name), the COMMAND or MODE line MUST end with the bracketed annotation `[fallback reason: <reason>]`. Acceptable reasons include: `shortcut path not found`, `tool does not support skills`, `tool does not support modes`, `unknown tool in binding.generation.tools`, `binding.generation.tools missing`, `skill not found in installed catalog`. Silent fallback is FORBIDDEN.
- Path resolution applies to both MODE and COMMAND for framework-defined entries (source: `aias/.skills/`, `aias-config/modes/`). Project-specific skills in `aias-config/skills/` are out of scope for handoff resolution.

---

## 6. Output Structure (Template)

````markdown
```markdown
MODE: <resolved mode shortcut path or "Unspecified"> [fallback reason: <reason>]?
COMMAND: <resolved command shortcut path or "Open"> [fallback reason: <reason>]?
REPO: <repo or "Unspecified">
TASK ID: <task id or "Unspecified">
DIR: <task dir or "Unspecified">

Context:
- <what happened; current state; relevant decisions already made>

Constraints:
- <known limits, risks, or boundaries already established in this session>

Assumptions:
- <explicit assumptions made; unknowns that carry forward — or "None">

[Optional contextual block for `@debug` + `/fix`]
Known validated bug:
- <bug statement as observed>
Observed reproduction context:
- <steps to reproduce as observed>
Environment:
- <environment details>

[Optional contextual block for `@dev` + `/assessment`]
Assessment context:
- <what was analyzed; relevant findings from the current session>
Behavioral reference:
- <artifact / evidence / contract already in play>

[Optional contextual block for `@planning` + `/blueprint`]
Planning context:
- <planning state reached; decisions and constraints already established>
Assessment outcome to honor:
- <assessment takeaway that must carry forward>
Behavioral reference:
- <artifact / constraint / reference already in scope>

[Optional contextual block for review follow-up]
What was verified:
- <reviewed surface>
Findings:
- <carry-forward findings>
Assumptions / unknowns:
- <unknowns>

[STATE: delivered | inconclusive] <one-line summary>
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
- Add sections not defined in Section 6 (e.g., `TASKS:`, `Next Steps:`, `Action Items:`, `Steps:` as a prescriptive list, `Goal:`, `Expected output:`, `Instructions:`, `Requested output:`)
- Include any content that tells the next agent what to do, what to achieve, or what to produce — that is the user's decision

---

## 8. Self-Verification Checklist

- [ ] Output includes required handoff fields and explicit uncertainty where evidence is incomplete.
- [ ] No file mutations or external write operations were performed.
- [ ] Any read-only provider lookups were correctly attributed.
- [ ] Terminal state line was emitted with canonical advisory token.

## 9. Halt Discipline

- Pause only at declared preconditions/blockers.
- Do not add ad-hoc confirmation pauses between deterministic formatting steps.
- If blocked, report blocker and required resume input.

## Terminal State Emission

`[STATE: delivered | inconclusive]` + one-line summary is mandatory.

## Invocation Mode Detection

- Standalone default.
- If invoked in a chain, behavior remains advisory/read-only; no semantic divergence is allowed.
