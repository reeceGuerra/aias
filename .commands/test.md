# Test (Run Project Tests) — v1

## 1. Identity

**Command Type:** Operative — Procedural / Execution

You are **running tests** for a configured project via the `max-test` script.
This command is responsible for resolving project configuration from `projects.json`, determining the test strategy (swiftpm or xcodebuild), constructing the CLI invocation, executing `max-test`, and presenting an execution summary.

---

## 2. Invocation / Usage

Invocation:
- `/test`
- `/test <projectAlias>`
- `/test <projectAlias> [flags]`

Examples:
```
/test                                         → defaults from projects.json
/test rdsnetworking                           → explicit project alias
/test -p rdsnetworking                        → same, with flag
/test mobilemax -s iphone16pm                 → explicit simulator for xcodebuild
/test --dry-run                               → show resolved command, do not execute
/test mobilemax -v                            → verbose output
```

Flags:
- `-p, --project <alias>` — project alias (default: `defaults.project` from `projects.json`)
- `-s, --simulator <alias>` — simulator alias for xcodebuild tests (default: `defaults.simulator`)
- `-v, --verbose` — verbose diagnostics
- `--dry-run` — print resolved command without executing
- `-h, --help` — show usage

Usage notes:
- This command may be invoked directly (no preceding mode required).
- When used with `@tooling` mode, the mode provides reasoning; this command handles execution.
- Positional `<projectAlias>` is equivalent to `-p <alias>`.
- The test strategy is determined automatically from the project's `kind` and optional `test.mode` override in `projects.json`.

---

## 3. Inputs

This command may use **only** the following inputs:
- Chat context explicitly provided by the user (project alias, flags)
- Repository configuration from `${HOME}/.cursor/projects.json`

Rules:
- All inputs MUST be explicit or derivable from `projects.json` defaults.
- If the resolved project alias does not exist in `.projects`, STOP and list available projects.
- The command does NOT validate whether the project has tests; that is `max-test`'s responsibility.

---

## 4. Output Contract (Format)

- The response MUST be rendered as **plain Markdown** in chat (not inside a code block, not written to a file).
- The output MUST follow the Execution Summary templates defined in section 6.
- On `--dry-run`, show the resolved command without executing.

---

## 5. Content Rules (Semantics)

- Output MUST be in **English**.
- Do **NOT** invent information not present in the script output.
- Always include: Status, Project (alias + kind), Strategy, Command executed.
- On failure: include test failure details if parseable from output, otherwise show last 10 lines of raw output.
- If the output contains identifiable test names (e.g., `testLoginSuccess`), list them under Failures.

---

## 6. Output Structure (Template)

### On success (exit 0):

```markdown
## Test Summary

- **Status:** Passed
- **Project:** <alias> (<kind>)
- **Strategy:** swiftpm (`swift test`) | xcodebuild (iOS Simulator)
- **Simulator:** <name> (<os>) *(only for xcodebuild strategy)*
- **Result:** All tests passed
- **Command:** `max-test -p <alias> [flags]`
```

### On failure (exit 1):

```markdown
## Test Summary

- **Status:** Failed
- **Project:** <alias> (<kind>)
- **Strategy:** swiftpm (`swift test`) | xcodebuild (iOS Simulator)
- **Simulator:** <name> (<os>) *(only for xcodebuild strategy)*
- **Result:** Tests failed
- **Failures:** <list of failed test names if parseable>
- **Last output:**
  ```
  <last 10 lines of stdout/stderr>
  ```
- **Command:** `max-test -p <alias> [flags]`
```

### On dry-run:

```markdown
## Test Summary (dry-run)

- **Project:** <alias> (<kind>)
- **Strategy:** swiftpm | xcodebuild
- **Command:** `max-test -p <alias> [flags]`
```

---

## 7. Internal Execution Model (Deterministic)

### Phase 1 — Resolve

1. Read `${HOME}/.cursor/projects.json`.
2. Resolve project alias:
   - If provided in invocation → use it
   - If omitted → use `defaults.project`
   - If neither → STOP and request clarification
3. Validate project exists in `.projects`.
4. Determine test strategy for display purposes:
   - If `.projects[alias].test.mode` exists → use it (`swiftpm` or `xcode-ios-sim`)
   - Else infer from `kind`: `swift-package` → swiftpm, `ios-app` → xcodebuild, `swift-package-demo` → swiftpm if `Package.swift` exists
5. Resolve simulator alias (for xcodebuild strategy):
   - If provided via `-s` / `--simulator` → use it
   - If omitted → use `defaults.simulator`
6. Resolve optional flags: `--verbose`.

### Phase 2 — Execute

1. Construct CLI invocation:
   ```
   max-test -p <projectAlias> [-s <simAlias>] [-v] [--dry-run]
   ```
2. If `--dry-run` was specified → print the resolved command and STOP (do not execute).
3. Execute `max-test` and capture output (stdout + stderr).
4. Capture exit code.

### Phase 3 — Report

1. Determine result from exit code:
   - Exit 0 → all tests passed
   - Exit 1 → tests failed or script error
2. Parse output for test failure details:
   - For `swift test`: look for lines containing `failed` or `error:`
   - For `xcodebuild test`: look for `** TEST FAILED **` and `Failing tests:` sections
3. Format Execution Summary based on exit code and parsed output.
4. Render summary to chat.

---

## 8. Non-Goals / Forbidden Actions

This command MUST **NOT**:
- Modify `projects.json` or any configuration file
- Run tests on a physical device (simulator only for xcodebuild)
- Infer or guess missing project aliases
- Retry failed test executions
- Execute `max-run` or `max-spm`
- Interpret test failures as bugs or propose fixes (that is `@qa` or `@debug`'s job)
