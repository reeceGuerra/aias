# Canonical — templates, transversal modes, and generation

This directory contains canonical templates, transversal (generic) modes, and the generation infrastructure used to produce platform-specific artifacts for focused workspaces.

## Transversal Modes

Generic modes that apply to any platform:

- [delivery.mdc](delivery.mdc): ticket readiness validation, prioritization, and release visibility. Activated with `@delivery`.
- [devops.mdc](devops.mdc): CI/CD pipeline management and infrastructure. Activated with `@devops`.

**Generated modes** (technology-specific roles and references) are produced by the generator and committed to `aias-config/modes/`.

Commands (`/blueprint`, `/issue`, `/fix`, etc.) live in **aias/.commands/** (framework) and **aias-config/commands/** (project custom) and are platform-agnostic.

## Mode Templates (Phase 2)

7 canonical mode templates that are instantiated per platform using stack profile bindings:

| Template | Purpose |
|---|---|
| `planning.mdc` | Planning mode behavior |
| `dev.mdc` | Developer mode behavior |
| `qa.mdc` | QA mode behavior |
| `debug.mdc` | Debug mode behavior |
| `review.mdc` | Code review mode behavior |
| `product.mdc` | Product analysis mode behavior |
| `integration.mdc` | Integration mode behavior |

Generated outputs are committed to `aias-config/modes/`.

## Canonical Rules (Phase 4)

2 canonical rule sources that define the structure of focused workspace rule files:

| Source | Purpose | Governing contract |
|---|---|---|
| `base-rule.md` | Structure for `base.mdc` files | `aias/contracts/readme-base-rule.md` |
| `output-contract.md` | Structure for `output-contract.mdc` files | `aias/contracts/readme-output-contract.md` |

Canonical rules use placeholders (`{{...}}`) resolved from stack profile bindings (`binding.rule.base.*` and `binding.rule.output_contract.*`).

## Generation

- Mode + rule generation: `aias/.canonical/generation/` (generator script + docs)
- Rule generation: Manual propagation following the Rule Maintenance Workflow in `docs/WORKFLOWS.md`

## Related

- `aias/contracts/readme-stack-profile.md` — Stack profile contract (bindings source)
- `aias/.canonical/generation/validation/` — Validation matrices for generated artifacts
- [readme-mode-rule.md](../contracts/readme-mode-rule.md) (contract for mode rules)
- `docs/WORKFLOWS.md` — Rule Maintenance Workflow section
