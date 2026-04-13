# Charter (Delivery Assessment) — v3

## 1. Identity

**Command Type:** Operative — Procedural / Execution

You are generating a **delivery charter** — a structured assessment that determines whether planned work is ready, viable, and well-understood before execution begins. This command transforms raw delivery data from `@delivery` into a structured document written to the task directory, with readiness evaluation, effort estimation, viability analysis, impact analysis, dependency mapping, execution timeline, and a clear recommendation.

**Skills referenced:** `rho-aias`, `technical-writing`, `incremental-decomposition`.

---

## 2. Invocation / Usage

Invocation:
- `/charter`

Usage notes:
- This command is intended to be used within `@delivery` mode.
- It can work **with plans** (full charter: viability, effort, dependencies, timeline) or **without plans** (preliminary triage: rough scope, viability, key questions to resolve).
- The output will be saved to a `delivery.charter.md` file.
- The primary input is `@delivery`'s evaluation of plan artifacts, tracker tickets, or both.

---

## 3. Inputs

This command may use **only** the following inputs:
- Chat context explicitly provided by the user
- Output from `@delivery` mode (raw delivery assessment data)
- References to plan artifacts in TASK_DIR or tracker tickets already evaluated by `@delivery`
- Upstream artifacts from TASK_DIR loaded via **rho-aias** skill (Phases 0–3)

Rules:
- All inputs must be explicit.
- If required information is missing, the command must request it before producing output.
- Do not fetch or read external sources (tracker/design/vcs providers, etc.); `@delivery` already did that.

---

## 4. Output Contract (Format)

### Gate: Artifact Preview

**Type:** Confirmation
**Fires:** Before writing `delivery.charter.md` to TASK_DIR.
**Skippable:** No.

**Context output:**
Present artifact summary in chat:
- Artifact: `delivery.charter.md`
- Target: TASK_DIR path
- Verdict and criticality from charter analysis
- Increment count and overall estimation

**AskQuestion:**
- **Runtime compatibility:** If `AskQuestion` is unavailable, use the Text Gate Protocol from `readme-commands.md` with the same prompt, option ids, labels, and `allow_multiple` semantics.
- **Prompt:** "Write delivery charter to <TASK_DIR>?"
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
- Write `delivery.charter.md` to TASK_DIR.
- If TASK_DIR does not exist, create it. Create `status.md` if it does not exist.
- The charter content must be the ONLY content in the file.

STATUS UPDATE (Phase 5)
- Add `delivery.charter.md` to the `artifacts` map in `status.md` with status `created` or `modified`.
- Add `charter` to `completed_steps`, set `current_step` to `closure`.
- **Classification escalation**: if the charter's assessment reveals higher impact than the current classification (e.g., cross-team dependencies, broader org impact), escalate the classification in `status.md` (minor→standard or standard→critical). MUST NOT downgrade. Report escalation in chat.
- Append to `command_log`: `{command: /charter, started_at: <UTC>, ended_at: <UTC>}` — obtain timestamps via `date -u +%Y-%m-%dT%H:%M:%SZ`. See `reference.md` § Command Log for full rules.
- Run Phase 5c: sync non-synced artifacts to resolved knowledge provider. Phase 5c always publishes — it is NOT conditioned by plan classification (see **rho-aias** skill § Phase 5c).

END-OF-RESPONSE CONFIRMATION (must follow)
- After writing the charter file, you MUST print a final line in the chat response (not in the file) exactly in this format:
  `Saved charter to: <absolute_path>`
- `<absolute_path>` must resolve to the fully expanded absolute path.

---

## 5. Content Rules (Semantics)

- Output must be in **English**.
- Apply the **technical-writing** skill patterns: Risk Articulation, Increment Goals, Conciseness.
- Apply the **incremental-decomposition** skill for increment estimation alignment (Estimation Alignment section in reference).
- Do **NOT** invent information.
- Use **ONLY** the provided inputs from `@delivery` mode.
- If information is missing, leave the section empty or include a short placeholder comment (e.g. `<!-- Not evaluated -->`).
- Structure the raw delivery data into the exact format specified below.
- Do **NOT** include implementation code, detailed technical steps, or file structure.
- Effort estimates must use relative sizing (S/M/L/XL), never hours or days.
- Mermaid diagrams must be syntactically valid and renderable.

---

## 6. Output Structure (Template)

The charter file MUST follow this exact structure:

```markdown
# Charter: <Title>

> **Verdict:** <Ready | Needs Info | Blocked | Risky | Out of Scope>
> **Criticality:** <Critical | High | Medium | Low>
> **Date:** <YYYY-MM-DD>

---

## 1) Executive Summary

<What is being evaluated, why it matters, and the overall recommendation in 2-3 lines. An executive reader should be able to read only this section and understand the recommendation.>

---

## 2) Plan Reference

| Field | Value |
|-------|-------|
| **Plan file** | <path to .plan.md or "N/A"> |
| **Tracker ticket(s)** | <ticket keys or "N/A"> |
| **Planning mode** | <@planning or "N/A"> |

---

## 3) Readiness Assessment

| DoR Dimension | Status | Gaps |
|---------------|--------|------|
| Functional | <Complete / Partial / Missing> | <gaps or "None"> |
| Non-Functional | <Complete / Partial / Missing> | <gaps or "None"> |
| Technical | <Complete / Partial / Missing> | <gaps or "None"> |
| Test Cases | <Complete / Partial / Missing> | <gaps or "None"> |
| Resources & Access | <Complete / Partial / Missing> | <gaps or "None"> |

### Open Questions (if any)

<Prioritized questions that must be resolved before proceeding. Each with priority: Critical / Important / Nice-to-have.>

---

## 4) Effort Estimation

| Increment | Complexity | Size | Confidence | Rationale |
|-----------|------------|------|------------|-----------|
| <Increment 1 name> | <Low/Med/High> | <S/M/L/XL> | <High/Med/Low> | <brief justification> |
| <Increment 2 name> | <Low/Med/High> | <S/M/L/XL> | <High/Med/Low> | <brief justification> |
| ... | ... | ... | ... | ... |
| **Total** | — | <aggregate size> | <overall confidence> | — |

---

## 5) Viability Analysis

### Technical Viability
<Is it feasible with the current stack? Any technology blockers?>

### Organizational Viability
<Team availability, approvals, access, coordination needed?>

### Scope Viability
<Is the scope realistic given the estimates? Risk of scope creep?>

---

## 6) Impact Analysis

### Technical Impact
<Modules, repos, services affected. What breaks if this goes wrong?>

### Business Impact
<Users, flows, KPIs affected. Business value.>

### Organizational Impact
<Teams that need to coordinate. Cross-team dependencies.>

---

## 7) Dependencies & Risks

### Dependencies

| Dependency | Type | Status | Notes |
|------------|------|--------|-------|
| <dependency> | <Technical / External / Temporal> | <Available / Pending / Blocked> | <notes> |
| ... | ... | ... | ... |

### Risks

| Risk | Type | Level | Mitigation |
|------|------|-------|------------|
| <risk description> | <scope / dependency / ambiguity / performance / unknown impact> | <Low / Medium / High> | <mitigation strategy> |
| ... | ... | ... | ... |

---

## 8) Dependency Map

```mermaid
graph TD
    <dependency relationships between modules, repos, services, and external dependencies>
```

---

## 9) Execution Timeline

```mermaid
gantt
    title Execution Timeline
    dateFormat X
    axisFormat %s
    <sections and increments with dependencies and parallelisms>
```

---

## 10) Recommendation

**Verdict:** <Ready | Needs Info | Blocked | Risky | Out of Scope>

<Clear recommendation with conditions if applicable. If "Needs Info", list what must be resolved. If "Blocked", state the blocker and path to unblock. If "Risky", state type, level, and mitigation. If "Conditional", list the conditions that must be met before proceeding.>
```

---

## 7. Non-Goals / Forbidden Actions

This command must **NOT**:
- Perform delivery analysis (that's `@delivery` mode's job)
- Invent information; only structure input from `@delivery`
- Infer missing context
- Write or modify code
- Touch files or repositories except writing the charter file to TASK_DIR
- Write artifacts outside TASK_DIR
- Suggest alternative designs or improvements
- Execute commands or scripts
- Generate code snippets or implementation details
- Fetch data from external services (tracker/design/vcs providers); `@delivery` already did that
