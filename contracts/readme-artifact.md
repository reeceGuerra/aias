# Artifact Contract — Cursor Configuration System (v2.3)

> **Keyword convention**: This contract uses RFC-2119 keywords (MUST, MUST NOT, SHOULD, MAY).
> See [readme-commands.md](readme-commands.md) § RFC-2119 Keyword Policy for definitions.

This document defines the **design contract** for task artifacts used in the rho-aias development architecture.

It exists to:
- Define what makes an artifact contract-compliant
- Establish naming conventions, directory rules, and TASK_ID format
- Provide quality criteria for reviewing artifact implementations
- Delegate runtime details (catalog, profiles, status lifecycle) to the `rho-aias` skill

This document is written **for maintainers** of the Cursor configuration system.

It is **not** a skill.
It is **not** executed by Cursor directly.
It is the reference against which artifact *implementations* are designed, reviewed, and corrected.

---

## Source of Truth

The **`rho-aias` skill** (`aias/.skills/rho-aias/`) is the single source of truth for all runtime artifact details:

| What | Where |
|------|-------|
| Closed artifact catalog (types, suffixes, producers) | `SKILL.md` — ARTIFACT CATALOG |
| Directory structure and discovery rules | `SKILL.md` — Discovery rules |
| Skill loading protocol (7 phases) | `SKILL.md` — LOADING PROTOCOL |
| Plan Classification (Minor/Standard/Critical) | `SKILL.md` — CORE RULES |
| Per-mode artifact requirements | `reference.md` — Per-Mode Artifact Requirements |
| Loading order | `reference.md` — Loading Order |
| Writing rules | `reference.md` — Writing Rules |
| Workflow profiles (steps, modes, chats) | `reference.md` — Workflow Profiles |
| Step definitions | `reference.md` — Step Definitions |
| `status.md` format and lifecycle | `reference.md` — status.md Format |
| Artifact sync states | `reference.md` — Artifact Sync Status |
| Structured Prompt fields | `reference.md` — Structured Prompt |
| Knowledge sync details | `reference.md` — Knowledge Sync Details |
| Directory state examples | `examples.md` |

This contract does **not** duplicate that content. When reviewing or creating artifacts, always consult the skill files for current values.

---

## What is an Artifact?

An **artifact** is a structured Markdown document that captures a specific aspect of a development task. Artifacts live in a centralized task directory and are produced and consumed by commands throughout the development lifecycle.

### Characteristics

- **Task-scoped** — Every artifact belongs to exactly one task directory
- **Type-constrained** — Only types in the closed catalog are allowed (see `SKILL.md`)
- **Suffix-discoverable** — Artifacts are found by globbing their suffix, not by hardcoding names
- **Sync-tracked** — Every artifact has a sync status relative to the resolved knowledge provider (`created` / `synced` / `modified`)

---

## Design Rules

### Naming Convention

All content artifacts follow the pattern:

```
<name>.<suffix>.md
```

- `<name>` — Descriptive label (e.g., `technical`, `analysis`, `report`, `delivery`, `instrumentation`, `delta`, `feasibility`)
- `<suffix>` — Type identifier used for glob discovery (e.g., `.plan`, `.product`, `.issue`, `.fix`, `.assessment`)
- `.md` — All artifacts are Markdown

`status.md` is the only exception — it has no suffix because it is a system file, not a content artifact.

### TASK_ID Format

- If a tracker ticket exists: use the ticket key exactly (e.g., `MAX-12345`)
- If no tracker ticket: use a descriptive kebab-case name (e.g., `refactor-auth-module`)

### Path Rules

- Base directory: resolved tasks directory (default: `~/.cursor/plans/`; configurable via `stack-profile.md` `binding.generation.tasks_dir` — see `aias/.skills/rho-aias/reference.md` § Tasks Base Directory)
- All artifacts for a task go in a single subdirectory: `<tasks_dir>/<TASK_ID>/`
- Old paths (`~/.cursor/issues/`, `~/.cursor/fixes/`, `~/.cursor/charters/`) are **deprecated**
- Never write artifacts outside TASK_DIR

### Cursor-First `.plan.md` Profile

Rho AIAS adopts a **Cursor-first** profile for `*.plan.md` artifacts. This is a framework-owned convention aligned with how Cursor appears to treat plan files, but it is **not** treated as a public Cursor API guarantee.

This profile applies to:

- `technical.plan.md`
- `increments.plan.md`
- `dor.plan.md`
- `dod.plan.md`
- any other artifact in the closed catalog whose suffix is `.plan.md`

#### Local artifact layers

For `*.plan.md`, the local artifact may contain two layers:

1. **Tooling metadata layer** — YAML frontmatter at the top of the file
2. **Document body layer** — Markdown content after the frontmatter

The tooling metadata layer is part of the local artifact used by the framework/runtime. The document body layer is the human-readable plan content.

#### Frontmatter fields

When a `*.plan.md` artifact uses the Cursor-first profile, the canonical frontmatter fields are:

- `name`
- `overview`
- `todos`
- `isProject`

The `todos` list is framework-owned. Cursor may render or ignore it depending on runtime context; Rho AIAS does not assume a public product contract beyond local compatibility.

#### Todo status enum

When `todos` is present in a `*.plan.md` artifact, each item status MUST use this closed enum:

- `pending`
- `completed`

Other values such as `done`, `finished`, `resolved`, or `in_progress` are not permitted in plan artifact frontmatter.

#### Todo ownership by artifact

Rho AIAS uses `todos` differently depending on the plan artifact:

- `increments.plan.md` — execution todos, produced by `/blueprint`, consumed and updated by `/implement`. Todos in `increments.plan.md` do NOT use a `kind` field.
- `technical.plan.md` — validation and amendment todos (v9.5+). Allowed `kind` values are `validation`, `amendment_dor`, and `amendment_dod` (closed enum; see `aias/.skills/rho-aias/reference.md § Todo kind enum`). Todos are produced by `/validate-plan` (registration only — `validation` from gap detection, `amendment_dor` and `amendment_dod` from the body sections `## Proposed DoR Amendments` and `## Proposed DoD Amendments`); consumed and resolved by `/consolidate-plan`. Backward compatibility: a todo without a `kind` field is treated as `validation`.
- Other `*.plan.md` artifacts — may use the Cursor-first profile for local compatibility, but MUST NOT invent new todo `kind` values unless explicitly defined by command and contract updates.

**Amendment routing invariant (v9.5+, technical.plan.md only):**

- `amendment_dor` todos MUST resolve only against `dor.plan.md`. Resolution by `/consolidate-plan` MUST remove the corresponding bullet from `## Proposed DoR Amendments` in `technical.plan.md` body.
- `amendment_dod` todos MUST resolve only against `dod.plan.md`. Resolution MUST remove the corresponding bullet from `## Proposed DoD Amendments`.
- Mixing DoR and DoD amendments inside a single Proposed section is FORBIDDEN.
- The legacy combined section `## Proposed DoR/DoD Amendments` is FORBIDDEN since v9.5. `/validate-plan` v2.0.0+ hard-fails on detection.

`/implement` MUST modify only `increments.plan.md` todos. Validation and amendment todos live in `technical.plan.md` and are outside `/implement` scope.

#### Structured Prompt naming

For contract, artifact, and schema documentation, the canonical names remain:

- `TASK_ID`
- `TASK_DIR`

For the human-written Structured Prompt, ergonomic aliases without underscores may be accepted:

- `TASK ID`
- `TASK DIR`
- `DIR` (alias for `TASK DIR`)

`TICKET` may remain as a legacy input alias, but it is not the canonical framework term.

### Catalog Rules

- The artifact catalog is **closed** — new artifact types MUST NOT be invented by agents or commands
- Adding a new artifact type requires updating `SKILL.md`, `reference.md`, `examples.md`, and this contract
- Every artifact type MUST have: a unique suffix, a single producer command, and a clear purpose

### Canonical Section Titles (transversal invariant, v2.3)

Producer skills (e.g., `/blueprint`, `/enrich`, `/charter`, `/issue`, `/fix`, `/trace`, `/assessment`, `/report`) may organize their internal data-collection phases under enumerated section headings (e.g., `### Category N: <Title>`, `### Phase N — <Step>`). The enumerated heading shape exists for the **author** of the artifact (the skill body, internal phase organization) — it MUST NOT bleed through into the produced artifact.

The artifact-file canonical heading is `## <Title>` without the `Category N:` / `Phase N:` / `Step N:` prefix. This invariant is transversal: it applies to all artifact-producing skills regardless of how many internal categories or phases they enumerate during data collection.

#### Canonical headings per artifact type

| Artifact | Canonical heading map |
|---|---|
| `technical.plan.md` | `## Problem Framing`, `## Architecture and Approach`, `## File Structure and Visualization`, `## Proposed DoR Amendments` (when present, v9.5+; DoR gaps, inline-confirmed or unresolved — see `§ Refinement Artifact Mutation Invariant`), `## Proposed DoD Amendments` (when present, v9.5+; DoD gaps, inline-confirmed or unresolved). The legacy combined section `## Proposed DoR/DoD Amendments` is FORBIDDEN since v9.5. The `## Resolution Log` heading is DEPRECATED since v9.6 (Path A removed); pre-existing logs in legacy artifacts MAY remain unchanged but MUST NOT be added or extended. |
| `increments.plan.md` | `## Governance` (optional, classification-driven), `## Increments` (with per-increment `### <Name>`), `## Self Code Review`, `## Testing` |
| `specs.design.md` | `## Design Specification` (with sub-sections for component hierarchy, visual states, interaction map, accessibility, design system mapping as needed) |
| `dor.plan.md` | One `## <Dimension>` per dimension per the active DoR template (e.g., `## Functional`, `## Non-Functional`, `## Technical constraints`, `## Test criteria`, `## Commitment`, `## Out of scope`) |
| `dod.plan.md` | Criterion checklist per the active DoD template (no enumerated prefixes) |
| `analysis.product.md` | Sections defined by `/enrich` Output Structure template — canonical headings only, no `Phase N:` prefixes |
| `report.issue.md` | Sections defined by `/issue` Output Structure template — canonical headings only |
| `analysis.fix.md` | Sections defined by `/fix` Output Structure template — canonical headings only |
| `feasibility.assessment.md` | Sections defined by `/assessment` Output Structure template — canonical headings only |
| `instrumentation.trace.md` | Sections defined by `/trace` Output Structure template — canonical headings only |
| `delivery.charter.md` | Sections defined by `/charter` Output Structure template (e.g., `## 1) Executive Summary`, `## 2) Plan Reference`, …) — the `N)` prefix IS canonical for charter; it is part of the charter's published heading shape, not an internal-phase enumeration |
| `delta.publish.md` | Sections defined by `/publish` Output Structure template — canonical headings only |

#### Producer invariants

- The skill body MAY use enumerated headings (`### Category N: <Title>`, `### Phase N — <Step>`) for its internal data-collection phase organization.
- The produced artifact MUST use the canonical heading without any internal-phase enumeration prefix.
- When a skill emits a producer-side section header in its template/output structure whose name differs from the artifact-side heading, the canonical artifact heading MUST be declared inline using the phrase: `**Canonical artifact heading:** \`## <Title>\``.
- Each producer skill MUST declare its Canonical artifact heading mapping explicitly in its `§ Content Rules (Semantics)` section.
- Emitting `## Category N: <Title>` or `## Phase N — <Step>` as a heading in any artifact file is FORBIDDEN.

Failing to honor this invariant causes internal scaffolding prefixes (e.g., `Category 7:`, `Phase 3 —`) to bleed through into the knowledge provider (e.g., Confluence) as `## Category 7: Risks` instead of the canonical `## File Structure and Visualization`, polluting published artifacts and breaking title canonicity (see `readme-knowledge-publishing-config.md` § Title Canonicity).

---

## Refinement Artifact Mutation Invariant (v2.3+)

`dor.plan.md` and `dod.plan.md` are **refinement artifacts** — they encode the negotiated scope (DoR) and acceptance contract (DoD) that all downstream commands consume as authoritative context. Their integrity depends on a tightly governed mutation surface.

### Authoritative create/modify matrix

| Operation | Allowed commands | Conditions |
|---|---|---|
| **CREATE** `dor.plan.md` / `dod.plan.md` | `/enrich` | Primary refinement path. Default for all non-bugfix profiles. |
| **CREATE** `dor.plan.md` / `dod.plan.md` | `/blueprint` | **Bug exception only.** Allowed iff `profile: bugfix` AND `feasibility.assessment.md` exists AND DoR/DoD do not yet exist (locally or via knowledge provider fallback). |
| **MODIFY** `dor.plan.md` / `dod.plan.md` | `/enrich --refresh` | Re-derives DoR/DoD from refreshed tracker payload, diffs against on-disk artifact, applies merged result under `Gate: Refresh Approval` (and `Sub-Gate: Amendment Reconciliation` when staged amendments exist). |
| **MODIFY** `dor.plan.md` / `dod.plan.md` | `/consolidate-plan` | Resolves `amendment_dor` / `amendment_dod` TODOs from `technical.plan.md` frontmatter, applying each via the Update Approval gate at the matched dimension/criterion. |
| **MODIFY** `dor.plan.md` / `dod.plan.md` | **No other command** | FORBIDDEN. This includes `/blueprint` even when the user resolves a DoR/DoD gap inline in chat — inline answers MUST be captured as `**Inline confirmation**:` sub-field markers inside `## Proposed Do{R,D} Amendments` bullets, not applied directly to the source artifact. |

### Inline confirmation marker

When `/blueprint` surfaces a DoR/DoD gap during Phase 1 and the user resolves it inline in the same chat, the resolved value MUST be captured as a sub-field marker inside the corresponding bullet in `## Proposed DoR Amendments` or `## Proposed DoD Amendments`:

```markdown
- **<Dimension>**: <gap description>.
  - **Proposed resolution**: <agent value or "needs <X> from <role>">
  - **Inline confirmation**: <user value> (YYYY-MM-DD)
```

**Format invariants:**

- Heading shape `**Inline confirmation**:` is exact-string normative (case sensitive, bold markdown delimiters, trailing colon).
- Value MUST be free-text user response captured verbatim.
- Date suffix MUST be `(YYYY-MM-DD)` UTC, parenthesized, separated from value by a single space.
- Canonical regex (for consumers like `/consolidate-plan` and `/validate-plan`): `^\s*-\s+\*\*Inline confirmation\*\*:\s+(?P<value>.+?)\s+\((?P<date>\d{4}-\d{2}-\d{2})\)\s*$`
- The sub-bullet MUST be indented exactly two spaces under its parent bullet to match `/validate-plan` v2.1.0+ and `/consolidate-plan` v2.1.0+ multi-line parsers.
- The marker is **ephemeral** — it lives only inside the Proposed bullet until `/consolidate-plan` resolves the TODO; on apply, the entire bullet (parent + sub-bullets) is removed from the Proposed section.

### Audit trail rationale (why Resolution Log was deprecated in v9.6)

The legacy `## Resolution Log` section was introduced in v9.5 as a one-line append-only audit of inline DoR/DoD modifications by `/blueprint`. It was removed in v9.6 because the audit surface fragmented in three places (`technical.plan.md § Resolution Log`, `status.md command_log`, knowledge-provider page history) without providing strictly stronger guarantees than the consolidated audit path:

- `status.md command_log` records every command invocation (start/end UTC, command name), which captures `/enrich --refresh` and `/consolidate-plan` events that mutate DoR/DoD.
- Git history on `~/.cursor/plans/<TASK_ID>/dor.plan.md` and `dod.plan.md` (when the task directory is under VCS) provides line-level provenance.
- Knowledge provider version history (Confluence page versions, Notion page history, etc.) provides remote-side provenance for published artifacts.

Routing all DoR/DoD mutations through `/enrich --refresh` and `/consolidate-plan` consolidates the mutation surface to two commands, both of which leave consistent traces in `command_log`. Pre-existing `## Resolution Log` sections in legacy artifacts (v9.5 era) MAY remain unchanged but MUST NOT be added or extended (`/blueprint` v5.4.0+ no longer emits them).

### Enforcement matrix

| Violation | Detected by | Action |
|---|---|---|
| `/blueprint` modifies existing `dor.plan.md` / `dod.plan.md` | Generator postflight test `TestRefinementArtifactImmutability` (see `aias/.canonical/generation/tests/test_unit.py`) | Generation gate fails, commit blocked |
| `/blueprint` emits new `## Resolution Log` heading | Same postflight test | Generation gate fails |
| `## Proposed Do{R,D} Amendments` bullet uses non-canonical inline confirmation phrasing | `/consolidate-plan` v2.1.0+ marker parser | Skip inline default, fall through to manual entry; emit advisory |
| Legacy combined `## Proposed DoR/DoD Amendments` heading | `/validate-plan` v2.0.0+ | Hard-fail with `[STATE: blocked]` and manual-split instructions |

---

## Quality Criteria

An artifact implementation is contract-compliant if:

1. File name matches the catalog in `SKILL.md` exactly
2. File lives inside `<resolved_tasks_dir>/<TASK_ID>/`
3. Suffix enables correct glob discovery
4. `status.md` is updated when the artifact is written (Phase 5)
5. Artifact sync status is tracked (`created` / `synced` / `modified`)
6. No artifact types exist outside the closed catalog
7. Content is written in English using **technical-writing** skill patterns

---

## References

- `aias/.skills/rho-aias/SKILL.md` — Artifact catalog, skill loading protocol, classification, core rules
- `aias/.skills/rho-aias/reference.md` — Per-mode requirements, profiles, step definitions, status.md format
- `aias/.skills/rho-aias/examples.md` — Directory states, status.md evolution examples
- `aias/contracts/readme-tracker-status-mapping.md` — Canonical tracker status mapping contract
