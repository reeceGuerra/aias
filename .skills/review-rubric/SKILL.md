---
name: review-rubric
description: "Single source of truth for multi-agent review inspection criteria. Use when performing /self-review or /peer-review with multi-agent dispatch. Each review dimension sub-agent (correctness, quality, architecture, test-coverage, security) and the reflector selects its dimension selector from this skill to drive focused inspection. Trigger terms: review rubric, review criteria, inspection checklist, dimension review, multi-agent review."
category: knowledge
disable-model-invocation: false
version: 1.1.0
---

## PURPOSE

Provides the per-dimension inspection criteria used by `/self-review`, `/peer-review`, and the six AIAS review sub-agents (`aias-correctness-reviewer`, `aias-quality-reviewer`, `aias-architecture-reviewer`, `aias-test-auditor`, `aias-security-auditor`, `aias-reflector`). This skill is the **single source of truth** for review checklists — individual commands and sub-agents MUST NOT embed their own checklists.

---

## DIMENSION SELECTORS

Each sub-agent selects exactly one dimension. The reflector selects `reflector`.

---

### Selector: `correctness`

**Focus:** Logic errors, edge cases, behavioral regressions, and contract violations.

**Scope:** Flag findings only for code introduced or modified in the current diff. Pre-existing patterns in the working tree are out of scope unless they are directly exercised, called, or contaminated by the modified code path.

**Legacy posture:** When the modified file is dominantly legacy and the change is a localized addition, the reviewer MUST evaluate only the addition's correctness relative to the introduced surface, not against an idealized target state of the file. Flagging legacy logic adjacent to the change but not exercised by it is FORBIDDEN.

Inspection checklist:
- [ ] All code paths produce the expected output for valid inputs
- [ ] Boundary and edge cases are handled (empty collections, nil/null, overflow, off-by-one)
- [ ] Error paths return or propagate errors correctly; no swallowed exceptions
- [ ] Async/concurrent code is free of race conditions and data hazards
- [ ] API/protocol contracts (return types, error codes, side effects) match declarations
- [ ] No regression against previously passing behaviors visible in the diff context
- [ ] Complex logic is decomposed and legible enough to verify correctness
- [ ] All acceptance criteria from `dod.plan.md` (when available) are met

---

### Selector: `quality`

**Focus:** Code clarity, maintainability, naming, duplication, and technical debt.

**Scope:** Flag findings only for code introduced or modified in the current diff. Pre-existing naming, duplication, or technical debt in the working tree is out of scope unless the modified code path extends or amplifies it.

**Legacy posture:** When the modified file is dominantly legacy and the change is a localized addition, the reviewer MUST evaluate the addition's quality relative to the introduced surface, not against an idealized target state of the file. Suggesting refactors of adjacent legacy code that the diff does not touch is FORBIDDEN.

Inspection checklist:
- [ ] Names (variables, functions, types, modules) are descriptive and consistent with the codebase conventions
- [ ] Functions/methods have a single, clear responsibility (no god-functions)
- [ ] Dead code, commented-out code, and TODOs introduced in this diff are either removed or tracked
- [ ] No unnecessary duplication — logic shared across locations is extracted appropriately
- [ ] Complexity is justified; overly complex code that can be simplified is flagged
- [ ] Code is readable without needing comments to explain what it does (comments explain why, not what)
- [ ] Magic numbers and string literals are extracted to named constants
- [ ] Consistent formatting and style with the surrounding file and project conventions

---

### Selector: `architecture`

**Focus:** Pattern conformance, layer boundaries, coupling, and scalability.

**Scope:** Flag findings only for architectural decisions introduced or modified by the current diff. Pre-existing architectural debt (legacy layer violations, ambient coupling) is out of scope unless the modified code path reinforces or extends it.

**Legacy posture:** When the modified file is dominantly legacy and the change is a localized addition, the reviewer MUST evaluate whether the addition itself respects the declared architecture, not whether the surrounding legacy code does. Suggesting layer realignments that require touching code outside the diff is FORBIDDEN.

Inspection checklist:
- [ ] Code placement respects the architectural layers declared in `RHOAIAS.md` / `technical.plan.md` (when available)
- [ ] No inappropriate coupling between layers (e.g., UI logic in a data layer)
- [ ] Dependencies flow in the correct direction per the architecture (no circular references)
- [ ] New modules/types introduced are justified and fit the existing design vocabulary
- [ ] Platform-agnostic modules remain platform-agnostic; platform-specific code is isolated
- [ ] Public APIs are minimal and intentional; internal implementation is encapsulated
- [ ] Scalability and extensibility are not compromised for the stated task scope
- [ ] Pattern conformance: MVVM, Clean Architecture, Repository, or other patterns declared in `stack-profile.md` are followed where applicable

---

### Selector: `test-coverage`

**Focus:** Test posture, coverage gaps, assertion quality, and untested paths.

**Scope:** Flag findings only for code introduced or modified by the current diff. Pre-existing untested code in the working tree is out of scope unless the modified code path directly exercises or depends on it.

**Legacy posture:** When the modified file is dominantly legacy and the change is a localized addition, the reviewer MUST evaluate test coverage of the addition only. Demanding tests for untouched legacy code, or demanding that legacy modules acquire net-new test infrastructure, is FORBIDDEN.

Inspection checklist:
- [ ] Unit tests exist for all new functions/methods with meaningful logic
- [ ] Tests cover the happy path, at least two edge cases, and one error path per function
- [ ] Test names clearly describe the scenario being validated (not just the function name)
- [ ] Assertions are specific and meaningful; no vacuous `assertTrue(true)` style assertions
- [ ] Mocks and stubs are used appropriately; external dependencies are not tested through real network calls
- [ ] Regression tests are added for any bug fixed in this diff
- [ ] Test isolation: tests do not depend on execution order or shared mutable state
- [ ] If UI code is present, at least one snapshot or integration test exists for the modified view

---

### Selector: `security`

**Focus:** Injection risks, authentication/authorization gaps, sensitive data exposure, and dependency vulnerabilities.

**Scope:** Flag findings only for security surface introduced or modified by the current diff. Pre-existing security debt in the working tree is out of scope unless the modified code path extends, calls, or amplifies it.

**Legacy posture:** When the modified file is dominantly legacy and the change is a localized addition, the reviewer MUST evaluate whether the addition introduces new security surface, not whether surrounding legacy code has historical issues. Suggesting hardening of legacy code that the diff does not touch is FORBIDDEN.

Inspection checklist:
- [ ] All user inputs are validated and sanitized before use in queries, file paths, or commands
- [ ] No SQL, shell, or template injection vectors introduced
- [ ] Authentication and authorization checks are not bypassed or weakened in the diff
- [ ] Sensitive data (tokens, keys, passwords, PII) is not logged, serialized to disk, or transmitted in plaintext
- [ ] New dependencies introduced do not have known critical CVEs (check available advisories)
- [ ] Cryptographic operations use current recommended algorithms; no MD5/SHA-1 for security purposes
- [ ] Error messages do not leak internal system details to external callers
- [ ] Network calls validate server certificates; no `allowsArbitraryLoads` or equivalent added

---

### Selector: `reflector`

**Focus:** Meta-review — synthesize findings from all 5 dimensions into a prioritized, deduplicated summary.

**Scope:** Operates over the consolidated findings list emitted by the five dimension reviewers. The reflector MUST NOT introduce findings sourced from its own re-reading of the diff; its job is synthesis and gate emission.

**Legacy posture:** The reflector MUST honor the per-dimension Legacy posture by discarding any finding that violates Scope or Legacy posture during the pre-filter step (Step 0 below). If a dimension reviewer produced a legacy-only finding by mistake, the reflector drops it silently and notes the count of pre-filtered findings in the summary footer.

Reflector protocol:
0. **Pre-filter (v1.1):** Walk every incoming finding and discard those that violate Scope or Legacy posture of their dimension. A finding is FORBIDDEN if it (a) anchors to code outside the diff, (b) targets untouched legacy code adjacent to the change, or (c) demands action that requires editing files not in the diff. Track the count of discarded findings; surface it in the summary footer as `[pre-filtered: N legacy/out-of-scope findings dropped]`.
1. Collect all findings from the five dimension reviewers.
2. Apply the deduplication protocol (from `readme-multi-agent-review.md`):
   - Exact duplicate (same file + line + rationale) → keep highest severity; attribute to all dimensions.
   - Overlapping duplicate (same file + nearby lines + related rationale) → merge with combined dimension label.
   - Independent findings → keep as distinct entries.
3. Group by severity: **Critical** first, then **Major**, then **Minor**.
4. Within each severity group, sort by dimension: correctness → security → architecture → quality → test-coverage.
5. Produce a final consolidated findings list with: `[Severity] [Dimension(s)] File:Line — Description`.
6. Emit a summary header:
   ```
   Review complete: N Critical, M Major, P Minor findings.
   [BLOCKED / ESCALATED / PASS] — rationale
   ```
7. If any Critical finding exists → emit `BLOCKED`. If only Major → emit `ESCALATED`. If only Minor or none → emit `PASS`.

---

## SAFETY RULES

- **Read-only**: this skill provides inspection criteria only. Sub-agents that consume it MUST NOT apply fixes autonomously.
- **No auto-escalation**: severity assignment is the sub-agent's judgment call based on the checklist; do not fabricate severity to appear thorough.
- **No cross-dimension contamination during review**: each sub-agent's pass is isolated; the reflector handles synthesis.
- **Context dependency**: when `dod.plan.md`, `technical.plan.md`, or `stack-profile.md` are available in TASK_DIR, they MUST be loaded before inspection to provide architectural and DoD context.
- **Scope discipline**: findings MUST be anchored to the current diff or working-tree change; do not flag pre-existing issues unless they are directly related to the modified code.
