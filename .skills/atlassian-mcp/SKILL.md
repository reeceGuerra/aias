---
name: atlassian-mcp
description: Read and write Jira issues and Confluence pages via the Atlassian MCP. Use when the user provides a Jira ticket URL, Jira key (e.g. PROJ-123), Confluence page URL, or asks to interact with Jira or Confluence.
category: mcp
tested_against:
  mcp_server: user-Atlassian@2026-05-05
  tools_count: 31
---

# Atlassian MCP

## PURPOSE

Teach the agent how to interact with the Atlassian MCP server (Jira and Confluence) using the correct call sequences, parameter extraction, and safety rules.

---

## PREREQUISITES

Every Atlassian operation requires a **cloudId**. Obtain it before any other call.

**Get cloudId:**
1. Call `getAccessibleAtlassianResources` (no parameters).
2. The response contains a list of accessible Atlassian sites with their `cloudId`.
3. Select the appropriate `cloudId` for subsequent calls.

If this call fails or returns no results: **abort** and ask the user to check Atlassian MCP configuration.

---

## OPERATIONS

### Read Jira Issue

**When:** User provides a Jira key (e.g. `PROJ-123`) or a Jira URL.

**Parameter extraction from URL:**
- URL format: `https://yoursite.atlassian.net/browse/PROJ-123`
- Extract `issueIdOrKey`: the key after `/browse/` (e.g. `PROJ-123`)
- If the user provides just a key (e.g. `PROJ-123`), use it directly.

**Call sequence:**
1. `getAccessibleAtlassianResources` → obtain `cloudId`
2. `getJiraIssue(cloudId, issueIdOrKey)` → returns issue data (summary, description, status, links, etc.)

**Optional parameters for `getJiraIssue`:**
- `fields` (array): specific fields to return
- `expand` (string): expand additional data

### Read patterns — targeted vs exhaustive (v9.4+ guidance, v9.6+ refresh extension)

| Pattern | When to use | Call |
|---|---|---|
| **Targeted read** | Status checks, transitions, narrow read-only confirmations where the agent already knows which fields it needs. | `getJiraIssue(cloudId, issueIdOrKey, fields=['summary','status','assignee'])` |
| **Exhaustive read** | Refinement / enrichment / RCA workflows where the agent must surface **all** custom fields (RCA categorical fields, legacy enrichment fields, project-specific extensions). Whitelisting fields here silently drops custom fields outside the whitelist and leaves the workflow blind. | `getJiraIssue(cloudId, issueIdOrKey, fields=['*all'], expand='renderedFields,names,schema')` |
| **Exhaustive read + comments (v9.6+)** | `/enrich --refresh` drift detection: must read description + custom fields + comment thread in one call so the diff against on-disk DoR/DoD captures comment-driven amendments (PM/QA edits added after the original `/enrich`). | `getJiraIssue(cloudId, issueIdOrKey, fields=['*all'], expand='renderedFields,names,schema,comment')` |

**Note on `expand` shape:** The `expand` parameter is a **comma-separated string**, not an array. The MCP tool descriptor expects `expand: string` even though earlier framework versions documented it as an array. Always pass `expand='renderedFields,names,schema'` (or with `,comment` appended for `--refresh`).

Rho AIAS adopter skills that MUST use the exhaustive read pattern by contract:

- `/enrich` (refinement reads).
- `/enrich --refresh` (refinement-refresh reads — exhaustive + comments).
- `/report` (RCA reads — needs option catalogs + runtime format metadata for every RCA-adjacent field).

Targeted writes (`editJiraIssue` with specific field keys) remain unchanged — only the input read becomes exhaustive. This guidance is framework-specific (informative) for adopters; generic Atlassian MCP usage MAY choose targeted reads when the field set is known statically.

### Comment thread parsing for refinement refresh (v9.6+)

When `/enrich --refresh` reads the comment thread, the parsing heuristic is:

1. Iterate comments chronologically (oldest first).
2. For each comment, attempt to attribute its body text to DoR/DoD dimensions or DoD criteria. Attribution is heuristic and best-effort — the agent uses semantic interpretation (e.g., "we also need to support iPad Pro 12.9" attributes to a device matrix dimension). When attribution is uncertain, treat the comment as orthogonal to existing dimensions and add a candidate `add` entry to the refresh diff.
3. Comments authored by the AI itself (signed `Rho AIAS via <Tool>` or matching the `addCommentToJiraIssue` payload pattern of `/enrich --brief`) MUST be excluded from the drift signal — they were the original derivation, not new input.
4. Comments older than the original `/enrich` invocation (per `status.md command_log`) are still parsed; their content is the baseline that the original DoR/DoD already encodes. Drift signal comes from comments newer than the last `/enrich` (or `/enrich --refresh`) invocation, identified via `command_log` `ended_at` or `status.md last_refreshed_at`.

The parsing is informative only — the agent surfaces candidate drift via the `Gate: Refresh Approval` preview, where the user decides per-dimension whether to apply.

---

### Search Jira Issues (JQL)

**When:** User asks to find or list issues with specific criteria.

**Call sequence:**
1. `getAccessibleAtlassianResources` → obtain `cloudId`
2. `searchJiraIssuesUsingJql(cloudId, jql)` → returns matching issues

**Key parameters:**
- `jql` (string, required): JQL expression (e.g. `project = MAX AND assignee = currentUser() AND status != Done`)
- `maxResults` (number, optional): max issues per page (default 50, max 100)
- `fields` (array, optional): fields to return (default: summary, description, status, issuetype, priority, created)
- `nextPageToken` (string, optional): for pagination

**Note:** Use `searchJiraIssuesUsingJql` only when JQL is specifically needed. For general searches across Jira and Confluence, use the `search` tool instead.

---

### Create Jira Issue

**When:** User **explicitly asks** to create a Jira issue.

**Call sequence:**
1. `getAccessibleAtlassianResources` → obtain `cloudId`
2. `getVisibleJiraProjects(cloudId)` → obtain `projectKey`
3. `getJiraProjectIssueTypesMetadata(cloudId, projectKey)` → obtain available `issueTypeName`
4. `createJiraIssue(cloudId, projectKey, issueTypeName, summary, ...)` → creates the issue

**Required parameters for `createJiraIssue`:**
- `cloudId`, `projectKey`, `issueTypeName`, `summary`

**Optional parameters:**
- `description` (string): Markdown content
- `parent` (string): key or id of parent issue (for subtasks)
- `assignee_account_id` (string): use `lookupJiraAccountId` to resolve from display name or email
- `additional_fields` (object): custom fields

---

### Edit Jira Issue

**When:** User **explicitly asks** to update an existing issue.

**Call sequence:**
1. `getAccessibleAtlassianResources` → obtain `cloudId`
2. `editJiraIssue(cloudId, issueIdOrKey, ...)` → updates the issue

---

### Add Comment to Jira Issue

**When:** User **explicitly asks** to add a comment to a ticket.

**Call sequence:**
1. `getAccessibleAtlassianResources` → obtain `cloudId`
2. `addCommentToJiraIssue(cloudId, issueIdOrKey, body)` → adds comment

**Parameters:**
- `body` (string): comment content in Markdown

---

### Transition Jira Issue

**When:** User **explicitly asks** to change the status of an issue.

**Call sequence:**
1. `getAccessibleAtlassianResources` → obtain `cloudId`
2. `getTransitionsForJiraIssue(cloudId, issueIdOrKey)` → list available transitions
3. `transitionJiraIssue(cloudId, issueIdOrKey, transitionId)` → apply the transition

---

### Read Confluence Page

**When:** User provides a Confluence URL or asks to read a Confluence page.

**Call sequence:**
1. `getAccessibleAtlassianResources` → obtain `cloudId`
2. `getConfluencePage(cloudId, pageId)` → returns page content

**Optional parameters for `getConfluencePage`:**
- `contentFormat` (string): `"markdown"` or `"adf"` (default: ADF)

**Parameter extraction from URL:**
- URL format: `https://yoursite.atlassian.net/wiki/spaces/SPACE/pages/12345/Page+Title`
- Extract `pageId` from the URL path.

---

### Search Confluence (CQL)

**When:** User asks to find Confluence pages.

**Call sequence:**
1. `getAccessibleAtlassianResources` → obtain `cloudId`
2. `searchConfluenceUsingCql(cloudId, cql)` → returns matching pages

---

### User Lookup

**When:** Need to resolve a user's `account_id` for assignment or mentions.

**Options:**
- `atlassianUserInfo` (no parameters) → current authenticated user
- `lookupJiraAccountId(displayName or email)` → resolve other users

---

### Get Issue Link Types

**When:** Need to discover available link types (Blocks, Duplicate, Clones, Relates, etc.) before creating a link.

**Call sequence:**
1. `getAccessibleAtlassianResources` → obtain `cloudId`
2. `getIssueLinkTypes(cloudId)` → returns available link type names and directions

---

### Create Issue Link

**When:** User **explicitly asks** to link two Jira issues.

**Call sequence:**
1. `getAccessibleAtlassianResources` → obtain `cloudId`
2. `getIssueLinkTypes(cloudId)` → obtain `type` name
3. `createIssueLink(cloudId, inwardIssue, outwardIssue, type)` → creates the link

---

### Get Confluence Comment Children

**When:** Need to retrieve replies (children) of a Confluence comment.

**Call sequence:**
1. `getAccessibleAtlassianResources` → obtain `cloudId`
2. `getConfluenceCommentChildren(cloudId, commentId, commentType)` → returns child comments

---

### Cross-Surface Search (Rovo)

**When:** User asks to find content across Jira and Confluence without specifying JQL or CQL. This is the preferred general-purpose search.

**Call:**
`search(query)` — no `cloudId` needed; derived automatically from the token.

**When NOT to use:** If the user explicitly provides JQL syntax, use `searchJiraIssuesUsingJql` instead. If the user provides CQL, use `searchConfluenceUsingCql` instead.

---

### Fetch by ARI

**When:** You have an Atlassian Resource Identifier (ARI) — a universal ID for any Atlassian resource — and need to retrieve the associated Jira issue or Confluence page.

**Call:**
`fetch(id)` — where `id` is the ARI string.

**Note:** Use this only when you have an ARI. For standard issue keys (e.g. `PROJ-123`) use `getJiraIssue`. For page IDs use `getConfluencePage`.

---

### Add Worklog to Jira Issue

**When:** User **explicitly asks** to log time on a Jira issue.

**Call sequence:**
1. `getAccessibleAtlassianResources` → obtain `cloudId`
2. `addWorklogToJiraIssue(cloudId, issueIdOrKey, timeSpent, ...)` → adds or updates worklog

**Required parameters:**
- `cloudId`, `issueIdOrKey`, `timeSpent` (e.g. `"2h"`, `"30m"`)

**Optional parameters:**
- `worklogId` (string): if provided, updates that worklog instead of creating a new one
- `commentBody` (string): worklog comment
- `started` (string): ISO 8601 date-time when work started (defaults to now)
- `visibility` (object): `{ type: "group"|"role", value: "..." }` to restrict visibility

---

### Get Issue Field Metadata

**When:** Need to discover which fields are available for a specific issue type before creating or editing an issue with custom fields.

**Call sequence:**
1. `getAccessibleAtlassianResources` → obtain `cloudId`
2. `getJiraIssueTypeMetaWithFields(cloudId, projectIdOrKey, issueTypeId, ...)` → returns available fields and constraints

---

### Get Remote Issue Links

**When:** Need to see external (non-Jira) links attached to a Jira issue (e.g., links to GitHub PRs, Confluence pages, or other external systems).

**Call sequence:**
1. `getAccessibleAtlassianResources` → obtain `cloudId`
2. `getJiraIssueRemoteIssueLinks(cloudId, issueIdOrKey)` → returns remote links

---

### Create Confluence Page

**When:** User **explicitly asks** to create a new Confluence page or blog post.

**Call sequence:**
1. `getAccessibleAtlassianResources` → obtain `cloudId`
2. `getConfluenceSpaces(cloudId)` → obtain `spaceId` (if not already known)
3. `createConfluencePage(cloudId, spaceId, body, ...)` → creates the page

**Required parameters:**
- `cloudId`, `spaceId`, `body`

**Optional parameters:**
- `title` (string): page title
- `contentType` (string): `"page"` (default) or `"blog"`
- `parentId` (string): parent page ID for nesting
- `status` (string): `"current"` (published, default) or `"draft"`
- `contentFormat` (string): `"markdown"` or `"adf"` (default: ADF)
- `isPrivate` (boolean): make private

---

### Update Confluence Page

**When:** User **explicitly asks** to update an existing Confluence page.

**Call sequence:**
1. `getAccessibleAtlassianResources` → obtain `cloudId`
2. `updateConfluencePage(cloudId, pageId, body, ...)` → updates the page

**Required parameters:**
- `cloudId`, `pageId`, `body`

**Optional parameters:**
- `title` (string): new title
- `contentFormat` (string): `"markdown"` or `"adf"` (default: ADF)
- `versionMessage` (string): change description
- `status` (string): `"current"` or `"draft"`
- `parentId` (string): reparent the page

---

### Get Confluence Spaces

**When:** Need to discover available Confluence spaces (to resolve a `spaceId` for page creation or navigation).

**Call sequence:**
1. `getAccessibleAtlassianResources` → obtain `cloudId`
2. `getConfluenceSpaces(cloudId, ...)` → returns list of spaces with their IDs and keys

**Optional filters:** `keys` (array of space keys), `type` (`"global"` | `"personal"`), `status`, `favourite`

---

### Get Pages in Confluence Space

**When:** Need to list pages or blog posts in a known space.

**Call sequence:**
1. `getAccessibleAtlassianResources` → obtain `cloudId`
2. `getPagesInConfluenceSpace(cloudId, spaceId, ...)` → returns pages in the space

**Optional parameters:** `contentType` (`"page"` | `"blog"`), `limit`, `cursor`, `status`, `title` (filter), `sort`

---

### Get Confluence Page Descendants

**When:** Need to explore the child page hierarchy under a given Confluence page.

**Call sequence:**
1. `getAccessibleAtlassianResources` → obtain `cloudId`
2. `getConfluencePageDescendants(cloudId, pageId, ...)` → returns child pages

**Optional parameters:** `depth` (max depth to traverse), `limit`, `cursor`

---

### Read Confluence Page Comments

**When:** Need to read comments left on a Confluence page.

**Call sequence:**
1. `getAccessibleAtlassianResources` → obtain `cloudId`
2. For footer comments: `getConfluencePageFooterComments(cloudId, pageId)` → returns footer comments
3. For inline comments: `getConfluencePageInlineComments(cloudId, pageId)` → returns inline comments

---

### Create Confluence Page Comment

**When:** User **explicitly asks** to add a comment to a Confluence page.

**Call sequence:**
1. `getAccessibleAtlassianResources` → obtain `cloudId`
2. For a footer comment: `createConfluenceFooterComment(cloudId, body, pageId, ...)` → adds footer comment
3. For an inline comment on highlighted text: `createConfluenceInlineComment(cloudId, body, pageId, inlineCommentProperties, ...)` → adds inline comment

**Inline comment `inlineCommentProperties`:**
- `textSelection` (string, required): the text to anchor the comment to
- `textSelectionMatchCount` (number, required): total occurrences of that text on the page
- `textSelectionMatchIndex` (number, required): which occurrence to highlight (0-based)

---

## CONTENT FORMAT

Most Confluence and Jira tools accept a `contentFormat` or `responseContentFormat` parameter:

- **Confluence** (`contentFormat`): `"markdown"` or `"adf"`. Default: ADF. Applies to: `createConfluencePage`, `updateConfluencePage`, `getConfluencePage`, `getPagesInConfluenceSpace`, `createConfluenceInlineComment`, `createConfluenceFooterComment`, `getConfluencePageInlineComments`, `getConfluencePageFooterComments`, `getConfluenceCommentChildren`.
- **Jira** (`responseContentFormat`): `"markdown"` or `"adf"`. Default: ADF. Applies to: `getJiraIssue`, `createJiraIssue`, `editJiraIssue`, `searchJiraIssuesUsingJql`, `addCommentToJiraIssue`.

For Markdown-first publishing workflows, use `contentFormat: "markdown"` when writing to Confluence. The exception is **TOC macro injection**: if a publishing config includes a `## Table of Contents` section, read each published page in ADF (`contentFormat: "adf"`), insert the TOC extension node if missing, and write back in ADF. If that section is absent, TOC injection is skipped.

### Optional Framework Integration Notes (Rho AIAS adopters)

The guidance below is framework-specific and optional. It MUST NOT be interpreted as a prerequisite for generic Atlassian MCP usage.

### Jira Rich Text Policy for Rho AIAS

For tracker enrichment workflows:

- Treat Jira field writes as a **remote representation**, not as the canonical local artifact.
- `analysis.product.md` remains local and provider-agnostic; provider-specific headers such as `Enhanced by` MUST NOT be written back into local artifacts.
- For `description`, `Acceptance Criteria`, and `Test Steps`, SHOULD use `contentFormat: "markdown"` when the MCP/instance accepts it reliably.
- If a textarea field rejects Markdown or renders the managed block incorrectly, fall back to explicit ADF for that field.
- When updating enriched text fields, preserve human-authored content outside the Rho AIAS-managed block and replace only the managed block content.
- Enrichment flows MUST NOT write RCA fields or RCA narrative when dedicated RCA fields exist.
- Never publish local filesystem paths or machine-specific references to Jira comments or fields.

### Jira RCA Policy for RCA publication flows

For validated bug RCA publication workflows:

- `/report` is **field-first, comment-last**.
- If the tracker exposes structured RCA fields, write there first.
- If equivalent structured RCA fields do not exist, fall back to one structured tracker comment.
- For categorical RCA fields, use only tracker-supported option ids from runtime metadata.
- For open-text RCA fields, SHOULD use `contentFormat: "markdown"` when supported; fall back to ADF when required.
- If tracker runtime metadata and the project mapping diverge, runtime metadata takes precedence for the remote write. The mapping must then be updated.
- If evidence is insufficient for a target RCA field, do not invent a value. Defer to the command's evidence sufficiency gate.

---

## REFERENCE

For complete parameter details, types, and return values for every tool, see [reference.md](reference.md).

For Jira field mapping (traceability, field catalogs, format rules, push behavior per command), see [aias-config/providers/atlassian/jira-field-mapping.md](../../aias-config/providers/atlassian/jira-field-mapping.md).

For Jira status transitions within the rho-aias development workflow, see [aias-config/providers/atlassian/tracker-status-mapping.md](../../aias-config/providers/atlassian/tracker-status-mapping.md).

For Confluence publishing configuration (space, root page, hierarchy, TECH resolution, date resolution, find-or-create navigation algorithm), see [aias-config/providers/atlassian/confluence-config.md](../../aias-config/providers/atlassian/confluence-config.md).

> **Separation of concerns:** Project-specific configuration files (field mappings, status mappings, publishing configs) live in `aias-config/providers/<provider_id>/`, not in this skill directory. This skill provides operational knowledge (MCP call sequences, safety rules, content format policy). Configuration is resolved through the provider config contract.

---

## PRE-WRITE RESOLUTION PROTOCOL

Before any write workflow pushes content to Jira fields, the agent MUST resolve the target format for each field using this protocol:

1. **Load field mapping**: Read `field_mapping_source` from the resolved tracker config. If missing, abort with `MISSING_FIELD_MAPPING`.
2. **For each target field**, resolve `content_format` using strict precedence:
   1. **Runtime field metadata** (from the Jira issue read response) — highest priority.
   2. **Mapping document** (`Format` column in the loaded `jira-field-mapping.md`) — second priority.
   3. **Default** (ADF for custom textarea fields, Markdown for `description`) — lowest priority.
3. **Record `decision_source`** for each field: `runtime`, `mapping`, or `default`.
4. **Build write plan**: Assemble the resolved format per field and present it in the workflow's confirmation gate before writing.
5. **Execute writes** using resolved formats only. Never assume a format without resolution.

If runtime metadata contradicts the mapping, use runtime metadata for the write and report mapping drift to the user.

---

## PRE-PUBLISH TITLE VALIDATION

Before any `createConfluencePage` or `updateConfluencePage` call, the agent MUST run the title through the `validateTitleBeforePublish` sub-routine derived from the resolved knowledge publishing config (see `readme-knowledge-publishing-config.md` § Rules § Title Canonicity and the project-specific provider config, e.g., `aias-config/providers/atlassian/confluence-config.md` § Title Canonicity (FORBIDDEN PATTERNS)).

### Sub-routine

```
function validateTitleBeforePublish(cloudId, pageType, title):
  config = loadResolvedKnowledgePublishingConfig()
  pattern = config.titleRegexFor(pageType)   # e.g. artifactRegex or hierarchyRegex
  if not regex_match(pattern, title):
    abort("FORBIDDEN_TITLE: '<title>' does not match canonical pattern for pageType=<pageType>.
           Re-derive the title from the canonical filename or hierarchy convention
           defined in the provider config before publishing.")
  return true
```

### Mandatory invocation points

- Immediately before invoking `createConfluencePage(cloudId, spaceId, title, body, ...)`.
- Immediately before invoking `updateConfluencePage(cloudId, pageId, body, title=...)` when `title` is being changed.

### Abort semantics

- The validator aborts the **specific publish call**, not the entire workflow. The orchestrator MAY recover by re-deriving the canonical title (e.g., from filename or hierarchy convention) and retrying the publish.
- The agent MUST NOT silently mutate the title to make it pass the regex; it MUST re-derive deterministically from the canonical source.
- Title humanization in any form (filename → description, separator substitution, case drift) is FORBIDDEN — see the FORBIDDEN PATTERNS section in the project's `confluence-config.md` for the closed list.

### Cross-provider applicability

This validator is provider-agnostic in shape but provider-specific in its regex source. Other knowledge providers (Notion, etc.) SHOULD declare equivalent regexes in their own `<provider>-config.md` files and reuse the same sub-routine pattern.

---

## SAFETY RULES

**Read-only by default:**
- Reading issues, pages, comments, and searching: always allowed.
- Creating, editing, transitioning issues; creating or updating Confluence pages; adding comments: **only when the user explicitly asks**. Never perform write operations autonomously.
- **Exception:** Framework orchestrators MAY perform configured automatic transitions/publishes when explicitly declared by their own contracts. Those behaviors are governed by mapping/config contracts, not by this general safety rule.

**Abort on failure:**
- If `getAccessibleAtlassianResources` fails or returns no `cloudId`: abort and ask the user to check Atlassian MCP configuration.
- If any subsequent call fails (timeout, error, permission denied): abort the operation, report the error, and ask the user to verify access.

**Data integrity:**
- Never invent or assume ticket content, status, or fields that the API did not return.
- If a field is missing from the response, report it as unknown; do not fill in defaults.

