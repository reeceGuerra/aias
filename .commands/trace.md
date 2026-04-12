# Trace (Log Instrumentation Plan) — v3

## 1. Identity

**Command Type:** Operative — Procedural / Execution

You are generating a **log instrumentation plan** — a structured, copy-ready specification of every `Log` call that must be inserted into a codebase to trace the execution of one or more flows.
This command is responsible for analyzing the target code, identifying every instrumentation point, producing an output that another agent (in `@dev` mode) can execute verbatim, and writing the trace plan to the task directory as `instrumentation.trace.md`.

**Skills referenced:** `rho-aias`.

---

## 2. Invocation / Usage

Invocation:
- `/trace FileName` — instrument a single file
- `/trace FileName AnotherFile` — instrument multiple files
- `/trace FileName --level debug` — override default log level (see Log Levels)

Usage notes:
- Best used with `@qa` or `@debug` mode active.
- The output is written to `instrumentation.trace.md` in TASK_DIR and also shown in chat.
- If TASK_DIR is set, the artifact is written to the directory. If not, the output is rendered in chat only (backward-compatible behavior).

---

## 3. Inputs

This command may use **only** the following inputs:
- File path(s) or class/struct name(s) provided by the user
- Chat context explicitly provided by the user (e.g., "trace the login flow", "instrument the checkout ViewModel")
- Codebase analysis results (reading the target files to identify methods, lifecycle hooks, state mutations, branches)
- Output from `@qa` or `@debug` mode reasoning (if active)

Rules:
- All inputs must be explicit.
- Read the target file(s) before producing output; never guess at method signatures or structure.
- If the scope is ambiguous (e.g., a file has multiple unrelated flows), ask the user to narrow down.

---

## 4. Output Contract (Format)

CHAT OUTPUT (always):
- The response MUST include a **Markdown code block** (` ```markdown ... ``` `) containing the full trace plan.
- The code block must be self-contained: another agent reading only this block must have everything needed to implement the logs.
- No text outside the code block except a one-line summary before it.
- Inside the code block, use rendered Markdown (headers, tables, code spans).

### Gate: Artifact Preview

**Type:** Confirmation
**Fires:** Before writing `instrumentation.trace.md` to TASK_DIR (only when TASK_DIR is set).
**Skippable:** No.

**Context output:**
Present artifact summary in chat:
- Artifact: `instrumentation.trace.md`
- Target: TASK_DIR path
- Total instrumentation points
- Flows covered

**AskQuestion:**
- **Runtime compatibility:** If `AskQuestion` is unavailable, use the Text Gate Protocol from `readme-commands.md` with the same prompt, option ids, labels, and `allow_multiple` semantics.
- **Prompt:** "Write trace plan to <TASK_DIR>?"
- **Options:**
  - `write`: "Write artifact to TASK_DIR"
  - `adjust`: "Adjust content before writing"
- **allow_multiple:** false

**On response:**
- `write` → Write artifact to TASK_DIR, proceed to End-of-Response Confirmation
- `adjust` → Apply corrections, return to context output and re-present gate

**Anti-bypass:** Inherits Gate Invocation Protocol. No additional rules.

FILE OUTPUT (when TASK_DIR is set):
- Follow the **rho-aias** skill loading protocol Phase 0 to resolve TASK_DIR.
- Write `instrumentation.trace.md` to TASK_DIR with the same content as the chat output.
- Create `status.md` if it does not exist (profile: infer from context).

STATUS UPDATE (Phase 5, when TASK_DIR is set):
- Add `instrumentation.trace.md` to the `artifacts` map with status `created` or `modified`.
- Add `trace` to `completed_steps`.
- Set `current_step` based on profile: if bugfix → `assess`; otherwise preserve current value.
- Run Phase 5c: sync non-synced artifacts to resolved knowledge provider. Phase 5c always publishes — it is NOT conditioned by plan classification (see **rho-aias** skill § Phase 5c).

END-OF-RESPONSE CONFIRMATION (when file is written):
  Saved trace to: <absolute_path>

---

## 5. Content Rules (Semantics)

- Output must be in **English**.
- Do **NOT** invent methods, properties, or flows that do not exist in the target code.
- Every `Log` call must include the **exact Swift code** ready to be inserted.
- Do **NOT** include explanations, rationale, or teaching content — only the instrumentation specification.

### Log Utility Rules

The project uses a custom `Log` enum with four levels:

| Method | Emoji | Emits in Release | Guard |
|---|---|---|---|
| `Log.debug(_:instance:)` | 🐛 | No | `#if DEBUG` |
| `Log.info(_:instance:)` | ℹ️ | No | `#if DEBUG` |
| `Log.warning(_:instance:)` | ⚠️ | Yes | — |
| `Log.error(_:instance:)` | ❌ | Yes | — |

**Default level policy:** Use `Log.warning` for entry/exit/lifecycle/mutation points and `Log.error` for error branches. If the user specifies `--level debug` or requests more detail, use `Log.debug` for entry/exit/lifecycle/mutation and `Log.info` for intermediate state, keeping `Log.error` for errors.

**`instance` parameter rules:**
- In **classes** (ViewModels, Services, Repositories, etc.): pass `self`.
- In **SwiftUI Views** (structs): pass the ViewModel property (e.g., `viewModel`). Identify which property holds the ViewModel by inspecting `@StateObject`, `@ObservedObject`, `@EnvironmentObject`, or `@State` with a class type. If no ViewModel exists, state it explicitly and skip `Log` calls for that view (suggest `print()` as fallback).

**Clock seed:**
- At the **entry point of the top-level flow** (e.g., the first method the user triggers), include `Log.resetClock()` so elapsed times (`t=...ms`) are relative to the flow start.
- Do NOT add `Log.resetClock()` at every method — only once at the flow entry.

**Message format:**
- Entry: `"→ methodName started param=\(value)"` (include relevant parameters, never sensitive data)
- Exit: `"← methodName completed result=\(summary)"` (include outcome summary)
- Lifecycle: `"◆ hookName triggered"` (e.g., `"◆ onAppear triggered"`)
- Mutation before: `"∆ propertyName will change: \(currentValue) → \(newValue)"` (when newValue is known) or `"∆ propertyName current: \(currentValue)"` (when newValue is computed)
- Mutation after: `"∆ propertyName did change → \(newValue)"`
- Error: `"✖ methodName failed: \(error)"` or `"✖ guard failed: conditionDescription"`

---

## 6. Output Structure (Template)

The code block must follow this structure:

```
## Trace Plan: <ClassName or FlowName>

### Scope
- **Files:** <list of files analyzed>
- **Flows:** <happy path + each error path identified>
- **Log level:** <warning/error (default) | debug/info/error (verbose)>
- **Instance parameter:** <`self` | `viewModel` | explanation>

### Clock Reset
<exact code for Log.resetClock() placement with location context>

### Happy Path

| # | Location | Type | Level | Code |
|---|---|---|---|---|
| 1 | `method()` entry | entry | warning | `Log.warning("→ method started", instance: self)` |
| 2 | ... | ... | ... | ... |

### Error Path: <Name>

| # | Location | Type | Level | Code |
|---|---|---|---|---|
| 1 | ... | error | error | `Log.error("✖ ...", instance: self)` |

### State Mutations

| # | Property | Trigger | When | Code |
|---|---|---|---|---|
| 1 | `isLoading` | `login()` | before | `Log.warning("∆ isLoading will change: \(isLoading) → true", instance: self)` |
| 2 | `isLoading` | `login()` | after | `Log.warning("∆ isLoading did change → \(isLoading)", instance: self)` |

### Lifecycle Hooks (SwiftUI only)

| # | Hook | View | Code |
|---|---|---|---|
| 1 | `onAppear` | `LoginView` | `Log.warning("◆ onAppear triggered", instance: viewModel)` |

### Summary
- **Total instrumentation points:** <N>
- **Flows covered:** <list>
- **Files touched:** <list>
```

Section rules:
- **Lifecycle Hooks** section: include only if target includes SwiftUI Views.
- **State Mutations** section: include only if mutable state (`@State`, `@Published`, `@Binding`, or plain `var`) is present.
- **Error Paths**: one sub-section per distinct error path identified. If no error paths exist, state "No error paths identified."
- Number rows sequentially within each table for easy reference.

---

## 7. Non-Goals / Forbidden Actions

This command must **NOT**:
- Modify any files or insert logs (that's `@dev`'s job)
- Propose code fixes, refactors, or architectural changes
- Include logs for files or methods not in the user's scope
- Use `print()` instead of `Log` (except as an explicit fallback note when no ViewModel is available in a struct)
- Invent methods, properties, or flows not present in the analyzed code
- Include `Log.resetClock()` more than once per flow
- Log sensitive data (passwords, tokens, PII) in message strings
- Add explanatory prose or teaching content inside the code block
