# Confluence Publishing Configuration

Source of truth for all Confluence publishing operations (Phase 5c progressive sync and `/publish` closure).

---

## Space

- **Space key:** `ECOMM`
- **Space ID:** Resolve at runtime via `getConfluenceSpaces(cloudId, keys=["ECOMM"])` — do not hardcode the numeric ID.
- **Space URL:** https://reeceusa.atlassian.net/wiki/spaces/ECOMM/
- **Root parent page:** `Requirements and Design`
- **Root parent page ID:** `2373517314`
- **Root parent page URL:** https://reeceusa.atlassian.net/wiki/spaces/ECOMM/pages/2373517314/Requirements+and+Design

---

## Publishing Hierarchy

All task artifacts are published as Confluence child pages under:

```
/<TECH>/<YEAR>/<QUARTER>/<TASK_ID>/
```

Where:

- `<TECH>` — platform/technology identifier, first-level grouping (see TECH Resolution below)
- `<YEAR>` — four-digit year (see Date Resolution below)
- `<QUARTER>` — quarter label (see Date Resolution below)
- `<TASK_ID>` — Jira key (e.g. `MAX-12345`)

---

## TECH Resolution (priority order)

Resolve `<TECH>` using the first source that yields a result:

1. **Jira ticket component** (preferred, most reliable):
   - `maX iOS` (id: `10046`) → `iOS`
   - `maX Android` (id: `10047`) → `Android`
   - `maX BE` (id: `10048`) → `Backend`
   - `maX Web` (id: `10045`) → `Web`
   - No component or unrecognized → fall through to next source
2. **Workspace `cursor.projectType`** (fallback):
   - `ios-app` → `iOS`
   - `android-app` → `Android`
   - `rho-aias-workspace` → `Framework`
   - Unrecognized → fall through
3. **User prompt** (last resort): ask the user explicitly. Do NOT guess.

### Supported TECH values

| TECH value | Jira component | `cursor.projectType` |
|------------|----------------|----------------------|
| `iOS` | `maX iOS` (`10046`) | `ios-app`, `swift-package`, `swift-package-demo` |
| `Android` | `maX Android` (`10047`) | `android-app` |
| `Framework` | — | `rho-aias-workspace` |
| `Backend` | `maX BE` (`10048`) | — |
| `Web` | `maX Web` (`10045`) | — |

To add a new technology (e.g. `KMP`, `React`, `Flutter`): add a row to this table and the corresponding Jira component if it exists. No other changes are needed — the hierarchy and algorithm work with any TECH value.

---

## Date Resolution

Both `<YEAR>` and `<QUARTER>` are derived from the **system date at the time of publishing**:

- `<YEAR>` — four-digit year from system date (e.g. `2026`)
- `<QUARTER>` — derived from the month of the system date:

| Months | Quarter |
|--------|---------|
| January — March | `Q1` |
| April — June | `Q2` |
| July — September | `Q3` |
| October — December | `Q4` |

**Format is strict:** `Q1`, `Q2`, `Q3`, `Q4` (uppercase Q + single digit). No other formats (`q1`, `Quarter 1`, `2026-Q1`, etc.) are allowed.

---

## Navigation Algorithm (find-or-create)

Confluence allows creating multiple pages with the same title under the same parent. To **prevent duplicates**, the agent MUST always search before creating.

For each level of the hierarchy, apply this function:

```
-- Step 0: resolve spaceId from spaceKey at runtime (once per publish session)
spaceId = getConfluenceSpaces(cloudId, keys=["ECOMM"]).results[0].id

function findOrCreatePage(cloudId, spaceId, parentId, title, body):
  1. Call getConfluencePageDescendants(cloudId, parentId)
  2. Search the returned list for a page whose title matches `title` exactly (case-sensitive)
  3. IF found:
     → Return the existing page's pageId
  4. IF NOT found:
     → Call createConfluencePage(cloudId, spaceId, title, body, parentId, contentFormat="markdown")
     → Return the newly created page's pageId
```

### Hierarchy and Artifact Title Convention

Confluence enforces title uniqueness at the **space** level, not per parent page. This affects both artifact pages and repeating hierarchy nodes. Titles such as `2026`, `Q1`, or `feasibility.assessment.md` can collide across different branches of the hierarchy.

To prevent this, repeating nodes must use **scope-aware** titles:

```
<TECH>
<TECH>: <YEAR>
<TECH>: <YEAR>: <QUARTER>
<TASK_ID>
<TASK_ID>: <artifact_filename>
```

Examples:
- `iOS`
- `iOS: 2026`
- `iOS: 2026: Q1`
- `MAX-12853`
- `MAX-12853: feasibility.assessment.md`

`<TASK_ID>` remains plain because Jira ticket keys are expected to be globally unique within the publishing space. If that assumption changes in the future, task pages must also adopt a scoped title convention.

### Full publishing flow

The algorithm applies `findOrCreatePage` sequentially for each level:

```
-- Step 0: resolve spaceId (once per session)
spaceId = getConfluenceSpaces(cloudId, keys=["ECOMM"]).results[0].id
rootPageId = "2373517314"

techPageId     = findOrCreatePage(cloudId, spaceId, rootPageId,     "<TECH>",                  "Artifacts for <TECH>")
yearPageId     = findOrCreatePage(cloudId, spaceId, techPageId,     "<TECH>: <YEAR>",          "Artifacts for <TECH> — <YEAR>")
quarterPageId  = findOrCreatePage(cloudId, spaceId, yearPageId,     "<TECH>: <YEAR>: <QUARTER>", "Artifacts for <TECH> — <YEAR> <QUARTER>")
taskPageId     = findOrCreatePage(cloudId, spaceId, quarterPageId,  "<TASK_ID>", "<task summary from status.md>")

-- Then for each artifact (titles are task-scoped):
FOR each artifact in status.md with sync status `created`:
  findOrCreatePage(cloudId, spaceId, taskPageId, "<TASK_ID>: <artifact filename>", "<full publishable artifact body>")

FOR each artifact in status.md with sync status `modified`:
  1. getConfluencePageDescendants(cloudId, taskPageId)
  2. Search for "<TASK_ID>: <artifact filename>" (canonical title)
     IF NOT found, search for "<artifact filename>" (legacy fallback)
  3. updateConfluencePage(cloudId, existingPageId, body=<full publishable artifact body>, contentFormat="markdown")
```

### Rules

- **Never call `createConfluencePage` without first checking descendants.** This is the single most important rule.
- **Resolve `spaceId` at runtime** via `getConfluenceSpaces(cloudId, keys=["ECOMM"])` — never hardcode the numeric space ID.
- **Always pass `contentFormat="markdown"`** in `createConfluencePage` and `updateConfluencePage` calls (artifacts are Markdown files).
- **Hierarchy titles are scope-aware for repeating nodes:** use `<TECH>` for technology pages, `<TECH>: <YEAR>` for year pages, and `<TECH>: <YEAR>: <QUARTER>` for quarter pages.
- **Task pages remain plain `<TASK_ID>`** because ticket keys are expected to be globally unique in the publishing space. Revisit this only if cross-project ticket collisions appear.
- **Artifact page titles are task-scoped:** always use `<TASK_ID>: <artifact filename>` for artifact pages.
- **Title matching is case-sensitive and exact** — `iOS` ≠ `ios` ≠ `IOS`.
- For year and quarter pages, search descendants for the canonical scoped title first; if not found, search for the legacy plain title (`<YEAR>` or `<QUARTER>`) as fallback. Update whichever page is found — do not force-rename legacy pages.
- For artifacts with sync status `created`, use `findOrCreatePage` with the canonical title (`<TASK_ID>: <artifact filename>`).
- For artifacts with sync status `modified`: search descendants for the canonical title first; if not found, search for the plain filename as legacy fallback. Update whichever page is found — do not force-rename legacy pages.
- Artifacts with sync status `synced` are skipped (already up to date).
- **Publish full publishable artifact content** — never summarize, truncate, or abbreviate.
- For Cursor-first `*.plan.md` artifacts, strip only the initial YAML frontmatter block before sending the Markdown payload.
- For non-plan artifacts, publish the full file content as-is.
- If `getConfluencePageDescendants` fails (network error), follow offline graceful degradation: log warning, keep artifact sync status unchanged, do not block command execution. Next command will retry.

---

## Example

Task `MAX-12345` (iOS, Q1 2026) and `MAX-12346` (Android, Q1 2026):

```
Requirements and Design (ID: 2373517314)
├── iOS
│   └── iOS: 2026
│       └── iOS: 2026: Q1
│           └── MAX-12345
│               ├── MAX-12345: analysis.product.md
│               ├── MAX-12345: technical.plan.md
│               ├── MAX-12345: increments.plan.md
│               ├── MAX-12345: specs.design.md
│               ├── MAX-12345: feasibility.assessment.md
│               └── MAX-12345: delta.publish.md
├── Android
│   └── Android: 2026
│       └── Android: 2026: Q1
│           └── MAX-12346
│               ├── MAX-12346: analysis.product.md
│               ├── MAX-12346: technical.plan.md
│               └── ...
├── Backend
│   └── ...
└── Web
    └── ...
```
