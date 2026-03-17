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
   - Unrecognized → fall through
3. **User prompt** (last resort): ask the user explicitly. Do NOT guess.

### Supported TECH values

| TECH value | Jira component | `cursor.projectType` |
|------------|----------------|----------------------|
| `iOS` | `maX iOS` (`10046`) | `ios-app`, `swift-package`, `swift-package-demo` |
| `Android` | `maX Android` (`10047`) | `android-app` |
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

### Artifact Title Convention

Confluence enforces title uniqueness at the **space** level, not per parent page. Two tasks publishing the same artifact filename (e.g., `feasibility.assessment.md`) under different parents will collide.

To prevent this, artifact page titles are **task-scoped**:

```
<TASK_ID>: <artifact_filename>
```

Examples:
- `MAX-12345: technical.plan.md`
- `MAX-12853: feasibility.assessment.md`
- `MAX-12345: delta.publish.md`

Hierarchy-level pages (`<TECH>`, `<YEAR>`, `<QUARTER>`, `<TASK_ID>`) are NOT prefixed — their titles are inherently unique or low-collision.

### Full publishing flow

The algorithm applies `findOrCreatePage` sequentially for each level:

```
-- Step 0: resolve spaceId (once per session)
spaceId = getConfluenceSpaces(cloudId, keys=["ECOMM"]).results[0].id
rootPageId = "2373517314"

techPageId     = findOrCreatePage(cloudId, spaceId, rootPageId,     "<TECH>",    "Artifacts for <TECH>")
yearPageId     = findOrCreatePage(cloudId, spaceId, techPageId,     "<YEAR>",    "Artifacts for <TECH> — <YEAR>")
quarterPageId  = findOrCreatePage(cloudId, spaceId, yearPageId,     "<QUARTER>", "Artifacts for <TECH> — <YEAR> <QUARTER>")
taskPageId     = findOrCreatePage(cloudId, spaceId, quarterPageId,  "<TASK_ID>", "<task summary from status.md>")

-- Then for each artifact (titles are task-scoped):
FOR each artifact in status.md with sync status `created`:
  findOrCreatePage(cloudId, spaceId, taskPageId, "<TASK_ID>: <artifact filename>", "<full artifact file content>")

FOR each artifact in status.md with sync status `modified`:
  1. getConfluencePageDescendants(cloudId, taskPageId)
  2. Search for "<TASK_ID>: <artifact filename>" (canonical title)
     IF NOT found, search for "<artifact filename>" (legacy fallback)
  3. updateConfluencePage(cloudId, existingPageId, body=<full artifact file content>, contentFormat="markdown")
```

### Rules

- **Never call `createConfluencePage` without first checking descendants.** This is the single most important rule.
- **Resolve `spaceId` at runtime** via `getConfluenceSpaces(cloudId, keys=["ECOMM"])` — never hardcode the numeric space ID.
- **Always pass `contentFormat="markdown"`** in `createConfluencePage` and `updateConfluencePage` calls (artifacts are Markdown files).
- **Artifact page titles are task-scoped:** always use `<TASK_ID>: <artifact filename>` for artifact pages. Hierarchy pages (`<TECH>`, `<YEAR>`, `<QUARTER>`, `<TASK_ID>`) keep plain titles.
- **Title matching is case-sensitive and exact** — `iOS` ≠ `ios` ≠ `IOS`.
- For artifacts with sync status `created`, use `findOrCreatePage` with the canonical title (`<TASK_ID>: <artifact filename>`).
- For artifacts with sync status `modified`: search descendants for the canonical title first; if not found, search for the plain filename as legacy fallback. Update whichever page is found — do not force-rename legacy pages.
- Artifacts with sync status `synced` are skipped (already up to date).
- **Publish full artifact content** — never summarize, truncate, or abbreviate. The Confluence page must be a faithful copy of the local file.
- If `getConfluencePageDescendants` fails (network error), follow offline graceful degradation: log warning, keep artifact sync status unchanged, do not block command execution. Next command will retry.

---

## Example

Task `MAX-12345` (iOS, Q1 2026) and `MAX-12346` (Android, Q1 2026):

```
Requirements and Design (ID: 2373517314)
├── iOS
│   └── 2026
│       └── Q1
│           └── MAX-12345
│               ├── MAX-12345: analysis.product.md
│               ├── MAX-12345: technical.plan.md
│               ├── MAX-12345: increments.plan.md
│               ├── MAX-12345: specs.design.md
│               ├── MAX-12345: feasibility.assessment.md
│               └── MAX-12345: delta.publish.md
├── Android
│   └── 2026
│       └── Q1
│           └── MAX-12346
│               ├── MAX-12346: analysis.product.md
│               ├── MAX-12346: technical.plan.md
│               └── ...
├── Backend
│   └── ...
└── Web
    └── ...
```
