# Provider Config Contract — Cursor Configuration System (v2.1)

This document defines the canonical contract for provider configuration artifacts used by the service abstraction layer.

It exists to:
- Standardize provider resolution across commands, modes, and system skills.
- Prevent hardcoded external service assumptions in consumers.
- Enforce fail-fast behavior when service resolution is invalid.
- Make service behavior explicit, testable, and maintainable.

This document is written for maintainers of the Cursor configuration system.

---

## What is a Service Config?

A service config is a category-scoped configuration artifact that declares:

- Active provider (`active_provider`)
- Provider implementation binding (`skill_binding`)
- Provider-specific parameters (`providers.<provider_id>`)
- Failure behavior contract for unresolved configurations

### Characteristics

- Category-scoped: one file per service category.
- Provider-agnostic at consumer level: consumers resolve by category, not vendor name.
- Human-editable: Markdown with YAML examples.
- Deterministic: precedence and validation are unambiguous.
- Fail-fast: missing or invalid config aborts the dependent external operation.

### What a Service Config is NOT

A service config is not a mode, command, skill, or runtime artifact.

| Artifact | Defines |
|---|---|
| Mode | How to think |
| Command | How to execute/format |
| Skill | How to operate a concrete tool |
| Service config | Which provider/skill is selected per category |

---

## File Location and Naming

Service config files must live under:

- `aias-providers/knowledge-config.md`
- `aias-providers/tracker-config.md`
- `aias-providers/design-config.md`
- `aias-providers/vcs-config.md`

Future categories must follow:

- `aias-providers/<category>-config.md`

---

## Referenced Document Directory

Provider configs reference external documents (field mappings, status mappings, publishing configs) that contain project-specific configuration. These documents live in a provider-specific subdirectory:

- `aias-providers/<provider_id>/` — where `provider_id` matches the `active_provider` value (e.g., `atlassian`, `figma`, `github`)

Documents are referenced via path keys in the provider parameters (`field_mapping_source`, `status_mapping_source`, `config_source`) and declared as dependencies in `skill_binding.resource_files`.

Creation: via `/aias configure-providers` (AI-assisted discovery) or manual scaffolding via `aias new --provider`.

### Referenced Document Contracts

| Document type | Governing contract |
|---|---|
| Field mapping | `aias/contracts/readme-tracker-field-mapping.md` |
| Status mapping | `aias/contracts/readme-tracker-status-mapping.md` |
| Publishing config | `aias/contracts/readme-knowledge-publishing-config.md` |

---

## Canonical Categories and Baseline Providers

Only these categories are valid in this contract:

| Category | Purpose | Baseline provider template |
|---|---|---|
| `knowledge` | Publishing/wiki/archive | `confluence` via `atlassian-mcp` |
| `tracker` | Task/issue tracking | `jira` via `atlassian-mcp` |
| `design` | Design context | `figma` via `figma-mcp` |
| `vcs` | PR/repository metadata | `github` via `github-mcp` |

Baseline providers are template defaults only. They are not runtime fallbacks.

---

## Mandatory Section Order (Per File)

Each service config file must include these sections in this order:

1. `Purpose`
2. `Active provider`
3. `Skill binding`
4. `Provider parameters`
5. `Failure behavior`
6. `Example`

---

## Normative Schema

All service configs must conform to this schema model.

### Root Keys

| Key | Type | Required | Constraints |
|---|---|---|---|
| `service_category` | string | yes | enum: `knowledge|tracker|design|vcs` |
| `active_provider` | string | yes | pattern: `^[a-z][a-z0-9-]{1,62}$` |
| `provider_mode` | string | no | enum: `mcp|api|manual`; default `mcp` |
| `skill_binding` | object | yes | must include `skill`, `capability` |
| `providers` | object map | yes | keyset must include `active_provider` |

### `skill_binding` Keys

| Key | Type | Required | Constraints |
|---|---|---|---|
| `skill` | string | yes | pattern: `^[a-z0-9-]{2,64}$`; must be resolvable |
| `capability` | string | yes | pattern: `^[a-z][a-z0-9-]{1,64}$` |
| `resource_files` | string[] | conditional | Dependency manifest: declarative list of external files the skill needs for this category. Required for categories with `*_source` keys (`tracker`, `knowledge`). Not applicable for `design`, `vcs`. Each item pattern: `^[A-Za-z0-9._/-]+$`. Every `*_source` path must also appear in `resource_files`. |

### `providers.<provider_id>` Minimum Keys

| Key | Type | Required | Constraints |
|---|---|---|---|
| `enabled` | boolean | yes | active provider must be `true` |
| `mcp_server` | string | conditional | required when `provider_mode=mcp` |

Additional keys are category/provider-specific and allowed, but must not violate root invariants.

---

## Category-Specific Minimum Requirements

In addition to the normative schema, these keys are mandatory for baseline templates:

### `knowledge` (`confluence`)

Required provider keys:
- `config_source` (string path)

### `tracker` (`jira`)

Required provider keys:
- `field_mapping_source` (string path)
- `status_mapping_source` (string path)
- `status_mapping_source` must point to a file conforming to `aias/contracts/readme-tracker-status-mapping.md`

### `design` (`figma`)

Required provider keys:
- `url_patterns` (string array, minimum length 1)

### `vcs` (`github`)

Required provider keys:
- no extra required key beyond schema minimum (`enabled`, `mcp_server`)

---

## Executable-Ready Minimum Templates

These minimum templates are normative baselines and can be copied as starting points.

### `knowledge` minimum template

```yaml
service_category: knowledge
active_provider: confluence
provider_mode: mcp
skill_binding:
  skill: atlassian-mcp
  capability: knowledge-publish
  resource_files:
    - aias-providers/atlassian/confluence-config.md
providers:
  confluence:
    enabled: true
    mcp_server: user-Atlassian
    config_source: aias-providers/atlassian/confluence-config.md
```

### `tracker` minimum template

```yaml
service_category: tracker
active_provider: jira
provider_mode: mcp
skill_binding:
  skill: atlassian-mcp
  capability: tracker-sync
  resource_files:
    - aias-providers/atlassian/jira-field-mapping.md
    - aias-providers/atlassian/tracker-status-mapping.md
providers:
  jira:
    enabled: true
    mcp_server: user-Atlassian
    field_mapping_source: aias-providers/atlassian/jira-field-mapping.md
    status_mapping_source: aias-providers/atlassian/tracker-status-mapping.md
```

### `design` minimum template

```yaml
service_category: design
active_provider: figma
provider_mode: mcp
skill_binding:
  skill: figma-mcp
  capability: design-context
providers:
  figma:
    enabled: true
    mcp_server: user-Figma
    url_patterns:
      - figma.com/design/
```

### `vcs` minimum template

```yaml
service_category: vcs
active_provider: github
provider_mode: mcp
skill_binding:
  skill: github-mcp
  capability: pull-request-and-branch
providers:
  github:
    enabled: true
    mcp_server: user-GitHub
```

---

## Validation Rules (Mandatory)

A service config is valid only if all rules below pass:

1. `service_category` is one of canonical categories.
2. `active_provider` key exists inside `providers`.
3. `providers.<active_provider>.enabled == true`.
4. `skill_binding.skill` exists and is resolvable.
5. `provider_mode` is valid and consistent with provider fields.
6. `skill_binding.capability` is compatible with category intent.
7. Unknown extra keys are allowed only under `providers.<provider_id>`.
8. For `service_category=tracker`, `providers.<active_provider>.status_mapping_source` is required and resolvable.

### Skill Resolvability Rule

`skill_binding.skill` is resolvable when at least one location exists:

- `aias/.skills/<skill>/`
- `.cursor/skills/<skill>/`
- `~/.cursor/skills/<skill>/`

If unresolved, consumers must abort the dependent operation and request provider configuration correction.

### Tracker Field Mapping Rule

When `service_category=tracker`:

- `providers.<active_provider>.field_mapping_source` is mandatory for write commands (`/enrich`, `/report`).
- The referenced file must exist.
- The referenced file must follow `aias/contracts/readme-tracker-field-mapping.md`.
- The path must also appear in `skill_binding.resource_files`.

If any condition fails, consumers must abort dependent write operations with `MISSING_FIELD_MAPPING`.

### Knowledge Config Source Rule

When `service_category=knowledge`:

- `providers.<active_provider>.config_source` is mandatory.
- The referenced file must exist.
- The referenced file must follow `aias/contracts/readme-knowledge-publishing-config.md`.
- The path must also appear in `skill_binding.resource_files`.

If any condition fails, consumers must abort dependent publishing operations with `MISSING_CONFIG_SOURCE`.

### Resource Files Consistency Rule

When `skill_binding.resource_files` is declared:

- Every `*_source` key value in `providers.<active_provider>` must have its path listed in `resource_files`.
- Every path in `resource_files` must point to an existing file.
- Paths pointing to `aias/.skills/` are valid but legacy (deprecated in v7.5).

If any condition fails, consumers must report the inconsistency and request configuration correction.

### Tracker Status Mapping Rule

When `service_category=tracker`:

- `providers.<active_provider>.status_mapping_source` is mandatory.
- The referenced file must exist.
- The referenced file must follow `aias/contracts/readme-tracker-status-mapping.md`.
- `command_triggers` in the referenced mapping must use only `slash + kebab-case`.
- Legacy trigger keys (for example `snake_case`) are invalid.

If any condition fails, consumers must abort dependent tracker operations and request configuration correction.

---

## Capability Compatibility Matrix

The configured `skill_binding.capability` must be compatible with the service category.

| Category | Required capability set (minimum) |
|---|---|
| `knowledge` | `knowledge-publish` |
| `tracker` | `tracker-sync` |
| `design` | `design-context` |
| `vcs` | `pull-request-and-branch` |

If a custom provider uses different labels, the mapped capability must still satisfy the category intent above.

---

## Standard Failure Rules

When resolution fails, consumers must use these normalized outcomes:

| Error code | Trigger condition | Mandatory behavior |
|---|---|---|
| `MISSING_CONFIG` | `aias-providers/<category>-config.md` not found | Abort dependent operation and request config |
| `INVALID_SCHEMA` | Required keys/types/constraints fail | Abort dependent operation and request config fix |
| `UNRESOLVABLE_SKILL` | `skill_binding.skill` cannot be resolved | Abort dependent operation and request config fix |
| `UNSUPPORTED_CAPABILITY` | capability not compatible with category intent | Abort dependent operation and request capability mapping fix |
| `UNAVAILABLE_PROVIDER` | provider/API unavailable at runtime | Abort remote operation and report provider unavailability |
| `MISSING_FIELD_MAPPING` | `field_mapping_source` not found or non-conformant | Abort dependent write operation and request config fix |
| `MISSING_CONFIG_SOURCE` | `config_source` not found or non-conformant | Abort dependent publishing operation and request config fix |

Error messages should include: category, configured provider (if available), and reason code.

---

## Resolution and Precedence (Canonical Formulation)

Consumers must use this canonical algorithm:

```text
resolveServiceOrAbort(category):
  load aias-providers/<category>-config.md
  validate config (schema + category rules + resolvability)
  if valid:
    return explicit config selection
  abort dependent operation and request provider configuration
```

Canonical precedence rule:

- Valid explicit config is required.
- If explicit config is missing or invalid, abort.

No alternate precedence source is allowed.

---

## Consumer Responsibilities

### Commands and modes

Consumers with external services must:

- Declare required service configs as inputs/dependencies.
- Resolve providers by category.
- Abort dependent remote operations if config is missing, invalid, or unresolvable.
- Avoid provider-first operational logic in normal execution paths.

### Skills coordinating cross-service behavior

Cross-service skills (for example `rho-aias`) must:

- Resolve providers by category before service-dependent steps.
- Preserve protocol ordering and semantics.
- Apply fail-fast behavior consistently in service-dependent operations.

---

## Separation of Concerns

### Allowed in service configs

- Provider selection
- Skill binding
- Provider parameters
- Failure behavior declaration

### Forbidden in service configs

- Mode reasoning rules
- Command output templates
- Workflow/phase sequencing semantics
- Project task procedures

---

## Conformance Checklist (Pass/Fail)

Use this checklist to approve a service config implementation:

| Check | Pass/Fail |
|---|---|
| 1. File path follows `aias-providers/<category>-config.md` | ☐ |
| 2. Mandatory section order is respected | ☐ |
| 3. `service_category` enum is valid | ☐ |
| 4. `active_provider` exists in `providers` map | ☐ |
| 5. Active provider has `enabled: true` | ☐ |
| 6. `skill_binding.skill` is resolvable | ☐ |
| 7. `provider_mode` and provider fields are consistent | ☐ |
| 8. Failure behavior section is present and fail-fast compliant | ☐ |
| 9. Canonical precedence rule is present | ☐ |
| 10. Consumer docs reference category resolution + abort model | ☐ |

A config set is conformant only if all checks pass.

---

## Automation-Ready Audit Checks

These stable check IDs are reserved for future validators (BL-S03):

| Check ID | Rule |
|---|---|
| `SCHEMA_SECTION_ORDER` | Mandatory section order exists in file |
| `SCHEMA_ROOT_KEYS` | Required root keys exist and types match |
| `ACTIVE_PROVIDER_EXISTS` | `active_provider` key exists under `providers` |
| `ACTIVE_PROVIDER_ENABLED` | `providers.<active_provider>.enabled == true` |
| `SKILL_RESOLVABLE` | `skill_binding.skill` is resolvable |
| `CAPABILITY_COMPATIBLE` | capability matches category intent |
| `PRECEDENCE_CANONICAL` | canonical precedence rule is present verbatim |
| `CONSUMER_DOC_REFERENCES` | commands/skills reference category resolution model |
| `FAILFAST_CODES_DECLARED` | standardized failure table exists |
| `FIELD_MAPPING_RESOLVABLE` | `field_mapping_source` exists and conforms to `readme-tracker-field-mapping.md` |
| `CONFIG_SOURCE_RESOLVABLE` | `config_source` exists and conforms to `readme-knowledge-publishing-config.md` |
| `RESOURCE_FILES_RESOLVABLE` | all paths in `resource_files` exist and all `*_source` paths are listed |

---

## Common Anti-Patterns

### Hardcoded Operational Provider
```markdown
Always call Jira for tracker updates.
```
Problem: breaks category abstraction.

### Ambiguous Precedence
```markdown
Use config or defaults depending on context.
```
Problem: non-deterministic behavior.

### Silent Degradation
```markdown
If config is absent, continue with another provider.
```
Problem: violates fail-fast and hides configuration defects.

### Non-Resolvable Skill Binding
```yaml
skill_binding:
  skill: custom-skill-that-does-not-exist
```
Problem: invalid config must abort dependent service operations.

---

## Related Contracts

- `aias/contracts/readme-commands.md`
- `aias/contracts/readme-skill.md`
- `aias/contracts/readme-tracker-status-mapping.md`
- `aias/contracts/readme-tracker-field-mapping.md`
- `aias/contracts/readme-knowledge-publishing-config.md`
- `aias/contracts/readme-artifact.md`
- `aias/contracts/readme-mode-rule.md`
- `aias/contracts/readme-project-context.md`

---

This document is the source of truth for provider config structure and fail-fast provider resolution behavior.
