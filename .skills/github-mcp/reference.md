# GitHub MCP — Tool Reference

Complete parameter reference for all tools available in the GitHub MCP server.

---

## Tool Selection Guide

| Category | When to use | Examples |
|----------|-------------|---------|
| **`list_*` tools** | Broad retrieval with pagination and basic filtering | All issues, all PRs, all branches |
| **`search_*` tools** | Targeted queries with specific criteria, keywords, or complex filters | Issues with certain text, PRs by author, code containing functions |

**Sorting:** Use separate `sort` and `order` parameters. Do **not** include `sort:` syntax inside query strings.

**Pagination:** Use batches of 5–10 items. Set `minimal_output: true` when full details are not needed.

---

## Authentication

### get_me

| Field | Details |
|-------|---------|
| **Purpose** | Get details of the authenticated GitHub user |
| **Parameters** | None |
| **When to use** | Always call first; also when a request is about the user's own profile or when lacking context for other calls |

---

## Issues

### list_issues

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `owner` | string | Yes | Repository owner |
| `repo` | string | Yes | Repository name |
| `state` | enum | No | `"OPEN"` \| `"CLOSED"` (default: both) |
| `labels` | array | No | Filter by label names |
| `orderBy` | enum | No | `"CREATED_AT"` \| `"UPDATED_AT"` \| `"COMMENTS"` |
| `direction` | enum | No | `"ASC"` \| `"DESC"` (requires `orderBy`) |
| `perPage` | number | No | Results per page (min 1, max 100) |
| `after` | string | No | Cursor for pagination (use `endCursor` from previous `PageInfo`) |
| `since` | string | No | Filter by date (ISO 8601 timestamp) |

### search_issues

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Search query using GitHub issue search syntax (scope `is:issue` already applied) |
| `owner` | string | No | Scope to repository owner |
| `repo` | string | No | Scope to repository name |
| `sort` | enum | No | `"comments"`, `"reactions"`, `"reactions-+1"`, `"reactions--1"`, `"reactions-smile"`, `"reactions-thinking_face"`, `"reactions-heart"`, `"reactions-tada"`, `"interactions"`, `"created"`, `"updated"` |
| `order` | enum | No | `"asc"` \| `"desc"` |
| `page` | number | No | Page number (min 1) |
| `perPage` | number | No | Results per page (min 1, max 100) |

### issue_read

| Field | Details |
|-------|---------|
| **Purpose** | Read a single issue by number |
| **Key parameters** | `owner`, `repo`, issue number |

### issue_write

| Field | Details |
|-------|---------|
| **Purpose** | Create or update an issue |
| **Notes** | Check `list_issue_types` for organizations. Search before creating to avoid duplicates. Set `state_reason` when closing. |

---

## Pull Requests

### list_pull_requests

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `owner` | string | Yes | Repository owner |
| `repo` | string | Yes | Repository name |
| Other parameters | — | No | Similar to `list_issues` (state, pagination, ordering) |

### search_pull_requests

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Search query using GitHub PR search syntax |
| Other parameters | — | No | Similar to `search_issues` (owner, repo, sort, order, pagination) |

### create_pull_request

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `owner` | string | Yes | Repository owner |
| `repo` | string | Yes | Repository name |
| `title` | string | Yes | PR title |
| `head` | string | Yes | Branch containing changes |
| `base` | string | Yes | Target branch for merge |
| `body` | string | No | PR description (use PR template if available) |
| `draft` | boolean | No | Create as draft PR |
| `maintainer_can_modify` | boolean | No | Allow maintainer edits |

> **Note:** Before creating, search for PR templates (`pull_request_template.md` or `.github/PULL_REQUEST_TEMPLATE/` directory) and use the template content for the body.

### pull_request_review_write

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `method` | enum | Yes | `"create"` \| `"submit_pending"` \| `"delete_pending"` |
| `owner` | string | Yes | Repository owner |
| `repo` | string | Yes | Repository name |
| `pullNumber` | number | Yes | PR number |
| `body` | string | No | Review comment text |
| `event` | enum | No | `"APPROVE"` \| `"REQUEST_CHANGES"` \| `"COMMENT"` (required for submit) |
| `commitID` | string | No | SHA of commit to review |

**Review workflow (complex reviews with line comments):**
1. `pull_request_review_write(method: "create")` → create pending review
2. `add_comment_to_pending_review(...)` → add line-specific comments (repeat)
3. `pull_request_review_write(method: "submit_pending", event: ...)` → submit

### add_comment_to_pending_review

| Field | Details |
|-------|---------|
| **Purpose** | Add line-specific comments to a pending review |
| **Prerequisites** | A pending review must exist (created with `method: "create"`) |

---

## Repositories and Code

### search_code

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Search query using GitHub code search syntax |

### search_repositories

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Search query |

### get_file_contents

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `owner` | string | Yes | Repository owner |
| `repo` | string | Yes | Repository name |
| `path` | string | Yes | File path within the repository |
| `ref` | string | No | Branch or tag (defaults to default branch) |

### create_or_update_file

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `owner` | string | Yes | Repository owner |
| `repo` | string | Yes | Repository name |
| `path` | string | Yes | File path |
| `message` | string | Yes | Commit message |
| `content` | string | Yes | File content |
| `branch` | string | Yes | Target branch |

> **Write operation** — only when the user explicitly requests it.

### delete_file

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `owner` | string | Yes | Repository owner |
| `repo` | string | Yes | Repository name |
| `path` | string | Yes | File path |
| `message` | string | Yes | Commit message |
| `branch` | string | Yes | Target branch |

> **Write operation** — only when the user explicitly requests it.

---

## Branches

### list_branches

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `owner` | string | Yes | Repository owner |
| `repo` | string | Yes | Repository name |

### create_branch

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `owner` | string | Yes | Repository owner |
| `repo` | string | Yes | Repository name |
| `branch` | string | Yes | New branch name |
| `sha` | string | Yes | Base commit SHA |

> **Write operation** — only when the user explicitly requests it.

---

## Commits

### list_commits

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `owner` | string | Yes | Repository owner |
| `repo` | string | Yes | Repository name |
| `sha` | string | No | Branch name or commit SHA (defaults to default branch) |
| `path` | string | No | Filter commits that touch this file path |

### get_commit

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `owner` | string | Yes | Repository owner |
| `repo` | string | Yes | Repository name |
| `sha` | string | Yes | Commit SHA |

**Returns:** Commit details including diff.

---

## Releases

### list_releases

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `owner` | string | Yes | Repository owner |
| `repo` | string | Yes | Repository name |

### get_latest_release

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `owner` | string | Yes | Repository owner |
| `repo` | string | Yes | Repository name |

### get_release_by_tag

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `owner` | string | Yes | Repository owner |
| `repo` | string | Yes | Repository name |
| `tag` | string | Yes | Release tag name |

---

## Tags

### list_tags

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `owner` | string | Yes | Repository owner |
| `repo` | string | Yes | Repository name |

### get_tag

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `owner` | string | Yes | Repository owner |
| `repo` | string | Yes | Repository name |
| `tag` | string | Yes | Tag name |

---

## Pull Request Management (Extended)

### update_pull_request

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `owner` | string | Yes | Repository owner |
| `repo` | string | Yes | Repository name |
| `pullNumber` | number | Yes | PR number to update |
| `title` | string | No | New title |
| `body` | string | No | New description |
| `state` | enum | No | `"open"` \| `"closed"` |
| `base` | string | No | New base branch |
| `draft` | boolean | No | Mark as draft or ready for review |
| `maintainer_can_modify` | boolean | No | Allow maintainer edits |
| `reviewers` | array | No | GitHub usernames to request reviews from |

### update_pull_request_branch

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `owner` | string | Yes | Repository owner |
| `repo` | string | Yes | Repository name |
| `pullNumber` | number | Yes | PR number |
| `expectedHeadSha` | string | No | Expected SHA of the PR's HEAD (safety check) |

### merge_pull_request

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `owner` | string | Yes | Repository owner |
| `repo` | string | Yes | Repository name |
| `pullNumber` | number | Yes | PR number |
| `merge_method` | enum | No | `"merge"` \| `"squash"` \| `"rebase"` |
| `commit_title` | string | No | Merge commit title |
| `commit_message` | string | No | Additional merge commit detail |

### request_copilot_review

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `owner` | string | Yes | Repository owner |
| `repo` | string | Yes | Repository name |
| `pullNumber` | number | Yes | PR number |

---

## Issues (Extended)

### add_issue_comment

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `owner` | string | Yes | Repository owner |
| `repo` | string | Yes | Repository name |
| `issue_number` | number | Yes | Issue or PR number |
| `body` | string | Yes | Comment content (Markdown) |

### sub_issue_write

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `owner` | string | Yes | Repository owner |
| `repo` | string | Yes | Repository name |
| `issue_number` | number | Yes | Parent issue number |
| `method` | enum | Yes | `"add"` \| `"remove"` \| `"reprioritize"` |
| `sub_issue_id` | number | Yes | ID of the sub-issue (not the issue number) |
| `after_id` | number | No | Prioritize after this sub-issue ID |
| `before_id` | number | No | Prioritize before this sub-issue ID |
| `replace_parent` | boolean | No | Replace existing parent (use with `"add"`) |

### assign_copilot_to_issue

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `owner` | string | Yes | Repository owner |
| `repo` | string | Yes | Repository name |
| `issue_number` | number | Yes | Issue number |
| `base_ref` | string | No | Branch for Copilot to start from |
| `custom_instructions` | string | No | Additional guidance beyond the issue body |

---

## Repository Management

### create_repository

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Repository name |
| `organization` | string | No | Create in an org instead of personal account |
| `description` | string | No | Repository description |
| `private` | boolean | No | Private repository (default: false) |
| `autoInit` | boolean | No | Initialize with README |

### fork_repository

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `owner` | string | Yes | Repository owner |
| `repo` | string | Yes | Repository name |
| `organization` | string | No | Fork into this organization |

### push_files

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `owner` | string | Yes | Repository owner |
| `repo` | string | Yes | Repository name |
| `branch` | string | Yes | Target branch |
| `files` | array | Yes | Array of `{ path: string, content: string }` objects |
| `message` | string | Yes | Commit message |

---

## Labels and Users

### get_label

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `owner` | string | Yes | Repository owner |
| `repo` | string | Yes | Repository name |
| `name` | string | Yes | Label name |

### search_users

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | User search query (e.g. `"john smith"`, `"location:seattle"`) |
| `sort` | string | No | Sort by `"followers"`, `"repositories"`, or `"joined"` |
| `order` | enum | No | `"asc"` \| `"desc"` |
| `page` | number | No | Page number |
| `perPage` | number | No | Results per page (max 100) |

---

## Typical Call Flows

### Read issue or PR
```
1. get_me                              → verify context
2. issue_read / pull_request_read      → get data
```

### Create PR
```
1. get_me                              → verify context
2. Search for PR templates             → pull_request_template.md or .github/PULL_REQUEST_TEMPLATE/
3. create_pull_request(owner, repo, title, head, base, body)
```

### Submit complex review
```
1. get_me                              → verify context
2. pull_request_review_write(method: "create")       → pending review
3. add_comment_to_pending_review(...)                 → line comments (repeat)
4. pull_request_review_write(method: "submit_pending", event: "REQUEST_CHANGES")
```
