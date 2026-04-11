> **DEPRECATED (v7.5)** — This file has moved to `aias-config/providers/atlassian/tracker-status-mapping.md`.
> This copy is kept for backward compatibility during migration.
> Run `/aias health` to detect and migrate automatically.
> This file will be removed in a future version.

# Tracker Status Mapping (Jira Provider)

## Purpose

Define the provider mapping from framework canonical tracker states to Jira workflow states.

This file is consumed through `status_mapping_source` in `aias-config/providers/tracker-config.md`.

## Provider

```yaml
provider: jira
provider_mode: mcp
```

## Canonical Status Catalog

Canonical framework states:

- `pending_dor`
- `ready`
- `in_progress`
- `in_review`
- `completed`
- `cancelled`

## Canonical -> Provider Mapping

```yaml
canonical_to_provider:
  pending_dor:
    state_name: PENDING DOR
    container_type: status
  ready:
    state_name: TO DO
    container_type: status
  in_progress:
    state_name: IN PROGRESS
    container_type: status
  in_review:
    state_name: IN REVIEW
    container_type: status
  completed:
    state_name: DONE
    container_type: status
    notes: Product responsibility; framework does not auto-transition
  cancelled:
    state_name: CANCELLED
    container_type: status
    notes: Manual-only; framework does not auto-transition
```

Optional reverse mapping:

```yaml
provider_to_canonical:
  PENDING DOR: pending_dor
  TO DO: ready
  IN PROGRESS: in_progress
  IN REVIEW: in_review
  DONE: completed
  CANCELLED: cancelled
```

## Command Triggers

```yaml
command_triggers:
  /enrich:
    from: pending_dor
    to: ready
  /blueprint:
    from: ready
    to: in_progress
  /blueprint (bug exception):
    from: pending_dor
    to: in_progress
  /pr:
    from: in_progress
    to: in_review
  /commit:
    verify: in_review
```

## Boundary Rules

1. Never auto-transition to `completed` (`DONE`) from framework commands.
2. Never auto-transition to `cancelled` (`CANCELLED`) from framework commands.
3. If ticket is already at target provider status, transition is idempotent (no-op).

## Resolution Rules

1. Read transitions dynamically from Jira (`getTransitionsForJiraIssue`).
2. Match target `state_name` from `canonical_to_provider`.
3. If target transition is not available, abort dependent tracker transition and report reason.
4. If mapping is missing or invalid, abort dependent tracker transition and request mapping/config correction.
5. If Jira is unavailable, abort dependent tracker transition and report provider unavailability.

## Example

```yaml
provider: jira
canonical_to_provider:
  pending_dor: { state_name: "PENDING DOR", container_type: "status" }
  ready: { state_name: "TO DO", container_type: "status" }
  in_progress: { state_name: "IN PROGRESS", container_type: "status" }
  in_review: { state_name: "IN REVIEW", container_type: "status" }
  completed: { state_name: "DONE", container_type: "status" }
  cancelled: { state_name: "CANCELLED", container_type: "status" }
command_triggers:
  /enrich: { from: pending_dor, to: ready }
  /blueprint: { from: ready, to: in_progress }
  /blueprint (bug exception): { from: pending_dor, to: in_progress }
  /pr: { from: in_progress, to: in_review }
  /commit: { verify: in_review }
```
