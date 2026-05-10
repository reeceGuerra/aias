# Service Abstraction Pattern (Phase 3)

## Concept

Rho AIAS decouples external providers from command/mode behavior through a category-based service layer. Service-dependent consumers resolve integrations by category instead of hardcoded provider names:

- `knowledge` for publishing/archive targets
- `tracker` for ticket reads/comments/transitions
- `design` for design context retrieval
- `vcs` for repository and pull-request context

The current policy for commands and modes is fail-fast:

- Resolve provider config from `aias-config/providers/<category>-config.md`
- Validate config and skill binding
- If missing/invalid/unresolvable, abort the dependent operation and request configuration

For tracker transitions, the active provider must also expose a valid `status_mapping_source` so canonical states resolve to provider labels deterministically.

## Current coverage

### Config-driven and fail-fast (implemented)

| Surface | Category-driven resolution | Failure policy |
|---|---|---|
| `aias-config/providers/*.md` | yes | fail-fast contract sections |
| `aias/.skills/report/SKILL.md` | yes | abort on missing/invalid tracker config |
| `aias/.skills/publish/SKILL.md` | yes | abort on missing/invalid knowledge/tracker config |
| `aias/.skills/pr/SKILL.md` | yes | abort on missing/invalid vcs/tracker/knowledge config |
| `aias/.skills/commit/SKILL.md` | yes | abort on missing/invalid vcs/tracker config |
| `aias/.skills/enrich/SKILL.md` | yes | abort on missing/invalid tracker/knowledge config |
| `aias/.skills/validate-plan/SKILL.md` | yes | abort on missing/invalid tracker/knowledge config |
| `aias/.skills/implement/SKILL.md` | yes | abort on missing/invalid tracker/knowledge config |
| `aias/.skills/blueprint/SKILL.md` | yes | abort on missing/invalid tracker/design/knowledge config |
| `aias/.canonical/*.mdc` | yes | abort on missing/invalid config |
| `aias/.canonical/delivery.mdc` | yes | abort on missing/invalid tracker/design config |
| `aias/.canonical/devops.mdc` | yes | abort on missing/invalid vcs config |

### Alignment status

| Surface | Status |
|---|---|
| `aias/.skills/rho-aias/*` | aligned to fail-fast (`resolveServiceOrAbort`, `tracker_status`) |

## Config model

Service configs live in `aias-config/providers/`:

- `knowledge-config.md`
- `tracker-config.md`
- `design-config.md`
- `vcs-config.md`

Each config follows the same structure:

- `service_category`
- `active_provider`
- `skill_binding` (skill + capability + optional resource files)
- `providers.<provider_name>` parameters
- `Failure behavior` (fail-fast rules)
- For `tracker`: `status_mapping_source` for the active provider

Related tracker contracts:

- `aias/contracts/readme-tracker-status-mapping.md` — status transition mappings
- `aias/contracts/readme-tracker-field-mapping.md` — field mapping for write commands

Traceability chain (tracker transitions):

1. `aias/contracts/readme-provider-config.md`
2. `aias/contracts/readme-tracker-status-mapping.md`
3. `aias-config/providers/tracker-config.md` (`status_mapping_source`, `field_mapping_source`)
4. `aias-config/providers/<provider_id>/` — provider-specific mapping files referenced by `resource_files`

## Resolution flow (canonical)

All service-dependent consumers should follow:

```text
1) Read aias-config/providers/<category>-config.md
2) Validate category + active provider + skill binding + required provider parameters
3) If valid, execute with configured provider
4) If missing/invalid/unresolvable, abort dependent operation and request configuration
```

Pseudoflow:

```text
resolveServiceOrAbort(category):
  config = read(category-config)
  if config is valid:
    return config.active_provider, config.skill_binding, config.providers[active_provider]
  abort dependent operation and request provider configuration
```

## Provider switch example

### Jira -> Linear (tracker category)

Goal: switch tracker behavior without editing commands or modes.

1. Update `aias-config/providers/tracker-config.md`:
   - set `active_provider: linear`
   - set `skill_binding.skill` to the Linear integration skill
   - set `providers.linear.enabled: true`
   - set `providers.linear.status_mapping_source` to a valid mapping file
2. Keep command and mode files unchanged.
3. Run workflow:
   - tracker operations resolve through `linear` config
   - if Linear config is invalid or unresolvable, the dependent tracker operation aborts and asks for config correction

## Validation checklist

- [x] Category configs exist for `knowledge`, `tracker`, `design`, `vcs`.
- [x] Service-dependent commands resolve by category and abort on config failures.
- [x] Canonical and transversal modes in scope resolve by category and abort on config failures.
- [x] Contract `readme-provider-config.md` defines fail-fast resolution.
- [x] Tracker mapping contract exists (`readme-tracker-status-mapping.md`).
- [x] Tracker config requires `status_mapping_source` for active provider.
- [x] `rho-aias` skill docs aligned to fail-fast.
- [x] Provider switch remains representable through config-only changes.

## Migration status

- Phase 3 remediation status: completed
- Gate A: completed (service contract moved to fail-fast)
- Gate B: completed (transversal modes aligned)
- Gate C: completed (documentation aligned to actual state)
- Gate D: completed (`rho-aias` alignment)
- Gate E: completed (final auditable validation)
