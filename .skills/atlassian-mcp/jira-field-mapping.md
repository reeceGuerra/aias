> **DEPRECATED (v7.5)** — This file has moved to `aias-config/providers/atlassian/jira-field-mapping.md`.
> This copy is kept for backward compatibility during migration.
> Run `/aias health` to detect and migrate automatically.
> This file will be removed in a future version.

# Jira Field Mapping — MAX Project (Story + Bug)

Field mapping for the MAX project across the issue types currently used by rho-aias tracker workflows.
Used by `/enrich`, `/report`, and `/brief` when pushing content to Jira.

Important precedence rule:
- **Runtime metadata first**: when Jira runtime metadata and this document diverge, the agent MUST use runtime metadata for remote writes.
- **Mapping second**: this file is the maintained project profile and operational documentation. If runtime metadata differs, update this file.

---

## 1. Story Issue Type (`issuetype.id: 10005`)

Story mapping is used primarily by `/enrich` and `/brief`.

### Traceability: Product → Enrich → Jira Field

| @product output | /enrich dimension | Jira field | Field key | Format |
|---|---|---|---|---|
| JTBD analysis, 5 Whys | **Problem statement** | Summary + Description | `summary` + `description` | Summary: plain text (one line). Description: Markdown (SHOULD) or ADF |
| User Journey Analysis | **User flow** | Description (flow subsection) | `description` | Markdown (SHOULD) or ADF |
| MoSCoW Prioritization | **Priority signal** | Priority | `priority` | `{ "id": "<id>" }` — see catalog |
| JTBD + User Journey | **Acceptance criteria** | Acceptance Criteria | `customfield_10036` | Markdown (Given/When/Then list) |
| User Journey (edge cases) | **Test criteria** | Test Steps | `customfield_10062` | Markdown (numbered steps) |
| — | **UI specification** | Description (design subsection) | `description` | Markdown (SHOULD) or ADF |
| — | **API / Data contract** | Description (API subsection) | `description` | Markdown (SHOULD) or ADF |
| — | **File impact** | Local artifact only by default | — | Kept in `analysis.product.md` unless explicitly promoted |
| — | **Dependencies** | Linked Issues + Description | `issuelinks` + `description` | Links via API; condensed list in description only when relevant |
| — | **Non-functional requirements** | Description (constraints subsection) | `description` | Markdown (SHOULD) or ADF |
| — | **Out of scope** | Description (scope subsection) | `description` | Markdown (SHOULD) or ADF |

### Story Mapping Rules

- **Summary** (`summary`): One-line problem statement. Max ~120 characters. No markdown.
- **Description** (`description`): Receives a curated narrative subset only. It MUST NOT duplicate the full local analysis artifact.
- **Acceptance Criteria** (`customfield_10036`): Only verifiable Given/When/Then criteria. No narrative.
- **Test Steps** (`customfield_10062`): Numbered manual verification steps derived from acceptance criteria and edge cases.
- **Priority** (`priority`): Map MoSCoW → Priority: Must Have → High/Highest, Should Have → Medium, Could Have → Low, Won't Have → do not set.

---

## 2. Bug Issue Type (`issuetype.id: 10010`)

Bug mapping is used primarily by `/report`.

### Traceability: Report → Jira RCA Fields

| `/report` output | Jira field | Field key | Format | Ownership |
|---|---|---|---|---|
| `RCA Determination` | RCA Determination | `customfield_10056` | `{ "id": "<option-id>" }` | `/report` |
| `RCA Introduction Factor` | RCA Introduction Factor | `customfield_10057` | `{ "id": "<option-id>" }` | `/report` |
| `RCA Detection Factor` | RCA Detection Factor | `customfield_10058` | `{ "id": "<option-id>" }` | `/report` |
| `RCA Analysis` | RCA Analysis | `customfield_10059` | Markdown (SHOULD) or ADF | `/report` |
| `RCA Preventive Action` | RCA Preventive Action | `customfield_10060` | Markdown (SHOULD) or ADF | `/report` |
| `RCA Corrective Action` | RCA Corrective Action | `customfield_10061` | Markdown (SHOULD) or ADF | `/report` |
| Problem / Expected / Actual summary | Structured fallback comment only when equivalent RCA fields are unavailable in the provider | — | Markdown comment | `/report` |

### Bug Mapping Rules

- `/report` owns all six RCA fields in bug workflows.
- `/enrich` MUST NOT write RCA fields or RCA narrative into tracker fields for bug workflows.
- Categorical RCA fields MUST use option ids from the tracker-supported catalog. Free text is invalid.
- Open-text RCA fields MUST be written only when evidence is sufficient or the user explicitly provides the missing text during the Evidence Sufficiency gate flow.
- If a structured RCA field is unsupported by the provider, `/report` MAY fall back to a structured tracker comment.

### Bug RCA Field Catalog

| Field | Key | Schema | Format (API / MCP) |
|---|---|---|---|
| RCA Determination | `customfield_10056` | option (radiobuttons) | `{ "id": "<id>" }` |
| RCA Introduction Factor | `customfield_10057` | option (radiobuttons) | `{ "id": "<id>" }` |
| RCA Detection Factor | `customfield_10058` | option (radiobuttons) | `{ "id": "<id>" }` |
| RCA Analysis | `customfield_10059` | string (textarea) | Markdown (SHOULD) or ADF |
| RCA Preventive Action | `customfield_10060` | string (textarea) | Markdown (SHOULD) or ADF |
| RCA Corrective Action | `customfield_10061` | string (textarea) | Markdown (SHOULD) or ADF |

### RCA Determination Catalog

| ID | Value | When to use |
|---|---|---|
| `10026` | Avoidable | Evidence shows the defect could reasonably have been prevented within the expected workflow |
| `10027` | Unavoidable | Evidence shows the defect was not reasonably preventable under the expected workflow |

### RCA Introduction Factor Catalog

| ID | Value | When to use |
|---|---|---|
| `10028` | Requirement Description was inadequate | The defect traces back to weak or incomplete requirement description |
| `10029` | Use Case was not Captured | A relevant use case was missing from the original understanding |
| `10030` | Communication Gap with Development Team | Misalignment or communication breakdown contributed to the defect |
| `10031` | Not Compliant with Requirement Document | Implementation deviated from the documented requirement |
| `10032` | Insufficient Unit Test Case | Missing or weak unit coverage allowed the defect in |
| `10033` | Insufficent Skillset | Capability gap materially contributed to the defect |
| `10034` | Defect Raise during to interaction with another requirement | The defect emerged from interaction effects with another requirement |
| `10035` | Requirement Tested in wrong way | Validation approach did not match the real requirement behavior |
| `10036` | Test Enviroment was Incorrect | The defect is attributable to an incorrect test environment |
| `10037` | Documentation is not clear | Unclear documentation materially contributed to the defect |
| `10038` | Deployment Issue | The defect originated in deployment or release handling |
| `10039` | Unforeseen Issue | None of the more specific introduction factors fit with confidence |

### RCA Detection Factor Catalog

| ID | Value | When to use |
|---|---|---|
| `10040` | Scoping | The defect should have been detected during scoping |
| `10041` | Planning | The defect should have been detected during planning |
| `10042` | Building | The defect should have been detected while building / implementing |
| `10043` | Testing | The defect should have been detected in test activities |
| `10044` | Deployment | The defect should have been detected during deployment |
| `10045` | Post Deployment | The defect was detected only after deployment |

---

## 3. Common Field Catalog — System Fields

| Field | Key | Schema | Format (API / MCP) | Catalog |
|---|---|---|---|---|
| Summary | `summary` | string | Plain text (single line) | — |
| Description | `description` | string | Markdown via MCP `editJiraIssue` (converted to ADF) | — |
| Assignee | `assignee` | user | `{ "accountId": "<id>" }` | Dynamic (user picker) |
| Priority | `priority` | priority | `{ "id": "<id>" }` | See below |
| Labels | `labels` | array of string | `["label1", "label2"]` | Free text |
| Components | `components` | array of component | `[{ "id": "<id>" }]` | See below |
| Fix Versions | `fixVersions` | array of version | `[{ "id": "<id>" }]` | Dynamic (project versions) |
| Linked Issues | `issuelinks` | array of issuelink | Via issue link API | — |
| Attachment | `attachment` | array of attachment | Via attachment API (not edit body) | — |

### Priority Catalog

| ID | Name | When to use |
|---|---|---|
| `1` | Highest | Critical blocker, production down |
| `2` | High | Must Have (MoSCoW), significant user impact |
| `3` | Medium | Should Have (MoSCoW), moderate impact |
| `10000` | Needs Priority | Default — not yet triaged |
| `4` | Low | Could Have (MoSCoW), minor impact |
| `5` | Lowest | Nice to have, no urgency |

### Components Catalog

| ID | Name | When to use |
|---|---|---|
| `10047` | maX Android | Android-specific work |
| `10048` | maX BE | Backend-specific work |
| `10046` | maX iOS | iOS-specific work |
| `10045` | maX Web | Web-specific work |
| `10036` | Technical Debt | Refactoring, tech debt reduction |

---

## 4. Common Field Catalog — Shared Custom Fields

| Field | Key | Schema | Format (API / MCP) | Catalog |
|---|---|---|---|---|
| Team | `customfield_10001` | team | Team ID | Dynamic (team picker) |
| Sprint | `customfield_10020` | array (json) | Sprint ID | Dynamic (board sprints) |
| Target Start | `customfield_10022` | date | `YYYY-MM-DD` | — |
| Target End | `customfield_10023` | date | `YYYY-MM-DD` | — |
| Story Points | `customfield_10028` | number (float) | Plain number | — |
| Acceptance Criteria | `customfield_10036` | string (textarea) | Markdown (SHOULD) or ADF | Story workflows |
| Test Steps | `customfield_10062` | string (textarea) | Markdown (SHOULD) or ADF | Story workflows |
| QA Assignee | `customfield_10293` | user (userpicker) | `{ "accountId": "<id>" }` | Dynamic (user picker) |
| Blocker Comment | `customfield_10446` | string (textarea) | Markdown (SHOULD) or ADF | — |
| Dev Estimate | `customfield_10552` | option (select) | `{ "id": "<id>" }` | See below |
| Demo Date | `customfield_10553` | date | `YYYY-MM-DD` | — |

### Dev Estimate Catalog

| ID | Value | Rough guidance |
|---|---|---|
| `10931` | 4 hours | Small fix, single file, well-understood |
| `10932` | 1-2 Days | Standard feature increment, few files |
| `10933` | 3-5 days | Multi-file feature, integration work |
| `11081` | 10 Days | Large feature, multiple increments, cross-module |

---

## 5. Format Rules for MCP Writes

When using `atlassian-mcp` to write to Jira:

- **Runtime metadata has precedence** over this document for remote writes.
- **`editJiraIssue`** accepts Markdown for `description` — the MCP converts it to ADF.
- **Custom textarea fields** (`customfield_10036`, `customfield_10059`, `customfield_10060`, `customfield_10061`, `customfield_10062`, `customfield_10446`): SHOULD use Markdown string. If the instance rejects it, fall back to ADF.
- **Select/option fields** (`priority`, `customfield_10056`, `customfield_10057`, `customfield_10058`, `customfield_10552`): MUST use `{ "id": "<id>" }` with a value from the catalog. Free text is rejected by the API.
- **Component fields**: MUST use `[{ "id": "<id>" }]` with IDs from the catalog. Names are not accepted.
- **User fields** (`assignee`, `customfield_10293`): require `accountId`. Do NOT set these unless the user explicitly provides the assignee.
- **Date fields**: ISO format `YYYY-MM-DD`. Do NOT set target dates unless explicitly provided.

If runtime metadata and this mapping diverge:
1. Use runtime metadata for the remote write.
2. Report the divergence as mapping drift.
3. Update this file to restore alignment for the MAX Jira profile.

---

## 6. `/enrich` Push Behavior (Story-oriented Enrichment)

When `/enrich` writes to Jira after the tracker write gate:

1. **Do NOT publish comments with local filesystem paths** or machine-specific references.
2. **Description** → preserve human content outside the Rho AIAS-owned block; create or replace only that managed block.
3. **Acceptance Criteria** → preserve human content outside the Rho AIAS-owned block; create or replace only that managed block with criteria content.
4. **Test Steps** → preserve human content outside the Rho AIAS-owned block; create or replace only that managed block with test-step content.
5. **Priority** → set via `priority` field only if the current value is `Needs Priority` (`10000`). Do not override a human-set priority.
6. **Components** → set if the ticket has none and the platform is identifiable. Do not remove existing components.
7. **Dev Estimate** → set only if explicitly derived from `/charter` or user input. Do not guess.
8. `/enrich` MUST NOT write RCA fields or push RCA narrative into tracker `Description`.
9. All other fields (Sprint, Assignee, QA Assignee, dates) → do NOT set automatically. These are team decisions.

### Description Structure for `/enrich`

When `/enrich` writes to `description`, it MUST preserve human-authored content outside the Rho AIAS-managed block and only add or replace the managed enrichment block. The block is a push-only representation; it does not exist in the local artifact.

Use this structure for the managed block:

```markdown
<original human content, may be empty>

## Enhanced by
Rho AIAS via <ToolName>

### Enrichment Content
## Problem Statement
<problem framing>

## Expected Behavior / Scope
<target behavior and scope summary>

## User Flow
1. <step>
2. <step>

## Key Constraints / Risks
- <constraint or risk>
```

Work-type shaping rules for `Description`:
- **Feature + user-facing**: user-facing outcome structure (for example user story + scope)
- **Bugfix**: `Problem / Expected / Actual` framing without RCA sections
- **Refactor / technical debt / infrastructure**: system-facing structure such as `Technical Intent / Scope / Constraints`

### Owned Block Replacement Algorithm

For each enriched text field:

1. Read the existing field value.
2. Detect whether a Rho AIAS-managed block already exists:
   - start marker: `## Enhanced by`
   - identity line: `Rho AIAS` or `Rho AIAS via <ToolName>`
   - managed content marker: `### Enrichment Content`
3. If no managed block exists:
   - preserve the existing human content as-is
   - append the managed block after a blank separator
4. If a managed block exists:
   - replace only the managed block
   - preserve any human-authored content before or after it
5. The operation MUST be idempotent: re-running `/enrich` updates the managed block instead of duplicating it.

---

## 7. `/report` Push Behavior (Bug RCA Publication)

When `/report` writes to Jira:

1. Detect the issue type and editable field metadata via runtime.
2. If structured RCA fields are supported, use them first.
3. Write the three categorical RCA fields only with valid option ids from the runtime-supported catalog.
4. Write the three open-text RCA fields using Markdown when supported, or ADF when required.
5. If equivalent structured RCA fields are not supported, publish a single structured fallback comment instead of inventing field writes.
6. `/report` owns the six RCA fields for bug workflows.
