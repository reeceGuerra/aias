---
name: figma-mcp
description: Get design context, screenshots, and metadata from Figma via the Figma MCP. Use when the user provides a Figma URL, mentions a Figma file or node, or asks to reference a design.
category: mcp
tested_against:
  mcp_server: user-Figma@2026-05-05
  tools_count: 19
---

# Figma MCP

## PURPOSE

Teach the agent how to interact with the Figma MCP server to obtain design context, screenshots, metadata, and Code Connect maps using the correct parameter extraction and call sequences.

---

## PREREQUISITES

No preliminary authentication call is required. Figma MCP authenticates via the configured token. If permission issues arise, call `whoami` to verify the authenticated user.

---

## URL PARSING

Most Figma operations require `fileKey` and `nodeId`. Extract them from URLs:

**Standard URL format:**
```
https://figma.com/design/:fileKey/:fileName?node-id=:int1-:int2
```
- `fileKey`: the segment after `/design/` (e.g. `pqrs` from `.../design/pqrs/ExampleFile?...`)
- `nodeId`: from `node-id` query parameter, replace `-` with `:` (e.g. `node-id=1-2` → `nodeId = "1:2"`)

**Branch URL format:**
```
https://figma.com/design/:fileKey/branch/:branchKey/:fileName
```
- Use `branchKey` as `fileKey` (not the original `fileKey`).
- Extract `nodeId` from the query parameter as above.

If the user provides a `nodeId` directly (e.g. `"123:456"` or `"123-456"`), normalize it to the colon format (`"123:456"`).

---

## OPERATIONS

### Get Design Context (Code Generation)

**When:** User asks to generate UI code from a Figma design, or wants implementation details for a component.

**Call:**
`get_design_context(fileKey, nodeId)`

**Required parameters:**
- `fileKey` (string): file key extracted from URL
- `nodeId` (string): node ID in colon format (e.g. `"123:456"`)

**Optional parameters:**
- `clientLanguages` (string): comma-separated languages (e.g. `"swift"`, `"kotlin"`, `"html,css,typescript"`). Use `"unknown"` if not known.
- `clientFrameworks` (string): comma-separated frameworks (e.g. `"swiftui"`, `"jetpack-compose"`, `"react"`). Use `"unknown"` if not known.
- `forceCode` (boolean): force code return even for large outputs. Only set when the user explicitly requests it.
- `disableCodeConnect` (boolean): disable Code Connect. Only set when the user explicitly requests it.

**Response:** Contains a code string and a JSON of download URLs for referenced assets.

---

### Get Screenshot

**When:** User asks for a visual reference or screenshot of a Figma component or screen.

**Call:**
`get_screenshot(fileKey, nodeId)`

**Required parameters:**
- `fileKey` (string)
- `nodeId` (string)

**Optional parameters:**
- `clientLanguages`, `clientFrameworks` (same as above)

---

### Get Metadata

**When:** User asks about properties, structure, or information of a Figma file or node without needing code.

**Call:**
`get_metadata(fileKey, nodeId)`

**Parameters:** Same as `get_design_context`.

---

### Get Variable Definitions

**When:** User asks about design tokens, variables, or design system values.

**Call:**
`get_variable_defs(fileKey, nodeId)`

**Parameters:** Same as `get_design_context`.

---

### Code Connect

**Get map:**
`get_code_connect_map(fileKey, nodeId)` — retrieve existing Code Connect mappings.

**Add map:**
`add_code_connect_map(fileKey, nodeId)` — add new Code Connect mappings.

**Note:** `add_code_connect_map` is a write operation — only call when the user explicitly requests it.

---

### Get FigJam Content

**When:** User asks about FigJam boards (whiteboards, brainstorms, diagrams).

**Call:**
`get_figjam(fileKey, nodeId)`

**Parameters:** Same as `get_design_context`.

---

### Design System Rules

**When:** User asks to create or manage design system rules.

**Call:**
`create_design_system_rules(fileKey, nodeId)`

**Note:** This is a write operation — only call when the user explicitly requests it.

---

### Search Design System

**When:** User needs to find specific components, variables (e.g. color tokens, spacing), or styles from design libraries.

**Call:**
`search_design_system(query, fileKey)`

**Required parameters:**
- `query` (string): text search (e.g. `"primary button"`, `"brand-red"`)
- `fileKey` (string): file key to determine which libraries to search

**Optional parameters:**
- `includeComponents` (boolean): default true
- `includeVariables` (boolean): default true
- `includeStyles` (boolean): default true
- `includeLibraryKeys` (array): restrict to specific library keys
- `disableCodeConnect` (boolean): disable Code Connect enrichment

---

### Get Libraries

**When:** Need to discover which design libraries are subscribed to a Figma file, or which libraries are available to add.

**Call:**
`get_libraries(fileKey)`

**Returns:** Two lists — libraries currently added to the file, and libraries available to add (community UI kits + organization libraries). Organization libraries list is paginated via `offset`.

---

### Generate Diagram (FigJam)

**When:** User asks to create a flowchart, decision tree, Gantt chart, sequence diagram, state diagram, or entity relationship diagram. Output is created in FigJam.

**Call:**
`generate_diagram(name, mermaidSyntax, ...)`

**Required parameters:**
- `name` (string): short, descriptive title for the diagram
- `mermaidSyntax` (string): valid Mermaid.js code for the diagram

**Optional parameters:**
- `planKey` (string): team/org key for the destination FigJam file
- `fileKey` (string): key of an existing FigJam file to add the diagram to
- `userIntent` (string): natural language description of what the diagram should convey

**Note:** Write operation — only call when the user explicitly requests it. Supported diagram types: flowchart, decision tree, Gantt, sequence, state, ER. NOT supported: class diagrams, timelines, Venn diagrams.

---

### Write to Figma Canvas (`use_figma`)

**When:** User asks to create, edit, delete, or inspect Figma objects directly (frames, components, variants, variables, styles, text, images, etc.).

**IMPORTANT:** You MUST load the `figma-use` skill **before** calling this tool. Never call `use_figma` without loading that skill first.

**Call:**
`use_figma(fileKey, code, description, ...)`

**Required parameters:**
- `fileKey` (string): target Figma file key
- `code` (string): JavaScript code using the Figma Plugin API (`figma` global)
- `description` (string): concise description of what the code does

**Optional parameters:**
- `skillNames` (string): comma-separated skill names being followed (e.g. `"figma-use"`)

**Note:** This is the general-purpose write tool for Figma canvas operations. Load the `figma-use` skill first for correct API usage patterns.

---

### Generate Figma Design from Web Page

**When:** User wants to capture a web page (live URL or localhost) and import it into Figma as a design.

**Call:**
`generate_figma_design(outputMode, ...)`

**Required parameters:**
- `outputMode` (string): `"newFile"` (create a new Figma file) or `"existingFile"` (add to existing)

**Optional parameters (for `newFile`):**
- `fileName` (string): name for the new Figma file
- `planKey` (string): team/org key for destination

**Optional parameters (for `existingFile`):**
- `fileKey` (string): target file key
- `nodeId` (string): node where design should be added

**Polling:** The tool may return a `captureId` before completion. If so, call it again with `captureId` to poll for the result.

**Note:** Write operation — only call when user explicitly requests it.

---

### Upload Assets

**When:** User wants to upload images or other assets into a Figma file (e.g. to set as a fill on an existing node or create new image frames).

**Call:**
`upload_assets(fileKey, count, ...)`

**Required parameters:**
- `fileKey` (string): target Figma file key
- `count` (number): number of upload URLs to obtain (1–5, default 1)

**Returns:** Single-use upload URLs. POST raw asset bytes to each URL with the correct `Content-Type` header (e.g. `image/png`, `image/jpeg`).

**Optional parameters:**
- `nodeId` (string): if provided, sets the uploaded asset as a fill on that existing node (only when `count: 1`)
- `scaleMode` (string): fill mode — default: `FILL`

**Note:** Write operation — only call when user explicitly requests it.

---

### Create New Figma File

**When:** User asks to create a new blank Figma design file or FigJam board.

**IMPORTANT:** Load the `figma-create-new-file` skill before calling this tool if it exists.

**Call:**
`create_new_file(fileName, planKey, editorType, ...)`

**Required parameters:**
- `fileName` (string): name for the new file
- `planKey` (string): team/org key — obtain from `whoami`
- `editorType` (string): `"design"` for a design file, `"figjam"` for a FigJam board

**Optional parameters:**
- `projectId` (string): place the file inside a specific project (folder)

**Note:** Write operation — only call when user explicitly requests it.

---

### Code Connect — Get Suggestions and Send Mappings

**When:** User wants to set up Code Connect mappings using AI-suggested strategies.

**Workflow:**
1. `get_code_connect_suggestions(nodeId, fileKey, ...)` → get AI-suggested strategy (review with user before saving)
2. `send_code_connect_mappings(nodeId, fileKey, mappings, ...)` → save approved mappings in bulk

**Note:** `get_context_for_code_connect(nodeId, fileKey)` provides structured component metadata (properties, variants, descendant tree) for building Code Connect template files manually — use before `send_code_connect_mappings` when you need the full component structure.

---

## AVAILABLE RESOURCES

The Figma MCP also exposes read-only documentation resources that can be fetched:
- `quickstart-guide`, `intro`, `config-file`
- `react`, `swiftui`, `compose`, `html`
- `code-connect-ui-setup`, `code-connect-ui-github`
- `templates`, `templatesv2`, `custom`, `no-parser`
- `storybook`, `ci-cd`, `github-permissions`
- `common-issues`, `comparing-cc`

Fetch these when you need implementation guidance for Code Connect or Figma integrations.

---

## REFERENCE

For complete parameter details, types, and return values for every tool, see [reference.md](reference.md).

---

## SAFETY RULES

**Read-only by default:**
- `get_design_context`, `get_screenshot`, `get_metadata`, `get_variable_defs`, `get_figjam`, `get_code_connect_map`, `whoami`: always allowed.
- `add_code_connect_map`, `create_design_system_rules`, `generate_diagram`: **only when the user explicitly asks**.

**Abort on failure:**
- If Figma returns a permission error: call `whoami` to verify the authenticated user, report the issue, and ask the user to check access.
- If the URL cannot be parsed (missing `fileKey` or `nodeId`): ask the user to provide a valid Figma URL or explicit IDs.
- If the MCP returns an error or timeout: abort and report the error.

**Data integrity:**
- Never invent design data, measurements, or colors that the API did not return.
- If a response is empty or truncated, report it as such.

