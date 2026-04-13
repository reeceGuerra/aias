# Atlassian MCP — Tool Reference

Complete parameter reference for all tools available in the Atlassian MCP server (Jira and Confluence).

---

## Authentication and Resources

### getAccessibleAtlassianResources

| Field | Details |
|-------|---------|
| **Purpose** | Obtain `cloudId` — required before any other Atlassian call |
| **Parameters** | None |
| **Returns** | List of accessible Atlassian Cloud sites with their `cloudId` (UUID) |

### atlassianUserInfo

| Field | Details |
|-------|---------|
| **Purpose** | Get information about the current authenticated Atlassian user |
| **Parameters** | None |
| **Returns** | Current user's account ID, display name, email |

### lookupJiraAccountId

| Field | Details |
|-------|---------|
| **Purpose** | Resolve a user's `account_id` from display name or email |
| **Parameters** | Display name or email address |
| **Returns** | Matching user account IDs |

---

## Jira — Projects

### getVisibleJiraProjects

| Field | Details |
|-------|---------|
| **Purpose** | List Jira projects visible to the authenticated user |
| **Parameters** | `cloudId` (string, required) |
| **Returns** | List of projects with `projectKey` |

### getJiraProjectIssueTypesMetadata

| Field | Details |
|-------|---------|
| **Purpose** | Get available issue types for a project |
| **Parameters** | `cloudId` (string, required), `projectKey` (string, required) |
| **Returns** | List of `issueTypeName` values (e.g. "Epic", "Story", "Task", "Bug", "Subtask") |

### getJiraIssueTypeMetaWithFields

| Field | Details |
|-------|---------|
| **Purpose** | Get field metadata for a specific issue type |
| **Parameters** | `cloudId` (string, required), `projectKey` (string, required), `issueTypeName` (string, required) |
| **Returns** | Available fields, their types, and constraints for the given issue type |

---

## Jira — Issues

### createJiraIssue

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cloudId` | string | Yes | Atlassian Cloud instance ID (UUID) |
| `projectKey` | string | Yes | Project key in Jira |
| `issueTypeName` | string | Yes | Issue type (e.g. "Story", "Bug", "Task") |
| `summary` | string | Yes | Issue title/summary |
| `description` | string | No | Issue description in Markdown |
| `parent` | string | No | Key or ID of parent issue (for "Subtask" type) |
| `assignee_account_id` | string | No | Account ID of assignee (use `lookupJiraAccountId` to resolve) |
| `additional_fields` | object | No | Custom fields as key-value pairs |
| `contentFormat` | string | No | Content format: `"markdown"` or `"adf"` (default: ADF) |
| `responseContentFormat` | string | No | Response content format: `"markdown"` or `"adf"` (default: ADF) |

### getJiraIssue

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cloudId` | string | Yes | Atlassian Cloud instance ID |
| `issueIdOrKey` | string | Yes | Issue numeric ID (e.g. `10000`) or key (e.g. `PROJ-123`) |
| `fields` | array | No | Specific fields to return |
| `fieldsByKeys` | boolean | No | Whether to reference fields by keys |
| `expand` | string | No | Expand additional data |
| `properties` | array | No | Issue properties to include |
| `updateHistory` | boolean | No | Whether to update the user's issue view history |
| `failFast` | boolean | No | Fail fast on error |
| `responseContentFormat` | string | No | Response content format: `"markdown"` or `"adf"` (default: ADF) |

### editJiraIssue

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cloudId` | string | Yes | Atlassian Cloud instance ID |
| `issueIdOrKey` | string | Yes | Issue to edit |
| All other parameters from `createJiraIssue` | — | No | Fields to update |
| `contentFormat` | string | No | Content format: `"markdown"` or `"adf"` (default: ADF) |
| `responseContentFormat` | string | No | Response content format: `"markdown"` or `"adf"` (default: ADF) |

**Rho AIAS guidance:**
- For `/enrich`, use `responseContentFormat` consistent with the parser needed to detect and replace the Rho AIAS-managed block safely.
- Prefer `contentFormat: "markdown"` for `description`, `customfield_10036`, and `customfield_10062` when the target field behaves correctly with Markdown.
- If a target textarea rejects Markdown or the rendered result is unstable, retry using explicit ADF for that field.
- Preserve human-authored content outside the managed block; replace only the `Enhanced by` block owned by Rho AIAS.
- `/enrich` MUST NOT write RCA fields for bug workflows.
- For `/report`, use runtime field metadata to determine whether structured RCA fields exist and which option ids are valid.
- If runtime metadata and the documented mapping diverge, use runtime metadata for the remote write and treat the mapping as needing maintenance.

### searchJiraIssuesUsingJql

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cloudId` | string | Yes | Atlassian Cloud instance ID |
| `jql` | string | Yes | JQL expression (e.g. `project = MAX AND status != Done`) |
| `maxResults` | number | No | Max issues per page (default 50, max 100) |
| `fields` | array | No | Fields to return (default: summary, description, status, issuetype, priority, created) |
| `nextPageToken` | string | No | Pagination cursor from previous response |
| `responseContentFormat` | string | No | Response content format: `"markdown"` or `"adf"` (default: ADF) |

> **Note:** Use this tool only when JQL syntax is specifically required. For general searches across Jira and Confluence, use the unified `search` tool instead.

### search

| Field | Details |
|-------|---------|
| **Purpose** | Unified search across Jira and Confluence |
| **Parameters** | General query string |
| **When to use** | For broad searches that are not JQL-specific |

---

## Jira — Transitions

### getTransitionsForJiraIssue

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cloudId` | string | Yes | Atlassian Cloud instance ID |
| `issueIdOrKey` | string | Yes | Issue to get transitions for |
| **Returns** | List of available transitions with `transitionId` and target status |

### transitionJiraIssue

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cloudId` | string | Yes | Atlassian Cloud instance ID |
| `issueIdOrKey` | string | Yes | Issue to transition |
| `transitionId` | string | Yes | Target transition ID (from `getTransitionsForJiraIssue`) |

---

## Jira — Comments and Worklogs

### addCommentToJiraIssue

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cloudId` | string | Yes | Atlassian Cloud instance ID |
| `issueIdOrKey` | string | Yes | Issue to comment on |
| `body` | string | Yes | Comment content in Markdown |
| `commentVisibility` | string | No | Restrict comment visibility |
| `contentFormat` | string | No | Content format: `"markdown"` or `"adf"` (default: ADF) |
| `responseContentFormat` | string | No | Response content format: `"markdown"` or `"adf"` (default: ADF) |

**Rho AIAS guidance:**
- Do NOT use Jira comments to publish local filesystem paths or machine-specific references.
- Comments remain valid for intentional tracker communications such as `/enrich` brief comments or `/publish` closure notices with remote knowledge links.
- For `/report`, comments are a fallback only when the tracker does not expose equivalent structured RCA fields.

### addWorklogToJiraIssue

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cloudId` | string | Yes | Atlassian Cloud instance ID |
| `issueIdOrKey` | string | Yes | Issue to log work on |
| `timeSpent` | string | Yes | Time spent (e.g. "2h", "30m") |
| `comment` | string | No | Optional worklog comment |
| `worklogId` | string | No | Worklog ID (for updates to existing worklogs) |
| `started` | string | No | Start date/time of the work |
| `visibility` | string | No | Restrict worklog visibility |
| `contentFormat` | string | No | Content format: `"markdown"` or `"adf"` (default: ADF) |

---

## Jira — Issue Links

### getIssueLinkTypes

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cloudId` | string | Yes | Atlassian Cloud instance ID |
| **Returns** | List of link types (e.g. "Blocks", "Duplicate", "Clones", "Relates") with inward/outward descriptions |

### createIssueLink

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cloudId` | string | Yes | Atlassian Cloud instance ID |
| `inwardIssue` | string | Yes | Issue key or ID for the inward side of the link |
| `outwardIssue` | string | Yes | Issue key or ID for the outward side of the link |
| `type` | string | Yes | Link type name (from `getIssueLinkTypes`) |
| `contentFormat` | string | No | Content format: `"markdown"` or `"adf"` (default: ADF) |

---

## Jira — Remote Links

### getJiraIssueRemoteIssueLinks

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cloudId` | string | Yes | Atlassian Cloud instance ID |
| `issueIdOrKey` | string | Yes | Issue to get remote links for |

---

## Confluence — Pages

### getConfluenceSpaces

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cloudId` | string | Yes | Atlassian Cloud instance ID |
| `ids` | array | No | Filter by space IDs |
| `keys` | array | No | Filter by space keys (e.g. `["ECOMM"]`) |
| `type` | string | No | Space type filter |
| `status` | string | No | Space status filter |
| `labels` | array | No | Filter by labels |
| `favourite` | boolean | No | Filter favourited spaces |
| `favoritedBy` | string | No | Filter by user who favourited |
| `expand` | string | No | Expand additional data |
| `start` | number | No | Pagination start index |
| `limit` | number | No | Results per page |

### getPagesInConfluenceSpace

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cloudId` | string | Yes | Atlassian Cloud instance ID |
| `spaceId` | string | Yes | Confluence space ID (resolve via `getConfluenceSpaces`) |
| `limit` | number | No | Results per page |
| `cursor` | string | No | Pagination cursor |
| `status` | string | No | Page status filter |
| `title` | string | No | Filter by page title |
| `sort` | string | No | Sort order |
| `contentFormat` | string | No | Content format: `"markdown"` or `"adf"` (default: ADF) |

### createConfluencePage

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cloudId` | string | Yes | Atlassian Cloud instance ID |
| `spaceId` | string | Yes | Confluence space ID (resolve via `getConfluenceSpaces`) |
| `title` | string | No | Page title |
| `body` | string | Yes | Page content |
| `parentId` | string | No | Parent page ID (for nested pages) |
| `contentFormat` | string | No | Content format: `"markdown"` or `"adf"` (default: ADF). Use `"markdown"` for rho-aias artifacts. |
| `isPrivate` | boolean | No | Whether the page is private |
| `subtype` | string | No | Page subtype |

### getConfluencePage

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cloudId` | string | Yes | Atlassian Cloud instance ID |
| `pageId` | string | Yes | Page ID |
| `contentFormat` | string | No | Content format: `"markdown"` or `"adf"` (default: ADF) |

### updateConfluencePage

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cloudId` | string | Yes | Atlassian Cloud instance ID |
| `pageId` | string | Yes | Page ID to update |
| `title` | string | No | Updated title |
| `body` | string | Yes | Updated content |
| `status` | string | No | Page status |
| `spaceId` | string | No | Space ID (for moving pages between spaces) |
| `parentId` | string | No | Parent page ID (for reparenting) |
| `contentFormat` | string | No | Content format: `"markdown"` or `"adf"` (default: ADF). Use `"markdown"` for rho-aias artifacts. |
| `versionMessage` | string | No | Version change message |
| `includeBody` | boolean | No | Whether to include body in response |

### getConfluencePageDescendants

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cloudId` | string | Yes | Atlassian Cloud instance ID |
| `pageId` | string | Yes | Parent page ID |
| `limit` | number | No | Results per page |
| `depth` | number | No | Depth of descendants to return |
| `cursor` | string | No | Pagination cursor |

### searchConfluenceUsingCql

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cloudId` | string | Yes | Atlassian Cloud instance ID |
| `cql` | string | Yes | CQL query string |

---

## Confluence — Comments

### getConfluencePageFooterComments

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cloudId` | string | Yes | Atlassian Cloud instance ID |
| `pageId` | string | Yes | Page ID |
| `contentFormat` | string | No | Content format: `"markdown"` or `"adf"` (default: ADF) |

### getConfluencePageInlineComments

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cloudId` | string | Yes | Atlassian Cloud instance ID |
| `pageId` | string | Yes | Page ID |
| `contentFormat` | string | No | Content format: `"markdown"` or `"adf"` (default: ADF) |

### createConfluenceFooterComment

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cloudId` | string | Yes | Atlassian Cloud instance ID |
| `pageId` | string | Yes | Page ID |
| `body` | string | Yes | Comment content in Markdown |
| `contentFormat` | string | No | Content format: `"markdown"` or `"adf"` (default: ADF) |

### createConfluenceInlineComment

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cloudId` | string | Yes | Atlassian Cloud instance ID |
| `pageId` | string | Yes | Page ID |
| `body` | string | Yes | Comment content in Markdown |
| `anchor` | string | No | Inline anchor position |
| `contentFormat` | string | No | Content format: `"markdown"` or `"adf"` (default: ADF) |

### getConfluenceCommentChildren

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cloudId` | string | Yes | Atlassian Cloud instance ID |
| `commentId` | string | Yes | Parent comment ID |
| `commentType` | string | Yes | Comment type (e.g. "inline", "footer") |
| `contentFormat` | string | No | Content format: `"markdown"` or `"adf"` (default: ADF) |

---

## Utilities

### fetch

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string | Yes | Atlassian Resource Identifier (ARI) — universal ID for Atlassian resources |

---

## Typical Call Flow

```
1. getAccessibleAtlassianResources          → cloudId
2. getVisibleJiraProjects(cloudId)          → projectKey
3. getJiraProjectIssueTypesMetadata(cloudId, projectKey)  → issueTypeName
4. lookupJiraAccountId(name or email)       → assignee_account_id (if needed)
5. createJiraIssue / getJiraIssue / etc.    → perform operation
```
