# Assessment (Fix Feasibility Evaluation) — v2

## 1. Identity

**Command Type:** Operative — Procedural / Execution

You are evaluating the **feasibility of a fix proposal** by analyzing the error mechanisms and solutions from `analysis.fix.md`, filtering them against codebase evidence, and producing a concrete approach for planning. This command bridges the gap between debug analysis and planning: it ensures only validated mechanisms and viable solutions reach `/blueprint`.

**Skills referenced:** `rho-aias`, `technical-writing`.

---

## 2. Invocation / Usage

Invocation:
- `/assessment`

Usage notes:
- This command is intended to be used in `@dev` mode, **after** `analysis.fix.md` exists in TASK_DIR.
- It consumes the fix analysis and issue report to produce a feasibility assessment.
- The output feeds into `@planning` + `/blueprint` in a different chat.
- Use `FIX:` and `ISSUE:` Structured Prompt fields to reference the input artifacts.

---

## 3. Inputs

This command may use **only** the following inputs:
- `analysis.fix.md` from TASK_DIR loaded via **rho-aias** skill (Phases 0–3) — **required**
- `report.issue.md` from TASK_DIR loaded via **rho-aias** skill (Phases 0–3) — **required**
- Chat context explicitly provided by the user
- Codebase state (files, dependencies, existing code)

Rules:
- All inputs must be explicit.
- TASK_DIR must be resolvable. If not, ask the user for the task ID or directory path.
- If `analysis.fix.md` is not found, ask the user to run `/fix` first.
- If `report.issue.md` is not found, ask the user to run `/issue` first.
- Do NOT invent mechanisms or solutions not present in the fix analysis.

---

## 4. Output Contract (Format)

### Gate: Artifact Preview

**Type:** Confirmation
**Fires:** Before writing `feasibility.assessment.md` to TASK_DIR.
**Skippable:** No.

**Context output:**
Present artifact summary in chat:
- Artifact: `feasibility.assessment.md`
- Target: TASK_DIR path
- Verdict (Sufficient / Partial / Insufficient)
- Confirmed mechanisms count and viable solutions count

**AskQuestion:**
- **Runtime compatibility:** If `AskQuestion` is unavailable, use the Text Gate Protocol from `readme-commands.md` with the same prompt, option ids, labels, and `allow_multiple` semantics.
- **Prompt:** "Write feasibility assessment to <TASK_DIR>?"
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
- Write `feasibility.assessment.md` to TASK_DIR.
- Create `status.md` if it does not exist (profile: `bugfix`).

STATUS UPDATE (Phase 5)
- Add `feasibility.assessment.md` to the `artifacts` map in `status.md` with status `created` or `modified`.
- Add `assess` to `completed_steps`, set `current_step` to `blueprint`.
- Append to `command_log`: `{command: /assessment, started_at: <UTC>, ended_at: <UTC>}` — obtain timestamps via `date -u +%Y-%m-%dT%H:%M:%SZ`. See `reference.md` § Command Log for full rules.
- Run Phase 5c: sync non-synced artifacts to resolved knowledge provider. Phase 5c always publishes — it is NOT conditioned by plan classification. After each successful publish, inject TOC per resolved provider config (see **rho-aias** skill § Phase 5c).

END-OF-RESPONSE CONFIRMATION (must follow)
- After writing, print: `Saved assessment to: <absolute_path>`

---

## 5. Content Rules (Semantics)

- Output must be in **English**.
- Apply the **technical-writing** skill patterns: Problem Framing, Risk Articulation, Conciseness.
- Do **NOT** invent mechanisms or solutions beyond what `analysis.fix.md` provides.
- Do **NOT** skip mechanisms or solutions — evaluate every one explicitly.
- Validate mechanisms and solutions against the **actual codebase**, not just the fix analysis text.
- If the fix analysis is insufficient, the assessment must say so clearly and recommend further investigation.

---

## 6. Output Structure (Template)

The assessment file must follow this exact structure:

```markdown
## Feasibility Assessment: <clear, concise title from issue>

### 1) Problem Summary

<!-- Concise summary from report.issue.md. Only the essential context — do not repeat the full issue. -->

---

### 2) Fix Evaluation

#### 2a) Error Mechanisms

| # | Mechanism | Applies | Evidence | Priority |
|---|-----------|---------|----------|----------|
| 1 | <from fix> | Yes / No / Partial | <codebase evidence supporting or discarding> | Critical / High / Low |
| 2 | ... | ... | ... | ... |

**Confirmed mechanisms:** <list of Yes/Partial with brief rationale>
**Discarded mechanisms:** <list of No with brief rationale>

#### 2b) Proposed Solutions

| # | Solution | Viable | Covers mechanisms | Risk | Estimated effort |
|---|----------|--------|-------------------|------|-----------------|
| 1 | <from fix> | Yes / No | <mechanism numbers> | Low / Med / High | Low / Med / High |
| 2 | ... | ... | ... | ... | ... |

**Viable solutions:** <list of Yes with brief rationale>
**Discarded solutions:** <list of No with brief rationale>

#### 2c) Verdict

<!-- One of: Sufficient / Partial / Insufficient -->
<!-- Sufficient = viable solutions cover all confirmed mechanisms -->
<!-- Partial = viable solutions cover some but not all confirmed mechanisms -->
<!-- Insufficient = no viable solution covers the confirmed mechanisms -->

---

### 3) Proposed Approach

<!-- If Sufficient: refine and structure the viable solutions as a concrete approach for planning -->
<!-- If Partial: complete with a proposal for the uncovered mechanisms, based on codebase analysis -->
<!-- If Insufficient: propose a robust alternative approach based on codebase analysis -->

<!-- In all cases: concrete steps, files/modules involved, no vague ideas -->

---

### 4) Scope

- **Files/modules affected:** <list>
- **Dependencies involved:** <list or "none">
- **Breaking vs non-breaking:** <assessment>

---

### 5) Risk Analysis

- **Regression risks:** <list>
- **Edge cases:** <list>
- **Impact on other areas:** <list or "none">

---

### 6) Recommendation

<!-- One of: -->
<!-- **Proceed** — approach is solid, ready for /blueprint -->
<!-- **Investigate further** — needs more analysis before planning (specify what) -->
```

---

## 7. Non-Goals / Forbidden Actions

This command must **NOT**:
- Perform debugging (that's `@debug` mode's job)
- Invent mechanisms or solutions not in `analysis.fix.md`
- Write implementation code
- Skip evaluation of any mechanism or solution from the fix analysis
- Modify `analysis.fix.md` or `report.issue.md`
- Write artifacts outside TASK_DIR
- Execute commands or scripts beyond reading the codebase
