# Feature Brief (Ticket Companion) — v4

## 1. Identity

**Command Type:** Operative — Procedural / Execution

You are generating a **feature brief** to be attached to a ticket.  
This command is responsible for transforming validated analysis into a concise, structured summary for tracking and communication purposes.

**Skills referenced:** `rho-aias`, `technical-writing`.

---

## 2. Invocation / Usage

Invocation:
- `/brief`

Usage notes:
- This command is intended to be used **after** a reasoning step (e.g. `@planning`).
- It must not be invoked as a first step when information is incomplete.

---

## 3. Inputs

This command may use **only** the following inputs:
- Chat context explicitly provided by the user
- Output from `@planning` or content of existing plan artifacts
- Plan artifacts from TASK_DIR loaded via **rho-aias** skill (Phases 0–3) if TASK_DIR is set
- Diffs, notes, or logs explicitly pasted by the user

Rules:
- All inputs must be explicit. The brief is a **ticket companion** (not a PR description).
- If required information is missing, the command must request it before producing output.

---

## 4. Output Contract (Format)

- **Default:** The response **MUST** be returned as **a single Markdown code block** using ```markdown (output only in chat).
- If the user **explicitly** asks to publish to the ticket (e.g. "publish to the ticket", "post as comment"), fire the Artifact Preview gate first, then resolve the tracker provider and publish.
- If tracker config is missing, invalid, or points to an unresolvable provider, abort publish and request provider configuration. Otherwise output only in chat.

### Gate: Artifact Preview

**Type:** Confirmation
**Fires:** Before publishing the brief to the resolved tracker provider (only when the user explicitly requests tracker publish).
**Skippable:** No.

**Context output:**
Present publish preview in chat:
- Brief content summary (title and key sections)
- Target task ID / tracker reference
- Tracker provider action (post as comment)

**AskQuestion:**
- **Runtime compatibility:** If `AskQuestion` is unavailable, use the Text Gate Protocol from `readme-commands.md` with the same prompt, option ids, labels, and `allow_multiple` semantics.
- **Prompt:** "Publish feature brief to <TASK_ID> via tracker provider?"
- **Options:**
  - `publish`: "Publish to tracker"
  - `adjust`: "Adjust content before publishing"
- **allow_multiple:** false

**On response:**
- `publish` → Publish via resolved tracker provider
- `adjust` → Apply corrections, return to context output and re-present gate

**Anti-bypass:** Inherits Gate Invocation Protocol. No additional rules.
- The code block **MUST start** with a Markdown heading (`##`). Only one code block is allowed. **NO text** outside the code block except when publishing to the resolved tracker provider.

SERVICE RESOLUTION PSEUDOFLOW:

```
resolveTrackerProvider():
  if tracker-config exists and is valid:
    use active_provider + skill_binding + provider parameters
  else:
    abort and request tracker service configuration
```

---

## 5. Content Rules (Semantics)

- Output must be in **English**.
- Apply the **technical-writing** skill patterns: Problem Framing, Conciseness.
- Do **NOT** invent information.
- Use **ONLY** the provided inputs.
- If information is missing, leave the section empty or include a short placeholder comment.
- This is **NOT** a PR description.
- Do **NOT** list files, commits, or diffs.
- Do **NOT** include code snippets unless explicitly provided in the input.

---

## 6. Output Structure (Template)

```markdown
## Feature Summary
<!-- What feature was implemented (1–2 sentences) -->

## Motivation
<!-- Why this feature was needed (user, product, or technical motivation) -->

## Key Decisions
<!-- 1–3 important design or technical decisions and why they were made -->
- 
- 

## Alternatives Considered
<!-- Briefly note any relevant alternatives that were considered and why they were rejected -->
- 

## Scope and Non-Goals
<!-- What this feature explicitly does NOT try to solve -->
- 

## Technical Notes
<!-- Relevant architecture, Use Cases, DI, concurrency, or performance considerations -->

## Validation Notes
<!-- High-level notes for QA: what to verify or pay attention to -->
```

---

## 7. Non-Goals / Forbidden Actions

This command must **NOT**:
- Perform analysis or reasoning
- Infer or invent motivation, decisions, or scope
- List files, commits, or diffs
- Write or modify code
- Touch files or repositories
- Publish to the ticket unless the user explicitly asks
- Suggest alternative designs or improvements
- Execute commands or scripts

