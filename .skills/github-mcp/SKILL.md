---
name: github-mcp
description: Interact with GitHub repositories, issues, pull requests, branches, releases, and code via the GitHub MCP. Use when the user provides a GitHub URL, mentions a PR number, asks to create or review a PR, or needs repository information.
category: mcp
tested_against:
  mcp_server: user-GitHub@2026-05-05
  tools_count: 37
---

# GitHub MCP

## PURPOSE

Teach the agent how to interact with the GitHub MCP server to read and write repositories, issues, pull requests, branches, releases, and code using the correct call sequences, parameter extraction, and safety rules.

---

## PREREQUISITES

**Get authenticated user context:**
1. Call `get_me` (no parameters) before any other GitHub operation.
2. This returns the current user's identity and permissions.
3. Use this to understand scope and avoid permission errors.

If `get_me` fails: **abort** and ask the user to check GitHub MCP configuration.

---

## URL PARSING

Extract `owner` and `repo` from GitHub URLs:

**Repository URL:** `https://github.com/:owner/:repo`
**Issue URL:** `https://github.com/:owner/:repo/issues/:number`
**PR URL:** `https://github.com/:owner/:repo/pull/:number`
**File URL:** `https://github.com/:owner/:repo/blob/:ref/:path`

---

## TOOL SELECTION

**`list_*` tools** — for broad, simple retrieval with pagination:
- All issues, all PRs, all branches, all releases
- Basic filtering (state, labels)

**`search_*` tools** — for targeted queries with specific criteria:
- Issues with certain text, PRs by author, code containing functions
- Complex filters and keywords

**Sorting:** Use separate `sort` and `order` parameters. Do **not** include `sort:` syntax inside query strings.

**Pagination:** Always use pagination with batches of 5–10 items. Use `minimal_output: true` when full details are not needed.

---

## OPERATIONS

### Read Issue

**When:** User provides a GitHub issue number or URL.

**Call sequence:**
1. `get_me` → verify context
2. `issue_read(owner, repo, issueNumber)` → returns issue data

---

### List Issues

**When:** User asks to see issues in a repository.

**Call:**
`list_issues(owner, repo)`

**Optional parameters:**
- `state`: `"OPEN"` | `"CLOSED"`
- `labels` (array): filter by labels
- `orderBy`: `"CREATED_AT"` | `"UPDATED_AT"` | `"COMMENTS"`
- `direction`: `"ASC"` | `"DESC"`
- `perPage` (number): results per page (max 100)
- `after` (string): cursor for pagination

---

### Search Issues

**When:** User asks to find issues with specific criteria.

**Call:**
`search_issues(query)`

**Parameters:**
- `query` (string, required): search query using GitHub issue search syntax (e.g. `org:myorg label:bug state:open`)
- `owner`, `repo` (optional): scope to a specific repository
- `sort`, `order` (optional): sorting parameters (separate from query string)
- `page`, `perPage` (optional): pagination

---

### Create Issue

**When:** User **explicitly asks** to create a GitHub issue.

**Call sequence:**
1. `get_me` → verify context
2. `search_issues(...)` → check for duplicates first
3. `issue_write(owner, repo, title, body, ...)` → creates the issue

---

### Read Pull Request

**When:** User provides a PR number or URL and wants details, diff, or status.

**Call sequence:**
1. `get_me` → verify context
2. `pull_request_read(owner, repo, pullNumber)` → returns PR data

---

### List Pull Requests

**When:** User asks to see PRs in a repository.

**Call:**
`list_pull_requests(owner, repo)`

**Optional parameters:** Similar to `list_issues`.

---

### Search Pull Requests

**When:** User asks to find PRs with specific criteria.

**Call:**
`search_pull_requests(query)`

**Parameters:** Similar to `search_issues`.

---

### Create Pull Request

**When:** User **explicitly asks** to create a PR.

**Call sequence:**
1. `get_me` → verify context
2. Search for PR templates: look for `pull_request_template.md` or files in `.github/PULL_REQUEST_TEMPLATE/`
3. `create_pull_request(owner, repo, title, head, base, body, ...)` → creates the PR

**Required parameters:**
- `owner`, `repo`, `title`, `head` (branch with changes), `base` (target branch)

**Optional parameters:**
- `body` (string): description (use PR template if found)
- `draft` (boolean): create as draft
- `maintainer_can_modify` (boolean)

---

### Review Pull Request

**When:** User **explicitly asks** to submit a review.

**Call sequence (for complex reviews with line comments):**
1. `pull_request_review_write(method: "create", owner, repo, pullNumber)` → create pending review
2. `add_comment_to_pending_review(...)` → add line-specific comments (repeat as needed)
3. `pull_request_review_write(method: "submit_pending", owner, repo, pullNumber, event, body)` → submit the review

**Event types:** `"APPROVE"` | `"REQUEST_CHANGES"` | `"COMMENT"`

---

### Read File Contents

**When:** User asks about a file in a repository.

**Call:**
`get_file_contents(owner, repo, path)`

**Optional parameter:**
- `ref` (string): branch or tag (defaults to default branch)

---

### Create or Update File

**When:** User **explicitly asks** to create or modify a file in a repository.

**Call:**
`create_or_update_file(owner, repo, path, message, content, branch)`

---

### Search Code

**When:** User asks to find code across repositories.

**Call:**
`search_code(query)`

---

### Branches

**List:** `list_branches(owner, repo)`
**Create:** `create_branch(owner, repo, branch, sha)` — only when user **explicitly asks**.

---

### Commits

**List:** `list_commits(owner, repo)` — optional: `sha` (branch), `path` (file)
**Get:** `get_commit(owner, repo, sha)` — returns commit details and diff

---

### Releases and Tags

**List releases:** `list_releases(owner, repo)`
**Latest release:** `get_latest_release(owner, repo)`
**Release by tag:** `get_release_by_tag(owner, repo, tag)`
**List tags:** `list_tags(owner, repo)`
**Get tag:** `get_tag(owner, repo, tag)`

---

### Update Pull Request

**When:** User **explicitly asks** to update an existing PR's title, body, state, or base branch.

**Call:**
`update_pull_request(owner, repo, pullNumber, ...)`

**Optional parameters:**
- `title` (string): new PR title
- `body` (string): new description
- `state` (string): `"open"` | `"closed"`
- `base` (string): new base branch
- `draft` (boolean): mark as draft or ready for review
- `maintainer_can_modify` (boolean)
- `reviewers` (array): GitHub usernames to request reviews from

---

### Update Pull Request Branch

**When:** User **explicitly asks** to sync a PR branch with the latest changes from its base branch (rebases the PR head).

**Call:**
`update_pull_request_branch(owner, repo, pullNumber)`

**Optional parameter:**
- `expectedHeadSha` (string): expected SHA of the PR's HEAD ref (for safety check)

---

### Merge Pull Request

**When:** User **explicitly asks** to merge a pull request.

**Call:**
`merge_pull_request(owner, repo, pullNumber, ...)`

**Optional parameters:**
- `merge_method` (string): `"merge"` | `"squash"` | `"rebase"`
- `commit_title` (string): title for the merge commit
- `commit_message` (string): additional detail for the merge commit

---

### Push Multiple Files

**When:** User **explicitly asks** to push several files to a repository in a single commit.

**Call:**
`push_files(owner, repo, branch, files, message)`

**Required parameters:**
- `branch` (string): target branch
- `files` (array): array of `{ path: string, content: string }` objects
- `message` (string): commit message

---

### Add Comment to Issue or PR

**When:** User **explicitly asks** to add a comment to an issue or pull request.

**Call:**
`add_issue_comment(owner, repo, issue_number, body)`

**Note:** Works for both issues and PRs — pass the PR number as `issue_number` for PRs.

---

### Sub-Issue

**When:** User **explicitly asks** to create a parent-child relationship between issues.

**Call:**
`sub_issue_write(owner, repo, issue_number, method, sub_issue_id, ...)`

**Required parameters:**
- `issue_number` (number): parent issue number
- `method` (string): `"add"` | `"remove"` | `"reprioritize"`
- `sub_issue_id` (number): ID of the sub-issue (not the issue number)

**Optional parameters:**
- `after_id` / `before_id` (number): ordering relative to other sub-issues
- `replace_parent` (boolean): replace the sub-issue's current parent (use with `"add"`)

---

### Search Users

**When:** User needs to find GitHub users by username, name, location, or other profile attributes.

**Call:**
`search_users(query, ...)`

**Required parameter:**
- `query` (string): search query (e.g. `"john smith"`, `"location:seattle"`, `"followers:>100"`)

**Optional parameters:** `sort`, `order`, `page`, `perPage`

---

### Search Repositories

**When:** User needs to find repositories by name, description, topics, or other metadata.

**Call:**
`search_repositories(query)`

---

### Labels

**Get label:** `get_label(owner, repo, name)` — retrieve a specific label's details.

---

### Create Repository

**When:** User **explicitly asks** to create a new GitHub repository.

**Call:**
`create_repository(name, ...)`

**Required parameter:**
- `name` (string): repository name

**Optional parameters:**
- `organization` (string): create in an org instead of personal account
- `description` (string)
- `private` (boolean)
- `autoInit` (boolean): initialize with a README

---

### Fork Repository

**When:** User **explicitly asks** to fork a repository.

**Call:**
`fork_repository(owner, repo, ...)`

**Optional parameter:**
- `organization` (string): fork into an organization instead of personal account

---

### Delete File

**When:** User **explicitly asks** to delete a file from a repository.

**Call:**
`delete_file(owner, repo, path, message, branch)`

---

### Copilot — Request Review / Assign to Issue

**When:** User asks to get automated Copilot feedback on a PR, or to assign Copilot to resolve an issue.

**Request Copilot PR review:**
`request_copilot_review(owner, repo, pullNumber)` — requests automated feedback before a human review.

**Assign Copilot to resolve an issue:**
`assign_copilot_to_issue(owner, repo, issue_number, ...)` — Copilot will attempt to open a PR with source code changes to resolve the issue.

**Optional parameters for `assign_copilot_to_issue`:**
- `base_ref` (string): branch for Copilot to start from (defaults to default branch)
- `custom_instructions` (string): additional guidance beyond the issue body

---

## REFERENCE

For complete parameter details, types, and return values for every tool, see [reference.md](reference.md).

---

## SAFETY RULES

**Read-only by default:**
- Reading issues, PRs, files, branches, commits, releases, tags, and searching: always allowed.
- Creating/editing issues, creating PRs, submitting reviews, creating branches, creating/updating/deleting files: **only when the user explicitly asks**. Never perform write operations autonomously.

**Abort on failure:**
- If `get_me` fails: abort and ask the user to check GitHub MCP configuration.
- If any subsequent call fails (404, permission denied, timeout): abort the operation, report the error, and ask the user to verify repository access and permissions.

**Data integrity:**
- Never invent commit SHAs, PR numbers, issue content, or file contents.
- If a field is missing from the response, report it as unknown.
- When creating PRs, always search for and use PR templates when available.

