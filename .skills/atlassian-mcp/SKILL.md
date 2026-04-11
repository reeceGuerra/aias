---
name: atlassian-mcp
description: Read and write Jira issues and Confluence pages via the Atlassian MCP. Use when the user provides a Jira ticket URL, Jira key (e.g. PROJ-123), Confluence page URL, or asks to interact with Jira or Confluence.
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

## CONTENT FORMAT

Most Confluence and Jira tools accept a `contentFormat` or `responseContentFormat` parameter:

- **Confluence** (`contentFormat`): `"markdown"` or `"adf"`. Default: ADF. Applies to: `createConfluencePage`, `updateConfluencePage`, `getConfluencePage`, `getPagesInConfluenceSpace`, `createConfluenceInlineComment`, `createConfluenceFooterComment`, `getConfluencePageInlineComments`, `getConfluencePageFooterComments`, `getConfluenceCommentChildren`.
- **Jira** (`responseContentFormat`): `"markdown"` or `"adf"`. Default: ADF. Applies to: `getJiraIssue`, `createJiraIssue`, `editJiraIssue`, `searchJiraIssuesUsingJql`, `addCommentToJiraIssue`.

For rho-aias publishing workflows, always use `contentFormat: "markdown"` when writing to Confluence (artifacts are Markdown files).

### Jira Rich Text Policy for Rho AIAS

For tracker enrichment workflows such as `/enrich`:

- Treat Jira field writes as a **remote representation**, not as the canonical local artifact.
- `analysis.product.md` remains local and provider-agnostic; provider-specific headers such as `Enhanced by` MUST NOT be written back into local artifacts.
- For `description`, `Acceptance Criteria`, and `Test Steps`, prefer `contentFormat: "markdown"` when the MCP/instance accepts it reliably.
- If a textarea field rejects Markdown or renders the managed block incorrectly, fall back to explicit ADF for that field.
- When updating enriched text fields, preserve human-authored content outside the Rho AIAS-managed block and replace only the managed block content.
- `/enrich` MUST NOT write RCA fields or RCA narrative for bug workflows when dedicated RCA fields exist.
- Never publish local filesystem paths or machine-specific references to Jira comments or fields.

### Jira RCA Policy for `/report`

For validated bug RCA publication workflows such as `/report`:

- `/report` is **field-first, comment-last**.
- If the tracker exposes structured RCA fields, write there first.
- If equivalent structured RCA fields do not exist, fall back to one structured tracker comment.
- For categorical RCA fields, use only tracker-supported option ids from runtime metadata.
- For open-text RCA fields, prefer `contentFormat: "markdown"` when supported; fall back to ADF when required.
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

Before any write command (`/enrich`, `/report`) pushes content to Jira fields, the agent MUST resolve the target format for each field using this protocol:

1. **Load field mapping**: Read `field_mapping_source` from the resolved tracker config. If missing, abort with `MISSING_FIELD_MAPPING`.
2. **For each target field**, resolve `content_format` using strict precedence:
   1. **Runtime field metadata** (from the Jira issue read response) — highest priority.
   2. **Mapping document** (`Format` column in the loaded `jira-field-mapping.md`) — second priority.
   3. **Default** (ADF for custom textarea fields, Markdown for `description`) — lowest priority.
3. **Record `decision_source`** for each field: `runtime`, `mapping`, or `default`.
4. **Build write plan**: Assemble the resolved format per field. Include in the command's confirmation gate (Tracker Write Preview for `/enrich`, Tracker Publish for `/report`).
5. **Execute writes** using resolved formats only. Never assume a format without resolution.

If runtime metadata contradicts the mapping, use runtime metadata for the write and report mapping drift to the user.

---

## SAFETY RULES

**Read-only by default:**
- Reading issues, pages, comments, and searching: always allowed.
- Creating, editing, transitioning issues; creating or updating Confluence pages; adding comments: **only when the user explicitly asks**. Never perform write operations autonomously.
- **Exception:** Commands that reference [tracker-status-mapping.md](../../aias-config/providers/atlassian/tracker-status-mapping.md) may perform automatic Jira transitions and Confluence publishes as part of the rho-aias loading protocol (Phase 5 and Phase 6). These are governed by the mapping rules, not by this general safety rule.

**Abort on failure:**
- If `getAccessibleAtlassianResources` fails or returns no `cloudId`: abort and ask the user to check Atlassian MCP configuration.
- If any subsequent call fails (timeout, error, permission denied): abort the operation, report the error, and ask the user to verify access.

**Data integrity:**
- Never invent or assume ticket content, status, or fields that the API did not return.
- If a field is missing from the response, report it as unknown; do not fill in defaults.
