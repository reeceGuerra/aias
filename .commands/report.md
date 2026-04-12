# Bug RCA Report (Structured Tracker Publication) — v3

## 1. Identity

**Command Type:** Operative — Procedural / Execution

You are generating a **validated bug RCA report** for tracker publication after the bug has been investigated and the fix has been validated. This command is the owner of the six RCA fields for bug workflows. It prefers structured tracker fields when the provider supports them and falls back to a structured tracker comment only when equivalent fields do not exist.

**Skills referenced:** `rho-aias`, `technical-writing`.

---

## 2. Invocation / Usage

Invocation:
- `/report`

Usage notes:
- This command is intended to be used **after** a reasoning or debugging step (e.g. `@debug`, `@qa`).
- It must not be invoked if the root cause or fix has not been validated.
- `/report` owns the six RCA fields for bug workflows:
  - `RCA Determination`
  - `RCA Introduction Factor`
  - `RCA Detection Factor`
  - `RCA Analysis`
  - `RCA Corrective Action`
  - `RCA Preventive Action`

---

## 3. Inputs

This command may use **only** the following inputs:
- Chat context explicitly provided by the user
- Output from a prior reasoning step (e.g. `@debug`, `@qa`)
- Tracker ticket data and tracker field metadata read via the resolved provider:
  - issue type
  - current RCA field values
  - editable RCA fields
  - option catalogs for categorical RCA fields
- Artifacts from TASK_DIR loaded via **rho-aias** skill (Phases 0–3) if TASK_DIR is set:
  - `report.issue.md`
  - `analysis.fix.md`
  - `analysis.product.md`
  - `feasibility.assessment.md`
  - relevant `*.plan.md` artifacts
- Logs, diffs, or notes explicitly pasted by the user

Rules:
- All inputs must be explicit.
- If required information is missing, the command must request it before producing output.
- Do **NOT** infer RCA fields from symptoms alone. Use only validated evidence from the available inputs.

---

## 4. Output Contract (Format)

- **Default:** The response **MUST** be returned as **a single Markdown code block** using ```markdown (output only in chat).
- If the user **explicitly** asks to publish to the ticket (e.g. "publish to the ticket", "post as comment"), resolve the tracker provider, evaluate RCA field support and evidence sufficiency, then fire the required gates before publishing.
- If tracker config is missing, invalid, or points to an unresolvable provider, abort publish and request provider configuration. Otherwise output only in chat.

### Tracker Output (when user requests publish)

Publish bug RCA using this order of precedence:
- **Field-first:** write to structured RCA fields when the resolved tracker provider exposes equivalent fields.
- **Comment-last:** if equivalent structured fields do not exist, publish one structured fallback comment with the RCA sections.

For trackers that support the six RCA fields:
- **RCA Determination**: categorical field, write only a valid option id from the tracker catalog.
- **RCA Introduction Factor**: categorical field, write only a valid option id from the tracker catalog.
- **RCA Detection Factor**: categorical field, write only a valid option id from the tracker catalog.
- **RCA Analysis**: textarea field, prefer Markdown when supported; fall back to ADF when required.
- **RCA Corrective Action**: textarea field, prefer Markdown when supported; fall back to ADF when required.
- **RCA Preventive Action**: textarea field, prefer Markdown when supported; fall back to ADF when required.

Field sufficiency rules:
- Open-text RCA fields may be written only when evidence is sufficient or the user provides explicit text through the Evidence Sufficiency gate flow.
- Categorical RCA fields may be written only when the selected option is backed by sufficient evidence or explicitly chosen by the user from the tracker-supported catalog.
- If a field does not meet the sufficiency rule, `/report` MUST omit it when empty or leave it untouched when already populated.

### Gate: Evidence Sufficiency

**Type:** Confirmation
**Fires:** Before tracker publish, only when `/report` cannot complete one or more RCA fields with sufficient evidence.
**Skippable:** No.

**Context output:**
Present the RCA evidence summary in chat:
- Fields with sufficient evidence
- Fields that remain incomplete or ambiguous
- Why evidence is insufficient per missing field
- Allowed options for any categorical fields that still need explicit user choice

**AskQuestion:**
- **Runtime compatibility:** If `AskQuestion` is unavailable, use the Text Gate Protocol from `readme-commands.md` with the same prompt, option ids, labels, and `allow_multiple` semantics.
- **Prompt:** "Some RCA fields for <TASK_ID> still need user input. How should `/report` proceed?"
- **Options:**
  - `provide`: "I will provide the missing RCA values now"
  - `omit`: "Publish only the RCA fields with sufficient evidence"
  - `cancel`: "Cancel tracker publish"
- **allow_multiple:** false

**On response:**
- `provide` → Request only the missing values:
  - open-text fields as explicit text
  - categorical fields as one of the displayed tracker-supported options
- `omit` → Continue with only the fields that satisfy sufficiency
- `cancel` → Abort publish and keep chat output only

### Gate: Tracker Publish

**Type:** Confirmation
**Fires:** Before publishing the RCA report to the resolved tracker provider (only when the user explicitly requests tracker publish).
**Skippable:** No.

**Context output:**
Present publish preview in chat:
- RCA report summary (problem, RCA analysis, corrective action, preventive action)
- Target task ID / tracker reference
- Issue type and RCA field support status
- `rca_strategy`: `field_first` or `comment_fallback` (with justification)
- If `field_first`: list each RCA field to write with resolved `content_format` (markdown/adf/option_id) and `decision_source` (runtime/mapping/default)
- If `comment_fallback`: indicate publication as structured comment
- Comment fallback: yes / no

**AskQuestion:**
- **Runtime compatibility:** If `AskQuestion` is unavailable, use the Text Gate Protocol from `readme-commands.md` with the same prompt, option ids, labels, and `allow_multiple` semantics.
- **Prompt:** "Publish RCA report to <TASK_ID> via tracker provider?"
- **Options:**
  - `publish`: "Publish RCA to tracker"
  - `adjust`: "Adjust content before publishing"
- **allow_multiple:** false

**On response:**
- `publish` → Publish via resolved tracker provider using field-first, comment-last behavior
- `adjust` → Apply corrections, return to context output and re-present gate

**Anti-bypass:** Inherits Gate Invocation Protocol. No additional rules.
- The code block **MUST start** with a Markdown heading (`##`). Only one code block is allowed. Do not write to a file unless the contract defines it.

SERVICE RESOLUTION PSEUDOFLOW:

```
resolveTrackerProvider():
  if tracker-config exists and is valid:
    use active_provider + skill_binding + provider parameters
  else:
    abort and request tracker service configuration

  load field_mapping_source (MANDATORY for write commands)
  if field mapping is missing/unresolvable:
    STOP with MISSING_FIELD_MAPPING
    request configuration via /aias configure-providers

  resolve RCA field availability from field mapping + runtime metadata:
    if RCA custom fields exist in provider:
      rca_strategy = field_first
    else:
      rca_strategy = comment_fallback
```

---

## 5. Content Rules (Semantics)

- Output must be in **English**.
- Apply the **technical-writing** skill patterns: Problem Framing, Root Cause Description, Conciseness.
- Do **NOT** invent information.
- Use **ONLY** the provided inputs.
- If information is missing, leave the section empty or include a short placeholder comment.
- Focus on **causality and resolution**, not on implementation details.
- Do **NOT** include large code blocks unless explicitly provided in the input.
- Treat tracker field metadata as authoritative for what can be written remotely.
- If tracker runtime metadata and the documented project mapping diverge, use runtime metadata for the remote write and surface the mapping drift as a maintenance issue.

---

## 6. Output Structure (Template)

```markdown
## Problem Summary
<!-- Short description of the validated problem -->

## Expected vs Actual Behavior
**Expected:**
<!-- What should have happened -->

**Actual:**
<!-- What actually happened -->

## RCA Classification
**Determination:** <!-- Avoidable / Unavoidable or [Needs input] -->

**Introduction Factor:** <!-- Tracker-supported option or [Needs input] -->

**Detection Factor:** <!-- Tracker-supported option or [Needs input] -->

## RCA Analysis
<!-- The validated root cause analysis -->

## Corrective Action
<!-- What was changed to resolve the issue -->

## Preventive Action
<!-- What should prevent this class of issue in the future -->

## Supporting Evidence
<!-- Key evidence backing the RCA decisions -->
```

---

## 7. Non-Goals / Forbidden Actions

This command must **NOT**:
- Infer RCA values from symptoms alone; only structure what comes from validated context (e.g. `@debug`, `@qa`, `analysis.fix.md`)
- Publish to the ticket unless the user explicitly asks
- Perform analysis or debugging
- Infer missing context
- Treat categorical RCA fields as free text
- Publish tracker comments by default when structured RCA fields exist
- Write or modify code
- Touch files or repositories
- Suggest alternative fixes
- Execute commands or scripts

