# Enrich (Tracker-Backed Task Refinement) — v5

## 1. Identity

**Command Type:** Type B — Procedural / Execution

You are **analyzing, enriching, and refining** a task for autonomous development. This command reads tracker data for the provided task id via the resolved tracker provider, evaluates its completeness against a product and technical checklist, classifies the task shape for description formatting, generates missing content, writes the product analysis to the task directory, and can push a curated remote enrichment to the resolved tracker provider after confirmation. Additionally, it produces **Definition of Ready** (`dor.plan.md`) and **Definition of Done** (`dod.plan.md`) artifacts from a dedicated structuring phase, publishes all artifacts to the knowledge provider, and triggers the canonical tracker transition `pending_dor` -> `ready` when publishing succeeds.

The local artifact remains the complete canonical analysis; tracker fields receive a provider-adapted representation for collaboration.

**Skills referenced:** `rho-aias`, `technical-writing`, `incremental-decomposition`.

---

## 2. Invocation / Usage

Invocation:

- `/enrich <TASK_ID>`

Usage notes:

- `<TASK_ID>` is required (e.g., `MAX-12761`). When the task id maps to a tracker ticket, the resolved tracker provider is used for enrichment. It also sets TASK_DIR to <resolved_tasks_dir>/<TASK_ID>/. (Default: `~/.cursor/plans/`)
- The enriched output is always written to `analysis.product.md` in TASK_DIR.
- DoR/DoD artifacts (`dor.plan.md`, `dod.plan.md`) are written to TASK_DIR after the readiness check.
- Remote enrichment is written to the resolved tracker provider only after user confirmation.
- `Enhanced by` headers exist only in the remote push representation. They do NOT appear in `analysis.product.md` or the local preview content.
- When publishing succeeds, this command triggers the canonical tracker transition `pending_dor` -> `ready`.
- This command works best after `@product` has provided product analysis (JTBD, 5 Whys, User Journey, MoSCoW), but it can also be used standalone.

---

## 3. Inputs

This command may use **only** the following inputs:

- Tracker ticket content read via resolved provider from `aias-config/providers/tracker-config.md`:
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
- Upstream artifacts from TASK_DIR if they exist (loaded via **rho-aias** skill (Phases 0–3)):
  - `report.issue.md` (for bugfix DoR derivation)
  - `analysis.fix.md` (for bugfix DoR derivation)
  - `feasibility.assessment.md` (for bugfix DoR derivation)
- Service configs:
  - `aias-config/providers/tracker-config.md`
  - `aias-config/providers/knowledge-config.md`

Rules:

- `<TASK_ID>` is mandatory. If not provided, ask for it before proceeding.
- All inputs must be explicit. Do not infer task ids or tracker ticket ids from vague references.
- If tracker or knowledge service config is missing, invalid, or unresolvable, STOP and request provider configuration.
- If resolved tracker provider cannot read the ticket, STOP and inform the user.

---

## 4. Output Contract (Format)

### File Output

| Artifact | Content |
|----------|---------|
| `analysis.product.md` | Gap summary, enhanced ticket content, product analysis |
| `dor.plan.md` | Definition of Ready — scope, criteria, and constraints for the task |
| `dod.plan.md` | Definition of Done — checklist of criteria for QA readiness |

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
- If classified as `spike`, `Description` SHOULD use `Hypothesis / Time-box / Success Criteria` framing.
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
- Status transition that will fire after publishing: `pending_dor` → `ready`

**AskQuestion:**
- **Runtime compatibility:** If `AskQuestion` is unavailable, use the Text Gate Protocol from `readme-commands.md` with the same prompt, option ids, labels, and `allow_multiple` semantics.
- **Prompt:** "Write enriched fields to <TASK_ID> via tracker provider?"
- **Options:**
  - `write`: "Write enriched fields to tracker"
  - `skip`: "Skip tracker write — keep local artifacts only (no tracker transition)"
- **allow_multiple:** false

**On response:**
- `write` → Write enriched fields to the resolved tracker provider
- `skip` → Skip tracker write; local artifacts are still written but tracker transition does not fire

**Anti-bypass:** Inherits Gate Invocation Protocol. No additional rules.

### Gate: DoR Readiness Check

**Type:** Confirmation
**Fires:** Phase 3-DoR, after structuring DoR/DoD artifacts but before writing them.
**Skippable:** No.

**Context output:**
Present DoR readiness check in chat. Each dimension is classified as **BLOCKING** or **non-blocking** based on the scope of the task (e.g., UI specification is BLOCKING only when the task has UI scope):

```
DoR READINESS (<work_type>):
  [ok] <Dimension>: present
  [!!] <Dimension>: missing — BLOCKING (<reason>)
  [--] <Dimension>: missing — non-blocking (recommended)
  ...

  Readiness: <READY | BLOCKED (N blocking items)>
  Recommendation: <action suggestion>
```

**AskQuestion:**
- **Runtime compatibility:** If `AskQuestion` is unavailable, use the Text Gate Protocol from `readme-commands.md` with the same prompt, option ids, labels, and `allow_multiple` semantics.
- **Prompt:** "DoR readiness check complete. <N> blocking items. Proceed?"
- **Options:**
  - `proceed`: "Proceed — no blocking items" (only when zero blockers)
  - `override`: "Accept risk and proceed despite blockers"
  - `stop`: "Stop — resolve blockers first"
- **allow_multiple:** false

**On response:**
- `proceed` → Continue to write artifacts
- `override` → Continue with acknowledged risk
- `stop` → Halt execution; inform user which blockers need resolution

### End-of-Response Confirmation

After writing all artifacts:
```
Saved artifacts to: <absolute_path>/
  - analysis.product.md
  - dor.plan.md
  - dod.plan.md
[Tracker fields updated: <list> | Tracker update skipped]
[Knowledge provider: <published | skipped | failed>]
[Tracker transition: pending_dor → ready | skipped]
```

### TRACKER SYNC (Phase 6 — after publishing)

- When readiness check passes (no blockers or override accepted) AND tracker write confirmed AND `task_id` in `status.md` is valid for the resolved tracker provider:
  1. Publish artifacts to resolved knowledge provider (Phase 5c).
  2. If knowledge publish succeeds: resolve tracker provider from `aias-config/providers/tracker-config.md`.
  3. Transition canonical tracker status from `pending_dor` -> `ready` using provider mapping.
  4. If config is missing, invalid, or unresolvable: abort sync and request provider configuration.
  5. Report transition result in chat.
- When readiness check fails (blocker without override) OR tracker write skipped: no publish, no tracker transition.
- When knowledge publish fails: no tracker transition (artifacts remain local, report error).

### Status Update (Phase 5)

After writing artifacts:
1. Create TASK_DIR and `status.md` if they do not exist (profile: infer from context, default `feature`; if only enrichment is planned, use `enrichment`).
2. Add `analysis.product.md`, `dor.plan.md`, and `dod.plan.md` to `artifacts` map with status `created` or `modified`.
3. Add `refinement` to `completed_steps`. Set `current_step` based on the profile: if `enrichment` → `closure`; otherwise → `blueprint`.
4. Set `refinement_validated` in `status.md`: `true` if tracker write was confirmed and publish succeeded; `false` otherwise.
5. Set `status` in `status.md`: `ready` if tracker transition succeeded; preserve previous value otherwise.
6. Run Phase 5c: sync non-synced artifacts to resolved knowledge provider. Phase 5c always publishes — it is NOT conditioned by plan classification.

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
- DoR Test criteria define **what** must be tested (scenarios, happy path, edge/corner cases, failure scenarios). They do NOT define **how** to implement the tests — that is the responsibility of `/blueprint` (Category 9: Testing).

---

## 6. Internal Execution Model

### Phase 1 — Read

1. Follow **rho-aias** skill loading protocol (Phases 0–3) to resolve TASK_DIR and load existing artifacts.
2. Resolve tracker provider from `aias-config/providers/tracker-config.md`; if missing/invalid/unresolvable, abort and request provider configuration.
3. Load `field_mapping_source` from the resolved tracker config (MANDATORY for write commands). If field mapping is missing or unresolvable, STOP with `MISSING_FIELD_MAPPING` and request configuration via `/aias configure-providers`.
4. Use the resolved provider to read the ticket: description, acceptance criteria, comments, linked issues, status.
5. If `@product` analysis is present in the chat context, collect it as supplementary input.

### Phase 2 — Analyze (Completeness Checklist)

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
- `work_type`: `feature`, `bugfix`, `refactor`, `spike`, `technical_debt`, or `infrastructure`
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

### Phase 3-DoR — Structure DoR/DoD

Structure the information collected in Phase 2 and Phase 3 into DoR and DoD artifacts. This phase transforms already-collected data — it does NOT re-collect or re-ask the user for information that is already available.

**Sources:** Completeness Checklist results (Phase 2), enriched content (Phase 3), upstream artifacts from TASK_DIR, chat context. No codebase reading.

**DoR feature template** — 6 dimensions:

| Dimension | Source | Content |
|-----------|--------|---------|
| **Functional** | Checklist: User flow + Acceptance criteria | Happy path, UX expectations, visible states |
| **Non-Functional** | Checklist: NFRs | Performance, security, accessibility constraints |
| **Technical constraints** | Checklist: File impact + Dependencies + API/Data | Known constraints from product perspective (NOT codebase architecture — that is `/blueprint`) |
| **Test criteria** | Checklist: Test criteria | **What** must be tested: happy path scenarios, edge cases, corner cases, failure scenarios. Does NOT define how to implement tests (that is `/blueprint` Cat 9). |
| **Commitment** | Tracker: status, linked issues, comments | Analysis of the requirement, team dependencies, blocking items, branch status |
| **Out of scope** | Checklist: Out of scope | Explicit boundaries of what is NOT included in this task |

**DoR bugfix template** (when upstream artifacts `report.issue.md`, `analysis.fix.md`, `feasibility.assessment.md` exist):

| Dimension | Source | Content |
|-----------|--------|---------|
| **Steps to reproduce** | `report.issue.md` | Exact reproduction steps |
| **Expected vs actual** | `report.issue.md` | Expected behavior and observed behavior |
| **Root cause hypothesis** | `analysis.fix.md` | Likely root cause from prior analysis |
| **Viable solutions** | `feasibility.assessment.md` | Evaluated solution approaches |
| **Regression scope** | All upstream artifacts | Areas at risk of regression |
| **Affected versions** | `report.issue.md`, tracker | Versions where the bug is present |

**DoR refactor template:**

| Dimension | Source | Content |
|-----------|--------|---------|
| **Technical debt metric** | Checklist / codebase context | What indicator triggers this refactor (complexity, coupling, duplication, performance) |
| **Scope boundary** | Checklist | Files, modules, or layers affected; explicit limits |
| **Target state** | Checklist | Desired end state (architecture, performance, readability) |
| **Regression risk** | Checklist | Areas at risk, existing test coverage, behavior preservation requirements |
| **Test criteria** | Checklist | Before/after comparisons, no behavior change verification, performance benchmarks if applicable |
| **Out of scope** | Checklist | What is NOT being refactored |

**DoR spike template** (lightweight — bounded by time-box):

| Dimension | Source | Content |
|-----------|--------|---------|
| **Hypothesis** | Checklist / ticket | What we are trying to learn, prove, or evaluate |
| **Time-box** | Checklist / ticket | Maximum time allocated for the spike |
| **Success criteria** | Checklist | What constitutes a successful spike (decision made, prototype built, proof obtained) |
| **Out of scope** | Checklist | What is NOT part of the spike (production code, deployment, full implementation) |

**DoD feature:** Checklist of criteria that determine when the implemented scope is ready for QA (not production).
**DoD bugfix:** Fix implemented, root cause confirmed, regression tests pass, no new bugs introduced.
**DoD refactor:** Refactored code compiles, all existing tests pass, no behavior change (unless explicitly scoped), documentation updated if architecture changed.
**DoD spike:** Hypothesis answered (confirmed/rejected/inconclusive), findings documented, decision recommendation provided.

After structuring, fire **Gate: DoR Readiness Check**.

### Phase 3b — Field Write Plan

Before presenting the write preview, resolve the format for each target field:

For each field that `/enrich` intends to write:

1. `field_key` — from the loaded field mapping.
2. `ownership` — which command/role owns writes to this field (verify `/enrich` is allowed).
3. `merge_strategy` — `create_or_replace_managed_block` | `set_if_default` | `append` | `skip`.
4. `content_format` — resolve with precedence:
   1. Runtime field metadata (from the ticket read response) — highest priority.
   2. Mapping document (`Format` column in `jira-field-mapping.md`) — second priority.
   3. Default (ADF for custom textarea fields, Markdown for description) — lowest priority.
5. `decision_source` — `runtime` | `mapping` | `default`.

Include the resolved write plan in the **Gate: Tracker Write Preview** context output.

### Phase 4 — Present + Write

1. Show in chat: Gap Summary table + Enhanced Ticket content + DoR/DoD summary.
2. Write `analysis.product.md` to TASK_DIR.
3. Write `dor.plan.md` and `dod.plan.md` to TASK_DIR.
4. Fire **Gate: Tracker Write Preview** (remote field enrichment only).
5. If confirmed: write the remote enrichment payload to the resolved tracker provider.
6. Run Phase 5 (status update).
7. Run Phase 6 (tracker sync — publish + transition).

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
- Infer task ids or tracker ticket ids from vague references
- Invent technical details not derivable from the ticket or project architecture
- Proceed if resolved tracker provider cannot read the ticket (STOP and inform)
- Execute any git, build, or deployment operations
- Write artifacts outside TASK_DIR
- Define **how** to implement tests (that is `/blueprint` Cat 9 responsibility); DoR Test criteria only define **what** must be tested
- Read the codebase to determine architecture or file structure for DoR Technical constraints (that is `/blueprint` responsibility); DoR Technical constraints only capture what is known from the product/ticket perspective
