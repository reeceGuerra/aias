# Run (Build & Launch on Simulator) — v1

## 1. Identity

**Command Type:** Operative — Procedural / Execution

You are **building and launching** an iOS app on the Simulator via the `max-run` script.
This command is responsible for resolving project and simulator configuration from `projects.json`, constructing the CLI invocation, executing `max-run`, and presenting an execution summary.

---

## 2. Invocation / Usage

Invocation:
- `/run`
- `/run <projectAlias>`
- `/run <projectAlias> [flags]`

Examples:
```
/run                                          → defaults from projects.json
/run mobilemax                                → explicit project alias
/run mobilemax -s iphone16pm                  → explicit simulator
/run mobilemax --simulator iphone16pm         → same, long flag
/run mobilemax -l                             → stream logs after launch
/run mobilemax --logs --log-level debug       → logs with level override
/run mobilemax --clean                        → clean build before running
/run --dry-run                                → show resolved command, do not execute
/run -p rdsui -s ipad -l                      → all short flags
```

Flags:
- `-p, --project <alias>` — project alias (default: `defaults.project` from `projects.json`)
- `-s, --simulator <alias>` — simulator alias (default: `defaults.simulator` from `projects.json`)
- `-l, --logs` — stream logs from the simulator after launch
- `--log-level <lvl>` — debug | info | warning | error (default: `defaults.logLevel` or `info`)
- `--log-seconds <n>` — stream logs for N seconds then stop (0 = infinite)
- `--clean` — clean build before running (default: incremental)
- `-v, --verbose` — verbose diagnostics
- `--dry-run` — print resolved command without executing
- `-h, --help` — show usage

Usage notes:
- This command may be invoked directly (no preceding mode required).
- When used with `@tooling` mode, the mode provides reasoning; this command handles execution.
- Positional `<projectAlias>` is equivalent to `-p <alias>`.

---

## 3. Inputs

This command may use **only** the following inputs:
- Chat context explicitly provided by the user (project alias, simulator, flags)
- Repository configuration from `${HOME}/.cursor/projects.json`

Rules:
- All inputs MUST be explicit or derivable from `projects.json` defaults.
- If the resolved project alias does not exist in `.projects`, STOP and list available projects.
- If the resolved project `kind` is not `ios-app` or `swift-package-demo`, STOP (not runnable).
- If the resolved simulator alias does not exist in `.catalog.simulators`, STOP and list available simulators.

---

## 4. Output Contract (Format)

- The response MUST be rendered as **plain Markdown** in chat (not inside a code block, not written to a file).
- The output MUST follow the Execution Summary templates defined in section 6.
- On `--dry-run`, show the resolved command without executing.

---

## 5. Content Rules (Semantics)

- Output MUST be in **English**.
- Do **NOT** invent information not present in the script output.
- Always include: Status, Project (alias + kind), Simulator (name + OS), Command executed.
- On failure: include the phase where it failed and the last relevant error from output.
- If output cannot be parsed, show the last 10 lines of raw output.

---

## 6. Output Structure (Template)

### On success (exit 0):

```markdown
## Run Summary

- **Status:** Success
- **Project:** <alias> (<kind>)
- **Simulator:** <name> (<os>)
- **Scheme:** <scheme>
- **Build:** Passed
- **Install:** Passed
- **Launch:** Passed
- **Logs:** Streaming (level: <lvl>) | Not requested
- **Command:** `max-run -p <alias> -s <sim> [flags]`
```

### On failure (exit 1):

```markdown
## Run Summary

- **Status:** Failed
- **Project:** <alias> (<kind>)
- **Simulator:** <name> (<os>)
- **Failed at:** Build | Boot | Install | Launch
- **Error:** <last error line from output>
- **Command:** `max-run -p <alias> -s <sim> [flags]`
```

### On dry-run:

```markdown
## Run Summary (dry-run)

- **Project:** <alias> (<kind>)
- **Simulator:** <name> (<os>)
- **Command:** `max-run -p <alias> -s <sim> [flags]`
```

---

## 7. Internal Execution Model (Deterministic)

### Phase 1 — Resolve

1. Read `${HOME}/.cursor/projects.json`.
2. Resolve project alias:
   - If provided in invocation → use it
   - If omitted → use `defaults.project`
   - If neither → STOP and request clarification
3. Validate project exists in `.projects` and is runnable (`kind: ios-app` or `swift-package-demo`).
4. Resolve simulator alias:
   - If provided via `-s` / `--simulator` → use it
   - If omitted → use `defaults.simulator`
5. Validate simulator exists in `.catalog.simulators`.
6. Resolve optional flags: `--logs`, `--log-level`, `--log-seconds`, `--clean`, `--verbose`.

### Phase 2 — Execute

1. Construct CLI invocation:
   ```
   max-run -p <projectAlias> -s <simAlias> [--clean] [--logs] [--log-level <lvl>] [--log-seconds <n>] [-v] [--dry-run]
   ```
2. If `--dry-run` was specified → print the resolved command and STOP (do not execute).
3. Execute `max-run` and capture output (stdout + stderr).
4. Capture exit code.

### Phase 3 — Report

1. Determine execution phase from output:
   - Look for `[info] Building` → build phase
   - Look for `[info] Waiting for simulator` → boot phase
   - Look for `[error]` → identify failure point
   - Look for `[info] App launched successfully` → success
2. Format Execution Summary based on exit code and parsed output.
3. Render summary to chat.

---

## 8. Non-Goals / Forbidden Actions

This command **MUST NOT**:
- Modify `projects.json` or any configuration file
- Run on a physical device (simulator only)
- Infer or guess missing project/simulator aliases
- Retry failed executions
- Execute `max-test` or `max-spm`
- Stream logs unless explicitly requested via `--logs` / `-l`
