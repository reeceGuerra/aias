# Agentic-Driven Development — Examples

`tracker_status` values shown in this file are illustrative provider labels. Actual runtime labels must be resolved from `status_mapping_source` for the active tracker provider.

> Paths in examples use `<resolved_tasks_dir>` which defaults to `~/.cursor/plans/`. See `reference.md` § Tasks Base Directory for configuration.

---

## rhoaias_update Lifecycle Reference

The `rhoaias_update` field in `status.md` is a scalar tracking whether `RHOAIAS.md` needs updating for this task. See `reference.md` for the governing spec.

### State transitions

| Value | Set when | Meaning |
|---|---|---|
| `null` | Initial state (set by `/enrich`) | No impact on `RHOAIAS.md` assessed yet |
| `required` | `/blueprint` detects RHOAIAS.md impact | RHOAIAS.md MUST be updated before PR |
| `deferred` | User acknowledges impact, continues | Update deferred — will be handled separately |
| `done` | RHOAIAS.md modified and present in diff at `/pr` | Update completed |
| `skipped` | User consciously skips at `/pr` gate | User accepted the omission |

### Snapshot examples per value

```yaml
# null — no RHOAIAS.md impact detected (initial / delivery / spike)
rhoaias_update: null
```

```yaml
# required — blueprint detected RHOAIAS.md impact; update pending
rhoaias_update: required
```

```yaml
# done — RHOAIAS.md was updated before the PR (most common for feature/bugfix)
rhoaias_update: done
```

```yaml
# skipped — user consciously chose not to update RHOAIAS.md at /pr gate
rhoaias_update: skipped
```

> **Note:** Snapshots in this file omit `rhoaias_update` when it has not changed from the canonical baseline (`null`). The field is shown when it transitions (e.g., at `/blueprint` and at closure).

---

## Feature Flow: Directory State Evolution

### After `/enrich MAX-12345 --brief`

```
<resolved_tasks_dir>/MAX-12345/
├── status.md
├── analysis.product.md
├── dor.plan.md
└── dod.plan.md
```

```yaml
# status.md
profile: feature
classification: null
task_id: MAX-12345
started: 2026-01-20
status: pending_dor
tracker_status: TO DO
completed_steps: [refinement]
current_step: blueprint
refinement_validated: true
rhoaias_update: null
published: null
completed: null
artifacts:
  analysis.product.md: synced
  dor.plan.md: synced
  dod.plan.md: synced
command_log:
  - command: /enrich
    started_at: 2026-01-20T14:30:00Z
    ended_at: 2026-01-20T14:35:47Z
```

### After `/blueprint`

> Note: the snapshots below show only fields that change from the canonical baseline. Fields such as `rhoaias_update` and `tracker_status` are omitted for brevity unless they change.

```
<resolved_tasks_dir>/MAX-12345/
├── status.md
├── analysis.product.md
├── dor.plan.md
├── dod.plan.md
├── technical.plan.md
├── increments.plan.md
└── specs.design.md
```

```yaml
# status.md
profile: feature
classification: standard
task_id: MAX-12345
started: 2026-01-20
status: in_progress
tracker_status: IN PROGRESS
completed_steps: [refinement, blueprint]
current_step: validate
refinement_validated: true
rhoaias_update: required
published: null
completed: null
artifacts:
  analysis.product.md: synced
  dor.plan.md: synced
  dod.plan.md: synced
  technical.plan.md: synced
  increments.plan.md: synced
  specs.design.md: synced
command_log:
  - command: /enrich
    started_at: 2026-01-20T14:30:00Z
    ended_at: 2026-01-20T14:35:47Z
  - command: /blueprint
    started_at: 2026-01-20T15:00:03Z
    ended_at: 2026-01-20T15:12:21Z
```

### Amendments TODO model (`/validate-plan` v2.1.0+ + `/consolidate-plan` v2.1.0+, v9.6+)

The example below shows how the unified TODO model routes amendments from `/blueprint` through `/validate-plan` (registration only) to `/consolidate-plan` (resolution). In v9.6+, inline user answers during `/blueprint` chat are captured as an `**Inline confirmation**:` sub-field — `/blueprint` no longer modifies `dor.plan.md` / `dod.plan.md` directly.

**`technical.plan.md` after `/blueprint` (Phase 1 staged three DoR gaps and one DoD gap; one bullet captures an inline-confirmed value):**

```markdown
---
name: User profile editor — technical plan
overview: Implements profile editing with photo upload.
todos: []
isProject: false
---

## Problem Framing
…

## Architecture and Approach
…

## File Structure and Visualization
…

## Proposed DoR Amendments
- **Test criteria**: login flow integration tests not enumerated.
  - **Proposed resolution**: extend the existing `LoginFlowTests` suite with profile-edit happy path
  - **Inline confirmation**: extend LoginFlowTests with profile-edit + cancel + retry cases (2026-01-20)
- **Non-Functional**: image upload size limit not specified.
  - **Proposed resolution**: 5MB cap with WEBP/JPEG-only validation (inferred from DS guidelines)
- **Technical constraints**: storage provider not declared.
  - **Proposed resolution**: reuse existing Firebase Storage bucket; please confirm

## Proposed DoD Amendments
- **Verification**: regression suite scope undefined.
  - **Proposed resolution**: extend `LoginFlowTests` suite with profile-edit cases
```

Notice that `dor.plan.md` and `dod.plan.md` on disk are **unchanged** after `/blueprint`, even though the Test criteria gap was resolved inline. The inline answer is captured in the `**Inline confirmation**:` sub-field; `/consolidate-plan` will apply it under the Update Approval gate.

**`technical.plan.md` frontmatter after `/validate-plan` (amendments registered as TODOs; `content` captures parent line only):**

```yaml
---
name: User profile editor — technical plan
overview: Implements profile editing with photo upload.
todos:
  - id: amendment-dor-test-criteria-login-flow
    content: "Test criteria: login flow integration tests not enumerated."
    status: pending
    kind: amendment_dor
    artifact: dor.plan.md
    dimension: Test criteria
  - id: amendment-dor-non-functional-upload-cap
    content: "Non-Functional: image upload size limit not specified."
    status: pending
    kind: amendment_dor
    artifact: dor.plan.md
    dimension: Non-Functional
  - id: amendment-dor-technical-storage-provider
    content: "Technical constraints: storage provider not declared."
    status: pending
    kind: amendment_dor
    artifact: dor.plan.md
    dimension: Technical constraints
  - id: amendment-dod-verification-regression-scope
    content: "Verification: regression suite scope undefined."
    status: pending
    kind: amendment_dod
    artifact: dod.plan.md
    dimension: Verification
  - id: validation-investigation-data-source
    content: "Investigation: backend endpoint not validated against API contract."
    status: pending
    kind: validation
    artifact: technical.plan.md
    dimension: Investigation
isProject: false
---
```

**After `/consolidate-plan` resolves all four amendment TODOs (and the one validation TODO):**

- For the `Test criteria` TODO, `/consolidate-plan` reads the bullet, detects the `**Inline confirmation**:` sub-field, and uses the inline value as the default in the Update Approval gate. The dev confirms (or overrides) and `dor.plan.md` is patched at the Test criteria dimension.
- For the remaining DoR TODOs (Non-Functional, Technical constraints), the Proposed resolution is the default; the dev decides per bullet.
- `dod.plan.md` is updated at Verification and marked `modified`.
- `technical.plan.md` body: the **entire** multi-line bullet (parent + sub-bullets) for each resolved amendment is removed from `## Proposed DoR Amendments` and `## Proposed DoD Amendments`. When a section becomes empty, the heading is removed too.
- Frontmatter: each resolved TODO has `status: completed`.
- Phase 5c publishes `dor.plan.md`, `dod.plan.md`, and `technical.plan.md` as normal `modified` artifacts (no `apply_local` exclusion).

**Legacy hard-fail example:** if a task in flight still carries `## Proposed DoR/DoD Amendments` (combined single block, v9.4 and earlier), `/validate-plan` v2.0.0+ aborts with `[STATE: blocked]` and the explicit manual-split instructions defined in `aias/.skills/validate-plan/SKILL.md § Phase: Process Proposed Amendments § Hard fail`. No auto-split is performed.

**Backward compatibility:**
- TODOs without a `kind` field are treated as `kind: validation` (matches v9.4 and earlier).
- v9.5 single-line Proposed bullets (no `**Inline confirmation**:` sub-field) continue to parse — `/validate-plan` v2.1.0 falls back to capturing the entire bullet line into `content`.

### `/enrich --refresh` (v9.6+) — drift detection from tracker comments

The user is mid-implementation when the PM updates the tracker ticket: tightens the device matrix in the description and adds a comment with new edge cases. The dev re-runs `/enrich --refresh` to pull those updates into the local DoR/DoD without losing in-flight Proposed Amendments.

**Phase 1b sequence (summary):**

1. Re-read tracker via the resolved provider (Atlassian MCP `getJiraIssue` with `expand: 'renderedFields,names,schema,comment'`).
2. Re-derive a fresh DoR/DoD from the updated tracker payload.
3. Diff the fresh derivation against the on-disk `dor.plan.md` / `dod.plan.md`.
4. Fire `Gate: Refresh Approval` showing per-dimension/criterion change preview (`add | modify | remove | unchanged`).
5. If `technical.plan.md` has non-empty `## Proposed Do{R,D} Amendments`, fire `Sub-Gate: Amendment Reconciliation` per bullet:
   - **Case A — confirm**: tracker now states what the bullet was proposing → `apply now (remove TODO) | keep TODO | skip refresh`.
   - **Case B — contradict**: tracker contradicts the bullet → `tracker wins (remove TODO) | bullet wins (keep TODO) | manual abort`.
   - **Case C — orthogonal**: no conflict → bullet kept verbatim, no prompt.
6. On `proceed`, write merged artifacts, mark DoR/DoD as `modified` in `status.md`, set `last_refreshed_at: <UTC>` in `status.md`, append `/enrich --refresh` to `command_log`.
7. Phase 5c publishes modified artifacts as normal.

**Status.md after refresh:**

```yaml
profile: feature
classification: standard
task_id: MAX-12345
last_refreshed_at: 2026-01-22T09:14:08Z
artifacts:
  dor.plan.md: modified
  dod.plan.md: modified
command_log:
  - command: /enrich
    started_at: 2026-01-20T14:30:00Z
    ended_at: 2026-01-20T14:35:47Z
  - command: /blueprint
    started_at: 2026-01-20T15:00:03Z
    ended_at: 2026-01-20T15:12:21Z
  - command: /enrich --refresh
    started_at: 2026-01-22T09:13:12Z
    ended_at: 2026-01-22T09:14:08Z
```

If `Case A apply now` or `Case B tracker` fires for any TODO, the TODO is **deleted** from `technical.plan.md` frontmatter (no `cancelled` state — the audit lives in `command_log` + git history + knowledge provider version history per `aias/contracts/readme-artifact.md` v2.3).

### After `/validate-plan` (passes)

```yaml
# status.md
profile: feature
classification: standard
task_id: MAX-12345
started: 2026-01-20
status: in_progress
tracker_status: IN PROGRESS
completed_steps: [refinement, blueprint, validate]
current_step: implement
refinement_validated: true
published: null
completed: null
artifacts:
  analysis.product.md: synced
  dor.plan.md: synced
  dod.plan.md: synced
  technical.plan.md: synced
  increments.plan.md: synced
  specs.design.md: synced
command_log:
  - command: /enrich
    started_at: 2026-01-20T14:30:00Z
    ended_at: 2026-01-20T14:35:47Z
  - command: /blueprint
    started_at: 2026-01-20T15:00:03Z
    ended_at: 2026-01-20T15:12:21Z
  - command: /validate-plan
    started_at: 2026-01-20T15:15:00Z
    ended_at: 2026-01-20T15:18:30Z
```

### After `/implement` (first increment)

```yaml
# status.md
profile: feature
classification: standard
task_id: MAX-12345
started: 2026-01-20
status: in_progress
tracker_status: IN PROGRESS
completed_steps: [refinement, blueprint, validate]
current_step: implement
refinement_validated: true
published: null
completed: null
artifacts:
  analysis.product.md: synced
  dor.plan.md: synced
  dod.plan.md: synced
  technical.plan.md: synced
  increments.plan.md: synced
  specs.design.md: synced
command_log:
  - command: /enrich
    started_at: 2026-01-20T14:30:00Z
    ended_at: 2026-01-20T14:35:47Z
  - command: /blueprint
    started_at: 2026-01-20T15:00:03Z
    ended_at: 2026-01-20T15:12:21Z
  - command: /validate-plan
    started_at: 2026-01-20T15:15:00Z
    ended_at: 2026-01-20T15:18:30Z
  - command: /implement
    started_at: 2026-01-20T16:00:00Z
    ended_at: 2026-01-20T16:45:33Z
```

### After `/commit` + `/pr`

```yaml
# status.md
profile: feature
classification: standard
task_id: MAX-12345
started: 2026-01-20
status: in_review
tracker_status: IN REVIEW
completed_steps: [refinement, blueprint, validate, implement, commit, pr]
current_step: closure
refinement_validated: true
published: null
completed: null
artifacts:
  analysis.product.md: synced
  dor.plan.md: synced
  dod.plan.md: synced
  technical.plan.md: synced
  increments.plan.md: synced
  specs.design.md: synced
command_log:
  - command: /enrich
    started_at: 2026-01-20T14:30:00Z
    ended_at: 2026-01-20T14:35:47Z
  - command: /blueprint
    started_at: 2026-01-20T15:00:03Z
    ended_at: 2026-01-20T15:12:21Z
  - command: /validate-plan
    started_at: 2026-01-20T15:15:00Z
    ended_at: 2026-01-20T15:18:30Z
  - command: /implement
    started_at: 2026-01-20T16:00:00Z
    ended_at: 2026-01-20T16:45:33Z
  - command: /commit
    started_at: 2026-01-20T16:46:00Z
    ended_at: 2026-01-20T16:47:12Z
  - command: /pr
    started_at: 2026-01-20T16:48:00Z
    ended_at: 2026-01-20T16:52:15Z
```

### After `/publish` (Standard closure)

```
<resolved_tasks_dir>/MAX-12345/
├── status.md
├── analysis.product.md
├── dor.plan.md
├── dod.plan.md
├── technical.plan.md
├── increments.plan.md
├── specs.design.md
└── delta.publish.md
```

```yaml
# status.md
profile: feature
classification: standard
task_id: MAX-12345
started: 2026-01-20
status: completed
tracker_status: IN REVIEW
completed_steps: [refinement, blueprint, validate, implement, commit, pr, closure]
current_step: null
refinement_validated: true
rhoaias_update: done
published: 2026-01-25
completed: 2026-01-25
artifacts:
  analysis.product.md: synced
  dor.plan.md: synced
  dod.plan.md: synced
  technical.plan.md: synced
  increments.plan.md: synced
  specs.design.md: synced
  delta.publish.md: synced
command_log:
  - command: /enrich
    started_at: 2026-01-20T14:30:00Z
    ended_at: 2026-01-20T14:35:47Z
  - command: /blueprint
    started_at: 2026-01-20T15:00:03Z
    ended_at: 2026-01-20T15:12:21Z
  - command: /validate-plan
    started_at: 2026-01-20T15:15:00Z
    ended_at: 2026-01-20T15:18:30Z
  - command: /implement
    started_at: 2026-01-20T16:00:00Z
    ended_at: 2026-01-20T16:45:33Z
  - command: /commit
    started_at: 2026-01-20T16:46:00Z
    ended_at: 2026-01-20T16:47:12Z
  - command: /pr
    started_at: 2026-01-20T16:48:00Z
    ended_at: 2026-01-20T16:52:15Z
  - command: /publish
    started_at: 2026-01-25T10:00:00Z
    ended_at: 2026-01-25T10:05:30Z
```

---

## Bugfix Flow: Directory State Evolution

### After `/issue MAX-67890` (Chat QA)

```
<resolved_tasks_dir>/MAX-67890/
├── status.md
└── report.issue.md
```

```yaml
# status.md
profile: bugfix
classification: null
task_id: MAX-67890
started: 2026-01-22
status: pending_dor
tracker_status: PENDING DOR
completed_steps: [investigate]
current_step: analyze
refinement_validated: null
rhoaias_update: null
published: null
completed: null
artifacts:
  report.issue.md: synced
command_log:
  - command: /issue
    started_at: 2026-02-10T09:00:00Z
    ended_at: 2026-02-10T09:08:45Z
```

### After `/fix` (Chat Debug)

```
<resolved_tasks_dir>/MAX-67890/
├── status.md
├── report.issue.md
└── analysis.fix.md
```

```yaml
# status.md
profile: bugfix
classification: null
task_id: MAX-67890
started: 2026-01-22
status: pending_dor
tracker_status: PENDING DOR
completed_steps: [investigate, analyze]
current_step: assess
refinement_validated: null
published: null
completed: null
artifacts:
  report.issue.md: synced
  analysis.fix.md: synced
command_log:
  - command: /issue
    started_at: 2026-02-10T09:00:00Z
    ended_at: 2026-02-10T09:08:45Z
  - command: /fix
    started_at: 2026-02-10T09:15:00Z
    ended_at: 2026-02-10T09:28:30Z
```

### After `/assessment` (Chat Dev)

```
<resolved_tasks_dir>/MAX-67890/
├── status.md
├── report.issue.md
├── analysis.fix.md
└── feasibility.assessment.md
```

```yaml
# status.md
profile: bugfix
classification: null
task_id: MAX-67890
started: 2026-01-22
status: pending_dor
tracker_status: PENDING DOR
completed_steps: [investigate, analyze, assess]
current_step: blueprint
refinement_validated: null
published: null
completed: null
artifacts:
  report.issue.md: synced
  analysis.fix.md: synced
  feasibility.assessment.md: synced
command_log:
  - command: /issue
    started_at: 2026-02-10T09:00:00Z
    ended_at: 2026-02-10T09:08:45Z
  - command: /fix
    started_at: 2026-02-10T09:15:00Z
    ended_at: 2026-02-10T09:28:30Z
  - command: /assessment
    started_at: 2026-02-10T09:30:00Z
    ended_at: 2026-02-10T09:38:15Z
```

### After `/blueprint` (Chat Planning — bug exception)

```
<resolved_tasks_dir>/MAX-67890/
├── status.md
├── report.issue.md
├── analysis.fix.md
├── feasibility.assessment.md
├── technical.plan.md
├── increments.plan.md
├── dor.plan.md
└── dod.plan.md
```

```yaml
# status.md
profile: bugfix
classification: minor
task_id: MAX-67890
started: 2026-01-22
status: in_progress
tracker_status: IN PROGRESS
completed_steps: [investigate, analyze, assess, blueprint]
current_step: validate
refinement_validated: null
rhoaias_update: null
published: null
completed: null
artifacts:
  report.issue.md: synced
  analysis.fix.md: synced
  feasibility.assessment.md: synced
  technical.plan.md: synced
  increments.plan.md: synced
  dor.plan.md: synced
  dod.plan.md: synced
command_log:
  - command: /issue
    started_at: 2026-02-10T09:00:00Z
    ended_at: 2026-02-10T09:08:45Z
  - command: /fix
    started_at: 2026-02-10T09:15:00Z
    ended_at: 2026-02-10T09:28:30Z
  - command: /assessment
    started_at: 2026-02-10T09:30:00Z
    ended_at: 2026-02-10T09:38:15Z
  - command: /blueprint
    started_at: 2026-02-10T10:00:00Z
    ended_at: 2026-02-10T10:14:20Z
```

### After `/publish` (Bugfix closure)

```
<resolved_tasks_dir>/MAX-67890/
├── status.md
├── report.issue.md
├── analysis.fix.md
├── feasibility.assessment.md
├── technical.plan.md
├── increments.plan.md
├── dor.plan.md
├── dod.plan.md
└── delta.publish.md
```

```yaml
# status.md
profile: bugfix
classification: minor
task_id: MAX-67890
started: 2026-01-22
status: completed
tracker_status: IN REVIEW
completed_steps: [investigate, analyze, assess, blueprint, validate, implement, commit, pr, report, closure]
current_step: null
refinement_validated: null
rhoaias_update: null
published: 2026-02-12
completed: 2026-02-12
artifacts:
  report.issue.md: synced
  analysis.fix.md: synced
  feasibility.assessment.md: synced
  technical.plan.md: synced
  increments.plan.md: synced
  dor.plan.md: synced
  dod.plan.md: synced
  delta.publish.md: synced
command_log:
  - command: /issue
    started_at: 2026-02-10T09:00:00Z
    ended_at: 2026-02-10T09:08:45Z
  - command: /fix
    started_at: 2026-02-10T09:15:00Z
    ended_at: 2026-02-10T09:28:30Z
  - command: /assessment
    started_at: 2026-02-10T09:30:00Z
    ended_at: 2026-02-10T09:38:15Z
  - command: /blueprint
    started_at: 2026-02-10T10:00:00Z
    ended_at: 2026-02-10T10:14:20Z
  - command: /validate-plan
    started_at: 2026-02-10T10:20:00Z
    ended_at: 2026-02-10T10:24:10Z
  - command: /implement
    started_at: 2026-02-10T10:30:00Z
    ended_at: 2026-02-10T11:22:48Z
  - command: /commit
    started_at: 2026-02-10T11:23:10Z
    ended_at: 2026-02-10T11:24:40Z
  - command: /pr
    started_at: 2026-02-10T11:25:00Z
    ended_at: 2026-02-10T11:30:11Z
  - command: /report
    started_at: 2026-02-10T11:32:00Z
    ended_at: 2026-02-10T11:35:54Z
  - command: /publish
    started_at: 2026-02-12T09:00:00Z
    ended_at: 2026-02-12T09:04:36Z
```

---

## Refactor Flow: Directory State Evolution

### After `/enrich MAX-11111 --brief`

```
<resolved_tasks_dir>/MAX-11111/
├── status.md
├── analysis.product.md
├── dor.plan.md
└── dod.plan.md
```

```yaml
# status.md
profile: refactor
classification: null
task_id: MAX-11111
started: 2026-01-23
status: pending_dor
tracker_status: TO DO
completed_steps: [refinement]
current_step: blueprint
refinement_validated: true
rhoaias_update: null
published: null
completed: null
artifacts:
  analysis.product.md: synced
  dor.plan.md: synced
  dod.plan.md: synced
command_log:
  - command: /enrich
    started_at: 2026-02-15T10:00:00Z
    ended_at: 2026-02-15T10:06:22Z
```

### After `/blueprint`

```
<resolved_tasks_dir>/MAX-11111/
├── status.md
├── analysis.product.md
├── dor.plan.md
├── dod.plan.md
├── technical.plan.md
└── increments.plan.md
```

```yaml
# status.md
profile: refactor
classification: minor
task_id: MAX-11111
started: 2026-01-23
status: in_progress
tracker_status: IN PROGRESS
completed_steps: [refinement, blueprint]
current_step: validate
refinement_validated: true
rhoaias_update: null
published: null
completed: null
artifacts:
  analysis.product.md: synced
  dor.plan.md: synced
  dod.plan.md: synced
  technical.plan.md: synced
  increments.plan.md: synced
command_log:
  - command: /enrich
    started_at: 2026-02-15T10:00:00Z
    ended_at: 2026-02-15T10:06:22Z
  - command: /blueprint
    started_at: 2026-02-15T10:30:00Z
    ended_at: 2026-02-15T10:41:50Z
```

### After `/publish` (Refactor closure)

```
<resolved_tasks_dir>/MAX-11111/
├── status.md
├── analysis.product.md
├── dor.plan.md
├── dod.plan.md
├── technical.plan.md
├── increments.plan.md
└── delta.publish.md
```

```yaml
# status.md
profile: refactor
classification: minor
task_id: MAX-11111
started: 2026-01-23
status: completed
tracker_status: IN REVIEW
completed_steps: [refinement, blueprint, validate, implement, commit, pr, closure]
current_step: null
refinement_validated: true
rhoaias_update: null
published: 2026-02-20
completed: 2026-02-20
artifacts:
  analysis.product.md: synced
  dor.plan.md: synced
  dod.plan.md: synced
  technical.plan.md: synced
  increments.plan.md: synced
  delta.publish.md: synced
command_log:
  - command: /enrich
    started_at: 2026-02-15T10:00:00Z
    ended_at: 2026-02-15T10:06:22Z
  - command: /blueprint
    started_at: 2026-02-15T10:30:00Z
    ended_at: 2026-02-15T10:41:50Z
  - command: /validate-plan
    started_at: 2026-02-15T10:45:00Z
    ended_at: 2026-02-15T10:49:33Z
  - command: /implement
    started_at: 2026-02-15T11:10:00Z
    ended_at: 2026-02-15T12:01:27Z
  - command: /commit
    started_at: 2026-02-15T12:03:00Z
    ended_at: 2026-02-15T12:04:18Z
  - command: /pr
    started_at: 2026-02-15T12:05:00Z
    ended_at: 2026-02-15T12:09:55Z
  - command: /publish
    started_at: 2026-02-20T08:40:00Z
    ended_at: 2026-02-20T08:44:12Z
```

---

## Enrichment Flow: Directory State Evolution

### After `/enrich MAX-22222 --brief`

```
<resolved_tasks_dir>/MAX-22222/
├── status.md
├── analysis.product.md
├── dor.plan.md
└── dod.plan.md
```

```yaml
# status.md
profile: enrichment
classification: null
task_id: MAX-22222
started: 2026-01-24
status: pending_dor
tracker_status: TO DO
completed_steps: [refinement]
current_step: closure
refinement_validated: true
rhoaias_update: null
published: null
completed: null
artifacts:
  analysis.product.md: synced
  dor.plan.md: synced
  dod.plan.md: synced
command_log:
  - command: /enrich
    started_at: 2026-03-01T11:00:00Z
    ended_at: 2026-03-01T11:07:18Z
```

### After `/publish` (Enrichment closure)

```
<resolved_tasks_dir>/MAX-22222/
├── status.md
├── analysis.product.md
├── dor.plan.md
├── dod.plan.md
└── delta.publish.md
```

```yaml
# status.md
profile: enrichment
classification: null
task_id: MAX-22222
started: 2026-01-24
status: completed
tracker_status: TO DO
completed_steps: [refinement, closure]
current_step: null
refinement_validated: true
published: 2026-03-01
completed: 2026-03-01
artifacts:
  analysis.product.md: synced
  dor.plan.md: synced
  dod.plan.md: synced
  delta.publish.md: synced
command_log:
  - command: /enrich
    started_at: 2026-03-01T11:00:00Z
    ended_at: 2026-03-01T11:07:18Z
  - command: /publish
    started_at: 2026-03-01T11:15:00Z
    ended_at: 2026-03-01T11:17:45Z
```

---

## Delivery Flow: Directory State Evolution

### After `/charter MAX-33333`

```
<resolved_tasks_dir>/MAX-33333/
├── status.md
└── delivery.charter.md
```

```yaml
# status.md
profile: delivery
classification: null
task_id: MAX-33333
started: 2026-01-25
status: pending_dor
tracker_status: PENDING DOR
completed_steps: [charter]
current_step: closure
refinement_validated: null
rhoaias_update: null
published: null
completed: null
artifacts:
  delivery.charter.md: synced
command_log:
  - command: /charter
    started_at: 2026-03-05T13:00:00Z
    ended_at: 2026-03-05T13:09:40Z
```

### After `/publish` (Standard closure)

```
<resolved_tasks_dir>/MAX-33333/
├── status.md
├── delivery.charter.md
└── delta.publish.md
```

```yaml
# status.md
profile: delivery
classification: null
task_id: MAX-33333
started: 2026-01-25
status: completed
tracker_status: PENDING DOR
completed_steps: [charter, closure]
current_step: null
refinement_validated: null
published: 2026-03-05
completed: 2026-03-05
artifacts:
  delivery.charter.md: synced
  delta.publish.md: synced
command_log:
  - command: /charter
    started_at: 2026-03-05T13:00:00Z
    ended_at: 2026-03-05T13:09:40Z
  - command: /publish
    started_at: 2026-03-05T13:30:00Z
    ended_at: 2026-03-05T13:35:12Z
```

---

## Artifact Sync Progression

Demonstrates how sync status evolves when offline:

### Step 1: `/enrich` completes, knowledge provider is reachable

```yaml
artifacts:
  analysis.product.md: synced     # published successfully
  dor.plan.md: synced             # published successfully
  dod.plan.md: synced             # published successfully
```

### Step 1b: `/blueprint` runs without tracker ticket (P1 fails)

Phase 5c is skipped because no tracker ticket exists for the task.

```yaml
task_id: null
artifacts:
  analysis.product.md: created
  dor.plan.md: created
  dod.plan.md: created
  technical.plan.md: created
  increments.plan.md: created
  specs.design.md: created
```

### Step 2: `/blueprint` completes, knowledge provider is unavailable

```yaml
artifacts:
  analysis.product.md: synced     # still synced from Step 1
  dor.plan.md: synced             # still synced from Step 1
  dod.plan.md: synced             # still synced from Step 1
  technical.plan.md: created      # written locally, sync failed
  increments.plan.md: created     # written locally, sync failed
  specs.design.md: created        # written locally, sync failed
```

### Step 3: `/validate-plan` completes, knowledge provider is reachable again

Phase 5c catches up — publishes all pending artifacts:

```yaml
artifacts:
  analysis.product.md: synced
  dor.plan.md: synced
  dod.plan.md: synced
  technical.plan.md: synced       # caught up
  increments.plan.md: synced      # caught up
  specs.design.md: synced         # caught up
```

### Step 4: User edits `technical.plan.md` and re-runs `/blueprint`

```yaml
artifacts:
  analysis.product.md: synced
  dor.plan.md: synced             # unchanged by /blueprint
  dod.plan.md: synced             # unchanged by /blueprint
  technical.plan.md: modified     # overwritten, needs re-sync
  increments.plan.md: modified    # overwritten
  specs.design.md: modified       # overwritten
```

Next command execution publishes all `modified` artifacts back to `synced`.

---

## Multi-Agent Dispatch Telemetry (`/self-review`, v9.4+)

When `/self-review` runs with `TASK_DIR` resolved and `status.md` present, the host MUST record dispatch telemetry as part of the `command_log` entry. The schema extends the base `command_log` entry with an OPTIONAL `dispatches: list[{subagent, started_at, ended_at}]` field (see `reference.md` § Command Log writing rule 7 and `aias/contracts/readme-multi-agent-review.md` § Dispatch Telemetry (host-owned)).

### `/self-review` after `/pr` (Standard plan, all 6 sub-agents)

```yaml
profile: feature
classification: standard
task_id: MAX-12345
status: in_review
tracker_status: IN REVIEW
completed_steps: [refinement, blueprint, validate, implement, commit, pr]
current_step: closure
refinement_validated: true
rhoaias_update: done
published: null
completed: null
artifacts:
  analysis.product.md: synced
  dor.plan.md: synced
  dod.plan.md: synced
  technical.plan.md: synced
  increments.plan.md: synced
  specs.design.md: synced
command_log:
  - command: /enrich
    started_at: 2026-05-16T14:30:12Z
    ended_at: 2026-05-16T14:35:47Z
  - command: /blueprint
    started_at: 2026-05-16T15:00:03Z
    ended_at: 2026-05-16T15:12:21Z
  - command: /validate-plan
    started_at: 2026-05-16T15:13:00Z
    ended_at: 2026-05-16T15:14:05Z
  - command: /implement
    started_at: 2026-05-16T15:20:00Z
    ended_at: 2026-05-16T16:10:00Z
  - command: /commit
    started_at: 2026-05-16T16:11:00Z
    ended_at: 2026-05-16T16:12:30Z
  - command: /pr
    started_at: 2026-05-16T16:13:00Z
    ended_at: 2026-05-16T16:15:42Z
  - command: /self-review
    started_at: 2026-05-16T16:30:12Z
    ended_at: 2026-05-16T16:42:51Z
    dispatches:
      - subagent: aias-correctness-reviewer
        started_at: 2026-05-16T16:31:02Z
        ended_at: 2026-05-16T16:38:27Z
      - subagent: aias-quality-reviewer
        started_at: 2026-05-16T16:31:02Z
        ended_at: 2026-05-16T16:37:18Z
      - subagent: aias-architecture-reviewer
        started_at: 2026-05-16T16:31:02Z
        ended_at: 2026-05-16T16:39:04Z
      - subagent: aias-test-auditor
        started_at: 2026-05-16T16:31:02Z
        ended_at: 2026-05-16T16:36:53Z
      - subagent: aias-security-auditor
        started_at: 2026-05-16T16:31:02Z
        ended_at: 2026-05-16T16:38:11Z
      - subagent: aias-reflector
        started_at: 2026-05-16T16:39:30Z
        ended_at: 2026-05-16T16:42:33Z
```

### Backward compatibility: legacy `/self-review` entry without `dispatches[]`

Pre-v9.4 entries (or hosts that operate without `TASK_DIR`) MAY omit `dispatches[]` entirely. The schema treats absence as an empty list — it does NOT imply failure to dispatch sub-agents:

```yaml
command_log:
  - command: /self-review
    started_at: 2026-04-10T10:15:03Z
    ended_at: 2026-04-10T10:28:12Z
    # no dispatches[] field — pre-v9.4 entry, treat as []
```

### `/peer-review` does NOT write telemetry

`/peer-review` reviews other developers' work and does not assume `TASK_DIR` exists for the reviewer's local workspace. It MUST NOT append a `command_log` entry. Telemetry of who reviewed which PR lives in the VCS provider (PR review history), not in the local reviewer's `status.md`.

---

## Conversation Cache Check Examples (Phase 0b)

Demonstrates how Phase 0b's conversation cache check applies in chained commands within the same agent session. The check is an optimization heuristic; correctness wins over cache when any MUST re-Read trigger fires.

### Cache-hit path: chained `/enrich → /blueprint`

Same agent session, no Write tool calls between commands except `status.md`, no user-indicated manual edits, no staleness gate firing on RHOAIAS.md.

```
Step 1 — /enrich (just executed)
  Read tool calls recorded in session:
    - RHOAIAS.md
    - base-rule.md
    - product.mdc (mode rule)
    - <TASK_DIR>/status.md
  Phase 5 — Write tool call against <TASK_DIR>/status.md
    (status update with completed_steps: [refinement])

Step 2 — /blueprint (next command in same chat)
  Phase 0b cache check:
    - RHOAIAS.md     → in context, no Write since,
                        no staleness gate fired → SKIP re-Read
    - base-rule.md   → in context, no Write since
                        → SKIP re-Read
    - planning.mdc   → not yet loaded (mode change product → planning)
                        → must Read
    - status.md      → /enrich's Phase 5 wrote status.md
                        → MUST re-Read (trigger iii)
  Result: /blueprint avoids redundant Read of RHOAIAS.md and
  base-rule; loads planning.mdc fresh; re-Reads status.md per
  trigger iii.
```

### Cache-miss path: status.md trigger fires

```
Step 1 — /enrich (just executed)
  Phase 5 — Write tool call against <TASK_DIR>/status.md
  (status update with completed_steps: [refinement])

Step 2 — /blueprint
  Phase 0b cache check on status.md:
    - Earlier session contains Write tool call against status.md
      → MUST re-Read (trigger iii — status.md is high-volatility)
  Result: status.md re-Read; updated state available to /blueprint
  before Phase 0 directory resolution proceeds.
```

### Cache-miss path: RHOAIAS.md staleness gate fires

```
Step 1 — /enrich (just executed)
  Read RHOAIAS.md; content shows last_refreshed_at = 2026-04-01.

Step 2 — /blueprint (10 days later, same chat hypothetically)
  Phase 0b cache check on RHOAIAS.md:
    - Already in context, no Write since
    - BUT freshness lifecycle (readme-project-context.md)
      defines staleness threshold; threshold has elapsed
      → MUST re-Read (trigger iv — freshness wins over cache)
  Result: RHOAIAS.md re-Read; staleness gate cleared per
  current state; /blueprint proceeds with fresh project context.
```

---

## Nested Context Discovery Example (Phase 0)

Scenario:
- Repository has root `RHOAIAS.md`
- `packages/mobile/RHOAIAS.md` exists with package-specific conventions
- Command runs from `packages/mobile/`

Expected behavior:
1. Walk-up finds nearest `packages/mobile/RHOAIAS.md`
2. Root `RHOAIAS.md` is also loaded as baseline
3. Overlapping sections use nested values; non-overlapping sections stay from root
4. `Rho AIAS Integration` remains root-defined

---

## Governance Examples by Classification

### Minor — No Governance Section

`increments.plan.md` for a simple bugfix (classification minor). No `## Governance` section is generated.

```markdown
## Increments

### Increment 1: Fix null check in LoginViewModel
**Goal:** Prevent crash when session token is nil during logout.
**Steps:**
1. Add guard for nil session in `logout()`.
2. Add unit test for nil session path.
**Improvement margin:** None.

### Increment 2: Update error handling
**Goal:** Surface the error to the user instead of silently failing.
**Steps:**
1. Replace `try?` with `do/catch` in `logout()`.
2. Present error alert via coordinator.
```

`/implement` behavior: Feedback gate after each increment (baseline). No custom gates, no approval gate.

### Standard — Custom Gates (optional)

`increments.plan.md` for a medium-impact feature (classification standard) where cross-module dependency warrants a custom gate.

```markdown
## Governance

| Increment | Gate Point | Gate Type | Gate Prompt | Options |
|-----------|-----------|-----------|-------------|---------|
| Increment 2: Integrate networking layer | after-completion | Confirmation | "Increment 2 modified the networking layer. Verify API contract with backend team before continuing." | confirm \| adjust |

## Increments

### Increment 1: Add data model
...
### Increment 2: Integrate networking layer
...
### Increment 3: Build UI components
...
```

`/implement` behavior: Feedback gate after Increment 1 (baseline). Custom "API Contract Verification" gate after Increment 2 (takes precedence over baseline Feedback). Feedback gate after Increment 3 (baseline).

### Critical — Mandatory Approval Gate

`increments.plan.md` for a critical architectural redesign (classification critical). A `## Governance` section MUST be present with at least one Approval gate.

```markdown
## Governance

| Increment | Gate Point | Gate Type | Gate Prompt | Options |
|-----------|-----------|-----------|-------------|---------|
| Increment 1: Restructure DI container | before-start | Approval | "This plan modifies the core DI container. Approve execution of 4 increments?" | approve \| reject |
| Increment 2: Migrate data layer | after-completion | Confirmation | "Data migration complete. Verify data integrity before UI migration." | confirm \| adjust |

## Increments

### Increment 1: Restructure DI container
...
### Increment 2: Migrate data layer
...
### Increment 3: Update UI bindings
...
### Increment 4: Remove deprecated adapters
...
```

`/implement` behavior: Ready gate (structural) → Architecture Approval gate (custom, takes precedence over Critical baseline Approval) → Increment 1. After Increment 2: Migration Checkpoint gate (custom). After Increments 1, 3, 4: Feedback gate (baseline).

---

## Spike Flow: Directory State Evolution

Example task: `MAX-SPIKE-001` — investigating authentication token refresh strategy.

### After `/enrich MAX-SPIKE-001`

```
<resolved_tasks_dir>/MAX-SPIKE-001/
├── status.md
├── analysis.product.md
└── dor.plan.md
```

```yaml
# status.md
profile: spike
classification: null
task_id: MAX-SPIKE-001
started: 2026-02-10
status: pending_dor
tracker_status: TO DO
completed_steps: [refinement]
current_step: investigate
refinement_validated: true
rhoaias_update: null
published: null
completed: null
artifacts:
  analysis.product.md: synced
  dor.plan.md: synced
command_log:
  - command: /enrich
    started_at: 2026-02-10T09:00:00Z
    ended_at: 2026-02-10T09:04:22Z
```

> `dod.plan.md` is not produced by spike `/enrich` — the lightweight spike DoR template omits it (no acceptance criteria in the traditional sense).

### After investigation + optional `/assessment`

```
<resolved_tasks_dir>/MAX-SPIKE-001/
├── status.md
├── analysis.product.md
├── dor.plan.md
└── feasibility.assessment.md
```

```yaml
# status.md (changed fields only from baseline above)
status: in_progress
completed_steps: [refinement, assess]
current_step: closure
```

### After `/publish` (Closure)

```
<resolved_tasks_dir>/MAX-SPIKE-001/
├── status.md
├── analysis.product.md
├── dor.plan.md
├── feasibility.assessment.md
└── delta.publish.md
```

```yaml
# status.md
profile: spike
classification: null
task_id: MAX-SPIKE-001
started: 2026-02-10
status: completed
tracker_status: TO DO
completed_steps: [refinement, assess, closure]
current_step: null
refinement_validated: true
rhoaias_update: null
published: 2026-02-10
completed: 2026-02-10
artifacts:
  analysis.product.md: synced
  dor.plan.md: synced
  feasibility.assessment.md: synced
  delta.publish.md: synced
command_log:
  - command: /enrich
    started_at: 2026-02-10T09:00:00Z
    ended_at: 2026-02-10T09:04:22Z
  - command: /assessment
    started_at: 2026-02-10T11:30:00Z
    ended_at: 2026-02-10T11:37:45Z
  - command: /publish
    started_at: 2026-02-10T14:00:00Z
    ended_at: 2026-02-10T14:04:18Z
```

> `rhoaias_update` stays `null` for spike closure — spike investigations typically do not modify `RHOAIAS.md`. If the spike results in a follow-up feature/bugfix task, `RHOAIAS.md` is updated as part of that task's flow.
