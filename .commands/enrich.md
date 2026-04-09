# Enrich (Tracker-Backed Task Enrichment) — v4

## 1. Identity

**Command Type:** Type B — Procedural / Execution

You are **analyzing and enriching** a task that lacks sufficient detail for autonomous development.
This command reads tracker data for the provided task id via the resolved tracker provider, evaluates its completeness against a product and technical checklist, classifies the task shape for description formatting, generates missing content, writes the product analysis to the task directory, and can push a curated remote enrichment to the resolved tracker provider after confirmation. The local artifact remains the complete canonical analysis; tracker fields receive a provider-adapted representation for collaboration.

**Skills referenced:** `rho-aias`, `technical-writing`, `incremental-decomposition`.

---

## 2. Invocation / Usage

Invocation:

- `/enrich <TASK_ID>`

Usage notes:

- `<TASK_ID>` is required (e.g., `MAX-12761`). When the task id maps to a tracker ticket, the resolved tracker provider is used for enrichment. It also sets TASK_DIR to <resolved_tasks_dir>/<TASK_ID>/. (Default: `~/.cursor/plans/`)
- The enriched output is always written to `analysis.product.md` in TASK_DIR.
- Remote enrichment is written to the resolved tracker provider only after user confirmation.
- `Enhanced by` headers exist only in the remote push representation. They do NOT appear in `analysis.product.md` or the local preview content.
- This command does NOT trigger any tracker status transition (it is a pre-DoR activity).
- This command works best after `@product` has provided product analysis (JTBD, 5 Whys, User Journey, MoSCoW), but it can also be used standalone.

---

## 3. Inputs

This command may use **only** the following inputs:

- Tracker ticket content read via resolved provider from `aias-providers/tracker-config.md`:
  - summary
  - description
  - issue type
  - labels
  - components
  - parent / epic context when available
  - comments
  - linked issues
  - status
  - transitions
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

Write the following remote enrichment to the resolved tracker provider:
- **Description**: preserve human content outside the Rho AIAS-owned block; insert or update a curated `Enhanced by` block using only the relevant narrative subset from the analysis.
- **Acceptance Criteria**: preserve human content outside the Rho AIAS-owned block; insert or update a field-specific `Enhanced by` block with verifiable criteria only.
- **Test Steps**: preserve human content outside the Rho AIAS-owned block; insert or update a field-specific `Enhanced by` block with test steps only.
- **Priority**: Set only when provider rules allow priority update.
- **Components**: Set only when provider rules allow component update and the platform is identifiable.

Provider-specific field keys must come from resolved tracker provider mapping.

Remote field representation rules:
- `analysis.product.md` remains the complete local source of truth and MUST NOT be rewritten to include provider-specific headers.
- The `Enhanced by` block exists only in the payload written to the tracker provider.
- `Description` MUST use a curated subset of the analysis. It MUST NOT copy the full content of `analysis.product.md`.
- `Description` MAY include: problem/context, expected behavior or scope, condensed user flow, and key constraints or risks.
- `/enrich` MUST NOT write RCA fields or push RCA narrative to tracker fields. `/report` owns the six RCA fields for bug workflows.
- `Acceptance Criteria` and `Test Steps` MUST contain only field-specific content; they MUST NOT duplicate narrative sections from `Description`.
- The tool signature SHOULD be `Rho AIAS via <ToolName>` when the active tool/runtime can be determined safely. Otherwise use `Rho AIAS`.

The push payload MUST NOT include local filesystem paths, machine-specific references, or comments that only make sense on the author's machine.

Description shaping rules:
- These are the currently supported **description rendering families**, not a closed taxonomy of all possible work classifications in the framework.
- If classified as `feature` with `user_facing` orientation, `Description` SHOULD use a user-facing outcome structure (e.g. user story + scope).
- If classified as `bugfix`, `Description` SHOULD use `Problem / Expected / Actual` framing without RCA sections.
- If classified as `refactor`, `technical_debt`, or `infrastructure`, `Description` SHOULD use a system-facing structure such as `Technical Intent / Scope / Constraints`.
- If the resolved classification does not map cleanly to one of these supported description families, `/enrich` MUST use a neutral description format or fire the Classification Comprehension gate when required.

### Gate: Classification Comprehension

**Type:** Confirmation
**Fires:** After classification, only when tracker signals and user-declared classification conflict or when classification confidence is insufficient for selecting a description format.
**Skippable:** No.

**Context output:**
Present classification context in chat:
- Tracker signals observed
- User-declared classification, if any
- Proposed `work_type`
- Proposed `orientation`
- Proposed description format
- Why the classification is conflicting or ambiguous

**AskQuestion:**
- **Runtime compatibility:** If `AskQuestion` is unavailable, use the Text Gate Protocol from `readme-commands.md` with the same prompt, option ids, labels, and `allow_multiple` semantics.
- **Prompt:** "How should `/enrich` classify <TASK_ID> for description shaping?"
- **Options:**
  - `proposed`: "Use the proposed classification"
  - `user`: "Use the user-declared classification"
  - `neutral`: "Use a neutral description format"
- **allow_multiple:** false

**On response:**
- `proposed` → Continue with the proposed classification
- `user` → Continue with the user-declared classification
- `neutral` → Continue with a neutral description format and no specialized template

### Gate: Tracker Write Preview

**Type:** Confirmation
**Fires:** Phase 4, before writing structured fields to the resolved tracker provider.
**Skippable:** No.

**Context output:**
Present tracker write preview in chat:
- Task ID
- Fields to update (list with summary of content per field)
- `Enhanced by` block action per field (`create` / `update` / `skip`)
- Description subset summary
- Format per field (`markdown` / `adf`)
- Status transition: none

**AskQuestion:**
- **Runtime compatibility:** If `AskQuestion` is unavailable, use the Text Gate Protocol from `readme-commands.md` with the same prompt, option ids, labels, and `allow_multiple` semantics.
- **Prompt:** "Write enriched fields to <TASK_ID> via tracker provider?"
- **Options:**
  - `write`: "Write enriched fields to tracker"
  - `skip`: "Skip tracker write — keep local artifact only"
- **allow_multiple:** false

**On response:**
- `write` → Write enriched fields to the resolved tracker provider
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
- For remote tracker writes, treat the tracker field payload as a derived representation of the local analysis, not as the canonical source.
- The local artifact and local preview MUST stay provider-agnostic and MUST NOT contain `Enhanced by` headers.
- Classification signals from tracker metadata MAY be used to shape `Description`, but `/enrich` MUST surface ambiguity or conflict through the Classification Comprehension gate instead of deciding silently.

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

Derive task classification for description shaping:
- `work_type`: `feature`, `bugfix`, `refactor`, `technical_debt`, or `infrastructure`
- `orientation`: `user_facing` or `system_facing`

Classification precedence:
1. Tracker structural signals (`issuetype`, labels, components, parent / epic, comparable metadata)
2. Explicit user-declared classification from chat context
3. Heuristic reading of the ticket content
4. Neutral fallback when confidence remains insufficient

If tracker signals and user-declared classification conflict, or if confidence is insufficient, fire **Gate: Classification Comprehension** before selecting the description format.

### Phase 3 — Enrich

1. For each dimension classified as **incomplete** or **missing**, generate concrete content.
2. For dimensions that cannot be completed without user input, include a **[Needs input]** marker.
3. Assemble the enhanced version using the resolved description format.
4. Derive the remote push payload separately:
   - `Description` = curated narrative subset only
   - `Acceptance Criteria` = field-specific criteria only
   - `Test Steps` = field-specific test steps only
   - tracker-owned fields (`Priority`, `Components`) only when supported and justified

### Phase 4 — Present + Write

1. Show in chat: Gap Summary table + Enhanced Ticket content.
2. Write `analysis.product.md` to TASK_DIR.
3. Fire **Gate: Tracker Write Preview** (remote field enrichment only).
4. If confirmed: write the remote enrichment payload to the resolved tracker provider.
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
- Publish local filesystem paths or machine-specific references to the tracker provider
- Populate or publish RCA fields
- Push RCA narrative into tracker `Description`
- Trigger any tracker status transition
- Infer task ids or tracker ticket ids from vague references
- Invent technical details not derivable from the ticket or project architecture
- Proceed if resolved tracker provider cannot read the ticket (STOP and inform)
- Execute any git, build, or deployment operations
- Write artifacts outside TASK_DIR
