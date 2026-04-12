# Commit (Stage and Commit by File) — v3

## 1. Identity

**Command Type:** Operative — Procedural / Execution

You are **staging and committing** modified files to git, **one file per commit**.
This command is responsible for deterministically converting a validated working tree into a sequence of atomic commits with clear, file-scoped messages. It also detects open PRs for the current branch and verifies tracker review status through the configured provider.

**Skills referenced:** `rho-aias`.

---

## 2. Invocation / Usage

Invocation:
- `/commit`
- `/commit <projectAlias>`
- `/commit --plan`
- `/commit --dry-run`
- `/commit <projectAlias> --plan`
- `/commit <projectAlias> --dry-run`

Usage notes:
- By default, this command executes commits.
- `--plan` and `--dry-run` activate **planning mode** only (e.g. after @dev to review messages before committing).
- Planning mode generates commit messages and file mapping **without staging or committing**.
- Planning mode is non-destructive and produces no git side effects.
- Optional: if there is an active plan with increments, suggest aligning commit messages with increment names.

---

## 3. Inputs

This command may use **only** the following inputs:
- Git working tree state (`git status`, `git diff`)
- Chat context explicitly provided by the user
- Explicit file include / exclude instructions from the user
- Service configs:
  - `aias-config/providers/vcs-config.md`
  - `aias-config/providers/tracker-config.md`
- **Repository resolution** (in order of precedence):
  1. **Workspace:** current `.code-workspace` `folders` — use the path of the folder that is a git root (if `cursor.commitRoot` is set, use that folder by name or index; otherwise the first folder that is a git root).
  2. **Fallback:** `${HOME}/.cursor/projects.json` — resolve `basePath` + `projects.<alias>.repoDir` (or `defaults.project` when no alias).

Rules:
- Repository resolution MUST succeed before any git command is executed.
- No inferred paths, repositories, or files are allowed.
- If resolution fails (no workspace git root and no valid projects.json / project alias), the command must STOP.

---

## 4. Output Contract (Format)

- The response MUST be rendered as **plain Markdown** (not inside a code block).
- The output MUST list:
  - Each processed file
  - The generated commit message
  - The execution status (`planned`, `committed`, or `skipped`)
- No additional formatting or templates are applied.
- If Phase 1 step 6 detected documentation-impacting changes, append at the end:
  **Documentation reminder:** Changes to `[area]` may require updating `[suggested doc files]`.

---

## 5. Content Rules (Semantics)

- Commit messages must be in **English**.
- Commit message format MUST be: `[TYPE]: brief description`
- TYPE must be one of:
  BUILD, CI, DOCS, FEAT, FIX, PERF, REFACTOR, STYLE, TEST
- **AI-assisted prefix:** When the commit is produced with AI assistance, prepend `AI` to the type tag:
  `[AI BUILD]`, `[AI CI]`, `[AI DOCS]`, `[AI FEAT]`, `[AI FIX]`, `[AI PERF]`, `[AI REFACTOR]`, `[AI STYLE]`, `[AI TEST]`
- **Auto-detection rule:** If TASK_DIR is active and `status.md` exists, the command MUST use the `[AI *]` prefix automatically. If no TASK_DIR is set, use the standard `[TYPE]` prefix (manual commit assumed).
- Without the `AI` prefix = manual commit. This is the default — no extra effort required from human developers.
- Messages must be concise and file-scoped.
- **Optional body**: if the file diff contains multiple semantic changes (e.g., a refactor + a new method + an import change), add a blank line after the subject and append a short body with bullet points describing the key changes. Keep bullets brief (one line each, max 3–4 bullets). For simple diffs (single-purpose change), the subject line alone is sufficient.
- Do NOT invent changes or files.
- **ONE FILE PER COMMIT — NO EXCEPTIONS.** Even if multiple files are staged or modified, each file MUST be committed individually with its own message. Never batch, group, or combine files into a single commit unless the user explicitly says "combine" or "single commit". This is the defining rule of this command.

---

## 6. Output Structure (Template)

For each file processed:

- **File:** `<relative/path>`
- **Commit Message:** `[TYPE]: brief description`
- **Status:** `planned | committed | skipped (reason)`

After all files are processed, append a **final summary**:

```
COMMIT SUMMARY:
  Branch: <current branch>
  Committed: <N> files
  Skipped: <N> files (<reasons>)
  Types: <TYPE: count, TYPE: count, ...>
  AI-assisted: <yes (TASK_DIR active) | no>
  Tracker: <in_review (verified) | no open PR | no ticket in context>
```

TRACKER SYNC (Phase 6 — after commits, execution mode only)
- After all commits are done, resolve VCS provider from `aias-config/providers/vcs-config.md`.
- Detect if there is an open PR for the current branch via the resolved VCS skill.
- If an open PR is detected AND `task_id` is resolvable from TASK_DIR `status.md`:
  - Resolve tracker provider from `aias-config/providers/tracker-config.md`.
  - Read current tracker status resolved via provider mapping.
  - Verify canonical `in_review` state only (no primary transition ownership in this command).
  - If already `in_review`: no-op, report `in_review (verified)`.
  - If not `in_review`: report mismatch and direct remediation through `/pr`.
- If no open PR or no task_id: skip tracker sync, report reason.
- If tracker/vcs config is missing, invalid, or points to an unresolvable provider: abort sync and request provider configuration.

PUBLISH NUDGE:
- If TASK_DIR is resolvable and any artifacts have sync status `created` or `modified`, append:
  "Unpublished artifacts detected. Run `/publish` to archive all artifacts."

SERVICE RESOLUTION PSEUDOFLOW:

```
vcs = resolve(vcs-config) or abort(missing/invalid vcs config)
tracker = resolve(tracker-config) or abort(missing/invalid tracker config)
```

---

## 7. Non-Goals / Forbidden Actions

This command must **NOT**:
- Perform deep architectural reasoning
- Modify files beyond staging
- Amend existing commits
- Rebase, merge, or **push** (never push; only stage + commit locally)
- Infer or include files not present in `git status`
- Combine multiple files in a single commit (one file = one commit, always)
- Use `git add .`, `git add -A`, or stage multiple files at once
- Execute non-git commands (except resolved VCS/tracker provider lookups/sync)
- Proceed if repository resolution fails (STOP: need a workspace folder that is a git root, or a valid projects.json with project alias)

---

## Internal Execution Model (Deterministic)

This command executes in **two internal phases**.

### Phase 1 — Plan (Internal, Non-Interactive)

Executed for **all modes**, including `--plan` / `--dry-run`.

1. Resolve `PROJECT_ROOT`: (1) if current workspace has folders that are git roots, use the commit root (see Inputs); else (2) load and validate `${HOME}/.cursor/projects.json` and resolve project alias → `basePath` + `repoDir`.
2. **Branch safeguard**: check the current branch name. If it is `main`, `master`, or `develop`, fire the Branch Safeguard gate.

#### Gate: Branch Safeguard

**Type:** Confirmation
**Fires:** Phase 1, when the current branch is `main`, `master`, or `develop`.
**Skippable:** No.

**Context output:**
Present warning in chat:
- Current branch name
- Explicit warning that committing directly to this branch is unusual

**AskQuestion:**
- **Runtime compatibility:** If `AskQuestion` is unavailable, use the Text Gate Protocol from `readme-commands.md` with the same prompt, option ids, labels, and `allow_multiple` semantics.
- **Prompt:** "Current branch is `<branch>`. Committing directly to a protected branch — are you sure?"
- **Options:**
  - `confirm`: "Yes, commit to `<branch>`"
  - `abort`: "Abort — switch to a feature branch first"
- **allow_multiple:** false

**On response:**
- `confirm` → Continue with Phase 1 (step 3+)
- `abort` → STOP. Do not proceed

**Anti-bypass:** Inherits Gate Invocation Protocol. No additional rules.
3. Read git status to determine modified files.
4. Apply include / exclude rules.
5. For each target file:
   - Analyze file-scoped diff.
   - Select commit TYPE.
   - Generate commit message.
6. **Documentation awareness**: scan the planned changes for modifications to data models, API contracts, dependencies, configuration, or installation-related files. If detected, include a non-blocking documentation reminder in the output (see Output Contract).

If any step fails, STOP before execution.

### Phase 2 — Execute (Skipped in Planning Mode)

Executed **only if NOT** in `--plan` / `--dry-run`.

For each planned file, **one at a time, sequentially** (never batch):
1. `git add <file>` — stage **exactly one file**. Never use `git add .`, `git add -A`, or multiple paths.
2. `git commit -m "<message>"` — commit that single file.
3. Report result.
4. Move to the next file. Repeat until all files are committed.

---

## Notes

- **Repository resolution:** See `docs/COMMIT-AND-WORKSPACE.md` for workspace-first resolution and optional `cursor.commitRoot` in `.code-workspace`.
- `--plan` and `--dry-run` are synonyms.
- Planning mode is safe to run repeatedly.
- Each file is committed independently in execution mode.
- Untracked or unchanged files are skipped with a reason.
- Behavior is identical regardless of project type (ios-app, android-app, swift-package, etc.); only the resolved `PROJECT_ROOT` matters for git.
