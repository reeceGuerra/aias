# SPM — Swift Package Manager Planner (v5)

## 1. Identity

**Command Type:** Operative — Procedural / Execution

You are **planning and executing** Swift Package Manager operations.
This command is responsible for interpreting user intent, generating a **complete, schema-compliant JSON plan**, executing `max-spm` with that plan, and formatting the result as a human-readable report.

---

## 2. Invocation / Usage

Invocation:
- `/spm <packageName> <commitHash>`
- `/spm <packageName> <commitHash> [flags]`
- `/spm <packageName> -u [flags]`

Examples:
```
/spm rdsui abc1234                            → pin with defaults
/spm rdsui abc1234 -b develop                 → pin with branch (short)
/spm rdsui abc1234 --branch develop           → pin with branch (long)
/spm rdsui -u                                 → update with existing branch (short)
/spm rdsui --update -b feature/x              → update with explicit branch
/spm rdsui abc1234 -p mobilemax               → explicit project (short)
/spm --dry-run rdsui abc1234                  → show JSON plan, do not execute
```

Flags:
- `-p, --project <alias>` — project alias (default: `defaults.project` from `projects.json`)
- `-u, --update` — update mode (mutually exclusive with commit hash)
- `-b, --branch <name>` — branch name (optional for pin, required for update if not in existing pin)
- `--pbxproj-branch <name>` — override branch in project.pbxproj (optional)
- `--dry-run` — show generated JSON plan without executing `max-spm`
- `-h, --help` — show usage

Usage notes:
- This command may be invoked directly.
- It may be preceded by an explicit reasoning step (`@planning`) when intent is complex.
- Positional `<packageName>` is always the first argument; `<commitHash>` is the second (for pin mode).
- `--dry-run` outputs the generated JSON plan to chat and stops; `max-spm` is NOT invoked.
- Internally, this command generates a JSON plan and pipes it to `max-spm` via stdin.

---

## 3. Inputs

This command may use **only** the following inputs:
- Chat context explicitly provided by the user
- Repository configuration from `${HOME}/.cursor/projects.json`
- Current `Package.resolved` content
- Explicit CLI-like arguments provided in the invocation

Rules:
- All inputs **MUST** be explicit or derivable from repository state.
- Any ambiguity (package identity, branch, project) **MUST** be resolved **before** plan emission.
- If ambiguity cannot be resolved, the command **MUST** STOP and request clarification.

---

## 4. Output Contract (Format)

- The response **MUST** be rendered as **plain Markdown** (not inside a code block).
- The output **MUST** include:
  - Execution status (`ok`, `stop`, or `error`)
  - Package changes (before/after state)
  - Execution details (timing, dependencies resolution)
  - Artifacts (files modified, backups created)
- Markdown MUST be formatted for readability (headings, lists, code blocks for technical details).

---

## 5. Content Rules (Semantics)

- Output **MUST** be in **English**.
- Do **NOT** invent information not present in the result JSON.
- Include **all relevant details** from the result:
  - Package state changes (`package.before` → `package.after`)
  - Execution timing and status (`execution.timingsMs`, `execution.resolveExitCode`)
  - Modified files and backups (`artifacts.filesModified`, `artifacts.backupCreated`)
  - Error details when `status` is `stop` or `error` (`code`, `details`)
- Format technical values (revisions, paths) clearly.
- Use appropriate formatting for success (`ok`), validation failures (`stop`), and errors (`error`).

---

## 6. Output Structure (Template)

The report structure varies by `status`:

### For `status: "ok"`

- **Status:** Success (`code`)
- **Operation:** `mode` (pin/update)
- **Package:** `package.matchedValue` (identity)
- **Changes:**
  - Before: `package.before.revision` / `package.before.branch`
  - After: `package.after.revision` / `package.after.branch`
- **Execution:**
  - Dependencies resolved: `execution.resolveDependencies` (if true)
  - Timing: `execution.timingsMs.total` ms (if available)
- **Artifacts:**
  - Files modified: `artifacts.filesModified`
  - Backup created: `artifacts.backupCreated` (if present)

### For `status: "stop"` or `status: "error"`

- **Status:** `status` (`code`)
- **Message:** `summary.message`
- **Details:** `details` object (if present and relevant)
- **Operation attempted:** `mode`
- **Package:** `package.matchedValue` (if available)
- **Artifacts:** `artifacts.filesModified` (if any files were modified before failure)

---

## 7. Non-Goals / Forbidden Actions

This command **MUST NOT**:
- Modify files directly (only via `max-spm`)
- Execute git, xcodebuild, or SwiftPM directly (only via `max-spm`)
- Call `max-run` or `max-test`
- Infer or guess missing data in the plan
- Retry failed executions
- Perform alternative planning strategies
- Emit raw JSON result without formatting (always render the Execution Summary)
- Pass CLI flags directly to `max-spm` (always use JSON plan via stdin — CLI migration is phase 2)

---

## Internal Execution Model (Deterministic)

This command executes in **three internal phases**.

### Phase 1 — Plan (Internal, Non-Interactive)

Executed for **all invocations**.

1. Load and validate `${HOME}/.cursor/projects.json` (or `configPath` if provided).
2. Resolve `projectAlias`:
   - If provided in invocation or chat context → use it
   - If omitted → use `defaults.project` from `projects.json`
   - If neither exists → STOP and request clarification
3. Resolve project paths from `projects.json`:
   - Locate `Package.resolved` at resolved `RUN_ROOT`
   - **Note**: For Xcode projects, `Package.resolved` may be at:
     - `RUN_ROOT/Package.resolved` (root)
     - `RUN_ROOT/*.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved` (Xcode workspace)
   - If `Package.resolved` does not exist at `RUN_ROOT` → check Xcode workspace path
   - If still not found → STOP and report location issue
4. Read `Package.resolved` (supports both modern `.pins` and legacy `.object.pins` formats).
5. Resolve `package.name`:
   - If provided in invocation → must match exactly one `identity` in `Package.resolved`
   - If multiple matches → STOP and list matches for user clarification
   - If no matches → STOP with package not found
6. Determine `mode`:
   - If `-u` / `--update` flag or "update" intent → `mode: "update"`
   - If commit hash provided → `mode: "pin"`
   - If neither → STOP and request clarification
7. For `mode: "pin"`:
   - Extract `revision` from invocation or chat context
   - Validate: 7–40 hex characters
   - Extract `branch` if provided (optional)
8. For `mode: "update"`:
   - Extract `branch` from invocation, chat context, or existing pin state
   - If branch cannot be determined → STOP
9. Determine `options.projectPbxprojBranch` (optional):
   - If explicitly provided in invocation (e.g., `--pbxproj-branch <branch>`) or chat context → use it
   - If omitted → do not include in plan (script will use `pin.branch`/`update.branch` as fallback)
10. Apply schema defaults:
   - `options.resolveDependencies`: default `true` (include explicitly)
11. Generate complete JSON plan conforming to Plan Schema v1.3.
    - **CRITICAL**: The JSON MUST be syntactically valid (all commas, brackets, quotes correct).
    - **CRITICAL**: `package.name` MUST be inside the `package` object, NOT at the top level.
    - Use this exact structure:
      - For `mode: "update"`:
        ```json
        {
          "schemaVersion": 1,
          "command": "max-spm",
          "projectAlias": "<resolved_alias>",
          "mode": "update",
          "package": {
            "name": "<exact_identity_from_Package.resolved>"
          },
          "update": {
            "branch": "<branch_name>"
          },
          "options": {
            "resolveDependencies": true,
            "projectPbxprojBranch": "<branch_name>"
          }
        }
        ```
        Note: Include `projectPbxprojBranch` in `options` only if explicitly provided or if different from `update.branch`.
      - For `mode: "pin"`:
        ```json
        {
          "schemaVersion": 1,
          "command": "max-spm",
          "projectAlias": "<resolved_alias>",
          "mode": "pin",
          "package": {
            "name": "<exact_identity_from_Package.resolved>"
          },
          "pin": {
            "revision": "<7-40_hex_characters>",
            "branch": "<branch_name>"
          },
          "options": {
            "resolveDependencies": true,
            "projectPbxprojBranch": "<branch_name>"
          }
        }
        ```
        Note: Include `projectPbxprojBranch` in `options` only if explicitly provided or if different from `pin.branch`. If `pin.branch` is omitted, include `projectPbxprojBranch` if provided.
    - **VALIDATION STEP**: Before executing, validate the JSON using `jq`:
      ```bash
      echo "$PLAN_JSON" | jq -e '.' >/dev/null 2>&1
      ```
      If validation fails, STOP and report the JSON syntax error. Do NOT proceed to execution.

If any step fails, STOP before execution.

### Phase 2 — Execute

Executed **immediately after** Phase 1.

1. **Validate JSON syntax** (CRITICAL):
   - Use `jq` to validate: `echo "$PLAN_JSON" | jq -e '.' >/dev/null 2>&1`
   - If validation fails → STOP immediately and report: "JSON syntax error in plan. Please review the generated JSON structure."
   - Do NOT proceed to execution if JSON is invalid.
2. **If `--dry-run` was specified:**
   - Print the validated JSON plan to chat as a fenced code block (```json).
   - Do NOT invoke `max-spm`. STOP here.
3. Invoke `max-spm` with the plan JSON via `stdin`:
   - Use: `echo "$PLAN_JSON" | max-spm --config "$CONFIG_PATH"`
   - Or: `cat << 'EOF' | max-spm --config "$CONFIG_PATH"` followed by the JSON and `EOF`
4. Capture `stdout` (result JSON) and `stderr` (logs):
   - Redirect `stdout` to capture result JSON
   - Redirect `stderr` to capture logs (optional, for debugging)
5. Parse result JSON (must conform to Result Schema v1):
   - Validate result JSON with `jq` before parsing
6. If JSON parsing fails → report error and STOP.
7. Capture exit code (`0` = ok, `2` = stop, `3` = error).

### Phase 3 — Format

Executed **immediately after** Phase 2.

1. Extract `status`, `code`, `summary`, `package`, `execution`, `artifacts`, `details` from result JSON.
2. Format report based on `status`:
   - `ok`: Success report with before/after, timing, artifacts
   - `stop`: Validation failure report with code, message, details
   - `error`: Error report with code, message, details
3. Render formatted Markdown to chat.

---

## Notes

- The plan generation phase resolves all ambiguity before execution.
- `max-spm` always emits valid JSON to `stdout` (even on errors, via traps).
- Exit codes from `max-spm`: `0` (ok), `2` (stop), `3` (error).
- Logs from `max-spm` go to `stderr` and are not required for parsing.
- The formatted report MUST be clear and actionable for human review.
