# Enrich (Tracker-Backed Task Enrichment) — v4

## 1. Identity

**Command Type:** Type B — Procedural / Execution

You are **analyzing and enriching** a task that lacks sufficient detail for autonomous development.
This command reads tracker data for the provided task id via the resolved tracker provider, evaluates its completeness against a product and technical checklist, generates missing content, writes the product analysis to the task directory, and writes only structured fields to the resolved tracker provider. Full prose content stays local and syncs through the resolved knowledge provider via progressive publishing.

**Skills referenced:** `rho-aias`, `technical-writing`, `incremental-decomposition`.

---

## 2. Invocation / Usage

Invocation:

- `/enrich <TASK_ID>`

Usage notes:

- `<TASK_ID>` is required (e.g., `MAX-12761`). When the task id maps to a tracker ticket, the resolved tracker provider is used for enrichment. It also sets TASK_DIR to <resolved_tasks_dir>/<TASK_ID>/. (Default: `~/.cursor/plans/`)
- The enriched output is always written to `analysis.product.md` in TASK_DIR.
- Structured fields (AC, test steps, priority, components) are written to the resolved tracker provider after user confirmation.
- A reference comment is posted in the resolved tracker provider linking to the local artifact.
- This command does NOT trigger any tracker status transition (it is a pre-DoR activity).
- This command works best after `@product` has provided product analysis (JTBD, 5 Whys, User Journey, MoSCoW), but it can also be used standalone.

---

## 3. Inputs

This command may use **only** the following inputs:

- Tracker ticket content read via resolved provider from `aias-providers/tracker-config.md` (description, comments, linked issues, status, transitions)
- Chat context explicitly provided by the user (including prior `@product` analysis if present)
- Project architecture and conventions from the active base rule
- Upstream artifacts from TASK_DIR if they exist (loaded via **rho-aias** skill (Phases 0–3)
- Service configs:
  - `aias-providers/tracker-config.md`
  - `aias-providers/knowledge-config.md`

Rules:

- `<TASK_ID>` is mandatory. If not provided, ask for it before proceeding.
- All inputs must be explicit. Do not infer task ids or tracker ticket ids from vague references.
- If tracker or knowledge service config is missing, invalid, or unresolvable, STOP and request provider configuration.
- If resolved tracker provider cannot read the ticket, STOP and inform the user.

---

## 4. Output Contract (Format)

### Local Artifact

Write `analysis.product.md` to TASK_DIR with the full enriched content (gap summary, enhanced ticket content, product analysis).

### Tracker Output (after user confirmation)

Write **only structured fields** to the resolved tracker provider:
- **Acceptance Criteria**: Given/When/Then criteria. Append if content exists.
- **Test Steps**: Numbered verification steps. Append if content exists.
- **Priority**: Set only when provider rules allow priority update.
- **Components**: Set only when provider rules allow component update and the platform is identifiable.

Provider-specific field keys must come from resolved tracker provider mapping.

Post a **reference comment** on the resolved tracker provider: "Product analysis artifact available locally at <resolved_tasks_dir>/<TASK_ID>/analysis.product.md. Full content published via the configured knowledge provider."

Do NOT write prose content (description, user flow, architecture analysis) to the tracker ticket description. The full prose lives in `analysis.product.md` and syncs via the resolved knowledge provider.

### Gate: Tracker Write Preview

**Type:** Confirmation
**Fires:** Phase 4, before writing structured fields to the resolved tracker provider.
**Skippable:** No.

**Context output:**
Present tracker write preview in chat:
- Task ID
- Fields to update (list with summary of content per field)
- Reference comment: yes
- Status transition: none

**AskQuestion:**
- **Runtime compatibility:** If `AskQuestion` is unavailable, use the Text Gate Protocol from `readme-commands.md` with the same prompt, option ids, labels, and `allow_multiple` semantics.
- **Prompt:** "Write structured fields to <TASK_ID> via tracker provider?"
- **Options:**
  - `write`: "Write fields and post reference comment"
  - `skip`: "Skip tracker write — keep local artifact only"
- **allow_multiple:** false

**On response:**
- `write` → Write structured fields to resolved tracker provider, post reference comment
- `skip` → Skip tracker write; `analysis.product.md` is still written locally

**Anti-bypass:** Inherits Gate Invocation Protocol. No additional rules.

### End-of-Response Confirmation

After writing the artifact:
```
Saved artifact to: <absolute_path>/analysis.product.md
[Tracker fields updated: <list> | Tracker update skipped]
```

### Status Update (Phase 5)

After writing `analysis.product.md`:
1. Create TASK_DIR and `status.md` if they do not exist (profile: infer from context, default `feature`; if only enrichment is planned, use `enrichment`).
2. Add `analysis.product.md` to `artifacts` map with status `created` or `modified`.
3. Add `product-analysis` to `completed_steps`. Set `current_step` based on the profile: if `enrichment` → `closure`; otherwise → `blueprint`.
4. Run Phase 5c (classification-gated): sync non-synced artifacts to resolved knowledge provider only if classification in `status.md` is B or C. Skip if null or A (see **rho-aias** skill § Phase 5c).

---

## 5. Content Rules (Semantics)

- Output must be in **English**.
- Apply the **technical-writing** skill patterns: Problem Framing, Acceptance Criteria, Risk Articulation, Conciseness.
- When generating file impact or acceptance criteria with increment granularity, apply the **incremental-decomposition** skill.
- Do **NOT** invent information that cannot be inferred from the ticket, chat context, or project architecture.
- When information is missing and cannot be inferred, mark it as **[Needs input]** with a targeted question.
- If `@product` analysis exists in the chat context (JTBD, User Journey, MoSCoW), incorporate it directly.

---

## 6. Internal Execution Model

### Phase 1 — Read

1. Follow **rho-aias** skill loading protocol (Phases 0–3) to resolve TASK_DIR and load existing artifacts.
2. Resolve tracker provider from `aias-providers/tracker-config.md`; if missing/invalid/unresolvable, abort and request provider configuration.
3. Use the resolved provider to read the ticket: description, acceptance criteria, comments, linked issues, status.
4. If `@product` analysis is present in the chat context, collect it as supplementary input.

### Phase 2 — Analyze

Evaluate the ticket against the Completeness Checklist:

| Dimension | What it must contain |
|-----------|---------------------|
| **Problem statement** | What problem is being solved and for whom |
| **Acceptance criteria** | Verifiable criteria for "done" (happy path + edge cases) |
| **User flow** | Complete flow: entry point → action → intermediate states → exit |
| **API / Data contract** | Endpoints involved if applicable |
| **UI specification** | Design reference or description of visual states if applicable |
| **File impact** | Files to create/modify according to the project's architecture |
| **Dependencies** | Modules, packages, or external services affected |
| **Non-functional requirements** | Performance, security, accessibility if applicable |
| **Test criteria** | What must be tested (unit, integration, manual) |
| **Out of scope** | What is explicitly NOT included |

Classify each dimension as: **present** / **incomplete** / **missing**.

### Phase 3 — Enrich

1. For each dimension classified as **incomplete** or **missing**, generate concrete content.
2. For dimensions that cannot be completed without user input, include a **[Needs input]** marker.
3. Assemble the enhanced version.

### Phase 4 — Present + Write

1. Show in chat: Gap Summary table + Enhanced Ticket content.
2. Write `analysis.product.md` to TASK_DIR.
3. Fire **Gate: Tracker Write Preview** (structured fields only).
4. If confirmed: write structured fields to resolved tracker provider + post reference comment.
5. Run Phase 5 (status update + knowledge sync).

SERVICE RESOLUTION PSEUDOFLOW:

```
tracker = resolve(tracker-config) or abort(missing/invalid tracker config)
knowledge = resolve(knowledge-config) or abort(missing/invalid knowledge config)
```

---

## 7. Non-Goals / Forbidden Actions

This command must **NOT**:

- Implement code or modify repository files
- Write prose content to the tracker ticket description (only structured fields)
- Trigger any tracker status transition
- Infer task ids or tracker ticket ids from vague references
- Invent technical details not derivable from the ticket or project architecture
- Proceed if resolved tracker provider cannot read the ticket (STOP and inform)
- Execute any git, build, or deployment operations
- Write artifacts outside TASK_DIR
