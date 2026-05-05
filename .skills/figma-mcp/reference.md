# Figma MCP — Tool Reference

Complete parameter reference for all tools and resources available in the Figma MCP server.

---

## Authentication

### whoami

| Field | Details |
|-------|---------|
| **Purpose** | Get information about the authenticated Figma user |
| **Parameters** | None |
| **When to use** | When experiencing permission issues; verify the correct user is authenticated |

---

## Design and Context

### get_design_context

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `nodeId` | string | Yes | Node ID in the Figma document (e.g. `"123:456"` or `"123-456"`) |
| `fileKey` | string | Yes | Figma file key (extracted from URL) |
| `clientLanguages` | string | No | Comma-separated languages (e.g. `"swift"`, `"kotlin"`, `"html,css,typescript"`). Use `"unknown"` if not known. |
| `clientFrameworks` | string | No | Comma-separated frameworks (e.g. `"swiftui"`, `"jetpack-compose"`, `"react"`). Use `"unknown"` if not known. |
| `forceCode` | boolean | No | Force code return even for large outputs. Only set when user explicitly requests it. |
| `disableCodeConnect` | boolean | No | Disable Code Connect. Only set when user explicitly requests it. |

**Returns:** Code string + JSON of download URLs for referenced assets.

**URL extraction:**
- Standard: `https://figma.com/design/:fileKey/:fileName?node-id=:int1-:int2`
  - `fileKey` = segment after `/design/`
  - `nodeId` = `node-id` param with `-` replaced by `:` (e.g. `node-id=1-2` → `"1:2"`)
- Branch: `https://figma.com/design/:fileKey/branch/:branchKey/:fileName`
  - Use `branchKey` as `fileKey`

### get_screenshot

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `nodeId` | string | Yes | Node ID in the Figma document |
| `fileKey` | string | Yes | Figma file key |
| `clientLanguages` | string | No | Same as `get_design_context` |
| `clientFrameworks` | string | No | Same as `get_design_context` |

**Returns:** Screenshot image of the specified node.

### get_metadata

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `nodeId` | string | Yes | Node ID in the Figma document |
| `fileKey` | string | Yes | Figma file key |
| `clientLanguages` | string | No | Same as `get_design_context` |
| `clientFrameworks` | string | No | Same as `get_design_context` |

**Returns:** Metadata about the file or node (properties, structure, information).

### get_figjam

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `nodeId` | string | Yes | Node ID in the FigJam document |
| `fileKey` | string | Yes | Figma file key |
| `clientLanguages` | string | No | Same as `get_design_context` |
| `clientFrameworks` | string | No | Same as `get_design_context` |

**Returns:** FigJam board content (whiteboards, brainstorms, diagrams).

---

## Variables and Tokens

### get_variable_defs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `nodeId` | string | Yes | Node ID in the Figma document |
| `fileKey` | string | Yes | Figma file key |
| `clientLanguages` | string | No | Same as `get_design_context` |
| `clientFrameworks` | string | No | Same as `get_design_context` |

**Returns:** Design token and variable definitions.

---

## Code Connect

### get_code_connect_map

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `nodeId` | string | Yes | Node ID |
| `fileKey` | string | Yes | File key |
| `clientLanguages` | string | No | Same as `get_design_context` |
| `clientFrameworks` | string | No | Same as `get_design_context` |

**Returns:** Existing Code Connect mappings for the node.

### add_code_connect_map

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `nodeId` | string | Yes | Node ID |
| `fileKey` | string | Yes | File key |
| `clientLanguages` | string | No | Same as `get_design_context` |
| `clientFrameworks` | string | No | Same as `get_design_context` |

> **Write operation** — only call when the user explicitly requests it.

---

## Generation and Rules

### generate_diagram

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Short descriptive title for the diagram |
| `mermaidSyntax` | string | Yes | Mermaid.js code for the diagram |
| `userIntent` | string | No | Description of what the diagram should convey |
| `planKey` | string | No | Team/org key for destination FigJam file |
| `fileKey` | string | No | Key of an existing FigJam file to add the diagram to |
| `useArchitectureLayoutCode` | string | No | Mermaid code for software architecture layout |

> **Write operation** — only call when the user explicitly requests it. Supported: flowchart, decision tree, Gantt, sequence, state, ER diagrams only.

### create_design_system_rules

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `nodeId` | string | Yes | Node ID in the Figma document |
| `fileKey` | string | Yes | Figma file key |
| `clientLanguages` | string | No | Same as `get_design_context` |
| `clientFrameworks` | string | No | Same as `get_design_context` |

> **Write operation** — only call when the user explicitly requests it.

---

## Design System Discovery

### search_design_system

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Text query (e.g. `"primary button"`, `"brand-red"`) |
| `fileKey` | string | Yes | File key to determine which libraries to search |
| `includeComponents` | boolean | No | Include components (default: true) |
| `includeVariables` | boolean | No | Include variables (default: true) |
| `includeStyles` | boolean | No | Include styles (default: true) |
| `includeLibraryKeys` | array | No | Restrict to specific library keys |
| `disableCodeConnect` | boolean | No | Disable Code Connect enrichment |

### get_libraries

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `fileKey` | string | Yes | File key to get libraries for |
| `offset` | number | No | Pagination offset for `libraries_available_to_add` |

**Returns:** `{ subscribed: [...], libraries_available_to_add: [...] }`

---

## Canvas Write

### use_figma

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `fileKey` | string | Yes | Target Figma file key |
| `code` | string | Yes | JavaScript code using the Figma Plugin API (`figma` global) |
| `description` | string | Yes | Concise description of what the code does |
| `skillNames` | string | No | Comma-separated skill names being followed (e.g. `"figma-use"`) |

> **Write operation** — load the `figma-use` skill before calling. General-purpose Figma canvas write tool.

### upload_assets

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `fileKey` | string | Yes | Target Figma file key |
| `count` | number | No | Number of upload URLs to obtain (1–5, default 1) |
| `nodeId` | string | No | Set uploaded asset as fill on this existing node (only when `count: 1`) |
| `scaleMode` | string | No | Fill mode (`FILL`, `FIT`, `CROP`, `TILE`). Default: `FILL` |

**Usage:** Call with `count` → receive single-use upload URLs → POST raw bytes with correct `Content-Type`.

### create_new_file

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `fileName` | string | Yes | Name for the new file |
| `planKey` | string | Yes | Team/org key (obtain from `whoami`) |
| `editorType` | string | Yes | `"design"` for design file, `"figjam"` for FigJam board |
| `projectId` | string | No | Place file inside this project/folder ID |

### generate_figma_design

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `outputMode` | string | Yes | `"newFile"` or `"existingFile"` |
| `captureId` | string | No | Returned from initial call; pass to poll for completion |
| `fileName` | string | No | Name for new file (newFile mode only) |
| `planKey` | string | No | Team/org key (newFile mode only) |
| `fileKey` | string | No | Target file key (existingFile mode only) |
| `nodeId` | string | No | Target node in existing file (existingFile mode only) |

**Note:** May return `captureId` before completion. Re-call with `captureId` to poll.

---

## Code Connect (Extended)

### get_context_for_code_connect

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `nodeId` | string | Yes | Node ID of the component or component set |
| `fileKey` | string | Yes | Figma file key |
| `clientLanguages` | string | No | Same as `get_design_context` |
| `clientFrameworks` | string | No | Same as `get_design_context` |

**Returns:** Property definitions with types/variants + descendant tree. Use for building Code Connect template files manually.

### get_code_connect_suggestions

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `nodeId` | string | Yes | Node ID |
| `fileKey` | string | Yes | Figma file key |
| `clientLanguages` | string | No | Same as `get_design_context` |
| `clientFrameworks` | string | No | Same as `get_design_context` |
| `excludeMappingPrompt` | boolean | No | Exclude prompt text/images, return lightweight list only |

**Workflow:** call → review with user → call `send_code_connect_mappings` to save approved mappings.

### send_code_connect_mappings

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `nodeId` | string | Yes | Node ID |
| `fileKey` | string | Yes | Figma file key |
| `mappings` | array | Yes | Array of approved Code Connect mappings to save |
| `clientLanguages` | string | No | Same as `get_design_context` |
| `clientFrameworks` | string | No | Same as `get_design_context` |

> **Write operation** — use only after reviewing `get_code_connect_suggestions` output with the user.

---

## Available Documentation Resources

The Figma MCP exposes read-only documentation resources. Fetch these when you need implementation guidance for Code Connect or Figma integrations.

| Resource | Description |
|----------|-------------|
| `quickstart-guide` | Getting started with Figma MCP |
| `intro` | Introduction to Code Connect |
| `config-file` | Configuration file reference |
| `react` | React integration guide |
| `swiftui` | SwiftUI integration guide |
| `compose` | Jetpack Compose integration guide |
| `html` | HTML/CSS integration guide |
| `code-connect-ui-setup` | Code Connect UI setup |
| `code-connect-ui-github` | Code Connect GitHub integration |
| `templates` | Template reference (v1) |
| `templatesv2` | Template reference (v2) |
| `custom` | Custom parser reference |
| `no-parser` | Usage without a parser |
| `storybook` | Storybook integration |
| `ci-cd` | CI/CD integration guide |
| `github-permissions` | GitHub permissions reference |
| `common-issues` | Troubleshooting common issues |
| `comparing-cc` | Comparing Code Connect approaches |

---

## Typical Call Flow

```
1. Extract fileKey and nodeId from Figma URL
2. get_design_context(fileKey, nodeId, clientLanguages, clientFrameworks)  → code + assets
   OR
   get_screenshot(fileKey, nodeId)  → visual reference
   OR
   get_metadata(fileKey, nodeId)  → node properties
3. If permission error → whoami() to verify authenticated user
```
