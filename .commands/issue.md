# Issue (Bug Report) — v3

## 1. Identity

**Command Type:** Operative — Procedural / Execution

You are generating a **bug report** (issue) to document defects found during QA.
This command is responsible for transforming raw QA data from `@qa` into a structured, evidence-driven bug report written to the task directory. The report must be **ready for @debug** (repro, expected/actual, environment, severity) so the flow @qa → /issue → @debug is smooth. Content is observational only; there is **no "Possible Fix" section** (that is provided by @debug + /fix in another chat).

**Skills referenced:** `rho-aias`, `technical-writing`.

---

## 2. Invocation / Usage

Invocation:
- `/issue`

Usage notes:
- This command is intended to be used **after** `@qa` mode has generated raw QA data.
- It must not be invoked as a first step when QA information is incomplete.
- The output will be saved to a `report.issue.md` file.

---

## 3. Inputs

This command may use **only** the following inputs:
- Chat context explicitly provided by the user
- Output from `@qa` mode (raw QA data: observations, evidence, repro steps, etc.)
- Logs, screenshots references, or notes explicitly pasted by the user

Rules:
- All inputs must be explicit.
- If required information is missing, the command must request it before producing output.

---

## 4. Output Contract (Format)

### Gate: Artifact Preview

**Type:** Confirmation
**Fires:** Before writing `report.issue.md` to TASK_DIR.
**Skippable:** No.

**Context output:**
Present artifact summary in chat:
- Artifact: `report.issue.md`
- Target: TASK_DIR path
- Bug title and severity
- Steps to reproduce count

**AskQuestion:**
- **Runtime compatibility:** If `AskQuestion` is unavailable, use the Text Gate Protocol from `readme-commands.md` with the same prompt, option ids, labels, and `allow_multiple` semantics.
- **Prompt:** "Write bug report to <TASK_DIR>?"
- **Options:**
  - `write`: "Write artifact to TASK_DIR"
  - `adjust`: "Adjust content before writing"
- **allow_multiple:** false

**On response:**
- `write` → Write artifact to TASK_DIR, proceed to End-of-Response Confirmation
- `adjust` → Apply corrections, return to context output and re-present gate

**Anti-bypass:** Inherits Gate Invocation Protocol. No additional rules.

FILE OUTPUT CONTRACT (must follow)
- Follow the **rho-aias** skill loading protocol Phase 0 to resolve TASK_DIR.
- If TASK_DIR is set (via Structured Prompt, task id, or context): write `report.issue.md` to TASK_DIR.
- If TASK_DIR is not set: create a new directory `<resolved_tasks_dir>/<Name>/` (default: ~/.cursor/plans/) using a kebab-case name derived from the bug title, and write `report.issue.md` there.
- Create `status.md` if it does not exist (profile: `bugfix`).
- The bug report content must be the ONLY content in the file. The template has **no "Possible Fix"** section.

STATUS UPDATE (Phase 5)
- Add `report.issue.md` to the `artifacts` map in `status.md` with status `created` or `modified`.
- Add `investigate` to `completed_steps`, set `current_step` to `analyze`.
- Run Phase 5c: sync non-synced artifacts to resolved knowledge provider. Phase 5c always publishes — it is NOT conditioned by plan classification (see **rho-aias** skill § Phase 5c).

END-OF-RESPONSE CONFIRMATION (must follow)
- After writing the bug report file, you MUST print a final line in the chat response (not in the file) exactly in this format:
  Saved issue to: <absolute_path>
- <absolute_path> must resolve to the fully expanded absolute path.

---

## 5. Content Rules (Semantics)

- Output must be in **English**.
- Apply the **technical-writing** skill patterns: Problem Framing, Conciseness.
- Do **NOT** invent information.
- Use **ONLY** the provided inputs from `@qa` mode.
- If information is missing, leave the section empty or include a short placeholder comment.
- Be objective and factual; avoid emotional or subjective language.
- Do **NOT** speculate about root cause unless explicitly supported by evidence.
- **MUST NOT** propose architectural changes or fixes.
- Focus on **observability, clarity, and reproducibility**.

---

## 6. Output Structure (Template)

The bug report file must follow this exact structure:

```markdown
## Bug Report: <clear, concise title>

## Description
<!-- Brief description of the issue and its impact -->

## Environment
- **Device**:
- **OS**:
- **App / Browser Version**:
- **Screen Resolution**: <!-- if relevant -->
- **User Role / Permissions**: <!-- if relevant -->

## Severity
<!-- Critical | High | Medium | Low | Trivial -->
<!-- Short justification -->

## Steps to Reproduce
1.
2.
3.

## Expected Behavior
<!-- What should happen -->

## Actual Behavior
<!-- What actually happens -->

## Visual Evidence
<!-- References to screenshots or videos, if any -->

## Logs / Error Messages
<!-- Relevant logs or error output, if any -->

## Additional Notes
<!-- Any other relevant context -->
```

---

## 7. Non-Goals / Forbidden Actions

This command MUST **NOT**:
- Perform QA analysis or testing (that's `@qa` mode's job)
- Invent repro steps, logs, or environment details
- Include root cause or fix proposal (the /issue template has no "Possible Fix" section; if critical data is missing, leave sections empty or "Unknown")
- Infer missing context
- Debug the issue or propose root causes
- Write or modify code
- Touch files or repositories (except writing the issue file to TASK_DIR)
- Write artifacts outside TASK_DIR
- Suggest refactors or architectural changes
- Execute commands or scripts
- Assign blame or make subjective judgments
