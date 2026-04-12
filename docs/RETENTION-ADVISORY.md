# Artifact Retention Advisory

This document offers non-normative guidance on managing the accumulation of SDLC artifacts over time. It is **not a contract** — Rho AIAS does not impose retention periods, archival rules, or deletion policies. Every team and organization has its own regulatory, legal, and operational context that determines what to keep and for how long.

The goal here is to surface the right questions so adopters can make informed decisions.

---

## Why Think About Retention?

Over the lifecycle of a project, commands like `/enrich`, `/blueprint`, `/implement`, `/report`, and `/publish` generate artifacts that are stored locally (in `TASK_DIR`) and optionally synced to knowledge providers (e.g., Confluence). Without periodic review:

- Knowledge bases accumulate superseded plans, outdated DoR/DoD documents, and stale analysis that no longer reflects the current system.
- Search results in the knowledge provider become noisy, making it harder to find what is currently relevant.
- Storage costs grow, particularly for organizations with large project portfolios.

---

## Questions to Ask Yourself

Before defining any retention approach, consider these questions at the team or organization level:

### Operational Value

- **When does an artifact lose operational value?** A `technical.plan.md` is critical during implementation but rarely consulted after the feature ships. At what point does it become noise?
- **Which artifacts remain useful as historical reference?** RCA reports (`rca.report.md`) may have long-term value for pattern analysis. Architecture decisions may be permanent.
- **Does your team revisit old plans during retrospectives?** If not, those plans may not need to persist in your primary knowledge space.

### Regulatory and Compliance

- **Does your industry require evidence retention?** Sectors subject to SOX, HIPAA, GDPR, ISO 27001, or similar frameworks may have mandatory retention windows for certain artifact types.
- **Is your knowledge provider the system of record, or just a convenience mirror?** If Confluence is supplementary and your Git history is the source of truth, retention pressure on the knowledge provider is lower.

### Knowledge Base Hygiene

- **How do you distinguish current from historical content?** Labels, archive spaces, date-based hierarchies, or explicit status markers can help.
- **Who owns the decision to archive or remove?** Retention decisions typically involve product owners, tech leads, or compliance teams — not individual developers.

---

## Tiered Thinking (a Starting Point)

Without prescribing specific durations, it can be helpful to categorize artifacts by their expected lifespan:

| Tier | Nature | Examples | Consideration |
|------|--------|----------|---------------|
| **Long-lived** | Decisions and rationale that shape the system over time | Architecture Decision Records, design contracts, system-level RCA reports | Likely worth preserving for the life of the project or product |
| **Medium-lived** | Evidence and plans tied to specific delivery cycles | DoR/DoD documents, technical plans, increment plans, sprint-scoped analysis | Value diminishes as the feature stabilizes; review periodically |
| **Short-lived** | Operational artifacts consumed during execution | Draft notes, exploratory analysis, intermediate review findings | May lose relevance within days or weeks of creation |

The tiers above are illustrative. Your actual categories depend on your domain, team size, and compliance requirements.

---

## Practical Approaches

These are patterns observed in teams managing artifact-heavy workflows. None are mandated by the framework.

### Periodic Review

Schedule a recurring review (e.g., quarterly) where the team identifies artifacts in the knowledge provider that are no longer operationally relevant. Move them to an archive space or flag them as historical.

### Space Separation

Use dedicated knowledge provider spaces or hierarchies for active vs. historical content. For example, a `Project / Active` space for current work and a `Project / Archive` space for completed cycles.

### Git as Source of Truth

If your local `TASK_DIR` artifacts are committed to version control, the knowledge provider copy is a convenience mirror. In this model, the knowledge provider can be more aggressively pruned because the canonical history lives in Git.

### Artifact Metadata

Some teams annotate published artifacts with a "review-by" date or a lifecycle status. This makes it easier to identify candidates for archival during periodic reviews.

---

## What the Framework Does Not Do

- **Does not auto-archive or auto-delete** — The framework writes and syncs artifacts but never removes them.
- **Does not enforce retention periods** — No command checks artifact age or triggers archival workflows.
- **Does not decide what is obsolete** — That judgment belongs to product owners, tech leads, and compliance teams.

The framework's responsibility ends at producing and syncing artifacts. Everything after that is a team decision.

---

## Further Reading

- `WORKFLOWS.md` — End-to-end workflow descriptions including artifact production points
- `rho-aias/reference.md` § Resilience Model — How sync failures are handled (artifacts are never lost)
- `readme-knowledge-publishing-config.md` — How publishing to knowledge providers is configured
