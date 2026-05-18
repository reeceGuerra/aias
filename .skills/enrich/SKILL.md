---
name: enrich
description: "Enriches a task with tracker data, DoR/DoD artifacts, and design context. Use at task intake to prepare for planning. Can update Jira fields when --fields flag is present. Trigger terms: /enrich, enrich task, enrich ticket, populate DoR."
category: operative
disable-model-invocation: true
version: 1.3.0
---

# Enrich (Tracker-Backed Task Refinement) — v5.3

## 1. Identity

**Command Type:** Operative — Procedural / Execution

You are **analyzing, enriching, and refining** a task for autonomous development. This command reads tracker data for the provided task id via the resolved tracker provider, evaluates its completeness against a product and technical checklist, classifies the task shape for description formatting, generates missing content, writes the product analysis to the task directory, and publishes all artifacts to the knowledge provider. Additionally, it produces **Definition of Ready** (`dor.plan.md`) and **Definition of Done** (`dod.plan.md`) artifacts from a dedicated structuring phase. External writes to the tracker are opt-in via flags: `--brief` posts an enrichment brief as a Jira comment for team context during refinement; `--fields` writes structured fields (Description, AC, Test Steps) to the tracker.

The local artifact remains the complete canonical analysis; tracker fields receive a provider-adapted representation for collaboration.

**Skills referenced:** `rho-aias`, `technical-writing`, `incremental-decomposition`.

---

## 2. Invocation / Usage

Invocation:

- `/enrich <TASK_ID>`
- `/enrich <TASK_ID> --brief`
- `/enrich <TASK_ID> --fields`
- `/enrich <TASK_ID> --brief --fields`
- `/enrich <TASK_ID> --refresh`
- `/enrich <TASK_ID> --refresh --brief`
- `/enrich <TASK_ID> --refresh --brief --fields`
- `/enrich --brief` (when TASK_ID is provided via Structured Prompt)
- `/enrich --brief --fields`
- `/enrich --refresh`

Flags:

- `--brief` — Post an enrichment brief as a Jira comment for team context during refinement. Fires the Brief Comment Preview gate. Required for `refinement_validated: true`.
- `--fields` — Write structured fields (Description, AC, Test Steps) to the tracker. Fires the Tracker Write Preview gate.
- `--refresh` (v9.6+) — Re-derive DoR/DoD from the current tracker payload (description + custom fields + comments), diff against on-disk artifacts, and apply merged result under `Gate: Refresh Approval`. Fires `Sub-Gate: Amendment Reconciliation` per bullet when `technical.plan.md § Proposed Do{R,D} Amendments` are non-empty. Sets `last_refreshed_at: <UTC>` in `status.md` on successful apply.

Without flags, `/enrich` performs analysis, writes local artifacts, and publishes to the knowledge provider (Confluence). No writes to Jira.

**Rationale for `--refresh` (v9.6+):** During implementation, the tracker ticket frequently evolves (PM tightens the device matrix, QA adds an edge case in a comment, design publishes the missing flow). Without a refresh path, the dev has three bad options: (1) hand-edit the local DoR/DoD and lose audit, (2) re-run `/enrich` clean and lose any inline-confirmed amendments still in flight, (3) keep working against stale DoR/DoD and discover the drift at PR time. `--refresh` consolidates the merge through a single governance surface (Refresh Approval + Amendment Reconciliation) with `command_log` audit, preserving in-flight Proposed Amendments unless the user explicitly retires them.

Usage notes:

- `<TASK_ID>` is required (e.g., `MAX-12761`). When the task id maps to a tracker ticket, the resolved tracker provider is used for enrichment. It also sets TASK_DIR to <resolved_tasks_dir>/<TASK_ID>/. (Default: `~/.cursor/plans/`)
- The enriched output is always written to `analysis.product.md` in TASK_DIR.
- DoR/DoD artifacts (`dor.plan.md`, `dod.plan.md`) are written to TASK_DIR after the readiness check.
- `--brief` posts an enrichment brief as a Jira comment (after user confirmation via gate). Without `--brief`, no Jira comment is posted.
- `--fields` writes structured tracker fields (Description, AC, Test Steps). Without `--fields`, no tracker fields are modified.
- `--refresh` requires DoR/DoD to already exist locally; if missing it falls back to the canonical first-run flow (refresh is a no-op when there is nothing to merge against). It does NOT modify `refinement_validated` — that flag remains a historical indicator of `--brief` + publish success.
- The absence of `--brief`, `--fields`, or `--refresh` is not a gate bypass — it is a branch not activated. The gates only apply when the corresponding flag enables the external write or refresh path.
- `Enhanced by` headers exist only in the remote push representation (`--fields`). They do NOT appear in `analysis.product.md` or the local preview content.
- This command does NOT transition the tracker status. The `pending_dor → ready` transition is a manual team responsibility during refinement.
- This command works best after `@product` has provided product analysis (JTBD, 5 Whys, User Journey, MoSCoW), but it can also be used standalone.

**Phase ordering with combined flags:** When `--refresh` is combined with `--brief` and/or `--fields`, the canonical execution order is: Phase 1 → Phase 1b (Refresh) → Phase 2 → Phase 3 → Phase 3-DoR → Phase 3b (when `--fields`) → Phase 4. The refresh resolves drift before re-classification, so downstream Completeness Checklist and tracker writes operate on the merged DoR/DoD. If Phase 1b's `Gate: Refresh Approval` is `abort`, the command halts before Phase 2 (no downstream side effects).

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
- When `--refresh` is active (v9.6+), additional inputs:
  - `dor.plan.md` and `dod.plan.md` (current on-disk artifacts to diff against)
  - `technical.plan.md` (read `## Proposed DoR Amendments`, `## Proposed DoD Amendments`, and frontmatter `todos` for the Amendment Reconciliation sub-gate)
- Service configs:
  - `aias-config/providers/tracker-config.md`
  - `aias-config/providers/knowledge-config.md`

Rules:

- `<TASK_ID>` is mandatory. If not provided, ask for it before proceeding.
- All inputs must be explicit. Do not infer task ids or tracker ticket ids from vague references.
- If tracker or knowledge service config is missing, invalid, or unresolvable, STOP and request provider configuration.
- If resolved tracker provider cannot read the ticket, STOP and inform the user.
- For `--refresh`, if `dor.plan.md` or `dod.plan.md` is missing locally, emit an advisory `--refresh is a no-op when local DoR/DoD do not exist; falling back to canonical first-run flow` and continue as if `--refresh` were absent.

---

## 4. Output Contract (Format)

### File Output

| Artifact | Content | When |
|----------|---------|------|
| `analysis.product.md` | Gap summary, enhanced ticket content, product analysis | First-run + refresh (always rewritten) |
| `dor.plan.md` | Definition of Ready — scope, criteria, and constraints for the task | First-run (create); `--refresh` (modify, post-Refresh Approval) |
| `dod.plan.md` | Definition of Done — checklist of criteria for QA readiness | First-run (create); `--refresh` (modify, post-Refresh Approval) |
| `technical.plan.md` | Updated `## Proposed Do{R,D} Amendments` sections + frontmatter `todos` array when `Sub-Gate: Amendment Reconciliation` produces a `remove` or `tracker` outcome | Only with `--refresh` and only when reconciliation deletes TODOs |

### Local Artifact

Write `analysis.product.md` to TASK_DIR with the full enriched content (gap summary, enhanced ticket content, product analysis).

### Brief Comment Output (only with `--brief`, v9.4+ restructure)

When the `--brief` flag is present, an enrichment brief is posted as a Jira comment via `addCommentToJiraIssue`. The brief is a **collaborative refinement note** that proposes the agent's understanding of the ticket to the team. It is not an evaluation, a grade, or a checklist of deficiencies. The brief follows the `Collaborative Refinement Tone` pattern from `technical-writing/SKILL.md` § 7.

**Output title:** `## Refinement Notes — <TASK_ID>`

**Structure (in order):**

| Section | Content | Condition |
|---|---|---|
| Opening paragraph | 1–2 sentences in the agent's own words paraphrasing the team's apparent intent. MUST NOT address or name the ticket author. The reader is the whole team. | Always |
| `### What's solid` | Bullets the dimensions the ticket already covers well. Acknowledges signal; not flattery. | Always (when at least one dimension is solid; otherwise omit) |
| `### What we already infer / propose to add` | Bullets the dimensions the agent has filled in (User flow, UI Spec, API/Data, Dependencies, NFRs, Test criteria — only those applicable). Each bullet attributes its inference to a source ("from the parent epic", "from the linked design", "from the chat context", "from the architecture") and ends with "please confirm" or "to validate". | Always (when at least one dimension was inferred) |
| `### Open clarifications` | Bullets the items that need explicit human input. Phrased as questions. Replaces the evaluative `[Missing]` markers. | Only when there are unresolved items |
| `### Out of scope (declared)` | Bullets what is NOT included in this task. Each item labeled with source ("from the ticket", "we propose to exclude"). | Always |
| `### Acceptance Criteria (consolidated)` | Bullets the final AC list as proposed. Each item is a verifiable criterion per `technical-writing/SKILL.md` § 2. | Always |
| `### Next steps` | Bullets the actions needed next. MUST NOT assign roles or individuals. The developer reading the comment tags whoever they think can help. | Always |

**Content invariants:**

- **Language**: MUST be in English regardless of chat conversation language. The brief lands in a shared tracker that mixes languages; English is the canonical tracker convention.
- **Tone**: MUST follow `Collaborative Refinement Tone` pattern (paraphrase, not evaluate). FORBIDDEN to use evaluative language ("missing", "incomplete", "lacks", "fails to specify"); SHOULD use collaborative language ("we infer", "we propose", "to confirm", "open question").
- **Gap Summary stays local**: The completeness dimensions table from `analysis.product.md` is internal-only. The brief MUST NOT include it. Posting that table externally reads as a scoreboard of the ticket author's work, contradicting the collaborative posture.
- **Next steps without role assignment**: `### Next steps` MUST list items only. MUST NOT assign actions to Product, UX, QA, or any role. Examples: "validate the user flow we proposed", "confirm the out-of-scope items", "attach the design reference if available". The dev decides who to tag.
- **No greetings, no sign-offs**: FORBIDDEN to greet the author by name/role or sign the comment ("— AI", "— Rho AIAS"). The collaborator posture is implied by the structure; an explicit sign-off makes it sound like a memo from outside the team.
- **No filesystem leakage**: FORBIDDEN to include local filesystem paths, machine-specific references, or `Enhanced by` headers.

**Substitutions (mandatory):**

| Replace evaluative | With collaborative |
|---|---|
| "missing X" / "X is missing" | "to confirm: X" or "we did not see X in the ticket — open question" |
| "incomplete" / "lacks Y" | "we propose to add Y as we infer it from <source>" |
| "needs Z" / "Z required" | "we infer Z; please confirm" |
| "the ticket fails to specify" | "we did not find a definition of" |
| "this is unclear" | "open clarification" |
| `[Missing]` / `[Incomplete]` markers | `What we already infer / propose to add` or `Open clarifications` |

### Tracker Field Write (only with `--fields`)

Tracker field writes are executed only when the `--fields` flag is present.

When requested, write the following remote enrichment to the resolved tracker provider:
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

**Anti-bypass:** Inherits Gate Invocation Protocol. No additional rules.

### Gate: Brief Comment Preview (only with `--brief`)

**Type:** Confirmation
**Fires:** Only when `--brief` flag is present. After writing local artifacts and publishing to knowledge provider, before posting the brief comment.
**Skippable:** No.

**Context output:**
Present the full brief comment in chat for review.

**AskQuestion:**
- **Runtime compatibility:** If `AskQuestion` is unavailable, use the Text Gate Protocol from `readme-commands.md` with the same prompt, option ids, labels, and `allow_multiple` semantics.
- **Prompt:** "Post enrichment brief as comment on <TASK_ID>?"
- **Options:**
  - `post`: "Post brief comment to Jira"
  - `adjust`: "Adjust the brief before posting"
  - `skip`: "Skip brief comment"
- **allow_multiple:** false

**On response:**
- `post` → Post brief as comment via `addCommentToJiraIssue`
- `adjust` → User provides feedback; regenerate brief and re-fire gate
- `skip` → Skip brief comment; local artifacts are still written

**Anti-bypass:** Inherits Gate Invocation Protocol. No additional rules.

### Gate: Tracker Write Preview (only with `--fields`)

**Type:** Confirmation
**Fires:** Only when `--fields` flag is present, before writing structured fields to the resolved tracker provider.
**Skippable:** No.

**Context output:**
Present tracker write preview in chat:
- Task ID
- Fields to update (list with summary of content per field)
- `Enhanced by` block action per field (`create` / `update` / `skip`)
- Description subset summary
- Format per field (`markdown` / `adf`)

**AskQuestion:**
- **Runtime compatibility:** If `AskQuestion` is unavailable, use the Text Gate Protocol from `readme-commands.md` with the same prompt, option ids, labels, and `allow_multiple` semantics.
- **Prompt:** "Write enriched fields to <TASK_ID> via tracker provider?"
- **Options:**
  - `write`: "Write enriched fields to tracker"
  - `skip`: "Skip tracker write — keep local artifacts only"
- **allow_multiple:** false

**On response:**
- `write` → Write the remote enrichment payload to the resolved tracker provider (Phase 3b already resolved the field write plan)
- `skip` → Skip tracker write; local artifacts are still written

**Anti-bypass:** Inherits Gate Invocation Protocol. No additional rules.

### Gate: Refresh Approval (only with `--refresh`, v9.6+)

**Type:** Confirmation
**Fires:** Phase 1b, after the agent has re-derived DoR/DoD from the refreshed tracker payload and diffed them against the on-disk artifacts.
**Skippable:** No.

**Context output:**
Present the diff in chat with per-dimension/criterion classification:

```
REFRESH DIFF for <TASK_ID>:
  dor.plan.md:
    [add] <Dimension>: <new content snippet>
    [modify] <Dimension>: <old> → <new>
    [remove] <Dimension>: <content being removed> (reason: <tracker no longer carries this>)
    [unchanged] <Dimension>: <no change>
  dod.plan.md:
    [add] <Criterion>: <new content snippet>
    [modify] <Criterion>: <old> → <new>
    [remove] <Criterion>: <content being removed>
    [unchanged] <Criterion>: <no change>

  Drift source: <tracker description | custom field <X> | comment <author, date>>
  Net change: +N additions / M modifications / K removals
```

When the diff is empty (no drift detected), emit `[STATE: completed] no drift detected — DoR/DoD unchanged` and skip both this gate and the Amendment Reconciliation sub-gate.

**AskQuestion:**
- **Runtime compatibility:** If `AskQuestion` is unavailable, use the Text Gate Protocol from `readme-commands.md` with the same prompt, option ids, labels, and `allow_multiple` semantics.
- **Prompt:** "Refresh diff for <TASK_ID> — apply to local DoR/DoD?"
- **Options:**
  - `proceed`: "Apply merged DoR/DoD and continue"
  - `adjust`: "Show me a specific dimension/criterion to override before applying"
  - `abort`: "Abort refresh — keep local DoR/DoD unchanged"
- **allow_multiple:** false

**On response:**
- `proceed` → Apply merged DoR/DoD; fire **Sub-Gate: Amendment Reconciliation** (only when `## Proposed DoR Amendments` or `## Proposed DoD Amendments` is non-empty in `technical.plan.md`). After reconciliation, write artifacts to TASK_DIR, mark them as `modified` in `status.md`, set `last_refreshed_at: <UTC>`.
- `adjust` → User picks a specific dimension/criterion; agent shows the conflict in isolation and re-presents this gate.
- `abort` → Halt refresh. Emit `[STATE: blocked] refresh aborted by user — local DoR/DoD unchanged`. Do NOT modify `last_refreshed_at`. Do NOT proceed to Phase 2 if this was a pure `--refresh` invocation.

**Anti-bypass:** Inherits Gate Invocation Protocol. No additional rules.

### Sub-Gate: Amendment Reconciliation (only with `--refresh`, when Proposed sections are non-empty, v9.6+)

**Type:** Confirmation (iterated per bullet)
**Fires:** Inside Phase 1b, after `Gate: Refresh Approval` returns `proceed` AND `technical.plan.md` contains at least one non-empty `## Proposed DoR Amendments` or `## Proposed DoD Amendments` section.
**Skippable:** No.

**Matching algorithm (per bullet, exact-string):**

1. Iterate every bullet in `## Proposed DoR Amendments` and `## Proposed DoD Amendments`.
2. Extract the parent dimension/criterion from the bullet (e.g., `**Non-Functional**`).
3. Look up the same dimension/criterion in the refreshed DoR/DoD derivation (exact-string match on the dimension/criterion name, case sensitive).
4. Classify the bullet into one of three cases:
   - **Case A — confirm**: refreshed DoR/DoD now carries content semantically equivalent to the bullet's `**Proposed resolution**:` value or `**Inline confirmation**:` value (when present). Tracker now confirms what the bullet was proposing.
   - **Case B — contradict**: refreshed DoR/DoD now carries content that contradicts the bullet's proposed value (different acceptance criterion, different test scope, etc.).
   - **Case C — orthogonal**: the refreshed DoR/DoD does not mention this dimension/criterion at all (or mentions it but in an unrelated context). The proposed amendment is unaffected by the refresh.
5. Case C bullets are kept verbatim — no prompt fires. Only Case A and Case B fire the sub-gate prompt.

**Per-bullet context output (Case A — confirm):**

```
[Case A — tracker confirms] <Section>: <Dimension>
  Local bullet:    <full bullet content>
  Tracker says:    <refreshed value>
  Suggested:       apply now (remove TODO from frontmatter, remove bullet from body)
```

**AskQuestion (Case A):**
- **Prompt:** "Tracker now confirms <Dimension>. Apply now and remove TODO?"
- **Options:**
  - `apply`: "Apply now (remove TODO from frontmatter, remove bullet from body)"
  - `keep`: "Keep TODO (defer apply to /consolidate-plan)"
  - `skip`: "Skip this refresh dimension (keep both bullet and refreshed value pending — re-evaluate next refresh)"
- **allow_multiple:** false

**Per-bullet context output (Case B — contradict):**

```
[Case B — tracker contradicts] <Section>: <Dimension>
  Local bullet:    <full bullet content>
  Tracker says:    <contradicting value>
  Suggested:       tracker wins (the bullet was based on stale context)
```

**AskQuestion (Case B):**
- **Prompt:** "Tracker contradicts <Dimension>. Which value wins?"
- **Options:**
  - `tracker`: "Tracker wins (remove TODO from frontmatter, remove bullet from body, accept refreshed value)"
  - `bullet`: "Bullet wins (keep TODO, override the refreshed DoR/DoD at this dimension with the bullet's proposed value)"
  - `manual`: "Manual abort — open the artifact in the editor and resolve myself"
- **allow_multiple:** false

**On response:**

| Case | Choice | DoR/DoD outcome | TODO outcome (technical.plan.md frontmatter) | Bullet outcome (technical.plan.md body) |
|---|---|---|---|---|
| A | `apply` | Refreshed value applied | TODO **deleted** | Bullet removed |
| A | `keep` | Refreshed value applied | TODO retained (`status: pending`) | Bullet retained |
| A | `skip` | Refreshed value NOT applied at this dimension; on-disk dimension retains old value | TODO retained | Bullet retained |
| B | `tracker` | Refreshed value applied | TODO **deleted** | Bullet removed |
| B | `bullet` | Refreshed value NOT applied at this dimension; on-disk dimension keeps the bullet's `**Proposed resolution**:` (or `**Inline confirmation**:`) value | TODO retained | Bullet retained |
| B | `manual` | Refresh ABORTS for the entire artifact (DoR or DoD) at this point | No mutation | No mutation |

**Manual abort persistence (Case B `manual`):** When the user chooses `manual`, the entire refresh stops at this bullet. Already-applied dimensions earlier in the iteration are **rolled back** — no partial DoR/DoD mutation is committed. The on-disk state is identical to pre-Refresh-Approval. `last_refreshed_at` is NOT set. Emit `[STATE: blocked] manual reconciliation requested — refresh rolled back; resolve <dimension> in <artifact> manually, then re-run /enrich --refresh`. Audit: append `command_log` entry as normal (the invocation happened).

**Race condition note:** Between the original `/enrich` and this `--refresh`, another agent or human MAY have edited `technical.plan.md` body without going through `/consolidate-plan` (e.g., direct editor edit). The matching algorithm uses exact-string match on the dimension/criterion name from the bullet's `**<Dimension>**:` header — it does NOT attempt fuzzy/semantic matching. If a bullet's dimension name does not appear in the refreshed DoR/DoD, it is classified as Case C (orthogonal) by default. The user MAY re-run with manual edits if Case C classification is incorrect.

**Anti-bypass:** Inherits Gate Invocation Protocol. The iteration MUST visit every Case A and Case B bullet (Case C bullets are silent). Skipping bullets via `--fast` is FORBIDDEN — the user MUST individually decide each non-orthogonal bullet.

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

**Anti-bypass:** Inherits Gate Invocation Protocol. No additional rules.

### End-of-Response Confirmation

After all phases complete:
```
Saved artifacts to: <absolute_path>/
  - analysis.product.md
  - dor.plan.md
  - dod.plan.md
  [- technical.plan.md (modified by --refresh reconciliation)]
[Refresh: applied (N additions, M modifications, K removals) | skipped | aborted | not requested (no --refresh)]
[Amendment reconciliation: N confirms, M contradicts, K orthogonal | not applicable]
[last_refreshed_at: <UTC ISO8601> | unchanged]
[Knowledge provider: published | skipped | failed]
[Brief comment: posted | skipped | not requested (no --brief)]
[Tracker fields: updated (<list>) | skipped | not requested (no --fields)]
```

### Status Update (Phase 5)

After writing local artifacts:
1. Create TASK_DIR and `status.md` if they do not exist. Bootstrap all mandatory fields with initial values:
   - `profile`: inferred from context (default: `feature`; if enrichment-only: `enrichment`)
   - `classification: null`
   - `task_id`: from invocation context
   - `started`: today's date (UTC)
   - `status: pending_dor`
   - `tracker_status: null` (or from tracker if already available)
   - `completed_steps: []`
   - `current_step: refinement`
   - `refinement_validated: null`
   - `rhoaias_update: null`
   - `published: null`
   - `completed: null`
   - `artifacts: {}`
   - `command_log: []`
2. Add `analysis.product.md`, `dor.plan.md`, and `dod.plan.md` to `artifacts` map with status `created` or `modified`. When `--refresh` applied changes to DoR/DoD, mark them as `modified`. When Amendment Reconciliation mutated `technical.plan.md`, mark it as `modified` too.
3. Add `refinement` to `completed_steps`. Set `current_step` based on the profile: if `enrichment` → `closure`; otherwise → `blueprint`. **Do NOT advance `current_step` on a pure `--refresh` invocation** when `refinement` is already in `completed_steps` — `--refresh` is a maintenance operation, not a step progression.
4. Run Phase 5c: sync non-synced artifacts to resolved knowledge provider. Phase 5c fires only when a valid tracker ticket exists for TASK_ID (P1–P3 preconditions; see **rho-aias** skill § Phase 5c). If preconditions are not met, skip silently — artifacts remain in created/modified state for `/publish` to reconcile. After each successful publish, inject TOC per resolved provider config.
5. Set `refinement_validated` in `status.md`: `true` if `--brief` was used, brief comment was posted, AND knowledge publish succeeded (team has context for refinement); `false` otherwise. This evaluation happens **after** Phase 5c and after the brief comment (if `--brief`). `--refresh` does NOT modify this flag (it remains the historical indicator of `--brief` + publish success on the original refinement).
6. When `--refresh` Phase 1b applied changes (Refresh Approval = `proceed`), set `last_refreshed_at: <UTC ISO8601>` in `status.md` (obtain via `date -u +%Y-%m-%dT%H:%M:%SZ`). When Refresh Approval = `abort` or `skip`, do NOT modify `last_refreshed_at`.
7. Append to `command_log`: `{command: /enrich [--refresh] [--brief] [--fields], started_at: <UTC>, ended_at: <UTC>}` — obtain timestamps via `date -u +%Y-%m-%dT%H:%M:%SZ`. The `command` value MUST include the active flags so the command_log is a faithful audit of what was invoked. See `reference.md` § Command Log for full rules.

---

## 5. Content Rules (Semantics)

- Output must be in **English**.
- Apply the **technical-writing** skill patterns: Problem Framing, Acceptance Criteria, Risk Articulation, Conciseness, and — for any tracker-facing output produced under `--brief` — Collaborative Refinement Tone (v9.4+, see `technical-writing/SKILL.md` § 7).
- When generating file impact or acceptance criteria with increment granularity, apply the **incremental-decomposition** skill.
- Do **NOT** invent information that cannot be inferred from the ticket, chat context, or project architecture.
- When information is missing and cannot be inferred, mark it as **[Needs input]** with a targeted question.
- If `@product` analysis exists in the chat context (JTBD, User Journey, MoSCoW), incorporate it directly.
- For remote tracker writes, treat the tracker field payload as a derived representation of the local analysis, not as the canonical source.
- The local artifact and local preview MUST stay provider-agnostic and MUST NOT contain `Enhanced by` headers.
- Classification signals from tracker metadata MAY be used to shape `Description`, but `/enrich` MUST surface ambiguity or conflict through the Classification Comprehension gate instead of deciding silently.
- DoR Test criteria define **what** must be tested (scenarios, happy path, edge/corner cases, failure scenarios). They do NOT define **how** to implement the tests — that is the responsibility of `/blueprint` (Category 5: Testing).

### Brief comment invariants (v9.4+, when `--brief` is present)

- **Language**: The brief comment MUST be in English regardless of the chat conversation language. This is independent of the agent's chat language and is the canonical tracker convention for shared cross-team tickets.
- **Tone**: MUST follow `Collaborative Refinement Tone` (`technical-writing/SKILL.md` § 7). Evaluative language is FORBIDDEN; collaborative language is REQUIRED.
- **Gap Summary stays local**: The brief MUST NOT include the Gap Summary table from `analysis.product.md`. The table is internal-only.
- **Next Steps without role assignment**: `### Next steps` MUST list items only. MUST NOT assign actions to Product, UX, QA, or any role.
- **No greetings, no sign-offs**: The brief MUST NOT greet the ticket author by name/role or sign the comment.

### Canonical Section Titles (v9.4+)

Per `aias/contracts/readme-artifact.md` § Canonical Section Titles, artifact section headings MUST use canonical heading names without producer-side enumeration prefixes (`Category N:`, `Phase N —`, `Step N:`).

- `analysis.product.md`: section headings (e.g., `## Gap Summary`, `## Acceptance Criteria`) come from the `/enrich` output template verbatim; the agent MUST NOT prepend any internal-phase marker.
- `dor.plan.md`: each `## <Dimension>` heading follows the active DoR template (e.g., feature, bugfix, refactor, spike) verbatim; no `Phase N:` or `Step N:` prefixes.
- `dod.plan.md`: criterion checklist follows the active DoD template verbatim; no enumeration prefixes on the criteria.
- Brief comment posted to the tracker (`## Refinement Notes — <TASK_ID>`): the sub-section headings (`### What's solid`, `### What we already infer / propose to add`, `### Open clarifications`, `### Out of scope (declared)`, `### Acceptance Criteria (consolidated)`, `### Next steps`) are canonical verbatim.

---

## 6. Internal Execution Model

### Phase 1 — Read

1. Follow **rho-aias** skill loading protocol (Phases 0–3) to resolve TASK_DIR and load existing artifacts.
2. Resolve tracker provider from `aias-config/providers/tracker-config.md`; if missing/invalid/unresolvable, abort and request provider configuration.
3. Load `field_mapping_source` from the resolved tracker config (MANDATORY for write commands). If field mapping is missing or unresolvable, STOP with `MISSING_FIELD_MAPPING` and request configuration via `/aias configure-providers`.
4. **Exhaustive tracker read (v9.4+, v9.6+ refresh extension)**: Use the resolved provider to read the ticket with the broadest read pattern available — refinement/enrichment commands MUST NOT whitelist fields, otherwise custom fields outside the whitelist (RCA categorical fields, legacy enrichment fields, project-specific extensions, etc.) are silently dropped from the Completeness Checklist and the enrichment runs blind to half the ticket. For Atlassian MCP, call `getJiraIssue(cloudId, issueIdOrKey, fields=['*all'], expand='renderedFields,names,schema')`. **When `--refresh` is active (v9.6+)**, also include `comment` in the expand string so the comment thread is returned in the same call: `expand='renderedFields,names,schema,comment'`. The refresh diff (Phase 1b) reads tracker description + custom fields + the comment thread to detect drift since the original `/enrich` run. Unknown fields that surface in the response MUST be exposed in the Completeness Checklist using the schema-given label. This rule overrides any targeted-fields guidance from earlier versions for refinement workflows; write commands (`/enrich --fields`, `/report`) keep targeted writes — only reads become exhaustive.
   - **Tracker unreachable handling:** If the read call fails (network error, auth error, ticket archived/deleted), STOP with `[STATE: blocked]` and a diagnostic message. When `--refresh` triggered the call, the on-disk DoR/DoD remain unchanged — no partial merge is attempted.
   - **Provider portability:** This sub-clause documents Atlassian MCP (Jira) specifics. Other tracker providers (Linear, GitHub Issues, etc.) MUST be invoked through their canonical exhaustive read pattern as documented in their respective MCP/skill (see `aias/.skills/<provider>-mcp/SKILL.md` when present). The semantic invariant — read description + custom fields + comment thread in one call — is provider-agnostic; the syntactic shape of the call is not.
5. If `@product` analysis is present in the chat context, collect it as supplementary input.

### Phase 1b — Refresh from tracker (only with `--refresh`, v9.6+)

This phase runs only when `--refresh` is active AND `dor.plan.md` and `dod.plan.md` exist locally. Otherwise it is skipped silently. The phase enforces the **Refinement Artifact Mutation Invariant** (`aias/contracts/readme-artifact.md` v2.3 § Refinement Artifact Mutation Invariant) — `/enrich --refresh` is one of the two commands authorized to modify DoR/DoD.

**Step ordering (11 steps):**

1. Read on-disk `dor.plan.md` and `dod.plan.md` into memory.
2. Read on-disk `technical.plan.md` (frontmatter `todos` + body `## Proposed DoR Amendments` + body `## Proposed DoD Amendments`) into memory. If `technical.plan.md` does not exist, treat Proposed sections as empty and skip the Amendment Reconciliation sub-gate (it will not fire).
3. Re-derive a fresh DoR/DoD from the refreshed tracker payload (description + custom fields + comment thread already read in Phase 1 step 4 with `expand='renderedFields,names,schema,comment'`).
4. Compute the diff per dimension/criterion. Classify each as `add | modify | remove | unchanged`. For each `modify`, store both old and new values for the gate preview.
5. If the diff is empty (only `unchanged` entries), emit `[STATE: completed] no drift detected — DoR/DoD unchanged`, do NOT modify any artifact, do NOT modify `last_refreshed_at`, and return. **The phase ends here for no-drift cases.**
6. Fire **Gate: Refresh Approval** with the diff preview. If the user chooses `abort`, halt with `[STATE: blocked] refresh aborted by user — local DoR/DoD unchanged` and return without mutating any artifact. If the user chooses `adjust`, show the specific dimension/criterion and re-present the gate.
7. On `proceed`, if `technical.plan.md § Proposed Do{R,D} Amendments` are non-empty, fire **Sub-Gate: Amendment Reconciliation** per bullet (Case A and Case B only — Case C bullets are silent). Track per-bullet outcomes for steps 8–10.
8. **Manual abort handling (Case B `manual` in step 7):** Roll back any DoR/DoD mutation already staged in memory for this refresh; do NOT write any artifact; do NOT modify `last_refreshed_at`; emit `[STATE: blocked] manual reconciliation requested — refresh rolled back` and return.
9. Write merged `dor.plan.md` and `dod.plan.md` to TASK_DIR. When Amendment Reconciliation produced any `apply (Case A)` or `tracker (Case B)` outcome, also write the updated `technical.plan.md` (with the resolved bullets removed from the body and the corresponding TODOs deleted from frontmatter).
10. Mark `dor.plan.md` and `dod.plan.md` as `modified` in `status.md`; mark `technical.plan.md` as `modified` only when step 9 modified it.
11. Set `last_refreshed_at: <UTC ISO8601>` in `status.md`. Phase 1b ends; control returns to the main Phase ordering (Phase 2 follows when `--refresh` is combined with downstream flags; Phase 1b is the terminal phase for a pure `--refresh` invocation, which then jumps directly to Phase 5 status update + Phase 5c publish).

**Provider portability:** Phase 1b is documented above against Atlassian MCP semantics. Other tracker providers MUST be invoked through their canonical exhaustive read pattern (description + custom fields + comments in a single call when supported). The diff/merge logic is provider-agnostic.

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

### Phase 3b — Field Write Plan (only with `--fields`)

When the `--fields` flag is present, resolve the format for each target field before presenting the write preview:

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
3. Write `dor.plan.md` and `dod.plan.md` to TASK_DIR. (Pure `--refresh` invocations skip steps 1–3 here because Phase 1b already wrote the merged DoR/DoD; `analysis.product.md` is not re-derived in pure refresh.)
4. Run Phase 5 (status update + Phase 5c knowledge publish). After each successful publish, inject TOC per resolved provider config (see **rho-aias** skill § Phase 5c).
5. If `--brief`: generate brief comment from `analysis.product.md` (executive summary — see Brief Comment Output) → fire **Gate: Brief Comment Preview** → if confirmed, post brief as comment via `addCommentToJiraIssue` → update `refinement_validated` to `true` in `status.md`. (Skip on pure `--refresh` without `--brief`.)
6. If `--fields`: execute Phase 3b (Field Write Plan) → fire **Gate: Tracker Write Preview** → write the remote enrichment payload to the resolved tracker provider. (Skip on pure `--refresh` without `--fields`.)
7. End-of-Response Confirmation.

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

---

## 8. Self-Verification Checklist

- [ ] DoR/DoD and enrichment artifacts were written as expected in TASK_DIR.
- [ ] `status.md` and `command_log` updates were applied when state changed.
- [ ] Optional tracker writes were executed only when flag/gate path required them.
- [ ] Terminal state line was emitted with canonical state token.

## 9. Halt Discipline

- Pause only at declared gates/preconditions/blockers.
- Avoid ad-hoc confirmation pauses between normal enrichment steps.
- If blocked, report blocker and required input to resume.

## Terminal State Emission

`[STATE: completed | partial | blocked | failed]` + one-line summary is mandatory.

## Invocation Mode Detection

- Standalone default.
- Pipeline mode MAY be inferred from `--from-pipeline`, `--invoked-by`, or predecessor evidence in `status.md`.
- Detection MAY skip duplicate chain gates only when already resolved, without changing semantic output.
