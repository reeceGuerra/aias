# Agentic-Driven Development — Examples

`tracker_status` values shown in this file are illustrative provider labels. Actual runtime labels must be resolved from `status_mapping_source` for the active tracker provider.

> Paths in examples use `<resolved_tasks_dir>` which defaults to `~/.cursor/plans/`. See `reference.md` § Tasks Base Directory for configuration.

## Feature Flow: Directory State Evolution

### After `/enrich MAX-12345`

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
status: ready
tracker_status: TO DO
completed_steps: [refinement]
current_step: blueprint
refinement_validated: true
published: null
completed: null
artifacts:
  analysis.product.md: synced
  dor.plan.md: synced
  dod.plan.md: synced
```

### After `/blueprint`

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
published: null
completed: null
artifacts:
  analysis.product.md: synced
  dor.plan.md: synced
  dod.plan.md: synced
  technical.plan.md: synced
  increments.plan.md: synced
  specs.design.md: synced
```

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
```

### After `/publish` (Standard closure)

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
published: null
completed: null
artifacts:
  report.issue.md: synced
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
published: null
completed: null
artifacts:
  report.issue.md: synced
  analysis.fix.md: synced
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
published: null
completed: null
artifacts:
  report.issue.md: synced
  analysis.fix.md: synced
  feasibility.assessment.md: synced
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
```

---

## Refactor Flow: Directory State Evolution

### After `/enrich MAX-11111`

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
status: ready
tracker_status: TO DO
completed_steps: [refinement]
current_step: blueprint
refinement_validated: true
published: null
completed: null
artifacts:
  analysis.product.md: synced
  dor.plan.md: synced
  dod.plan.md: synced
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
published: null
completed: null
artifacts:
  analysis.product.md: synced
  dor.plan.md: synced
  dod.plan.md: synced
  technical.plan.md: synced
  increments.plan.md: synced
```

---

## Enrichment Flow: Directory State Evolution

### After `/enrich MAX-22222`

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
status: ready
tracker_status: TO DO
completed_steps: [refinement]
current_step: closure
refinement_validated: true
published: null
completed: null
artifacts:
  analysis.product.md: synced
  dor.plan.md: synced
  dod.plan.md: synced
```

### After `/report` (Minor closure)

```yaml
# status.md
profile: enrichment
classification: minor
task_id: MAX-22222
started: 2026-01-24
status: completed
tracker_status: TO DO
completed_steps: [refinement, closure]
current_step: null
refinement_validated: true
published: null
completed: 2026-01-24
artifacts:
  analysis.product.md: synced
  dor.plan.md: synced
  dod.plan.md: synced
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
classification: standard
task_id: MAX-33333
started: 2026-01-25
status: pending_dor
tracker_status: PENDING DOR
completed_steps: [charter]
current_step: closure
published: null
completed: null
artifacts:
  delivery.charter.md: synced
```

### After `/publish` (Standard closure)

```yaml
# status.md
profile: delivery
classification: standard
task_id: MAX-33333
started: 2026-01-25
status: completed
tracker_status: PENDING DOR
completed_steps: [charter, closure]
current_step: null
published: 2026-01-25
completed: 2026-01-25
artifacts:
  delivery.charter.md: synced
  delta.publish.md: synced
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

### Custom Gate: API Contract Verification
- **Type:** Confirmation
- **Trigger:** after Increment 2
- **Prompt:** "Increment 2 modified the networking layer. Verify API contract with backend team before continuing."
- **Options:** confirm / adjust

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

### Custom Gate: Architecture Approval
- **Type:** Approval
- **Trigger:** before Increment 1
- **Prompt:** "This plan modifies the core DI container. Approve execution of 4 increments?"
- **Options:** approve / reject

### Custom Gate: Migration Checkpoint
- **Type:** Confirmation
- **Trigger:** after Increment 2
- **Prompt:** "Data migration complete. Verify data integrity before UI migration."
- **Options:** confirm / adjust

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
