---
name: xcode-mcp
description: Build, test, preview, search, and manage files in Xcode projects via the Xcode Tools MCP. Use when the user asks to build, run tests, render previews, check build errors, search Apple docs, or manipulate files within an Xcode project structure.
---

# Xcode Tools MCP

## PURPOSE

Teach the agent how to interact with Xcode IDE via the Xcode Tools MCP server to build projects, run tests, render SwiftUI previews, inspect build logs and diagnostics, search Apple documentation, and manage files within the Xcode project structure.

---

## PREREQUISITES

### tabIdentifier

Almost every operation requires a `tabIdentifier` — the identifier of the Xcode workspace tab. Obtain it before any other call.

**Get tabIdentifier:**
1. Call `XcodeListWindows` (no parameters).
2. The response lists open Xcode windows with their workspace information and `tabIdentifier`.
3. Select the appropriate `tabIdentifier` for subsequent calls.

If this call fails or returns no windows: **abort** and ask the user to ensure Xcode is open with the target project.

### Xcode Project Paths

All file operations use **Xcode project organization paths**, not filesystem paths. Format: `ProjectName/Sources/MyFile.swift` (not `/Users/.../Sources/MyFile.swift`). Use `XcodeLS` to discover the project structure if paths are unknown.

---

## OPERATIONS

### Build Project

**When:** User asks to build, compile, or check if the project compiles.

**Call:** `BuildProject(tabIdentifier)`

**Returns:** Build result (success/failure), elapsed time, and list of errors with file paths and line numbers.

**Follow-up:** If the build fails, use `GetBuildLog` to get detailed error information.

---

### Get Build Log

**When:** User asks about build errors, warnings, or needs detailed build output. Also useful after a failed `BuildProject`.

**Call:** `GetBuildLog(tabIdentifier)`

**Optional filters:**
- `severity`: `"error"` | `"warning"` | `"remark"` (default: `"error"`)
- `pattern`: regex to match issue messages or task descriptions
- `glob`: glob to match file paths

---

### Run All Tests

**When:** User asks to run all tests or the full test suite.

**Call:** `RunAllTests(tabIdentifier)`

**Returns:** Test results (limited to 100, failures first) with a text file containing the full summary.

**Result interpretation:**
- Primary success indicator: `counts.failed == 0`. This is the authoritative signal.
- Per-result `state` field indicates individual test outcome (e.g., `"passed"`, `"failed"`).
- The `errors` field in individual results is **only present when the test has errors**. An absent `errors` field means the test passed — it is NOT an indicator that tests did not run.
- If `counts.total > 0` and `counts.failed == 0`, the test suite passed regardless of whether individual results contain an `errors` field.

---

### Run Specific Tests

**When:** User asks to run specific test classes or methods.

**Call sequence:**
1. `GetTestList(tabIdentifier)` → discover available tests and their identifiers
2. `RunSomeTests(tabIdentifier, tests)` → run the selected tests

**`tests` parameter:** Array of objects, each with:
- `targetName` (string): test target name
- `testIdentifier` (string): test identifier in XCTestIdentifier format

**Tip:** Use the `fullTestListPath` from `GetTestList` with grep to find specific tests by target, identifier, or file path.

---

### Get Test List

**When:** User asks what tests are available, or you need to discover test identifiers before running specific tests.

**Call:** `GetTestList(tabIdentifier)`

**Returns:** Up to 100 tests. Full list written to `fullTestListPath` in grep-compatible format. Search keys: `TEST_TARGET`, `TEST_IDENTIFIER`, `TEST_FILE_PATH`.

---

### Render SwiftUI Preview

**When:** User asks to see a preview, render a SwiftUI view, or check how a component looks.

**Call:** `RenderPreview(tabIdentifier, sourceFilePath)`

**Optional parameters:**
- `previewDefinitionIndexInFile` (integer): zero-based index of the `#Preview` or `PreviewProvider` in the file (default: 0)
- `timeout` (integer): seconds to wait (default: 120)

**Returns:** Path to the rendered preview snapshot image.

---

### Execute Code Snippet

**When:** User asks to run a code snippet in the context of a specific file (e.g., to test a function, print a value, validate behavior).

**Call:** `ExecuteSnippet(tabIdentifier, codeSnippet, sourceFilePath)`

**Parameters:**
- `codeSnippet` (string): Swift code to execute
- `sourceFilePath` (string): Xcode project path of the file whose context to use (the snippet has access to `fileprivate` declarations)
- `timeout` (integer, optional): seconds to wait (default: 120)

**Returns:** Console output from `print` statements in the snippet.

**Note:** Only available for source files in targets that compile apps, frameworks, libraries, or command-line executables.

---

### Search Apple Documentation

**When:** User asks about an Apple API, framework, or needs documentation reference.

**Call:** `DocumentationSearch(query)`

**Optional parameter:**
- `frameworks` (array of strings): limit search to specific frameworks

**Returns:** Relevant documents with title, URI, content, and match score.

**Note:** This is the only operation (besides `XcodeListWindows`) that does NOT require `tabIdentifier`.

---

### Check File Diagnostics

**When:** User asks about compiler errors/warnings in a specific file, or you need to verify a file compiles after editing.

**Call:** `XcodeRefreshCodeIssuesInFile(tabIdentifier, filePath)`

**Returns:** Formatted diagnostics with severity levels and messages.

---

### List Navigator Issues

**When:** User asks about all current issues in the project (build errors, package resolution problems, workspace config issues).

**Call:** `XcodeListNavigatorIssues(tabIdentifier)`

**Optional filters:**
- `severity`: `"error"` | `"warning"` | `"remark"` (default: `"error"`)
- `pattern`: regex to match issue messages
- `glob`: glob to match file paths

---

### File Operations

**Read file:** `XcodeRead(tabIdentifier, filePath)` — returns content with line numbers. Use `offset`/`limit` for large files.

**Write file:** `XcodeWrite(tabIdentifier, filePath, content)` — creates or overwrites. Auto-adds new files to the project structure.

**Edit file:** `XcodeUpdate(tabIdentifier, filePath, oldString, newString)` — string replacement. Use `replaceAll: true` for all occurrences.

**List files:** `XcodeLS(tabIdentifier, path)` — lists project structure. Recursive by default. Use `ignore` to filter.

**Find files:** `XcodeGlob(tabIdentifier, pattern)` — find files by wildcard pattern (e.g. `*.swift`, `**/*.json`).

**Search in files:** `XcodeGrep(tabIdentifier, pattern)` — regex search across project files. Supports `glob`, `type`, `outputMode`, context lines.

**Create directory:** `XcodeMakeDir(tabIdentifier, directoryPath)` — creates directory and group in project.

**Move/rename:** `XcodeMV(tabIdentifier, sourcePath, destinationPath)` — move or copy. Use `operation: "copy"` for copy.

**Delete:** `XcodeRM(tabIdentifier, path)` — removes from project. Use `deleteFiles: true` (default) to also trash the actual files. Use `recursive: true` for directories.

---

## REFERENCE

For complete parameter details, types, and return values for every tool, see [reference.md](reference.md).

---

## SAFETY RULES

**Read-only by default:**
- Reading files, listing structure, searching, getting build logs, getting test lists, checking diagnostics, listing issues, listing windows, searching docs: always allowed.
- Building, running tests, rendering previews, executing snippets: allowed (they don't modify source code, but they do compile/execute).
- Writing, updating, creating directories, moving, deleting files: **only when the user explicitly asks or when the active mode authorizes code modifications** (e.g., `@dev` with an explicit action verb).

**Abort on failure:**
- If `XcodeListWindows` fails or returns no windows: abort and ask the user to ensure Xcode is open.
- If any subsequent call fails (timeout, error, invalid tabIdentifier): abort the operation, report the error, and ask the user to verify Xcode state.

**Data integrity:**
- Never invent file paths, test names, or build results that the API did not return.
- File paths must use Xcode project organization format, not filesystem paths.
- When editing files, `oldString` must exist in the file; do not guess content.
