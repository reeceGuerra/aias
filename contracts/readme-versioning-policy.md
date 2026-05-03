# Contract Versioning Policy — Rho AIAS Configuration System (v1.2)

> **Keyword convention**: This contract uses RFC-2119 keywords (MUST, MUST NOT, SHOULD, MAY).
> See [readme-commands.md](readme-commands.md) § RFC-2119 Keyword Policy for definitions.

This document defines the canonical policy for versioning, deprecation, and backward compatibility of contracts in the Rho AIAS configuration system.

It exists to:
- Establish a uniform versioning scheme across all contracts
- Define when and how contract versions MUST be bumped
- Provide deprecation rules with minimum coexistence periods
- Enable adopters and contributors to assess breaking changes

This document is written **for maintainers** of the Rho AIAS configuration system.

---

## Versioning Scheme

All contracts use a **Major.Minor** scheme:

| Level | When to bump | Examples |
|---|---|---|
| **Major** (v1 -> v2) | Breaking change: removes or renames a mandatory section, changes semantics of an existing requirement, removes a mandatory binding key, alters the normative schema | Removing a mandatory section, renaming `resource_files` to `dependencies` |
| **Minor** (v1.0 -> v1.1) | Additive or clarifying change: new optional section, new optional binding key, editorial rewording that does not alter normative meaning, adding examples | Adding a new optional field, clarifying an ambiguous rule |

Patch versions (v1.0.1) are NOT used. Editorial fixes that do not change normative meaning (typos, formatting) do not require a version bump.

---

## Version Placement

Every contract MUST declare its version in the H1 heading:

```
# <Contract Name> — <System Name> (v<Major>.<Minor>)
```

When a contract has no prior version history, it SHOULD be initialized at **v1.0**.

---

## Current Contract Versions

| Contract | Current Version |
|---|---|
| `readme-artifact.md` | v2.0 |
| `readme-base-rule.md` | v1.0 |
| `readme-commands.md` | v6.0 |
| `readme-knowledge-publishing-config.md` | v1.0 |
| `readme-mode-rule.md` | v1.0 |
| `readme-output-contract.md` | v1.0 |
| `readme-project-context.md` | v1.0 |
| `readme-provider-config.md` | v2.1 |
| `readme-skill.md` | v1.1 |
| `readme-stack-profile.md` | v1.2 |
| `readme-tool-adapter.md` | v1.0 |
| `readme-tracker-field-mapping.md` | v1.0 |
| `readme-tracker-status-mapping.md` | v1.0 |
| `readme-versioning-policy.md` | v1.2 |

---

## Deprecation Policy

When a contract element (section, key, field, behavior) is deprecated:

1. **Mark in contract**: Add a `**deprecated**` annotation with the version that introduced the deprecation and the replacement (if any).
2. **CHANGELOG entry**: Record the deprecation in `aias/CHANGELOG.md` under the framework version that ships the change.
3. **Minimum coexistence**: The deprecated element MUST remain functional for at least **one major framework version** after the deprecation notice. Example: if deprecated in v8.x, removal is allowed starting in v9.0.
4. **Removal**: When removing a deprecated element, bump the contract's major version and document the removal in the CHANGELOG.

### Deprecation Notice Format

```markdown
- `<element>` — **deprecated** (v<contract_version>). Use `<replacement>` instead. Scheduled for removal in framework v<N>.0.
```

---

## Backward Compatibility Rules

1. **Additive changes are safe**: New optional sections, new optional keys, and new examples do not break existing consumers.
2. **Normative changes require major bump**: Changing the meaning of MUST/SHOULD/MAY for an existing requirement is a breaking change.
3. **Removal requires deprecation first**: No mandatory element MAY be removed without a prior deprecation period.
4. **Rename = remove + add**: Renaming a mandatory key or section is treated as removal of the old and addition of the new — requires major version bump and deprecation of the old name.

---

## When to Bump

| Scenario | Action |
|---|---|
| Fix a typo in descriptive text | No bump |
| Reword a normative rule without changing meaning | No bump |
| Add a new optional section | Minor bump |
| Add a new optional binding key | Minor bump |
| Add examples or clarifying notes | Minor bump |
| Change a SHOULD to a MUST | Major bump |
| Remove a mandatory section | Major bump (+ prior deprecation) |
| Rename a mandatory key | Major bump (+ prior deprecation of old key) |
| Add RFC-2119 preamble | No bump (editorial) |

---

## Relationship with Framework Versions

Contract versions are independent of framework versions (`v8.0`, `v9.0`, etc.). A framework version release MAY include changes to zero or more contracts. The CHANGELOG records both:
- Framework-level milestones (in the Release History table)
- Contract-level changes (mentioned within the relevant framework version entry)

### Phase-Major Closures (Recommended Pattern, v1.1+)

Historically, framework major bumps have coincided with the closure of major architectural phases that introduce a **new architectural layer**:

| Phase milestone | Framework version | Architectural shift |
|---|---|---|
| Artifact Directory Architecture | v5.0 | Centralized task artifacts under `~/.cursor/plans/<TASK_ID>/` |
| Phase 1 — Rebranding (`cursorconfig` → `aias`) | v6.0 | Identity consolidation, naming canonicalization |
| Phase 6 — Packaging + Documentation | v7.0 | Distribution-ready framework |
| SDLC Refinement Restructure | v8.0 | DoR/DoD ownership realignment, classification refresh |

When a phase introduces a new architectural layer, the closure of that phase **SHOULD** coincide with a framework major bump. Examples of "new architectural layer":

- New runtime observation/enforcement surface (e.g., hooks introduce a layer that did not exist before)
- New execution context that tensions an existing invariant (e.g., cloud / non-interactive agents vs. the "agente fresco" invariant)
- New host-platform integration that adopters cannot opt out of without losing core capability

Conversely, when a phase consists **only** of additive contracts, skills, behavioral refinements, or documentation updates (none of which alter philosophy, structure, or artifact relationships), the phase **MAY** close as a series of minor bumps without a major bump.

**Hybrid releases are allowed and preferred** when a phase mixes both types: additive items ship as minor bumps as soon as ready, while items introducing the new layer accumulate into the next major bump. This preserves incremental adopter value without diluting the semantic weight of the major version.

Phase 8 (Cursor Platform Integration) is the first phase to follow this pattern explicitly: 26 items close as v8.x minor bumps; the 3 Major candidates (Hooks contract `BL-S34`, Cloud Agent doctrine `BL-S40`, Model-routing contract `BL-S50b`) accumulate into **v9.0 — Cursor Platform Integration · Runtime Governance Layer** when ready as a cohort.

### Execution Order Principles (v1.2+)

When a phase contains many pending items with overlapping dependencies (Phase 8 with 35 items as the canonical example), publishing the full inventory without a global execution order forces every reader to reconstruct the critical path mentally. To prevent this drift and govern how phase milestones close, **active phases SHOULD declare a global Execution Order grouped into waves**.

A **wave** is a set of items sharing comparable dependency depth and blast radius. Waves close monotonically: items in Wave N MUST NOT depend on items in Wave M where M > N (no backward dependency). Items within the same wave MAY ship in any order or in parallel.

Three principles govern wave assignment:

1. **Wave 0 SHOULD be strictly non-breaking.** Items that ship documentation, no-bump skill extensions, or trivial-LOC fixes belong here. Wave 0 closing produces zero regression risk. This is the wave that establishes credibility and warmup velocity for the rest of the phase.
2. **Each subsequent wave MAY introduce greater blast radius, but MUST NOT introduce less governance than the previous wave.** "Less governance" means: weaker acceptance criteria, ad-hoc dependencies, or unscoped impact sweeps. A wave that admits less-rigorous items than the wave before it is a contract violation; the offending item MUST be moved or its scope tightened before the wave is published.
3. **The wave assignment lives in a single place** (typically `BACKLOG.md` § Execution Order at phase level), never duplicated across per-item entries. When an item's wave changes, only the Execution Order section is edited; per-item entries continue to declare priority, blocked-by, and coordination — never wave (per-item wave fields would create drift).

#### Recommended Wave taxonomy

The following 10-wave taxonomy is offered as a baseline; phases MAY collapse, expand, or rename waves provided the principles above hold:

| Wave | Typical contents |
|---|---|
| Wave 0 — Pre-flight | Documentation reconciliation, no-bump skill extensions, trivial fixes |
| Wave 1 — Quick wins | Minor additive contract bumps with no spike dependency |
| Wave 2 — Spikes / investigations | Items resolving architectural questions that gate later waves |
| Wave 3 — Independent contracts post-spike | Contracts that did not need a spike, can land in parallel |
| Wave 4 — Spike-gated contracts | Contracts that depend on a Wave 2 spike resolving GO |
| Wave 5 — Dependency-sequenced | Items that unlock when their explicit prerequisites close |
| Wave 6 — Documentation / ergonomy | Pure-doc items that benefit from earlier waves landing first |
| Wave 7 — Major cohort | Items that introduce a new architectural layer (per § Phase-Major Closures) and accumulate into the next major bump |
| Wave 8 — External-gate-blocked | Items blocked by corporate / partner / regulatory gates |
| Wave 9 — Parked / environment-dependent | Items tracked for traceability but not on the critical path |

Phase 8 (Cursor Platform Integration) is the first phase to follow this pattern explicitly; see `BACKLOG.md` § Active Phase 8 § Execution Order for the canonical Phase 8 wave assignment.

When a wave fully closes (all items `done` or `cancelled`), the wave SHOULD be struck through in the Execution Order section (preserving auditability) rather than removed.

---

## Quality Criteria

A properly versioned contract:

1. Has a version number in the H1 heading
2. Bumps version on every normative change
3. Uses deprecation notices before removing elements
4. Is reflected in the Current Contract Versions table above
5. Has its version changes recorded in `aias/CHANGELOG.md`

---

## Related Contracts

- `readme-commands.md` — RFC-2119 Keyword Policy (canonical definition)
- `aias/CONTRIBUTING.md` — PR guidelines referencing contract versions

---

This document is the **source of truth** for contract versioning and deprecation policy.
