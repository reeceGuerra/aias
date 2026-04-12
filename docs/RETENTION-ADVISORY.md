# Artifact Retention Advisory

This document offers non-normative guidance on managing the accumulation of published artifacts in knowledge providers (Confluence, Notion, etc.). It is **not a contract** — Rho AIAS does not impose retention periods, archival rules, or deletion policies. Every team and organization has its own regulatory, legal, and operational context that determines what to keep and for how long.

**Scope:** This advisory concerns only content synchronized to knowledge providers via Phase 5c. Local artifacts in `TASK_DIR` are outside scope — they are cheap, ephemeral, and managed by the developer at their discretion.

---

## Why Think About Knowledge Provider Retention?

Phase 5c publishes artifacts unconditionally after every command execution. Over the lifecycle of a project, published content accumulates: superseded plans, outdated DoR/DoD checklists, stale analysis, intermediate review artifacts. Without periodic review:

- **Search degrades.** Knowledge provider search results become noisy with outdated content, making it harder for team members to find what is currently relevant.
- **Onboarding suffers.** New team members navigating the knowledge base encounter historical artifacts without clear signals about which content reflects the current system state.
- **Storage costs grow.** Organizations with large project portfolios accumulate significant published volume, particularly when multiple SDLC cycles run in parallel.

---

## Questions to Ask Yourself

Before defining any retention approach, consider these questions at the team or organization level:

### Operational Value

- **When does a published artifact lose operational value?** A `technical.plan.md` page is critical during implementation but rarely consulted after the feature ships. At what point does it become noise in your knowledge base?
- **Which published artifacts remain useful as historical reference?** RCA reports (`analysis.fix.md`) MAY have long-term value for pattern analysis. Architecture decision rationale MAY be permanent.
- **Does your team revisit published plans during retrospectives?** If not, those pages MAY not need to persist in your primary knowledge space.

### Regulatory and Compliance

- **Does your industry require evidence retention?** Sectors subject to SOX, HIPAA, GDPR, ISO 27001, or similar frameworks MAY have mandatory retention windows for certain artifact types as published documentation.
- **Is your knowledge provider the system of record, or a convenience mirror?** If the knowledge provider is supplementary and your Git history is the authoritative source, retention pressure on published content is lower.

### Knowledge Base Hygiene

- **How do you distinguish current from historical published content?** Labels, archive spaces, date-based hierarchies, or explicit status markers can help.
- **Who owns the decision to archive or remove published pages?** Retention decisions typically involve product owners, tech leads, or compliance teams — not individual developers.

---

## Tiered Thinking (a Starting Point)

Without prescribing specific durations, it can be helpful to categorize published artifacts by their expected lifespan in the knowledge provider:

| Tier | Nature | Published artifact examples | Consideration |
|------|--------|----------------------------|---------------|
| **Long-lived** | Decisions and rationale that shape the system over time | RCA reports (`analysis.fix.md`), delivery charters with architectural scope, Plan Deltas documenting significant design decisions | Likely worth preserving in the knowledge provider for the life of the project or product |
| **Medium-lived** | Evidence and plans tied to specific delivery cycles | DoR/DoD checklists (`dor.plan.md`, `dod.plan.md`), technical plans, increment plans, product analysis | Value diminishes as the feature stabilizes; review periodically for archival |
| **Short-lived** | Operational artifacts consumed during a single task | Intermediate `specs.design.md` versions, `instrumentation.trace.md` for resolved issues, `feasibility.assessment.md` for shipped fixes | MAY lose relevance within weeks of task closure; candidates for early archival |

The tiers above are illustrative. Your actual categories depend on your domain, team size, and compliance requirements.

---

## Practical Approaches

These are patterns observed in teams managing published artifact accumulation. None are mandated by the framework.

### Periodic Review

Schedule a recurring review (e.g., quarterly) where the team identifies published pages in the knowledge provider that are no longer operationally relevant. Move them to an archive space or flag them as historical.

### Space Separation

Use dedicated knowledge provider spaces or hierarchies for active vs. historical content. For example, a `Project / Active` space for current work and a `Project / Archive` space for completed task hierarchies.

### Post-Closure Archival

After `/publish` closes a task and produces the Plan Delta, the entire task hierarchy in the knowledge provider becomes a candidate for archival. Teams MAY define a cooldown period (e.g., 30 days after closure) before moving the task pages to an archive space.

### Artifact Metadata

Some teams annotate published pages with a "review-by" date or a lifecycle status at the knowledge provider level. This makes it easier to identify candidates for archival during periodic reviews.

---

## What the Framework Does Not Do

- **Does not auto-archive or auto-delete published content** — The framework publishes and updates pages but never removes them from the knowledge provider.
- **Does not enforce retention periods** — No command checks published page age or triggers archival workflows.
- **Does not decide what is obsolete** — That judgment belongs to product owners, tech leads, and compliance teams.

The framework's responsibility ends at publishing and synchronizing artifacts to the knowledge provider. Everything after that — archival, deletion, space management — is a team decision.

---

## Further Reading

- `WORKFLOWS.md` — End-to-end workflow descriptions including artifact publication points
- `../.skills/rho-aias/reference.md` § Knowledge Sync Details — How Phase 5c progressive sync works
- `../contracts/readme-knowledge-publishing-config.md` — How publishing to knowledge providers is configured
