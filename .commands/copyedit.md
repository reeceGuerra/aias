# Copyedit (Document Quality Editing) — v2

## 1. Identity

**Command Type:** Operative — Procedural / Execution

You are performing **editorial copyediting** to improve the communicative quality of any document that contains natural language prose — excluding code and structured configuration files.

This command is responsible for analyzing and improving the textual quality of documents by applying editorial standards for adequacy, coherence, cohesion, intelligibility, clarity, and precision.

---

## 2. Invocation / Usage

Invocation:
- `/copyedit`
- `/copyedit <file-path>`
- `/copyedit --dry`
- `/copyedit <file-path> --dry`

Usage notes:
- By default, this command **modifies the document** by applying editorial improvements.
- `--dry` activates **dry-run mode** which only reports issues without modifying the file.
- The command detects document type by file extension and applies format-specific handling.
- If no file path is provided, the command must request it or use chat context to identify the target document.
- Common path: <resolved_tasks_dir>/<TASK_ID>/* (default: `~/.cursor/plans/`) — but any explicit path is accepted.

---

## 3. Inputs

This command may use **only** the following inputs:
- A document file explicitly provided by the user (path or content)
- Chat context explicitly provided by the user

### Supported formats (direct edit)

| Extension | Handling |
|-----------|----------|
| `.md` | Markdown documents — artifacts, documentation, contracts, plans, READMEs |
| `.txt` | Plain text documents |
| `.mdc` | Cursor rule files — preserve YAML frontmatter and structural headers, copyedit only the prose content within sections |

### Limited support (chat-only)

| Extension | Handling |
|-----------|----------|
| `.docx` | If content is pasted in chat, apply copyedit and return improved version in chat. Cannot modify the original file. |
| `.pages` | If content is pasted in chat, apply copyedit and return improved version in chat. Cannot modify the original file. |

### Excluded (reject with clear message)

**Code files:** `.swift`, `.kt`, `.java`, `.py`, `.js`, `.ts`, `.h`, `.m`, `.c`, `.cpp`, `.go`, `.rs`, `.rb`, `.sh`, `.zsh`, `.bash`, `.r`, `.sql`

**Structured data/config:** `.json`, `.yaml`, `.yml`, `.toml`, `.plist`, `.pbxproj`, `.storyboard`, `.xib`, `.env`, `.gitignore`, `.xcconfig`, `.entitlements`, `.strings`, `.properties`, `.gradle`, `.kts`, `.pro`

Rejection message: "This file type (`.<ext>`) is not supported by /copyedit. This command operates on documents, not code or configuration files."

Rules:
- All inputs must be explicit.
- If no document is provided, the command must request it before producing output.
- The command must read the document file content to perform copyediting.
- The command must respect the document's structure and template while improving textual quality.
- Do not change structure (headers, checkboxes, sections); only text.
- Do not remove information; only improve clarity, coherence, and precision.
- Confirm the target is a file and the path is agreed before overwriting.
- **Preserve domain-specific terminology and specialized vocabulary.** Copyedit prose quality (clarity, coherence, precision) without simplifying technical terms. A technical document benefits from editorial quality without losing terminological accuracy.
- **For `.mdc` files:** Treat YAML frontmatter (between `---` delimiters) as structural — do not modify. Apply copyedit only to the prose content within sections.

---

## 4. Output Contract (Format)

### Gate: Target Confirmation

**Type:** Confirmation
**Fires:** Before modifying the document (default mode only; does NOT fire in `--dry` mode).
**Skippable:** No.

**Context output:**
Present target summary in chat:
- File path (absolute)
- File type and handling mode
- Confirmation that the file exists and is writable

**AskQuestion:**
- **Runtime compatibility:** If `AskQuestion` is unavailable, use the Text Gate Protocol from `readme-commands.md` with the same prompt, option ids, labels, and `allow_multiple` semantics.
- **Prompt:** "Copyedit and overwrite <file-path>?"
- **Options:**
  - `proceed`: "Apply copyedits to the file"
  - `dry-run`: "Switch to dry-run — report issues only"
  - `cancel`: "Cancel — do not modify"
- **allow_multiple:** false

**On response:**
- `proceed` → Apply copyedits in place
- `dry-run` → Switch to dry-run output (no file modification)
- `cancel` → Abort. No changes made

**Anti-bypass:** Inherits Gate Invocation Protocol. No additional rules.

### Default Mode (Apply Changes)

FILE MODIFICATION CONTRACT (must follow)
- You MUST modify the document file **in place** (overwrite the original file).
- The modified document must maintain its original structure, template, and format.
- Only textual content is improved; structural elements (headers, sections, checkboxes) remain unchanged.
- The document must preserve all original information while improving clarity, coherence, and precision.

END-OF-RESPONSE CONFIRMATION (must follow)
- After modifying the document file, you MUST print a final line in the chat response (not in the file) exactly in this format:
  Copyedited document: <absolute_path>
- <absolute_path> must resolve to the fully expanded absolute path.

### Dry-Run Mode (`--dry`)

OUTPUT FORMAT (must follow)
- Output must be **raw, unstructured text** (no template structure, no formatted sections).
- Output must be presented directly in the chat response (not saved to a file).
- Output must list quality issues grouped by the six editorial dimensions.

---

## 5. Content Rules (Semantics)

- Output must be in **English**.
- Do **NOT** invent information or issues that do not exist.
- Use **ONLY** the provided document content to identify quality issues.
- When applying changes, preserve all original meaning and information.
- Improve clarity, coherence, and precision without altering the document's intent.
- Respect the document's original structure and template format.
- If a dimension has no issues, explicitly state that it meets quality standards.

---

## 6. Output Structure

### Default Mode (Apply Changes)

The command modifies the document by:
1. Analyzing the document across six editorial dimensions.
2. Identifying specific quality issues.
3. Applying improvements to enhance:
   - **Adequacy**: Adapting content to the communicative situation, audience, and context.
   - **Coherence**: Ensuring clear organization and structure with logically connected ideas and no contradictions.
   - **Cohesion**: Ensuring document parts are logically united and related.
   - **Intelligibility**: Making the document easily understandable and clear in meaning.
   - **Clarity**: Removing ambiguities and redundancies.
   - **Precision**: Ensuring content communicates exactly what is intended.
4. Preserving the document's structure, format, and all original information.
5. Writing the improved version back to the original file.

### Dry-Run Mode (`--dry`)

The output must list quality issues grouped by the six editorial dimensions (Adequacy, Coherence, Cohesion, Intelligibility, Clarity, Precision). For each dimension: if no issues, state "No issues identified"; if issues exist, list each issue as a specific, actionable item with location reference.

---

## 7. Non-Goals / Forbidden Actions

This command must **NOT**:
- Modify the document's structure, template, or format
- Remove or add sections, headers, or structural elements
- Change the document's intent or meaning
- Add information that was not in the original document
- Remove information from the original document
- Simplify or replace domain-specific technical terminology
- Modify YAML frontmatter in `.mdc` files
- Suggest alternative designs or implementations (in default mode)
- Execute commands or scripts unrelated to file editing
- Modify files other than the target document
- Attempt to edit code or structured configuration files
